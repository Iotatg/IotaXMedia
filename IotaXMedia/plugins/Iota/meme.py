# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
import asyncio
import requests
from IotaXMedia import app
from IotaXMedia.utils.permissions import mention
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command("meme"))
async def meme_command(client, message):
    args = message.text.split()
    category = args[1] if len(args) > 1 else ""

    api_url = f"https://meme-api.com/gimme/{category}" if category else "https://meme-api.com/gimme"

    try:
        response = await asyncio.to_thread(requests.get, api_url)
        data = response.json()

        if response.status_code == 403 or "message" in data and "Unable to Access Subreddit" in data["message"]:
            await message.reply_text(f"❌ {god_text('ᴍᴇᴍᴇs ғʀᴏᴍ ᴛʜɪs ᴄᴀᴛᴇɢᴏʀʏ ᴀʀᴇ ɴᴏᴛ ғᴏᴜɴᴅ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀ ᴅɪғғᴇʀᴇɴᴛ ᴏɴᴇ.')}")
            return

        meme_url = data.get("url")
        title = data.get("title")

        bot_info = await app.get_me()

        caption = (
            f"{title}\n\n"
            f"{god_text('ʀᴇQᴜᴇsᴛ ʙʏ')} {mention(message.from_user.id, message.from_user.first_name)}\n"
            f"Bot username: @{bot_info.username}"
        )

        await message.reply_photo(photo=meme_url, caption=caption, parse_mode="markdown")

    except Exception as e:
        print(f"Error fetching meme: {e}")
        msg = god_text("Sorry, I couldn't fetch a meme at the moment.")
        await message.reply_text("❌ " + msg)
