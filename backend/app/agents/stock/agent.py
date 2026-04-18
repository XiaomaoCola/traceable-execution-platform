from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx

from backend.app.agents.utils import sse
from backend.app.agents.stock.prompts import SYSTEM_PROMPT
from backend.app.agents.stock.tools import TOOLS, execute_tool

OLLAMA_URL = "http://host.docker.internal:11434/v1/chat/completions"
MODEL = "llama3.1:8b"
# TODO: OLLAMA_URL 和 MODEL 在三个 agent 里各自硬编码，应统一移到
#       backend/app/core/config.py（Settings 类），通过环境变量注入，
#       各 agent 改成从 settings 读取，方便切换模型或部署环境。


async def generate(message: str) -> AsyncGenerator[str, None]:
    """量化先知 Agent 主流程，返回 SSE 事件流。

    SSE 事件类型：
      tool_start  — Agent 开始调用某工具
      tool_result — 工具返回结果
      text_chunk  — 最终分析报告的逐字流
      error       — 出错信息
      done        — 流结束
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    got_text = False
    try:
        async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
            for _ in range(8):
                tool_calls_acc: dict[int, dict] = {}

                async with client.stream(
                    "POST", OLLAMA_URL,
                    json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        delta = chunk.get("choices", [{}])[0].get("delta", {})

                        content = delta.get("content") or ""
                        if content:
                            got_text = True
                            yield sse({"type": "text_chunk", "content": content})

                        for tc in delta.get("tool_calls") or []:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.get("id"):
                                tool_calls_acc[idx]["id"] = tc["id"]
                            fn = tc.get("function", {})
                            if fn.get("name"):
                                tool_calls_acc[idx]["name"] += fn["name"]
                            if fn.get("arguments"):
                                tool_calls_acc[idx]["arguments"] += fn["arguments"]

                if not tool_calls_acc:
                    break

                tool_calls_list = [
                    {
                        "id": tool_calls_acc[i]["id"],
                        "type": "function",
                        "function": {
                            "name": tool_calls_acc[i]["name"],
                            "arguments": tool_calls_acc[i]["arguments"],
                        },
                    }
                    for i in sorted(tool_calls_acc)
                ]

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls_list,
                })

                for tc in tool_calls_list:
                    name = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    yield sse({"type": "tool_start", "tool": name, "args": args})
                    result = await execute_tool(name, args)
                    yield sse({"type": "tool_result", "tool": name, "result": result})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })

            # 工具调用完毕但 LLM 没有生成最终文字，强制不带 tools 再请求一次
            if not got_text:
                messages.append({"role": "user", "content": "请根据以上所有工具返回的数据，生成完整的分析报告。"})
                async with client.stream(
                    "POST", OLLAMA_URL,
                    json={"model": MODEL, "messages": messages, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content") or ""
                        if content:
                            yield sse({"type": "text_chunk", "content": content})

    except Exception as exc:
        yield sse({"type": "error", "content": str(exc)})

    yield sse({"type": "done"})
