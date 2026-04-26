from __future__ import annotations

import httpx
from pydantic import BaseModel

from ...core.config import get_settings
from ..types import NodeType
from .base import BaseNode, NodeRunResult, RunStatus


class LLMNodeData(BaseModel):
    """LLMNode 的静态配置（workflow 定义时写死）。

    Dify 的 LLMNodeData 还包含：
    - context（RAG 知识库配置）
    - vision（图片输入配置）
    - memory（对话历史配置）
    - completion_params（top_p / presence_penalty 等采样参数）
    我们只保留最核心的 5 个字段，够用于 router config 分析场景。
    """

    model: str = "gpt-4o-mini"
    prompt_template: str          # 支持 {{node_id.var_name}} 模板占位符
    system_prompt: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7


class LLMNode(BaseNode[LLMNodeData]):
    """调用 LLM 的节点。

    执行流程：
    1. 用 variable_pool.resolve_template() 把 prompt_template 里的占位符替换为实际值
    2. 调用 LiteLLM 网关（httpx POST）
    3. 把响应文本写入 outputs["response"]

    Dify 的 LLMNode 还处理：
    - streaming（流式输出，通过 SSE 推送给前端）
    - tool calling（function call）
    - 用量统计（prompt_tokens / completion_tokens 写入 Run）
    我们省略以上三点，保持节点职责单一，未来按需扩展。
    """

    node_type = NodeType.LLM

    async def _run(self) -> NodeRunResult:
        # 1. 模板解析：把 {{node_id.var_name}} 替换为 pool 里的实际值
        prompt = self.variable_pool.resolve_template(self.node_data.prompt_template)
        system = self.variable_pool.resolve_template(self.node_data.system_prompt)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # 2. 调用 LiteLLM 网关
        # Dify 通过内部的 ModelManager 抽象层调用，支持多租户 API key 管理。
        # 我们直接 httpx POST，LiteLLM 本身已经是 provider 抽象层，够用了。
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{get_settings().litellm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {get_settings().litellm_master_key}"},
                    json={
                        "model": self.node_data.model,
                        "messages": messages,
                        "max_tokens": self.node_data.max_tokens,
                        "temperature": self.node_data.temperature,
                    },
                )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"LiteLLM 返回错误 {exc.response.status_code}: {exc.response.text}",
            )
        except httpx.RequestError as exc:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"LiteLLM 连接失败: {exc}",
            )

        # 3. 提取响应文本
        data = resp.json()
        response_text: str = data["choices"][0]["message"]["content"]

        return NodeRunResult(
            status=RunStatus.SUCCESS,
            outputs={"response": response_text},
        )
