# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["tip", "donate"]) & filters.group)
@language
async def tip_command(client, message: Message, _):
    """Send a Telegram Stars tip invoice (Bot API >= 7.8 with XTR)."""
    if not hasattr(app, "send_invoice"):
        return await message.reply_text(god_text("stars tips unsupported on this bot api"))
    parts = message.text.split(None, 1)
    amount = 1
    if len(parts) > 1 and parts[1].strip().isdigit():
        amount = max(1, min(1000, int(parts[1].strip())))
    try:
        await app.send_invoice(
            chat_id=message.chat.id,
            title=god_text("support iotaxmedia"),
            description=god_text("send stars to keep the music flowing"),
            payload=f"tip:{message.from_user.id}:{amount}",
            provider_token="",
            currency="XTR",
            prices=[{"label": "Stars", "amount": amount}],
        )
    except Exception as e:
        await message.reply_text(god_text("stars tips unsupported") + f" : {e}")
