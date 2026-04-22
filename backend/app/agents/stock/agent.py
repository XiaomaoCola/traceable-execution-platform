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
                tool_calls_accumulator: dict[int, dict] = {}

                async with client.stream(
                    "POST", OLLAMA_URL,
                    json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": True},
                ) as respond:
                    respond.raise_for_status()
                    # .raise_for_status 的意思是  检查这次 HTTP 请求是否成功。
                    async for line in respond.aiter_lines():
                    # aiter_lines() 的意思是 ， 从服务器返回的数据流里，一行一行地“异步读取”。
                        if not line.startswith("data: "):
                        # 只处理以  “data:”  开头的 SSE 数据行，别的行跳过。
                            continue
                            # 直接跳过这一轮循环，进入下一轮。
                        data = line[6:]
                        # 因为 "data: " 一共 6 个字符，所以需要把这6个字符切掉，只保留真正的内容。
                        if data.strip() == "[DONE]":
                            break
                            # 跳出循环。
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        # .get() 是 dict（字典）的安全取值方法。 例子：
                        # chunk["choices"] 如果key不存在的话，就会报错；
                        # chunk.get("choices") 如果key不存在，只会返回None；
                        # chunk.get("choices", [{}]) 这是带默认值的写法， 如果key不存在，返回默认值。
                        # "choices": [ {...}, {...} ] ， 一般只用第一个，所以用[0]。

                        content = delta.get("content") or ""
                        if content:
                            got_text = True
                            yield sse({"type": "text_chunk", "content": content})

                        for tool_call in delta.get("tool_calls") or []:
                        # tool_calls的value是 list， 比如
                        # "tool_calls": [
                        # { "index": 0, "function": { "name": "get_stock", "arguments": "{AAPL}" } },
                        # { "index": 1, "function": { "name": "get_stock", "arguments": "{TSLA}" } } ]
                            index = tool_call.get("index", 0)
                            if index not in tool_calls_accumulator:
                            # d = { 3: "hello" } 这个字典里， 3 in d 这个判断是 True。
                                tool_calls_accumulator[index] = {"id": "", "name": "", "arguments": ""}
                            if tool_call.get("id"):
                                tool_calls_accumulator[index]["id"] = tool_call["id"]
                            function_call = tool_call.get("function", {})
                            if function_call.get("name"):
                                tool_calls_accumulator[index]["name"] += function_call["name"]
                            if function_call.get("arguments"):
                                tool_calls_accumulator[index]["arguments"] += function_call["arguments"]

                if not tool_calls_accumulator:
                    break

                tool_calls_list = [
                    {
                        "id": tool_calls_accumulator[i]["id"],
                        "type": "function",
                        "function": {
                            "name": tool_calls_accumulator[i]["name"],
                            "arguments": tool_calls_accumulator[i]["arguments"],
                        },
                    }
                    for i in sorted(tool_calls_accumulator)
                ]

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls_list,
                })

                for tool_call in tool_calls_list:
                    name = tool_call["function"]["name"]
                    try:
                        args = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        args = {}

                    yield sse({"type": "tool_start", "tool": name, "args": args})
                    result = await execute_tool(name, args)
                    yield sse({"type": "tool_result", "tool": name, "result": result})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result,
                    })

            # 工具调用完毕但 LLM 没有生成最终文字，强制不带 tools 再请求一次
            if not got_text:
                messages.append({"role": "user", "content": "请根据以上所有工具返回的数据，生成完整的分析报告。"})
                async with client.stream(
                    "POST", OLLAMA_URL,
                    json={"model": MODEL, "messages": messages, "stream": True},
                ) as respond:
                    respond.raise_for_status()
                    async for line in respond.aiter_lines():
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
