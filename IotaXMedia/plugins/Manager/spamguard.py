# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Broadcast catcher — catches advert/greeting bot floods that talk handlers
only feed. One message broadcast from a single sender lands byte-identical
(under every font and case trick) in every invaded group; that repetition is
the one thing a broadcast cannot escape. The fingerprint needs no membership
tricks: it fires on whatever this bot can see — bots' posts that arrive via
channel identity, via-bot inline pushes, forwards, and human copy-paste
broadcasts.
"""
import asyncio
import hashlib
import logging
import re
import time
import unicodedata
from collections import defaultdict

from pyrogram import enums, filters
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import ChatPermissions, Message

from IotaXMedia import app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia.utils.cache import TTLCache

logger = logging.getLogger(__name__)

_sg_state = mongodb.sg_state
_enabled_cache = TTLCache(maxsize=2048, ttl=30)
_seen = defaultdict(dict)
_journal = defaultdict(list)
_rate = defaultdict(list)
_repeat = defaultdict(list)
_SEEN_WINDOW = 6 * 3600
_MIN_BODY = 48
_guard_cd = {}
_repair_cd = {}

_PROMO_HINT = re.compile(r"t\.me/|https?://|@|join|free|add .{0,20}to your group", re.I)


def _fold(body):
    """Font-proof, case-proof, spacing-proof fingerprint base. Repeated
    letters collapse, so greeting-farm variants ("Hi", "hiiiii", "ʜɪ") all
    digest the same."""
    body = unicodedata.normalize("NFKC", body).casefold()
    body = re.sub(r"[^a-z0-9]", "", body)
    return re.sub(r"(.)\1+", r"\1", body)


def _digest_of(sender_id, body):
    return hashlib.sha1(f"{sender_id}:{_fold(body)}".encode()).hexdigest()


def _others(cid, digest, message_id=0):
    """How many OTHER chats this sender pushed this exact copy into recently.
    Registers the sighting as a side effect. Greeting-farm bots broadcast
    "hi"/"join" everywhere, so short copy is fingerprinted too — callers set
    per-sender thresholds instead of ignoring short messages. Every sighting
    also lands in the message journal so a fired rule can purge all copies,
    including the first message of the broadcast that sailed through before
    the pattern was known."""
    if not digest:
        return 0
    stamp = time.time()
    chats = {c: when for c, when in _seen[digest].items() if stamp - when < _SEEN_WINDOW}
    if len(_seen) > 4000:
        for old in [k for k, v in _seen.items() if not v or max(v.values()) < stamp - _SEEN_WINDOW]:
            _seen.pop(old, None)
        for old in [k for k, v in _journal.items() if not v or v[-1][2] < stamp - _SEEN_WINDOW]:
            _journal.pop(old, None)
    entries = [e for e in _journal[digest] if stamp - e[2] < _SEEN_WINDOW]
    entries.append((cid, message_id, stamp))
    _journal[digest] = entries[-30:]
    others = len([c for c in chats if c != cid])
    chats[cid] = stamp
    _seen[digest] = chats
    return others


async def _purge(client, digest, keep):
    """Delete every remembered copy of a broadcast, chat by chat, with the
    watching identity first and the bot client as fallback. Best effort."""
    if not digest:
        return 0
    gone = 0
    for cid, mid, _ts in list(_journal.get(digest, ())):
        if (cid, mid) == keep:
            continue
        if await _try_delete(client.delete_messages, cid, mid) \
                or await _try_delete(app.delete_messages, cid, mid):
            gone += 1
    return gone


async def _try_delete(deleter, cid, mid):
    """One delete with a single flood-wait mercy; False means no rights."""
    for attempt in (0, 1):
        try:
            await deleter(cid, mid)
            return True
        except FloodWait as fw:
            if attempt:
                return False
            await asyncio.sleep(min(int(getattr(fw, "value", 5) or 5), 5))
        except RPCError:
            return False
    return False


async def _enabled(cid):
    cached = _enabled_cache.get(str(cid))
    if cached is not None:
        return cached
    row = await _sg_state.find_one({"_id": cid})
    state = (row or {}).get("state", "on") == "on"
    _enabled_cache.set(str(cid), state)
    return state


def _sender_of(message):
    """Real sender even when the post wears a linked-channel identity."""
    user = message.from_user
    if user is not None:
        return user.id, getattr(user, "is_bot", False), f"[{user.first_name}]"
    chat = getattr(message, "sender_chat", None)
    if chat is not None:
        return chat.id, chat.type == ChatType.BOT, f"[{getattr(chat, 'title', None) or 'Channel'}]"
    return None, False, None


async def _drop(client, message, why):
    """Delete with whichever identity has the right.

    Assistant user sessions see every other bot's post but sit in groups as
    plain members; the group's own bot is almost always an admin, and the
    delete API works through it even though it never saw the message."""
    cid = message.chat.id
    ok = await _try_delete(client.delete_messages, cid, message.id) or \
        await _try_delete(app.delete_messages, cid, message.id)
    if not ok:


        now_ts = time.time()
        if now_ts - _repair_cd.get(cid, 0) > 600:
            _repair_cd[cid] = now_ts
            me = await client.get_me()
            repaired = False
            try:
                await app.set_chat_permissions(
                    cid, ChatPermissions(can_delete_messages=True), user_id=me.id)
                repaired = True
            except RPCError:
                pass
            if repaired:
                ok = await _try_delete(client.delete_messages, cid, message.id)
                if not ok:
                    repaired = False
            if not repaired:
                try:
                    await message.reply_text(
                        "⚠️ Advert pakda gaya par message delete nahi ho paya — "
                        "assistant ko **can delete messages** dein (admin rights).",
                        parse_mode="markdown",
                    )
                except RPCError:
                    pass
    if not ok:
        logger.warning("spamguard: neither the assistant nor the bot could delete "
                       "chat=%s mid=%s — add the group bot as admin with delete rights",
                       cid, message.id)
        return
    now_ts = time.time()
    if now_ts - _guard_cd.get(message.chat.id, 0) > 120:
        _guard_cd[message.chat.id] = now_ts
        try:
            await message.reply_text(f"🛰️ **Broadcast blocked** — {why}.", parse_mode="markdown")
        except RPCError:
            pass


async def spamguard_watch(client, message):
    """Shared by the bot client and every assistant user session.

    The bot client never receives other bots' group posts; the assistants
    receive everything, so binding this watch to them is what actually makes
    bot floods deletable. Messages a human sends arrive once per identity —
    thresholds absorb that duplication."""
    if getattr(message, "command", None):
        return
    me = getattr(client, "cached_me", None)
    if me is None:
        me = await client.get_me()
        client.cached_me = me
    if message.from_user is not None and message.from_user.id == me.id:
        return
    if message.via_bot is not None and message.via_bot.id == me.id:
        return
    if not await _enabled(message.chat.id):
        return
    body = message.text or message.caption or ""
    sender_id, is_bot, who = _sender_of(message)
    if sender_id is None:
        return
    key = (message.chat.id, sender_id)
    now_ts = time.time()
    digest = _fold(body) if body.strip() else ""
    digest_key = _digest_of(sender_id, body) if digest else None
    keep = (message.chat.id, message.id)


    stamps = [t for t in _rate[key] if now_ts - t < 10]
    stamps.append(now_ts)
    _rate[key] = stamps
    if len(_rate) > 4096:
        _rate.clear()
    if len(stamps) >= (3 if is_bot else 6):
        gone = await _purge(client, digest_key, keep)
        why = f"{'bot' if is_bot else 'message'} flood"
        await _drop(client, message, why + (f"; {gone} copies purged" if gone else ""))
        return


    if digest:
        reps = [(t, d) for t, d in _repeat[key] if now_ts - t < 180]
        hits = sum(1 for _t, d in reps if d == digest) + 1
        reps.append((now_ts, digest))
        _repeat[key] = reps
        if len(_repeat) > 4096:
            _repeat.clear()
        if hits >= (2 if is_bot else 3) and (is_bot or _PROMO_HINT.search(body)):
            gone = await _purge(client, digest_key, keep)
            why = f"repeated copy {hits}x in this chat"
            await _drop(client, message, why + (f"; {gone} copies purged" if gone else ""))
            return

    others = _others(message.chat.id, digest_key, message.id)
    if others <= 0:
        return
    forwarded = getattr(message, "forward_origin", None) is not None or getattr(message, "forward_from", None) is not None
    hint = bool(_PROMO_HINT.search(body)) or forwarded
    if is_bot and (others >= 2 or (others >= 1 and hint)):


        gone = await _purge(client, digest_key, keep)
        why = f"bot broadcast in {others + 1} chats {who}"
        await _drop(client, message, why + (f"; {gone} earlier copies purged" if gone else ""))
    elif forwarded and others >= 1 and len(body) >= _MIN_BODY:
        gone = await _purge(client, digest_key, keep)
        why = f"same forwarded broadcast in {others + 1} chats"
        await _drop(client, message, why + (f"; {gone} earlier copies purged" if gone else ""))
    elif not is_bot and len(body) >= _MIN_BODY and others >= 2 and hint:
        gone = await _purge(client, digest_key, keep)
        why = f"manual broadcast in {others + 1} chats"
        await _drop(client, message, why + (f"; {gone} earlier copies purged" if gone else ""))


def _bind_assistants():
    """Register the watch on every assistant user session (bound inside
    core.userbot once each client has started and has a dispatcher)."""
    from IotaXMedia.core.userbot import ASSISTANT_WATCHES
    ASSISTANT_WATCHES.append((spamguard_watch, -7))


@app.on_message(filters.group & filters.incoming & ~filters.service, group=-8)
async def spamguard_plugin(client, message: Message):
    await spamguard_watch(client, message)


@app.on_message(filters.command("spamguard") & filters.group)
async def spamguard_toggle(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
        return
    arg = message.text.split(maxsplit=1)[1].lower() if len(message.text.split()) > 1 else ""
    if arg in ("on", "off"):
        await _sg_state.update_one({"_id": message.chat.id}, {"$set": {"state": arg}}, upsert=True)
        _enabled_cache.set(str(message.chat.id), arg == "on")
        await message.reply_text(f"🛰️ Spamguard **{arg}**.", parse_mode="markdown")
        return
    row = await _sg_state.find_one({"_id": message.chat.id})
    state = (row or {}).get("state", "on")
    await message.reply_text(
        f"🛰️ Spamguard is **{state}** — catches cross-chat broadcast floods "
        f"(bots, forwards, copy-paste) automatically.\n/spamguard on | /spamguard off",
        parse_mode="markdown",
    )


_bind_assistants()
