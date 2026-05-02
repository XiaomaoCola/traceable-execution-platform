from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from backend.app.agents.customer_service.intent.base import Intent
from backend.app.agents.customer_service.prompts import INTENT_CLASSIFY_PROMPT

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL, temperature=0)


async def classify(message: str) -> Intent:
    """用 LLM 对用户消息进行意图分类，返回 Intent 枚举值。"""
    result = await _llm.ainvoke([
        SystemMessage(content=INTENT_CLASSIFY_PROMPT),
        HumanMessage(content=message),
    ])
    raw = result.content.strip().lower()
    # 模型可能输出多余文字，逐项匹配
    for intent in Intent:
        if intent.value in raw:
            return intent
    return Intent.GENERAL
