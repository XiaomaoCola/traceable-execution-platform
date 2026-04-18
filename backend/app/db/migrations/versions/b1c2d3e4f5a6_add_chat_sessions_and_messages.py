"""add chat sessions and messages

Revision ID: b1c2d3e4f5a6
Revises: a3f1c2b4d5e6
Create Date: 2026-04-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b1c2d3e4f5a6'
down_revision = 'a3f1c2b4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'chat_sessions',
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_sessions_session_id', 'chat_sessions', ['session_id'], unique=True)
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])

    op.create_table(
        'chat_messages',
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])


def downgrade() -> None:
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index('ix_chat_sessions_user_id', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_session_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')
