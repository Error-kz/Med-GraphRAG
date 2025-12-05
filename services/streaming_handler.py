"""
流式处理服务
处理医疗问答的流式输出，实时发送查询进度和结果
"""
import json
import re
import datetime
import requests
from typing import AsyncGenerator

from core.cache.redis_client import get_redis_client, save_conversation_history, save_session_to_history


async def send_event(event_type: str, data: dict) -> str:
    """
    发送SSE事件
    
    Args:
        event_type: 事件类型
        data: 事件数据
        
    Returns:
        SSE格式的事件字符串
    """
    event_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {event_data}\n\n"


async def chatbot_stream(
    query: str,
    session_id: str,
    milvus_vectorstore,
    client_llm,
    graph_api_url: str,
    graph_api_url_backup: str,
    format_docs_func
) -> AsyncGenerator[str, None]:
    """
    流式处理医疗问答
    实时发送查询进度和结果
    
    Args:
        query: 用户问题
        session_id: 会话ID
        milvus_vectorstore: Milvus向量存储实例
        client_llm: DeepSeek LLM客户端
        graph_api_url: 知识图谱服务主地址
        graph_api_url_backup: 知识图谱服务备用地址
        format_docs_func: 格式化文档的函数
        
    Yields:
        SSE格式的事件字符串
    """
    # 发送会话ID事件（前端需要保存）
    yield await send_event('session_id', {
        'session_id': session_id
    })
    
    # 初始化搜索路径和结果追踪
    search_path = []
    search_stages = {
        'milvus_vector': {'status': 'pending', 'results': [], 'count': 0, 'description': '向量数据库检索'},
        'knowledge_graph': {'status': 'pending', 'results': [], 'count': 0, 'description': '知识图谱查询', 'cypher_query': '', 'confidence': 0}
    }
    
    # 发送向量检索开始事件
    yield await send_event('search_stage', {
        'stage': 'milvus_vector',
        'status': 'pending',
        'message': '开始向量数据库检索...'
    })
    
    # 1、向量数据库检索
    context = ""
    try:
        recall_rerank_milvus = milvus_vectorstore.similarity_search(
            query,
            k=10,
            ranker_type='rrf',
            ranker_params={'k': 100}
        )
        
        if recall_rerank_milvus:
            context = format_docs_func(recall_rerank_milvus)
            search_stages['milvus_vector']['status'] = 'success'
            search_stages['milvus_vector']['count'] = len(recall_rerank_milvus)
            search_stages['milvus_vector']['results'] = [
                doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content
                for doc in recall_rerank_milvus[:3]
            ]
            search_path.append('milvus_vector')
            
            # 发送向量检索完成事件
            yield await send_event('search_stage', {
                'stage': 'milvus_vector',
                'status': 'success',
                'count': len(recall_rerank_milvus),
                'results': search_stages['milvus_vector']['results'],
                'message': f'向量检索完成，找到 {len(recall_rerank_milvus)} 条结果'
            })
        else:
            context = ""
            search_stages['milvus_vector']['status'] = 'empty'
            yield await send_event('search_stage', {
                'stage': 'milvus_vector',
                'status': 'empty',
                'message': '向量检索未找到结果'
            })
    except Exception as e:
        context = ""
        search_stages['milvus_vector']['status'] = 'error'
        search_stages['milvus_vector']['error'] = str(e)
        print(f'向量检索错误: {str(e)}')
        yield await send_event('search_stage', {
            'stage': 'milvus_vector',
            'status': 'error',
            'error': str(e),
            'message': f'向量检索失败: {str(e)}'
        })
    
    # 发送知识图谱查询开始事件
    yield await send_event('search_stage', {
        'stage': 'knowledge_graph',
        'status': 'pending',
        'message': '开始知识图谱查询...'
    })
    
    # 2、知识图谱查询
    graph_context = ""
    current_api_url = graph_api_url
    
    try:
        graph_data = {'natural_language_query': query}
        
        try:
            graph_response = requests.post(
                f'{current_api_url}/generate',
                json=graph_data,
                timeout=60,
                proxies={'http': None, 'https': None}
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f'⚠️ 主地址连接失败，尝试备用地址: {graph_api_url_backup}')
            current_api_url = graph_api_url_backup
            graph_response = requests.post(
                f'{current_api_url}/generate',
                json=graph_data,
                timeout=60,
                proxies={'http': None, 'https': None}
            )
        
        if graph_response.status_code == 200:
            graph_response_data = graph_response.json()
            cypher_query = graph_response_data.get('cypher_query')
            confidence = graph_response_data.get('confidence', 0)
            is_valid = graph_response_data.get('validated', False)
            
            search_stages['knowledge_graph']['cypher_query'] = cypher_query or ''
            search_stages['knowledge_graph']['confidence'] = float(confidence) if confidence else 0
            
            # 发送Cypher查询生成事件
            yield await send_event('search_stage', {
                'stage': 'knowledge_graph',
                'status': 'pending',
                'cypher_query': cypher_query or '',
                'confidence': float(confidence) if confidence else 0,
                'message': f'已生成Cypher查询，置信度: {confidence}'
            })
            
            if cypher_query and float(confidence) >= 0.7 and is_valid:
                print(f'知识图谱查询生成成功，置信度: {confidence}')
                
                # 验证查询
                validate_data = {'cypher_query': cypher_query}
                validate_response = requests.post(
                    f'{current_api_url}/validate',
                    json=validate_data,
                    timeout=15,
                    proxies={'http': None, 'https': None}
                )
                
                if validate_response.status_code == 200:
                    validate_data = validate_response.json()
                    if validate_data.get('is_valid', False):
                        # 执行查询
                        execute_data = {'cypher_query': cypher_query}
                        execute_response = requests.post(
                            f'{current_api_url}/execute',
                            json=execute_data,
                            timeout=20,
                            proxies={'http': None, 'https': None}
                        )
                        
                        if execute_response.status_code == 200:
                            execute_result = execute_response.json()
                            if execute_result.get('success') and execute_result.get('records'):
                                records = execute_result['records']
                                
                                # 解析Cypher查询，提取关键信息
                                relationship_type = None
                                disease_name = None
                                entity_type = None
                                
                                rel_match = re.search(r'\[[^:]*:(.*?)\]', cypher_query)
                                if rel_match:
                                    relationship_type = rel_match.group(1).strip()
                                
                                disease_match = re.search(r"p\.name\s*=\s*['\"](.*?)['\"]", cypher_query)
                                if disease_match:
                                    disease_name = disease_match.group(1)
                                
                                return_match = re.search(r'RETURN\s+(\w+)\.name', cypher_query, re.IGNORECASE)
                                if return_match:
                                    var_name = return_match.group(1)
                                    var_def_match = re.search(rf'\({var_name}:(\w+)\)', cypher_query)
                                    if var_def_match:
                                        entity_type = var_def_match.group(1)
                                
                                # 关系类型描述映射
                                relationship_descriptions = {
                                    'not_eat': '不能吃',
                                    'do_eat': '适合吃',
                                    'recommand_eat': '推荐吃',
                                    'has_symptom': '的症状',
                                    'recommand_drug': '推荐使用的药物',
                                    'command_drug': '推荐使用的药物',
                                    'need_check': '需要做的检查',
                                    'belongs_to': '所属科室',
                                    'acompany_with': '的并发症',
                                    'drugs_of': '的生产厂商'
                                }
                                
                                relationship_desc = relationship_descriptions.get(relationship_type, '相关')
                                
                                # 格式化知识图谱查询结果
                                graph_results = []
                                entity_names = []
                                
                                for record in records:
                                    for key, value in record.items():
                                        if isinstance(value, dict):
                                            if value.get('type') == 'Node':
                                                props = value.get('properties', {})
                                                if 'name' in props:
                                                    entity_names.append(props['name'])
                                            elif value.get('type') == 'Relationship':
                                                props = value.get('properties', {})
                                                if 'name' in props:
                                                    entity_names.append(props['name'])
                                        else:
                                            if value is not None:
                                                value_str = str(value).strip()
                                                if value_str:
                                                    entity_names.append(value_str)
                                
                                # 生成描述性文本
                                if entity_names:
                                    if disease_name and relationship_desc:
                                        if relationship_type in ['not_eat', 'do_eat', 'recommand_eat']:
                                            graph_results.append(f"{disease_name}患者{relationship_desc}的食物：{', '.join(entity_names)}")
                                        elif relationship_type == 'has_symptom':
                                            graph_results.append(f"{disease_name}{relationship_desc}：{', '.join(entity_names)}")
                                        elif relationship_type in ['recommand_drug', 'command_drug']:
                                            graph_results.append(f"{disease_name}{relationship_desc}：{', '.join(entity_names)}")
                                        elif relationship_type == 'need_check':
                                            graph_results.append(f"{disease_name}{relationship_desc}：{', '.join(entity_names)}")
                                        elif relationship_type == 'belongs_to':
                                            graph_results.append(f"{disease_name}{relationship_desc}：{', '.join(entity_names)}")
                                        elif relationship_type == 'acompany_with':
                                            graph_results.append(f"{disease_name}{relationship_desc}：{', '.join(entity_names)}")
                                        else:
                                            graph_results.append(f"{disease_name}的{relationship_desc}：{', '.join(entity_names)}")
                                    else:
                                        if entity_names:
                                            graph_results.append(f"查询结果：{', '.join(entity_names)}")
                                
                                if graph_results:
                                    graph_context = "【知识图谱查询结果 - 这是从结构化知识图谱数据库中查询到的准确信息，请作为回答的核心依据】\n" + "\n".join(graph_results)
                                    search_stages['knowledge_graph']['status'] = 'success'
                                    search_stages['knowledge_graph']['count'] = len(entity_names)
                                    search_stages['knowledge_graph']['results'] = graph_results
                                    search_path.append('knowledge_graph')
                                    print(f'✅ 知识图谱查询成功，返回 {len(entity_names)} 条结果')
                                    
                                    # 发送知识图谱查询完成事件
                                    yield await send_event('search_stage', {
                                        'stage': 'knowledge_graph',
                                        'status': 'success',
                                        'count': len(entity_names),
                                        'results': graph_results,
                                        'cypher_query': cypher_query,
                                        'confidence': float(confidence) if confidence else 0,
                                        'message': f'知识图谱查询完成，找到 {len(entity_names)} 条结果'
                                    })
                                
    except requests.exceptions.Timeout as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'请求超时: {str(e)}'
        print(f'⚠️ 知识图谱服务请求超时: {str(e)}')
        yield await send_event('search_stage', {
            'stage': 'knowledge_graph',
            'status': 'error',
            'error': f'请求超时: {str(e)}',
            'message': f'知识图谱查询超时'
        })
    except requests.exceptions.ConnectionError as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'连接失败: {str(e)}'
        print(f'⚠️ 知识图谱服务连接失败: {str(e)}')
        yield await send_event('search_stage', {
            'stage': 'knowledge_graph',
            'status': 'error',
            'error': f'连接失败: {str(e)}',
            'message': f'知识图谱服务连接失败'
        })
    except Exception as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'查询异常: {str(e)}'
        print(f'⚠️ 知识图谱查询异常: {str(e)}')
        yield await send_event('search_stage', {
            'stage': 'knowledge_graph',
            'status': 'error',
            'error': str(e),
            'message': f'知识图谱查询异常'
        })
    
    # 合并所有上下文 - 以知识图谱为核心，结合向量搜索结果
    vector_context_label = ""
    if context:
        vector_context_label = "【向量检索补充信息 - 这些信息来自向量数据库检索，可作为补充和参考，帮助完善答案】"
    
    if graph_context:
        # 如果有知识图谱结果，以知识图谱为核心，向量检索作为补充
        if context:
            context = graph_context + '\n\n' + vector_context_label + '\n' + context
        else:
            context = graph_context
        print(f'📝 最终上下文长度: {len(context)} 字符（知识图谱为核心，向量检索作为补充）')
    else:
        # 如果没有知识图谱结果，使用向量检索结果
        if context:
            context = vector_context_label + '\n' + context
        print('⚠️ 本次查询未使用知识图谱结果，仅使用向量检索结果')
    
    # 发送开始生成回答事件
    yield await send_event('answer_start', {
        'message': '开始生成回答...'
    })
    
    # 定义系统提示和用户提示
    SYSTEM_PROMPT = """
        System: 你是一个非常得力的医学助手, 你可以通过从数据库中检索出的信息找到问题的答案.
        
        重要要求：
        1. 回答必须使用纯文本格式，不要使用任何 Markdown 格式（如 **粗体**、*斜体*、# 标题等）
        2. 不要使用任何 HTML 标签（如 <p>、<br>、<div> 等）
        3. 不要使用代码块格式（如 ``` 等）
        4. 直接使用普通的中文文本回答，使用换行符分隔段落
        5. 保持回答简洁、清晰、专业
        6. **以知识图谱为核心，结合向量搜索结果**：
           - 如果上下文中包含"【知识图谱查询结果】"部分，这些信息是从结构化知识图谱数据库中查询到的准确信息，必须作为回答的核心依据。
           - 如果上下文中还包含"【向量检索补充信息】"部分，这些信息来自向量数据库检索，应该结合知识图谱结果一起使用，帮助完善和丰富答案。
           - 知识图谱结果具有更高的准确性和权威性，应该优先使用；向量检索结果可以作为补充，提供更全面的信息。
    """

    USER_PROMPT = f"""
        User: 利用介于<context>和</context>之间的从数据库中检索出的信息来回答问题, 具体的问题介于<question>和</question>之间.
        
        **重要提示 - 综合使用两路查询结果**：
        1. **以知识图谱为核心**：如果上下文中包含"【知识图谱查询结果】"部分，这些信息是从结构化知识图谱数据库中查询到的准确信息，必须作为回答的核心依据和主要信息来源。
        2. **结合向量搜索结果**：如果上下文中还包含"【向量检索补充信息】"部分，这些信息来自向量数据库检索，应该与知识图谱结果结合使用，帮助完善、丰富和补充答案，提供更全面的信息。
        3. **综合策略**：
           - 优先使用知识图谱查询结果作为核心答案
           - 使用向量检索结果补充细节、背景信息或相关知识点
           - 如果知识图谱结果和向量检索结果有冲突，以知识图谱结果为准
           - 如果只有向量检索结果，可以使用它作为主要信息来源
        4. 如果提供的信息为空, 则按照你的经验知识来给出尽可能严谨准确的回答。
        5. 不知道的时候坦诚的承认不了解, 不要编造不真实的信息。
        6. 请用纯文本格式回答，不要使用任何特殊标签或格式标记。
        
        <context>
        {context}
        </context>

        <question>
        {query}
        </question>
    """
    
    # 使用 DeepSeek 模型流式生成回复
    try:
        response = client_llm.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {"role": "user", "content": USER_PROMPT},
            ],
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                # 发送流式回答片段
                yield await send_event('answer_chunk', {
                    'content': content
                })
        
        # 后处理：移除可能的 Markdown 格式标记
        full_response = re.sub(r'\*\*(.*?)\*\*', r'\1', full_response)
        full_response = re.sub(r'\*(.*?)\*', r'\1', full_response)
        full_response = re.sub(r'^#+\s*', '', full_response, flags=re.MULTILINE)
        full_response = re.sub(r'```[\s\S]*?```', '', full_response)
        full_response = re.sub(r'`([^`]+)`', r'\1', full_response)
        full_response = re.sub(r'<[^>]+>', '', full_response)
        full_response = re.sub(r'\n{3,}', '\n\n', full_response)
        full_response = full_response.strip()
        
        # 保存对话历史到Redis
        new_session_id = None
        try:
            redis_client = get_redis_client()
            new_session_id, should_create_new = save_conversation_history(redis_client, session_id, query, full_response)
            
            # 如果达到10条，需要创建新会话
            if should_create_new and new_session_id:
                print(f"对话达到10条，自动创建新会话: {new_session_id}")
                # 发送新会话创建事件
                yield await send_event('new_session_created', {
                    'new_session_id': new_session_id,
                    'old_session_id': session_id,
                    'message': '对话达到10条，已自动创建新会话'
                })
        except Exception as e:
            print(f"保存对话历史失败: {str(e)}")
        
        # 发送最终结果
        now = datetime.datetime.now()
        time = now.strftime("%Y-%m-%d %H:%M:%S")
        yield await send_event('answer_complete', {
            'response': full_response,
            'status': 200,
            'time': time,
            'session_id': session_id,  # 当前回答仍属于旧会话
            'new_session_id': new_session_id if new_session_id else None,  # 如果创建了新会话，返回新的session_id供下次使用
            'new_session_created': new_session_id is not None,  # 标识是否创建了新会话
            'search_path': search_path,
            'search_stages': search_stages
        })
        
    except Exception as e:
        print(f'生成回答错误: {str(e)}')
        yield await send_event('answer_error', {
            'error': str(e),
            'message': f'生成回答失败: {str(e)}'
        })

