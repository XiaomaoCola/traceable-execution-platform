"""add pgvector extension and embedding column to chat_messages

Revision ID: d5e6f7a8b9c0
Revises: c2d3e4f5a6b7
Create Date: 2026-04-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e6f7a8b9c0'
down_revision = 'c2d3e4f5a6b7'
branch_labels = None
depends_on = None

EMBED_DIM = 768


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "chat_messages",
        sa.Column(
            "embedding",
            sa.Text(),  # 占位类型，下面立刻用 raw SQL 改成真正的 vector 类型
            nullable=True,
        ),
    )
    # SQLAlchemy 的 Column 不认识 vector 类型，直接用 DDL 改
    op.execute(f"ALTER TABLE chat_messages ALTER COLUMN embedding TYPE vector({EMBED_DIM}) USING NULL")


def downgrade() -> None:
    op.drop_column("chat_messages", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
