# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Queue management: clear, remove, playnext, replay, nowplaying."""
from __future__ import annotations

from pyrogram import filters
from pyrogram.types import Message

from config import BANNED_USERS
from IotaXMedia import app
from IotaXMedia.core.call import StreamController
from IotaXMedia.misc import db
from IotaXMedia.plugins.Manager.anonymous import mask_by
from IotaXMedia.utils.admin_filters import admin_filter
from IotaXMedia.utils.database import get_cmode, is_active_chat, is_music_playing
from IotaXMedia.utils.decorators.language import language
from IotaXMedia.utils.formatters import normalize_duration, stream_type_label
from IotaXMedia.utils.god_style import god_text, stream_card, SYM


def _chat_id_from_message(message: Message) -> int:
    return message.chat.id


async def _resolve_chat(message: Message) -> int | None:
    cmd = (message.command[0] if message.command else "").lower()
    if cmd.startswith("c"):
        chat_id = await get_cmode(message.chat.id)
        return chat_id
    return message.chat.id


@app.on_message(
    filters.command(["clearqueue", "cq", "cclear", "clearq"])
    & filters.group
    & admin_filter
    & ~filters.user(list(BANNED_USERS))
)
@language
async def clear_queue_cmd(client, message: Message, _):
    chat_id = await _resolve_chat(message)
    if chat_id is None:
        return await message.reply_text(god_text("Channel play mode is not set."))
    if not await is_active_chat(chat_id):
        return await message.reply_text(god_text("Nothing is playing right now."))
    got = db.get(chat_id)
    if not got or len(got) <= 1:
        return await message.reply_text(
            god_text("Queue is empty (only current track or nothing).")
        )
    current = got[0]
    db[chat_id] = [current]
    return await message.reply_text(
        god_text("Queue cleared.")
        + "\n"
        + god_text("Kept currently playing")
        + f": {current.get('title', 'Unknown')}"
    )


@app.on_message(
    filters.command(["remove", "rm", "cremove"])
    & filters.group
    & admin_filter
    & ~filters.user(list(BANNED_USERS))
)
@language
async def remove_queue_cmd(client, message: Message, _):
    chat_id = await _resolve_chat(message)
    if chat_id is None:
        return await message.reply_text(god_text("Channel play mode is not set."))
    got = db.get(chat_id)
    if not got or len(got) <= 1:
        return await message.reply_text(god_text("No queued tracks to remove."))

    if len(message.command) < 2:
        return await message.reply_text(
            god_text("Usage")
            + ": /remove <position>\n"
            + god_text("Example")
            + ": /remove 2  ("
            + god_text("removes 2nd item in queue, not current")
            + ")"
        )
    try:
        pos = int(message.command[1])
    except ValueError:
        return await message.reply_text(
            god_text("Position must be a number (starting from 1 for next track).")
        )


    if pos < 1 or pos >= len(got):
        n = max(0, len(got) - 1)
        return await message.reply_text(
            god_text("Invalid position.")
            + " "
            + god_text("Queue has")
            + f" {n} "
            + god_text("upcoming track(s).")
        )
    removed = got.pop(pos)
    title = removed.get("title", "Unknown")
    return await message.reply_text(
        god_text("Removed from queue") + f" #{pos}: {title}"
    )


@app.on_message(
    filters.command(["playnext", "pn", "cplaynext"])
    & filters.group
    & admin_filter
    & ~filters.user(list(BANNED_USERS))
)
@language
async def playnext_cmd(client, message: Message, _):
    """Move a queued track to play next (position 1)."""
    chat_id = await _resolve_chat(message)
    if chat_id is None:
        return await message.reply_text(god_text("Channel play mode is not set."))
    got = db.get(chat_id)
    if not got or len(got) <= 2:
        return await message.reply_text(
            god_text("Need at least 2 upcoming tracks, or use")
            + " /remove "
            + god_text("and re-queue.")
        )
    if len(message.command) < 2:
        return await message.reply_text(
            god_text("Usage")
            + ": /playnext <position>\n"
            + god_text("Example")
            + ": /playnext 3  ("
            + god_text("move 3rd upcoming track to play next")
            + ")"
        )
    try:
        pos = int(message.command[1])
    except ValueError:
        return await message.reply_text(god_text("Position must be a number."))
    if pos < 1 or pos >= len(got):
        n = max(0, len(got) - 1)
        return await message.reply_text(
            god_text("Invalid position.")
            + " "
            + god_text("Queue has")
            + f" {n} "
            + god_text("upcoming track(s).")
        )
    item = got.pop(pos)
    got.insert(1, item)
    return await message.reply_text(
        god_text("Will play next") + f": {item.get('title', 'Unknown')}"
    )


@app.on_message(
    filters.command(["replay", "creplay"])
    & filters.group
    & admin_filter
    & ~filters.user(list(BANNED_USERS))
)
@language
async def replay_cmd(client, message: Message, _):
    chat_id = await _resolve_chat(message)
    if chat_id is None:
        return await message.reply_text(god_text("Channel play mode is not set."))
    if not await is_active_chat(chat_id):
        return await message.reply_text(god_text("Nothing is playing right now."))
    got = db.get(chat_id)
    if not got:
        return await message.reply_text(god_text("Queue is empty."))


    current = dict(got[0])
    current["played"] = 0

    file_path = current.get("file")
    video = str(current.get("streamtype", "")).lower() == "video"
    if not file_path:
        return await message.reply_text(god_text("Cannot replay this stream type."))
    try:
        await StreamController.skip_stream(chat_id, file_path, video=video)
        return await message.reply_text(
            god_text("Replaying") + f": {current.get('title', 'Unknown')}"
        )
    except Exception as e:
        return await message.reply_text(god_text("Replay failed") + f": {e}")


@app.on_message(
    filters.command(["np", "nowplaying", "now", "cnp"])
    & filters.group
    & ~filters.user(list(BANNED_USERS))
)
@language
async def now_playing_cmd(client, message: Message, _):
    chat_id = await _resolve_chat(message)
    if chat_id is None:
        return await message.reply_text(god_text("Channel play mode is not set."))
    if not await is_active_chat(chat_id):
        return await message.reply_text(god_text("Nothing is playing right now."))
    got = db.get(chat_id)
    if not got:
        return await message.reply_text(god_text("Nothing is playing right now."))
    cur = got[0]
    title = cur.get("title", "Unknown")
    dur = normalize_duration(cur.get("dur"))
    by = await mask_by(cur.get("by", "Unknown"), cur.get("user_id"))
    stype = stream_type_label(cur.get("streamtype", "audio"))
    vidid = cur.get("vidid", "")
    remaining = sum(1 for t in got[1:] if not t.get("autoplay"))
    status = "Playing" if await is_music_playing(chat_id) else "Paused"
    link = ""
    if vidid and len(str(vidid)) == 11:
        link = f"\n{god_text('YouTube')}: https://www.youtube.com/watch?v={vidid}"
    text = stream_card(title, dur, by, stream_type=stype)
    text += (
        f"\n{SYM['tri']} {god_text('status')}: {god_text(status)}"
        f"\n{SYM['seal']} {god_text('in queue')}: {remaining} {god_text('more')}"
        f"{link}"
    )
    return await message.reply_text(text, disable_web_page_preview=True)
