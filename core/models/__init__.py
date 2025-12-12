"""
模型模块
包含Embedding模型和LLM模型
"""
from core.models.embeddings import ZhipuAIEmbeddings, OpenRouterEmbeddings
from core.models.llm import (
    create_openrouter_client, 
    create_deepseek_client,  # 向后兼容别名
    generate_openrouter_answer,
    generate_deepseek_answer  # 向后兼容别名
)

__all__ = [
    'ZhipuAIEmbeddings',
    'OpenRouterEmbeddings',
    'create_openrouter_client',
    'create_deepseek_client',  # 向后兼容别名
    'generate_openrouter_answer',
    'generate_deepseek_answer'  # 向后兼容别名
]

