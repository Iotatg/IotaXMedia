# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Clean /info card + public TG helpers.

Output style (unicode, minimal):
  Name's Hɪꜱᴛᴏʀʏ
  ________________________
  Fᴜʟʟ Nᴀᴍᴇꜱ:
  • ...
  Uꜱᴇʀɴᴀᴍᴇꜱ:
  • @...

Sources: Telegram API, Mongo cache/history/peers, LOLS, tg-userid resolve.
Phone only when Telegram exposes it (contact/self).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Optional

import httpx
from pyrogram import enums, raw
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied, UsernameInvalid

from IotaXMedia.utils import user_tracker

logger = logging.getLogger(__name__)

LOLS_URL = "https://api.lols.bot/account"
TG_USERID_URL = "https://tg-userid.onrender.com/api/user"

try:
    from IotaXMedia.utils.sg_archive import approx_creation_date as _approx_age
except Exception:  # pragma: no cover
    def _approx_age(user_id: int) -> str:
        return "unknown"



_SC = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ",
)


def _label(text: str) -> str:
    return text.upper().translate(_SC)


def full_name(user) -> str:
    if not user:
        return "Unknown"
    first = getattr(user, "first_name", None) or ""
    last = getattr(user, "last_name", None) or ""
    return f"{first} {last}".strip() or "Unknown"


def status_text(status) -> str:
    if status is None:
        return "Unknown"
    if isinstance(status, str):
        key = status.replace("UserStatus.", "").lower()
    elif isinstance(status, enums.UserStatus):
        key = status.name.lower()
    else:
        key = str(status).lower()
    return {
        "online": "Online",
        "offline": "Offline",
        "recently": "Recently",
        "last_week": "Within a week",
        "last_month": "Within a month",
        "long_ago": "Long time ago",
    }.get(key, key.replace("_", " ").title())


def fmt_dt(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        try:
            return value.strftime("%d/%m/%Y")
        except Exception:
            return str(value)[:10]
    return str(value)[:16]


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


async def resolve_user(client, message, arg: Optional[str] = None):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    text_arg = arg
    if text_arg is None and message.command and len(message.command) > 1:
        text_arg = message.command[1]
    if not text_arg:
        if message.entities:
            for ent in message.entities:
                if ent.type == enums.MessageEntityType.TEXT_MENTION and ent.user:
                    return ent.user
        return message.from_user

    text_arg = text_arg.strip()
    try:
        if text_arg.isdigit() or (text_arg.startswith("-") and text_arg[1:].isdigit()):
            return await client.get_users(int(text_arg))
        return await client.get_users(text_arg.lstrip("@"))
    except (PeerIdInvalid, UsernameNotOccupied, UsernameInvalid, IndexError, KeyError, ValueError):
        if text_arg.lstrip("@").replace("_", "").isalnum():
            prof = await user_tracker.lookup_by_username(text_arg)
            if prof:
                try:
                    return await client.get_users(int(prof["_id"]))
                except Exception:
                    return None
        return None
    except Exception as e:
        logger.debug(f"resolve_user failed: {e}")
        return None


async def fetch_full_user(client, user_id: int) -> dict:
    out: dict[str, Any] = {}
    try:
        peer = await client.resolve_peer(user_id)
        result = await client.invoke(raw.functions.users.GetFullUser(id=peer))
        full = getattr(result, "full_user", None) or result
        out["about"] = getattr(full, "about", None)
        out["common_chats_count"] = getattr(full, "common_chats_count", None)
        out["has_profile_photo"] = bool(getattr(full, "profile_photo", None))
        for u in getattr(result, "users", None) or []:
            if getattr(u, "id", None) == user_id:
                phone = getattr(u, "phone", None)
                if phone:
                    out["phone"] = phone
                break
    except Exception as e:
        logger.debug(f"GetFullUser failed for {user_id}: {e}")
    return out


async def fetch_lols(user_id: int) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as http:
            r = await http.get(LOLS_URL, params={"id": int(user_id)})
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict):
                    return data
    except Exception as e:
        logger.debug(f"LOLS lookup failed: {e}")
    return {}


async def fetch_tg_userid(username: Optional[str] = None) -> dict:
    if not username:
        return {}
    try:
        async with httpx.AsyncClient(timeout=7.0) as http:
            r = await http.get(
                TG_USERID_URL, params={"username": username.lstrip("@")}
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and data.get("id"):
                    return data
    except Exception as e:
        logger.debug(f"tg-userid lookup failed: {e}")
    return {}


def _unique_names(hist: list, current: str) -> list:
    seen = set()
    out = []
    if current:
        key = current.strip().lower()
        seen.add(key)
        out.append(current.strip())
    for n in hist:
        val = (n.get("name") or "").strip()
        if not val:
            continue
        key = val.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out


def _unique_usernames(hist: list, current: Optional[str]) -> list:
    seen = set()
    out = []
    if current:
        u = current.lstrip("@").lower()
        seen.add(u)
        out.append(f"@{current.lstrip('@')}")
    for n in hist:
        val = (n.get("username") or "").strip().lstrip("@").lower()
        if not val or val in seen:
            continue
        seen.add(val)
        out.append(f"@{val}")
    return out


async def build_user_info(client, user, *, include_history: bool = True) -> str:
    """Clean unicode history-style card. Saves profile to Mongo on every call."""
    await user_tracker.track_from_pyrogram_user(
        user, source=user_tracker.EVENT_LOOKUP
    )

    try:
        chat = await client.get_chat(user.id)
    except Exception:
        chat = None

    full = await fetch_full_user(client, user.id)
    lols = await fetch_lols(user.id)
    uname = getattr(user, "username", None)
    ext = await fetch_tg_userid(uname) if uname else {}

    name = full_name(user)
    bio = (
        full.get("about")
        or (getattr(chat, "bio", None) if chat else None)
        or ""
    )
    phone = getattr(user, "phone_number", None) or full.get("phone")


    try:
        await user_tracker.track_user(
            user.id,
            getattr(user, "first_name", None),
            getattr(user, "last_name", None),
            uname,
            is_bot=bool(user.is_bot or ext.get("isBot")),
            is_premium=bool(user.is_premium or ext.get("isPremium")),
            is_verified=bool(user.is_verified or ext.get("isVerified")),
            is_scam=bool(getattr(user, "is_scam", False)),
            is_fake=bool(getattr(user, "is_fake", False)),
            language_code=getattr(user, "language_code", None),
            dc_id=getattr(user, "dc_id", None),
            phone=phone,
            source=user_tracker.EVENT_LOOKUP,
        )
    except Exception:
        pass

    names_hist = await user_tracker.get_name_history(user.id, limit=30)
    unames_hist = await user_tracker.get_username_history(user.id, limit=30)
    full_names = _unique_names(names_hist, name)
    usernames = _unique_usernames(unames_hist, uname)


    for attr in ("active_usernames", "usernames"):
        extra = getattr(user, attr, None)
        if extra:
            for u in extra:
                un = getattr(u, "username", None) or (u if isinstance(u, str) else None)
                if un:
                    tag = f"@{un.lstrip('@')}"
                    if tag.lower() not in [x.lower() for x in usernames]:
                        usernames.append(tag)

    title = f"{_esc(name)}'s {_label('History')}"
    lines = [
        f"<b>{title}</b>",
        "________________________",
        "",
        f"<b>{_label('Full Names')}:</b>",
    ]
    if full_names:
        for n in full_names:
            lines.append(f"• {_esc(n)}")
    else:
        lines.append("• —")

    lines += ["", "-----------", "", f"<b>{_label('Usernames')}:</b>"]
    if usernames:
        for u in usernames:
            lines.append(f"• {u}")
    else:
        lines.append("• —")

    lines += [
        "",
        "-----------",
        "",
        f"<b>{_label('Profile')}:</b>",
        f"• ID: <code>{user.id}</code>",
    ]
    if phone:
        lines.append(f"• Phone: <code>{_esc(phone)}</code>")

    bits = []
    if user.is_bot or ext.get("isBot"):
        bits.append("Bot")
    if user.is_verified or ext.get("isVerified"):
        bits.append("Verified")
    if user.is_premium or ext.get("isPremium"):
        bits.append("Premium")
    if getattr(user, "is_scam", False):
        bits.append("Scam")
    if getattr(user, "is_fake", False):
        bits.append("Fake")
    if bits:
        lines.append(f"• Flags: {', '.join(bits)}")

    age = _approx_age(user.id)
    if age and age != "unknown":
        lines.append(f"• Approx age: <code>{age}</code>")

    if bio:
        lines.append(f"• Bio: {_esc(bio[:200])}")

    st = status_text(getattr(user, "status", None))
    if st and st != "Unknown":
        lines.append(f"• Status: {st}")

    if lols.get("banned") is True:
        when = lols.get("when") or ""
        lines.append(f"• LOLS: BANNED{(' ' + str(when)) if when else ''}")
    elif lols.get("banned") is False:
        lines.append("• LOLS: Clean")


    try:
        out_p = await user_tracker.get_outgoing_peers(user.id, limit=5)
        in_p = await user_tracker.get_incoming_peers(user.id, limit=5)
        if out_p or in_p:
            lines += ["", "-----------", "", f"<b>{_label('Seen With')}:</b>"]
            for r in out_p[:4]:
                tid = r.get("target_id")
                prof = await user_tracker.get_profile(tid) if tid else {}
                nm = prof.get("name") or str(tid)
                un = prof.get("username")
                tag = f"@{un}" if un else str(tid)
                lines.append(f"• → {_esc(nm)} ({tag})")
            for r in in_p[:4]:
                oid = r.get("observer_id")
                prof = await user_tracker.get_profile(oid) if oid else {}
                nm = prof.get("name") or str(oid)
                un = prof.get("username")
                tag = f"@{un}" if un else str(oid)
                lines.append(f"• ← {_esc(nm)} ({tag})")
    except Exception:
        pass

    prof = await user_tracker.get_profile(user.id)
    if prof and (prof.get("first_seen_at") or prof.get("seen_count")):
        lines += ["", "-----------"]
        if prof.get("seen_count"):
            lines.append(f"• Seen: <code>{prof['seen_count']}</code>x")
        if prof.get("first_seen_at"):
            lines.append(f"• First: {fmt_dt(prof.get('first_seen_at'))}")
        if prof.get("last_seen_at"):
            lines.append(f"• Last: {fmt_dt(prof.get('last_seen_at'))}")

    text = "\n".join(lines)
    if len(text) > 3900:
        text = text[:3900] + "…"
    return text


async def build_history_card(user_id: int, name: str = "") -> str:
    """Fallback when only local id is known (no live User object)."""
    names = await user_tracker.get_name_history(user_id, limit=30)
    unames = await user_tracker.get_username_history(user_id, limit=30)
    prof = await user_tracker.get_profile(user_id)
    display = name or prof.get("name") or str(user_id)
    full_names = _unique_names(names, display if display != str(user_id) else "")
    usernames = _unique_usernames(unames, prof.get("username"))

    lines = [
        f"<b>{_esc(display)}'s {_label('History')}</b>",
        "________________________",
        "",
        f"<b>{_label('Full Names')}:</b>",
    ]
    if full_names:
        for n in full_names:
            lines.append(f"• {_esc(n)}")
    else:
        lines.append("• No names cached yet")

    lines += ["", "-----------", "", f"<b>{_label('Usernames')}:</b>"]
    if usernames:
        for u in usernames:
            lines.append(f"• {u}")
    else:
        lines.append("• No usernames cached yet")

    lines += [
        "",
        "-----------",
        "",
        f"• ID: <code>{user_id}</code>",
    ]
    if prof.get("phone"):
        lines.append(f"• Phone: <code>{_esc(prof['phone'])}</code>")
    if prof.get("seen_count"):
        lines.append(f"• Seen: <code>{prof['seen_count']}</code>x")
    return "\n".join(lines)
