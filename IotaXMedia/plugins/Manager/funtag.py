# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import html
import random
import re
from pyrogram import filters
from pyrogram.enums import ChatType, ChatMembersFilter, ParseMode
from pyrogram.errors import FloodWait
from IotaXMedia import app
from IotaXMedia.utils.admin_check import is_admin
from IotaXMedia.plugins.misc.funtag_messages import (
    GN_MESSAGES,
    GM_MESSAGES,
    HI_MESSAGES,
    QUOTES,
    SHAYARI,
)

spam_chats = set()
active_tags = {}



_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def to_html(text: str) -> str:
    """Escape user/text content, then restore **bold** as <b>."""
    return _BOLD_RE.sub(lambda m: f"<b>{m.group(1)}</b>", html.escape(text or ""))


def mention_link(user) -> str:
    """Return a clickable, HTML-safe mention for a ChatMember user."""
    name = getattr(user, "first_name", "") or "User"
    return f'<a href="tg://user?id={user.id}">{html.escape(name)}</a>'

async def mention_members(client, message, message_pool, stop_cmd):
    chat_id = message.chat.id

    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("❗ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs.")

    if not await is_admin(message):
        return await message.reply_text("🚫 ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")

    if chat_id in spam_chats:
        stop_command = active_tags.get(chat_id, "tagstop")
        return await message.reply_text(
            f"⚠️ ᴀ ᴛᴀɢɢɪɴɢ sᴇssɪᴏɴ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ.\n"
            f"➤ ᴜsᴇ /{stop_command} ᴛᴏ sᴛᴏᴘ ɪᴛ."
        )

    spam_chats.add(chat_id)
    active_tags[chat_id] = stop_cmd

    tagged = 0
    try:


        collected = []
        for filt in (ChatMembersFilter.RECENT, ChatMembersFilter.SEARCH):
            try:
                async for member in client.get_chat_members(chat_id, filter=filt):
                    collected.append(member)
                if collected:
                    break
            except Exception as e:
                print(f"get_chat_members filter {filt} failed: {e}")

        for member in collected:
            if chat_id not in spam_chats:
                break
            user = getattr(member, "user", None)
            if user is None or getattr(user, "is_bot", False):
                continue
            try:
                mention = mention_link(user)
                if message_pool:
                    mention = f"{to_html(random.choice(message_pool))} {mention}"
                await client.send_message(
                    chat_id,
                    mention,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
                tagged += 1
                await asyncio.sleep(4)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                print(f"Error tagging user {getattr(user, 'id', None)}: {e}")
                continue
    except Exception as e:
        spam_chats.discard(chat_id)
        active_tags.pop(chat_id, None)
        return await client.send_message(
            chat_id,
            f"⚠️ ᴄᴏᴜʟᴅ ɴᴏᴛ ᴛᴀɢ ᴍᴇᴍʙᴇʀs: `{e}`.\n"
            "➤ ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ 'ᴀᴅᴅ ᴍᴇᴍʙᴇʀs' / 'ʙᴀɴ ᴜsᴇʀs' ᴘᴇʀᴍɪssɪᴏɴ.",
        )
    finally:
        spam_chats.discard(chat_id)
        active_tags.pop(chat_id, None)
        await client.send_message(
            chat_id,
            f"✅ ᴛᴀɢɢɪɴɢ sᴇssɪᴏɴ ᴇɴᴅᴇᴅ.\n➤ ᴛᴏᴛᴀʟ ᴛᴀɢɢᴇᴅ: {tagged}",
        )

@app.on_message(filters.command("gntag", prefixes=["/", "!"]))
async def gntag(client, message):
    await mention_members(client, message, GN_MESSAGES, "gnstop")

@app.on_message(filters.command("gmtag", prefixes=["/", "!"]))
async def gmtag(client, message):
    await mention_members(client, message, GM_MESSAGES, "gmstop")

@app.on_message(filters.command("hitag", prefixes=["/", "!"]))
async def hitag(client, message):
    await mention_members(client, message, HI_MESSAGES, "histop")

@app.on_message(filters.command("lifetag", prefixes=["/", "!"]))
async def lifetag(client, message):
    await mention_members(client, message, QUOTES, "lifestop")

@app.on_message(filters.command("shayari", prefixes=["/", "!"]))
async def shayari_tag(client, message):
    await mention_members(client, message, SHAYARI, "shayarioff")

@app.on_message(filters.command("tagall", prefixes=["/", "!"]))
async def tag_all(client, message):
    custom_text = None
    if len(message.command) > 1:
        custom_text = " ".join(message.command[1:])
    await mention_members(client, message, [custom_text] if custom_text else None, "tagoff")

@app.on_message(filters.command(["gmstop", "gnstop", "histop", "lifestop", "shayarioff", "tagoff", "tagstop"], prefixes=["/", "!"]))
async def stop_tagging(client, message):
    chat_id = message.chat.id

    if not await is_admin(message):
        return await message.reply_text("🚫 ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ sᴛᴏᴘ ᴛᴀɢɢɪɴɢ.")

    if chat_id not in spam_chats:
        return await message.reply_text("⚠️ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀɢɢɪɴɢ sᴇssɪᴏɴ ғᴏᴜɴᴅ.")

    spam_chats.discard(chat_id)
    active_tags.pop(chat_id, None)
    await message.reply_text("✅ ᴍᴇɴᴛɪᴏɴɪɴɢ sᴛᴏᴘᴘᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
