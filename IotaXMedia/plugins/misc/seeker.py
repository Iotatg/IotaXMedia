# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio

from IotaXMedia.misc import db
from IotaXMedia.utils.database import get_active_chats, is_music_playing


async def timer():
    while not await asyncio.sleep(1):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            if not await is_music_playing(chat_id):
                continue
            playing = db.get(chat_id)
            if not playing:
                continue
            duration = int(playing[0]["seconds"])
            if duration == 0:
                continue
            if db[chat_id][0]["played"] >= duration:
                continue
            db[chat_id][0]["played"] += 1


def _borrow_mode() -> bool:



    import builtins

    return bool(getattr(builtins, "_IOTAX_CLONE_BORROW", False))


if not _borrow_mode():
    asyncio.create_task(timer())
