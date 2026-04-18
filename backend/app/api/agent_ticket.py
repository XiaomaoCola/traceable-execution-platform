from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from backend.app.agents.ticket import agent as ticket_agent

router = APIRouter(prefix="/agent2", tags=["Agent - 工单助手"])

_DEMO_HTML = (Path(__file__).parent.parent / "agents" / "ticket" / "demo.html").read_text(encoding="utf-8")


class TicketChatRequest(BaseModel):
    message: str


@router.post("/ticket")
async def ticket_chat(req: TicketChatRequest):
    """工单助手主接口，返回 SSE 流。"""
    return StreamingResponse(ticket_agent.generate(req.message), media_type="text/event-stream")


@router.get("/ticket/demo", response_class=HTMLResponse)
async def ticket_demo():
    """浏览器直接打开即可使用。"""
    return HTMLResponse(content=_DEMO_HTML)
