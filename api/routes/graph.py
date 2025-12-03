"""
知识图谱路由
知识图谱服务的API路由
"""
from fastapi import APIRouter, Request
from services.graph_service import (
    generate_cypher,
    validate_cypher,
    execute_query,
    get_schema as get_graph_schema,
    root as graph_root
)

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/")
async def graph_root_endpoint():
    """知识图谱服务根路径"""
    return await graph_root()


@router.get("/schema")
async def schema_endpoint():
    """获取图模式"""
    return await get_graph_schema()


@router.post("/generate")
async def generate_cypher_endpoint(request: Request):
    """生成 Cypher 查询"""
    data = await request.json()
    query = data.get("query")
    if not query:
        return {"error": "查询不能为空"}
    return await generate_cypher(query)


@router.post("/validate")
async def validate_cypher_endpoint(request: Request):
    """验证 Cypher 查询"""
    data = await request.json()
    cypher = data.get("cypher")
    if not cypher:
        return {"error": "Cypher 查询不能为空"}
    return await validate_cypher(cypher)


@router.post("/execute")
async def execute_query_endpoint(request: Request):
    """执行 Cypher 查询"""
    data = await request.json()
    cypher = data.get("cypher")
    if not cypher:
        return {"error": "Cypher 查询不能为空"}
    return await execute_query(cypher)

