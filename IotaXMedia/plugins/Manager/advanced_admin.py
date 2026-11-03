# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
------------------------------------------------------------------------------------------------
IotaXMedia ⚡ Advanced Admin Arsenal — 20+ powerful owner & admin systems.

OWNER / SUDO  (every one asks for Yes/No inline confirmation):
  • /kickadmins  – kick EVERY admin (except owner, runner & the bot) — even admins the owner made.
  • /demoteall   – demote every admin back to member (except owner & the bot).
  • /kickbots    – kick every bot in the group (except this bot).
  • /banbots     – ban every bot in the group (except this bot).
  • /nuke        – ban all members AND wipe the whole chat history.
  • /resetgroup  – demote all admins + unpin all + restore default member permissions.
  • /warnall     – warn every member at once.
  • /unwarnall   – clear every warn in the group.
  • /revokelinks – revoke all active invite links.

ADMIN  (standard privilege checks):
  • /lockall     – silence the chat (members cannot send anything).
  • /unlockall   – restore full member permissions.
  • /slowmode <s>– set the slow-mode timer (0 turns it off).
  • /setusername @name – set/remove the group public username.
  • /cleanup [n] – delete the bot's own recent messages (default 10).
  • /protect     – enable "protect content" (no forwarding/screenshots).
  • /unprotect   – disable "protect content".
  • /checkadmin  – inspect a member's admin rights.
  • /listbots    – list every bot in the group.
  • /channels    – list anonymous admins / sender channels.
  • /banlist     – list all banned users.
  • /blockchannel @ch – block a channel from posting in the group.
  • /unblockchannel @ch – allow a blocked channel again.
------------------------------------------------------------------------------------------------
"""

import asyncio
import html

from pyrogram import filters, Client
from pyrogram import enums
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import (
    ChatAdminRequired, UserAdminInvalid, RPCError, FloodWait, UserNotParticipant,
)
from pyrogram.types import (
    Message, ChatPermissions, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup, ChatPrivileges,
)

_DEMOTE_PRIVS = ChatPrivileges(can_manage_chat=False)

from IotaXMedia import app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia.logging import LOGGER
from IotaXMedia.utils.decorator import admin_required
from IotaXMedia.utils.permissions import is_owner_or_sudoer, mention
from IotaXMedia.utils.colored_buttons import styled_button, send_message_colored
from IotaXMedia.utils.god_style import god_text

log = LOGGER(__name__)

_warn = mongodb["warns"]

_ADMIN_STATUS = (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

_FULL_MEMBER_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
    can_change_info=True,
    can_pin_messages=True,
)





async def _me_id(client) -> int:
    return (await client.get_me()).id


async def _check_bot_priv(client, chat_id, *flags) -> bool:
    me = await client.get_chat_member(chat_id, (await client.get_me()).id)
    priv = getattr(me, "privileges", None) or getattr(me, "permissions", None)
    return all(bool(getattr(priv, f, False)) for f in flags)


def _confirm_col(cmd):
    return [
        [styled_button("✔ ʏᴇs", callback_data=f"{cmd}_yes", style="success"),
         styled_button("✖ ɴᴏ", callback_data=f"{cmd}_no", style="danger")]
    ]


def _confirm_kb(cmd):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("✔ ʏᴇs", callback_data=f"{cmd}_yes", style=enums.ButtonStyle.SUCCESS),
          InlineKeyboardButton("✖ ɴᴏ", callback_data=f"{cmd}_no", style=enums.ButtonStyle.DANGER)]]
    )


async def _safe_edit(cb: CallbackQuery, text: str):
    try:
        await cb.message.edit(text, parse_mode="markdown")
        return True
    except Exception:
        try:
            await cb.answer(text[:200], show_alert=False)
        except Exception:
            pass
        return False



_REASON_LABELS = {
    "rank": "🔒 outranks me — Telegram only lets a bot manage admins promoted AFTER it. Ask the owner to demote & re-promote me so I become top admin.",
    "rights": "❌ I am not admin / lack the needed rights in this chat",
    "flood": "⏳ Telegram rate-limit (flood wait)",
    "bot": "🤖 cannot act on that bot",
    "other": "⚠️ other error",
}


def _reason_key(e: Exception) -> str:
    if isinstance(e, UserAdminInvalid):
        return "rank"
    if isinstance(e, ChatAdminRequired):
        return "rights"
    if isinstance(e, FloodWait):
        return "flood"
    if isinstance(e, (UserNotParticipant,)):
        return "rights"
    return "other"


def _note(reasons: dict, e: Exception):
    key = _reason_key(e)
    reasons[key] = reasons.get(key, 0) + 1


def _format_reasons(reasons: dict) -> str:
    if not reasons:
        return ""
    lines = "\n".join(f"{_REASON_LABELS[k]} × {v}" for k, v in sorted(reasons.items(), key=lambda i: -i[1]))
    return "\n\n📋 **Failures:**\n" + lines



async def _wipe_history(client, chat_id: int, concurrency=3, batch_size=100):
    """Delete every message in the chat using the bot itself.

    Returns:
      -1 → full history cleared instantly (raw DeleteHistory)
       n → number of messages batch-deleted
      -2 → could not delete (no admin delete rights)
    """

    try:
        from pyrogram.raw import functions

        await client.invoke(
            functions.messages.DeleteHistory(
                peer=await client.resolve_peer(chat_id),
                max_id=0,
                just_clear=False,
                revoke=True,
            )
        )
        return -1
    except ChatAdminRequired:
        return -2
    except Exception:
        pass


    sem = asyncio.Semaphore(concurrency)
    tasks, count = [], 0

    async def _deleter(ids):
        nonlocal count
        async with sem:
            while True:
                try:
                    await client.delete_messages(chat_id, ids)
                    count += len(ids)
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    break

    try:
        batch = []
        async for msg in client.get_chat_history(chat_id):
            batch.append(msg.id)
            if len(batch) >= batch_size:
                tasks.append(asyncio.create_task(_deleter(batch)))
                batch = []
                if len(tasks) >= 10:
                    await asyncio.gather(*tasks)
                    tasks.clear()
        if batch:
            tasks.append(asyncio.create_task(_deleter(batch)))
        if tasks:
            await asyncio.gather(*tasks)
    except ChatAdminRequired:
        return count if count else -2
    except Exception:
        pass
    return count



async def _ask_owner_confirm(client, message: Message, cmd: str):
    ok, owner = await is_owner_or_sudoer(client, message.chat.id, message.from_user.id)
    if not ok:
        owner_m = mention(owner.id, owner.first_name) if owner else "the owner"
        return await message.reply_text(
            f"❌ {god_text('ᴏɴʟʏ')} {owner_m} {god_text('ᴍᴀʏ ʀᴜɴ')} /{cmd}.",
            parse_mode="markdown",
        )

    text = (
        f"{mention(message.from_user.id, message.from_user.first_name)}, "
        f"{god_text('ᴘʟᴇᴀsᴇ ᴄᴏɴғɪʀᴍ')} **/{cmd}** {god_text('ғᴏʀ')} **{message.chat.title}**?\n\n"
        f"_{god_text('ᴛʜɪs ɪs ᴀ ᴅᴇsᴛʀᴜᴄᴛɪᴠᴇ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅ.')}_"
    )
    try:
        r = await send_message_colored(message.chat.id, text, _confirm_col(cmd), parse_mode="markdown")
        if r:
            return
    except Exception:
        pass
    await message.reply_text(text, reply_markup=_confirm_kb(cmd), parse_mode="markdown")






OVERRIDE_CMDS = [
    "kickadmins", "demoteall", "kickbots", "banbots",
    "nuke", "resetgroup", "warnall", "unwarnall", "revokelinks",
]


@app.on_message(filters.command(OVERRIDE_CMDS) & filters.group)
async def ask_override_confirm(client: Client, message: Message):
    await _ask_owner_confirm(client, message, message.command[0])


@app.on_callback_query(filters.regex(rf"^({'|'.join(OVERRIDE_CMDS)})_(yes|no)$"))
async def override_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    cmd, ans = data.rsplit("_", 1)
    chat_id = callback.message.chat.id
    uid = callback.from_user.id

    ok, _owner = await is_owner_or_sudoer(client, chat_id, uid)
    if not ok:
        return await callback.answer(f"{god_text('ᴏɴʟʏ ᴛʜᴇ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴄᴏɴғɪʀᴍ.')}", show_alert=True)

    if ans == "no":
        return await _safe_edit(callback, f"❌ /{cmd} {god_text('ᴄᴀɴᴄᴇʟᴇᴅ.')}")

    priv_map = {
        "kickadmins": ("can_restrict_members", "can_promote_members"),
        "demoteall": ("can_promote_members",),
        "kickbots": ("can_restrict_members",),
        "banbots": ("can_restrict_members",),
        "nuke": ("can_restrict_members", "can_delete_messages"),
        "resetgroup": ("can_promote_members", "can_pin_messages"),
        "warnall": (),
        "unwarnall": (),
        "revokelinks": ("can_invite_users",),
    }
    if priv_map[cmd] and not await _check_bot_priv(client, chat_id, *priv_map[cmd]):
        return await _safe_edit(callback, f"❌ {god_text('I ʟᴀᴄᴋ ᴛʜᴇ ᴘʀɪᴠɪʟᴇɢᴇs ɴᴇᴇᴅᴇᴅ ғᴏʀ')} /{cmd}.")

    await _safe_edit(callback, f"⏳ /{cmd} {god_text('ɪɴ ᴘʀᴏɢʀᴇss…')}")
    try:
        if cmd == "kickadmins":
            done, reasons = await _do_kickadmins(client, chat_id, uid)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴋɪᴄᴋᴇᴅ')} **{done}** {god_text('ᴀᴅᴍɪɴ(s)')}." + _format_reasons(reasons))
        elif cmd == "demoteall":
            done, reasons = await _do_demoteall(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴅᴇᴍᴏᴛᴇᴅ')} **{done}** {god_text('ᴀᴅᴍɪɴ(s)')}." + _format_reasons(reasons))
        elif cmd == "kickbots":
            done, reasons = await _do_kickbots(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴋɪᴄᴋᴇᴅ')} **{done}** {god_text('ʙᴏᴛ(s)')}." + _format_reasons(reasons))
        elif cmd == "banbots":
            done, reasons = await _do_banbots(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ʙᴀɴɴᴇᴅ')} **{done}** {god_text('ʙᴏᴛ(s)')}." + _format_reasons(reasons))
        elif cmd == "nuke":
            banned, demoted, cleared, reasons = await _do_nuke(client, chat_id)
            if cleared == -1:
                wiped = f"🧹 {god_text('ʜɪsᴛᴏʀʏ ᴡɪᴘᴇᴅ — ᴀʟʟ ᴍᴇssᴀɢᴇs ᴅᴇʟᴇᴛᴇᴅ')}"
            elif cleared >= 0:
                wiped = f"🧹 {god_text('ʜɪsᴛᴏʀʏ ᴡɪᴘᴇᴅ — ᴅᴇʟᴇᴛᴇᴅ')} ~**{cleared}** {god_text('ᴍᴇssᴀɢᴇs')}"
            else:
                wiped = f"🧹 {god_text('ʜɪsᴛᴏʀʏ ɴᴏᴛ ᴡɪᴘᴇᴅ — I ɴᴇᴇᴅ ᴅᴇʟᴇᴛᴇ-ᴍᴇssᴀɢᴇs ᴀᴅᴍɪɴ ʀɪɢʜᴛ')}"
            text = (f"✅ /{cmd} → {god_text('ʙᴀɴɴᴇᴅ')} **{banned}** {god_text('ᴜsᴇʀ(s)')}, {god_text('ᴅᴇᴍᴏᴛᴇᴅ')} **{demoted}** {god_text('ᴀᴅᴍɪɴ(s)')}.\n"
                    f"{wiped}." + _format_reasons(reasons))
            try:
                await client.send_message(chat_id, text)
            except Exception:
                await _safe_edit(callback, text)
        elif cmd == "resetgroup":
            demoted, reasons = await _do_resetgroup(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴅᴇᴍᴏᴛᴇᴅ')} **{demoted}** {god_text('ᴀᴅᴍɪɴ(s), ᴜɴᴘɪɴɴᴇᴅ ᴀʟʟ, ʀᴇsᴛᴏʀᴇᴅ ᴘᴇʀᴍɪssɪᴏɴs.')}" + _format_reasons(reasons))
        elif cmd == "warnall":
            warned, reasons = await _do_warnall(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴡᴀʀɴᴇᴅ')} **{warned}** {god_text('ᴍᴇᴍʙᴇʀ(s)')}." + _format_reasons(reasons))
        elif cmd == "unwarnall":
            cleared = await _do_unwarnall(chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ᴄʟᴇᴀʀᴇᴅ')} **{cleared}** {god_text('ᴡᴀʀɴ ʀᴇᴄᴏʀᴅ(s)')}.")
        elif cmd == "revokelinks":
            revoked, reasons = await _do_revokelinks(client, chat_id)
            await _safe_edit(callback, f"✅ /{cmd} → {god_text('ʀᴇᴠᴏᴋᴇᴅ')} **{revoked}** {god_text('ʟɪɴᴋ(s)')}." + _format_reasons(reasons))
    except Exception as e:
        log.error("override %s failed: %s", cmd, e)
        await _safe_edit(callback, f"❌ /{cmd} {god_text('ᴇʀʀᴏʀ')}:\n{e}")




async def _do_kickadmins(client, chat_id: int, actor_id: int):
    me_id = await _me_id(client)
    done, reasons = 0, {}
    async for m in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if m.status == ChatMemberStatus.OWNER:
            continue
        if m.user and m.user.id in (actor_id, me_id):
            continue
        uid = m.user.id
        try:
            try:
                await client.promote_chat_member(chat_id, uid, privileges=_DEMOTE_PRIVS)
            except Exception:
                pass
            await client.ban_chat_member(chat_id, uid)
            await asyncio.sleep(0.2)
            await client.unban_chat_member(chat_id, uid)
            done += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)
    return done, reasons


async def _do_demoteall(client, chat_id: int):
    me_id = await _me_id(client)
    done, reasons = 0, {}
    async for m in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if m.status == ChatMemberStatus.OWNER or (m.user and m.user.id == me_id):
            continue
        try:
            await client.promote_chat_member(chat_id, m.user.id, privileges=_DEMOTE_PRIVS)
            done += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)
    return done, reasons


async def _do_kickbots(client, chat_id: int):
    me_id = await _me_id(client)
    done, reasons = 0, {}
    async for b in client.get_chat_members(chat_id, filter=ChatMembersFilter.BOTS):
        if b.user.id == me_id:
            continue
        try:
            await client.ban_chat_member(chat_id, b.user.id)
            await asyncio.sleep(0.2)
            await client.unban_chat_member(chat_id, b.user.id)
            done += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)
    return done, reasons


async def _do_banbots(client, chat_id: int):
    me_id = await _me_id(client)
    done, reasons = 0, {}
    async for b in client.get_chat_members(chat_id, filter=ChatMembersFilter.BOTS):
        if b.user.id == me_id:
            continue
        try:
            await client.ban_chat_member(chat_id, b.user.id)
            done += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)
    return done, reasons


async def _do_nuke(client, chat_id: int):
    """Systematic total-wipe: demote admins → ban everyone → delete all messages."""
    me_id = await _me_id(client)
    demoted, reasons = 0, {}


    async for m in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if m.status == ChatMemberStatus.OWNER or (m.user and m.user.id == me_id):
            continue
        try:
            await client.promote_chat_member(chat_id, m.user.id, privileges=_DEMOTE_PRIVS)
            demoted += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)


    banned = 0
    async for m in client.get_chat_members(chat_id):
        if not m.user:
            continue
        if m.user.id == me_id or m.status == ChatMemberStatus.OWNER:
            continue
        try:
            await client.ban_chat_member(chat_id, m.user.id)
            banned += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.05)


    cleared = await _wipe_history(client, chat_id)

    return banned, demoted, cleared, reasons


async def _do_resetgroup(client, chat_id: int):
    demoted, reasons = 0, {}
    me_id = await _me_id(client)
    async for m in client.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
        if m.status == ChatMemberStatus.OWNER or (m.user and m.user.id == me_id):
            continue
        try:
            await client.promote_chat_member(chat_id, m.user.id, privileges=_DEMOTE_PRIVS)
            demoted += 1
        except Exception as e:
            _note(reasons, e)
            if isinstance(e, FloodWait):
                await asyncio.sleep(e.value)
        await asyncio.sleep(0.1)
    try:
        await client.unpin_all_chat_messages(chat_id)
    except Exception:
        pass
    try:
        await client.set_chat_permissions(chat_id, _FULL_MEMBER_PERMS)
    except Exception:
        pass
    return demoted, reasons


async def _do_warnall(client, chat_id: int):
    warned, reasons = 0, {}
    async for m in client.get_chat_members(chat_id):
        if m.user and (m.user.is_bot or m.status in _ADMIN_STATUS):
            continue
        try:
            await _warn.update_one(
                {"_id": f"{chat_id}_{m.user.id}"},
                {"$inc": {"warns": 1}},
                upsert=True,
            )
            warned += 1
        except Exception as e:
            _note(reasons, e)
        await asyncio.sleep(0.05)
    return warned, reasons


async def _do_unwarnall(chat_id: int) -> int:
    res = await _warn.delete_many({"_id": {"$regex": f"^{chat_id}_"}})
    return res.deleted_count


async def _do_revokelinks(client, chat_id: int):
    revoked, reasons = 0, {}
    try:
        async for admin in client.get_chat_admins_with_invite_links(chat_id):
            async for link in client.get_chat_admin_invite_links(chat_id, admin.admin_id):
                try:
                    await client.revoke_chat_invite_link(chat_id, link.invite_link)
                    revoked += 1
                except Exception as e:
                    _note(reasons, e)
                await asyncio.sleep(0.05)
    except (ChatAdminRequired, RPCError) as e:
        _note(reasons, e)
        log.warning("revokelinks scan skipped: %s", e)
    return revoked, reasons






@app.on_message(filters.command("lockall") & filters.group)
@admin_required("can_restrict_members")
async def lockall_cmd(client, message: Message):
    try:
        await client.set_chat_permissions(message.chat.id, ChatPermissions())
        await message.reply_text(f"🔒 **{message.chat.title}** locked — members cannot send anything.\nUse /unlockall to restore.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")


@app.on_message(filters.command("unlockall") & filters.group)
@admin_required("can_restrict_members")
async def unlockall_cmd(client, message: Message):
    try:
        await client.set_chat_permissions(message.chat.id, _FULL_MEMBER_PERMS)
        await message.reply_text(f"🔓 **{message.chat.title}** unlocked — full member permissions restored.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")


@app.on_message(filters.command("slowmode") & filters.group)
@admin_required("can_restrict_members")
async def slowmode_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /slowmode [seconds]  (0 turns it off)")
    try:
        sec = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid seconds.")
    if sec < 0 or sec > 300:
        return await message.reply_text("0–300 seconds only.")
    try:
        await client.set_slow_mode(message.chat.id, sec)
        await message.reply_text(f"🐢 Slow mode **{'off' if sec == 0 else f'{sec}s'}**.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")


@app.on_message(filters.command("setusername") & filters.group)
@admin_required("can_change_info")
async def setusername_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /setusername @username   |   /setusername -  (remove)")
    uname = message.command[1].lstrip("@")
    if uname in ("-", "del", "remove"):
        uname = None
    try:
        await client.set_chat_username(message.chat.id, uname)
        await message.reply_text(f"🔖 Username set: @{uname}" if uname else "🔖 Username removed.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")


@app.on_message(filters.command("cleanup") & filters.group)
@admin_required("can_delete_messages")
async def cleanup_cmd(client, message: Message):
    n = 10
    if len(message.command) > 1:
        try:
            n = int(message.command[1])
        except ValueError:
            pass
    n = max(1, min(n, 200))
    me_id = await _me_id(client)
    deleted, failed = 0, 0
    async for msg in client.get_chat_history(message.chat.id, limit=min(1000, max(100, n * 5))):
        if deleted >= n:
            break
        if getattr(msg, "from_user", None) and msg.from_user.id == me_id:
            try:
                await client.delete_messages(message.chat.id, msg.id)
                deleted += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.1)
    suffix = f" ({failed} failed)" if failed else ""
    await message.reply_text(f"🧹 Deleted **{deleted}** bot message(s).{suffix}")


@app.on_message(filters.command(["protect", "unprotect"]) & filters.group)
@admin_required("can_change_info")
async def protect_cmd(client, message: Message):
    enabled = message.command[0] == "protect"
    try:
        await client.set_chat_protected_content(message.chat.id, enabled)
        await message.reply_text(f"🛡️ Protected content **{'enabled' if enabled else 'disabled'}**.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")






@app.on_message(filters.command("checkadmin") & filters.group)
async def checkadmin_cmd(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        uid = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            uid = (await client.get_users(message.command[1])).id
        except RPCError:
            return await message.reply_text("User not found.")
    else:
        uid = message.from_user.id

    try:
        m = await client.get_chat_member(message.chat.id, uid)
    except RPCError:
        return await message.reply_text("Not a member.")

    name = (m.user.first_name or "User") if m.user else "Channel"
    txt = f"🔎 {mention(uid, name)} is **{m.status.value}**"
    if m.status == ChatMemberStatus.ADMINISTRATOR and m.privileges:
        priv = m.privileges
        flags = [
            f for f in (
                "is_anonymous", "can_manage_chat", "can_delete_messages",
                "can_manage_video_chats", "can_restrict_members", "can_promote_members",
                "can_change_info", "can_invite_users", "can_pin_messages",
                "can_edit_messages", "can_post_messages",
            )
            if getattr(priv, f, False)
        ]
        if flags:
            txt += "\n🛡️ **Rights:**\n" + "\n".join(f"• {f}" for f in flags)
    await message.reply_text(txt)


@app.on_message(filters.command("listbots") & filters.group)
async def listbots_cmd(client, message: Message):
    bots = []
    async for b in client.get_chat_members(message.chat.id, filter=ChatMembersFilter.BOTS):
        bots.append((b.user, b.status in _ADMIN_STATUS))
    if not bots:
        return await message.reply_text("🤖 No bots in this group.")
    lines = []
    for i, (u, is_admin) in enumerate(bots):
        handle = f"@{u.username}" if u.username else mention(u.id, u.first_name or "Bot")
        lines.append(f"{'└' if i == len(bots) - 1 else '├'} {handle}{' 🛡️' if is_admin else ''}")
    await message.reply_text(f"🤖 **Bots ({len(bots)}):**\n" + "\n".join(lines))


@app.on_message(filters.command("channels") & filters.group)
async def channels_cmd(client, message: Message):
    anon = []
    async for m in client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        priv = getattr(m, "privileges", None)
        if priv and priv.is_anonymous:
            if getattr(m, "user", None):
                anon.append(m.user)
            elif getattr(m, "chat", None):
                anon.append(m.chat)
    if not anon:
        return await message.reply_text("📡 No anonymous admins / sender channels.")
    lines = []
    for i, u in enumerate(anon):
        name = getattr(u, "title", None) or (u.first_name or "?")
        handle = f"@{u.username}" if getattr(u, "username", None) else html.escape(name)
        lines.append(f"{'└' if i == len(anon) - 1 else '├'} {handle}")
    await message.reply_text("📡 **Anonymous admins / sender channels:**\n" + "\n".join(lines))


@app.on_message(filters.command("banlist") & filters.group)
async def banlist_cmd(client, message: Message):
    banned = []
    async for m in client.get_chat_members(message.chat.id, filter=ChatMembersFilter.BANNED):
        if m.user:
            banned.append(m.user)
    if not banned:
        return await message.reply_text("🚫 No banned users.")
    lines = []
    for i, u in enumerate(banned):
        handle = f"@{u.username}" if u.username else mention(u.id, u.first_name or "User")
        lines.append(f"{'└' if i == len(banned) - 1 else '├'} {handle}")
    await message.reply_text(f"🚫 **Banned ({len(banned)}):**\n" + "\n".join(lines))






@app.on_message(filters.command(["blockchannel", "unblockchannel"]) & filters.group)
@admin_required("can_restrict_members")
async def blockchannel_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /blockchannel @channel_or_id   |   /unblockchannel @channel_or_id")
    ident = message.command[1].lstrip("@")
    blocking = message.command[0] == "blockchannel"
    try:
        if blocking:
            await client.ban_chat_member(message.chat.id, ident)
        else:
            await client.unban_chat_member(message.chat.id, ident)
        await message.reply_text(f"{'🚫 Blocked' if blocking else '✅ Unblocked'} channel **@{ident}**.")
    except RPCError as e:
        await message.reply_text(f"❌ {e}")
