"""
主配置文件
统一管理所有配置项，支持环境变量
"""
import os
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class Settings:
    """应用配置类"""
    
    # ========== API Keys ==========
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-28cb551d7d7444be8a5cb39664be4942")
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "572a40052210412586393a62b15136ae.NWU8EZVlZXjcQfVN")
    
    # ========== Neo4j配置 ==========
    NEO4J_URI: str = os.getenv("NEO4J_URI", "neo4j://0.0.0.0:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "12345678")
    NEO4J_ENCRYPTED: bool = os.getenv("NEO4J_ENCRYPTED", "False").lower() == "true"
    
    # ========== Redis配置 ==========
    REDIS_HOST: str = os.getenv("REDIS_HOST", "0.0.0.0")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    
    # ========== Milvus配置 ==========
    MILVUS_AGENT_DB: str = str(PROJECT_ROOT / "storage" / "databases" / "milvus_agent.db")
    PDF_AGENT_DB: str = str(PROJECT_ROOT / "storage" / "databases" / "pdf_agent.db")
    
    # ========== 服务端口配置 ==========
    AGENT_SERVICE_PORT: int = int(os.getenv("AGENT_SERVICE_PORT", "8103"))
    GRAPH_SERVICE_PORT: int = int(os.getenv("GRAPH_SERVICE_PORT", "8101"))
    RED_SPIDER_SERVICE_PORT: int = int(os.getenv("RED_SPIDER_SERVICE_PORT", "5001"))
    
    # ========== 模型路径配置 ==========
    MODEL_BASE_PATH: str = str(PROJECT_ROOT / "storage" / "models")
    
    # ========== 数据路径配置 ==========
    DATA_RAW_PATH: str = str(PROJECT_ROOT / "data" / "raw")
    DATA_PROCESSED_PATH: str = str(PROJECT_ROOT / "data" / "processed")
    DATA_DICT_PATH: str = str(PROJECT_ROOT / "data" / "dict")
    
    # ========== 日志配置 ==========
    LOG_DIR: str = str(PROJECT_ROOT / "storage" / "logs")
    GRAPH_QUERY_LOG: str = str(PROJECT_ROOT / "storage" / "logs" / "graph_query.log")
    
    # ========== 其他配置 ==========
    TOKENIZERS_PARALLELISM: bool = False  # 禁用tokenizer并行，避免警告


# 创建全局配置实例
settings = Settings()

# 设置环境变量
os.environ["TOKENIZERS_PARALLELISM"] = "false"
if settings.DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY

