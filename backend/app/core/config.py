"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
# BaseSettings：把「环境变量 / .env 文件」自动变成 Python 对象。
# SettingsConfigDict：告诉 BaseSettings「去哪里读、怎么读」。
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        # 配置从 .env 文件读，相当于告诉Pydantic “除了系统环境变量，再额外去读一个 .env 文件”。没有这行的话，只读系统环境变量，不读 .env。
        env_file_encoding="utf-8",
        # .env 用 utf-8 编码读。
        case_sensitive=False,
        # 环境变量大小写不敏感，比如 .env 中 DATABASE_URL=... 或者 database_url=... 都可以匹配 database_url: str。
        extra="ignore"
        # .env 里有多余变量，也不会报错。
    )

    # API Settings
    project_name: str = "Traceable Execution Platform"
    api_v1_prefix: str = "/api/v1"
    # "/api/v1"属于默认配置，最终运行时应该用 .env / 环境变量覆盖。
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
