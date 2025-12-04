"""
主Agent服务
集成向量检索、知识图谱查询的医疗问答服务
基于Agent/agent2.py重构，使用新的模块结构
"""
import os
import re
import json
import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
from langchain_milvus import Milvus, BM25BuiltInFunction

from config.settings import settings
from config.neo4j_config import NEO4J_CONFIG
from core.models.embeddings import ZhipuAIEmbeddings
from core.models.llm import create_deepseek_client, generate_deepseek_answer
from zai import ZhipuAiClient
from neo4j import GraphDatabase

from .streaming_handler import chatbot_stream


# 设置环境变量
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 创建FastAPI应用
app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（前端页面）
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# 初始化Embedding模型
client_embedding = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
embedding_model = ZhipuAIEmbeddings(client_embedding)
print('embedding模型创建成功！！')

# 创建 Milvus 向量存储（基于JSON文本）
try:
    milvus_vectorstore = Milvus(
        embedding_function=embedding_model,
        builtin_function=BM25BuiltInFunction(),
        vector_field=['dense', 'sparse'],
        index_params=[
            {
                'metric_type': 'IP',
                'index_type': 'IVF_FLAT',
            },
            {
                'metric_type': 'BM25',
                'index_type': 'SPARSE_INVERTED_INDEX',
            }
        ],
        connection_args={'uri': settings.MILVUS_AGENT_DB}
    )
    retriever = milvus_vectorstore.as_retriever()
    print("创建Milvus向量检索器成功！！")
except Exception as e:
    error_msg = str(e)
    if "has been opened by another program" in error_msg or "Open local milvus failed" in error_msg:
        print("\n" + "=" * 60)
        print("❌ 错误：数据库文件正在被其他程序使用")
        print("=" * 60)
        print("\n可能的原因：")
        print("  1. 另一个 agent_service.py 实例正在运行")
        print("  2. create_vector.py 脚本正在运行")
        print("  3. 之前的连接未正确关闭")
        print("\n解决方法：")
        print("  1. 查找并停止正在运行的进程：")
        print("     ps aux | grep -E 'agent_service|create_vector'")
        print("     kill <进程ID>")
        print("  2. 等待几秒后重试")
        print("  3. 如果问题持续，检查是否有僵尸进程")
        print(f"\n数据库路径: {settings.MILVUS_AGENT_DB}")
        print("=" * 60)
        print("\n⚠️  服务启动失败，请解决数据库占用问题后重试")
        raise
    else:
        print(f"❌ Milvus连接失败: {error_msg}")
        raise

# 创建大语言模型客户端
client_llm = create_deepseek_client()
print('创建 DeepSeek 成功...')

# 初始化 Neo4j 驱动（用于知识图谱查询）
try:
    neo4j_driver = GraphDatabase.driver(
        NEO4J_CONFIG['uri'],
        auth=NEO4J_CONFIG['auth']
    )
    print('Neo4j 知识图谱连接成功...')
except Exception as e:
    neo4j_driver = None
    print(f'Neo4j 连接失败: {str(e)}，将跳过知识图谱查询')

# 知识图谱服务地址
GRAPH_API_URL = f'http://localhost:{settings.GRAPH_SERVICE_PORT}'
GRAPH_API_URL_BACKUP = f'http://0.0.0.0:{settings.GRAPH_SERVICE_PORT}'


def format_docs(docs):
    """格式化文档列表为字符串"""
    return "\n\n".join(doc.page_content for doc in docs)


@app.get("/")
async def root():
    """根路径，返回前端页面或服务信息"""
    web_file = web_dir / "index.html"
    if web_file.exists():
        return FileResponse(str(web_file))
    return {
        "service": "医学助手 Agent 服务",
        "status": "运行中",
        "version": "1.0",
        "endpoints": {
            "GET /": "前端页面（如果存在）或服务信息",
            "POST /": "医学问答接口，需要传递 {'question': '你的问题'}"
        },
        "port": settings.AGENT_SERVICE_PORT
    }

@app.get("/api/info")
async def api_info():
    """API信息接口"""
    return {
        "service": "医学助手 Agent 服务",
        "status": "运行中",
        "version": "1.0",
        "endpoints": {
            "GET /": "前端页面",
            "POST /": "医学问答接口，需要传递 {'question': '你的问题'}",
            "GET /api/info": "API信息"
        },
        "port": settings.AGENT_SERVICE_PORT
    }

@app.post("/")
async def chatbot(request: Request):
    """
    医疗问答主接口（兼容旧版本，返回完整结果）
    集成向量检索、知识图谱查询
    """
    json_post_raw = await request.json()
    json_post = json.dumps(json_post_raw)
    json_post_list = json.loads(json_post)
    query = json_post_list.get('question')
    
    # 检查是否请求流式输出
    use_stream = json_post_list.get('stream', False)
    
    if use_stream:
        # 返回流式响应
        return StreamingResponse(
            chatbot_stream(
                query=query,
                milvus_vectorstore=milvus_vectorstore,
                client_llm=client_llm,
                graph_api_url=GRAPH_API_URL,
                graph_api_url_backup=GRAPH_API_URL_BACKUP,
                format_docs_func=format_docs
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # 初始化搜索路径和结果追踪
    search_path = []
    search_stages = {
        'milvus_vector': {'status': 'pending', 'results': [], 'count': 0, 'description': '向量数据库检索'},
        'knowledge_graph': {'status': 'pending', 'results': [], 'count': 0, 'description': '知识图谱查询', 'cypher_query': '', 'confidence': 0}
    }

    # 1、向量数据库检索
    try:
        recall_rerank_milvus = milvus_vectorstore.similarity_search(
            query,
            k=10,
            ranker_type='rrf',
            ranker_params={'k': 100}
        )
        
        if recall_rerank_milvus:
            context = format_docs(recall_rerank_milvus)
            search_stages['milvus_vector']['status'] = 'success'
            search_stages['milvus_vector']['count'] = len(recall_rerank_milvus)
            search_stages['milvus_vector']['results'] = [
                doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content
                for doc in recall_rerank_milvus[:3]
            ]
            search_path.append('milvus_vector')
        else:
            context = ""
            search_stages['milvus_vector']['status'] = 'empty'
    except Exception as e:
        context = ""
        search_stages['milvus_vector']['status'] = 'error'
        search_stages['milvus_vector']['error'] = str(e)
        print(f'向量检索错误: {str(e)}')

    # 2、知识图谱查询
    graph_context = ""
    current_api_url = GRAPH_API_URL
    
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
            print(f'⚠️ 主地址连接失败，尝试备用地址: {GRAPH_API_URL_BACKUP}')
            current_api_url = GRAPH_API_URL_BACKUP
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
                                
    except requests.exceptions.Timeout as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'请求超时: {str(e)}'
        print(f'⚠️ 知识图谱服务请求超时: {str(e)}')
    except requests.exceptions.ConnectionError as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'连接失败: {str(e)}'
        print(f'⚠️ 知识图谱服务连接失败: {str(e)}')
    except Exception as e:
        search_stages['knowledge_graph']['status'] = 'error'
        search_stages['knowledge_graph']['error'] = f'查询异常: {str(e)}'
        print(f'⚠️ 知识图谱查询异常: {str(e)}')
    
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

    # 使用 DeepSeek 模型生成回复
    response = generate_deepseek_answer(client_llm, SYSTEM_PROMPT + USER_PROMPT)

    now = datetime.datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")
    answer = {
        'response': response,
        'status': 200,
        'time': time,
        'search_path': search_path,
        'search_stages': search_stages
    }
    return answer


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.AGENT_SERVICE_PORT, workers=1)

