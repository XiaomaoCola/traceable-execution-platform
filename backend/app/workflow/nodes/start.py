from __future__ import annotations

from pydantic import BaseModel, Field

from ..types import NodeType
from .base import BaseNode, NodeRunResult, RunStatus


class InputVariableDeclaration(BaseModel):
    """单个输入变量的声明。

    Dify 的 StartNode 有完整的输入变量 schema（包含类型、是否必填、默认值、
    文件类型限制等），用于在 UI 上渲染动态表单。
    我们只保留 variable（变量名）和 required（是否必填）两个字段，
    聚焦在运行时校验，去掉 UI 渲染相关的字段（label / placeholder / options 等）。
    """

    variable: str
    required: bool = True


class StartNodeData(BaseModel):
    """StartNode 的静态配置。

    声明这个 workflow 期望接收哪些输入变量，用于运行时校验。
    如果 input_schema 为空列表，则接受任意输入（宽松模式）。
    """

    input_schema: list[InputVariableDeclaration] = Field(default_factory=list)


class StartNode(BaseNode[StartNodeData]):
    """workflow 的入口节点，负责接收外部输入并写入 VariablePool。

    核心职责：
    1. 校验必填输入是否都已提供
    2. 把 variable_pool.user_inputs 写入 start.* 命名空间，
       供下游节点通过 {{start.artifact_id}} 这样的 selector 读取

    Dify 的 StartNode 还处理文件类型校验、枚举选项校验等，
    我们只做必填校验，类型校验由各节点自行负责。
    """

    node_type = NodeType.START

    async def _run(self) -> NodeRunResult:
        inputs = self.variable_pool.user_inputs

        # 校验必填变量
        if self.node_data.input_schema:
            missing = [
                decl.variable
                for decl in self.node_data.input_schema
                if decl.required and decl.variable not in inputs
            ]
            if missing:
                return NodeRunResult(
                    status=RunStatus.FAILED,
                    error=f"缺少必填输入变量：{missing}",
                )

        # 把所有输入写入 outputs，run() 基类会统一写入 pool 的 start.* 命名空间
        return NodeRunResult(status=RunStatus.SUCCESS, outputs=dict(inputs))
