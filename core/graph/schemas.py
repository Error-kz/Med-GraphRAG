"""
知识图谱模式定义
定义Neo4j图数据库的节点和关系模式
"""
from pydantic import BaseModel
from typing import Dict, List


class NodeSchema(BaseModel):
    """节点模式定义"""
    label: str
    properties: Dict[str, str]


class RelationshipSchema(BaseModel):
    """关系模式定义"""
    from_node: str
    to_node: str
    type: str
    properties: Dict[str, str]


class GraphSchema(BaseModel):
    """图模式定义"""
    nodes: List[NodeSchema]
    relationships: List[RelationshipSchema]


# 示例图模型
EXAMPLE_SCHEMA = GraphSchema(
    # 节点的名称一定要严格保持跟neo4j一致
    nodes=[
        NodeSchema(
            label="Disease",
            properties={
                "name": "string",
                "desc": "string",
                "prevent": "string",
                "cause": "string",
                "easy_get": "string",
                "cure_way": "string",
                "cure_department": "string",
                "cure_lasttime": "string",
                "cured_prob": "string",
                "get_prob": "string",
                "yibao_status": "string",
                "get_way": "string",
                "cost_money": "string",
                "category": "string"
            }
        ),
        NodeSchema(label="Drug", properties={"name": "string"}),
        NodeSchema(label="Food", properties={"name": "string"}),
        NodeSchema(label="Symptom", properties={"name": "string"}),
        NodeSchema(label="Check", properties={"name": "string"}),
        NodeSchema(label="Department", properties={"name": "string"}),
        NodeSchema(label="Producer", properties={"name": "string"}),
        NodeSchema(label="Category", properties={"name": "string"}),
        NodeSchema(label="Treatment", properties={"name": "string"})
    ],
    # 关系的相关字段一定严格保持跟neo4j一致
    relationships=[
        RelationshipSchema(
            type='has_symptom',
            from_node='Disease',
            to_node='Symptom',
            properties={}
        ),
        RelationshipSchema(
            type='recommand_drug',
            from_node='Disease',
            to_node='Drug',
            properties={}
        ),
        RelationshipSchema(
            type='recommand_eat',
            from_node='Disease',
            to_node='Food',
            properties={}
        ),
        RelationshipSchema(
            type='not_eat',
            from_node='Disease',
            to_node='Food',
            properties={}
        ),
        RelationshipSchema(
            type='do_eat',
            from_node='Disease',
            to_node='Food',
            properties={}
        ),
        RelationshipSchema(
            type='command_drug',
            from_node='Disease',
            to_node='Drug',
            properties={}
        ),
        RelationshipSchema(
            type='drugs_of',
            from_node='Drug',
            to_node='Producer',
            properties={}
        ),
        RelationshipSchema(
            type='need_check',
            from_node='Disease',
            to_node='Check',
            properties={}
        ),
        RelationshipSchema(
            type='acompany_with',
            from_node='Disease',
            to_node='Disease',
            properties={}
        ),
        RelationshipSchema(
            type='belongs_to',
            from_node='Disease',
            to_node='Department',
            properties={}
        ),
        RelationshipSchema(
            type='sub_department',
            from_node='Department',
            to_node='Department',
            properties={}
        ),
        RelationshipSchema(
            type='has_category',
            from_node='Disease',
            to_node='Category',
            properties={}
        ),
        RelationshipSchema(
            type='treated_by',
            from_node='Disease',
            to_node='Treatment',
            properties={}
        ),
    ]
)

