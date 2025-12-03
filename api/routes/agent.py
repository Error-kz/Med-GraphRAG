"""
Agent路由
主Agent服务的API路由
"""
from fastapi import APIRouter, Request
from services.agent_service import chatbot, root

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.get("/")
async def agent_root():
    """Agent服务根路径"""
    return await root()


@router.post("/")
async def agent_chatbot(request: Request):
    """Agent问答接口"""
    return await chatbot(request)

