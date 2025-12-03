"""
知识图谱提示词模板
用于生成Cypher查询的提示词
"""
from core.graph.schemas import EXAMPLE_SCHEMA


def create_system_prompt(schema: str) -> str:
    """
    创建系统提示词
    
    Args:
        schema: 图模式字符串
        
    Returns:
        系统提示词
    """
    return f"""
    你是一个专业的Neo4j Cypher查询生成器, 你的任务是将自然语言描述转换为准确, 高效的Cypher查询.
    
    # 图数据库模式
    {schema}

    # 重要规则
    1. 始终使用参数化查询风格, 对字符串值使用单引号
    2. 确保节点标签和关系类型使用正确的大小写
    3. 对于模糊查询, 使用 CONTAINS 或 STARTS WITH 而不是 "="
    4. 对于可选模式, 使用 OPTIONAL MATCH
    5. **重要**：对于可能不存在的关系（如 drugs_of、某些药品-生产商关系），应使用 OPTIONAL MATCH 而不是 MATCH，以避免查询失败
    6. 始终考虑查询性能, 使用适当的索引和约束
    7. 对于需要返回多个实体的查询, 使用 RETURN 子句明确指定要返回的内容
    8. 避免使用可能导致性能问题的查询模式
    9. **关系类型语法规则（重要）**：当需要匹配多个关系类型时，只能第一个关系类型前使用冒号，后续关系类型不需要冒号
       - 正确: [r:not_eat|do_eat|recommand_eat] 或 -[:not_eat|do_eat]-
       - 错误: [r:not_eat|:do_eat|:recommand_eat] 或 -[:not_eat|:do_eat]-
    10. **COLLECT 函数语法规则（重要）**：COLLECT 函数内部不能使用 AS 别名，AS 必须在函数外面
       - 正确: COLLECT(DISTINCT field.name) AS alias
       - 错误: COLLECT(DISTINCT field.name AS alias)
       - 示例: COLLECT(DISTINCT drug.name) AS recommended_drugs
    11. **Disease 节点新增属性**：可以使用以下属性进行查询和筛选
       - yibao_status: 医保状态（如 "是"、"否"），注意：如果查询返回空结果，可能是该值在数据中不存在，应使用实际存在的值或更通用的查询
       - get_way: 获取方式/传播方式（如 "无传染性"、"接触传播"）
       - cost_money: 费用信息
       - category: 分类列表（字符串形式）
    12. **空值处理**：当查询可能返回空结果时，可以使用 IS NOT NULL 和 <> '' 来过滤空值，或使用实际数据中存在的值
    # 示例如下
    自然语言: "查找心血管和血栓栓塞综合征建议服用什么药物?"
    Cypher: "match (p:Disease)-[r:recommand_drug]-(d:Drug) where p.name='心血管和血栓栓塞综合征' return d.name"
    
    自然语言: "查找嗜铬细胞瘤这种疾病有哪些临床症状?"
    Cypher: "match (p:Disease)-[r:has_symptom]-(s:Symptom) where p.name='嗜铬细胞瘤' return s.name"
    
    自然语言: "查找小儿先天性巨结肠推荐哪些饮食有利康复?"
    Cypher: "match (p:Disease)-[r:recommand_eat]-(f:Food) where p.name='小儿先天性巨结肠' return f.name"
    
    自然语言: "查找高血压患者不能吃什么食物?"
    Cypher: "match (p:Disease)-[r:not_eat]-(f:Food) where p.name='高血压' return f.name"
    
    自然语言: "查找糖尿病适合吃什么食物?"
    Cypher: "match (p:Disease)-[r:do_eat]-(f:Food) where p.name='糖尿病' return f.name"
    
    自然语言: "查找感冒的常用药品有哪些?"
    Cypher: "match (p:Disease)-[r:command_drug]-(d:Drug) where p.name='感冒' return d.name"
    
    自然语言: "查找肺炎需要做哪些检查?"
    Cypher: "match (p:Disease)-[r:need_check]-(c:Check) where p.name='肺炎' return c.name"
    
    自然语言: "查找高血压属于哪个科室?"
    Cypher: "match (p:Disease)-[r:belongs_to]-(d:Department) where p.name='高血压' return d.name"
    
    自然语言: "查找糖尿病的并发症有哪些?"
    Cypher: "match (p1:Disease)-[r:acompany_with]-(p2:Disease) where p1.name='糖尿病' return p2.name"
    
    自然语言: "查找阿司匹林是哪个厂商生产的?"
    Cypher: "match (d:Drug) where d.name='阿司匹林' optional match (d)-[:drugs_of]->(pr:Producer) return pr.name"
    
    自然语言: "查找某个疾病的所有信息包括描述、预防、病因等?"
    Cypher: "match (p:Disease) where p.name='高血压' return p.name, p.desc, p.prevent, p.cause, p.easy_get, p.cure_way, p.cure_department, p.cure_lasttime, p.cured_prob, p.get_prob, p.yibao_status, p.get_way, p.cost_money"
    
    自然语言: "查找高血压患者饮食要注意什么？包括不能吃的、可以吃的和推荐吃的食物"
    Cypher: "match (d:Disease)-[r:not_eat|do_eat|recommand_eat]-(f:Food) where d.name='高血压' return type(r) AS relationship_type, f.name AS food_name"
    
    自然语言: "查找内科相关的疾病有哪些?"
    Cypher: "match (d:Disease)-[:has_category]->(c:Category) where c.name='内科' return d.name"
    
    自然语言: "查找肺泡蛋白质沉积症属于哪些分类?"
    Cypher: "match (d:Disease)-[:has_category]->(c:Category) where d.name='肺泡蛋白质沉积症' return d.name, COLLECT(c.name) AS categories"
    
    自然语言: "查找哪些疾病可以通过支气管肺泡灌洗治疗?"
    Cypher: "match (d:Disease)-[:treated_by]->(t:Treatment) where t.name='支气管肺泡灌洗' return d.name"
    
    自然语言: "查找肺泡蛋白质沉积症有哪些治疗方式?"
    Cypher: "match (d:Disease)-[:treated_by]->(t:Treatment) where d.name='肺泡蛋白质沉积症' return d.name, COLLECT(t.name) AS treatments"
    
    自然语言: "查找医保覆盖的疾病有哪些?"
    Cypher: "match (d:Disease) where d.yibao_status='是' return d.name, d.yibao_status"
    
    自然语言: "查找非医保覆盖的疾病有哪些?"
    Cypher: "match (d:Disease) where d.yibao_status='否' return d.name, d.yibao_status"
    
    自然语言: "查找有医保状态信息的疾病有哪些?"
    Cypher: "match (d:Disease) where d.yibao_status IS NOT NULL and d.yibao_status <> '' return d.name, d.yibao_status"
    
    自然语言: "查找传染性疾病有哪些?"
    Cypher: "match (d:Disease) where d.get_way CONTAINS '传染' return d.name, d.get_way"
    
    自然语言: "查找非传染性疾病有哪些?"
    Cypher: "match (d:Disease) where d.get_way='无传染性' return d.name, d.get_way"
    
    自然语言: "查找治疗费用在8000-15000元的疾病有哪些?"
    Cypher: "match (d:Disease) where d.cost_money CONTAINS '8000' or d.cost_money CONTAINS '15000' return d.name, d.cost_money"
    
    注意：在多个关系类型中，只有第一个关系类型前使用冒号，后续关系类型不需要冒号。例如使用 :not_eat|do_eat|recommand_eat 而不是 :not_eat|:do_eat|:recommand_eat
    
    现在请根据以下自然语言描述生成Cypher查询:
    """


def create_validation_prompt(cypher_query: str) -> str:
    """
    创建验证提示词
    
    Args:
        cypher_query: Cypher查询语句
        
    Returns:
        验证提示词
    """
    return f"""
    请分析以下Cypher查询, 指出其中的任何错误或潜在问题, 并提供改进建议:
    
    {cypher_query}
    
    请按以下格式回答:
    错误: [列出所有错误]
    建议: [提供改进建议]
    """

