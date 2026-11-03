# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import platform
from sys import version as pyver

import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaVideo, Message
from pytgcalls.__version__ import __version__ as pytgver

import config
from IotaXMedia import app
from IotaXMedia.core.userbot import assistants
from IotaXMedia.misc import SUDOERS, mongodb
from IotaXMedia.plugins import ALL_MODULES
from IotaXMedia.utils.database import get_served_chats, get_served_users, get_sudoers
from IotaXMedia.utils.decorators.language import language, languageCB
from IotaXMedia.utils.inline.stats import (
    build_stats_keyboard,
    build_stats_keyboard_colored,
    build_back_keyboard,
    build_back_keyboard_colored,
    StatsCallbacks,
)
from IotaXMedia.utils.colored_buttons import send_video_colored, edit_message_media_colored, edit_message_text_colored
from config import BANNED_USERS


async def _edit_media_or_reply_with_video(cbq, caption: str, reply_markup, reply_markup_col=None):
    media = InputMediaVideo(media=config.STATS_VID_URL, caption=caption)
    if reply_markup_col:
        try:
            r = await edit_message_media_colored(
                cbq.message.chat.id,
                cbq.message.id,
                {"type": "video", "media": config.STATS_VID_URL, "caption": caption, "parse_mode": "HTML"},
                reply_markup_col,
            )
            if r:
                return
        except Exception:
            pass
    try:
        await cbq.edit_message_media(media=media, reply_markup=reply_markup)
    except MessageIdInvalid:
        await cbq.message.reply_video(
            video=config.STATS_VID_URL, caption=caption, reply_markup=reply_markup
        )


@app.on_message(filters.command(["stats", "gstats"]) & ~filters.user(list(BANNED_USERS)))
@language
async def open_stats(client, message: Message, _):
    is_sudo = message.from_user and (message.from_user.id in SUDOERS)
    keyboard = build_stats_keyboard(_, is_sudo)
    keyboard_col = build_stats_keyboard_colored(_, is_sudo)
    caption = _["gstats_2"].format(app.mention)



    cc = getattr(config, "CLONE_CONFIG", None)
    if cc is not None:
        from IotaXMedia.clone import customization as cust

        clone_id = getattr(cc, "token", None) or config.BOT_TOKEN
        stats_media = await cust.get_stats_media(clone_id) or getattr(cc, "stats_media", None)
        media_type, mid = cust.parse_media(stats_media)
        if mid:
            try:
                if media_type == "video":
                    return await message.reply_video(
                        video=mid, caption=caption, reply_markup=keyboard
                    )
                if media_type == "animation":
                    return await message.reply_animation(
                        animation=mid, caption=caption, reply_markup=keyboard
                    )
                if media_type == "document":
                    return await message.reply_document(
                        document=mid, caption=caption, reply_markup=keyboard
                    )
                return await message.reply_photo(
                    photo=mid, caption=caption, reply_markup=keyboard
                )
            except Exception:
                pass
    try:
        r = await send_video_colored(message.chat.id, config.STATS_VID_URL, caption, keyboard_col)
        if r:
            return
    except Exception:
        pass
    await message.reply_video(
        video=config.STATS_VID_URL,
        caption=caption,
        reply_markup=keyboard,
    )


@app.on_callback_query(filters.regex(f"^{StatsCallbacks.BACK}$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def handle_back_to_stats(client, callback_query, _):
    is_sudo = callback_query.from_user and (callback_query.from_user.id in SUDOERS)
    keyboard = build_stats_keyboard(_, is_sudo)
    keyboard_col = build_stats_keyboard_colored(_, is_sudo)
    text = _["gstats_2"].format(app.mention)
    try:
        r = await edit_message_text_colored(
            callback_query.message.chat.id, callback_query.message.id, text, keyboard_col
        )
        if r:
            return
    except Exception:
        pass
    await callback_query.edit_message_text(text=text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(f"^{StatsCallbacks.SHOW_OVERVIEW}$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def handle_show_overview(client, callback_query, _):
    await callback_query.answer()
    back_keyboard = build_back_keyboard(_)
    back_keyboard_col = build_back_keyboard_colored(_)
    await callback_query.edit_message_text(_["gstats_1"].format(app.mention))
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    caption = _["gstats_3"].format(
        app.mention,
        len(assistants),
        len(BANNED_USERS),
        served_chats,
        served_users,
        len(ALL_MODULES),
        len(SUDOERS),
        config.AUTO_LEAVING_ASSISTANT,
        config.DURATION_LIMIT_MIN,
    )
    try:
        from IotaXMedia.utils.stream.playstats import leaderboard_block

        caption += await leaderboard_block(client, limit=10)
    except Exception:
        pass
    await _edit_media_or_reply_with_video(callback_query, caption, back_keyboard, back_keyboard_col)


@app.on_callback_query(filters.regex(f"^{StatsCallbacks.SHOW_BOT_STATS}$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def handle_show_bot_stats(client, callback_query, _):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer(_["gstats_4"], show_alert=True)
    back_keyboard = build_back_keyboard(_)
    back_keyboard_col = build_back_keyboard_colored(_)
    try:
        await callback_query.answer()
    except Exception:
        pass
    await callback_query.edit_message_text(_["gstats_1"].format(app.mention))
    physical_cores = psutil.cpu_count(logical=False)
    total_cores = psutil.cpu_count(logical=True)
    ram_total_gb = f"{round(psutil.virtual_memory().total / (1024.0 ** 3))} ɢʙ"
    try:
        freq_current = psutil.cpu_freq().current
        if freq_current >= 1000:
            cpu_freq = f"{round(freq_current / 1000, 2)}ɢʜᴢ"
        else:
            cpu_freq = f"{round(freq_current, 2)}ᴍʜᴢ"
    except Exception:
        cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
    disk = psutil.disk_usage("/")
    disk_total = str(disk.total / (1024.0 ** 3))[:4]
    disk_used = str(disk.used / (1024.0 ** 3))[:4]
    disk_free = str(disk.free / (1024.0 ** 3))[:4]
    db_stats = await mongodb.command("dbstats")
    data_size_kb = str(db_stats["dataSize"] / 1024)[:6]
    storage_kb = db_stats["storageSize"] / 1024
    collections = db_stats["collections"]
    objects = db_stats["objects"]
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    caption = _["gstats_5"].format(
        app.mention,
        len(ALL_MODULES),
        platform.system(),
        ram_total_gb,
        physical_cores,
        total_cores,
        cpu_freq,
        pyver.split()[0],
        pyrover,
        pytgver,
        disk_total,
        disk_used,
        disk_free,
        served_chats,
        served_users,
        len(BANNED_USERS),
        len(await get_sudoers()),
        data_size_kb,
        storage_kb,
        collections,
        objects,
    )
    await _edit_media_or_reply_with_video(callback_query, caption, back_keyboard, back_keyboard_col)
