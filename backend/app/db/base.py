"""SQLAlchemy declarative base and common model mixins."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base


# Declarative base for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class IDMixin:
    """Mixin for integer primary key."""

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
