"""add ticket search indexes

Revision ID: b1c2d3e4f5a6
Revises: a3f1c2b4d5e6
Create Date: 2026-03-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'b1c2d3e4f5a6'
down_revision = 'a3f1c2b4d5e6'  # 你最新的 migration 的 revision id
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 状态字段索引（筛选用）
    op.create_index('ix_tickets_status', 'tickets', ['status'], unique=False)
    # 创建时间索引（排序用）
    op.create_index('ix_tickets_created_at', 'tickets', ['created_at'], unique=False)
    # 创建人索引（非管理员过滤用）
    op.create_index('ix_tickets_created_by_id', 'tickets', ['created_by_id'], unique=False)
    # 资产索引（资产筛选用）
    op.create_index('ix_tickets_asset_id', 'tickets', ['asset_id'], unique=False)
    # 标题全文搜索索引
    op.execute("CREATE INDEX ix_tickets_title_fts ON tickets USING gin(to_tsvector('simple', title))")


def downgrade() -> None:
    op.drop_index('ix_tickets_title_fts', table_name='tickets')
    op.drop_index('ix_tickets_asset_id', table_name='tickets')
    op.drop_index('ix_tickets_created_by_id', table_name='tickets')
    op.drop_index('ix_tickets_created_at', table_name='tickets')
    op.drop_index('ix_tickets_status', table_name='tickets')