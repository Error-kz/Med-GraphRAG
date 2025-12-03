"""
Milvus向量存储客户端
封装Milvus向量数据库操作
"""
from tqdm import tqdm
import time
from langchain_core.documents import Document
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import ParentDocumentRetriever
from core.models.embeddings import ZhipuAIEmbeddings
from config.settings import settings
from zai import ZhipuAiClient


class MilvusVectorStore:
    """
    Milvus向量存储类
    用于创建和管理Milvus向量数据库
    """
    
    def __init__(self, embedding_model: ZhipuAIEmbeddings = None, uri: str = None):
        """
        初始化Milvus向量存储
        
        Args:
            embedding_model: Embedding模型实例，如果为None则自动创建
            uri: Milvus数据库URI，如果为None则使用配置中的默认值
        """
        if embedding_model is None:
            client = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
            self.embeddings = ZhipuAIEmbeddings(client)
        else:
            self.embeddings = embedding_model
        
        self.URI = uri or settings.MILVUS_AGENT_DB
        
        # 定义索引类型
        self.dense_index = {
            'metric_type': 'IP',
            'index_type': 'IVF_FLAT',
        }
        self.sparse_index = {
            'metric_type': 'BM25',
            'index_type': 'SPARSE_INVERTED_INDEX'
        }
    
    def create_vector_store(self, docs: list):
        """
        创建向量存储并添加文档
        
        Args:
            docs: 文档列表
            
        Returns:
            Milvus向量存储实例
        """
        # 初始化前10个文档
        init_docs = docs[:10]
        self.vectorstore = Milvus.from_documents(
            documents=init_docs,
            embedding=self.embeddings,
            builtin_function=BM25BuiltInFunction(),
            index_params=[self.dense_index, self.sparse_index],
            vector_field=['dense', 'sparse'],
            connection_args={'uri': self.URI},
            consistency_level='Bounded',
            drop_old=False,
        )
        
        print('已初始化创建 Milvus !!')
        
        # 批量添加剩余文档
        count = 10
        temp = []
        for doc in tqdm(docs[10:], desc="添加文档到Milvus"):
            temp.append(doc)
            if len(temp) >= 5:
                self.vectorstore.add_documents(temp)
                count += len(temp)
                temp = []
                print(f'已插入{count}条数据...')
                time.sleep(1)
        
        # 添加剩余的文档
        if temp:
            self.vectorstore.add_documents(temp)
            count += len(temp)
        
        print(f'总共插入 {count} 条数据.....')
        print('已创建 Milvus 索引完成！！！')
        
        return self.vectorstore

