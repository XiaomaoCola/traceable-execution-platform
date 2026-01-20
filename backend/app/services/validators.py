"""Built-in validators for proof runs."""

from typing import Any
import json


class FileHashValidator:
    """
    Basic file hash validator.

    Validates that file hash matches expected value.
    """

    async def validate(self, artifact_data: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate file hash."""
        import hashlib

        # Compute hash
        computed_hash = hashlib.sha256(artifact_data).hexdigest()
        expected_hash = metadata.get("expected_hash")

        valid = computed_hash == expected_hash if expected_hash else True

        return {
            "valid": valid,
            "errors": [] if valid else [f"Hash mismatch: expected {expected_hash}, got {computed_hash}"],
            "warnings": [],
            "report": {
                "computed_hash": computed_hash,
                "expected_hash": expected_hash,
                "file_size": len(artifact_data)
            }
        }


class ConfigFormatValidator:
    """
    Config file format validator.

    Validates that config file is valid JSON/YAML/INI.
    """

    async def validate(self, artifact_data: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate config file format."""
        errors = []
        warnings = []
        report = {}

        filename = metadata.get("filename", "")

        # Try JSON
        if filename.endswith(".json"):
            try:
                config = json.loads(artifact_data.decode("utf-8"))
                report["format"] = "json"
                report["keys"] = list(config.keys()) if isinstance(config, dict) else None
            except Exception as e:
                errors.append(f"Invalid JSON: {str(e)}")

        # Try YAML
        elif filename.endswith((".yaml", ".yml")):
            try:
                import yaml
                config = yaml.safe_load(artifact_data.decode("utf-8"))
                report["format"] = "yaml"
                report["keys"] = list(config.keys()) if isinstance(config, dict) else None
            except Exception as e:
                errors.append(f"Invalid YAML: {str(e)}")

        # Try INI
        elif filename.endswith(".ini"):
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read_string(artifact_data.decode("utf-8"))
                report["format"] = "ini"
                report["sections"] = list(config.sections())
            except Exception as e:
                errors.append(f"Invalid INI: {str(e)}")

        else:
            warnings.append(f"Unknown config format for file: {filename}")
            report["format"] = "unknown"

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "report": report
        }
