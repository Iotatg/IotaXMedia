# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.misc import db
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["pin", "pinnow"]) & filters.group)
@AdminActual
async def pin_nowplaying(client, message: Message, _):
    pl = db.get(message.chat.id)
    if not pl:
        return await message.reply_text(_["queue_2"])
    mystic = pl[0].get("mystic")
    mid = getattr(mystic, "id", None)
    if not mid:
        return await message.reply_text(god_text("nothing playing to pin"))
    try:
        await app.pin_chat_message(
            message.chat.id, mid, disable_notification=True
        )
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    await message.reply_text("📌 " + god_text("pinned now-playing") + ".")


@app.on_message(filters.command(["unpin", "unpinnow"]) & filters.group)
@AdminActual
async def unpin_nowplaying(client, message: Message, _):
    try:
        await app.unpin_chat_message(message.chat.id)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    await message.reply_text("📌 " + god_text("unpinned") + ".")
