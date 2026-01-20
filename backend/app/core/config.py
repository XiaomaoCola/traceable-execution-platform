"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Settings
    project_name: str = "Traceable Execution Platform"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Storage
    artifact_storage_type: Literal["local", "minio", "s3"] = "local"
    artifact_storage_path: str = "./data/artifacts"

    # MinIO/S3 (optional, for future)
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None

    # Audit
    audit_log_path: str = "./data/audit"

    # Run Execution
    run_timeout_seconds: int = 300  # 5 minutes default
    max_artifact_size_mb: int = 100


# Global settings instance
settings = Settings()
