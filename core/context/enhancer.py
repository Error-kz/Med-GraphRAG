"""
上下文增强器
分析用户问题是否依赖上下文，并从历史对话中提取主题实体来增强问题
"""
import re
import json
from typing import List, Dict, Optional, Tuple
from core.models.llm import create_openrouter_client


def has_reference_pronouns(query: str) -> bool:
    """
    检测问题是否包含指代性词语（如"有什么"、"怎么"、"如何"等）
    
    Args:
        query: 用户问题
        
    Returns:
        bool: 如果包含指代性词语返回True，否则返回False
    """
    # 指代性词语模式
    reference_patterns = [
        r'有什么',
        r'怎么',
        r'如何',
        r'怎样',
        r'哪些',
        r'什么',
        r'这个',
        r'那个',
        r'它',
        r'它们',
        r'该',
        r'此',
        r'上述',
        r'前面',
        r'之前',
        r'刚才',
        r'还',
        r'也',
        r'又',
        r'再',
        r'继续',
        r'更多',
        r'其他',
        r'别的',
        r'另外',
    ]
    
    # 检查是否包含指代性词语
    for pattern in reference_patterns:
        if re.search(pattern, query):
            return True
    
    return False


def extract_entities_from_history(history: List[Dict[str, str]], max_history: int = 5) -> Dict[str, List[str]]:
    """
    从对话历史中提取主题实体（疾病、症状、药物等）
    使用大模型进行智能提取
    
    Args:
        history: 对话历史列表，每个元素包含 question, answer, timestamp
        max_history: 最多使用最近几条历史记录，默认5条
        
    Returns:
        dict: 包含提取的实体信息
            - diseases: 疾病列表
            - symptoms: 症状列表
            - drugs: 药物列表
            - topics: 主题关键词列表
    """
    # 只使用最近的历史记录
    recent_history = history[-max_history:] if len(history) > max_history else history
    
    entities = {
        'diseases': [],
        'symptoms': [],
        'drugs': [],
        'topics': []
    }
    
    if not recent_history:
        return entities
    
    try:
        # 使用大模型提取主题实体
        client = create_openrouter_client()
        
        # 构建对话历史文本
        history_text = ""
        for i, record in enumerate(recent_history, 1):
            question = record.get('question', '')
            answer = record.get('answer', '')
            # 只取答案的前100字，避免过长
            answer_short = answer[:100] + '...' if len(answer) > 100 else answer
            history_text += f"问题{i}: {question}\n回答{i}: {answer_short}\n\n"
        
        # 构建提示词
        system_prompt = """你是一个医学信息提取专家。请从对话历史中提取主要的医学主题实体。

要求：
1. 提取对话中讨论的主要疾病名称（如：感冒、高血压、糖尿病等）
2. 提取主要症状（如果有）
3. 提取主要药物（如果有）
4. 提取对话的核心主题关键词（通常是疾病或症状名称）

请以JSON格式返回结果，格式如下：
{
    "main_topic": "主要主题（疾病或症状名称，2-4个字）",
    "diseases": ["疾病1", "疾病2"],
    "symptoms": ["症状1", "症状2"],
    "drugs": ["药物1", "药物2"]
}

如果某个类别没有找到，返回空数组。main_topic 必须是最核心的主题，通常是第一个问题中提到的疾病或症状名称。"""

        user_prompt = f"""请从以下对话历史中提取医学主题实体：

{history_text}

请提取对话的核心主题，并以JSON格式返回。"""
        
        # 调用大模型
        from config.settings import settings
        response = client.chat.completions.create(
            model=settings.OPENROUTER_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # 使用较低温度，提高准确性
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 尝试解析JSON结果
        # 移除可能的markdown代码块标记
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        result_text = result_text.strip()
        
        # 尝试提取JSON部分（支持多行）
        json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(0)
        
        # 解析JSON
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试更宽松的提取
            # 查找第一个 { 到最后一个 } 之间的内容
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                result_text = result_text[start_idx:end_idx+1]
                result = json.loads(result_text)
            else:
                raise
        
        # 填充实体信息
        if result.get('main_topic'):
            entities['topics'] = [result['main_topic']]
        
        if result.get('diseases'):
            entities['diseases'] = result['diseases']
            # 如果没有主题，使用第一个疾病作为主题
            if not entities['topics']:
                entities['topics'] = [result['diseases'][0]]
        
        if result.get('symptoms'):
            entities['symptoms'] = result['symptoms']
        
        if result.get('drugs'):
            entities['drugs'] = result['drugs']
        
    except Exception as e:
        # 如果大模型提取失败，使用简单的回退策略
        print(f"⚠️ 大模型提取失败，使用简单策略: {str(e)}")
        
        # 回退策略：从第一个问题中提取主题
        first_question = recent_history[0].get('question', '')
        if first_question:
            # 从问题开头提取2-4字的名词短语
            stop_words = ['的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', 
                         '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', 
                         '好', '自己', '这', '什么', '怎么', '如何', '哪些', '应该', '可以', '需要',
                         '患者', '注意', '饮食', '治疗', '预防', '症状', '表现', '感觉']
            
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', first_question)
            meaningful_words = [w for w in words if w not in stop_words and len(w) >= 2]
            
            if meaningful_words:
                main_topic = meaningful_words[0]
                entities['topics'] = [main_topic]
                
                # 根据关键词判断实体类型
                if any(keyword in main_topic for keyword in ['病', '症', '炎', '癌', '瘤']):
                    entities['diseases'] = [main_topic]
                elif any(keyword in main_topic for keyword in ['症状', '表现', '感觉', '疼', '痛']):
                    entities['symptoms'] = [main_topic]
    
    return entities


def enhance_query_with_context(
    query: str, 
    history: List[Dict[str, str]], 
    max_history: int = 5
) -> Tuple[str, bool]:
    """
    根据对话历史增强用户问题
    使用大模型智能判断是否需要增强以及如何增强
    
    Args:
        query: 用户当前问题
        history: 对话历史列表
        max_history: 最多使用最近几条历史记录，默认5条
        
    Returns:
        tuple: (enhanced_query, was_enhanced)
            - enhanced_query: 增强后的问题
            - was_enhanced: 是否进行了增强
    """
    # 如果没有历史记录，直接返回原问题
    if not history:
        return query, False
    
    try:
        # 使用大模型进行智能增强
        client = create_openrouter_client()
        
        # 只使用最近的历史记录
        recent_history = history[-max_history:] if len(history) > max_history else history
        
        # 构建对话历史文本
        history_text = ""
        for i, record in enumerate(recent_history, 1):
            question = record.get('question', '')
            answer = record.get('answer', '')
            # 只取答案的前100字，避免过长
            answer_short = answer[:100] + '...' if len(answer) > 100 else answer
            history_text += f"问题{i}: {question}\n回答{i}: {answer_short}\n\n"
        
        # 构建提示词
        system_prompt = """你是一个医学对话理解专家。请分析用户当前问题是否依赖对话历史中的上下文信息。

任务：
1. 判断当前问题是否包含指代性词语（如"有什么"、"怎么"、"如何"、"这个"、"那个"等），需要依赖上下文才能理解
2. 如果问题完整且不依赖上下文，返回原问题
3. 如果需要增强，从对话历史中提取核心主题（通常是疾病或症状名称），将主题补充到问题中

要求：
- 如果问题已经包含主题实体（如"感冒有什么症状？"），不需要增强
- 如果问题包含指代但历史中没有明确主题，返回原问题
- 增强后的问题应该自然、完整、易于理解

请以JSON格式返回结果：
{
    "need_enhance": true/false,
    "enhanced_query": "增强后的问题（如果需要增强）",
    "reason": "增强原因或说明"
}

如果不需要增强，enhanced_query 应该等于原问题。"""

        user_prompt = f"""请分析以下情况：

对话历史：
{history_text}

当前问题：{query}

请判断是否需要增强问题，如果需要，请从对话历史中提取核心主题并补充到问题中。

示例：
- 如果历史中讨论的是"感冒"，当前问题是"有什么特效药？"，应该增强为"感冒有什么特效药？"
- 如果当前问题是"感冒了有什么症状？"，已经包含主题，不需要增强
- 如果历史中没有明确的主题，返回原问题

请以JSON格式返回结果。"""
        
        # 调用大模型
        from config.settings import settings
        response = client.chat.completions.create(
            model=settings.OPENROUTER_LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # 使用较低温度，提高准确性
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 尝试解析JSON结果
        # 移除可能的markdown代码块标记
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        result_text = result_text.strip()
        
        # 尝试提取JSON部分（支持多行）
        json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(0)
        
        # 解析JSON
        try:
            result = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果解析失败，尝试更宽松的提取
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                result_text = result_text[start_idx:end_idx+1]
                result = json.loads(result_text)
            else:
                raise
        
        # 处理结果
        if result.get('need_enhance', False) and result.get('enhanced_query'):
            enhanced_query = result['enhanced_query'].strip()
            # 验证增强后的问题是否合理
            if enhanced_query and enhanced_query != query:
                print(f"✅ 问题已增强: {query} -> {enhanced_query}")
                if result.get('reason'):
                    print(f"   原因: {result['reason']}")
                return enhanced_query, True
        
        # 不需要增强或增强失败，返回原问题
        return query, False
        
    except Exception as e:
        # 如果大模型增强失败，使用简单的回退策略
        print(f"⚠️ 大模型增强失败，使用简单策略: {str(e)}")
        
        # 回退策略：简单的指代检测和主题提取
        if not has_reference_pronouns(query):
            return query, False
        
        # 从历史中提取实体
        entities = extract_entities_from_history(history, max_history)
        
        # 优先使用疾病名称，如果没有则使用主题关键词
        main_topic = None
        if entities['diseases']:
            main_topic = entities['diseases'][0]
        elif entities['topics']:
            main_topic = entities['topics'][0]
        elif entities['symptoms']:
            main_topic = entities['symptoms'][0]
        
        # 如果找到了主题，增强问题
        if main_topic:
            # 检查问题是否已经包含主题（避免重复）
            if main_topic in query:
                return query, False
            
            # 清理主题
            main_topic = main_topic.strip()
            if len(main_topic) < 2 or len(main_topic) > 10:
                return query, False
            
            # 根据问题类型增强
            if '有什么' in query or '哪些' in query:
                enhanced = f"{main_topic}{query}"
            elif '怎么' in query or '如何' in query or '怎样' in query:
                enhanced = f"{main_topic}{query}"
            elif '什么' in query:
                enhanced = f"{main_topic}{query}"
            else:
                enhanced = f"{main_topic}，{query}"
            
            return enhanced, True
        
        return query, False

