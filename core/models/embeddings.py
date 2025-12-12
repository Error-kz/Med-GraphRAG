"""
统一的Embedding模型封装
智谱AI Embedding模型封装
"""
from langchain.embeddings.base import Embeddings
from zai import ZhipuAiClient
from config.settings import settings


class ZhipuAIEmbeddings(Embeddings):
    """
    智谱AI Embedding模型封装
    统一管理，避免在多个文件中重复定义
    """
    
    def __init__(self, client: ZhipuAiClient = None):
        """
        初始化Embedding模型
        
        Args:
            client: ZhipuAiClient实例，如果为None则自动创建
        """
        if client is None:
            self.client = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
        else:
            self.client = client
    
    def embed_documents(self, texts: list) -> list:
        """
        批量生成文档的嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self.client.embeddings.create(
                model='embedding-3',
                input=[text]
            )
            embeddings.append(embedding.data[0].embedding)
        return embeddings
    
    def embed_query(self, text: str) -> list:
        """
        生成查询文本的嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        return self.embed_documents([text])[0]


# OpenRouter Embedding 类（保留用于未来扩展）
class OpenRouterEmbeddings(Embeddings):
    """
    OpenRouter Embedding模型封装
    用于通过 OpenRouter 调用其他 Embedding 模型
    """
    
    def __init__(self, client=None, model: str = None):
        """
        初始化Embedding模型
        
        Args:
            client: OpenAI客户端实例（配置为OpenRouter），如果为None则自动创建
            model: Embedding模型名称，如果为None则使用配置中的默认模型
        """
        from openai import OpenAI
        if client is None:
            self.client = OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url='https://openrouter.ai/api/v1'
            )
        else:
            self.client = client
        
        self.model = model or settings.OPENROUTER_EMBEDDING_MODEL
    
    def embed_documents(self, texts: list) -> list:
        """
        批量生成文档的嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    
    def embed_query(self, text: str) -> list:
        """
        生成查询文本的嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        return self.embed_documents([text])[0]

