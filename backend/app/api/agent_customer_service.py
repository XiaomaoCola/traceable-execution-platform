from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.app.agents.customer_service import agent as cs_agent
from backend.app.core.dependencies import CurrentUser

router = APIRouter(prefix="/agent/customer-service", tags=["Agent - 客服"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def customer_service_chat(req: ChatRequest, current_user: CurrentUser):
    """客服 Agent 主接口，返回 SSE 流。登录用户自动关联自己的对话历史。"""
    return StreamingResponse(
        cs_agent.generate(current_user.id, req.message),
        media_type="text/event-stream",
    )
