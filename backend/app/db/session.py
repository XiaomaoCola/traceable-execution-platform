"""Database session management(async)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.config import settings


# # Create database engine
# engine = create_engine(
#     settings.database_url,
#     pool_pre_ping=True,  # Verify connections before using them
#     echo=settings.environment == "development"  # Log SQL in development
# )
#
# # Create session factory
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
#
# def get_db() -> Session:
#     """
#     FastAPI dependency for database sessions.
#
#     Yields a database session and ensures it's closed after use.
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import settings


# Create async database engine
engine = create_async_engine(
    settings.database_url,          # 必须是 async URL
    pool_pre_ping=True,
    echo=settings.environment == "development",
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,         # 很建议开着，避免 commit 后对象过期
)

async def get_db() -> AsyncSession:
    """
    FastAPI dependency for async database sessions.

    Yields a database session and ensures it's closed after use.
    """
    async with AsyncSessionLocal() as db:
        yield db

