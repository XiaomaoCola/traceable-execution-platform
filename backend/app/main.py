"""
FastAPI application entry point.

Traceable Execution Platform - A backend for traceable, recoverable, controlled execution.
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.api import health, auth, tickets, assets, runs, artifacts, chat


# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan: startup and shutdown."""
    # --- startup ---
    print(f"🚀 Starting {settings.project_name}")
    print(f"📊 Environment: {settings.environment}")
    print(f"📁 Artifact storage: {settings.artifact_storage_type} ({settings.artifact_storage_path})")
    print(f"📝 Audit logs: {settings.audit_log_path}")

    if settings.redis_url:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        print(f"🔴 Redis connected: {settings.redis_url}")
    else:
        app.state.redis = None
        print("⚠️  Redis not configured — Redis-dependent features will return 503")

    yield

    # --- shutdown ---
    if app.state.redis is not None:
        await app.state.redis.aclose()
    print(f"👋 Shutting down {settings.project_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="A traceable and recoverable controlled execution backend platform",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(tickets.router, prefix=settings.api_v1_prefix)
app.include_router(assets.router, prefix=settings.api_v1_prefix)
app.include_router(runs.router, prefix=settings.api_v1_prefix)
app.include_router(artifacts.router, prefix=settings.api_v1_prefix)
app.include_router(chat.router, prefix=settings.api_v1_prefix)



@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Traceable Execution Platform API",
        "version": "0.1.0",
        "docs": f"{settings.api_v1_prefix}/docs"
    }
