# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import random
import re
from collections import deque

from IotaXMedia import YouTube
from IotaXMedia.core.call import StreamController, resolve_app
from IotaXMedia.core.mongo import mongodb
from IotaXMedia import LOGGER
from IotaXMedia.misc import db
from IotaXMedia.utils.database import get_lang
from IotaXMedia.utils.stream.queue import put_queue
from IotaXMedia.utils.thumbnails import get_thumb
from IotaXMedia.utils.formatters import stream_type_label
from IotaXMedia.utils.god_style import god_text, stream_card
from IotaXMedia.utils.inline import stream_markup_timer_colored
from IotaXMedia.utils.colored_buttons import smart_send_stream
from IotaXMedia.platforms.Youtube import (
    _youtube_api_search,
    _youtube_api_video,
    get_related_suggestions,
)
from strings import get_string

autoplay_db = mongodb.autoplay
AUTO_PLAYING = {}
AUTO = god_text("autoplay") + " 🟢"



AUTO_STATE: dict[int, bool] = {}


async def is_autoplay_on(chat_id: int) -> bool:



    data = await autoplay_db.find_one({"chat_id": chat_id})
    status = True if data is None else bool(data.get("status"))
    AUTO_STATE[chat_id] = status
    return status


async def toggle_autoplay(chat_id: int) -> bool:
    data = await autoplay_db.find_one({"chat_id": chat_id})
    if not data:

        await autoplay_db.insert_one({"chat_id": chat_id, "status": False})
        AUTO_STATE[chat_id] = False
        return False
    new_status = not data.get("status")
    await autoplay_db.update_one(
        {"chat_id": chat_id}, {"$set": {"status": new_status}}
    )
    AUTO_STATE[chat_id] = new_status
    return new_status


async def set_autoplay(chat_id: int, status: bool) -> None:
    await autoplay_db.update_one(
        {"chat_id": chat_id}, {"$set": {"status": bool(status)}}, upsert=True
    )
    AUTO_STATE[chat_id] = bool(status)













_RECENT: dict[int, deque] = {}


def _recent(chat_id: int) -> deque:
    return _RECENT.setdefault(chat_id, deque(maxlen=50))


def note_recent(chat_id: int, vidid, title: str = "") -> None:
    if vidid:
        _recent(chat_id).append(str(vidid))


async def _collect_related_candidates(last_vidid, chat_id, max_pool=12):
    """Build a YTM radio-mix candidate pool, excluding history.

    Returns a list of dicts with at least ``id`` and ``title`` keys. Never
    raises — returns ``[]`` on failure.
    """
    if not last_vidid:
        return []
    seen_ids = {str(last_vidid)} | {str(v) for v in _recent(chat_id)}
    try:
        suggestions = await get_related_suggestions(
            last_vidid, limit=max_pool, exclude_ids=seen_ids
        )
    except Exception:
        return []
    pool = []
    for s in suggestions or []:
        rid = str(s.get("video_id") or "")
        if not rid or rid in seen_ids:
            continue
        seen_ids.add(rid)



        pool.append(
            {
                "id": rid,
                "title": s.get("title") or "sɪᴍɪʟᴀʀ sᴏɴɢ",
            }
        )
        if len(pool) >= max_pool:
            break
    return pool


async def auto_play_next(
    chat_id: int,
    original_chat_id,
    last_title: str,
    last_vidid: str,
    video: bool = False,
) -> bool:
    """Port of iotaxmedia-beta's play_next autoplay branch.

    On a natural track end with nothing queued, search YouTube for songs
    related to the track that just ended, pick one at random, download it and
    start it via the robust join_call path (same as /play forceplay — with
    retry + fallback) so the assistant does NOT leave the VC. Returns True if a
    track was started, else False (caller then clears & leaves).
    """
    if AUTO_PLAYING.get(chat_id):
        LOGGER(__name__).warning("AUTOPLAY[%s]: skipped, already in progress", chat_id)
        return False
    AUTO_PLAYING[chat_id] = True


    _bot = resolve_app(original_chat_id)
    LOGGER(__name__).warning(
        "AUTOPLAY[%s]: routed via bot=%s session=%s",
        chat_id,
        getattr(_bot, "id", "?"),
        getattr(_bot, "name", "?"),
    )
    try:
        if not await is_autoplay_on(chat_id):
            LOGGER(__name__).warning("AUTOPLAY[%s]: disabled (is_autoplay_on=False)", chat_id)
            return False



        note_recent(chat_id, last_vidid, last_title)
        results = await _collect_related_candidates(last_vidid, chat_id)
        if not results:
            try:
                results = [
                    r
                    for r in (
                        _youtube_api_search(
                            "top music videos", max_results=15
                        )
                        or []
                    )
                    if r.get("id")
                    and str(r.get("id")) != str(last_vidid)
                ]
            except Exception:
                results = []
        LOGGER(__name__).warning(
            "AUTOPLAY[%s]: seed=%r diverse_candidates=%d",
            chat_id,
            (last_title or "")[:40],
            len(results),
        )
        if not results:


            LOGGER(__name__).warning("AUTOPLAY[%s]: no results → leaving VC", chat_id)
            try:
                await _bot.send_message(
                    original_chat_id,
                    text=f"{AUTO} ꜰᴀɪʟᴇᴅ ❌\n\nʀᴇʟᴀᴛᴇᴅ sᴏɴɢ ɴᴀʜɪ ᴍɪʟᴀ (YouTube Data API sᴇᴀʀᴄʜ ᴇᴍᴘᴛʏ).",
                )
            except Exception:
                pass
            return False



        random.shuffle(results)
        tried = 0
        for pick in results:
            if tried >= 5:
                break
            tried += 1
            vidid = pick.get("id")
            if not vidid:
                continue
            info = None
            try:
                info = _youtube_api_video(vidid)
            except Exception as e:
                LOGGER(__name__).warning("AUTOPLAY[%s]: api_video exc: %s", chat_id, e)
            info = info or {}
            title = info.get("title") or pick.get("title", "🇮🇳 ꜱɪᴍɪʟᴀʀ sσɴɢ")
            dur = info.get("duration_min") or "00:00"
            LOGGER(__name__).warning("AUTOPLAY[%s]: trying %s (%s)", chat_id, vidid, title)

            file_path, direct = None, None
            for attempt in range(2):
                try:
                    file_path, direct = await YouTube.download(
                        vidid, None, video=video, videoid=vidid
                    )
                except Exception as e:
                    LOGGER(__name__).warning("AUTOPLAY[%s]: download exc (try %d): %s", chat_id, attempt, e)
                    file_path, direct = None, None
                if file_path:
                    break
            if not file_path:
                LOGGER(__name__).warning("AUTOPLAY[%s]: download failed for %s, next", chat_id, vidid)
                continue

            try:
                await StreamController.join_call(
                    chat_id, original_chat_id, file_path, video=video
                )
            except Exception as e:
                LOGGER(__name__).warning("AUTOPLAY[%s]: join_call failed for %s: %s", chat_id, vidid, e)
                continue
            LOGGER(__name__).warning("AUTOPLAY[%s]: join_call OK → playing %s", chat_id, vidid)

            db[chat_id] = []
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                dur,
                AUTO,
                vidid,
                _bot.id,
                "video" if video else "audio",
                forceplay=True,
                owner_app=_bot,
            )
            note_recent(chat_id, vidid, title)

            language = await get_lang(chat_id)
            _ = get_string(language)
            try:
                img = await get_thumb(vidid)
                button_col = stream_markup_timer_colored(_, chat_id, "0:00", dur, force=True)
                run = await smart_send_stream(
                    original_chat_id,
                    photo=img,
                    caption=stream_card(
                        str(title)[:23],
                        dur,
                        AUTO,
                        title_url=f"https://youtube.com/watch?v={vidid}",
                        requester_id=_bot.id,
                        stream_type=stream_type_label("audio"),
                    ),
                    reply_markup=button_col,
                )
                if run is not None:
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
            except Exception:
                pass
            return True


        LOGGER(__name__).warning("AUTOPLAY[%s]: all candidates failed → leaving VC", chat_id)
        try:
            await _bot.send_message(
                original_chat_id,
                text=f"{AUTO} ꜰᴀɪʟᴇᴅ ❌\n\nᴋᴏɪ sᴏɴɢ ᴅᴏᴡɴʟᴏᴀᴅ/ᴘʟᴀʏ ɴᴀʜɪ ʜᴏ ᴘᴀʏᴀ (API/VC ɪs.sᴜᴇ).",
            )
        except Exception:
            pass
        return False
    except Exception:
        return False
    finally:
        AUTO_PLAYING.pop(chat_id, None)
