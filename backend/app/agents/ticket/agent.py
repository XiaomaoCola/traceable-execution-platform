from __future__ import annotations

from typing import AsyncGenerator

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

from backend.app.agents.utils import sse
from backend.app.agents.ticket.prompts import SYSTEM_PROMPT
from backend.app.agents.ticket.tools import search_tickets, get_ticket_detail, get_tickets_by_asset

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"
# TODO: OLLAMA_BASE_URL 和 MODEL 在三个 agent 里各自硬编码，应统一移到
#       backend/app/core/config.py（Settings 类），通过环境变量注入，
#       各 agent 改成从 settings 读取，方便切换模型或部署环境。

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
_tools = [search_tickets, get_ticket_detail, get_tickets_by_asset]

_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

_agent = create_tool_calling_agent(_llm, _tools, _prompt)
_executor = AgentExecutor(agent=_agent, tools=_tools)


async def generate(message: str) -> AsyncGenerator[str, None]:
    """工单助手 Agent 主流程，返回 SSE 事件流。

    SSE 事件类型：
      tool_start  — Agent 开始调用某工具
      tool_result — 工具返回结果
      text_chunk  — 最终回答的逐字流
      error       — 出错信息
      done        — 流结束
    """
    try:
        async for event in _executor.astream_events({"input": message}, version="v2"):
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

    yield sse({"type": "done"})
