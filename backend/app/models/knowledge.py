"""知识库数据模型。

【当前用途】
客服机器人的知识库支持。管理员上传文档，系统切片向量化后，
客服 Agent 在回答时自动检索相关内容注入 system prompt。

【为什么要多知识库（KnowledgeBase），而不是单一全局知识库？】

对于简单的单一业务客服（如本平台），一个知识库确实够用，
多知识库的设计看起来有点"复杂过头"。

但这套结构是为了支持未来的高考志愿填报系统而保留的：

  高考场景下，数据天然按省份/类别隔离：
    KnowledgeBase("山东省")  → 山东招生计划.pdf、山东高校排名.txt
    KnowledgeBase("北京市")  → 北京高校数据.pdf、北京分数线.xlsx
    KnowledgeBase("985/211") → 顶尖院校通用数据.pdf


【用户选择知识库的两种模式】

  模式 A（当前实现）：用户手动勾选
    用户在界面上选择自己感兴趣的知识库，Agent 检索时只查已选的。
    适合用户明确知道自己需要什么（如客服选特定产品线知识库）。

  模式 B（高考场景推荐）：Agent 自动路由
    用户无需手动选，Agent 根据对话内容（"我想去山东的高校"）自动判断
    应该检索哪个省的知识库。
    实现思路：在 _retrieve_knowledge() 里改为先让 LLM 识别省份/意图，
    再动态决定 knowledge_base_id，而不是查 user_knowledge_selections 表。

【数据流】
  上传文档
    → knowledge_documents（status=pending）
    → 后台异步切片 + embed
    → knowledge_chunks（content + embedding 768维）
    → knowledge_documents（status=ready）

  用户提问
    → embed(query)
    → 查 user_knowledge_selections 找用户激活的 KB
    → 在对应 KB 的 knowledge_chunks 里做向量相似度检索（<=>）
    → top-K 切片文本注入 system prompt
"""

import enum

from sqlalchemy import Column, String, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from backend.app.db.base import Base, IDMixin, TimestampMixin


class DocumentStatus(str, enum.Enum):
    pending = "pending"   # 刚上传，等待处理
    ready = "ready"       # 切片+向量化完成，可检索
    failed = "failed"     # 处理失败（文件损坏、embed 超时等）


class KnowledgeBase(Base, IDMixin, TimestampMixin):
    """知识库，是文档的命名集合。

    当前：客服机器人用，管理员按业务主题建库（如"产品手册"、"退换货政策"）。
    未来高考系统：按省份建库（"山东省"、"北京市"），支持 Agent 按省份路由检索。
    """

    __tablename__ = "knowledge_bases"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    documents = relationship("KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])


class KnowledgeDocument(Base, IDMixin, TimestampMixin):
    """上传到知识库的原始文件。

    支持 .txt / .md / .pdf（见 knowledge_service.py）。
    上传后立刻返回 pending，后台异步切片+向量化，完成后变 ready。
    """

    __tablename__ = "knowledge_documents"

    knowledge_base_id = Column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename = Column(String(255), nullable=False)

    # create_type=False：PostgreSQL enum type 由 Alembic 迁移脚本手动创建，
    # 防止 SQLAlchemy 在 env.py 导入模型时将其注册进 Base.metadata，
    # 导致 op.create_table 时重复建 type 报错。
    status = Column(
        PgEnum(DocumentStatus, name="documentstatus", create_type=False),
        nullable=False,
        default=DocumentStatus.pending,
    )

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeChunk(Base, IDMixin, TimestampMixin):
    """文档切片，每条存一段文本和对应的 768 维向量。

    切片策略（见 knowledge_service._chunk_text）：
      - 按段落（\\n\\n）切，目标 500 字符/片，相邻片有 50 字符重叠保证语义连贯。
      - 单段超长则按字符数强制截断。

    检索时用余弦距离（<=>）排序，取 top-K 最相关的片段。
    """

    __tablename__ = "knowledge_chunks"

    document_id = Column(
        Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(768), nullable=True)  # nomic-embed-text 输出 768 维

    document = relationship("KnowledgeDocument", back_populates="chunks")


class UserKnowledgeSelection(Base, TimestampMixin):
    """用户激活了哪些知识库，复合主键，无自增 ID。

    当前模式（手动选择）：
      用户在客服页面勾选知识库 → 写入此表 → Agent 检索时只查已选的 KB。

    高考系统改造建议（自动路由，不需要此表）：
      删掉用户手动选择的交互，改为 Agent 在 _retrieve_knowledge() 里
      先识别用户意图（省份、院校类型），再动态决定检索哪个 KB。
      届时此表可废弃，或改为存储用户的"偏好省份"等结构化信息。
    """

    __tablename__ = "user_knowledge_selections"
    __table_args__ = (
        UniqueConstraint("user_id", "knowledge_base_id", name="uq_user_kb_selection"),
    )

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    knowledge_base_id = Column(
        Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), primary_key=True
    )
