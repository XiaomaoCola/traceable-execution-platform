"""Artifact upload/download endpoints."""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy import select, func

from backend.app.schemas.artifact import ArtifactResponse, ArtifactUploadResponse, PaginatedArtifactResponse
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.services.artifact_service import upload_artifact, download_artifact
from backend.app.models.artifact import Artifact
from backend.app.models.ticket import Ticket


router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("", response_model=ArtifactUploadResponse)
async def upload_artifact_endpoint(
    ticket_id: int,
    file: UploadFile = File(...),
    artifact_type: str | None = None,
    description: str | None = None,
    db: DatabaseSession = None,
    current_user: CurrentUser = None
):
    """
    Upload an artifact for a ticket.

    Args:
        ticket_id: Associated ticket ID
        file: File to upload
        artifact_type: Optional artifact classification
        description: Optional description
    """
    # Verify ticket exists and user has permission
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if ticket.created_by_id != current_user.id:
        # 当前用户如果不是管理员 ，
        # 而且 如果这个工单不是由当前已登录的用户创建的话，报错。
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload artifacts for this ticket"
            )

    # Upload artifact
    artifact = await upload_artifact(
        db=db,
        file=file.file,
        filename=file.filename,
        ticket_id=ticket_id,
        uploader=current_user,
        content_type=file.content_type,
        artifact_type=artifact_type,
        description=description
    )

    return ArtifactUploadResponse(artifact=artifact)


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact_metadata(
    artifact_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Get artifact metadata."""
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )

    # Check permissions
    if not current_user.is_admin:
        if artifact.ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this artifact"
            )

    return artifact


@router.get("/{artifact_id}/download")
async def download_artifact_endpoint(
    artifact_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """Download artifact file."""
    file_content, artifact = await download_artifact(db, artifact_id, current_user)

    from urllib.parse import quote
    encoded_filename = quote(artifact.filename, encoding="utf-8")
    return Response(
        content=file_content,
        media_type=artifact.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/ticket/{ticket_id}", response_model=PaginatedArtifactResponse)
async def list_ticket_artifacts(
    ticket_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """List all artifacts for a ticket with pagination."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if not current_user.is_admin:
        if ticket.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view artifacts for this ticket"
            )

    query = select(Artifact).where(
        Artifact.ticket_id == ticket_id,
        Artifact.is_deleted == False
    )

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        query.order_by(Artifact.created_at.desc())
             .offset((page - 1) * page_size)
             .limit(page_size)
    )
    artifacts = result.scalars().all()

    return {
        "data": artifacts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }