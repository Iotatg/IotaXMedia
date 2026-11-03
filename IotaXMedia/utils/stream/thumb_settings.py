# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from IotaXMedia.core.mongo import mongodb

thumb_db = mongodb.thumb


async def is_thumb_on(chat_id: int) -> bool:
    """Album-art (thumbnail) display in stream updates. Default: ON (True)."""
    data = await thumb_db.find_one({"chat_id": chat_id})
    return bool(data.get("status", True)) if data else True


async def set_thumb(chat_id: int, status: bool) -> bool:
    await thumb_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": status}},
        upsert=True,
    )
    return status


async def thumb_on(chat_id: int) -> bool:
    return await set_thumb(chat_id, True)


async def thumb_off(chat_id: int) -> bool:
    return await set_thumb(chat_id, False)


async def toggle_thumb(chat_id: int) -> bool:
    data = await thumb_db.find_one({"chat_id": chat_id})
    if not data:
        await thumb_db.insert_one({"chat_id": chat_id, "status": False})
        return False
    new_status = not bool(data.get("status", True))
    await thumb_db.update_one(
        {"chat_id": chat_id},
        {"$set": {"status": new_status}},
    )
    return new_status
