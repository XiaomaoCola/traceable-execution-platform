"""
Runtime state store for run execution state.

Supports in-memory and Redis backends.
"""

from abc import ABC, abstractmethod
from typing import Any
import json

from backend.app.core.config import settings


class StateStore(ABC):
    """Abstract base class for state storage backends."""

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], expire: int | None = None) -> bool:
        """
        Set a value in the state store.

        Args:
            key: State key
            value: State value (must be JSON-serializable)
            expire: Optional expiration time in seconds

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None:
        """
        Get a value from the state store.

        Args:
            key: State key

        Returns:
            State value or None if not found
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a key from the state store.

        Args:
            key: State key

        Returns:
            True if key existed and was deleted
        """
        pass


class InMemoryStateStore(StateStore):
    """In-memory state store (for development/testing)."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def set(self, key: str, value: dict[str, Any], expire: int | None = None) -> bool:
        """Set value in memory."""
        self._store[key] = value
        # Note: expire not implemented for in-memory store
        return True

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from memory."""
        return self._store.get(key)

    async def delete(self, key: str) -> bool:
        """Delete key from memory."""
        if key in self._store:
            del self._store[key]
            return True
        return False


class RedisStateStore(StateStore):
    """Redis-backed state store (for production)."""

    def __init__(self, redis_url: str):
        """
        Initialize Redis state store.

        Args:
            redis_url: Redis connection URL
        """
        # Import redis here to make it optional
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError("redis package required for RedisStateStore")

        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def set(self, key: str, value: dict[str, Any], expire: int | None = None) -> bool:
        """Set value in Redis."""
        serialized = json.dumps(value)
        await self.redis.set(key, serialized, ex=expire)
        return True

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from Redis."""
        value = await self.redis.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        result = await self.redis.delete(key)
        return result > 0


def get_state_store() -> StateStore:
    """
    Get configured state storage backend.

    Returns:
        Configured state store instance
    """
    # For now, always use in-memory store
    # TODO: Add config option to use Redis in production
    if settings.environment == "production" and settings.redis_url:
        try:
            return RedisStateStore(settings.redis_url)
        except ImportError:
            # Fall back to in-memory if redis not available
            pass

    return InMemoryStateStore()


# Global state store instance
state_store = get_state_store()
