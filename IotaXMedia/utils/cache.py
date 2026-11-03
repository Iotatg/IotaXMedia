# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

import time
from typing import Any, Optional

from IotaXMedia.core.mongo import mongodb

cache_coll = mongodb.cache


class TTLCache:
    """Small in-memory LRU-with-TTL cache for hot, process-local data."""

    def __init__(self, maxsize: int = 512, ttl: int = 600):
        self._data: dict[str, tuple[float, Any]] = {}
        self._max = maxsize
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if not item:
            return None
        exp, val = item
        if exp < time.time():
            self._data.pop(key, None)
            return None
        return val

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: str, val: Any) -> None:
        self.set(key, val)

    def set(self, key: str, val: Any, ttl: Optional[int] = None) -> None:
        if len(self._data) >= self._max:
            try:
                oldest = min(self._data, key=lambda k: self._data[k][0])
                self._data.pop(oldest, None)
            except ValueError:
                pass
        self._data[key] = (time.time() + (ttl if ttl is not None else self._ttl), val)

    def clear(self) -> None:
        self._data.clear()

    def pop(self, key: str, default: Any = None) -> Any:
        item = self._data.pop(key, None)
        return item[1] if item else default


async def mongo_cache_get(key: str) -> Optional[Any]:
    """Persistent cache backed by MongoDB (survives restarts)."""
    doc = await cache_coll.find_one({"_id": key})
    if not doc:
        return None
    if doc.get("exp", 0) < time.time():
        await cache_coll.delete_one({"_id": key})
        return None
    return doc.get("value")


async def mongo_cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    await cache_coll.update_one(
        {"_id": key},
        {"$set": {"value": value, "exp": time.time() + ttl}},
        upsert=True,
    )
