# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Dict

from IotaXMedia import app
from IotaXMedia.utils.cache import TTLCache

_boost_cache = TTLCache(maxsize=256, ttl=1800)


async def get_boost_level(chat_id: int) -> Dict[str, int]:
    """Return {'level': int, 'count': int} for a chat (cached 30m).

    Telegram unlocks perks by boost level: L1 = custom emoji in name,
    L2 = 15s pinned stories, L3 = 20-chat folders, L4 = 10MB bio upload,
    L5 = emoji status, etc. Bots read this to gate premium-style features.
    """
    key = str(chat_id)
    cached = _boost_cache.get(key)
    if cached is not None:
        return cached
    try:
        chat = await app.get_chat(chat_id)
        level = int(getattr(chat, "boost_level", 0) or 0)
        count = int(getattr(chat, "boost_count", 0) or 0)
    except Exception:
        level, count = 0, 0
    data = {"level": level, "count": count}
    _boost_cache.set(key, data)
    return data
