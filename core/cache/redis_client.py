"""
Redis缓存客户端
统一管理Redis连接和缓存操作
"""
import redis
from config.settings import settings


def get_redis_client() -> redis.Redis:
    """
    创建Redis客户端连接池
    
    Returns:
        Redis客户端实例
    """
    pool = redis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        max_connections=settings.REDIS_MAX_CONNECTIONS
    )
    r = redis.Redis(connection_pool=pool)
    
    # 测试连接
    try:
        r.ping()
        print("Redis连接成功")
    except redis.exceptions.ConnectionError:
        print("Redis连接失败")
    
    return r


def cache_set(r: redis.Redis, question: str, answer: str, expire: int = 3600):
    """
    将问答对保存到Redis数据库
    
    Args:
        r: Redis客户端实例
        question: 问题
        answer: 答案
        expire: 过期时间（秒），默认3600秒
    """
    r.hset('qa', question, answer)
    r.expire('qa', expire)


def cache_get(r: redis.Redis, question: str) -> bytes:
    """
    通过问题获取答案
    
    Args:
        r: Redis客户端实例
        question: 问题
        
    Returns:
        答案（bytes类型），如果不存在返回None
    """
    return r.hget('qa', question)

