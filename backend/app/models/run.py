"""Run model for execution records."""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum

from backend.app.db.base import Base, IDMixin, TimestampMixin


class RunType(str, enum.Enum):
    """
    Type of run execution.

    PROOF: Proof/validation run - validates artifacts, generates reports
    ACTION: Action run - executes scripts, makes changes to assets
    """
    PROOF = "proof"
    ACTION = "action"


class RunStatus(str, enum.Enum):
    """Run execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Run(Base, IDMixin, TimestampMixin):
    """
    Run represents a system-participated execution instance.

    Key principle: Run is the "system's commitment" - proof that the system
    did/verified/recorded something, not just a status update.

    ProofRun: System validates artifacts, generates compliance reports
    ActionRun: System executes scripts, makes controlled changes
    """

    __tablename__ = "runs"

    # Run identification
    run_type = Column(SQLEnum(RunType), nullable=False, index=True)
    status = Column(SQLEnum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)

    # Related ticket
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    # Executor (who triggered this run)
    executed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Script/Validator information
    script_id = Column(String(100), nullable=True)  # Reference to script_specs
    validator_version = Column(String(50), nullable=True)  # Version of validator used
    rules_version = Column(String(50), nullable=True)  # Version of validation rules

    # Execution metadata
    inputs_manifest = Column(JSON, nullable=True)  # Hash list of input files
    outputs_manifest = Column(JSON, nullable=True)  # Hash list of output files
    execution_context = Column(JSON, nullable=True)  # Client info, environment, etc.

    # Execution logs
    stdout_log = Column(Text, nullable=True)
    stderr_log = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)  # Human-readable summary

    # Exit code (for script execution)
    exit_code = Column(Integer, nullable=True)

    # Relationships
    ticket = relationship("Ticket", back_populates="runs")
    executor = relationship("User", foreign_keys=[executed_by_id], back_populates="runs")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Run(id={self.id}, type={self.run_type.value}, "
            f"status={self.status.value}, ticket_id={self.ticket_id})>"
        )
