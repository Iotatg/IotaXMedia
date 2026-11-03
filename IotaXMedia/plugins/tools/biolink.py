# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Bio-link filter: auto-restrict members whose bio contains links.

Owner/sudo toggles the filter (biolink), authorizes users (bauth),
lists them (bauthlist). Authorized users are ignored by the filter.
"""
import re
import time

from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, ChatPermissions, Message

from IotaXMedia import app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia.utils.decorator import _is_sudo, admin_required
from IotaXMedia.utils.permissions import extract_user_and_reason, mention

_bio_db = mongodb["biolink"]
_auth_db = mongodb["bio_auth"]

_URL_RE = re.compile(r"(https?://|www\.|t\.me/|\.com|\.net|\.org|\.io)\S*", re.I)


async def _is_enabled(chat_id: int) -> bool:
    doc = await _bio_db.find_one({"_id": chat_id})
    return bool(doc and doc.get("enabled"))


async def _set_enabled(chat_id: int, enabled: bool) -> None:
    await _bio_db.update_one(
        {"_id": chat_id}, {"$set": {"enabled": enabled}}, upsert=True
    )


async def _is_authorized(user_id: int) -> bool:
    return bool(await _auth_db.find_one({"_id": user_id}))


async def _authorize(user_id: int, name: str = "") -> None:
    await _auth_db.update_one(
        {"_id": user_id},
        {"$set": {"_id": user_id, "name": name, "at": time.time()}},
        upsert=True,
    )


async def _unauthorize(user_id: int) -> None:
    await _auth_db.delete_one({"_id": user_id})



@app.on_message(filters.command("biolink"))
@admin_required("can_restrict_members")
async def biolink_toggle(client, message: Message):
    args = message.command[1:] if len(message.command) > 1 else []
    arg = (args[0] if args else "").lower()

    if not arg:
        cur = "Enabled" if await _is_enabled(message.chat.id) else "Disabled"
        return await message.reply_text(
            f"🔗 **Bio Link Filter Status: {cur}**\n\n"
            "Usage: `/biolink on|off`",
            parse_mode="markdown",
        )

    if arg in {"on", "enable", "yes"}:
        await _set_enabled(message.chat.id, True)
        return await message.reply_text("✅ Bio link filter **enabled** in this chat.", parse_mode="markdown")
    if arg in {"off", "disable", "no"}:
        await _set_enabled(message.chat.id, False)
        return await message.reply_text("❌ Bio link filter **disabled** in this chat.", parse_mode="markdown")

    return await message.reply_text("Usage: `/biolink on|off`", parse_mode="markdown")



@app.on_message(filters.command("bauth"))
@admin_required("can_restrict_members")
async def bauth_cmd(client, message: Message):
    user_id, name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return

    await _authorize(user_id, name or str(user_id))
    await message.reply_text(
        f"✅ **Authorized:** {mention(user_id, name or 'user')}\n"
        "This user is now ignored by the bio link filter.",
        parse_mode="markdown",
    )



@app.on_message(filters.command(["bauthlist", "bauths"]))
@admin_required("can_restrict_members")
async def bauthlist_cmd(client, message: Message):
    docs = [d async for d in _auth_db.find()]
    if not docs:
        return await message.reply_text("No authorized users yet.")

    lines = ["🔐 **Authorized users:**", ""]
    for d in docs:
        uid = d["_id"]
        nm = d.get("name") or uid
        lines.append(f"• `{uid}` — {nm}")
    await message.reply_text("\n".join(lines), parse_mode="markdown")



@app.on_message(filters.command("unbauth"))
@admin_required("can_restrict_members")
async def unbauth_cmd(client, message: Message):
    user_id, name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return

    await _unauthorize(user_id)
    await message.reply_text(
        f"🗑 Removed authorization for {mention(user_id, name or 'user')}.",
        parse_mode="markdown",
    )



@app.on_chat_member_updated(filters.group & ~filters.bot)
async def bio_filter_member(client: Client, update: ChatMemberUpdated):
    if update.new_chat_member is None:
        return

    user = update.new_chat_member.user
    if user is None:
        return
    if await _is_authorized(user.id):
        return
    if not await _is_enabled(update.chat.id):
        return

    try:
        profile = await client.get_users(user.id)
    except Exception:
        return
    if _is_sudo(profile.id):
        return

    bio = getattr(profile, "bio", "") or ""
    if not bio or not _URL_RE.search(bio):
        return

    try:
        await client.restrict_chat_member(
            update.chat.id,
            profile.id,
            ChatPermissions(can_send_messages=False),
        )
        await app.send_message(
            update.chat.id,
            f"🚫 **Bio link detected** — {mention(profile.id, profile.first_name or 'user')} "
            "has been restricted.\nTo allow them, an admin can use `/bauth`.",
            parse_mode="markdown",
        )
    except Exception:
        pass
