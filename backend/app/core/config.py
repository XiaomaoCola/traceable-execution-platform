"""Application configuration using Pydantic Settings."""

from functools import lru_cache

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
    # Database (sync, for migrations)
    sync_database_url: str

    # Redis (optional; if not set, Redis-dependent features return 503)
    redis_url: str | None = None

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Storage
    artifact_storage_type: Literal["local", "minio", "s3"] = "local"
    artifact_storage_path: str = "./data/artifacts"

    # MinIO/S3
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_use_ssl: bool = False
    minio_bucket_artifacts: str = "artifacts"

    # Audit
    audit_log_path: str = "./data/audit"

    # Run Execution
    run_timeout_seconds: int = 300  # 5 minutes default
    max_artifact_size_mb: int = 100

    # LiteLLM Gateway
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局 Settings 单例。

    用 @lru_cache 替代模块级 settings = Settings()，让实例化推迟到
    第一次调用时，而不是 import 时。好处：
      - 测试可通过 get_settings.cache_clear() + monkeypatch 替换返回值
      - CI 环境没有 .env 时，只要测试不触发路径就不会崩溃
      - FastAPI 路由可用 Depends(get_settings) 接收，测试用 dependency_overrides 覆盖
    """
    return Settings()
