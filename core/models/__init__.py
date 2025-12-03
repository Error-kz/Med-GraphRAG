"""
模型模块
包含Embedding模型和LLM模型
"""
from core.models.embeddings import ZhipuAIEmbeddings
from core.models.llm import create_deepseek_client, generate_deepseek_answer

__all__ = [
    'ZhipuAIEmbeddings',
    'create_deepseek_client',
    'generate_deepseek_answer'
]

