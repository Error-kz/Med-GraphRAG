"""
Neo4j客户端封装
提供Neo4j数据库连接和基本操作
"""
from neo4j import GraphDatabase
from config.neo4j_config import NEO4J_CONFIG
from typing import Optional


class Neo4jClient:
    """Neo4j客户端封装类"""
    
    def __init__(self, uri: str = None, auth: tuple = None):
        """
        初始化Neo4j客户端
        
        Args:
            uri: Neo4j URI，如果为None则使用配置中的值
            auth: (用户名, 密码)元组，如果为None则使用配置中的值
        """
        if uri is None:
            uri = NEO4J_CONFIG['uri']
        if auth is None:
            auth = NEO4J_CONFIG['auth']
        
        self.uri = uri
        self.auth = auth
        self.driver: Optional[GraphDatabase.driver] = None
    
    def connect(self):
        """建立Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=self.auth,
                max_connection_lifetime=1000
            )
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            print('Neo4j 知识图谱连接成功...')
            return True
        except Exception as e:
            print(f'Neo4j 连接失败: {str(e)}')
            self.driver = None
            return False
    
    def execute_query(self, query: str):
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询语句
            
        Returns:
            查询结果
        """
        if not self.driver:
            raise ConnectionError("Neo4j连接未建立，请先调用connect()方法")
        
        with self.driver.session() as session:
            result = session.run(query)
            return list(result)
    
    def close(self):
        """关闭Neo4j连接"""
        if self.driver:
            self.driver.close()
            self.driver = None

