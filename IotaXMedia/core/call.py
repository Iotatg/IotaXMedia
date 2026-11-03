# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import builtins
import os
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import TelegramServerError, ConnectionNotFound
from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall, NoAudioSourceFound, NoVideoSourceFound
from pytgcalls.types import AudioQuality, ChatUpdate, MediaStream, StreamEnded, Update, VideoQuality

import config
from strings import get_string
from IotaXMedia import LOGGER, YouTube, app
from IotaXMedia.misc import db
from IotaXMedia.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    get_volume,
    group_assistant,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
    set_volume,
    VC_START_DIAG,
)
from IotaXMedia.utils.exceptions import AssistantErr
from IotaXMedia.utils.formatters import check_duration, seconds_to_min, speed_converter
from IotaXMedia.utils.inline.play import ended_markup_colored, stream_markup
from IotaXMedia.utils.colored_buttons import smart_edit_reply_markup
from IotaXMedia.utils.stream.autoclear import auto_clean
from IotaXMedia.utils.thumbnails import get_thumb
from IotaXMedia.utils.errors import capture_internal_err

autoend = {}
counter = {}









def set_chat_owner(chat_id, bot_id) -> None:
    d = getattr(builtins, "_IOTAX_CHAT_OWNER", None)
    if d is None:
        d = {}
        builtins._IOTAX_CHAT_OWNER = d
    try:
        d[int(chat_id)] = int(bot_id)
    except (TypeError, ValueError):
        pass


def get_chat_owner(chat_id):
    d = getattr(builtins, "_IOTAX_CHAT_OWNER", None)
    try:
        return d.get(int(chat_id)) if d else None
    except (TypeError, ValueError):
        return None


def resolve_app(chat_id: int):
    """Return the bot client that owns this chat's playback.

    Falls back to the main bot when the chat was never stamped by a clone or
    the owning clone is no longer running.
    """
    bot_id = get_chat_owner(chat_id)
    if not bot_id or bot_id == app.id:
        LOGGER(__name__).warning(
            f"[OWNER-RESOLVE] chat={chat_id} owner={bot_id} -> main(app={app.id})"
        )
        return app
    try:
        from IotaXMedia.clone.runtime import get_clone_manager

        for clone in get_clone_manager()._clones.values():
            capp = getattr(clone, "app", None)
            if capp is not None and getattr(capp, "id", None) == bot_id:
                LOGGER(__name__).warning(
                    f"[OWNER-RESOLVE] chat={chat_id} owner={bot_id} "
                    f"-> clone(app={capp.id}, session={getattr(capp, 'name', '?')})"
                )
                return capp
    except Exception as e:
        LOGGER(__name__).warning(
            f"[OWNER-RESOLVE] chat={chat_id} owner={bot_id} lookup-error={e!r}"
        )
    LOGGER(__name__).warning(
        f"[OWNER-RESOLVE] chat={chat_id} owner={bot_id} no-running-clone -> main"
    )
    return app












def _is_remote(path: str) -> bool:
    p = (path or "").strip().lower()
    return p.startswith("http://") or p.startswith("https://")


def _merge_ffmpeg_params(
    extra: str | None = None,
    *,
    remote: bool = False,
) -> str | None:
    """
    Build PyTgCalls ffmpeg_parameters (placed after -i as output options).
    Only seek/extra flags (e.g. "-ss 30 -to 200") are forwarded; no audio
    filter is added so Telegram's speaking indicator keeps working.
    """
    parts: list[str] = []

    if extra and extra.strip():
        parts.append(extra.strip())

    return " ".join(parts) if parts else None


def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    remote = _is_remote(str(path))
    params = _merge_ffmpeg_params(ffmpeg_params, remote=remote)




    common = dict(
        media_path=path,
        audio_parameters=AudioQuality.HIGH,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE,
    )
    if video:
        common["video_parameters"] = VideoQuality.HD_720p
    try:
        if params:
            if video:
                return MediaStream(
                    media_path=path,
                    audio_parameters=AudioQuality.HIGH,
                    video_parameters=VideoQuality.HD_720p,
                    audio_flags=MediaStream.Flags.REQUIRED,
                    video_flags=MediaStream.Flags.REQUIRED,
                    ffmpeg_parameters=params,
                )
            return MediaStream(
                media_path=path,
                audio_parameters=AudioQuality.HIGH,
                audio_flags=MediaStream.Flags.REQUIRED,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=params,
            )
    except Exception:
        LOGGER(__name__).warning(f"dynamic_media_stream with params failed, retrying bare: {params}")
    return MediaStream(**common)


async def _apply_volume(assistant, chat_id: int) -> None:
    """Re-apply saved volume after every play (PyTgCalls resets otherwise)."""
    try:
        vol = await get_volume(chat_id)
        await assistant.change_volume_call(chat_id, int(vol))
    except Exception:
        pass


async def _ensure_unmuted(assistant, chat_id: int) -> None:
    """Force the assistant to be unmuted in the voice chat.

    A participant that joins muted (group mute policy, or a join-mute that
    PyTgCalls' auto-unmute didn't clear) appears as "listening" and transmits
    NO audio even though the stream is running. Explicitly unmuting the
    assistant guarantees it can speak. Harmless if already unmuted.
    """
    try:
        await assistant.unmute(chat_id)
    except Exception as _e:
        LOGGER(__name__).warning("ensure_unmuted failed: %s", _e)

async def _clear_(chat_id: int) -> None:
    popped = db.pop(chat_id, None)
    if popped:
        await auto_clean(popped)
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)
    await set_loop(chat_id, 0)

class Call:
    def __init__(self):



        self.one = None
        self.two = None
        self.three = None
        self.four = None
        self.five = None
        self.active_calls: set[int] = set()

    def _mtproto(self, assistant) -> Client | None:
        if assistant is None:
            return None
        return getattr(assistant, "mtproto_client", None) or getattr(
            assistant, "_mtproto", None
        )

    async def _ensure_peer(self, assistant, chat_id: int) -> None:
        """Make sure the PyTgCalls pyrogram client can resolve chat_id."""
        client = self._mtproto(assistant)
        if client is None:
            return
        try:
            await client.resolve_peer(chat_id)
            return
        except Exception:
            pass
        try:
            await client.get_chat(chat_id)
            await client.resolve_peer(chat_id)
            return
        except Exception:
            pass
        try:
            chat = await app.get_chat(chat_id)
            uname = getattr(chat, "username", None)
            if uname:
                await client.resolve_peer(uname)
                return
        except Exception as e:
            LOGGER(__name__).warning(f"ensure_peer failed for {chat_id}: {e}")


    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    @capture_internal_err
    async def change_volume(self, chat_id: int, volume: int) -> int:
        """Set VC stream volume (clamped) and persist for this chat."""
        vol = await set_volume(chat_id, volume)
        assistant = await group_assistant(self, chat_id)
        try:
            await assistant.change_volume_call(chat_id, vol)
        except Exception:

            pass
        return vol

    @capture_internal_err
    async def _strip_now_playing_buttons(self, chat_id: int) -> None:
        """Replace control buttons on the now-playing message with
        the single '____' end marker when playback stops."""
        check = db.get(chat_id)
        if not check:
            return
        try:
            entry = check[0] if check else None
            if entry and entry.get("mystic") is not None:
                _msg = entry["mystic"]
                _orig = entry.get("chat_id") or chat_id
                await smart_edit_reply_markup(
                    _orig, _msg.id, ended_markup_colored()
                )
        except Exception:
            pass

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        await self._strip_now_playing_buttons(chat_id)
        assistant = await group_assistant(self, chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)


    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await self._strip_now_playing_buttons(chat_id)
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except (IndexError, KeyError):
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)


    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)
        await _apply_volume(assistant, chat_id)

    @capture_internal_err
    async def play_now(self, chat_id: int, file_path: str, video: Union[bool, str] = False, image=None) -> None:
        """Beta-style direct play on the live call (no leave / rejoin).

        Mirrors iotaxmedia-beta's play_media: when the call is already
        active (e.g. right after a song ended), briefly let PyTgCalls settle,
        then call play() directly to REPLACE the current stream. This is what
        makes autoplay actually start the next track instead of just queuing
        or silently failing at the StreamEnded transition.
        """
        from IotaXMedia.utils.database import is_active_chat as _active



        if await _active(chat_id):
            await asyncio.sleep(0.5)

        assistant = await group_assistant(self, chat_id)
        if assistant is None:
            raise AssistantErr("No assistant available for voice chat.")
        stream = dynamic_media_stream(path=file_path, video=bool(video))
        await assistant.play(chat_id, stream)
        await _apply_volume(assistant, chat_id)
        await _ensure_unmuted(assistant, chat_id)
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        from IotaXMedia.utils.stream.playstats import note_play

        await note_play(chat_id)

    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        assistant = await group_assistant(self, chat_id)
        participants = await assistant.get_participants(chat_id)
        return [p.user_id for p in participants if not p.is_muted]

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)
        await _apply_volume(assistant, chat_id)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await group_assistant(self, chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join("playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))

            cmd = (
                f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" '
                f'-af "atempo={speed},aresample=48000:resampler=soxr,aformat=channel_layouts=stereo" '
                f'-y "{out}"'
            )
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        is_video = playing[0]["streamtype"] == "video"
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=is_video, ffmpeg_params=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            await _apply_volume(assistant, chat_id)
            db[chat_id][0].update({
                "played": con_seconds,
                "dur": duration_min,
                "seconds": dur,
                "speed_path": out,
                "speed": speed,
                "old_dur": db[chat_id][0].get("dur"),
                "old_second": db[chat_id][0].get("seconds"),
            })
        else:
            raise AssistantErr("Stream mismatch during speedup.")


    @capture_internal_err
    async def stream_call(self, link: str) -> None:
        if not config.LOGGER_ID:
            return
        assistant = await group_assistant(self, config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(8)
        finally:
            try:
                await assistant.leave_call(config.LOGGER_ID)
            except:
                pass

    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        assistant = await group_assistant(self, chat_id)
        if assistant is None:
            raise AssistantErr("No assistant available for voice chat.")
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        await self._ensure_peer(assistant, chat_id)

        stream = dynamic_media_stream(path=link, video=bool(video))





        try:
            _last_exc = None
            for _attempt in range(3):
                try:
                    await assistant.play(chat_id, stream)
                    await _apply_volume(assistant, chat_id)
                    break
                except (
                    NoAudioSourceFound,
                    NoActiveGroupCall,
                    ChatAdminRequired,
                    NoVideoSourceFound,
                    ConnectionNotFound,
                    TelegramServerError,
                    AssistantErr,
                ):
                    raise
                except Exception as _e:
                    _last_exc = _e
                    if _attempt < 2:
                        await asyncio.sleep(2)
                        continue
                    raise
            else:
                if _last_exc is not None:
                    raise _last_exc
        except NoAudioSourceFound:

            try:
                if video:
                    bare = MediaStream(
                        media_path=link,
                        audio_parameters=AudioQuality.HIGH,
                        video_parameters=VideoQuality.HD_720p,
                        audio_flags=MediaStream.Flags.REQUIRED,
                        video_flags=MediaStream.Flags.REQUIRED,
                    )
                else:
                    bare = MediaStream(
                        media_path=link,
                        audio_parameters=AudioQuality.HIGH,
                        audio_flags=MediaStream.Flags.REQUIRED,
                        video_flags=MediaStream.Flags.IGNORE,
                    )
                await assistant.play(chat_id, bare)
                await _apply_volume(assistant, chat_id)
            except NoAudioSourceFound:

                try:
                    if "=" in link:
                        vid = link.split("v=")[-1].split("&")[0]
                    else:
                        vid = link.split("/")[-1].split("?")[0]
                    file_path, _dl = await YouTube.download(
                        vid, None, video=bool(video), videoid=str(vid)
                    )
                    if not file_path:
                        raise AssistantErr(_["call_11"])
                    fallback = dynamic_media_stream(path=file_path, video=bool(video))
                    await assistant.play(chat_id, fallback)
                    await _apply_volume(assistant, chat_id)
                except AssistantErr:
                    raise
                except Exception as e:
                    raise AssistantErr(_["call_11"] + f"\nErr: {e}")
            except Exception:
                raise AssistantErr(_["call_11"])
        except (NoActiveGroupCall, ChatAdminRequired):
            raise AssistantErr(_["call_8"])
        except NoVideoSourceFound:
            raise AssistantErr(_["call_12"])
        except (ConnectionNotFound, TelegramServerError):
            raise AssistantErr(_["call_10"])
        except Exception as e:
            raise AssistantErr(
                f"Unable to join the group call.\nReason: {e}"
            )
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        await _ensure_unmuted(assistant, chat_id)
        if video:
            await add_active_video_chat(chat_id)





        if chat_id in autoend:
            autoend.pop(chat_id, None)


    async def _advance_or_leave(self, client, chat_id: int, popped=None) -> None:
        """Queue is empty: try autoplay; only leave if autoplay is off/fails.

        Mirrors iotaxmedia-beta's play_next behaviour — on a natural track end
        with nothing queued it searches for an autoplay track instead of
        dropping the call.
        """
        try:
            from IotaXMedia.utils.stream.autoplay import (
                AUTO_PLAYING as _AP,
                auto_play_next as _auto_play_next,
            )



            if _AP.get(chat_id):
                return
            last_title = popped.get("title", "") if popped else ""
            last_vidid = popped.get("vidid", "") if popped else ""
            original_chat_id = (popped.get("chat_id") if popped else None) or chat_id
            video = bool(popped and str(popped.get("streamtype")) == "video")
            ok = await _auto_play_next(
                chat_id, original_chat_id, last_title, last_vidid, video=video
            )
            if ok:
                LOGGER(__name__).warning("AUTOPLAY[%s]: started next track", chat_id)
                return
            LOGGER(__name__).warning("AUTOPLAY[%s]: no track started → leaving VC", chat_id)
        except Exception as e:
            LOGGER(__name__).warning("Autoplay trigger failed: %s", e)

        await _clear_(chat_id)
        if chat_id in self.active_calls:
            try:
                await client.leave_call(chat_id)
            except NoActiveGroupCall:
                pass
            except Exception:
                pass
            finally:
                self.active_calls.discard(chat_id)

    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        check = db.get(chat_id)


        _bot = resolve_app(chat_id)






        from IotaXMedia.utils.stream.autoplay import AUTO_PLAYING as _AP
        if _AP.get(chat_id):
            return
        popped = None
        loop = await get_loop(chat_id)
        try:




            if not check:
                await self._advance_or_leave(client, chat_id, popped)
                return
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)


            if popped:
                try:
                    if popped.get("mystic") is not None:
                        _msg = popped["mystic"]
                        _orig = popped.get("chat_id") or chat_id
                        await smart_edit_reply_markup(
                            _orig, _msg.id, ended_markup_colored()
                        )
                except Exception:
                    pass
            if not check:
                await self._advance_or_leave(client, chat_id, popped)
                return
        except Exception as e:
            LOGGER(__name__).warning("play() advance error (non-fatal): %s", e)





            try:
                await self._advance_or_leave(client, chat_id, popped)
            except Exception:
                pass
            return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0

            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0

            video = True if str(streamtype) == "video" else False

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await _bot.send_message(original_chat_id, text=_["call_6"])

                stream = dynamic_media_stream(path=link, video=video)
                try:
                    await client.play(chat_id, stream)
                    await _apply_volume(client, chat_id)
                except NoAudioSourceFound:
                    try:
                        file_path, _dl = await YouTube.download(
                            videoid, None, video=video, videoid=videoid
                        )
                        if not file_path:
                            return await _bot.send_message(original_chat_id, text=_["call_6"])
                        stream = dynamic_media_stream(path=file_path, video=video)
                        await client.play(chat_id, stream)
                        await _apply_volume(client, chat_id)
                    except NoAudioSourceFound:
                        return await _bot.send_message(original_chat_id, text=_["call_11"])
                    except (NoActiveGroupCall, ChatAdminRequired):
                        return await _bot.send_message(original_chat_id, text=_["call_12"])
                    except (ConnectionNotFound, TelegramServerError):
                        return await _bot.send_message(original_chat_id, text=_["call_10"])
                    except Exception:
                        return await _bot.send_message(original_chat_id, text=_["call_6"])
                except Exception:
                    return await _bot.send_message(original_chat_id, text=_["call_6"])

                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                run = await _bot.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{_bot.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif "vid_" in queued:
                mystic = await _bot.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], disable_web_page_preview=True
                    )

                stream = dynamic_media_stream(path=file_path, video=video)
                try:
                    await client.play(chat_id, stream)
                    await _apply_volume(client, chat_id)
                except:
                    return await _bot.send_message(original_chat_id, text=_["call_6"])

                img = await get_thumb(videoid)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await _bot.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{_bot.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

            elif "index_" in queued:
                stream = dynamic_media_stream(path=videoid, video=video)
                try:
                    await client.play(chat_id, stream)
                    await _apply_volume(client, chat_id)
                except:
                    return await _bot.send_message(original_chat_id, text=_["call_6"])

                button = stream_markup(_, chat_id)
                run = await _bot.send_photo(
                    chat_id=original_chat_id,
                    photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                stream = dynamic_media_stream(path=queued, video=video)
                try:
                    await client.play(chat_id, stream)
                    await _apply_volume(client, chat_id)
                except:
                    return await _bot.send_message(original_chat_id, text=_["call_6"])

                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    run = await _bot.send_photo(
                        chat_id=original_chat_id,
                        photo=(
                            config.TELEGRAM_AUDIO_URL
                            if str(streamtype) == "audio"
                            else config.TELEGRAM_VIDEO_URL
                        ),
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=button,
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    run = await _bot.send_photo(
                        chat_id=original_chat_id,
                        photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=button,
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                else:
                    img = await get_thumb(videoid)
                    button = stream_markup(_, chat_id)
                    try:
                        run = await _bot.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{_bot.username}?start=info_{videoid}",
                                title[:23],
                                check[0]["dur"],
                                user,
                            ),
                            reply_markup=button,
                        )
                    except FloodWait as e:
                        LOGGER(__name__).warning(f"FloodWait: Sleeping for {e.value}")
                        await asyncio.sleep(e.value)
                        run = await _bot.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(
                                f"https://t.me/{_bot.username}?start=info_{videoid}",
                                title[:23],
                                check[0]["dur"],
                                user,
                            ),
                            reply_markup=button,
                        )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"


    async def start(self) -> None:


        from IotaXMedia import userbot
        from IotaXMedia.core.userbot import assistants

        LOGGER(__name__).info("Starting PyTgCalls Clients...")
        mapping = {
            1: ("one", userbot.one),
            2: ("two", userbot.two),
            3: ("three", userbot.three),
            4: ("four", userbot.four),
            5: ("five", userbot.five),
        }
        VC_START_DIAG["assistants"] = list(assistants)
        VC_START_DIAG["pytgcalls_errors"] = []
        bound = 0
        for idx, (attr, client) in mapping.items():
            if idx not in assistants:
                continue
            try:
                pytg = PyTgCalls(client)
                await pytg.start()
                setattr(self, attr, pytg)
                bound += 1
            except Exception as e:
                VC_START_DIAG["pytgcalls_errors"].append(f"assistant {idx}: {e}")
                LOGGER(__name__).error(f"PyTgCalls assistant {idx} failed: {e}")

        VC_START_DIAG["bound"] = bound
        if not assistants:
            LOGGER(__name__).warning(
                "No assistant userbot started (STRING_SESSION missing/invalid) "
                "— VC playback is disabled until a valid STRING_SESSION is set."
            )
        elif bound == 0:
            LOGGER(__name__).critical(
                "All assistant PyTgCalls bindings failed though userbots started. "
                "VC playback will not work: "
                + " | ".join(VC_START_DIAG["pytgcalls_errors"])
            )
        else:
            LOGGER(__name__).info(f"PyTgCalls bound for {bound} assistant(s).")

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        for client in (self.one, self.two, self.three, self.four, self.five):
            if client is not None:
                try:
                    pings.append(client.ping)
                except Exception:
                    pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        assistants = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))



        CRITICAL = (
            ChatUpdate.Status.KICKED
            | ChatUpdate.Status.LEFT_GROUP
            | ChatUpdate.Status.CLOSED_VOICE_CHAT
        )

        async def unified_update_handler(client, update: Update) -> None:
            try:
                if isinstance(update, StreamEnded):

                    if update.stream_type in (
                        StreamEnded.Type.AUDIO,
                        StreamEnded.Type.VIDEO,
                    ):
                        chat_id = update.chat_id
                        if chat_id not in self.active_calls:
                            return
                        assistant = await group_assistant(self, chat_id)
                        if assistant is None:
                            return




                        await self.play(assistant, chat_id)

                elif isinstance(update, ChatUpdate):
                    status = update.status
                    if status & CRITICAL:
                        await self.stop_stream(update.chat_id)
            except Exception as e:
                LOGGER(__name__).warning(f"update handler: {e}")

        for assistant in assistants:
            assistant.on_update()(unified_update_handler)


StreamController = Call()
