"""
主配置文件
统一管理所有配置项，支持从 .env 文件或环境变量加载
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# .env 文件路径
ENV_FILE = PROJECT_ROOT / ".env"

# 加载 .env 文件（如果存在）
# override=True 表示环境变量优先于 .env 文件中的值
# 这样可以支持在运行时通过环境变量覆盖配置
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)
    print(f"✅ 已加载配置文件: {ENV_FILE}")
else:
    print(f"⚠️  未找到 .env 文件: {ENV_FILE}，将使用环境变量或默认值")


class Settings:
    """
    应用配置类
    所有配置优先从 .env 文件加载，如果 .env 中不存在则从系统环境变量读取
    如果都不存在，则使用默认值（如果有）
    """
    
    # ========== API Keys ==========
    # 从 .env 文件或环境变量加载，如果不存在则为 None
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    ZHIPU_API_KEY: Optional[str] = os.getenv("ZHIPU_API_KEY")
    
    # ========== Neo4j配置 ==========
    NEO4J_URI: str = os.getenv("NEO4J_URI")
    NEO4J_USER: str = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD")
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

# 设置环境变量（供其他库使用）
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 验证必要的 API Key 是否已配置
if not settings.ZHIPU_API_KEY:
    print("⚠️  警告: ZHIPU_API_KEY 未配置，Embedding 功能可能无法使用")
if not settings.DEEPSEEK_API_KEY:
    print("⚠️  警告: DEEPSEEK_API_KEY 未配置，LLM 功能可能无法使用")

# 如果配置了 API Key，设置到环境变量中（供其他库使用）
if settings.DEEPSEEK_API_KEY:
    os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY
if settings.ZHIPU_API_KEY:
    os.environ["ZHIPU_API_KEY"] = settings.ZHIPU_API_KEY

