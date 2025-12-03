"""
创建Milvus向量数据库
将JSON文件数据导入到milvus_agent.db向量数据库中
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径，以便导入项目模块
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import time
from tqdm import tqdm
from langchain_core.documents import Document
from langchain_milvus import Milvus, BM25BuiltInFunction

from config.settings import settings
from core.models.embeddings import ZhipuAIEmbeddings
from core.cache.redis_client import get_redis_client, cache_set, cache_get
from utils.document_loader import prepare_document
from zai import ZhipuAiClient


class MilvusVectorBuilder:
    """
    Milvus向量数据库构建器
    用于将文档数据导入到milvus_agent.db向量数据库
    """
    
    def __init__(self, embedding_model: ZhipuAIEmbeddings = None, uri: str = None):
        """
        初始化向量数据库构建器
        
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
            docs: 文档列表（LangChain Document对象）
            
        Returns:
            Milvus向量存储实例
        """
        if not docs:
            raise ValueError("文档列表不能为空")
        
        print(f"开始创建向量数据库，共 {len(docs)} 条文档...")
        
        # 初始化前10个文档创建向量存储
        init_docs = docs[:10] if len(docs) >= 10 else docs
        
        print("正在初始化向量存储...")
        try:
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
            print('✅ 已初始化创建 Milvus 向量存储')
        except Exception as e:
            error_msg = str(e)
            if "has been opened by another program" in error_msg or "Open local milvus failed" in error_msg:
                print("\n" + "=" * 60)
                print("❌ 数据库连接失败：数据库文件正在被其他程序使用")
                print("=" * 60)
                print("\n可能的原因：")
                print("  1. agent_service.py 正在运行中")
                print("  2. 另一个脚本正在使用该数据库")
                print("  3. 之前的连接未正确关闭")
                print("\n解决方法：")
                print("  1. 停止正在运行的 agent_service.py 服务：")
                print("     ps aux | grep agent_service")
                print("     kill <进程ID>")
                print("  2. 等待几秒后重试")
                print("  3. 如果问题持续，可以重启终端或检查是否有僵尸进程")
                print(f"\n数据库路径: {self.URI}")
                print("=" * 60)
            raise
        
        # 批量添加剩余文档
        if len(docs) > 10:
            count = 10
            temp = []
            
            for doc in tqdm(docs[10:], desc="添加文档到Milvus"):
                temp.append(doc)
                if len(temp) >= 5:
                    self.vectorstore.add_documents(temp)
                    count += len(temp)
                    temp = []
                    print(f'已插入 {count} 条数据...')
                    time.sleep(1)  # 避免请求过快
            
            # 添加剩余的文档
            if temp:
                self.vectorstore.add_documents(temp)
                count += len(temp)
            
            print(f'✅ 总共插入 {count} 条数据')
        else:
            print(f'✅ 总共插入 {len(docs)} 条数据')
        
        print('✅ 已创建 Milvus 索引完成！')
        
        return self.vectorstore


def build_milvus_database(file_paths: list = None, uri: str = None):
    """
    构建Milvus向量数据库的便捷函数
    
    Args:
        file_paths: JSONL文件路径列表，默认使用配置中的数据路径
        uri: Milvus数据库URI，默认使用配置中的MILVUS_AGENT_DB
        
    Returns:
        Milvus向量存储实例
    """
    # 加载文档
    print("=" * 60)
    print("开始构建 Milvus 向量数据库")
    print("=" * 60)
    
    print("\n[步骤1] 加载JSON文档...")
    docs = prepare_document(file_paths)
    
    if not docs:
        print("❌ 未加载到任何文档，请检查文件路径")
        return None
    
    print(f"✅ 成功加载 {len(docs)} 条文档")
    
    # 创建向量存储
    print("\n[步骤2] 创建向量存储...")
    builder = MilvusVectorBuilder(uri=uri)
    vectorstore = builder.create_vector_store(docs)
    
    print("\n" + "=" * 60)
    print("✅ 向量数据库构建完成！")
    print("=" * 60)
    print(f"\n数据库路径: {builder.URI}")
    print("可以开始使用向量检索功能了！")
    
    return vectorstore


def main():
    """主函数，用于命令行执行"""
    try:
        vectorstore = build_milvus_database(
            file_paths=[f'{settings.DATA_RAW_PATH}/data.jsonl']

        )
        if vectorstore:
            print("\n✅ 全部初始化完成，可以开始问答了！")
    except Exception as e:
        error_msg = str(e)
        if "has been opened by another program" in error_msg or "Open local milvus failed" in error_msg:
            # 已经在 create_vector_store 中处理了，这里不需要重复打印
            pass
        else:
            print(f"\n❌ 构建失败: {error_msg}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
