# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Add Manager — owner onboarding + play-log notifications (always on, no command).

Three events notify the bot owner via a DM, all rendered in IotaXMedia's
god-level unicode:

  1. A brand-new user starts the bot for the first time (PM ``/start``).
  2. Someone adds the BOT to a group — owner gets the adder's profile button
     plus a button that opens the group's invite / open link.
  3. A track is played anywhere — owner gets a play log (chat, user, query,
     stream type).

The owner is resolved from (a) ``config.OWNER_ID`` and (b) the per-clone
``config.CLONE_CONFIG.owner_id``; every distinct, non-zero id is notified so
the deployer always learns about new activity even if only one is configured.

Dedup (events 1 & 2) is handled in Mongo (``managerdb``) so the owner is
notified only the first time per user / per group. Event 3 (play log) is sent
on every play. Disabled by setting ``ADD_MANAGER=0``.
"""
from __future__ import annotations

import re
import time

from pyrogram import filters

import config
from IotaXMedia import app
from IotaXMedia.logging import LOGGER
from IotaXMedia.utils.colored_buttons import (
    smart_send_message,
    styled_button,
)
from IotaXMedia.utils.database import (
    manager_add_chat_member,
    manager_add_user,
)
from IotaXMedia.utils.font_styles import Fonts

LOG = LOGGER(__name__)
G = Fonts.god


def owner_ids() -> set:
    """All chat ids that should receive owner notifications.

    On the main bot that is the deployer (``config.OWNER_ID``). On a clone it
    is ONLY the clone's own owner: routing every play on every tenant bot to
    the main deployer's DM is noise/privacy leakage, not a feature.
    """
    ids: set = set()
    cc = getattr(config, "CLONE_CONFIG", None)
    if cc is not None:
        c = int(getattr(cc, "owner_id", 0) or 0)
        if c:
            ids.add(c)
            return ids
    o = int(getattr(config, "OWNER_ID", 0) or 0)
    if o:
        ids.add(o)
    return ids


def _mention(user) -> str:
    try:
        return user.mention
    except Exception:
        return f"<code>{getattr(user, 'id', 0)}</code>"


async def _resolve_link(chat_id: int, user_id: int) -> str:
    if chat_id == 0:
        return f"tg://user?id={user_id}"
    try:
        chat = await app.get_chat(chat_id)
        if getattr(chat, "invite_link", None):
            return chat.invite_link
        if getattr(chat, "username", None):
            return f"https://t.me/{chat.username}"
    except Exception as e:
        LOG.warning(f"[AddManager] could not resolve group link: {e}")
    return f"tg://openmessage?chat_id={chat_id}"


def _enabled() -> bool:
    return bool(getattr(config, "ADD_MANAGER", True))


def _bot_name() -> str:
    """The bot's real Telegram name (first name, else @username)."""
    me = getattr(app, "me", None)
    if me is not None:
        return getattr(me, "first_name", None) or getattr(me, "username", None) or "Bot"
    return "Bot"


async def _notify_start(user) -> None:
    """DM the owner(s) when a brand-new user starts the bot.

    Dedup uses our OWN ``managerdb`` record (``manager_add_user``), NOT
    ``is_served_user`` — the main ``/start`` handler already marks the user as
    served before this runs, so that check would always be True and suppress
    every notification.
    """
    if not _enabled():
        return
    if user is None or user.is_self:
        return
    if not await manager_add_user(user.id):
        return
    owners = owner_ids()
    if not owners:
        LOG.warning(
            "[AddManager] new user %s started but no OWNER_ID/clone owner "
            "configured — cannot notify.",
            user.id,
        )
        return
    LOG.info("[AddManager] new user %s started; notifying owners=%s", user.id, owners)
    name = getattr(user, "first_name", None) or getattr(user, "full_name", "") or ""
    uname = f"@{user.username}" if user.username else "(no username)"
    text = (
        "❖ " + G(f"New user started the {_bot_name()}.") + "\n\n"
        f"✧ {G('Name')} :- {name}\n"
        f"✧ {G('Username')} :- {uname}\n"
        f"✧ {G('Uid')} :- <code>{user.id}</code>\n"
        f"✧ {G('Time')} :- {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    for oid in owners:
        try:
            await smart_send_message(oid, text)
            LOG.info("[AddManager] new-user DM sent to owner %s", oid)
        except Exception as e:
            LOG.error(f"[AddManager] new-user DM to {oid} failed: {e}", exc_info=True)


async def _notify_bot_added(adder, chat) -> None:
    """DM the owner(s) when someone ADDS THE BOT to a group.

    ``adder`` is the user who performed the add (message.from_user). The owner
    receives the adder's details plus two colored URL buttons:
        • User  → opens the adder's Telegram profile (tg://user?id=...)
        • Where → opens the group's invite / open link
    """
    if not _enabled():
        return
    if not await manager_add_chat_member(chat.id, app.id):
        return
    owners = owner_ids()
    if not owners:
        LOG.warning(
            "[AddManager] bot added to group %s but no OWNER_ID/clone owner "
            "configured — cannot notify.",
            chat.id,
        )
        return
    LOG.info(
        "[AddManager] bot added to group %s by %s; notifying owners=%s",
        chat.id,
        getattr(adder, "id", None),
        owners,
    )
    adder_text = "Unknown (added by system)"
    adder_id = 0
    if adder is not None:
        adder_id = adder.id
        uname = f"@{adder.username}" if adder.username else "(no username)"
        adder_text = f"{_mention(adder)}\n✧ {G('Username')} :- {uname}"
    chat_title = getattr(chat, "title", None) or "Unknown group"
    text = (
        "❖ " + G(f"{_bot_name()} added to group") + "\n\n"
        f"✧ {G('Added by')} :- {adder_text}\n"
        f"✧ {G('Group')} :- {chat_title}\n"
        f"✧ {G('Group id')} :- <code>{chat.id}</code>\n"
        f"✧ {G('Time')} :- {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    link = await _resolve_link(chat.id, adder_id)




    user_url = (
        f"https://t.me/{adder.username}"
        if adder.username
        else f"tg://user?id={adder_id}"
    )
    buttons = [[
        styled_button(G("User"), url=user_url, style="primary"),
        styled_button(G("Where"), url=link, style="success"),
    ]]
    for oid in owners:
        try:
            await smart_send_message(oid, text, reply_markup=buttons)
            LOG.info("[AddManager] bot-added DM sent to owner %s", oid)
        except Exception as e:
            LOG.error(f"[AddManager] bot-added DM to {oid} failed: {e}", exc_info=True)


async def notify_play_log(message, streamtype: str, query: str = None) -> None:
    """DM the owner(s) a god-styled play log whenever a track is played.

    Called from ``IotaXMedia.utils.logger.play_logs`` so it covers every play
    path (command, callback, playlist, radio, etc.).
    """
    if not _enabled():
        return
    chat = getattr(message, "chat", None)
    user = getattr(message, "from_user", None)
    if chat is None:
        return
    owners = owner_ids()
    if not owners:
        return
    if query is None:
        try:
            query = message.text.split(None, 1)[1]
        except Exception:
            query = "—"
    name = getattr(user, "first_name", None) or getattr(user, "full_name", "") or "—"
    uname = f"@{user.username}" if (user and user.username) else "None"
    title = getattr(chat, "title", None) or "Private"
    cuname = f"@{chat.username}" if getattr(chat, "username", None) else "None"
    text = (
        G("CloneR Play Log") + " ㋡\n\n"
        f"{G('Chat id')} : <code>{chat.id}</code>\n"
        f"{G('Chat name')} : {G(title)}\n"
        f"{G('Chat username')} : @{cuname}\n\n"
        f"{G('User id')} : <code>{user.id if user else 0}</code>\n"
        f"{G('Name')} : {G(name)}\n"
        f"{G('Username')} : @{uname}\n\n"
        f"{G('Streamtype')} : {G(streamtype)}\n"
        f"{G('Query')} : {G(query)}"
    )
    LOG.info("[AddManager] play log chat=%s user=%s type=%s", chat.id, getattr(user, 'id', None), streamtype)
    uid = user.id if user else 0
    link = await _resolve_link(chat.id, uid)


    user_url = (
        f"https://t.me/{user.username}"
        if (user and user.username)
        else f"tg://user?id={uid}"
    )
    buttons = [[
        styled_button(G("User"), url=user_url, style="primary"),
        styled_button(G("Where"), url=link, style="success"),
    ]]
    for oid in owners:
        try:
            await smart_send_message(oid, text, reply_markup=buttons)
            LOG.info("[AddManager] play-log DM sent to owner %s", oid)
        except Exception as e:
            LOG.error(f"[AddManager] play-log DM to {oid} failed: {e}", exc_info=True)


@app.on_message(
    filters.command(["start"]) & filters.private & ~filters.user(list(config.BANNED_USERS)),
    group=100,
)
async def _addmanager_start(client, message) -> None:

    try:
        await _notify_start(message.from_user)
    except Exception as e:
        LOG.error(f"[AddManager] start notify crashed: {e}", exc_info=True)


@app.on_message(filters.new_chat_members, group=-2)
async def _addmanager_join(client, message) -> None:


    try:
        if not _enabled():
            return
        for member in (message.new_chat_members or []):
            if getattr(member, "is_self", False):
                await _notify_bot_added(message.from_user, message.chat)
    except Exception as e:
        LOG.error(f"[AddManager] join notify crashed: {e}", exc_info=True)

