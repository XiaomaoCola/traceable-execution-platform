"""Run schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any

from backend.app.models.run import RunType, RunStatus


class RunBase(BaseModel):
    """Base run schema."""
    run_type: RunType
    script_id: str | None = None
    execution_context: dict[str, Any] | None = None


class RunCreate(RunBase):
    """Schema for creating a new run."""
    ticket_id: int


class RunUpdate(BaseModel):
    """Schema for updating run status (internal use)."""
    status: RunStatus | None = None
    stdout_log: str | None = None
    stderr_log: str | None = None
    result_summary: str | None = None
    exit_code: int | None = None
    outputs_manifest: dict[str, Any] | None = None


class RunResponse(RunBase):
    """Schema for run response."""
    id: int
    status: RunStatus
    ticket_id: int
    executed_by_id: int
    validator_version: str | None = None
    rules_version: str | None = None
    inputs_manifest: dict[str, Any] | None = None
    outputs_manifest: dict[str, Any] | None = None
    execution_context: dict[str, Any] | None = None
    result_summary: str | None = None
    exit_code: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RunDetailResponse(RunResponse):
    """Schema for detailed run response including logs."""
    stdout_log: str | None = None
    stderr_log: str | None = None

    model_config = ConfigDict(from_attributes=True)
