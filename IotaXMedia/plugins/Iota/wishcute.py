# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
import random
import asyncio
import requests
from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import styled_button, send_animation_colored, send_document_colored

SUPPORT_CHAT = "https://t.me/+Q493A_VBAUpkMmRl"
SUPPORT_BTN = InlineKeyboardMarkup(
    [[InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_CHAT, style=enums.ButtonStyle.PRIMARY)]]
)
SUPPORT_BTN_COL = [[styled_button("ꜱᴜᴘᴘᴏʀᴛ", url=SUPPORT_CHAT, style="primary")]]

CUTE_VIDEO = "https://telegra.ph/file/528d0563175669e123a75.mp4"


@app.on_message(filters.command("wish"))
async def wish(_, m):
    if len(m.command) < 2:
        return await m.reply_text("❌ ᴀᴅᴅ ʏᴏᴜʀ ᴡɪꜱʜ ʙᴀʙʏ 🥀!")

    try:
        api = (await asyncio.to_thread(requests.get, "https://nekos.best/api/v2/happy")).json()
        url = api["results"][0]["url"]
    except Exception:
        return await m.reply_text("⚠️ Couldn't fetch animation, try again later.")

    text = m.text.split(None, 1)[1]
    wish_count = random.randint(1, 100)
    name = m.from_user.first_name or "User"

    caption = (
        f"✨ ʜᴇʏ {name}!\n"
        f"🪄 ʏᴏᴜʀ ᴡɪꜱʜ: {text}\n"
        f"📊 ᴘᴏꜱꜱɪʙɪʟɪᴛʏ: {wish_count}%"
    )

    try:
        r = await send_animation_colored(m.chat.id, url, caption, SUPPORT_BTN_COL)
        if r:
            return
    except Exception:
        pass
    await app.send_animation(
        chat_id=m.chat.id,
        animation=url,
        caption=caption,
        reply_markup=SUPPORT_BTN,
    )


@app.on_message(filters.command("cute"))
async def cute(_, message):
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    percent = random.randint(1, 100)

    caption = f"🍑 {mention} ɪꜱ {percent}% ᴄᴜᴛᴇ ʙᴀʙʏ 🥀"

    try:
        r = await send_document_colored(
            message.chat.id, CUTE_VIDEO, caption, SUPPORT_BTN_COL, parse_mode="markdown"
        )
        if r:
            return
    except Exception:
        pass
    await app.send_document(
        chat_id=message.chat.id,
        document=CUTE_VIDEO,
        caption=caption,
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=SUPPORT_BTN,
        reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
    )
