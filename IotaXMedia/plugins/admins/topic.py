# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text
from IotaXMedia.utils.topic import get_topic_id, set_topic_id

TOPIC_NAME = "🎵 IotaXMedia Queue"


@app.on_message(filters.command(["topic", "queuetopic"]) & filters.group)
@AdminActual
async def topic_command(client, message: Message, _):
    chat = message.chat
    if not getattr(chat, "is_forum", False):
        return await message.reply_text(god_text("this chat is not a forum / supergroup topics"))

    parts = message.text.split(None, 1)
    arg = parts[1].strip().lower() if len(parts) > 1 else ""

    if arg in ("off", "disable", "0"):
        await set_topic_id(chat.id, None)
        return await message.reply_text(god_text("queue topic disabled") + ".")

    existing = await get_topic_id(chat.id)
    if existing:
        return await message.reply_text(
            f"{god_text('queue topic already set')} : <a href='https://t.me/c/{str(chat.id)[4:]}/{existing}'>{TOPIC_NAME}</a>"
        )
    try:
        topic = await app.create_forum_topic(chat.id, TOPIC_NAME)
        await set_topic_id(chat.id, topic.message_thread_id)
    except Exception as e:
        return await message.reply_text(f"ᴇʀʀσʀ : {e}")
    await message.reply_text(
        f"✅ {god_text('queue topic created')} : {TOPIC_NAME}\n"
        f"{god_text('now-playing and queue cards route here')}."
    )
