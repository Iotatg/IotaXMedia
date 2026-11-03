# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from typing import Dict, List

from IotaXMedia.utils.cache import TTLCache

_stats_cache: TTLCache = TTLCache(128, 300)


async def record_play(chat_id: int, title: str, by: int = 0) -> None:
    """Increment per-chat play counters + per-track counts (best-effort)."""
    try:
        from IotaXMedia.core.mongo import mongodb

        await mongodb.stats.update_one(
            {"chat_id": chat_id},
            {"$inc": {"plays": 1, f"tracks.{_slug(title)}": 1}, "$set": {"last_title": title}},
            upsert=True,
        )
    except Exception:
        pass


async def get_stats(chat_id: int) -> Dict:
    cached = _stats_cache.get(chat_id)
    if cached is not None:
        return cached
    doc = {}
    try:
        from IotaXMedia.core.mongo import mongodb

        doc = await mongodb.stats.find_one({"chat_id": chat_id}) or {}
    except Exception:
        pass
    _stats_cache[chat_id] = doc
    return doc


def top_tracks(doc: Dict, limit: int = 5) -> List:
    tracks = doc.get("tracks", {}) or {}
    items = sorted(tracks.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [(k.replace("_", " ").strip(), v) for k, v in items]


def _slug(title: str) -> str:
    return (
        str(title)
        .lower()
        .replace(" ", "_")
        .replace(".", "")
        .replace("/", "_")[:60]
    )
