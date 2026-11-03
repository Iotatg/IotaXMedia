# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import os
from random import randint
from typing import Union

from pyrogram.types import InlineKeyboardMarkup

import config
from IotaXMedia import Carbon, YouTube, app
from IotaXMedia.core.call import StreamController
from IotaXMedia.misc import db
from IotaXMedia.plugins.Manager.anonymous import is_anonymous, mask_by
from IotaXMedia.utils.database import add_active_video_chat, is_active_chat
from IotaXMedia.utils.exceptions import AssistantErr
from IotaXMedia.utils.formatters import stream_type_label
from IotaXMedia.utils.inline import aq_markup, aq_markup_colored, close_markup, close_markup_colored, stream_markup, stream_markup_timer, stream_markup_timer_colored
from IotaXMedia.utils.god_style import stream_card
from IotaXMedia.utils.colored_buttons import send_with_colors, edit_message_text_colored, edit_reply_markup_colored, buttons_to_inline_markup, smart_send_photo, smart_send_stream
from IotaXMedia.utils.pastebin import IOTABIN
from IotaXMedia.utils.stream.queue import put_queue, put_queue_index
from IotaXMedia.utils.thumbnails import get_thumb
from IotaXMedia.utils.errors import capture_internal_err


async def _colored_send(chat_id, text=None, photo=None, btns_col=None, btns_fb=None):
    return await send_with_colors(
        chat_id, text=text, photo=photo, btns_col=btns_col, btns_fb=btns_fb
    )


@capture_internal_err
async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
) -> None:
    if not result:
        return

    forceplay = bool(forceplay)
    is_video = bool(video)





    if await is_anonymous(user_id):
        user_name = await mask_by(user_name, user_id)
        user_id = None

    kind = "video" if is_video or str(streamtype).lower() == "video" else "audio"
    display_stype = stream_type_label(kind)

    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        position = 0

        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(
                    search, videoid=search
                )
            except Exception:
                continue

            if str(duration_min) == "None":
                continue
            if duration_sec and duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if is_video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=is_video, videoid=vidid
                    )
                except Exception:
                    raise AssistantErr(_["play_14"])
                if not file_path:
                    raise AssistantErr(_["play_14"])

                await StreamController.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=is_video,
                    image=thumbnail,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if is_video else "audio",
                    forceplay=forceplay,
                )
                img = await get_thumb(vidid, thumbnail)
                button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
                run = await smart_send_stream(
                    original_chat_id,
                    photo=img,
                    caption=stream_card(
                        title[:23],
                        duration_min,
                        user_name,
                        title_url=f"https://t.me/{app.username}?start=info_{vidid}",
                        stream_type=display_stype,
                    ),
                    reply_markup=button_col,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return
        link = await IOTABIN(msg)
        lines = msg.count("\n")
        car = os.linesep.join(msg.split(os.linesep)[:17]) if lines >= 17 else msg
        try:
            carbon = await Carbon.generate(car, randint(100, 10000000))
            playlist_photo = carbon
        except Exception:
            playlist_photo = config.PLAYLIST_IMG_URL
        upl = close_markup(_)
        upl_col = close_markup_colored(_)
        final_position = len(db.get(chat_id) or []) - 1
        if final_position < 0:
            final_position = 0
        return await _colored_send(
            original_chat_id,
            photo=playlist_photo,
            text=_["play_21"].format(final_position, link),
            btns_col=upl_col,
            btns_fb=upl,
        )

    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]

        file_path, direct = None, None
        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, video=is_video, videoid=vidid
            )
        except Exception:
            file_path, direct = None, None


        if not file_path and not is_video:
            try:
                from yt_dlp import YoutubeDL
                from IotaXMedia.utils.downloader import yt_dlp_download
                import asyncio

                def _sc_search(q: str):
                    opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "noplaylist": True,
                        "skip_download": True,
                        "default_search": "scsearch1",
                    }
                    with YoutubeDL(opts) as ydl:
                        return ydl.extract_info(q, download=False)

                loop = asyncio.get_running_loop()
                sc_info = await loop.run_in_executor(None, _sc_search, title)
                entry = None
                if sc_info:
                    if sc_info.get("entries"):
                        entry = next((e for e in sc_info["entries"] if e), None)
                    elif sc_info.get("webpage_url") or sc_info.get("url"):
                        entry = sc_info
                sc_url = None
                if entry:
                    sc_url = entry.get("webpage_url") or entry.get("url")
                    if entry.get("title"):
                        title = str(entry["title"]).title()
                    if entry.get("thumbnail"):
                        thumbnail = entry["thumbnail"]
                    if entry.get("duration"):
                        try:
                            sec = int(entry["duration"])
                            duration_min = f"{sec // 60}:{sec % 60:02d}"
                        except Exception:
                            pass
                if sc_url:
                    sc_path = await yt_dlp_download(sc_url, type="audio", title=title)
                    if sc_path:
                        file_path, direct = sc_path, True
                        vidid = vidid or "soundcloud"
            except Exception:
                pass

        if not file_path:
            from IotaXMedia.utils.downloader import get_last_yt_error
            from config import API_KEY, API_URL, VIDEO_API_URL

            reason = get_last_yt_error()
            if not reason:
                has_api = bool(API_URL and API_KEY) or bool(VIDEO_API_URL and API_KEY)
                reason = (
                    "YouTube blocked this server's IP. Set YTPROXY_URL (a proxy) in "
                    "config, or point API_URL/VIDEO_API_URL at a working YouTube "
                    "download API."
                    if not has_api
                    else "Download failed through both yt-dlp and the configured API. "
                    "Set YTPROXY_URL (a proxy) to bypass YouTube's IP block, or use a "
                    "working API_URL/VIDEO_API_URL."
                )
            raise AssistantErr(
                f"{_['play_14']}\n\n<code>{reason[:350]}</code>"
            )


        queued = file_path if file_path else f"vid_{vidid}"

        active = await is_active_chat(chat_id)
        if active and not forceplay:

            await put_queue(
                chat_id,
                original_chat_id,
                queued,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button_col = aq_markup_colored(_, chat_id)
            button = aq_markup(_, chat_id)
            await _colored_send(original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                btns_col=button_col, btns_fb=button,
            )
        else:






            if forceplay and active:
                await StreamController.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=is_video,
                    image=thumbnail,
                )
                db[chat_id] = []
            else:
                db[chat_id] = []
                await StreamController.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=is_video,
                    image=thumbnail,
                )
            await put_queue(
                chat_id,
                original_chat_id,
                queued,
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid, thumbnail)
            button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
            run = await smart_send_stream(
                original_chat_id,
                photo=img,
                caption=stream_card(
                    title[:23],
                    duration_min,
                    user_name,
                    title_url=f"https://t.me/{app.username}?start=info_{vidid}",
                    requester_id=user_id,
                    stream_type=display_stype,
                ),
                reply_markup=button_col,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        if isinstance(title, bytes):
            title = title.decode("utf-8", "ignore")
        duration_min = result["duration_min"]
        if not file_path:
            raise AssistantErr(_["play_14"])

        active = await is_active_chat(chat_id)
        if active and not forceplay:

            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            button_col = aq_markup_colored(_, chat_id)
            button = aq_markup(_, chat_id)
            await _colored_send(original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                btns_col=button_col, btns_fb=button,
            )
        else:



            if forceplay and active:
                await StreamController.join_call(chat_id, original_chat_id, file_path, video=False)
                db[chat_id] = []
            else:
                db[chat_id] = []
                await StreamController.join_call(chat_id, original_chat_id, file_path, video=False)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
            run = await smart_send_stream(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=stream_card(
                    title[:23],
                    duration_min,
                    user_name,
                    requester_id=user_id,
                    stream_type=display_stype,
                ),
                reply_markup=button_col,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        if not file_path:
            raise AssistantErr(_["play_14"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button_col = aq_markup_colored(_, chat_id)
            button = aq_markup(_, chat_id)
            await _colored_send(original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                btns_col=button_col, btns_fb=button,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(chat_id, original_chat_id, file_path, video=is_video)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            if is_video:
                await add_active_video_chat(chat_id)
            button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
            run = await smart_send_stream(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if is_video else config.TELEGRAM_AUDIO_URL,
                caption=stream_card(title[:23], duration_min, user_name, title_url=link, requester_id=user_id, stream_type=display_stype),
                reply_markup=button_col,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button_col = aq_markup_colored(_, chat_id)
            button = aq_markup(_, chat_id)
            await _colored_send(original_chat_id,
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                btns_col=button_col, btns_fb=button,
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            if not file_path:
                raise AssistantErr(_["play_14"])

            await StreamController.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=is_video,
                image=thumbnail or None,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid, thumbnail)
            button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
            run = await smart_send_stream(
                original_chat_id,
                photo=img,
                caption=stream_card(
                    title[:23],
                    duration_min,
                    user_name,
                    title_url=f"https://t.me/{app.username}?start=info_{vidid}",
                    requester_id=user_id,
                    stream_type=display_stype,
                ),
                reply_markup=button_col,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"

        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if is_video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            button_col = aq_markup_colored(_, chat_id)
            button = aq_markup(_, chat_id)
            try:
                r = await edit_message_text_colored(chat_id, mystic.id, _["queue_4"].format(position, title[:27], duration_min, user_name), button_col)
                if not r:
                    await mystic.edit_text(
                        text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
            except Exception:
                await mystic.edit_text(
                    text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                    reply_markup=InlineKeyboardMarkup(button),
                )
        else:
            if not forceplay:
                db[chat_id] = []
            await StreamController.join_call(
                chat_id,
                original_chat_id,
                link,
                video=is_video,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if is_video else "audio",
                forceplay=forceplay,
            )
            button_col = stream_markup_timer_colored(_, chat_id, "0:00", duration_min, force=True)
            run = await smart_send_stream(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=stream_card(title[:27], duration_min, user_name, requester_id=user_id, stream_type=display_stype),
                reply_markup=button_col,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
