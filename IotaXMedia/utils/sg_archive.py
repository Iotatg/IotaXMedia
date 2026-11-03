# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""External username/name history archive helpers.

Internet scan (Aug 2026): No free official Telegram username-history REST API exists.
Working sources:
  1. Local Mongo tracker (bot-seen changes) — FREE
  2. Cached previous SangMata answers — FREE after first hit
  3. SangMata & friends via userbot (quota-limited)
  4. Approx account creation from public user-id ranges
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from IotaXMedia.core.mongo import mongodb

logger = logging.getLogger(__name__)

_cache = mongodb.sg_history_cache



SANGMATA_BOTS = [
    "SangMata_bot",
    "SangMataInfo_bot",
    "sangmata_beta_bot",
    "SangMata_beta_bot",
    "MotherSearcherBot",
    "usinfobot",
    "creationdatebot",
    "NameHistoryBot",
    "UserHistoryBot",
    "SangMata_bot",
]


_SM_TIMEOUT_PER_BOT = 12.0
_POLL_INTERVAL = 1.0


_ID_RANGES = [
    (1_000_000, 2013, 8),
    (10_000_000, 2013, 12),
    (100_000_000, 2014, 5),
    (500_000_000, 2015, 6),
    (1_000_000_000, 2016, 6),
    (1_500_000_000, 2017, 6),
    (2_000_000_000, 2018, 1),
    (2_500_000_000, 2018, 7),
    (3_000_000_000, 2019, 1),
    (3_500_000_000, 2019, 7),
    (4_000_000_000, 2020, 1),
    (4_500_000_000, 2020, 7),
    (5_000_000_000, 2021, 1),
    (5_500_000_000, 2021, 7),
    (6_000_000_000, 2022, 1),
    (6_500_000_000, 2022, 7),
    (7_000_000_000, 2023, 1),
    (7_500_000_000, 2023, 7),
    (8_000_000_000, 2024, 1),
    (8_500_000_000, 2024, 7),
    (9_000_000_000, 2025, 1),
    (9_500_000_000, 2025, 7),
    (10_000_000_000, 2026, 1),
]

_QUOTA_RE = re.compile(
    r"quota|limit|donate|rate.?limit|try again later|used up|too many requests|you have used",
    re.I,
)
_NO_DATA_RE = re.compile(
    r"not found|no records?|no data|no history|empty|couldn't find|doesn't exist|unavailable",
    re.I,
)

_HISTORY_LIKE_RE = re.compile(
    r"(?:names?|usernames?|name.?history|username.?history|👤|history for)",
    re.I,
)
_DATE_LINE_RE = re.compile(r"\[\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}")


def approx_creation_date(user_id: int) -> str:
    if not user_id or user_id < 0:
        return "unknown"
    prev_y, prev_m = 2013, 1
    for thr, y, m in _ID_RANGES:
        if user_id < thr:
            return f"~{prev_y}-{prev_m:02d} → {y}-{m:02d}"
        prev_y, prev_m = y, m
    return f"after {prev_y}"


def _now():
    return datetime.now(timezone.utc)


def _is_quota(text: str) -> bool:
    return bool(_QUOTA_RE.search(text or ""))


def _is_no_data(text: str) -> bool:
    return bool(_NO_DATA_RE.match(text or ""))


def _looks_like_history(text: str) -> bool:
    """Only TRUE if talked about history/data for user."""
    t = (text or "").strip()
    if not t or _is_quota(t) or _is_no_data(t):
        return False

    if _HISTORY_LIKE_RE.search(t):
        return True
    if _DATE_LINE_RE.search(t):
        return True
    if "Name" in t and ("[07" in t or "[0" in t or "[1" in t or "[0" in t):

        return True
    if "Username" in t and ("[07" in t or "[08" in t or "|" in t):
        return True
    return False


async def get_cached(user_id: int, max_age_hours: int = 72) -> Optional[str]:
    doc = await _cache.find_one({"_id": int(user_id)})
    if not doc or not doc.get("text"):
        return None
    text = doc["text"]
    ts = doc.get("updated_at")
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if _now() - ts > timedelta(hours=max_age_hours):
            text = doc["text"]
    return text


async def get_cached_meta(user_id: int) -> dict:
    return await _cache.find_one({"_id": int(user_id)}) or {}


async def save_cache(user_id: int, text: str, source: str = "sangmata") -> None:
    if not text or _is_quota(text):
        return
    if not _looks_like_history(text):
        return
    await _cache.update_one(
        {"_id": int(user_id)},
        {"$set": {"text": text, "source": source, "updated_at": _now()}},
        upsert=True,
    )


async def import_history_into_tracker(user_id: int, text: str) -> None:
    """Parse SangMata-style dump into local tracker.*documents*."""
    if not text or _is_quota(text) or not _looks_like_history(text):
        return
    try:
        from IotaXMedia.utils import user_tracker
    except Exception:
        return

    seen = set()

    for m in re.findall(r"@([A-Za-z0-9_]{4,64})", text):
        ul = m.lower()
        if ul in seen or ul in ("sangmata_bot", "sangmata_beta_bot", "SangSupport"):
            continue
        seen.add(ul)
        try:
            await user_tracker._push_history(user_tracker._user_hist, user_id, "username", ul)
        except Exception:
            pass

    for m in re.finditer(r"(?m)^(\d+\.\s*\[.*?\])\s*\(empty\)", text):
        try:
            await user_tracker._push_history(user_tracker._user_hist, user_id, "username", "")
        except Exception:
            pass


    for m in re.finditer(
        r"(?m)^\s*\d+\.\s*\[(.*?)\]\s*(.+?)(?:\s*•\s*via.*)?$",
        text,
    ):
        name = m.group(2).strip()
        if not name or name in ("(empty)", "empty", ""):
            continue
        try:
            await user_tracker._push_history(user_tracker._name_hist, user_id, "name", name)
        except Exception:
            pass


async def query_sangmata_bots(
    ubot,
    user_id: int,
    *,
    timeout_per_bot: float = None,
    max_bots: int = 5,
) -> tuple[Optional[str], str]:
    """Multi-bot SangMata query (userbot side only). Returns (text, status)."""
    if ubot is None:
        return None, "no_assistant"
    if timeout_per_bot is None:
        timeout_per_bot = _SM_TIMEOUT_PER_BOT

    bots = list(SANGMATA_BOTS)
    random.shuffle(bots)
    bots = bots[:max_bots]

    last_status = "empty"
    for sg_bot_name in bots:
        try:

            pre_id = 0
            try:
                async for m in ubot.get_chat_history(sg_bot_name, limit=1):
                    pre_id = m.id
                    break
            except Exception:
                pre_id = 0

            sent = await ubot.send_message(sg_bot_name, str(user_id))
            head_id = max(getattr(sent, "id", 0), pre_id)
            try:
                await sent.delete()
            except Exception:
                pass


            reply_text = ""
            deadline = asyncio.get_event_loop().time() + timeout_per_bot
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(_POLL_INTERVAL)
                try:
                    async for m in ubot.get_chat_history(sg_bot_name, limit=8):
                        if not m or m.id <= head_id or getattr(m, "outgoing", True):
                            continue
                        body = (m.text or m.caption or "").strip()
                        if not body:
                            continue



                        if _looks_like_history(body):
                            reply_text = body
                            last_status = "ok"
                            break
                        if str(user_id) in body:

                            chk = re.sub(r"\s+", "", body)
                            if chk != str(user_id):
                                reply_text = body
                                last_status = "ok"
                                break
                    if reply_text:
                        break
                except Exception as e:
                    logger.debug(f"poll {sg_bot_name}: {e}")
                    break


            try:
                from pyrogram.raw.functions.messages import DeleteHistory
                peer = await ubot.resolve_peer(sg_bot_name)
                await ubot.send(DeleteHistory(peer=peer, max_id=0, revoke=True))
            except Exception:
                pass

            if last_status == "ok" and reply_text:

                await save_cache(user_id, reply_text, source="live" + sg_bot_name)
                await import_history_into_tracker(user_id, reply_text)
                return reply_text, "ok"

            if last_status == "quota":
                continue
        except Exception as e:
            logger.debug(f"SangMata {sg_bot_name} live: {e}")
            last_status = "error"
            continue

    return None, last_status