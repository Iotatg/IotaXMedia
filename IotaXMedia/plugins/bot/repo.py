# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from IotaXMedia import app
from config import REPO_IMG_URL, GITHUB_AVATAR_URL
import config
from IotaXMedia.utils.colored_buttons import styled_button, send_photo_colored

repo_caption = """**
🚀 ᴄʟᴏɴᴇ ᴀɴᴅ ᴅᴇᴘʟᴏʏ – ᴄᴇʀᴛɪꜰɪᴇᴅ ᴄᴏᴅᴇʀꜱ ʀᴇᴘᴏ 🚀

➤ ᴅᴇᴘʟᴏʏ ᴇᴀsɪʟʏ ᴏɴ ʜᴇʀᴏᴋᴜ ᴡɪᴛʜᴏᴜᴛ ᴇʀʀᴏʀꜱ  
➤ ɴᴏ ʜᴇʀᴏᴋᴜ ʙᴀɴ ɪꜱꜱᴜᴇ  
➤ ɴᴏ ɪᴅ ʙᴀɴ ɪꜱꜱᴜᴇ  
➤ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅʏɴᴏꜱ  
➤ ʀᴜɴ 24/7 ʟᴀɢ ꜰʀᴇᴇ

ɪꜰ ʏᴏᴜ ꜰᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ, ꜱᴇɴᴅ ꜱꜱ ɪɴ ꜱᴜᴘᴘᴏʀᴛ
**"""


async def _github_avatar() -> str:
    """Live Iotatg GitHub pfp — always follows current profile avatar."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.github.com/users/Iotatg",
                headers={"Accept": "application/vnd.github+json"},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    avatar = data.get("avatar_url")
                    if avatar:

                        return f"{avatar}&s=512" if "?" in avatar else f"{avatar}?s=512"
    except Exception:
        pass
    return REPO_IMG_URL or GITHUB_AVATAR_URL


@app.on_message(filters.command("repo"))
async def show_repo(_, msg):
    buttons = [
        [styled_button("➕ ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ ✨", url=f"https://t.me/{getattr(config, 'BOT_USERNAME', '')}?startgroup=true", style="success")],
        [
            styled_button("👑 ᴏᴡɴᴇʀ", url="https://t.me/im_ntg", style="primary"),
            styled_button("💬 ꜱᴜᴘᴘᴏʀᴛ", url="https://t.me/+Q493A_VBAUpkMmRl", style="primary")
        ],
        [
            styled_button("🛠️ ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url="https://t.me/Iota", style="primary"),
            styled_button("🎵 ɢɪᴛʜᴜʙ", url="https://github.com/Iotatg/Iota", style="primary")
        ]
    ]

    photo = await _github_avatar()

    try:
        r = await send_photo_colored(
            msg.chat.id,
            photo,
            repo_caption,
            buttons,
        )
        if r:
            return
    except Exception:
        pass

    try:
        await msg.reply_photo(
            photo=photo,
            caption=repo_caption,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(b["text"], url=b["url"], style=enums.ButtonStyle.PRIMARY) for b in row] for row in buttons]
            )
        )
    except Exception:
        try:
            await msg.reply_photo(
                photo=GITHUB_AVATAR_URL,
                caption=repo_caption,
            )
        except Exception:
            pass
