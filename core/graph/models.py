"""
知识图谱数据模型
定义API请求和响应的数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class QueryType(str, Enum):
    """查询类型枚举"""
    MATCH = "MATCH"
    CREATE = "CREATE"
    MERGE = "MERGE"
    DELETE = "DELETE"
    SET = "SET"
    REMOVE = "REMOVE"


class NL2CypherRequest(BaseModel):
    """自然语言转Cypher请求模型"""
    natural_language_query: str = Field(
        description="自然语言描述需求",
        examples=["查找'心血管和血栓栓塞综合征'建议服用什么药物?"]
    )
    
    query_type: Optional[QueryType] = Field(
        default=None,
        description="指定查询类型,如果不指定则由模型推断"
    )
    
    limit: Optional[int] = Field(
        default=10,
        description="结果限制数量",
        ge=1,
        le=1000
    )


class CypherResponse(BaseModel):
    """Cypher查询响应模型"""
    cypher_query: str = Field(
        ...,
        description="生成的Cypher查询语句"
    )
    
    explanation: str = Field(
        ...,
        description="对生成的Cypher查询的解释"
    )
    
    confidence: float = Field(
        ...,
        description="模型对生成查询的信心度(0-1)",
        ge=0,
        le=1,
    )
    
    validated: bool = Field(
        default=False,
        description="查询是否通过验证"
    )
    
    validation_errors: List[str] = Field(
        default_factory=list,
        description="验证过程中发现的错误"
    )


class ValidationRequest(BaseModel):
    """Cypher查询验证请求模型"""
    cypher_query: str = Field(
        ...,
        description="需要验证的Cypher查询"
    )


class ValidationResponse(BaseModel):
    """Cypher查询验证响应模型"""
    is_valid: bool = Field(
        ...,
        description="查询是否有效"
    )
    
    errors: List[str] = Field(
        default_factory=list,
        description="发现的错误列表"
    )
    
    suggestions: List[str] = Field(
        default_factory=list,
        description="改进建议"
    )

