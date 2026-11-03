# Authored By Iota Coders (Instagram reels/photo downloader)
# SPDX-License-Identifier: MIT
import asyncio
import os
import shutil
import tempfile

import yt_dlp
from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.utils.decorators.language import language

IG_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)


def _build_url(text: str) -> str:
    text = text.strip().strip("@")
    if "instagram.com" in text:
        return text
    return f"https://www.instagram.com/{text}/"


@app.on_message(filters.command(["ig", "insta"]))
@language
async def insta_download(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ig <URL or username>")

    processing_message = await message.reply_text("🔄 Processing...")
    url = _build_url(message.command[1])
    tmpdir = tempfile.mkdtemp(prefix="instadl_")
    opts = {
        "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "http_headers": {"User-Agent": IG_UA},
        "format": "best",
        "noplaylist": False,
        "playlist_items": "1-3",
    }
    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(
            None, lambda: _ydl_extract(url, tmpdir, opts)
        )
        files = sorted(
            os.path.join(tmpdir, f) for f in os.listdir(tmpdir)
        )
        if not files:
            return await processing_message.edit(
                "⚠️ No media found. Please check the input."
            )
        await processing_message.delete()
        for file_path in files:
            duration = (info or {}).get("duration")
            plays = (info or {}).get("view_count")
            caption_parts = []
            if duration:
                caption_parts.append(f"𝐃ᴜʀᴀᴛɪᴏɴ : {duration}s")
            if plays:
                caption_parts.append(f"𝐏ʟᴀʏs : {plays}")
            caption = "\n".join(caption_parts) if caption_parts else None
            if file_path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
                if caption:
                    await message.reply_video(file_path, caption=caption)
                else:
                    await message.reply_video(file_path)
            elif file_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                if caption:
                    await message.reply_photo(file_path, caption=caption)
                else:
                    await message.reply_photo(file_path)
            else:
                if caption:
                    await message.reply_document(file_path, caption=caption)
                else:
                    await message.reply_document(file_path)
    except Exception as e:
        await processing_message.edit(f"❌ Error: {e}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _ydl_extract(url: str, tmpdir: str, opts: dict) -> dict:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info or {}