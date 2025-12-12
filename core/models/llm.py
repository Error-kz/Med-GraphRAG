"""
大语言模型封装
统一管理LLM相关功能
使用 OpenRouter 作为统一的 API 网关
"""
import os
import re
from openai import OpenAI
from config.settings import settings


def create_openrouter_client() -> OpenAI:
    """
    创建 OpenRouter 客户端
    
    Returns:
        OpenAI客户端实例（配置为 OpenRouter API）
    """
    client = OpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url='https://openrouter.ai/api/v1'
    )
    return client


# 保持向后兼容的别名
def create_deepseek_client() -> OpenAI:
    """
    创建 OpenRouter 客户端（向后兼容别名）
    
    Returns:
        OpenAI客户端实例（配置为 OpenRouter API）
    """
    return create_openrouter_client()


def generate_openrouter_answer(client: OpenAI, question: str, model: str = None) -> str:
    """
    使用 OpenRouter 生成答案
    
    Args:
        client: OpenRouter 客户端
        question: 问题文本
        model: 模型名称，如果为 None 则使用配置中的默认模型
        
    Returns:
        生成的答案（已清理Markdown格式）
    """
    if model is None:
        model = settings.OPENROUTER_LLM_MODEL
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是一个能力非常强大的助手。请使用纯文本格式回答，不要使用任何 Markdown 格式、HTML 标签或代码块。"
            },
            {"role": "user", "content": question},
        ],
        temperature=0.7,
        max_tokens=2048,
        stream=False,
    )
    
    content = response.choices[0].message.content
    
    # 后处理：移除可能的 Markdown 格式标记
    # 移除 Markdown 粗体 **text**
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    # 移除 Markdown 斜体 *text*
    content = re.sub(r'\*(.*?)\*', r'\1', content)
    # 移除 Markdown 标题 # ## ###
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    # 移除代码块标记 ```
    content = re.sub(r'```[\s\S]*?```', '', content)
    # 移除行内代码标记 `
    content = re.sub(r'`([^`]+)`', r'\1', content)
    # 移除 HTML 标签
    content = re.sub(r'<[^>]+>', '', content)
    # 移除多余的换行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()


# 保持向后兼容的别名
def generate_deepseek_answer(client: OpenAI, question: str) -> str:
    """
    使用 OpenRouter 生成答案（向后兼容别名）
    
    Args:
        client: OpenRouter 客户端
        question: 问题文本
        
    Returns:
        生成的答案（已清理Markdown格式）
    """
    return generate_openrouter_answer(client, question)

