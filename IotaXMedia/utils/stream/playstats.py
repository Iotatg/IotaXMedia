# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT




import logging
from time import time

logger = logging.getLogger("IotaXMedia.playstats")

_title_cache: dict = {}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _col():
    from IotaXMedia.core.mongo import mongodb

    return mongodb.playstats


async def note_play(chat_id: int) -> None:
    """Record one track start for a chat (count + recency)."""
    try:
        cid = int(chat_id)
        now = int(time())
        await _col().update_one(
            {"_id": cid},
            {"$inc": {"plays": 1}, "$set": {"last_played": now}},
            upsert=True,
        )
    except Exception as e:
        logger.debug(f"note_play failed for {chat_id}: {e}")


async def get_last_played(chat_id: int) -> int:
    """Epoch of the chat's last track start (0 if never)."""
    try:
        doc = await _col().find_one({"_id": int(chat_id)})
        return int(doc.get("last_played", 0)) if doc else 0
    except Exception:
        return 0


async def get_top_chats(limit: int = 10) -> list:
    """Top chats by lifetime play count: [(chat_id, plays), ...]."""
    out = []
    try:
        cursor = _col().find({}, {"plays": 1}).sort("plays", -1).limit(limit)
        async for doc in cursor:
            plays = int(doc.get("plays", 0))
            if plays > 0:
                out.append((int(doc["_id"]), plays))
    except Exception as e:
        logger.debug(f"get_top_chats failed: {e}")
    return out


async def chat_title(client, chat_id: int):
    """Cached chat title lookup; failures cached as None."""
    key = (getattr(client, "id", 0), int(chat_id))
    if key in _title_cache:
        return _title_cache[key]
    title = None
    try:
        chat = await client.get_chat(chat_id)
        title = (
            getattr(chat, "title", None)
            or getattr(chat, "first_name", None)
            or str(chat_id)
        )
    except Exception:
        pass
    _title_cache[key] = title
    return title


async def leaderboard_block(client, limit: int = 10) -> str:
    """HTML block listing top-played chats, or empty string when none."""
    top = await get_top_chats(limit)
    if not top:
        return ""
    lines = ["\n<b>🏆 ᴛᴏᴘ 𝟷𝟶 ɢʀᴏᴜᴘꜱ (ꜱᴏɴɢꜱ ᴘʟᴀʏᴇᴅ)</b>"]
    for rank, (cid, plays) in enumerate(top, 1):
        medal = MEDALS.get(rank, f"<code>{rank}.</code>")
        name = await chat_title(client, cid) or f"<code>{cid}</code>"
        lines.append(f"{medal} <b>{name}</b> — <code>{plays}</code>")
    return "\n".join(lines) + "\n"
