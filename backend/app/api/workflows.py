"""workflow 触发 API。

当前只有一个端点：对工单绑定的路由器配置文件触发 LLM 分析。
未来新增其他 workflow 时，在这里加新的端点即可，service 层对应扩展。
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from ..core.dependencies import CurrentUser, DatabaseSession
from ..models.artifact import Artifact
from ..models.ticket import Ticket
from ..services.workflow_service import run_router_config_analysis

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class RouterConfigAnalysisRequest(BaseModel):
    artifact_id: int


class RouterConfigAnalysisResponse(BaseModel):
    status: str
    analysis: str | None = None
    analysis_artifact_id: int | None = None
    config_filename: str | None = None
    error: str | None = None


@router.post(
    "/tickets/{ticket_id}/analyze-router-config",
    response_model=RouterConfigAnalysisResponse,
    summary="触发路由器配置 LLM 分析",
    description=(
        "对指定工单下已上传的路由器配置 artifact 执行 LLM 分析 workflow。\n"
        "分析结果会作为新的 artifact 保存到工单。"
    ),
)
async def trigger_router_config_analysis(
    ticket_id: int,
    body: RouterConfigAnalysisRequest,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> RouterConfigAnalysisResponse:
    # 校验工单存在且当前用户有权限
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    if not current_user.is_admin and ticket.created_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此工单")

    # 校验 artifact 属于该工单
    art_result = await db.execute(
        select(Artifact).where(
            Artifact.id == body.artifact_id,
            Artifact.ticket_id == ticket_id,
            Artifact.is_deleted.is_(False),
        )
    )
    if art_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="artifact 不存在或不属于该工单",
        )

    # 执行 workflow
    wf_result = await run_router_config_analysis(
        db=db,
        ticket_id=ticket_id,
        artifact_id=body.artifact_id,
        triggered_by=current_user,
    )

    return RouterConfigAnalysisResponse(
        status=wf_result.status,
        analysis=wf_result.outputs.get("analysis"),
        analysis_artifact_id=wf_result.outputs.get("analysis_artifact_id"),
        config_filename=wf_result.outputs.get("config_filename"),
        error=wf_result.error,
    )
