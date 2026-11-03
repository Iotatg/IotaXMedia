# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Assistant userbot chatbot (Sep 2026).

Runs a second Iota persona on the assistant userbot account (STRING1 /
self.one) so replies can come from the assistant's real-user-account
username in addition to the main bot. Same persona prompt, same AI
provider, same conversation history — the assistant is just a second
"front" for the same girl.

Anti-loop filters:
- skip messages from any bot (assistant itself, main bot, other bots)
- skip slash commands (commands belong to the main bot)
- per-user 2-second cooldown
- DM and group @mention / reply-to-assistant / "iota" word triggers (not "aisha")
"""
import logging
import re
import time

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from IotaXMedia import userbot

logger = logging.getLogger(__name__)


_cooldowns: dict[int, float] = {}
COOLDOWN_SECS = 2.0


_DIRECT_RE = re.compile(r"\biota\b", re.IGNORECASE)


_registered = False


def _strip_mention(text: str, my_username: str) -> str:
    """Strip @assistant_username only. Keep iota words so a
    bare 'iota' still has text for the AI."""
    if my_username:
        text = re.sub(re.escape(f"@{my_username}"), "", text, flags=re.IGNORECASE)
    return text.strip()


def _cached_me(client):
    me = getattr(client, "me", None)
    if me is None:
        return None
    uid = getattr(me, "id", None)
    if not isinstance(uid, int) or uid == 0:
        return None
    return me


async def _resolve_me(client):
    me = _cached_me(client)
    if me is not None:
        return me
    try:
        return await client.get_me()
    except Exception as e:
        logger.debug(f"assistant_chat get_me failed: {e}")
        return None


def _has_media(message: Message) -> bool:
    return bool(
        getattr(message, "photo", None)
        or getattr(message, "video", None)
        or getattr(message, "video_note", None)
        or getattr(message, "voice", None)
        or getattr(message, "audio", None)
        or getattr(message, "document", None)
    )


def _gate_text(message: Message) -> str:
    return ((message.text or "") + " " + (message.caption or "")).strip()


async def _should_handle(client, message: Message) -> bool:
    """Return True if the assistant userbot should respond to this message."""
    if not message.from_user:
        return False
    if message.from_user.is_self:
        return False
    if message.from_user.is_bot:
        return False
    if message.service:
        return False
    gate = _gate_text(message)
    has_media = _has_media(message)
    if not gate and not has_media:
        return False
    if gate.lstrip().startswith(("/", ".")):
        return False

    uid = message.from_user.id
    now = time.time()
    last = _cooldowns.get(uid, 0)
    if now - last < COOLDOWN_SECS:
        return False
    _cooldowns[uid] = now

    ctype = message.chat.type
    if ctype == ChatType.PRIVATE:
        return True

    me = await _resolve_me(client)
    my_username = ((me.username or "") if me else "").lower()
    my_id = me.id if me else 0
    if message.reply_to_message and message.reply_to_message.from_user:
        if my_id and message.reply_to_message.from_user.id == my_id:
            return True
    text_lower = gate.lower()
    if my_username and f"@{my_username}" in text_lower:
        return True
    entities = list(getattr(message, "entities", None) or [])
    entities += list(getattr(message, "caption_entities", None) or [])
    for ent in entities:
        user = getattr(ent, "user", None)
        if my_id and user is not None and getattr(user, "id", None) == my_id:
            return True
    if _DIRECT_RE.search(gate):
        return True
    return False


async def _run_chatbot(client, message: Message):
    from IotaXMedia.plugins.tools.chatbot import _do_reply, handle_incoming_media, _try_reply_to_media, _md_to_html, _split_text, _safe_send

    if _has_media(message):
        await handle_incoming_media(message)
        return

    is_group = message.chat.type != ChatType.PRIVATE
    original = (message.text or "").strip()
    if is_group:
        me = await _resolve_me(client)
        uname = (me.username or "") if me else ""
        clean = _strip_mention(original, uname)
        user_text = clean or original
        if not user_text:
            return
    else:
        user_text = original

    answer = await _try_reply_to_media(message, user_text)
    if answer:
        answer = _md_to_html(answer)
        for chunk in _split_text(answer):
            await _safe_send(message, chunk)
        return

    await _do_reply(message, user_text, is_group=is_group)


async def _handle(client, message: Message):
    try:
        from IotaXMedia.plugins.tools.chatbot import _ai_ready

        if not _ai_ready():
            return
        if not await _should_handle(client, message):
            return
        await _run_chatbot(client, message)
    except Exception as e:
        logger.warning(f"assistant_chat handler error: {e}")


def register():
    """Register the message handler on userbot.one. Called from __main__."""
    global _registered
    if _registered:
        return
    _registered = True

    if userbot.one is None:
        logger.info("assistant_chat: no userbot.one, skipping")
        return

    userbot.one.on_message(
        filters.text
        & ~filters.regex(r"^[/.]")
        & ~filters.bot
        & ~filters.service,
    )(_handle)
    _media = (
        filters.photo
        | filters.video
        | filters.video_note
        | filters.audio
        | filters.voice
        | filters.document
    )
    userbot.one.on_message(
        _media
        & ~filters.bot
        & ~filters.service
        & ~filters.sticker
        & ~filters.animation,
    )(_handle)
    logger.info("assistant_chat: registered on userbot.one (STRING1)")
