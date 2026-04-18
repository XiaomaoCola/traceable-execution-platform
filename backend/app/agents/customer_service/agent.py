from __future__ import annotations

from typing import AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select

from backend.app.agents.utils import sse
from backend.app.agents.customer_service.prompts import SYSTEM_PROMPT
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.chat_session import ChatSession, ChatMessage

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"
# TODO: OLLAMA_BASE_URL 和 MODEL 在三个 agent 里各自硬编码，应统一移到
#       backend/app/core/config.py（Settings 类），通过环境变量注入，
#       各 agent 改成从 settings 读取，方便切换模型或部署环境。

# 每次携带的历史消息条数上限（太多会撑爆 context window）
MAX_HISTORY = 20

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)


async def _get_or_create_session(user_id: int) -> ChatSession:
    """按 user_id 找到唯一会话，不存在则新建。一个用户永远只有一个会话。"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatSession).where(ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(user_id=user_id)
            db.add(session)
            await db.commit()
            await db.refresh(session)

        return session


async def _load_history(session_db_id: int) -> list[ChatMessage]:
    """加载最近 MAX_HISTORY 条消息。"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_db_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(MAX_HISTORY)
        )
        # 倒序取最近N条，再翻转回正序
        return list(reversed(result.scalars().all()))


async def _save_messages(session_db_id: int, user_content: str, assistant_content: str) -> None:
    """把本轮对话（用户 + AI）存入数据库。"""
    async with AsyncSessionLocal() as db:
        db.add(ChatMessage(session_id=session_db_id, role="user", content=user_content))
        db.add(ChatMessage(session_id=session_db_id, role="assistant", content=assistant_content))
        await db.commit()


async def generate(user_id: int, message: str) -> AsyncGenerator[str, None]:
    """客服 Agent 主流程，返回 SSE 事件流。

    SSE 事件类型：
      text_chunk  — 回答的逐字流
      error       — 出错信息
      done        — 流结束
    """
    session = await _get_or_create_session(user_id)
    history = await _load_history(session.id)

    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in history:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
    lc_messages.append(HumanMessage(content=message))

    full_response = ""
    try:
        async for chunk in _llm.astream(lc_messages):
            content = chunk.content
            if content:
                full_response += content
                yield sse({"type": "text_chunk", "content": content})

    except Exception as exc:
        yield sse({"type": "error", "content": str(exc)})
        yield sse({"type": "done"})
        return

    await _save_messages(session.id, message, full_response)
    yield sse({"type": "done"})
