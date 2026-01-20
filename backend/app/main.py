"""
FastAPI application entry point.

Traceable Execution Platform - A backend for traceable, recoverable, controlled execution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.api import health, auth, tickets, assets, runs, artifacts


# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="A traceable and recoverable controlled execution backend platform",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc"
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


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    print(f"🚀 Starting {settings.project_name}")
    print(f"📊 Environment: {settings.environment}")
    print(f"📁 Artifact storage: {settings.artifact_storage_type} ({settings.artifact_storage_path})")
    print(f"📝 Audit logs: {settings.audit_log_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    print(f"👋 Shutting down {settings.project_name}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Traceable Execution Platform API",
        "version": "0.1.0",
        "docs": f"{settings.api_v1_prefix}/docs"
    }
