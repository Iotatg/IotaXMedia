# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram import enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultPhoto,
)
from IotaXMedia.platforms.ytsearch import VideosSearch
from IotaXMedia.utils.formatters import normalize_duration

from IotaXMedia.utils.inlinequery import answer
from config import BANNED_USERS
from IotaXMedia import app
from IotaXMedia.logging import LOGGER


@app.on_inline_query(~filters.user(list(BANNED_USERS)))
async def inline_query_handler(client, query):
    text = query.query.strip().lower()
    if text.strip() == "":
        try:
            await client.answer_inline_query(query.id, results=answer, cache_time=10)
        except Exception as e:
            LOGGER(__name__).error("inline empty answer failed: %s: %s", type(e).__name__, e)
        return
    try:
        a = VideosSearch(text, limit=20)
        result = (await a.next()).get("result") or []
    except Exception as e:
        LOGGER(__name__).error("inline search failed for %r: %s: %s", text, type(e).__name__, e)
        return
    answers = []
    for x in range(min(15, len(result))):
        try:
            item = result[x] or {}
            title = (item.get("title") or "Unknown").title()
            duration = normalize_duration(item.get("duration"))
            _vc = item.get("viewCount")
            views = _vc.get("short", "Unknown") if isinstance(_vc, dict) else (str(_vc) if _vc else "Unknown")
            thumbs = item.get("thumbnails") or []
            thumbnail = (thumbs[0].get("url") if thumbs else item.get("thumbnail")) or ""
            thumbnail = thumbnail.split("?")[0]
            channel_info = item.get("channel") or {}
            channellink = channel_info.get("link") or "https://youtube.com"
            channel = channel_info.get("name") or "Unknown"
            link = item.get("link") or item.get("url") or ""
            published = item.get("publishedTime") or "Unknown"
            description = f"{views} | {duration} ᴍɪɴᴜϯєs | {channel}  | {published}"
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʏᴏᴜϯυʙє 🎄",
                            url=link,
                        style=enums.ButtonStyle.PRIMARY)
                    ],
                ]
            )
            searched_text = f"""
❄ <b>ᴛɪϯʟє :</b> <a href={link}>{title}</a>

⏳ <b>ᴅυʀαϯɪση :</b> {duration} ᴍɪɴυϯєs
👀 <b>ᴠɪєωs :</b> <code>{views}</code>
🎥 <b>ᴄнαηηєʟ :</b> <a href={channellink}>{channel}</a>
⏰ <b>ᴘυʙʟɪѕнєᴅ ση :</b> {published}


<u><b>➻ ɪηʟɪηє ѕєαʀᴄн ᴍσᴅє ʙγ {app.name}</b></u>"""
            answers.append(
                InlineQueryResultPhoto(
                    photo_url=thumbnail,
                    title=title,
                    thumb_url=thumbnail,
                    description=description,
                    caption=searched_text,
                    reply_markup=buttons,
                )
            )
        except Exception as e:
            LOGGER(__name__).error("inline item %s failed: %s: %s", x, type(e).__name__, e)
            continue
    try:
        return await client.answer_inline_query(query.id, results=answers, cache_time=10)
    except Exception as e:
        LOGGER(__name__).error("inline answer failed: %s: %s", type(e).__name__, e)
        return
