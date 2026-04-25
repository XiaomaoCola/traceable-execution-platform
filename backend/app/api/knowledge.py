"""知识库管理 API。

管理员：创建/删除知识库、上传/删除文档。
普通用户：查看所有知识库、管理自己的选择。
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from backend.app.core.dependencies import CurrentUser, CurrentAdmin, DatabaseSession
from backend.app.models.knowledge import (
    KnowledgeBase, KnowledgeDocument, DocumentStatus, UserKnowledgeSelection,
)
from backend.app.services.knowledge_service import process_document

router = APIRouter(prefix="/knowledge", tags=["Knowledge - 知识库"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


# ── Schemas ────────────────────────────────────────────────────────────────

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None


class ChunkOut(BaseModel):
    id: int
    chunk_index: int
    content: str

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    filename: str
    status: DocumentStatus

    model_config = {"from_attributes": True}


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str | None
    documents: list[DocumentOut]

    model_config = {"from_attributes": True}


# ── 管理员：知识库 CRUD ────────────────────────────────────────────────────

@router.post(
    "/bases",
    response_model=KnowledgeBaseOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建知识库",
    description="仅管理员可用。创建一个新的知识库（命名集合），后续可向其中上传文档。",
)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    db: DatabaseSession,
    current_admin: CurrentAdmin,
):
    existing = await db.execute(select(KnowledgeBase).where(KnowledgeBase.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="知识库名称已存在")

    kb = KnowledgeBase(name=body.name, description=body.description, created_by_id=current_admin.id)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    # refresh 不会自动加载关联，需要重新查一次带 selectinload
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb.id).options(selectinload(KnowledgeBase.documents))
    )
    return result.scalar_one()


@router.get(
    "/bases",
    response_model=list[KnowledgeBaseOut],
    summary="获取所有知识库",
    description="所有登录用户可用。返回全部知识库列表，每个知识库包含其下的文档列表及处理状态（pending/ready/failed）。",
)
async def list_knowledge_bases(db: DatabaseSession, current_user: CurrentUser):
    result = await db.execute(select(KnowledgeBase).options(selectinload(KnowledgeBase.documents)))
    return result.scalars().all()


@router.delete(
    "/bases/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识库",
    description="仅管理员可用。删除指定知识库及其下所有文档和切片（CASCADE）。",
)
async def delete_knowledge_base(kb_id: int, db: DatabaseSession, current_admin: CurrentAdmin):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    await db.delete(kb)
    await db.commit()


# ── 管理员：文档上传/删除 ──────────────────────────────────────────────────

@router.post(
    "/bases/{kb_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传文档到知识库",
    description=(
        "仅管理员可用。支持 .txt / .md / .pdf 格式。\n\n"
        "上传后立即返回（status=pending），后台异步执行切片和向量化，完成后变为 ready。\n\n"
        "切片规则：按段落切，每片约 500 字，相邻片重叠 50 字；"
        "切片越多、KB 文件越多，向量检索的精度会逐渐下降（见 knowledge_service.py 中的说明）。"
    ),
)
async def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    db: DatabaseSession,
    current_admin: CurrentAdmin,
    file: UploadFile = File(...),
):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    filename = file.filename or "unknown"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅支持 {ALLOWED_EXTENSIONS}")

    content = await file.read()

    doc = KnowledgeDocument(knowledge_base_id=kb_id, filename=filename, status=DocumentStatus.pending)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(process_document, doc.id, filename, content)
    return doc


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除文档",
    description="仅管理员可用。删除指定文档及其所有切片（CASCADE），向量数据同步清除。",
)
async def delete_document(doc_id: int, db: DatabaseSession, current_admin: CurrentAdmin):
    result = await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    await db.delete(doc)
    await db.commit()


# ── 用户：知识库选择 ───────────────────────────────────────────────────────

@router.get(
    "/my-selections",
    response_model=list[int],
    summary="获取我已选择的知识库",
    description="返回当前登录用户已激活的知识库 ID 列表。客服 Agent 回答时只检索这些知识库的内容。",
)
async def get_my_selections(db: DatabaseSession, current_user: CurrentUser):
    result = await db.execute(
        select(UserKnowledgeSelection.knowledge_base_id).where(
            UserKnowledgeSelection.user_id == current_user.id
        )
    )
    return result.scalars().all()


@router.post(
    "/my-selections/{kb_id}",
    status_code=status.HTTP_201_CREATED,
    summary="激活知识库",
    description="将指定知识库加入当前用户的激活列表。已激活则忽略（幂等）。激活后 Agent 会在该知识库中检索相关内容辅助回答。",
)
async def select_knowledge_base(kb_id: int, db: DatabaseSession, current_user: CurrentUser):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    existing = await db.execute(
        select(UserKnowledgeSelection).where(
            UserKnowledgeSelection.user_id == current_user.id,
            UserKnowledgeSelection.knowledge_base_id == kb_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(UserKnowledgeSelection(user_id=current_user.id, knowledge_base_id=kb_id))
        await db.commit()
    return {"ok": True}


@router.delete(
    "/my-selections/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="取消激活知识库",
    description="将指定知识库从当前用户的激活列表中移除。取消后 Agent 不再检索该知识库。",
)
async def deselect_knowledge_base(kb_id: int, db: DatabaseSession, current_user: CurrentUser):
    await db.execute(
        delete(UserKnowledgeSelection).where(
            UserKnowledgeSelection.user_id == current_user.id,
            UserKnowledgeSelection.knowledge_base_id == kb_id,
        )
    )
    await db.commit()
