from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from sqlalchemy import select

from backend.app.agents.customer_service.intent import Intent, classify
from backend.app.agents.customer_service.prompts import (
    PRODUCT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    TICKET_SYSTEM_PROMPT,
)
from backend.app.agents.ticket.tools import (
    get_ticket_detail,
    get_tickets_by_asset,
    search_tickets,
)
from backend.app.agents.utils import sse
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.chat_session import ChatMessage, ChatSession, MessageRole
from backend.app.models.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    UserKnowledgeSelection,
)

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"
EMBED_MODEL = "nomic-embed-text"

# 语义检索 top-K 条 + 最近兜底 N 条
TOP_K_SEMANTIC = 6
RECENT_FALLBACK = 4
TOP_K_KNOWLEDGE = 4

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
_embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)

_ticket_tools = [search_tickets, get_ticket_detail, get_tickets_by_asset]
_ticket_prompt = ChatPromptTemplate.from_messages([
    ("system", TICKET_SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
_ticket_executor = AgentExecutor(
    agent=create_tool_calling_agent(_llm, _ticket_tools, _ticket_prompt),
    tools=_ticket_tools,
)


async def _embed(text: str) -> list[float]:
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


async def _retrieve_context(session_db_id: int, query_embedding: list[float]) -> list[ChatMessage]:
    """向量检索语义相关消息 + 最近消息兜底，合并去重后按时间排序。"""
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


async def _retrieve_knowledge(user_id: int, query_embedding: list[float]) -> list[str]:
    """从用户已选知识库中语义检索最相关的切片文本。"""
    async with AsyncSessionLocal() as db:
        selected_kb_ids = select(UserKnowledgeSelection.knowledge_base_id).where(
            UserKnowledgeSelection.user_id == user_id
        )
        result = await db.execute(
            select(KnowledgeChunk)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.knowledge_base_id.in_(selected_kb_ids))
            .where(KnowledgeChunk.embedding.isnot(None))
            .order_by(KnowledgeChunk.embedding.op("<=>")(query_embedding))
            .limit(TOP_K_KNOWLEDGE)
        )
        chunks = result.scalars().all()
    return [c.content for c in chunks]


def _build_history_prefix(context: list[ChatMessage]) -> str:
    """将历史消息格式化为前缀文本，供工单路径注入 agent input。"""
    if not context:
        return ""
    lines = ["[对话历史]"]
    for msg in context:
        role_label = "用户" if msg.role == MessageRole.user else "助手"
        lines.append(f"{role_label}：{msg.content}")
    return "\n".join(lines) + "\n\n"


async def _handle_ticket(
    context: list[ChatMessage],
    message: str,
) -> AsyncGenerator[str, None]:
    """工单意图：使用工具调用查询工单/设备信息。"""
    agent_input = _build_history_prefix(context) + f"[用户当前消息]\n{message}"
    try:
        async for event in _ticket_executor.astream_events({"input": agent_input}, version="v2"):
            kind = event["event"]

            if kind == "on_tool_start":
                yield sse({
                    "type": "tool_start",
                    "tool": event["name"],
                    "args": event["data"].get("input") or {},
                })

            elif kind == "on_tool_end":
                yield sse({
                    "type": "tool_result",
                    "tool": event["name"],
                    "result": str(event["data"].get("output") or ""),
                })

            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content if hasattr(chunk, "content") else ""
                if content:
                    yield sse({"type": "text_chunk", "content": content})

    except Exception as exc:
        yield sse({"type": "error", "content": str(exc)})


async def _handle_product(
    context: list[ChatMessage],
    kb_chunks: list[str],
    message: str,
) -> AsyncGenerator[str, None]:
    """产品知识意图：知识库 RAG 流式回答。"""
    # 知识库内容注入 system prompt
    system_content = PRODUCT_SYSTEM_PROMPT
    if kb_chunks:
        kb_text = "\n---\n".join(kb_chunks)
        system_content += f"\n\n以下是可能相关的知识库内容，请优先参考：\n{kb_text}"

    langchain_messages = [SystemMessage(content=system_content)]
    for msg in context:
        if msg.role == MessageRole.user:
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRole.assistant:
            langchain_messages.append(AIMessage(content=msg.content))
    langchain_messages.append(HumanMessage(content=message))

    try:
        async for chunk in _llm.astream(langchain_messages):
            content = chunk.content
            if content:
                yield sse({"type": "text_chunk", "content": content})

    except Exception as exc:
        yield sse({"type": "error", "content": str(exc)})


async def _handle_general(
    context: list[ChatMessage],
    message: str,
) -> AsyncGenerator[str, None]:
    """通用意图：普通对话，带历史上下文。"""
    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in context:
        if msg.role == MessageRole.user:
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRole.assistant:
            langchain_messages.append(AIMessage(content=msg.content))
    langchain_messages.append(HumanMessage(content=message))

    try:
        async for chunk in _llm.astream(langchain_messages):
            content = chunk.content
            if content:
                yield sse({"type": "text_chunk", "content": content})

    except Exception as exc:
        yield sse({"type": "error", "content": str(exc)})


async def generate(user_id: int, message: str) -> AsyncGenerator[str, None]:
    """客服 Agent 主流程（带意图路由），返回 SSE 事件流。

    SSE 事件类型：
      intent      — 识别到的意图（ticket / product / general）
      tool_start  — 开始调用工具（仅 ticket 路径）
      tool_result — 工具返回结果（仅 ticket 路径）
      text_chunk  — 回答的逐字流
      error       — 出错信息
      done        — 流结束
    """
    session = await _get_or_create_session(user_id)
    query_embedding = await _embed(message)

    # 并发：意图识别 + 对话历史检索 + 知识库检索（复用同一个 embedding，不重复计算）
    intent, context, kb_chunks = await asyncio.gather(
        classify(message),
        _retrieve_context(session.id, query_embedding),
        _retrieve_knowledge(user_id, query_embedding),
    )

    yield sse({"type": "intent", "intent": intent.value})

    if intent == Intent.TICKET:
        handler = _handle_ticket(context, message)
    elif intent == Intent.PRODUCT:
        handler = _handle_product(context, kb_chunks, message)
    else:
        handler = _handle_general(context, message)

    full_response = ""
    async for event_str in handler:
        # 从 text_chunk 事件里累积回答文本，用于存入历史
        try:
            payload = json.loads(event_str.removeprefix("data: ").rstrip())
            if payload.get("type") == "text_chunk":
                full_response += payload.get("content", "")
        except (json.JSONDecodeError, AttributeError):
            pass
        yield event_str

    if full_response:
        await _save_messages(session.id, message, full_response)

    yield sse({"type": "done"})
