# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Parent-side clone management commands (run in the MAIN bot process).

Available to all users (private chat):
    /clone  <bot_token>       — spawn a new clone (anyone)
    /myclone (or /mybot)      — list clones you own

Owner-only commands:
    /delclone (or /rmbot)     — stop + delete a clone by bot_id (owner/owner+sudo)
    /cloned                    — total # clones (owner only)
    /totalbots                 — total # clones (owner only)
    /clonedinfo                — detailed list (owner only)
    /delallclone               — factory reset (owner only)

Clones run in-process as full replicas of the main bot (see
``IotaXMedia/clone/runtime.py``); these commands only call into the
CloneManager and update the registry.
"""
from __future__ import annotations

import asyncio
import re

from pyrogram import Client, filters
from pyrogram.errors import Unauthorized
from pyrogram.types import Message

import config
from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.clone.runtime import get_clone_manager
from IotaXMedia.clone.db import (
    get_clone,
    get_all_clones,
    get_clones_by_owner,
    add_clone,
    delete_clone,
    count_clones,
    purge_clones,
    set_clone_status,
)






_CLONE_MODE = bool(getattr(config, "CLONE_MODE", False))

OWNER = filters.user([config.OWNER_ID]) if config.OWNER_ID else filters.user([])
_TOKEN_RE = re.compile(r"^\d{6,12}:[A-Za-z0-9_-]{20,}$")






def on_clone_managed(*args, **kwargs):
    """Decorator that registers the handler ONLY when NOT in clone mode."""
    if _CLONE_MODE:
        def _noop(func):
            return func
        return _noop
    return app.on_message(*args, **kwargs)



@on_clone_managed(filters.command("clone") & filters.private)
async def clone_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "๏ /clone — ˹𝐈ᴏᴛᴀ ✘ 𝙼ᴜꜱɪᴄ˼ ʙᴏᴛ ᴄʟᴏɴᴇʀ\n"
            "ᴜsᴀɢᴇ: <code>/clone <ʙᴏᴛ_ᴛᴏᴋᴇɴ></code>\n"
            "ɢᴇᴛ ᴀ ᴛᴏᴋᴇɴ ғʀᴏᴍ @BotFather."
        )
    token = message.command[1].strip()
    if not _TOKEN_RE.match(token):
        return await message.reply_text("❌ ᴛʜᴀᴛ ᴅᴏᴇsɴ'ᴛ ʟᴏᴏᴋ ʟɪᴋᴇ ᴀ ᴠᴀʟɪᴅ ʙᴏᴛ ᴛᴏᴋᴇɴ.")

    existing = await get_clone(token)
    if existing:
        return await message.reply_text(
            f"🟡 ᴛʜɪs ʙᴏᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀ ᴄʟᴏɴᴇ: @{existing.get('username') or '?'}"
        )


    try:
        probe = Client(
            name="clone_probe",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=token,
            no_updates=True,
            in_memory=True,
        )
        await probe.start()
        me = await probe.get_me()
        bot_id = me.id
        username = (me.username or "").lstrip("@")
        await probe.stop()
        del probe
    except Unauthorized:
        return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ (ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ).")
    except Exception as e:
        return await message.reply_text(f"❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴘʀᴏʙᴇ ᴛʜᴇ ᴛᴏᴋᴇɴ: <code>{e}</code>")

    await add_clone(token, bot_id, username, message.from_user.id)
    ok = await get_clone_manager().start_clone(token)
    if not ok:
        await delete_clone(token)
        return await message.reply_text("❌ ꜰᴀɪʟᴇᴅ ᴛᴏ sᴛᴀʀᴛ ᴄʟᴏɴᴇ. ᴄʜᴇᴄᴋ ʟᴏɢs.")
    await message.reply_text(
        f"🟢 ᴄʟᴏɴᴇ ᴅᴇᴘʟᴏʏᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!: @{username}\n\n"
        "ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ɢᴏ ᴛᴏ ᴄʟᴏɴᴇ ᴄᴜsᴛᴏᴍɪᴢᴇ & ᴘᴇʀsᴏɴᴀʟɪᴢᴇ ᴛʜᴇ ʙᴏᴛ.\n"
        "ʀᴜɴ /help ᴏɴ ʏᴏᴜʀ ᴄʟᴏɴᴇ ᴛᴏ sᴇᴇ ᴡʜᴀᴛ ɪᴛ ᴄᴀɴ ᴅᴏ."
    )



@on_clone_managed(filters.command(["delclone", "rmbot"]) & filters.private)
async def delclone_cmd(client: Client, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "ᴜsᴀɢᴇ: /delclone <ʙᴏᴛ_ɪᴅ>  — ʏᴏᴜʀ ᴄʟᴏɴᴇ ɪᴅs ᴄᴏᴍᴇ ғʀᴏᴍ /myclone."
        )
    arg = message.command[1].strip()
    try:
        bot_id = int(arg)
    except ValueError:
        return await message.reply_text("❌ ʙᴏᴛ_ɪᴅ ᴍᴜsᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.")

    from IotaXMedia.clone.db import get_clone_by_id
    doc = await get_clone_by_id(bot_id)
    if not doc:
        return await message.reply_text("❌ ɴᴏ ᴄʟᴏɴᴇ ᴡɪᴛʜ ᴛʜᴀᴛ ɪᴅ.")
    is_owner = message.from_user and (
        message.from_user.id == doc.get("owner_id")
        or message.from_user.id == config.OWNER_ID
    )
    if not is_owner:
        return await message.reply_text("🚫 ʏᴏᴜ ᴅᴏɴ'ᴛ ᴏᴡɴ ᴛʜɪs ᴄʟᴏɴᴇ.")

    token = doc["_id"]
    await get_clone_manager().stop_clone(token)
    await delete_clone(token)
    await message.reply_text(
        f"✅ ᴄʟᴏɴᴇ @{doc.get('username') or str(bot_id)} sᴛᴏᴘᴘᴇᴅ & ᴅᴇʟᴇᴛᴇᴅ."
    )



@on_clone_managed(filters.command(["myclone", "mybot"]) & filters.private)
async def myclone_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    clones = await get_clones_by_owner(message.from_user.id)
    if not clones:
        return await message.reply_text(
            "ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴄʟᴏɴᴇᴅ ᴀɴʏ ʙᴏᴛ ʏᴇᴛ. ᴜsᴇ /clone <ʙᴏᴛ_ᴛᴏᴋᴇɴ>."
        )
    lines = ["ʏᴏᴜʀ ᴄʟᴏɴᴇs:", ""]
    for c in clones:

        live = "🟢 ʀᴜɴɴɪɴɢ" if get_clone_manager().is_running(c["_id"]) else "🔴 sᴛᴏᴘᴘᴇᴅ"
        lines.append(f"• @{c.get('username') or '?'} ({c.get('bot_id')}) — {live}")
    await message.reply_text("\n".join(lines))



@on_clone_managed(filters.command(["cloned", "totalbots"]) & filters.private & OWNER)
async def cloned_cmd(client: Client, message: Message):
    total = await count_clones()
    running = await get_clone_manager().get_running_count()
    await message.reply_text(f"📊 ᴛᴏᴛᴀʟ ᴄʟᴏɴᴇs: {total}\n🟢 ʀᴜɴɴɪɴɢ: {running}")



@on_clone_managed(filters.command("clonedinfo") & filters.private & OWNER)
async def clonedinfo_cmd(client: Client, message: Message):
    clones = await get_all_clones()
    if not clones:
        return await message.reply_text("ɴᴏ ᴄʟᴏɴᴇs ʏᴇᴛ.")
    lines = [f"📋 ᴀʟʟ ᴄʟᴏɴᴇs ({len(clones)}):", ""]
    for c in clones:
        live = "🟢" if get_clone_manager().is_running(c["_id"]) else "🔴"
        owner = c.get("owner_id") or "?"
        lines.append(f"{live} @{c.get('username') or '?'} ({c.get('bot_id')}) — ᴏᴡɴᴇʀ {owner}")
    await message.reply_text("\n".join(lines))



@on_clone_managed(filters.command("delallclone") & filters.private & OWNER)
async def delallclone_cmd(client: Client, message: Message):
    clones = await get_all_clones()
    stopped = 0
    for c in clones:
        stopped += 1 if await get_clone_manager().stop_clone(c["_id"]) else 0
    removed = await purge_clones()
    await message.reply_text(
        f"🗑 ꜰᴀᴄᴛᴏʀʏ ʀᴇsᴇᴛ.\nsᴛᴏᴘᴘᴇᴅ {stopped}, ᴘᴜʀɢᴇᴅ {removed} ᴄʟᴏɴᴇs + sᴇᴛᴛɪɴɢs."
    )
