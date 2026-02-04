from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from app.config.settings import settings
from app.models.schemas import SessionState


class SessionStore:
    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._memory: dict[str, tuple[datetime, str]] = {}

    async def connect(self) -> None:
        if settings.redis_url:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()

    def _expiry(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)

    async def get(self, session_id: str) -> SessionState | None:
        if self._redis:
            raw = await self._redis.get(session_id)
            if not raw:
                return None
            return SessionState.model_validate_json(raw)

        entry = self._memory.get(session_id)
        if not entry:
            return None
        expires_at, raw = entry
        if expires_at < datetime.now(timezone.utc):
            self._memory.pop(session_id, None)
            return None
        return SessionState.model_validate_json(raw)

    async def set(self, session: SessionState) -> None:
        raw = session.model_dump_json()
        if self._redis:
            await self._redis.setex(session.session_id, settings.session_ttl_seconds, raw)
            return

        self._memory[session.session_id] = (self._expiry(), raw)

    async def delete(self, session_id: str) -> None:
        if self._redis:
            await self._redis.delete(session_id)
            return
        self._memory.pop(session_id, None)


session_store = SessionStore()