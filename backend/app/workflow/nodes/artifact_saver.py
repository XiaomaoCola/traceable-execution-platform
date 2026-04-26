from __future__ import annotations

import io

from pydantic import BaseModel

from ...models.artifact import Artifact
from ..types import NodeType
from .base import BaseNode, NodeRunResult, RunStatus


class ArtifactSaverNodeData(BaseModel):
    """ArtifactSaverNode 的静态配置。

    content_selector : 从 VariablePool 哪个位置读取要保存的文本内容。
    filename         : 保存到存储层的文件名。
    artifact_type    : artifact 分类标签，与现有 Artifact.artifact_type 字段对应。
    description      : artifact 描述，方便审计时阅读。
    """

    content_selector: list[str]
    filename: str
    artifact_type: str = "llm_analysis"
    description: str = ""



# TODO（LLM 分析结果存储方式重构）：
#
# 当前实现把 LLM 的分析结果作为普通 artifact 保存到 artifacts 表，
# 与用户上传的原始配置文件混在一起，导致一个工单下有一堆 artifact 却看不出哪个是源文件、哪个是分析结果。
#
# 正确的做法是新建 artifact_analyses 表，建立「源文件 → 分析结果」的明确关联：
#
#   artifact_analyses
#     id
#     artifact_id     FK → artifacts.id   （被分析的原始文件）
#     analysis_type   varchar              （e.g. "router_config"，方便未来支持多种分析类型）
#     content         text                 （LLM 输出直接存文本，不需要再走 artifact_store 存文件）
#     status          varchar              （success / failed）
#     error           text                 （失败原因）
#     created_by_id   FK → users.id
#     created_at
#
# 改动涉及：
#   1. 新建 ArtifactAnalysis model（backend/app/models/artifact_analysis.py）
#   2. 新建对应的 Alembic migration
#   3. 用新的 AnalysisSaverNode 替换本节点，直接写文本到 artifact_analyses，
#      不再走 artifact_store 存文件、也不再往 artifacts 表插记录
#   4. 更新 router_config_analysis workflow 定义，换用新节点
#   5. 更新 workflow_service 和 API 响应，返回 analysis_id 而非 artifact_id
#
# 在此之前先把整条 workflow 跑通，存储方式的重构作为后续任务。


class ArtifactSaverNode(BaseNode[ArtifactSaverNodeData]):
    """把 VariablePool 里的文本内容持久化为 artifact，写入存储层和数据库。

    依赖注入（通过 context）：
      context["db"]             → AsyncSession，创建 Artifact 数据库记录
      context["artifact_store"] → ArtifactStore，保存文件字节

    从 sys.* 命名空间读取 ticket_id / user_id，
    这两个值由 workflow_service 在启动 engine 时注入到 system_variables。
    """

    node_type = NodeType.ARTIFACT_SAVER

    async def _run(self) -> NodeRunResult:
        content = self.variable_pool.get_value(self.node_data.content_selector)
        if content is None:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error=f"找不到要保存的内容，selector={self.node_data.content_selector}",
            )

        # 从 sys.* 命名空间读取由 service 层注入的运行时元数据
        ticket_id = self.variable_pool.get_value(["sys", "ticket_id"])
        uploader_id = self.variable_pool.get_value(["sys", "user_id"])

        db = self.context.get("db")
        store = self.context.get("artifact_store")
        if db is None or store is None:
            return NodeRunResult(
                status=RunStatus.FAILED,
                error="context 缺少 db 或 artifact_store",
            )

        # 文本编码为字节，存入 storage
        content_bytes = content.encode("utf-8")
        file_obj = io.BytesIO(content_bytes)
        storage_path = f"tickets/{ticket_id}/workflow/{self.node_data.filename}"
        storage_path, size_bytes, sha256_hash = await store.save(file_obj, storage_path)

        # 在数据库里创建 Artifact 记录，与工单关联
        artifact = Artifact(
            filename=self.node_data.filename,
            content_type="text/plain",
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            storage_path=storage_path,
            artifact_type=self.node_data.artifact_type,
            description=self.node_data.description,
            ticket_id=ticket_id,
            uploaded_by_id=uploader_id,
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)

        return NodeRunResult(
            status=RunStatus.SUCCESS,
            outputs={"artifact_id": artifact.id, "filename": artifact.filename},
        )
