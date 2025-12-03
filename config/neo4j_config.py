"""
Neo4j数据库配置
"""
from config.settings import settings

NEO4J_CONFIG = {
    'uri': settings.NEO4J_URI,
    'auth': (settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    'encrypted': settings.NEO4J_ENCRYPTED
}

