"""
Script and validator registry.

This module manages the whitelist of scripts and validators that can be executed.
"""

from typing import Protocol, Any
from pathlib import Path
import json


class Validator(Protocol):
    """Protocol for artifact validators."""

    async def validate(self, artifact_data: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Validate an artifact.

        Args:
            artifact_data: Raw artifact data
            metadata: Artifact metadata (filename, type, etc.)

        Returns:
            Validation result with structure:
            {
                "valid": bool,
                "errors": list[str],
                "warnings": list[str],
                "report": dict[str, Any]  # Structured validation report
            }
        """
        ...


class ScriptSpec:
    """Specification for a registered script or validator."""

    def __init__(
        self,
        script_id: str,
        name: str,
        description: str,
        version: str,
        script_type: str,  # "proof" or "action"
        validator_class: str | None = None,
        script_path: str | None = None,
        requires_approval: bool = False
    ):
        self.script_id = script_id
        self.name = name
        self.description = description
        self.version = version
        self.script_type = script_type
        self.validator_class = validator_class
        self.script_path = script_path
        self.requires_approval = requires_approval


class ScriptRegistry:
    """Registry of whitelisted scripts and validators."""

    def __init__(self):
        self._scripts: dict[str, ScriptSpec] = {}
        self._load_builtin_scripts()

    def _load_builtin_scripts(self):
        """Load built-in proof validators."""

        # Built-in: Generic file hash validator
        self.register(ScriptSpec(
            script_id="proof.file_hash",
            name="File Hash Validator",
            description="Validates file integrity by checking SHA-256 hash",
            version="1.0.0",
            script_type="proof",
            validator_class="backend.app.services.validators.FileHashValidator"
        ))

        # Built-in: Config file format validator
        self.register(ScriptSpec(
            script_id="proof.config_format",
            name="Config Format Validator",
            description="Validates configuration file format and basic structure",
            version="1.0.0",
            script_type="proof",
            validator_class="backend.app.services.validators.ConfigFormatValidator"
        ))

    def register(self, spec: ScriptSpec) -> None:
        """
        Register a script or validator.

        Args:
            spec: Script specification
        """
        self._scripts[spec.script_id] = spec

    def get(self, script_id: str) -> ScriptSpec | None:
        """
        Get a script specification by ID.

        Args:
            script_id: Script ID

        Returns:
            Script specification or None if not found
        """
        return self._scripts.get(script_id)

    def list_all(self) -> list[ScriptSpec]:
        """List all registered scripts."""
        return list(self._scripts.values())

    def list_by_type(self, script_type: str) -> list[ScriptSpec]:
        """
        List scripts by type.

        Args:
            script_type: "proof" or "action"

        Returns:
            List of matching script specifications
        """
        return [s for s in self._scripts.values() if s.script_type == script_type]


# Global registry instance
script_registry = ScriptRegistry()
