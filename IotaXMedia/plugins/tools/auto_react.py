# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""IotaXMedia — auto-reaction handler.

Wires `IotaXMedia.utils.auto_react.maybe_react` into the message pipeline
so the music bot reacts to users' messages with emoji reactions when the
content clearly calls for it. Personality: music/hype/party heavy.

Two handlers, at different groups so they don't block existing
chatbot (group 1) or sticker-reply (group 2 sticker) handlers:
- Text (group 2): after chatbot, independent.
- Stickers (group 3): after sticker_reply, so users get both the
  sticker-to-sticker reply AND a quick reaction.
"""
from pyrogram import filters
from pyrogram.types import Message

from config import BANNED_USERS

from IotaXMedia import app
from IotaXMedia.utils.auto_react import maybe_react


async def _on_react_text(client, message: Message):
    await maybe_react(client, message)


async def _on_react_sticker(client, message: Message):
    await maybe_react(client, message)


@app.on_message(
    filters.text
    & ~filters.bot
    & ~filters.service
    & ~filters.regex(r"^[/.]")
    & ~filters.user(list(BANNED_USERS)),
    group=2,
)
async def auto_react_text(client, message: Message):
    await _on_react_text(client, message)


@app.on_message(
    filters.sticker
    & ~filters.bot
    & ~filters.service
    & ~filters.user(list(BANNED_USERS)),
    group=3,
)
async def auto_react_sticker(client, message: Message):
    await _on_react_sticker(client, message)
