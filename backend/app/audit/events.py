"""Audit event definitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"

    # User management events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

    # Asset events
    ASSET_CREATED = "asset.created"
    ASSET_UPDATED = "asset.updated"
    ASSET_DELETED = "asset.deleted"

    # Ticket events
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_APPROVED = "ticket.approved"
    TICKET_CLOSED = "ticket.closed"

    # Run events (critical for traceability)
    RUN_CREATED = "run.created"
    RUN_STARTED = "run.started"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_TIMEOUT = "run.timeout"

    # Artifact events (critical for evidence chain)
    ARTIFACT_UPLOADED = "artifact.uploaded"
    ARTIFACT_DOWNLOADED = "artifact.downloaded"
    ARTIFACT_DELETED = "artifact.deleted"
    ARTIFACT_VERIFIED = "artifact.verified"


class AuditEvent(BaseModel):
    """
    Immutable audit event record.

    This represents a single audit log entry that cannot be modified
    once created. All events are append-only.
    """

    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Who performed the action
    actor_id: int | None = None  # User ID (None for system events)
    actor_username: str | None = None

    # What was affected
    resource_type: str | None = None  # e.g., "ticket", "run", "artifact"
    resource_id: int | None = None

    # Details about the event
    action: str  # Human-readable action description
    details: dict[str, Any] | None = None  # Additional context

    # Request metadata
    ip_address: str | None = None
    user_agent: str | None = None

    # Result
    success: bool = True
    error_message: str | None = None

    class Config:
        frozen = True  # Make the model immutable

    def to_log_line(self) -> str:
        """
        Convert event to a structured log line.

        Format: timestamp|event_type|actor|resource|success|action
        """
        actor = f"{self.actor_username}({self.actor_id})" if self.actor_id else "system"
        resource = f"{self.resource_type}:{self.resource_id}" if self.resource_type else "none"
        success_str = "SUCCESS" if self.success else "FAILED"

        return (
            f"{self.timestamp.isoformat()}|"
            f"{self.event_type.value}|"
            f"{actor}|"
            f"{resource}|"
            f"{success_str}|"
            f"{self.action}"
        )
