# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Per-user Anonymous mode.

When a user turns Anonymous ON, the bot hides their identifying details
(name / username / id / history) from other users in /id and /info
lookups, and shows a generic anonymous name as the requester of any
streaming/queue card.

Scope: global per-user toggle (the user's preference, applied in every
chat). The user themselves can still see their own details — masking
only applies when *another* user looks them up.
"""
from pyrogram import filters
from pyrogram.types import Message

from config import BANNED_USERS
from IotaXMedia import app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia.utils.god_style import god_text

anondb = mongodb.anonymous


ANON_NAME = "anonymous"
ANON_INFO = "🚫 This is a Anonymous User."




ANON_ID_PLACEHOLDER = "ʜɪᴅᴅᴇɴ"

ON = "on"
OFF = "off"


async def set_anonymous(user_id: int, on: bool) -> None:
    """Persist the anonymous preference for a user."""
    if on:
        await anondb.update_one(
            {"_id": user_id},
            {"$set": {"_id": user_id, "on": True}},
            upsert=True,
        )
    else:
        await anondb.update_one(
            {"_id": user_id},
            {"$set": {"on": False}},
            upsert=True,
        )


async def is_anonymous(user_id: int) -> bool:
    """Return True if the given user has Anonymous mode enabled."""
    if not user_id:
        return False
    doc = await anondb.find_one({"_id": user_id})
    return bool(doc and doc.get("on"))


async def mask_by(by: str, user_id: int) -> str:
    """Return ANON_NAME if the requester is anonymous, else the original.

    Use this when rendering a stored "by" / requester display string and
    the original user_id is known (e.g. from the queue entry).
    """
    if user_id and await is_anonymous(user_id):
        return god_text(ANON_NAME)
    return by


@app.on_message(
    filters.command(["anonymous", "anon"])
    & ~filters.user(list(BANNED_USERS))
)
async def anonymous_toggle(client, message: Message):
    if not message.from_user:
        return

    if len(message.command) < 2:

        on = await is_anonymous(message.from_user.id)
        state = "ON ✅" if on else "OFF ❌"
        return await message.reply_text(
            "🕶️ **Anonymous Mode**\n"
            f"➤ Status: {state}\n\n"
            "Usage:\n"
            "• `/anonymous on` — hide your details from /id, /info and the streaming card\n"
            "• `/anonymous off` — show your details normally"
        )

    arg = message.command[1].lower()
    if arg not in (ON, OFF):
        return await message.reply_text(
            "❌ Invalid argument. Use `/anonymous on` or `/anonymous off`."
        )

    turn_on = arg == ON
    await set_anonymous(message.from_user.id, turn_on)
    if turn_on:
        await message.reply_text(
            "🕶️ **Anonymous Mode ENABLED**\n"
            "➤ Your details will be hidden from other users in /id, /info "
            "and the streaming requester field."
        )
    else:
        await message.reply_text(
            "✅ **Anonymous Mode DISABLED**\n"
            "➤ Your details are visible again."
        )
