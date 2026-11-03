# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Mongo helpers for mood-based sticker packs (sticker-to-sticker replies)."""
from datetime import datetime, timezone

from IotaXMedia.core.mongo import mongodb

_col = mongodb.sticker_packs


def _now():
    return datetime.now(timezone.utc)


async def add_sticker_to_pack(mood: str, file_id: str, added_by: int = 0) -> None:
    await _col.update_one(
        {"_id": mood.lower()},
        {
            "$addToSet": {"file_ids": file_id},
            "$set": {"updated_at": _now(), "updated_by": added_by},
        },
        upsert=True,
    )


async def remove_sticker_from_pack(mood: str, file_id: str) -> bool:
    result = await _col.update_one(
        {"_id": mood.lower()}, {"$pull": {"file_ids": file_id}}
    )
    return result.modified_count > 0


async def get_stickers_for_mood(mood: str) -> list:
    doc = await _col.find_one({"_id": mood.lower()})
    return doc.get("file_ids", []) if doc else []


async def list_all_sticker_packs() -> dict:
    docs = await _col.find({}).to_list(1000)
    return {
        d["_id"]: len(d.get("file_ids", []))
        for d in docs
        if isinstance(d["_id"], str)
    }


async def clear_sticker_pack(mood: str) -> int:
    doc = await _col.find_one({"_id": mood.lower()})
    count = len(doc.get("file_ids", [])) if doc else 0
    await _col.delete_one({"_id": mood.lower()})
    return count
