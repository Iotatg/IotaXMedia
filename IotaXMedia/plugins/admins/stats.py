# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text
from IotaXMedia.utils.playstats import get_stats, top_tracks
from IotaXMedia.utils.boost import get_boost_level


@app.on_message(filters.command(["stats", "chatstats"]) & filters.group)
@AdminActual
async def stats_command(client, message: Message, _):
    try:
        chat_id = message.chat.id
        doc = await get_stats(chat_id)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    plays = int(doc.get("plays", 0))
    boost = await get_boost_level(chat_id)
    top = top_tracks(doc)
    text = (
        f"{god_text('chat music stats')} :\n\n"
        f"❥ {god_text('total plays')} : {plays}\n"
        f"❥ {god_text('boost level')} : {boost['level']}\n"
        f"❥ {god_text('last track')} : {doc.get('last_title', '—')}\n\n"
    )
    if top:
        text += f"{god_text('top tracks')} :\n"
        for i, (t, c) in enumerate(top, 1):
            text += f"{i}. {t} — {c}x\n"
    else:
        text += god_text("no plays recorded yet")
    await message.reply_text(text, disable_web_page_preview=True)
