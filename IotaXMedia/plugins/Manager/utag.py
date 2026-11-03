# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import html
import re
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ParseMode
from pyrogram.errors import UserNotParticipant, FloodWait
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.admin_filters import admin_filter
from IotaXMedia.plugins.Manager.funtag import mention_link, to_html

spam_chats = set()


@app.on_message(filters.command(["utag", "all", "mention"]) & filters.group & admin_filter)
async def tag_all_users(client: Client, message: Message):
    replied = message.reply_to_message
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""

    if not replied and not text:
        return await message.reply(
            "**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ᴛᴀɢ ᴀʟʟ.**",
            parse_mode="markdown",
        )

    spam_chats.add(message.chat.id)
    usernum, usertxt, total_tagged = 0, "", 0

    try:
        members = client.get_chat_members(
            message.chat.id, filter=ChatMembersFilter.RECENT
        )
        async for member in members:
            if message.chat.id not in spam_chats:
                break

            if not member.user or member.user.is_bot:
                continue

            usernum += 1
            total_tagged += 1
            usertxt += f"⊚ {mention_link(member.user)}\n"

            if usernum == 5:
                try:
                    body = f"{to_html(text)}\n{usertxt}\n📢 ᴛᴀɢɢɪɴɢ {total_tagged} ᴜsᴇʀs ᴅᴏɴᴇ..."
                    if replied:
                        await replied.reply_text(body, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                    else:
                        await message.reply_text(body, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"utag send error: {e}")
                    pass

                await asyncio.sleep(3)
                usernum, usertxt = 0, ""

        if usertxt:
            try:
                body = f"{to_html(text)}\n{usertxt}\n📢 ᴛᴀɢɢɪɴɢ {total_tagged} ᴜsᴇʀs ᴅᴏɴᴇ..."
                if replied:
                    await replied.reply_text(body, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                else:
                    await message.reply_text(body, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as e:
                print(f"utag final send error: {e}")
                pass

        await message.reply(
            f"✅ <b>ᴛᴀɢɢɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ. ᴛᴏᴛᴀʟ:</b> <code>{total_tagged}</code> <b>ᴜsᴇʀs.</b>",
            parse_mode=ParseMode.HTML,
        )

    finally:
        spam_chats.discard(message.chat.id)


@app.on_message(filters.command(["cancel", "ustop"]))
async def cancel_spam(client: Client, message: Message):
    chat_id = message.chat.id

    if chat_id not in spam_chats:
        return await message.reply("**ɪ'ᴍ ɴᴏᴛ ᴛᴀɢɢɪɴɢ ᴀɴʏᴏɴᴇ ʀɪɢʜᴛ ɴᴏᴡ.**", parse_mode="markdown")

    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return await message.reply("**ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄᴀɴᴄᴇʟ ᴛᴀɢɢɪɴɢ.**", parse_mode="markdown")
    except UserNotParticipant:
        return await message.reply("**ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ᴘᴀʀᴛɪᴄɪᴘᴀɴᴛ ᴏғ ᴛʜɪs ᴄʜᴀᴛ.**", parse_mode="markdown")
    except Exception:
        return await message.reply("**ᴇʀʀᴏʀ ᴄʜᴇᴄᴋɪɴɢ ᴀᴅᴍɪɴ sᴛᴀᴛᴜs.**", parse_mode="markdown")

    spam_chats.discard(chat_id)
    return await message.reply("**🚫 ᴛᴀɢɢɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.**", parse_mode="markdown")
