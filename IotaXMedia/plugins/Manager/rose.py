# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import os
import random
import re
import time
from collections import defaultdict

from pyrogram import filters, enums
from pyrogram.errors import (
    ChatAdminRequired, UserAdminInvalid, UserNotParticipant, RPCError,
)
try:
    from pyrogram.errors import TopicClosed
except ImportError:
    TopicClosed = RPCError
from pyrogram.types import Message, ChatPermissions, ChatMemberUpdated, CallbackQuery

from IotaXMedia import app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia.utils.cache import TTLCache
from IotaXMedia.utils.decorator import admin_required
from IotaXMedia.utils.replies import ADMIN_ONLY
from IotaXMedia.utils.permissions import mention, extract_user_and_reason
from IotaXMedia.utils.colored_buttons import (
    styled_button,
    buttons_to_inline_markup,
    send_message_colored,
)





_warn = mongodb["warns"]
_warnset = mongodb["warn_settings"]
_rules = mongodb["rules"]
_goodbye = mongodb["goodbye"]
_notes = mongodb["notes"]
_filters = mongodb["filters"]
_filters_state = mongodb["filter_settings"]
_blacklist = mongodb["blacklist"]
_blacklist_state = mongodb["blacklist_settings"]
_flood = mongodb["antiflood"]
_locks = mongodb["locks"]
_captcha = mongodb["captcha"]
_report = mongodb["report_settings"]
_disable = mongodb["disabled"]
_raid = mongodb["antiraid"]
_user_notes = mongodb["user_notes"]
_approved = mongodb["approved"]

_cfg_cache = TTLCache(maxsize=4096, ttl=20)


async def _cached_doc(coll, _id):
    key = f"{coll.name}:{_id}"
    doc = _cfg_cache.get(key)
    if doc is None:
        doc = await coll.find_one({"_id": _id}) or {}
        _cfg_cache.set(key, doc)
    return doc


def _invalidate(coll_name: str, _id) -> None:
    _cfg_cache.pop(f"{coll_name}:{_id}")





_DEF_MUTE = ChatPermissions()
_MUTE_PERMS = ChatPermissions(
    can_send_messages=True, can_send_media_messages=True, can_send_polls=True,
    can_send_other_messages=True, can_add_web_page_previews=True, can_invite_users=True,
)
_LOCK_TYPES = {
    "msgs": "can_send_messages", "media": "can_send_media_messages",
    "stickers": "can_send_other_messages", "gifs": "can_send_other_messages",
    "games": "can_send_other_messages", "inline": "can_send_other_messages",
    "polls": "can_send_polls", "info": "can_change_info",
    "invites": "can_invite_users", "pin": "can_pin_messages",
    "links": "links",
}
_LINK_REGEX = r"(https?://|t\.me/|www\.)\S+"
_flood_tracker: dict[str, list] = defaultdict(list)
_captcha_pending: dict[str, int] = {}
_raid_tracker: dict[int, list] = defaultdict(list)


def _is_admin_status(s):
    return s in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)


async def _get_member_safe(c, chat_id, user_id):
    try:
        return await c.get_chat_member(chat_id, user_id)
    except (UserNotParticipant, RPCError):
        return None


async def _apply_perm(c, chat_id, perm, lock):
    try:
        chat = await c.get_chat(chat_id)
        perms = chat.permissions or ChatPermissions(
            can_send_messages=True, can_send_media_messages=True, can_send_polls=True,
            can_send_other_messages=True, can_add_web_page_previews=True, can_invite_users=True,
        )
        setattr(perms, perm, not lock)
        await c.set_chat_permissions(chat_id, perms)
    except RPCError:
        pass


async def _is_disabled(chat_id, cmd: str) -> bool:
    doc = await _disable.find_one({"_id": chat_id}, {cmd: 1})
    return (doc or {}).get(cmd, False)







async def _is_approved(chat_id: int, user_id: int) -> bool:
    doc = await _cached_doc(_approved, f"{chat_id}_{user_id}")
    return bool(doc)


async def _approve_user(chat_id: int, user_id: int, name: str = "") -> None:
    await _approved.update_one(
        {"_id": f"{chat_id}_{user_id}"},
        {"$set": {"chat_id": chat_id, "user_id": user_id, "name": name}},
        upsert=True,
    )
    _invalidate(_approved.name, f"{chat_id}_{user_id}")


async def _disapprove_user(chat_id: int, user_id: int) -> None:
    await _approved.delete_one({"_id": f"{chat_id}_{user_id}"})
    _invalidate(_approved.name, f"{chat_id}_{user_id}")


@app.on_message(filters.command(["approve", "a"]) & filters.group)
@admin_required("can_restrict_members")
async def approve_cmd(client, message: Message):
    user_id, name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return
    await _approve_user(message.chat.id, user_id, name or "user")
    await message.reply_text(
        f"✅ **{mention(user_id, name or 'user')} has been approved in {message.chat.title}.**\n\n"
        "They will now be ignored by locks, blocklists and antiflood.",
        parse_mode="markdown",
    )


@app.on_message(filters.command(["disapprove", "unapprove", "da"]) & filters.group)
@admin_required("can_restrict_members")
async def disapprove_cmd(client, message: Message):
    user_id, name, _ = await extract_user_and_reason(message, client)
    if not user_id:
        return
    await _disapprove_user(message.chat.id, user_id)
    await message.reply_text(
        f"🗑 **{mention(user_id, name or 'user')} disapproved.** They are no longer ignored "
        "by locks, blocklists and antiflood.",
        parse_mode="markdown",
    )


@app.on_message(filters.command("approved") & filters.group)
async def approved_cmd(client, message: Message):
    lines = [f"✅ **Approved users in {message.chat.title}:**", ""]
    async for d in _approved.find({"chat_id": message.chat.id}):
        nm = d.get("name") or d["user_id"]
        lines.append(f"• `{d['user_id']}` — {nm}")
    if len(lines) == 2:
        lines.append("No approved users yet.")
    await message.reply_text("\n".join(lines), parse_mode="markdown")






_greet_cd = {}

@app.on_message(filters.regex(r"(?i)^(hi|hello|hey|hlo|bot)\b") & filters.text & filters.group, group=-99)
async def chatbot_handler(client, message: Message):



    user = message.from_user
    if not user or getattr(user, "is_bot", False):
        return
    if getattr(message, "forward_origin", None) is not None or getattr(message, "forward_from", None) is not None:
        return
    now_ts = time.time()
    key = (message.chat.id, user.id)
    if now_ts - _greet_cd.get(key, 0) < 60:
        return
    _greet_cd[key] = now_ts
    if len(_greet_cd) > 4096:
        _greet_cd.clear()
    replies = [
        "Hello! 👋", "Hi there!", "Hey! How can I help?", "Namaste 🙏",
        "What's up?", "Yo!", "Hi, how are you?",
    ]
    await message.reply(random.choice(replies))






@app.on_message(filters.command("goodbye") & filters.group)
async def goodbye_toggle(client, m: Message):
    usage = "Usage: /goodbye [on|off]\n/goodbye msg <custom text>"
    if len(m.command) < 2:
        return await m.reply_text(usage)
    user = await client.get_chat_member(m.chat.id, m.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await m.reply_text(ADMIN_ONLY)
    if m.command[1].lower() == "msg":
        if len(m.command) < 3:
            return await m.reply_text("Usage: /goodbye msg <text>")
        txt = m.text.split(None, 2)[2]
        await _goodbye.update_one({"_id": m.chat.id}, {"$set": {"message": txt}}, upsert=True)
        return await m.reply_text("Goodbye message updated!\nPlaceholders: {mention}, {name}, {uid}, {uname}")
    flag = m.command[1].lower()
    if flag not in ("on", "off"):
        return await m.reply_text(usage)
    await _goodbye.update_one({"_id": m.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await m.reply_text(f"Goodbye **{flag}**.", parse_mode="markdown")


@app.on_chat_member_updated(filters.group, group=-2)
async def goodbye_handler(client, update: ChatMemberUpdated):
    old, new = update.old_chat_member, update.new_chat_member
    cid = update.chat.id
    if not old: return
    if old.status not in (enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR): return
    if new and new.status != enums.ChatMemberStatus.LEFT: return
    doc = await _goodbye.find_one({"_id": cid}, {"state": 1, "message": 1})
    if not doc or doc.get("state", "on") != "on": return
    user = old.user
    if not user: return
    text = (doc.get("message") or "Goodbye, {mention}! 👋").format(
        mention=user.mention, name=user.first_name, uid=user.id, uname=user.username or "No Username",
    )
    try:
        await send_message_colored(cid, text, [[styled_button("👋", url=f"tg://openmessage?user_id={user.id}", style="primary")]])
    except Exception:
        try:
            await client.send_message(cid, text)
        except Exception:
            pass






@app.on_message(filters.command("captcha"))
async def captcha_toggle(client, message: Message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return await message.reply_text(ADMIN_ONLY)
    if len(message.command) != 2 or message.command[1].lower() not in ("on", "off"):
        return await message.reply_text("Usage: /captcha [on|off]")
    flag = message.command[1].lower()
    await _captcha.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Captcha **{flag}**.", parse_mode="markdown")


@app.on_chat_member_updated(filters.group, group=-1)
async def captcha_join(client, update: ChatMemberUpdated):
    old, new = update.old_chat_member, update.new_chat_member
    cid = update.chat.id
    if not (new and new.status == enums.ChatMemberStatus.MEMBER): return
    if old and old.status not in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED): return
    doc = await _captcha.find_one({"_id": cid}, {"state": 1})
    if not doc or doc.get("state", "off") != "on": return
    user = new.user
    if user.is_bot: return
    try:
        await client.restrict_chat_member(cid, user.id, ChatPermissions(can_send_messages=False))
    except RPCError: return
    a, b = random.randint(1, 20), random.randint(1, 20)
    answer = str(a + b)
    opts = [answer, str(a + b + random.randint(1, 5)), str(a + b - random.randint(1, 5))]
    random.shuffle(opts)
    key = f"{cid}_{user.id}"
    _captcha_pending[key] = int(answer)
    btns = [[styled_button(o, callback_data=f"rose_captcha_{user.id}_{o}", style="primary")] for o in opts]
    try:
        msg = await send_message_colored(
            cid,
            f"**Captcha**\n\n{mention(user.id, user.first_name)}, solve:\n\nWhat is {a} + {b}?",
            reply_markup=btns,
            parse_mode="markdown",
        )
    except Exception: return
    await asyncio.sleep(120)
    if key in _captcha_pending:
        del _captcha_pending[key]
        try: await client.ban_chat_member(cid, user.id); await client.unban_chat_member(cid, user.id)
        except RPCError: pass
        try: await app.delete_messages(cid, msg.get("message_id"))
        except Exception: pass


@app.on_callback_query(filters.regex(r"^rose_captcha_"))
async def captcha_cb(client, query: CallbackQuery):
    parts = query.data.split("_")
    uid = int(parts[2])
    chosen = parts[3]
    if query.from_user.id != uid:
        return await query.answer("Not for you!", show_alert=True)
    cid, key = query.message.chat.id, f"{query.message.chat.id}_{uid}"
    expected = _captcha_pending.get(key)
    if expected is None: return await query.answer("Expired!", show_alert=True)
    if int(chosen) == expected:
        del _captcha_pending[key]
        try: await client.restrict_chat_member(cid, uid, _MUTE_PERMS)
        except RPCError: pass
        await query.message.edit_text(f"✅ {query.from_user.mention}, verified!")
        await query.answer("Verified!")
    else:
        await query.answer("Wrong!", show_alert=True)






@app.on_message(filters.command("setrules"))
@admin_required("can_change_info")
async def setrules_cmd(client, message: Message):
    if len(message.command) == 1: return await message.reply_text("Usage: /setrules <text>")
    await _rules.update_one({"_id": message.chat.id}, {"$set": {"rules": message.text.split(None, 1)[1]}}, upsert=True)
    await message.reply_text("**Rules saved!**", parse_mode="markdown")


@app.on_message(filters.command("rules"))
async def rules_cmd(client, message: Message):
    doc = await _rules.find_one({"_id": message.chat.id}, {"rules": 1})
    if not doc or not doc.get("rules"): return await message.reply_text("No rules set.")
    await message.reply_text(f"**Rules for {message.chat.title}:**\n\n{doc['rules']}", parse_mode="markdown")


@app.on_message(filters.command("delrules"))
@admin_required("can_change_info")
async def delrules_cmd(client, message: Message):
    await _rules.delete_one({"_id": message.chat.id})
    await message.reply_text("**Rules deleted.**", parse_mode="markdown")






@app.on_message(filters.command("save"))
@admin_required("can_change_info")
async def save_note(client, message: Message):
    if len(message.command) < 3: return await message.reply_text("Usage: /save <name> <content>")
    name = message.command[1].lower()
    content = message.text.split(None, 2)[2]
    await _notes.update_one({"_id": f"{message.chat.id}_{name}"}, {"$set": {"chat_id": message.chat.id, "name": name, "content": content}}, upsert=True)
    await message.reply_text(f"Note saved: `{name}`", parse_mode="markdown")


@app.on_message(filters.command("note"))
async def get_note(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /note <name>")
    doc = await _notes.find_one({"_id": f"{message.chat.id}_{message.command[1].lower()}"}, {"content": 1})
    if not doc: return await message.reply_text(f"No note `{message.command[1]}`.", parse_mode="markdown")
    await message.reply_text(doc["content"])


@app.on_message(filters.command("notes"))
async def list_notes(client, message: Message):
    cursor = _notes.find({"chat_id": message.chat.id}, {"name": 1, "_id": 0})
    docs = await cursor.to_list(length=100)
    if not docs: return await message.reply_text("No notes.")
    text = "**📌 Notes:**\n\n" + "\n".join(f"• `{d['name']}`" for d in docs)
    await message.reply_text(text)


@app.on_message(filters.command("delete"))
@admin_required("can_change_info")
async def del_note(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /delete <name>")
    name = message.command[1].lower()
    res = await _notes.delete_one({"_id": f"{message.chat.id}_{name}"})
    await message.reply_text(f"Note `{name}` {'deleted.' if res.deleted_count else 'not found.'}", parse_mode="markdown")






@app.on_message(filters.command("filter"))
@admin_required("can_delete_messages")
async def save_filter(client, message: Message):
    if len(message.command) < 3: return await message.reply_text("Usage: /filter <keyword> <reply/text>")
    kw = message.command[1].lower()
    if message.reply_to_message:
        content = message.reply_to_message.text or message.reply_to_message.caption or ""
        if not content: return await message.reply_text("Reply to text.")
    else:
        content = message.text.split(None, 2)[2]
    await _filters.update_one({"_id": f"{message.chat.id}_{kw}"}, {"$set": {"chat_id": message.chat.id, "keyword": kw, "content": content}}, upsert=True)
    await message.reply_text(f"Filter saved: `{kw}`", parse_mode="markdown")


@app.on_message(filters.command("filters"))
async def list_filters(client, message: Message):
    cursor = _filters.find({"chat_id": message.chat.id}, {"keyword": 1, "_id": 0})
    docs = await cursor.to_list(length=200)
    if not docs: return await message.reply_text("No filters.")
    await message.reply_text("**🔍 Filters:**\n\n" + "\n".join(f"• `{d['keyword']}`" for d in docs), parse_mode="markdown")


@app.on_message(filters.command(["stopfilter", "stopnote"]))
@admin_required("can_delete_messages")
async def stop_filter(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /stop <filter>")
    kw = message.command[1].lower()
    res = await _filters.delete_one({"_id": f"{message.chat.id}_{kw}"})
    await message.reply_text(f"Filter `{kw}` {'stopped.' if res.deleted_count else 'not found.'}", parse_mode="markdown")


@app.on_message(filters.command(["filteron", "filteroff"]))
@admin_required("can_delete_messages")
async def filter_toggle(client, message: Message):
    flag = "on" if message.command[0] == "filteron" else "off"
    await _filters_state.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Filters **{flag}**.", parse_mode="markdown")


@app.on_message(filters.text & filters.group & ~filters.service, group=5)
async def auto_filter(client, message: Message):
    if not message.text: return
    doc = await _cached_doc(_filters_state, message.chat.id)
    if not doc or doc.get("state", "on") != "on": return
    cursor = _filters.find({"chat_id": message.chat.id}, {"keyword": 1, "content": 1})
    async for d in cursor:
        if d["keyword"] in message.text.lower():
            try:
                await message.reply_text(d["content"])
            except Exception: pass
            break






@app.on_message(filters.command("addblacklist"))
@admin_required("can_delete_messages")
async def add_bl(client, message: Message):
    if len(message.command) < 2: return await message.reply_text("Usage: /addblacklist <word>")
    word = message.text.split(None, 1)[1].lower()
    await _blacklist.update_one(
        {"_id": message.chat.id},
        {"$addToSet": {"words": word}},
        upsert=True,
    )
    await message.reply_text(f"Blacklisted: `{word}`", parse_mode="markdown")


@app.on_message(filters.command("rmblacklist"))
@admin_required("can_delete_messages")
async def rm_bl(client, message: Message):
    if len(message.command) < 2: return await message.reply_text("Usage: /rmblacklist <word>")
    word = message.text.split(None, 1)[1].lower()
    await _blacklist.update_one(
        {"_id": message.chat.id},
        {"$pull": {"words": word}},
    )
    await message.reply_text(f"Removed: `{word}`", parse_mode="markdown")


@app.on_message(filters.command("blacklisted"))
async def list_bl(client, message: Message):
    doc = await _blacklist.find_one({"_id": message.chat.id}, {"words": 1})
    words = (doc or {}).get("words", [])
    if not words: return await message.reply_text("No blacklisted words.")
    await message.reply_text("**🚫 Blacklisted words:**\n\n" + "\n".join(f"• `{w}`" for w in words), parse_mode="markdown")


@app.on_message(filters.command(["blackliston", "blacklistoff"]))
@admin_required("can_delete_messages")
async def bl_toggle(client, message: Message):
    flag = "on" if message.command[0] == "blackliston" else "off"
    await _blacklist_state.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Blacklist **{flag}**.", parse_mode="markdown")


@app.on_message(filters.text & filters.group & ~filters.service, group=6)
async def auto_blacklist(client, message: Message):
    if not message.text: return
    if await _is_approved(message.chat.id, message.from_user.id): return
    doc = await _cached_doc(_blacklist_state, message.chat.id)
    if doc and doc.get("state", "on") != "on": return
    bldoc = await _cached_doc(_blacklist, message.chat.id)
    words = (bldoc or {}).get("words", [])
    if not words: return
    text_lower = message.text.lower()
    for w in words:
        if w in text_lower:
            try:
                await message.delete()
            except Exception: pass
            try:
                await message.reply_text(f"**Blacklisted word detected!**", parse_mode="markdown")
            except Exception: pass
            break






def _warn_txt(chat, uid, name, admin, warns, limit, reason=None):
    t = (f"⚠️ **Warn in** {chat}\n User: {mention(uid, name)}\n Admin: {admin}\n Warns: {warns}/{limit}")
    if reason: t += f"\n Reason: {reason}"
    return t


@app.on_message(filters.command("warn"))
@admin_required("can_restrict_members")
async def warn_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text("Usage: /warn @user [reason]")
    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid: return
    tgt = await _get_member_safe(client, message.chat.id, uid)
    if tgt and _is_admin_status(tgt.status): return await message.reply_text("Cannot warn admin.")
    key = f"{message.chat.id}_{uid}"
    wdoc = await _warn.find_one_and_update({"_id": key}, {"$inc": {"warns": 1}}, upsert=True, return_document=True)
    warns = wdoc["warns"]
    limit = (await _warnset.find_one({"_id": message.chat.id}, {"limit": 1}) or {}).get("limit", 3)
    action = (await _warnset.find_one({"_id": message.chat.id}, {"action": 1}) or {}).get("action", "mute")
    am = mention(message.from_user.id, message.from_user.first_name)
    await message.reply_text(_warn_txt(message.chat.title, uid, name, am, warns, limit, reason), parse_mode="markdown")
    if warns >= limit:
        try:
            if action == "ban": await client.ban_chat_member(message.chat.id, uid)
            elif action == "mute": await client.restrict_chat_member(message.chat.id, uid, _DEF_MUTE)
            elif action == "kick":
                await client.ban_chat_member(message.chat.id, uid)
                await asyncio.sleep(2)
                await client.unban_chat_member(message.chat.id, uid)
            await message.reply_text(f"{mention(uid, name)} auto-{action}ed (warn limit).", parse_mode="markdown")
        except ChatAdminRequired: await message.reply_text("Need restrict perms.")
        await _warn.delete_one({"_id": key})


@app.on_message(filters.command("unwarn"))
@admin_required("can_restrict_members")
async def unwarn_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text("Usage: /unwarn @user")
    uid, name, _ = await extract_user_and_reason(message, client)
    if not uid: return
    key = f"{message.chat.id}_{uid}"
    doc = await _warn.find_one({"_id": key})
    if not doc or doc.get("warns", 0) == 0: return await message.reply_text(f"0 warns.")
    wdoc = await _warn.find_one_and_update({"_id": key}, {"$inc": {"warns": -1}}, return_document=True)
    warns = max(0, wdoc["warns"])
    if warns == 0: await _warn.delete_one({"_id": key})
    await message.reply_text(f"Removed warn. {mention(uid, name)} now has {warns} warn(s).", parse_mode="markdown")


@app.on_message(filters.command("resetwarns"))
@admin_required("can_restrict_members")
async def resetwarns_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text("Usage: /resetwarns @user")
    uid, name, _ = await extract_user_and_reason(message, client)
    if not uid: return
    await _warn.delete_one({"_id": f"{message.chat.id}_{uid}"})
    await message.reply_text(f"Reset warns for {mention(uid, name)}.", parse_mode="markdown")


@app.on_message(filters.command("warns"))
async def warns_cmd(client, message: Message):
    if message.reply_to_message:
        uid, name = message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        try:
            u = await client.get_users(message.command[1])
            uid, name = u.id, u.first_name
        except: return await message.reply_text("User not found.")
    else:
        uid, name = message.from_user.id, message.from_user.first_name
    doc = await _warn.find_one({"_id": f"{message.chat.id}_{uid}"})
    warns = (doc or {}).get("warns", 0)
    limit = (await _warnset.find_one({"_id": message.chat.id}, {"limit": 1}) or {}).get("limit", 3)
    await message.reply_text(f"{mention(uid, name)} has **{warns}/{limit}** warn(s).", parse_mode="markdown")


@app.on_message(filters.command(["warnlimit", "setwarnlimit"]))
@admin_required("can_restrict_members")
async def setwarnlimit_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /warnlimit <num>")
    try: lmt = int(message.command[1])
    except: return await message.reply_text("Invalid number.")
    if lmt < 1 or lmt > 20: return await message.reply_text("1-20 only.")
    await _warnset.update_one({"_id": message.chat.id}, {"$set": {"limit": lmt}}, upsert=True)
    await message.reply_text(f"Warn limit set to {lmt}.")


@app.on_message(filters.command(["warnaction", "setwarnaction"]))
@admin_required("can_restrict_members")
async def setwarnaction_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /warnaction <mute|ban|kick>")
    act = message.command[1].lower()
    if act not in ("mute", "ban", "kick"): return await message.reply_text("mute/ban/kick.")
    await _warnset.update_one({"_id": message.chat.id}, {"$set": {"action": act}}, upsert=True)
    await message.reply_text(f"Warn action: {act}.")






@app.on_message(filters.command(["report"]) & filters.group, group=2)
async def report_cmd(client, message: Message):
    doc = await _report.find_one({"_id": message.chat.id}, {"state": 1})
    if not doc or doc.get("state", "on") != "on": return
    if not message.reply_to_message: return await message.reply_text("Reply to a message to report.")
    admins = []
    async for m in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if not m.user.is_bot: admins.append(mention(m.user.id, m.user.first_name))
    if not admins: return await message.reply_text("No admins.")
    txt = (f"📢 **Report**\n Chat: {message.chat.title}\n Reported by: {mention(message.from_user.id, message.from_user.first_name)}\n"
           f" User: {mention(message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name) if message.reply_to_message and message.reply_to_message.from_user else 'Unknown'}\n"
           f" Message: {(message.reply_to_message.text or '[not text]')[:200]}")
    await message.reply_text(txt, parse_mode="markdown")
    try: await message.reply_text(" ".join(admins) + "\n\n**Please check the report!**", parse_mode="markdown")
    except TopicClosed: pass


@app.on_message(filters.command(["reporton", "reportoff"]))
async def report_toggle(client, message: Message):
    user = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER): return
    flag = "on" if message.command[0] == "reporton" else "off"
    await _report.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Report **{flag}**.", parse_mode="markdown")






@app.on_message(filters.text & filters.group & ~filters.service, group=3)
async def antiflood_handler(client, message: Message):
    if message.sender_chat: return
    if await _is_approved(message.chat.id, message.from_user.id): return
    doc = await _cached_doc(_flood, message.chat.id)
    if not doc or doc.get("state", "off") != "on": return
    limit = doc.get("limit", 5)
    window = doc.get("time", 5)
    action = doc.get("action", "mute")
    uid, cid = message.from_user.id, message.chat.id
    key = f"{cid}_{uid}"
    now = time.time()
    _flood_tracker[key].append(now)
    _flood_tracker[key] = [t for t in _flood_tracker[key] if now - t <= window]
    if len(_flood_tracker[key]) > limit:
        _flood_tracker[key].clear()
        tgt = await _get_member_safe(client, cid, uid)
        if tgt and _is_admin_status(tgt.status): return
        nm = message.from_user.first_name
        try:
            if action == "mute":
                await client.restrict_chat_member(cid, uid, _DEF_MUTE)
                await message.reply_text(f"{mention(uid, nm)} muted [flood]", parse_mode="markdown")
            elif action == "ban":
                await client.ban_chat_member(cid, uid)
                await message.reply_text(f"{mention(uid, nm)} banned [flood]", parse_mode="markdown")
            elif action == "kick":
                await client.ban_chat_member(cid, uid); await asyncio.sleep(2); await client.unban_chat_member(cid, uid)
                await message.reply_text(f"{mention(uid, nm)} kicked [flood]", parse_mode="markdown")
            elif action == "warn":
                key2 = f"{cid}_{uid}"
                w = (await _warn.find_one_and_update({"_id": key2}, {"$inc": {"warns": 1}}, upsert=True, return_document=True))["warns"]
                wl = (await _warnset.find_one({"_id": cid}, {"limit": 1}) or {}).get("limit", 3)
                wa = (await _warnset.find_one({"_id": cid}, {"action": 1}) or {}).get("action", "mute")
                await message.reply_text(f"{mention(uid, nm)} warned [flood] ({w}/{wl})")
                if w >= wl:
                    if wa == "ban": await client.ban_chat_member(cid, uid)
                    elif wa == "mute": await client.restrict_chat_member(cid, uid, _DEF_MUTE)
                    elif wa == "kick":
                        await client.ban_chat_member(cid, uid); await asyncio.sleep(2); await client.unban_chat_member(cid, uid)
                    await _warn.delete_one({"_id": key2})
        except (ChatAdminRequired, UserAdminInvalid): pass


@app.on_message(filters.command("setflood"))
@admin_required("can_restrict_members")
async def setflood_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /setflood <count>")
    try: lmt = int(message.command[1])
    except: return await message.reply_text("Invalid number.")
    if lmt < 2 or lmt > 50: return await message.reply_text("2-50 only.")
    await _flood.update_one({"_id": message.chat.id}, {"$set": {"limit": lmt}}, upsert=True)
    await message.reply_text(f"Flood limit: {lmt} msgs.")


@app.on_message(filters.command("floodaction"))
@admin_required("can_restrict_members")
async def floodaction_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /floodaction <mute|ban|kick|warn>")
    act = message.command[1].lower()
    if act not in ("mute", "ban", "kick", "warn"): return await message.reply_text("mute/ban/kick/warn.")
    await _flood.update_one({"_id": message.chat.id}, {"$set": {"action": act}}, upsert=True)
    await message.reply_text(f"Flood action: {act}.")


@app.on_message(filters.command("floodtime"))
@admin_required("can_restrict_members")
async def floodtime_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /floodtime <seconds>")
    try: sec = int(message.command[1])
    except: return await message.reply_text("Invalid number.")
    if sec < 1 or sec > 60: return await message.reply_text("1-60 only.")
    await _flood.update_one({"_id": message.chat.id}, {"$set": {"time": sec}}, upsert=True)
    await message.reply_text(f"Flood time: {sec}s.")


@app.on_message(filters.command(["floodon", "floodoff"]))
@admin_required("can_restrict_members")
async def flood_toggle(client, message: Message):
    flag = "on" if message.command[0] == "floodon" else "off"
    await _flood.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Anti-flood **{flag}**.", parse_mode="markdown")






@app.on_message(filters.command("lock"))
@admin_required("can_restrict_members")
async def lock_cmd(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /lock <type>\nTypes: " + " | ".join(_LOCK_TYPES.keys()))
    lt = message.command[1].lower()
    if lt not in _LOCK_TYPES: return await message.reply_text("Invalid type.")
    await _locks.update_one({"_id": message.chat.id}, {"$set": {lt: True}}, upsert=True)
    if _LOCK_TYPES[lt] != "links": await _apply_perm(client, message.chat.id, _LOCK_TYPES[lt], True)
    await message.reply_text(f"**Locked:** `{lt}`", parse_mode="markdown")


@app.on_message(filters.command("unlock"))
@admin_required("can_restrict_members")
async def unlock_cmd(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /unlock <type>\nTypes: " + " | ".join(_LOCK_TYPES.keys()))
    lt = message.command[1].lower()
    if lt not in _LOCK_TYPES: return await message.reply_text("Invalid type.")
    await _locks.update_one({"_id": message.chat.id}, {"$set": {lt: False}}, upsert=True)
    if _LOCK_TYPES[lt] != "links": await _apply_perm(client, message.chat.id, _LOCK_TYPES[lt], False)
    await message.reply_text(f"**Unlocked:** `{lt}`", parse_mode="markdown")


@app.on_message(filters.command("locks"))
async def locks_cmd(client, message: Message):
    doc = await _locks.find_one({"_id": message.chat.id})
    lines = []
    for lt in _LOCK_TYPES:
        locked = (doc or {}).get(lt, False)
        lines.append(f"{'🔒' if locked else '🔓'} `{lt}`")
    await message.reply_text("**Locks:**\n\n" + "\n".join(lines), parse_mode="markdown")


@app.on_message(filters.text & filters.group & ~filters.service, group=4)
async def link_lock_handler(client, message: Message):
    if message.sender_chat or not message.text: return
    if await _is_approved(message.chat.id, message.from_user.id): return
    doc = await _cached_doc(_locks, message.chat.id)
    if not doc or not doc.get("links"): return
    tgt = await _get_member_safe(client, message.chat.id, message.from_user.id)
    if tgt and _is_admin_status(tgt.status): return
    if re.search(_LINK_REGEX, message.text, re.IGNORECASE):
        try: await message.delete()
        except: pass






@app.on_message(filters.command(["raid", "antiraid"]))
async def raid_toggle(client, message: Message):
    u = await client.get_chat_member(message.chat.id, message.from_user.id)
    if u.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER): return
    if len(message.command) != 2: return await message.reply_text("Usage: /raid [on|off]")
    flag = message.command[1].lower()
    if flag not in ("on", "off"): return await message.reply_text("on/off.")
    await _raid.update_one({"_id": message.chat.id}, {"$set": {"state": flag}}, upsert=True)
    await message.reply_text(f"Anti-raid **{flag}**.", parse_mode="markdown")


@app.on_chat_member_updated(filters.group, group=-5)
async def raid_detect(client, update: ChatMemberUpdated):
    old, new = update.old_chat_member, update.new_chat_member
    cid = update.chat.id
    if not (new and new.status == enums.ChatMemberStatus.MEMBER): return
    if old and old.status not in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED): return
    doc = await _raid.find_one({"_id": cid}, {"state": 1})
    if not doc or doc.get("state", "off") != "on": return
    now = time.time()
    _raid_tracker[cid].append(now)
    _raid_tracker[cid] = [t for t in _raid_tracker[cid] if now - t <= 10]
    if len(_raid_tracker[cid]) >= 10:
        _raid_tracker[cid].clear()
        try:
            chat = await client.get_chat(cid)
            perms = ChatPermissions(can_send_messages=False)
            await client.set_chat_permissions(cid, perms)
            await client.send_message(cid, "**Raid detected!** Group locked (no msgs) for safety. Admins use /unlock msgs.", parse_mode="markdown")
        except Exception: pass






@app.on_message(filters.command("disable"))
@admin_required("can_change_info")
async def disable_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /disable <command>")
    cmd = message.command[1].lower().replace("/", "")
    await _disable.update_one({"_id": message.chat.id}, {"$set": {cmd: True}}, upsert=True)
    await message.reply_text(f"Disabled: `/{cmd}`", parse_mode="markdown")


@app.on_message(filters.command("enable"))
@admin_required("can_change_info")
async def enable_cmd(client, message: Message):
    if len(message.command) != 2: return await message.reply_text("Usage: /enable <command>")
    cmd = message.command[1].lower().replace("/", "")
    await _disable.update_one({"_id": message.chat.id}, {"$unset": {cmd: ""}})
    await message.reply_text(f"Enabled: `/{cmd}`", parse_mode="markdown")


@app.on_message(filters.command("disabled"))
async def disabled_cmd(client, message: Message):
    doc = await _disable.find_one({"_id": message.chat.id})
    if not doc: return await message.reply_text("No disabled commands.")
    cmds = [f"`/{k}`" for k in doc if k != "_id"]
    if not cmds: return await message.reply_text("No disabled commands.")
    await message.reply_text("**Disabled commands:**\n\n" + "\n".join(cmds), parse_mode="markdown")






@app.on_message(filters.command("usernote"))
@admin_required("can_restrict_members")
async def usernote_cmd(client, message: Message):
    if len(message.command) < 3: return await message.reply_text("Usage: /usernote @user <note>")
    uid, name, _ = await extract_user_and_reason(message, client)
    if not uid: return
    note = message.text.split(None, 2)[2]
    await _user_notes.update_one({"_id": f"{message.chat.id}_{uid}"}, {"$set": {"chat_id": message.chat.id, "user_id": uid, "note": note}}, upsert=True)
    await message.reply_text(f"Note saved for {mention(uid, name)}.")


@app.on_message(filters.command("usernotes"))
async def usernotes_cmd(client, message: Message):
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            u = await client.get_users(message.command[1])
            uid = u.id
        except: return await message.reply_text("User not found.")
    else:
        uid = message.from_user.id
    doc = await _user_notes.find_one({"_id": f"{message.chat.id}_{uid}"}, {"note": 1})
    if not doc: return await message.reply_text("No note for this user.")
    await message.reply_text(f"**User note:**\n\n{doc['note']}", parse_mode="markdown")







