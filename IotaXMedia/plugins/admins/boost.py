# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.misc import db
from IotaXMedia.utils.boost import get_boost_level
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["boost", "chatboost"]) & filters.group)
@AdminActual
async def boost_command(client, message: Message, _):
    try:
        chat_id = message.chat.id
        info = await get_boost_level(chat_id)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    perks = {
        1: god_text("custom emoji in chat name"),
        2: god_text("15s pinned stories"),
        3: god_text("20 chat folders / 10 pinned chats"),
        4: god_text("10mb bio upload"),
        5: god_text("emoji status"),
    }
    next_perk = next((lv for lv in sorted(perks) if lv > info["level"]), None)
    text = (
        f"{god_text('chat boost status')} :\n\n"
        f"❥ {god_text('boost level')} : {info['level']}\n"
        f"❥ {god_text('total boosts')} : {info['count']}\n"
    )
    if next_perk:
        need = next_perk
        text += f"\n{god_text('next perk at level')} {need} : {perks[need]}"
    else:
        text += f"\n{god_text('max perks unlocked')} 🔥"
    await message.reply_text(text, disable_web_page_preview=True)
