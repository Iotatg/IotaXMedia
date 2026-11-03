# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Telegram user info — only /info.

Passive tracker saves every public profile + peer edge the bot sees to MongoDB.
/info shows clean unicode history card (names, usernames, basic profile).
"""
import asyncio
import logging

from pyrogram import filters, enums
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import BANNED_USERS
from IotaXMedia import app
from IotaXMedia.plugins.Manager.anonymous import ANON_INFO, is_anonymous
from IotaXMedia.utils.colored_buttons import edit_message_text_colored, styled_button
from IotaXMedia.utils import tg_info, user_tracker

logger = logging.getLogger(__name__)




@app.on_message(
    filters.group & ~filters.service & ~filters.user(list(BANNED_USERS)),
    group=-8,
)
async def _track_group_users(_, message: Message):
    try:
        actor = message.from_user
        if actor and not actor.is_bot:
            await user_tracker.track_from_pyrogram_user(
                actor, source=user_tracker.EVENT_GROUP_MSG
            )

        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user
            if not target.is_bot:
                await user_tracker.observe_pair(
                    actor,
                    target,
                    user_tracker.EVENT_REPLY,
                    chat_id=message.chat.id if message.chat else None,
                )

        fwd = getattr(message, "forward_from", None)
        if fwd and not getattr(fwd, "is_bot", False):
            await user_tracker.observe_pair(
                actor,
                fwd,
                user_tracker.EVENT_FORWARD,
                chat_id=message.chat.id if message.chat else None,
            )

        if message.contact and getattr(message.contact, "user_id", None):
            c = message.contact
            await user_tracker.track_user(
                c.user_id,
                getattr(c, "first_name", None),
                getattr(c, "last_name", None),
                phone=getattr(c, "phone_number", None),
                source=user_tracker.EVENT_CONTACT,
            )
            if actor:
                await user_tracker.record_peer(
                    actor.id,
                    c.user_id,
                    user_tracker.EVENT_CONTACT,
                    chat_id=message.chat.id if message.chat else None,
                )

        for ent in message.entities or []:
            if ent.type == enums.MessageEntityType.TEXT_MENTION and ent.user:
                if not ent.user.is_bot:
                    await user_tracker.observe_pair(
                        actor,
                        ent.user,
                        user_tracker.EVENT_MENTION,
                        chat_id=message.chat.id if message.chat else None,
                    )
    except Exception as e:
        logger.debug(f"track group user failed: {e}")


@app.on_message(
    filters.private & ~filters.service & ~filters.user(list(BANNED_USERS)),
    group=-8,
)
async def _track_private_users(_, message: Message):
    try:
        actor = message.from_user
        if actor and not actor.is_bot:
            await user_tracker.track_from_pyrogram_user(
                actor, source=user_tracker.EVENT_PRIVATE
            )
        if message.reply_to_message and message.reply_to_message.from_user:
            t = message.reply_to_message.from_user
            if not t.is_bot:
                await user_tracker.observe_pair(
                    actor, t, user_tracker.EVENT_REPLY, chat_id=message.chat.id
                )
        if message.contact and getattr(message.contact, "user_id", None):
            c = message.contact
            await user_tracker.track_user(
                c.user_id,
                getattr(c, "first_name", None),
                getattr(c, "last_name", None),
                phone=getattr(c, "phone_number", None),
                source=user_tracker.EVENT_CONTACT,
            )
            if actor:
                await user_tracker.record_peer(
                    actor.id, c.user_id, user_tracker.EVENT_CONTACT
                )
    except Exception as e:
        logger.debug(f"track private user failed: {e}")


@app.on_message(filters.new_chat_members, group=-7)
async def _track_new_members(_, message: Message):
    try:
        actor = message.from_user
        for u in message.new_chat_members or []:
            if u and not u.is_bot:
                await user_tracker.track_from_pyrogram_user(
                    u, source=user_tracker.EVENT_JOIN
                )
                if actor and actor.id != u.id:
                    await user_tracker.observe_pair(
                        actor,
                        u,
                        user_tracker.EVENT_JOIN,
                        chat_id=message.chat.id if message.chat else None,
                    )
    except Exception as e:
        logger.debug(f"track new members failed: {e}")




@app.on_message(filters.command("info") & ~filters.user(list(BANNED_USERS)))
async def whois_handler(client, message: Message):
    loading = await message.reply_text("Looking up...")
    try:
        user = await tg_info.resolve_user(client, message)
        if not user:
            arg = (
                message.command[1]
                if message.command and len(message.command) > 1
                else None
            )
            if arg and arg.lstrip("-").isdigit():
                text = await tg_info.build_history_card(int(arg))
                return await loading.edit_text(text, parse_mode=enums.ParseMode.HTML)
            return await loading.edit_text(
                "User not found.\n"
                "Usage: /info | /info @user | /info <id> | reply + /info"
            )



        try:
            if (
                not user.is_bot
                and message.from_user
                and message.from_user.id != user.id
                and await is_anonymous(user.id)
            ):
                return await loading.edit_text(ANON_INFO)
        except Exception:
            pass

        try:
            if message.from_user and message.from_user.id != user.id:
                await user_tracker.observe_pair(
                    message.from_user,
                    user,
                    user_tracker.EVENT_LOOKUP,
                    chat_id=message.chat.id if message.chat else None,
                    meta={"cmd": "info"},
                )
        except Exception:
            pass

        text = await tg_info.build_user_info(client, user, include_history=True)

        profile_url = (
            f"https://t.me/{user.username}"
            if user.username
            else f"tg://user?id={user.id}"
        )
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Profile", url=profile_url, style=enums.ButtonStyle.PRIMARY)]]
        )
        buttons_col = [
            [styled_button("Profile", url=profile_url, style="primary")]
        ]

        try:
            r = await edit_message_text_colored(
                message.chat.id, loading.id, text, buttons_col
            )
            if r:
                return
        except Exception:
            pass

        try:
            await app.edit_message_text(
                chat_id=message.chat.id,
                message_id=loading.id,
                text=text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
        except MessageNotModified:
            return
        except Exception:
            await message.reply_text(
                text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=buttons,
                disable_web_page_preview=True,
            )
            try:
                await loading.delete()
            except Exception:
                pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await whois_handler(client, message)
    except RPCError as e:
        await loading.edit_text(f"RPC error:\n<code>{e}</code>")
    except Exception as e:
        logger.exception("info failed")
        try:
            await loading.edit_text(f"Error:\n<code>{e}</code>")
        except Exception:
            await message.reply_text(f"Error: {e}")
