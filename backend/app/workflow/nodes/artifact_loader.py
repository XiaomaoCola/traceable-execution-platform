from __future__ import annotations

from sqlalchemy import select
from pydantic import BaseModel, Field

from ...models.artifact import Artifact
from ..types import NodeType
from .base import BaseNode, NodeRunResult, RunStatus


class ArtifactLoaderNodeData(BaseModel):
    """ArtifactLoaderNode 的静态配置。

    artifact_selector : 从 VariablePool 哪个位置读取 artifact_id，
                        默认读 start 节点写入的 artifact_id。
    encoding          : 文件字节解码方式，路由器配置文件通常是 utf-8 或 gbk。
    """

    artifact_selector: list[str] = Field(default=["start", "artifact_id"])
    encoding: str = "utf-8"


class ArtifactLoaderNode(BaseNode[ArtifactLoaderNodeData]):
    """从存储层读取 artifact 内容，输出为文本供下游节点（如 LLM）使用。

    依赖注入（通过 context）：
      context["db"]             → AsyncSession，查 artifact 的 storage_path
      context["artifact_store"] → ArtifactStore，读取实际文件字节

    这个节点是 workflow 和现有 artifact 基础设施的桥梁，
    让 LLMNode 不需要感知存储细节，只拿到文本字符串即可。
    """

    node_type = NodeType.ARTIFACT_LOADER

    async def _run(self) -> NodeRunResult:
        artifact_id = self.variable_pool.get_value(self.node_data.artifact_selector)
        if artifact_id is None:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"找不到 artifact_id，selector={self.node_data.artifact_selector}",
            )

        db = self.context.get("db")
        store = self.context.get("artifact_store")
        if db is None or store is None:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error="context 缺少 db 或 artifact_store，请在 engine.run() 时传入 node_context",
            )

        # 查询 artifact 元数据，拿 storage_path
        result = await db.execute(
            select(Artifact).where(Artifact.id == artifact_id, Artifact.is_deleted.is_(False))
        )
        artifact = result.scalar_one_or_none()
        if artifact is None:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"Artifact {artifact_id} 不存在或已删除",
            )

        # 从存储层读取原始字节，解码为文本
        content_bytes = await store.read(artifact.storage_path)
        content = content_bytes.decode(self.node_data.encoding, errors="replace")

        return NodeRunResult(
            status=RunStatus.SUCCESS,
            outputs={"content": content, "filename": artifact.filename},
        )
