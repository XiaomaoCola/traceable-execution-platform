"""drop runs table and artifacts.run_id

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-04-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "g8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("artifacts_run_id_fkey", "artifacts", type_="foreignkey")
    op.drop_column("artifacts", "run_id")
    op.drop_table("runs")
    op.execute("DROP TYPE IF EXISTS runtype")
    op.execute("DROP TYPE IF EXISTS runstatus")


def downgrade() -> None:
    op.execute("""
        CREATE TYPE runtype AS ENUM ('proof', 'action')
    """)
    op.execute("""
        CREATE TYPE runstatus AS ENUM ('pending', 'running', 'success', 'failed', 'timeout')
    """)
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_type", sa.Enum("proof", "action", name="runtype"), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "success", "failed", "timeout", name="runstatus"), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("executed_by_id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.String(length=100), nullable=True),
        sa.Column("validator_version", sa.String(length=50), nullable=True),
        sa.Column("rules_version", sa.String(length=50), nullable=True),
        sa.Column("inputs_manifest", sa.JSON(), nullable=True),
        sa.Column("outputs_manifest", sa.JSON(), nullable=True),
        sa.Column("execution_context", sa.JSON(), nullable=True),
        sa.Column("stdout_log", sa.Text(), nullable=True),
        sa.Column("stderr_log", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["executed_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("artifacts", sa.Column("run_id", sa.Integer(), nullable=True))
    op.create_foreign_key("artifacts_run_id_fkey", "artifacts", "runs", ["run_id"], ["id"])
