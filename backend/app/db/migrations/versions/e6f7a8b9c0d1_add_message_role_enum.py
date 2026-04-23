"""convert chat_messages.role to enum type

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-24 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None

message_role = sa.Enum("user", "assistant", "system", name="messagerole")


def upgrade() -> None:
    message_role.create(op.get_bind(), checkfirst=True)
    op.execute(
        "ALTER TABLE chat_messages "
        "ALTER COLUMN role TYPE messagerole USING role::messagerole"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE chat_messages "
        "ALTER COLUMN role TYPE varchar(20) USING role::varchar"
    )
    message_role.drop(op.get_bind(), checkfirst=True)
