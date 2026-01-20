"""
Run execution engine.

This module handles the actual execution of proof runs and action runs.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from backend.app.models.run import Run, RunStatus, RunType
from backend.app.models.artifact import Artifact
from backend.app.services.registry import script_registry
from backend.app.services.run_service import update_run_status
from backend.app.core.config import settings


logger = logging.getLogger(__name__)


class RunExecutor:
    """Executor for running proof and action runs."""

    async def execute_run(self, db: Session, run: Run) -> None:
        """
        Execute a run.

        Args:
            db: Database session
            run: Run to execute
        """
        try:
            # Update status to running
            await update_run_status(db, run.id, RunStatus.RUNNING)

            if run.run_type == RunType.PROOF:
                await self._execute_proof_run(db, run)
            elif run.run_type == RunType.ACTION:
                await self._execute_action_run(db, run)
            else:
                raise ValueError(f"Unknown run type: {run.run_type}")

        except asyncio.TimeoutError:
            logger.error(f"Run {run.id} timed out")
            await update_run_status(
                db, run.id, RunStatus.TIMEOUT,
                result_summary="Run execution timed out",
                stderr_log=f"Execution exceeded timeout of {settings.run_timeout_seconds} seconds"
            )

        except Exception as e:
            logger.exception(f"Run {run.id} failed with error: {e}")
            await update_run_status(
                db, run.id, RunStatus.FAILED,
                result_summary=f"Run failed: {str(e)}",
                stderr_log=str(e)
            )

    async def _execute_proof_run(self, db: Session, run: Run) -> None:
        """
        Execute a proof run (validation).

        Proof run workflow:
        1. Collect artifacts associated with this run
        2. Get validator from registry
        3. Run validation on each artifact
        4. Generate validation report
        5. Update run with results
        """
        logger.info(f"Executing proof run {run.id}")

        # Get associated artifacts
        artifacts = db.query(Artifact).filter(
            Artifact.run_id == run.id,
            Artifact.is_deleted == False
        ).all()

        if not artifacts:
            await update_run_status(
                db, run.id, RunStatus.FAILED,
                result_summary="No artifacts found to validate",
                stderr_log="Proof run requires at least one artifact"
            )
            return

        # Get validator
        script_spec = script_registry.get(run.script_id) if run.script_id else None

        # Build inputs manifest (hash list of input files)
        inputs_manifest = {
            "artifacts": [
                {
                    "id": artifact.id,
                    "filename": artifact.filename,
                    "sha256": artifact.sha256_hash,
                    "size_bytes": artifact.size_bytes
                }
                for artifact in artifacts
            ]
        }

        # Validation results
        validation_results = []
        all_valid = True

        # Validate each artifact
        for artifact in artifacts:
            try:
                # For now, basic validation: check hash integrity
                from backend.app.services.artifact_service import verify_artifact

                is_valid = await verify_artifact(db, artifact.id)

                validation_results.append({
                    "artifact_id": artifact.id,
                    "filename": artifact.filename,
                    "validation": "passed" if is_valid else "failed",
                    "hash_verified": is_valid
                })

                if not is_valid:
                    all_valid = False

            except Exception as e:
                logger.error(f"Failed to validate artifact {artifact.id}: {e}")
                validation_results.append({
                    "artifact_id": artifact.id,
                    "filename": artifact.filename,
                    "validation": "error",
                    "error": str(e)
                })
                all_valid = False

        # Generate report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run.id,
            "ticket_id": run.ticket_id,
            "validator": script_spec.name if script_spec else "default",
            "validator_version": script_spec.version if script_spec else "1.0.0",
            "total_artifacts": len(artifacts),
            "validation_results": validation_results,
            "overall_result": "passed" if all_valid else "failed"
        }

        # Update run with results
        result_summary = (
            f"Validation {'passed' if all_valid else 'failed'}: "
            f"{len(artifacts)} artifact(s) checked"
        )

        outputs_manifest = {
            "validation_report": report
        }

        await update_run_status(
            db, run.id,
            RunStatus.SUCCESS if all_valid else RunStatus.FAILED,
            result_summary=result_summary,
            stdout_log=f"Validated {len(artifacts)} artifacts\n" +
                      "\n".join([f"- {r['filename']}: {r['validation']}" for r in validation_results]),
            exit_code=0 if all_valid else 1
        )

        # Update run with manifests
        run.inputs_manifest = inputs_manifest
        run.outputs_manifest = outputs_manifest
        run.validator_version = script_spec.version if script_spec else "1.0.0"
        db.commit()

    async def _execute_action_run(self, db: Session, run: Run) -> None:
        """
        Execute an action run (script execution).

        This is a placeholder for future implementation.
        """
        logger.info(f"Executing action run {run.id}")

        # TODO: Implement action run execution
        # 1. Get script from registry
        # 2. Prepare execution environment (sandbox)
        # 3. Execute script with timeout
        # 4. Collect outputs and logs
        # 5. Update run with results

        await update_run_status(
            db, run.id, RunStatus.FAILED,
            result_summary="Action runs not yet implemented",
            stderr_log="Action run execution is not yet implemented"
        )


# Global executor instance
run_executor = RunExecutor()
