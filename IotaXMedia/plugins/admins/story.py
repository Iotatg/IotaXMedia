# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command(["story", "poststory"]) & filters.private)
@language
async def story_command(client, message: Message, _):
    """Post the replied media as a Story (Bot API >= 8.x). Degrades gracefully."""
    if not hasattr(app, "send_story"):
        return await message.reply_text(god_text("stories unsupported on this bot api version"))
    media = message.reply_to_message
    if not media or not (media.photo or media.video):
        return await message.reply_text(god_text("reply to a photo or video to post a story"))
    try:
        if media.photo:
            await app.send_story(photo=media.photo.file_id)
        else:
            await app.send_story(video=media.video.file_id)
        await message.reply_text("📸 " + god_text("story posted") + ".")
    except Exception as e:
        await message.reply_text(god_text("stories unsupported") + f" : {e}")
