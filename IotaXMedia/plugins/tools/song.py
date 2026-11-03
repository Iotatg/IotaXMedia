# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""YouTube song/video download for private chats."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums

from config import BANNED_USERS, SONG_DOWNLOAD_DURATION, SONG_DOWNLOAD_DURATION_LIMIT
from IotaXMedia import YouTube, app
from IotaXMedia.utils.decorators.language import language, languageCB
from IotaXMedia.utils.downloader import get_cookie_file, get_ytdlp_base_opts, yt_dlp_download, get_final_path_from_info, get_last_yt_error
from IotaXMedia.core.dir import DOWNLOAD_DIR as _DOWN_DIR
from IotaXMedia.utils.colored_buttons import styled_button, send_message_colored, send_photo_colored
from IotaXMedia.utils.errors import capture_callback_err, capture_err
from IotaXMedia.utils.formatters import convert_bytes
from IotaXMedia.logging import LOGGER

_LOGGER = LOGGER(__name__)

import subprocess
import tempfile


async def _get_thumb_file(vidid: str) -> Optional[str]:
    """Download the video's thumbnail to a temp .jpg file. Returns path or None."""
    if not vidid:
        return None
    thumb_url = f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
    try:
        from IotaXMedia.utils.downloader import get_http_session

        session = await get_http_session()
        async with session.get(thumb_url) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
        if not data or len(data) < 256:
            return None
        fd, path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path
    except Exception as e:
        _LOGGER.warning(f"[song-dl] thumbnail download failed: {e}")
        return None


def _embed_audio_cover(src: str, thumb: str) -> Optional[str]:
    """Embed the thumbnail as ID3 cover art into a new MP3 file. Returns the
    new path, or None on any failure (caller keeps the original file)."""
    try:
        dst = f"{src.rsplit('.', 1)[0]}_cover.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-i", src,
            "-i", thumb,
            "-map", "0:a:0", "-map", "1:0",
            "-c:a", "libmp3lame", "-b:a", "320k",
            "-c:v", "mjpeg",
            "-id3v2_version", "3",
            "-metadata:s:v", "title=Album cover",
            "-metadata:s:v", "comment=Cover (front)",
            dst,
        ]
        proc = subprocess.run(cmd, capture_output=True, timeout=180)
        if proc.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1024:
            _LOGGER.info(f"[song-dl] embedded cover -> {dst}")
            return dst
        _LOGGER.warning(f"[song-dl] ffmpeg embed failed rc={proc.returncode}")
    except Exception as e:
        _LOGGER.warning(f"[song-dl] embed cover error: {e}")
    return None

SONG_COMMAND = ["song"]

_DEFAULTS = {
    "song_1": "𐌚συ ᴄαη ᴅσωηℓσαᴅ ᴍυѕɪᴄ/νɪᴅєσ ғʀσᴍ 𐌚συϯυʙє σηℓγ ɪη ρʀɪναϯє ᴄнαϯ. 𐌔ϯαʀϯ ᴍє ɪη 𐌃𐌍.",
    "song_2": "𐌖ѕαɢє:\n\n/song [ᴍυѕɪᴄ ηαᴍє] σʀ [𐌚συϯυʙє ℓɪηκ]",
    "song_3": "𐌌ɪνє ℓɪηκ ᴅєϯєᴄϯєᴅ. 𐌌ɪνє 𐌚συϯυʙє νɪᴅєσѕ ᴄαη'ϯ ʙє ᴅσωηℓσαᴅєᴅ.",
    "song_4": "ϯɪϯℓє: {0}\n\n𐌔єℓєᴄϯ ᴅσωηℓσαᴅ ϯγρє:",
    "song_5": "𐌍σϯ α ναℓɪᴅ 𐌚συϯυʙє ℓɪηκ.",
    "song_6": "Ǥєϯϯɪηɢ ғσʀᴍαϯѕ... ρℓєαѕє ωαɪϯ.",
    "song_7": "𐌅αɪℓєᴅ ϯσ ɢєϯ αναɪℓαʙℓє ғσʀᴍαϯѕ.",
    "song_8": "𐌃σωηℓσαᴅɪηɢ... ρℓєαѕє ωαɪϯ.",
    "song_9": "𐌃σωηℓσαᴅ ғαɪℓєᴅ.\n\n𐌓єαѕση: {0}",
    "song_10": "𐌅αɪℓєᴅ ϯσ υρℓσαᴅ ϯσ ϯєℓєɢʀαᴍ.",
    "song_11": "𐌖ρℓσαᴅɪηɢ...",
    "SG_B_1": "𐌏ρєη ρʀɪναϯє ᴄнαϯ",
    "SG_B_2": "αυᴅɪσ ✧",
    "SG_B_3": "νɪᴅєσ ⌬",
    "SG_B_4": "νɪᴅєσ 4K ⌬",
    "BACK_BUTTON": "๏ ʙαᴄκ ๏",
    "CLOSE_BUTTON": "๏ ᴄℓσѕє ๏",
    "play_1": "𐌔єαʀᴄнɪηɢ...",
    "play_3": "Failed to fetch track details. Try another query.",
    "play_4": "𐌃υʀαϯɪση ℓɪᴍɪϯ єχᴄєєᴅєᴅ ({0} ᴍɪη). ϯʀαᴄκ ɪѕ {1}.",
}


def _t(lang: Any, key: str, *args) -> str:
    try:
        if isinstance(lang, dict) and key in lang and lang[key]:
            text = lang[key]
        else:
            text = _DEFAULTS.get(key, key)
    except Exception:
        text = _DEFAULTS.get(key, key)
    if args:
        try:
            return text.format(*args)
        except Exception:
            return text
    return text


def _song_type_markup(lang, vidid: str, mode: Optional[str] = None) -> InlineKeyboardMarkup:
    video_key = "SG_B_4" if mode == "4k" else "SG_B_3"
    video_data = f"song_dl video4k|{vidid}" if mode == "4k" else f"song_dl video|{vidid}"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_t(lang, "SG_B_2"),
                    callback_data=f"song_dl audio|{vidid}",
                style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(
                    text=_t(lang, video_key),
                    callback_data=video_data,
                style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton(
                    text=_t(lang, "CLOSE_BUTTON"),
                    callback_data="close",
                style=enums.ButtonStyle.DANGER)
            ],
        ]
    )


def _song_type_markup_colored(lang, vidid: str, mode: Optional[str] = None):
    video_key = "SG_B_4" if mode == "4k" else "SG_B_3"
    video_data = f"song_dl video4k|{vidid}" if mode == "4k" else f"song_dl video|{vidid}"
    return [
        [
            styled_button(_t(lang, "SG_B_2"), callback_data=f"song_dl audio|{vidid}", style="success"),
            styled_button(_t(lang, video_key), callback_data=video_data, style="primary"),
        ],
        [
            styled_button(_t(lang, "CLOSE_BUTTON"), callback_data="close", style="danger"),
        ],
    ]


def _download_with_format(link: str, fmt: str) -> Optional[str]:
    """Sync yt-dlp download with explicit format (used for song downloads)."""
    import glob as _glob_mod
    _started = datetime.utcnow()
    retval = None
    try:
        from yt_dlp import YoutubeDL
        from IotaXMedia.core.dir import DOWNLOAD_DIR

        _LOGGER.info(f"[song-dl] → link={link}  fmt={fmt}  DOWNLOAD_DIR={DOWNLOAD_DIR}  cwd={os.getcwd()}")
        opts = get_ytdlp_base_opts()
        opts["format"] = fmt
        opts["outtmpl"] = f"{DOWNLOAD_DIR}/%(id)s.%(ext)s"
        opts["quiet"] = False
        opts["no_warnings"] = False
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True) or {}
            vid = info.get("id")
            ext = info.get("ext")
            filesize = info.get("filesize") or info.get("filesize_approx")
            _LOGGER.info(f"[song-dl] yt-dlp returned vid={vid}  ext={ext}  filesize={filesize}")
            if vid and ext:
                path = f"{DOWNLOAD_DIR}/{vid}.{ext}"
                exists = os.path.exists(path)
                size = os.path.getsize(path) if exists else -1
                _LOGGER.info(f"[song-dl] direct path attempt  path={path}  exists={exists}  size={size}")
                if exists and size > 1024:
                    retval = path
                    _LOGGER.info(f"[song-dl] SUCCESS via direct path: {path}")
                    return path
            if vid:
                for e in ("webm", "m4a", "mp3", "mp4", "mkv", "opus"):
                    path = f"{DOWNLOAD_DIR}/{vid}.{e}"
                    exists = os.path.exists(path)
                    if exists:
                        size = os.path.getsize(path)
                        _LOGGER.info(f"[song-dl] ext scan  ext={e}  path={path}  exists=True  size={size}")
                        if size > 1024:
                            retval = path
                            _LOGGER.info(f"[song-dl] SUCCESS via ext scan {e}")
                            return path
            final = get_final_path_from_info(info)
            _LOGGER.info(f"[song-dl] get_final_path_from_info returned: {final}")
            if final:
                retval = final
                _LOGGER.info(f"[song-dl] SUCCESS via final path")
                return final
            if vid:
                candidates = sorted(
                    _glob_mod.glob(f"{DOWNLOAD_DIR}/{vid}.*"),
                    key=os.path.getmtime, reverse=True,
                )
                _LOGGER.info(f"[song-dl] glob candidates in {DOWNLOAD_DIR}/{vid}.*: {candidates}")
                for p in candidates:
                    try:
                        sz = os.path.getsize(p)
                        _LOGGER.info(f"[song-dl] glob check  {p}  size={sz}  ends_with_part={p.endswith('.part')}")
                        if sz > 1024 and not p.endswith(".part"):
                            retval = p
                            _LOGGER.info(f"[song-dl] SUCCESS via glob")
                            return p
                    except OSError as exc:
                        _LOGGER.info(f"[song-dl] glob OSError on {p}: {exc}")

            _LOGGER.warning(
                f"[song-dl] NO FILE FOUND  vid={vid}  ext={ext}  DOWNLOAD_DIR={DOWNLOAD_DIR}  "
                f"dir_contents={os.listdir(DOWNLOAD_DIR) if os.path.isdir(DOWNLOAD_DIR) else 'NO_DIR'}"
            )
    except Exception as e:
        _LOGGER.error(f"[song-dl] download error: {e}\n{traceback.format_exc()}")
    elapsed = (datetime.utcnow() - _started).total_seconds()
    _LOGGER.info(f"[song-dl] FAILED after {elapsed:.1f}s  fmt={fmt}  result={retval}")
    return None


@app.on_message(
    filters.command(SONG_COMMAND) & filters.group & ~filters.user(list(BANNED_USERS))
)
@capture_err
@language
async def song_command_group(client, message: Message, lang):
    uname = getattr(app, "username", None) or "Iotamusicbot"
    text = _t(lang, "song_1")
    buttons_col = [
        [
            styled_button(
                _t(lang, "SG_B_1"),
                url=f"https://t.me/{uname}?start=song",
                style="primary",
            )
        ]
    ]
    try:
        r = await send_message_colored(message.chat.id, text, buttons_col)
        if r:
            return
    except Exception:
        pass
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=_t(lang, "SG_B_1"),
                        url=f"https://t.me/{uname}?start=song",
                    style=enums.ButtonStyle.PRIMARY)
                ]
            ]
        ),
    )


@app.on_message(
    filters.command(SONG_COMMAND) & filters.private & ~filters.user(list(BANNED_USERS))
)
@capture_err
@language
async def song_command_private(client, message: Message, lang):
    mystic = await message.reply_text(_t(lang, "play_1"))

    url = None
    try:
        url = await YouTube.url(message)
    except Exception:
        url = None




    raw = ""
    if message.text and len(message.command) > 1:
        raw = message.text.split(None, 1)[1].strip()
    is4k = bool(raw) and bool(re.search(r"(?i)(^|\s)4k(\s*$)", raw))

    query = url if url else raw
    if not query:
        return await mystic.edit_text(_t(lang, "song_2"))



    if query and not query.startswith("http"):
        query = re.sub(r"(?i)\s+4k\s*$", "", query).strip() or query

    try:
        title, dur_min, dur_sec, thumb, vidid = await YouTube.details(query)
    except Exception:
        return await mystic.edit_text(_t(lang, "play_3"))

    if not vidid:
        return await mystic.edit_text(_t(lang, "play_3"))


    if not dur_min and not dur_sec:

        pass

    try:
        sec = int(dur_sec or 0)
    except Exception:
        sec = 0
    if sec and sec > int(SONG_DOWNLOAD_DURATION_LIMIT):
        return await mystic.edit_text(
            _t(lang, "play_4", SONG_DOWNLOAD_DURATION // 60, dur_min or sec)
        )

    thumb_url = thumb or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
    caption = _t(lang, "song_4", title or vidid)
    mode = "4k" if is4k else None
    markup = _song_type_markup(lang, vidid, mode)
    markup_col = _song_type_markup_colored(lang, vidid, mode)

    try:
        await mystic.delete()
    except Exception:
        pass

    try:
        r = await send_photo_colored(message.chat.id, thumb_url, caption, markup_col)
        if r:
            return
    except Exception:
        pass

    try:
        await message.reply_photo(
            photo=thumb_url,
            caption=caption,
            reply_markup=markup,
        )
    except Exception:
        await message.reply_text(caption, reply_markup=markup)


@app.on_callback_query(
    filters.regex(r"^song_dl ") & ~filters.user(list(BANNED_USERS))
)
@capture_callback_err
@languageCB
async def song_download_cb(client, cq, lang):
    try:
        await cq.answer("Starting download...")
    except Exception:
        pass

    try:
        payload = cq.data.split(" ", 1)[1]
        stype, vidid = payload.split("|", 1)
    except Exception:
        return await cq.answer("Invalid data", show_alert=True)

    yturl = f"https://www.youtube.com/watch?v={vidid}"
    _LOGGER.info(f"[song-dl-cb] callback stype={stype}  vidid={vidid}  chat={cq.message.chat.id}")
    try:
        await cq.edit_message_caption(caption=_t(lang, "song_8"))
    except Exception:
        try:
            await cq.edit_message_text(_t(lang, "song_8"))
        except Exception:
            pass

    loop = asyncio.get_running_loop()
    file_path = None
    title = vidid
    thumb_path = None
    embedded = None

    try:
        try:
            title = await YouTube.title(yturl) or vidid
        except Exception:
            title = vidid
        title = re.sub(r"\s+", " ", re.sub(r"[^\w\s\-\.\(\)\[\]]+", " ", title)).strip()[
            :180
        ] or vidid



        if stype == "audio":
            dl_type = "audio"
            fmt_chain = (
                "251/140/250/249/bestaudio",
                "251/bestaudio",
                "bestaudio/best",
                "best",
            )
        elif stype == "video4k":
            dl_type = "video"
            fmt_chain = (
                "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best",
                "best[ext=mp4][height<=2160]/best[height<=2160]/best",
                "401/400/399/137/136/22/18/best",
                "best",
            )
        else:
            dl_type = "video"
            fmt_chain = (
                "best[ext=mp4][height<=1080]/best[height<=1080]/best",
                "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best",
                "137/136/22/18/best",
                "best",
            )
        for fmt in fmt_chain:
            _LOGGER.info(f"[song-dl-cb] trying {dl_type} fmt={fmt}")
            file_path = await loop.run_in_executor(
                None, _download_with_format, yturl, fmt
            )
            if file_path:
                _LOGGER.info(f"[song-dl-cb] {dl_type} SUCCESS fmt={fmt} path={file_path}")
                break
        if not file_path:
            _LOGGER.info(f"[song-dl-cb] explicit formats failed, falling back to yt_dlp_download")
            file_path = await yt_dlp_download(yturl, type=dl_type, title=title)

        _LOGGER.info(f"[song-dl-cb] final file_path={file_path}  exists={os.path.exists(file_path) if file_path else 'None'}")
        if not file_path or not os.path.exists(file_path):
            import glob as _glob
            candidates = sorted(
                _glob.glob(f"{_DOWN_DIR}/{vidid}.*"),
                key=os.path.getmtime, reverse=True,
            )
            _LOGGER.info(f"[song-dl-cb] fallback glob in {_DOWN_DIR}/{vidid}.*: {candidates}")
            for cand in candidates:
                try:
                    if os.path.getsize(cand) > 1024 and not cand.endswith(".part"):
                        file_path = cand
                        _LOGGER.info(f"[song-dl-cb] fallback SUCCESS {cand}")
                        break
                except OSError:
                    continue
            if not file_path or not os.path.exists(file_path):
                yt_err = get_last_yt_error()
                msg = "download returned empty path"
                if yt_err:
                    msg += f" — {yt_err}"
                raise RuntimeError(msg)

        chat_id = cq.message.chat.id

        thumb_path = await _get_thumb_file(vidid)
        send_path = file_path
        embedded = None
        if stype == "audio" and thumb_path:
            embedded = await asyncio.to_thread(_embed_audio_cover, file_path, thumb_path)
            if embedded:
                send_path = embedded

        if stype == "audio":
            await app.send_chat_action(chat_id, ChatAction.UPLOAD_AUDIO)
            await app.send_audio(
                chat_id=chat_id,
                audio=send_path,
                title=title,
                caption=title,
                thumb=thumb_path if not embedded else None,
            )
        else:
            await app.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
            await app.send_video(
                chat_id=chat_id,
                video=file_path,
                caption=title,
                thumb=thumb_path,
                supports_streaming=True,
            )

        try:
            await cq.message.delete()
        except Exception:
            pass

    except Exception as e:
        err = str(e)[:200]
        try:
            await cq.edit_message_caption(caption=_t(lang, "song_9", err))
        except Exception:
            try:
                await cq.edit_message_text(_t(lang, "song_9", err))
            except Exception:
                await app.send_message(cq.message.chat.id, _t(lang, "song_9", err))
    finally:
        for p in (file_path, thumb_path, embedded):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
