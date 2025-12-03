"""
Cypher查询验证器
验证Cypher查询的语法和模式
"""
import re
from typing import List, Tuple
from neo4j import GraphDatabase
from core.graph.schemas import GraphSchema


class CypherValidator:
    """Cypher查询验证器（使用Neo4j连接）"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """
        初始化验证器
        
        Args:
            neo4j_uri: Neo4j URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
        """
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def validate_syntax(self, cypher_query: str) -> Tuple[bool, List[str]]:
        """
        验证Cypher查询的语法
        
        Args:
            cypher_query: Cypher查询语句
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 基本语法检查
        if not cypher_query.strip().upper().startswith(('MATCH', 'CREATE', 'MERGE', 'CALL')):
            errors.append("查询必须以MATCH, CREATE, MERGE 或 CALL开头!!!")
        
        # 检查是否有潜在的注入风险
        if any(keyword in cypher_query.upper() for keyword in ['DROP', 'DELETE', 'DETACH', 'REMOVE']):
            if not any(keyword in cypher_query.upper() for keyword in ['DELETE', 'DETACH']):
                errors.append("查询包含可能危险的操作符 ")
        
        # 检查RETURN语句是否存在 (对于MATCH查询)
        if cypher_query.upper().startswith('MATCH') and 'RETURN' not in cypher_query.upper():
            errors.append("MATCH查询必须包含RETURN语句!!!")
        
        # 使用Neo4j解释计划验证查询
        try:
            with self.driver.session() as session:
                result = session.run(f"EXPLAIN {cypher_query}")
                # 如果解释成功, 语法基本正确
                return True, errors
        except Exception as e:
            errors.append(f"语法错误: {str(e)}")
            return False, errors
    
    def validate_against_schema(self, cypher_query: str, schema: GraphSchema) -> Tuple[bool, List[str]]:
        """
        根据模式验证查询
        
        Args:
            cypher_query: Cypher查询语句
            schema: 图模式
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 提取所有节点标签
        node_labels = [node.label for node in schema.nodes]
        # 匹配节点模式：(var:Label) 或 (:Label)，只提取有冒号的标签
        node_pattern = r'\(([a-zA-Z0-9_]+)?:([a-zA-Z0-9_]+)\)'
        matches = re.findall(node_pattern, cypher_query)
        
        for match in matches:
            # match[0] 是变量名（可选），match[1] 是节点标签（必须有冒号）
            node_label = match[1]
            if node_label and node_label not in node_labels:
                errors.append(f"使用了不存在的节点标签: {node_label}")
        
        # 提取所有关系类型
        rel_types = [rel.type for rel in schema.relationships]
        # 匹配关系模式：[var:Type] 或 [:Type]，只提取有冒号的类型
        rel_pattern = r'\[([a-zA-Z0-9_]+)?:([a-zA-Z0-9_]+)\]'
        rel_matches = re.findall(rel_pattern, cypher_query)
        
        for match in rel_matches:
            # match[0] 是变量名（可选），match[1] 是关系类型（必须有冒号）
            rel_type = match[1]
            if rel_type and rel_type not in rel_types:
                errors.append(f"使用了不存在的关系类型: {rel_type}")
        
        return len(errors) == 0, errors
    
    def close(self):
        """关闭Neo4j连接"""
        self.driver.close()


class RuleBasedValidator:
    """基于规则的验证器（当无法连接Neo4j时使用）"""
    
    def validate_against_schema(self, cypher_query: str, schema: GraphSchema) -> Tuple[bool, List[str]]:
        """
        根据模式验证查询（基于规则的验证）
        
        Args:
            cypher_query: Cypher查询语句
            schema: 图模式
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 检查基本结构
        if not cypher_query.strip():
            errors.append("查询不能为空!!!")
            return False, errors
        
        # 检查是否包含潜在危险操作
        dangerous_patterns = [
            (r'(?i)drop\s+', "DROP操作可能危险 "),
            (r'(?i)delete\s+', "DELETE操作需要谨慎 "),
            (r'(?i)detach\s+delete', "DETACH DELETE操作非常危险 "),
            (r'(?i)remove\s+', "REMOVE操作需要谨慎 "),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, cypher_query):
                errors.append(message)
        
        # 检查MATCH查询是否包含RETURN
        if re.match(r'(?i)match', cypher_query) and not re.search(r'(?i)return', cypher_query):
            errors.append("MATCH查询必须包含RETURN子句")
        
        # 检查CREATE查询是否合理
        if re.match(r'(?i)create', cypher_query) and not re.search(r'(?i)(node|relationship|label|index)', cypher_query):
            errors.append("CREATE查询应该明确创建节点或关系")
        
        # 提取所有节点标签
        node_labels = [node.label for node in schema.nodes]
        # 匹配节点模式：(var:Label) 或 (:Label)，只提取有冒号的标签
        node_pattern = r'\(([a-zA-Z0-9_]+)?:([a-zA-Z0-9_]+)\)'
        matches = re.findall(node_pattern, cypher_query)
        
        for match in matches:
            # match[0] 是变量名（可选），match[1] 是节点标签（必须有冒号）
            node_label = match[1]
            if node_label and node_label not in node_labels:
                errors.append(f"使用了不存在的节点标签: {node_label}")
        
        # 提取所有关系类型
        rel_types = [rel.type for rel in schema.relationships]
        # 匹配关系模式：[var:Type] 或 [:Type]，只提取有冒号的类型
        rel_pattern = r'\[([a-zA-Z0-9_]+)?:([a-zA-Z0-9_]+)\]'
        rel_matches = re.findall(rel_pattern, cypher_query)
        
        for match in rel_matches:
            # match[0] 是变量名（可选），match[1] 是关系类型（必须有冒号）
            rel_type = match[1]
            if rel_type and rel_type not in rel_types:
                errors.append(f"使用了不存在的关系类型: {rel_type}")
        
        return len(errors) == 0, errors

