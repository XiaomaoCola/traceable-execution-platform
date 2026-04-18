from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from backend.app.agents.stock import agent as stock_agent

router = APIRouter(prefix="/agent1", tags=["Agent - 量化先知"])

_DEMO_HTML = (Path(__file__).parent.parent / "agents" / "stock" / "demo.html").read_text(encoding="utf-8")


class StockRequest(BaseModel):
    message: str


@router.post("/stock")
async def stock_chat(req: StockRequest):
    """量化先知 Agent 主接口，返回 SSE 流。"""
    return StreamingResponse(stock_agent.generate(req.message), media_type="text/event-stream")


@router.get("/stock/demo", response_class=HTMLResponse)
async def stock_demo():
    """直接在浏览器打开查看演示页面。"""
    return HTMLResponse(content=_DEMO_HTML)
