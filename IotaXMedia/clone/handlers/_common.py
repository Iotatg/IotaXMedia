# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Shared helpers used by the in-child clone handlers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

if TYPE_CHECKING:
    from ..runtime_child import CloneRuntime

















CLONE_HANDLER_GROUP = 100



def owner_only(runtime: "CloneRuntime"):
    """Filter that matches only this clone's owner (from the clone record)."""
    return filters.user([runtime.config.owner_id]) if runtime.config.owner_id else filters.user([])


def sudoers(runtime: "CloneRuntime"):
    return filters.create(
        lambda _, __, m: m.from_user is not None and m.from_user.id == runtime.config.owner_id
    )


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id == 0:
        return False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def is_bot_admin(client: Client, chat_id: int) -> bool:
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False



async def get_clone_db(runtime: "CloneRuntime"):
    """Return the per-clone mongo (own URI if set, else parent shared)."""
    if runtime.mongo is not None:
        return runtime.mongo

    from IotaXMedia.core.mongo import mongodb
    return mongodb



async def extract_user(client: Client, message: Message) -> Optional[Tuple[int, str]]:
    """Returns (user_id, mention) extracted from reply/arg/username."""
    user_id = 0
    mention = ""
    reply = message.reply_to_message
    if message.command and len(message.command) > 1:
        cmd = message.command[1]
        if cmd.isdigit():
            user_id = int(cmd)
        elif cmd.startswith("@"):
            try:
                u = await client.get_users(cmd)
                user_id = u.id
                mention = u.mention
            except Exception:
                user_id = 0
                mention = cmd
    elif reply and reply.from_user:
        user_id = reply.from_user.id
        mention = reply.from_user.mention
    elif reply and reply.sender_chat:
        user_id = reply.sender_chat.id
        mention = reply.sender_chat.title or "channel"
    if user_id and not mention:
        mention = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    return (user_id, mention) if user_id else None
