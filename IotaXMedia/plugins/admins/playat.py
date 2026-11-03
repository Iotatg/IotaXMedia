# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import re
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text

TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


@app.on_message(filters.command(["playat", "schedule"]) & filters.group)
@AdminActual
async def playat_command(client, message: Message, _):
    """Schedule a track to auto-play later.

    Sends a scheduled `/play <query>` message; when it is delivered the
    normal play pipeline runs (bot must be admin, which is standard for
    music groups). Reuses the entire existing play flow — no duplication.
    """
    parts = message.text.split(None, 2)
    if len(parts) < 3 or not TIME_RE.match(parts[1]):
        return await message.reply_text(
            f"{god_text('usage')} : /playat HH:MM <song name>\n"
            f"{god_text('example')} : /playat 21:30 arijit singh"
        )
    hh, mm = TIME_RE.match(parts[1]).groups()
    query = parts[2].strip()
    now = datetime.now()
    target = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    try:
        await app.send_message(message.chat.id, f"/play {query}", when=target)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    await message.reply_text(
        f"⏰ {god_text('scheduled')} : {query}\n"
        f"🕒 {target.strftime('%d-%m-%Y %H:%M')}\n\n"
        f"{god_text('bot will auto-play if it is admin in this chat')}."
    )
