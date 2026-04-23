from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy import select

from backend.app.agents.utils import sse
from backend.app.agents.customer_service.prompts import SYSTEM_PROMPT
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.chat_session import ChatSession, ChatMessage, MessageRole

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"
EMBED_MODEL = "nomic-embed-text"

# 语义检索 top-K 条 + 最近兜底 N 条
TOP_K_SEMANTIC = 6
RECENT_FALLBACK = 4

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
_embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)


async def _embed(text: str) -> list[float]:
# 把 一句话 转换成 embedding 向量。
    return await _embeddings.aembed_query(text)


async def _get_or_create_session(user_id: int) -> ChatSession:
    """按 user_id 找到唯一会话，不存在则新建。"""
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


async def _retrieve_context(session_db_id: int, query: str) -> list[ChatMessage]:
    """向量检索语义相关消息 + 最近消息兜底，合并去重后按时间排序。"""
    query_embedding = await _embed(query)

    async with AsyncSessionLocal() as db:
        # 语义相似度检索（余弦距离 <=>，越小越相似）
        semantic_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_db_id)
            .where(ChatMessage.embedding.isnot(None))
            # 只查那些 embedding 不为空 的消息。
            .order_by(ChatMessage.embedding.op("<=>")(query_embedding))
            # 跟 query_embedding 比较距离。
            .limit(TOP_K_SEMANTIC)
            # 只取前 TOP_K_SEMANTIC 条结果。
        )
        semantic_messages = semantic_result.scalars().all()
        # .all 的意思是 ： 一次性全部拿出来，变成 Python 列表, 大概样子如下
        # semantic_messages = [ChatMessage(...),ChatMessage(...),ChatMessage(...)] 。

        # 最近 N 条兜底，保证上下文连贯
        recent_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_db_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(RECENT_FALLBACK)
        )
        recent_messages = list(reversed(recent_result.scalars().all()))

    # 合并去重，按时间排序
    seen: set[int] = set()
    merged: list[ChatMessage] = []
    for message in recent_messages + list(semantic_messages):
    # list的可加性。 例子： [1, 2] + [2, 3] = [1, 2, 2, 3]
        if message.id not in seen:
            seen.add(message.id)
            merged.append(message)

    merged.sort(key=lambda m: m.created_at)
    # .sort 是修改原列表（更省内存）, 对 merged用完  .sort 之后，merged已经变成新的了。
    #  key=lambda m: m.created_at， 排序的时候，按每个元素的 created_at 来排序。
    return merged


async def _save_messages(session_db_id: int, user_content: str, assistant_content: str) -> None:
    """保存本轮对话，并异步生成 embedding 存入 DB。"""
    user_vec, assistant_vec = await asyncio.gather(
        _embed(user_content),
        _embed(assistant_content),
    )
    async with AsyncSessionLocal() as db:
        db.add(ChatMessage(
            session_id=session_db_id,
            role=MessageRole.user,
            content=user_content,
            embedding=user_vec,
        ))
        db.add(ChatMessage(
            session_id=session_db_id,
            role=MessageRole.assistant,
            content=assistant_content,
            embedding=assistant_vec,
        ))
        await db.commit()


async def generate(user_id: int, message: str) -> AsyncGenerator[str, None]:
    """客服 Agent 主流程，返回 SSE 事件流。

    SSE 事件类型：
      text_chunk  — 回答的逐字流
      error       — 出错信息
      done        — 流结束
    """
    session = await _get_or_create_session(user_id)
    context = await _retrieve_context(session.id, message)

    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in context:
        if msg.role == MessageRole.user:
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRole.assistant:
            langchain_messages.append(AIMessage(content=msg.content))
    langchain_messages.append(HumanMessage(content=message))

    full_response = ""
    try:
        async for chunk in _llm.astream(langchain_messages):
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
