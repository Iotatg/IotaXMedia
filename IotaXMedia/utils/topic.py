# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from typing import Optional

from IotaXMedia.utils.cache import TTLCache

_topic_cache: TTLCache = TTLCache(256, 1800)


async def get_topic_id(chat_id: int) -> Optional[int]:
    """Return the dedicated queue topic id for a chat, if set."""
    cached = _topic_cache.get(chat_id)
    if cached is not None:
        return cached
    try:
        from IotaXMedia.core.mongo import mongodb

        doc = await mongodb.topics.find_one({"chat_id": chat_id}, {"topic_id": 1})
        tid = int(doc["topic_id"]) if doc and doc.get("topic_id") else None
    except Exception:
        tid = None
    _topic_cache[chat_id] = tid
    return tid


async def set_topic_id(chat_id: int, topic_id: Optional[int]) -> None:
    try:
        from IotaXMedia.core.mongo import mongodb

        if topic_id:
            await mongodb.topics.update_one(
                {"chat_id": chat_id},
                {"$set": {"topic_id": topic_id}},
                upsert=True,
            )
        else:
            await mongodb.topics.delete_one({"chat_id": chat_id})
    except Exception:
        pass
    _topic_cache[chat_id] = topic_id
