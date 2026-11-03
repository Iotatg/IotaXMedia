# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import FloodWait, RPCError
from pyrogram.raw import functions, types
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.database import get_assistant
from IotaXMedia.utils.decorator import admin_required


async def _call_peer(assistant, chat_id: int):
    """Resolve the active voice/group call InputGroupCall for a chat."""
    peer = await assistant.resolve_peer(chat_id)
    if hasattr(peer, "channel_id"):
        full = await assistant.invoke(
            functions.channels.GetFullChannel(channel=peer)
        )
    else:
        full = await assistant.invoke(
            functions.messages.GetFullChat(chat_id=peer.chat_id)
        )

    call = getattr(full, "call", None)
    if call is None:
        return None
    return types.InputGroupCall(id=call.id, access_hash=call.access_hash)


async def _member_ids(client, chat_id: int, mode: str):
    member_filter = ChatMembersFilter.ADMINISTRATORS if mode == "admin" else None
    async for member in client.get_chat_members(chat_id, filter=member_filter):
        user = member.user
        if not user or user.is_deleted or user.is_bot:
            continue
        if mode == "admin" and member.status not in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        }:
            continue
        yield user.id


async def _invite_users(assistant, call, user_ids):
    invited = 0
    failed = 0
    batch = []
    for user_id in user_ids:
        try:
            peer = await assistant.resolve_peer(user_id)
            if not hasattr(peer, "user_id") or not hasattr(peer, "access_hash"):
                failed += 1
                continue
            batch.append(
                types.InputUser(user_id=peer.user_id, access_hash=peer.access_hash)
            )
        except Exception:
            failed += 1
        if len(batch) < 20:
            continue
        try:
            await assistant.invoke(
                functions.phone.InviteToGroupCall(call=call, users=batch)
            )
            invited += len(batch)
        except FloodWait as error:
            await __import__("asyncio").sleep(getattr(error, "value", 0) or 0)
            try:
                await assistant.invoke(
                    functions.phone.InviteToGroupCall(call=call, users=batch)
                )
                invited += len(batch)
            except Exception:
                failed += len(batch)
        except RPCError:
            failed += len(batch)
        batch = []
    if batch:
        try:
            await assistant.invoke(
                functions.phone.InviteToGroupCall(call=call, users=batch)
            )
            invited += len(batch)
        except Exception:
            failed += len(batch)
    return invited, failed


@app.on_message(
    filters.command("vcinvite") & filters.group
)
@admin_required("can_manage_video_chats")
async def vcinvite_cmd(client: Client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "Usage: /vcinvite -admin or /vcinvite -all\n"
            "The bot and assistant must have voice-chat management rights."
        )
    mode = message.command[1].lower().lstrip("-")
    if mode not in {"admin", "all"}:
        return await message.reply_text(
            "Usage: /vcinvite -admin or /vcinvite -all\n"
            "The bot and assistant must have voice-chat management rights."
        )
    status = await message.reply_text("Preparing voice-chat invitations...")
    assistant = None
    try:
        assistant = await get_assistant(message.chat.id)
        if assistant is None:
            return await status.edit_text(
                "Assistant (STRING_SESSION) is not configured, so the bot "
                "cannot manage voice chats. Set STRING_SESSION to use /vcinvite."
            )
        call = await _call_peer(assistant, message.chat.id)
        if call is None:
            return await status.edit_text(
                "No active voice chat was found. Start a voice chat first."
            )
        user_ids = [uid async for uid in _member_ids(client, message.chat.id, mode)]
        if not user_ids:
            return await status.edit_text("No members found to invite.")
        invited, failed = await _invite_users(assistant, call, user_ids)
        await status.edit_text(
            f"VC invite completed.\nInvited: {invited}\nFailed or skipped: {failed}"
        )
    except FloodWait as error:
        await status.edit_text(
            f"Telegram rate limit. Try again after {getattr(error, 'value', 0)} seconds."
        )
    except Exception as error:
        import traceback as _tb

        await status.edit_text(
            f"VC invite failed: {error}\n\n{_tb.format_exc()[-1500:]}"
        )
