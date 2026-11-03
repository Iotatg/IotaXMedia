# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["sleep", "stopafter"]) & filters.group)
@AdminActual
async def sleep_command(client, message: Message, _):
    """Stop playback after N minutes (schedule a /stop message)."""
    parts = message.text.split(None, 1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        return await message.reply_text(
            f"{god_text('usage')} : /sleep <minutes>\n{god_text('example')} : /sleep 30"
        )
    mins = int(parts[1].strip())
    if mins < 1 or mins > 1440:
        return await message.reply_text(god_text("enter minutes between 1 and 1440"))
    when = datetime.now() + timedelta(minutes=mins)
    try:
        await app.send_message(message.chat.id, "/stop", when=when)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    await message.reply_text(
        f"⏱ {god_text('sleep timer set')} : {mins} {god_text('min')}\n"
        f"🕒 {when.strftime('%H:%M')} — {god_text('playback will stop')}."
    )
