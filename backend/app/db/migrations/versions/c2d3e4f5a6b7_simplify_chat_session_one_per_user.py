"""simplify chat session: one per user, drop session_id

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c2d3e4f5a6b7'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_chat_sessions_session_id', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'session_id')
    op.create_unique_constraint('uq_chat_sessions_user_id', 'chat_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_constraint('uq_chat_sessions_user_id', 'chat_sessions', type_='unique')
    op.add_column('chat_sessions', sa.Column('session_id', sa.String(length=64), nullable=True))
    op.create_index('ix_chat_sessions_session_id', 'chat_sessions', ['session_id'], unique=True)
