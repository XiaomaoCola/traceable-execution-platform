from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from backend.app.agents.fortune import agent as fortune_agent

router = APIRouter(prefix="/agent", tags=["Agent - 算命"])

_DEMO_HTML = (Path(__file__).parent.parent / "agents" / "fortune" / "demo.html").read_text(encoding="utf-8")


class FortuneRequest(BaseModel):
    message: str


@router.post("/fortune")
async def fortune_chat(req: FortuneRequest):
    """算命 Agent 主接口，返回 SSE 流。"""
    return StreamingResponse(fortune_agent.generate(req.message), media_type="text/event-stream")


@router.get("/fortune/demo", response_class=HTMLResponse)
async def fortune_demo():
    """直接在浏览器打开这个 URL 就能看到演示页面。"""
    return HTMLResponse(content=_DEMO_HTML)
