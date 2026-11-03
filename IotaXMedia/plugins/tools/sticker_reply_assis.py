# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Assistant userbot sticker-to-sticker reply for IotaXMedia (Sep 2026).

Runs the same sticker engine on userbot.one (STRING_SESSION_1) using
the helper functions already exported by
IotaXMedia.plugins.tools.sticker_reply. Mirrors the trigger rules
from IotaXMedia.plugins.tools.assistant_chat so behaviour stays
consistent across the main bot and the assistant.

  * DMs always
  * Groups: reply-to-assistant, @<assistant_username>, or the word
    "iota" (not "aisha")
  * Skip bot senders, slash / dot commands, service msgs
  * 2-second per-user cooldown (shared with assistant_chat)
"""
import logging
import time

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from IotaXMedia import userbot
from IotaXMedia.plugins.tools.assistant_chat import (
    COOLDOWN_SECS,
    _cooldowns,
    _DIRECT_RE,
)
from IotaXMedia.plugins.tools.sticker_reply import (
    _auto_reply_from_pack,
    _detect_mood_from_sticker,
    _reply_any_sticker,
    _reply_sticker_for_mood,
)

logger = logging.getLogger(__name__)

_registered = False


async def _should_handle_assistant(client, message: Message) -> bool:
    if not message.from_user:
        return False
    if message.from_user.is_self:
        return False
    if message.from_user.is_bot:
        return False
    if message.service:
        return False
    if not getattr(message, "sticker", None):
        return False
    text = (message.text or message.caption or "") or ""
    if text.lstrip().startswith(("/", ".")):
        return False

    uid = message.from_user.id
    now = time.time()
    last = _cooldowns.get(uid, 0)
    if now - last < COOLDOWN_SECS:
        return False
    _cooldowns[uid] = now

    if message.chat and message.chat.type == ChatType.PRIVATE:
        return True

    me = getattr(client, "me", None)
    uid = getattr(me, "id", None) if me is not None else None
    if not isinstance(uid, int) or uid == 0:
        try:
            me = await client.get_me()
        except Exception as e:
            logger.debug(f"assistant sticker: get_me failed: {e}")
            return False
        uid = getattr(me, "id", None) if me is not None else None
    my_id = uid if isinstance(uid, int) else 0
    my_username = ((me.username or "") if me else "").lower()

    if message.reply_to_message and message.reply_to_message.from_user:
        if my_id and message.reply_to_message.from_user.id == my_id:
            return True
    if my_username and f"@{my_username}" in text.lower():
        return True
    if text and _DIRECT_RE.search(text):
        return True
    return False


async def _handle_assistant_sticker(client, message: Message):
    try:
        if not await _should_handle_assistant(client, message):
            return
        mood = _detect_mood_from_sticker(message.sticker)
        if await _reply_sticker_for_mood(message, mood, client=client):
            return
        if await _auto_reply_from_pack(message, client=client):
            return
        await _reply_any_sticker(message, client=client)
    except Exception as e:
        logger.warning(f"assistant sticker handler error: {e}")


def register():
    """Attach the sticker handler to userbot.one. No-op if STRING1 unset."""
    global _registered
    if _registered:
        return
    _registered = True

    if userbot.one is None:
        logger.info("sticker_reply_assis: no userbot.one, skipping")
        return

    userbot.one.on_message(
        filters.sticker & ~filters.bot & ~filters.service,
    )(_handle_assistant_sticker)
    logger.info("sticker_reply_assis: registered on userbot.one (STRING1)")
