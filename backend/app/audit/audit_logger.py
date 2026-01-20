"""
Append-only audit logger.

All audit events are written to an immutable log file that can be used
for compliance, forensics, and dispute resolution.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from backend.app.audit.events import AuditEvent
from backend.app.core.config import settings


class AuditLogger:
    """
    Append-only audit logger.

    Features:
    - Append-only writes (never modify existing logs)
    - Structured JSON format for machine parsing
    - Human-readable text format for quick review
    - Automatic log rotation by date
    """

    def __init__(self, log_dir: str):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup Python logger for audit events
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Don't propagate to root logger

    def _get_log_file_path(self, prefix: str = "audit") -> Path:
        """
        Get log file path for current date.

        Args:
            prefix: Log file prefix

        Returns:
            Path to log file
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{prefix}_{date_str}.jsonl"

    async def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        # Write to JSON Lines file (for machine parsing)
        json_log_file = self._get_log_file_path("audit")
        with open(json_log_file, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

        # Also write human-readable format
        text_log_file = self._get_log_file_path("audit_readable")
        with open(text_log_file, "a", encoding="utf-8") as f:
            f.write(event.to_log_line() + "\n")

        # Log to Python logger as well
        self.logger.info(
            f"AUDIT: {event.event_type.value} | {event.action}",
            extra={
                "event_type": event.event_type.value,
                "actor_id": event.actor_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
            }
        )

    async def query(
        self,
        event_type: str | None = None,
        actor_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditEvent]:
        """
        Query audit logs (basic implementation).

        For production, consider using a database or log aggregation system.

        Args:
            event_type: Filter by event type
            actor_id: Filter by actor ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results

        Returns:
            List of matching audit events
        """
        events = []

        # Read all log files in date range
        for log_file in sorted(self.log_dir.glob("audit_*.jsonl")):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = AuditEvent.model_validate_json(line)

                        # Apply filters
                        if event_type and event.event_type != event_type:
                            continue
                        if actor_id and event.actor_id != actor_id:
                            continue
                        if resource_type and event.resource_type != resource_type:
                            continue
                        if resource_id and event.resource_id != resource_id:
                            continue
                        if start_date and event.timestamp < start_date:
                            continue
                        if end_date and event.timestamp > end_date:
                            continue

                        events.append(event)

                        if len(events) >= limit:
                            return events

                    except Exception as e:
                        # Log parsing error but continue
                        logging.warning(f"Failed to parse audit log line: {e}")
                        continue

        return events


# Global audit logger instance
audit_logger = AuditLogger(settings.audit_log_path)
