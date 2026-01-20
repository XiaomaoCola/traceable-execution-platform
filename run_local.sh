#!/bin/bash

# Create necessary directories
mkdir -p data/artifacts data/audit

# Export environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DATABASE_URL="postgresql://traceable_user:traceable_pass@localhost:5432/traceable_db"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="dev-secret-key-please-change-in-production-min-32-chars"
export ENVIRONMENT="development"
export ARTIFACT_STORAGE_TYPE="local"
export ARTIFACT_STORAGE_PATH="./data/artifacts"
export AUDIT_LOG_PATH="./data/audit"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
