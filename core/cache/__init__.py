"""
缓存模块
Redis缓存相关功能
"""
from core.cache.redis_client import get_redis_client, cache_set, cache_get

__all__ = ['get_redis_client', 'cache_set', 'cache_get']

