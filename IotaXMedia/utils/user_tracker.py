# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Track public Telegram profile data + peer-to-peer observations.

Only stores data Telegram already exposes to the bot:
  - id, name, username, flags, language, dc (if present)
  - peer links: who replied / forwarded / looked up whom (bot-seen)
Does NOT scrape private phones or closed-profile secrets.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from IotaXMedia.core.mongo import mongodb

_profiles = mongodb.tg_user_profiles
_name_hist = mongodb.tg_name_history
_user_hist = mongodb.tg_username_history
_peers = mongodb.tg_peer_links
_events = mongodb.tg_peer_events

_MAX_HISTORY = 50
_MAX_PEERS = 40
_MAX_EVENTS = 30


EVENT_REPLY = "reply"
EVENT_FORWARD = "forward"
EVENT_MENTION = "mention"
EVENT_LOOKUP = "lookup"
EVENT_GROUP_MSG = "group_msg"
EVENT_JOIN = "join"
EVENT_PRIVATE = "private"
EVENT_CONTACT = "contact"


def _now():
    return datetime.now(timezone.utc)


def _full_name(first: Optional[str], last: Optional[str]) -> str:
    parts = [p for p in [(first or "").strip(), (last or "").strip()] if p]
    return " ".join(parts) or "Unknown"


async def _push_history(col, user_id: int, field: str, value: str) -> None:
    if value is None:
        return

    doc = await col.find_one({"_id": int(user_id)}) or {}
    hist = doc.get("history") or []
    tip = hist[0].get(field) if hist else None
    if tip == value:
        return
    entry = {field: value, "changed_at": _now()}
    await col.update_one(
        {"_id": int(user_id)},
        {
            "$push": {
                "history": {
                    "$each": [entry],
                    "$position": 0,
                    "$slice": _MAX_HISTORY,
                }
            }
        },
        upsert=True,
    )


async def track_user(
    user_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    *,
    is_bot: bool = False,
    is_premium: bool = False,
    is_verified: bool = False,
    is_scam: bool = False,
    is_fake: bool = False,
    language_code: Optional[str] = None,
    dc_id: Optional[int] = None,
    phone: Optional[str] = None,
    source: str = "seen",
) -> dict:
    """Upsert public profile + name/username history on change."""
    if not user_id:
        return {}

    name = _full_name(first_name, last_name)
    uname = (username or "").lstrip("@").lower() or None
    now = _now()

    update = {
        "name": name,
        "first_name": first_name or "",
        "last_name": last_name or "",
        "username": uname,
        "is_bot": bool(is_bot),
        "is_premium": bool(is_premium),
        "is_verified": bool(is_verified),
        "is_scam": bool(is_scam),
        "is_fake": bool(is_fake),
        "language_code": language_code,
        "last_seen_at": now,
        "updated_at": now,
        "last_source": source,
    }
    if dc_id is not None:
        update["dc_id"] = dc_id

    if phone:
        update["phone"] = str(phone)

    await _profiles.update_one(
        {"_id": int(user_id)},
        {
            "$set": update,
            "$setOnInsert": {"first_seen_at": now},
            "$inc": {"seen_count": 1},
            "$addToSet": {"sources": source},
        },
        upsert=True,
    )

    await _push_history(_name_hist, user_id, "name", name)
    if uname:
        await _push_history(_user_hist, user_id, "username", uname)

    return update


async def track_from_pyrogram_user(user, *, source: str = "seen") -> dict:
    if not user:
        return {}
    return await track_user(
        user.id,
        getattr(user, "first_name", None),
        getattr(user, "last_name", None),
        getattr(user, "username", None),
        is_bot=bool(getattr(user, "is_bot", False)),
        is_premium=bool(getattr(user, "is_premium", False)),
        is_verified=bool(getattr(user, "is_verified", False)),
        is_scam=bool(getattr(user, "is_scam", False)),
        is_fake=bool(getattr(user, "is_fake", False)),
        language_code=getattr(user, "language_code", None),
        dc_id=getattr(user, "dc_id", None),
        phone=getattr(user, "phone_number", None) or getattr(user, "phone", None),
        source=source,
    )


async def record_peer(
    observer_id: int,
    target_id: int,
    event: str,
    *,
    chat_id: Optional[int] = None,
    meta: Optional[dict] = None,
) -> None:
    """Store directed observation: observer touched target via event.

    Examples:
      A replies to B  → observer=A target=B event=reply
      A runs /info B  → observer=A target=B event=lookup
      A forwards B    → observer=A target=B event=forward
    """
    if not observer_id or not target_id or observer_id == target_id:
        return
    now = _now()
    oid, tid = int(observer_id), int(target_id)
    link_id = f"{oid}:{tid}"

    await _peers.update_one(
        {"_id": link_id},
        {
            "$set": {
                "observer_id": oid,
                "target_id": tid,
                "last_event": event,
                "last_chat_id": chat_id,
                "last_at": now,
            },
            "$setOnInsert": {"first_at": now},
            "$inc": {"count": 1, f"events.{event}": 1},
        },
        upsert=True,
    )


    entry = {
        "event": event,
        "chat_id": chat_id,
        "at": now,
        "meta": meta or {},
    }
    await _events.update_one(
        {"_id": link_id},
        {
            "$push": {
                "log": {
                    "$each": [entry],
                    "$position": 0,
                    "$slice": _MAX_EVENTS,
                }
            },
            "$set": {"observer_id": oid, "target_id": tid, "updated_at": now},
        },
        upsert=True,
    )


async def observe_pair(
    observer,
    target,
    event: str,
    *,
    chat_id: Optional[int] = None,
    meta: Optional[dict] = None,
) -> None:
    """Track both users' public profiles + peer edge."""
    if observer:
        await track_from_pyrogram_user(observer, source=event)
    if target:
        await track_from_pyrogram_user(target, source=event)
    if observer and target:
        await record_peer(
            observer.id,
            target.id,
            event,
            chat_id=chat_id,
            meta=meta,
        )


async def get_profile(user_id: int) -> dict:
    return await _profiles.find_one({"_id": int(user_id)}) or {}


async def get_name_history(user_id: int, limit: int = 20) -> list:
    doc = await _name_hist.find_one({"_id": int(user_id)}) or {}
    return (doc.get("history") or [])[:limit]


async def get_username_history(user_id: int, limit: int = 20) -> list:
    doc = await _user_hist.find_one({"_id": int(user_id)}) or {}
    return (doc.get("history") or [])[:limit]


async def lookup_by_username(username: str) -> Optional[dict]:
    uname = (username or "").lstrip("@").lower()
    if not uname:
        return None
    return await _profiles.find_one({"username": uname})


async def get_outgoing_peers(user_id: int, limit: int = 15) -> list:
    """Users this user interacted with / looked up (bot-seen)."""
    cur = (
        _peers.find({"observer_id": int(user_id)})
        .sort("last_at", -1)
        .limit(limit)
    )
    return await cur.to_list(length=limit)


async def get_incoming_peers(user_id: int, limit: int = 15) -> list:
    """Users who interacted with / looked up this user (bot-seen)."""
    cur = (
        _peers.find({"target_id": int(user_id)})
        .sort("last_at", -1)
        .limit(limit)
    )
    return await cur.to_list(length=limit)


async def enrich_peer_rows(rows: list) -> list:
    """Attach cached profile snippets to peer link rows."""
    out = []
    for r in rows:
        oid = r.get("observer_id")
        tid = r.get("target_id")
        other_id = tid
        prof_o = await get_profile(oid) if oid else {}
        prof_t = await get_profile(tid) if tid else {}
        out.append(
            {
                **r,
                "observer": {
                    "id": oid,
                    "name": prof_o.get("name"),
                    "username": prof_o.get("username"),
                },
                "target": {
                    "id": tid,
                    "name": prof_t.get("name"),
                    "username": prof_t.get("username"),
                },
            }
        )
    return out


async def build_peer_card(user_id: int, limit: int = 8) -> str:
    """HTML snippet of peer graph for /info."""
    out_rows = await enrich_peer_rows(await get_outgoing_peers(user_id, limit))
    in_rows = await enrich_peer_rows(await get_incoming_peers(user_id, limit))

    def _fmt_side(rows, key_other: str) -> list:
        lines = []
        for r in rows:
            other = r.get(key_other) or {}
            name = other.get("name") or "—"
            un = other.get("username")
            tag = f"@{un}" if un else str(other.get("id") or "?")
            ev = r.get("last_event") or "?"
            n = r.get("count") or 1
            lines.append(f"• {name} ({tag}) — {ev}×{n}")
        return lines

    parts = []
    if out_rows:
        parts.append("<b>Observed contacts</b> (this user → others, bot-seen):")
        parts.extend(_fmt_side(out_rows, "target")[:limit])
    if in_rows:
        parts.append("<b>Seen by</b> (others → this user, bot-seen):")
        parts.extend(_fmt_side(in_rows, "observer")[:limit])
    if not parts:
        return ""
    return "\n".join(parts)
