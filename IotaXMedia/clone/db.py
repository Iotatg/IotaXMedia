# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone persistence — uses the main ``Iota`` Mongo database for clone
records + per-clone settings/customization. A clone can later override its
own database via ``set_clone_mongo``; that URI is only used *inside* the
clone's child process, never here (the parent process must always be able
to manage clone lifecycle).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from IotaXMedia.core.mongo import mongodb


_clones_col = None
_settings_col = None


def _clones():
    global _clones_col
    if _clones_col is None:
        _clones_col = mongodb.iotax_clones
    return _clones_col


def _settings():
    global _settings_col
    if _settings_col is None:
        _settings_col = mongodb.iotax_clone_settings
    return _settings_col



async def get_clone(bot_token: str) -> Optional[Dict[str, Any]]:
    """Return clone record keyed by bot_token (empty after strip)."""
    if not bot_token:
        return None
    token = bot_token.strip()
    return await _clones().find_one({"_id": token})


async def get_clone_by_id(bot_id: int) -> Optional[Dict[str, Any]]:
    return await _clones().find_one({"bot_id": int(bot_id)})


async def get_all_clones() -> List[Dict[str, Any]]:
    cursor = _clones().find({})
    return [doc async for doc in cursor]


async def get_clones_by_owner(owner_id: int) -> List[Dict[str, Any]]:
    cursor = _clones().find({"owner_id": int(owner_id)})
    return [doc async for doc in cursor]


async def add_clone(
    bot_token: str,
    bot_id: int,
    username: str,
    owner_id: int,
) -> Dict[str, Any]:
    doc = {
        "_id": bot_token.strip(),
        "bot_id": int(bot_id),
        "username": (username or "").lstrip("@"),
        "owner_id": int(owner_id),
        "status": "pending",
        "added_at": int(__import__("time").time()),
        "last_pid": None,
        "last_started": None,
        "last_stopped": None,
        "error": None,
    }
    await _clones().update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    return doc


async def update_clone(bot_token: str, **fields: Any) -> None:
    if not fields:
        return
    await _clones().update_one({"_id": bot_token.strip()}, {"$set": fields})


async def delete_clone(bot_token: str) -> bool:
    """Full delete — clone record AND all its settings/customization."""
    res = await _clones().delete_one({"_id": bot_token.strip()})
    await _settings().delete_many({"clone_id": bot_token.strip()})
    return res.deleted_count > 0


async def delete_clone_but_settings(bot_token: str) -> bool:
    """Delete the clone record but KEEP its customization (for re-clone)."""
    res = await _clones().delete_one({"_id": bot_token.strip()})
    return res.deleted_count > 0


async def delete_clone_by_id(bot_id: int) -> bool:
    doc = await get_clone_by_id(int(bot_id))
    if not doc:
        return False
    return await delete_clone(doc["_id"])


async def count_clones() -> int:
    return await _clones().count_documents({})


async def get_clone_owner(bot_token: str) -> Optional[int]:
    doc = await get_clone(bot_token)
    return doc.get("owner_id") if doc else None


async def set_clone_status(
    bot_token: str,
    status: str,
    *,
    pid: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    import time
    fields: Dict[str, Any] = {"status": status}
    if pid is not None:
        fields["last_pid"] = int(pid)
    if error is not None:
        fields["error"] = str(error)[:500]
    elif status == "running":
        fields["last_started"] = int(time.time())
        fields["error"] = None
    elif status == "stopped":
        fields["last_stopped"] = int(time.time())
    await update_clone(bot_token, **fields)


async def purge_clones() -> int:
    """Drop every clone record + every setting (sudo/owner only)."""
    await _settings().delete_many({})
    res = await _clones().delete_many({})
    return res.deleted_count or 0



async def get_clone_setting(clone_id: str, key: str, default: Any = None) -> Any:
    doc = await _settings().find_one({"_id": f"{clone_id}:{key}"})
    return doc.get("value") if doc else default


async def set_clone_setting(clone_id: str, key: str, value: Any) -> None:
    await _settings().update_one(
        {"_id": f"{clone_id}:{key}"},
        {"$set": {"clone_id": clone_id, "key": key, "value": value}},
        upsert=True,
    )


async def del_clone_setting(clone_id: str, key: str) -> bool:
    res = await _settings().delete_one({"_id": f"{clone_id}:{key}"})
    return res.deleted_count > 0


async def get_all_clone_settings(clone_id: str) -> Dict[str, Any]:
    cursor = _settings().find({"clone_id": clone_id})
    docs = [doc async for doc in cursor]

    mapping = {}
    for doc in docs:
        k = doc.get("key")
        if not k:
            continue
        mapping[k] = doc.get("value")
    return mapping
