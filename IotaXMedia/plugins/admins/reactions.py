# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.misc import db
from IotaXMedia.utils.decorators import language


@app.on_message(filters.command("like") & filters.group)
@language
async def like_command(client, message: Message, _):
    chat_id = message.chat.id
    pl = db.get(chat_id)
    if not pl:
        return await message.reply_text(_["queue_2"])
    mystic = pl[0].get("mystic")
    mid = getattr(mystic, "id", None)
    if not mid:
        return await message.reply_text("ᴀʙʜɪ ɪs ᴄʜᴀᴛ ᴍᴇɪɴ ᴋσɪ ᴩʟᴀʏ ɴᴀʜɪ.")
    try:



        await app.send_reaction(chat_id, mid, emoji="❤")
    except Exception:
        pass
    pl[0]["reactions"] = int(pl[0].get("reactions", 0)) + 1
    await message.reply_text(f"💗 ʟɪᴋᴇᴅ ! ᴛσᴛᴀʟ : {pl[0]['reactions']}")


@app.on_message(filters.command("reactions") & filters.group)
@language
async def reactions_command(client, message: Message, _):
    chat_id = message.chat.id
    pl = db.get(chat_id)
    if not pl:
        return await message.reply_text(_["queue_2"])
    await message.reply_text(f"❤ ʀᴇᴀᴄᴛɪσηs : {int(pl[0].get('reactions', 0))}")

