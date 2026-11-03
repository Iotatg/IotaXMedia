# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["gift", "sendgift"]) & filters.group)
@AdminActual
async def gift_command(client, message: Message, _):
    """Send a gift to the chat (Bot API >= 9.x). Degrades gracefully otherwise."""
    if not hasattr(app, "send_gift"):
        return await message.reply_text(god_text("gifts unsupported on this bot api version"))
    parts = message.text.split(None, 1)
    gift_id = parts[1].strip() if len(parts) > 1 else None
    if not gift_id:
        return await message.reply_text(god_text("usage") + " : /gift <gift_id>")
    try:
        await app.send_gift(
            chat_id=message.chat.id,
            gift_id=gift_id,
        )
        await message.reply_text("🎁 " + god_text("gift sent") + ".")
    except Exception as e:
        await message.reply_text(god_text("gifts unsupported") + f" : {e}")
