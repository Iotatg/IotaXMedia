# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""``/reel`` and ``/breel`` command handlers.

Single-reel and bulk Instagram downloader commands. The actual media-fetch
logic lives in :mod:`IotaXMedia.plugins.tools.instagram_reel`; this file is
the user-facing surface (filters, error messages, callback wiring).

Commands:
    /reel <url>             — fetch quick info, show 1080p / 4K HD buttons
    /reel 1080p <url>       — direct download at 1080p
    /reel 4k <url>          — direct download at best available quality
    /breel <username>       — bulk 4K download of last N posts
    /breel <username> <N>   — bulk 4K download of last N posts (capped 200)

Error messages (kept short, in the same Unicode-style "small caps" as the
rest of the bot):

    MediaNotFoundError → "» ɴᴏ ᴍᴇᴅɪᴀ ꜰᴏᴜɴᴅ. ᴄʜᴇᴄᴋ ᴛʜᴇ ʟɪɴᴋ ᴏʀ ᴛʜᴇ ᴘᴏsᴛ ᴍᴀʏ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ."
    AuthRequiredError  → "🔒 ᴘʀɪᴠᴀᴛᴇ ᴘᴏsᴛ — ᴄσηғɪɢᴜʀᴇ IG_COOKIES in .env ᴛσ ғᴇᴛᴄʜ."
    NetworkError       → "🌐 ηᴇᴛᴡσʀᴋ ᴇʀʀσʀ — ʀᴇᴛʀʏ ɪη ᴀ ᴍσᴍᴇηᴛ."
    Other Exception    → "» ᴇʀʀσʀ: {e}"  (full traceback logged via LOGGER.error)

Design note: there is no GIF conversion in the /reel / /breel pipeline.
Output media is sent as :func:`reply_video`, :func:`reply_audio`, or
:func:`reply_photo` only. Telegram's GIF-only media type is never used.
"""

from __future__ import annotations

import asyncio
import shutil

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import CallbackQuery, Message

from IotaXMedia import LOGGER, app
from IotaXMedia.utils.colored_buttons import smart_edit_message_text, styled_button
from IotaXMedia.plugins.tools.instagram import ig_profile_entries
from IotaXMedia.plugins.tools.instagram_reel import (
    _AUDIO_EXT,
    _IMG_EXT,
    _VIDEO_EXT,
    AuthRequiredError,
    InstagramReelDownloader,
    MediaNotFoundError,
    NetworkError,
    ReelError,
)





REEL_CACHE: dict = {}


async def _send_media(target, files, caption: str) -> None:
    """Send a list of media files (video / audio / image) as a reply.

    Respects :class:`FloodWait` by sleeping and retrying once. Other
    exceptions are swallowed (logged) so a single bad file does not abort
    the whole batch. Output is dispatched as video, audio, or photo only
    — there is no GIF dispatch in this code path.
    """
    for f in files:
        ext = f.lower()
        try:
            if ext.endswith(_VIDEO_EXT):
                await target.reply_video(f, caption=caption)
            elif ext.endswith(_AUDIO_EXT):
                await target.reply_audio(f, caption=caption)
            else:
                await target.reply_photo(f, caption=caption)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                if ext.endswith(_VIDEO_EXT):
                    await target.reply_video(f, caption=caption)
                elif ext.endswith(_AUDIO_EXT):
                    await target.reply_audio(f, caption=caption)
                else:
                    await target.reply_photo(f, caption=caption)
            except Exception:
                LOGGER.error("reel: retry after FloodWait failed for %s", f)
        except Exception:
            LOGGER.error("reel: send failed for %s", f, exc_info=True)


async def _send_error(status, exc: Exception) -> None:
    """Edit the status message with a user-friendly error description."""
    if isinstance(exc, MediaNotFoundError):
        await status.edit(
            "» ɴᴏ ᴍᴇᴅɪᴀ ꜰᴏᴜɴᴅ.\n"
            "» ᴄʜᴇᴄᴋ ᴛʜᴇ ʟɪɴᴋ ᴏʀ ᴛʜᴇ ᴘᴏsᴛ ᴍᴀʏ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ."
        )
    elif isinstance(exc, AuthRequiredError):
        await status.edit(
            "🔒 ᴘʀɪᴠᴀᴛᴇ ᴘᴏsᴛ — ᴄσηғɪɢᴜʀᴇ IG_COOKIES in .env ᴛσ ғᴇᴛᴄʜ."
        )
    elif isinstance(exc, NetworkError):
        await status.edit(
            "🌐 ηᴇᴛᴡσʀᴋ ᴇʀʀσʀ — ʀᴇᴛʀʏ ɪη ᴀ ᴍσᴍᴇηᴛ."
        )
    else:
        LOGGER.error("reel: unhandled exception", exc_info=exc)
        await status.edit(f"» ᴇʀʀσʀ: {exc}")


async def _reel_do(target, url: str, quality: str) -> None:
    """Download ``url`` at the given quality and send the result.

    Catches every :class:`ReelError` subclass and dispatches to
    :func:`_send_error` for the user-facing message. Cleans up the
    download tmpdir in a ``finally`` block.
    """
    status = await target.reply_text("» ᴅσᴡɴʟσᴀᴅɪηɢ…")
    res = None
    try:
        res = await InstagramReelDownloader.download(url, quality)
        if not res.files:
            return await status.edit("» ɴᴏ ᴍᴇᴅɪᴀ ꜰᴏᴜɴᴅ.")
        title = (
            res.info.get("title")
            or res.info.get("description")
            or "Instagram Media"
        )
        cap = f"📥 {quality.upper()} • {title[:60]}"
        if res.is_video:
            cap += "\n(ɪɴsᴛᴀɢʀᴀᴍ ʀᴇᴇʟs ᴍᴀx 1080p)"
        await _send_media(target, res.files, cap)
        await status.delete()
    except ReelError as e:
        await _send_error(status, e)
    except Exception as e:
        await _send_error(status, e)
    finally:
        if res and res.tmpdir:
            shutil.rmtree(res.tmpdir, ignore_errors=True)


@app.on_message(filters.command("reel"))
async def reel_cmd(client: Client, message: Message):
    """/reel <url> · /reel 1080p <url> · /reel 4k <url>

    Without a quality prefix, fetches quick info and shows two buttons
    (1080p / 4K HD). With a quality prefix, downloads immediately.
    """
    if len(message.command) < 2:
        return await message.reply_text(
            "» ᴜsᴀɢᴇ: `/reel <instagram_url>`\n"
            "» ᴅɪʀᴇᴄᴛ: `/reel 1080p <url>` / `/reel 4k <url>`"
        )
    args = message.command[1:]
    quality_pref = None
    if args[0].lower() in ("1080p", "4k", "best"):
        quality_pref = args[0].lower()
        if len(args) < 2:
            return await message.reply_text(
                "» ᴜsᴀɢᴇ: `/reel 1080p <instagram_url>`"
            )
        url = args[1]
    else:
        url = args[0]
    if "instagram.com" not in url:
        return await message.reply_text("» ɴᴏᴛ ᴀɴ ɪɴsᴛᴀɢʀᴀᴍ ʟɪɴᴋ.")
    if quality_pref:
        return await _reel_do(message, url, quality_pref)
    status = await message.reply_text("» ꜰᴇᴛᴄʜɪɴɢ ʀᴇᴇʟ…")
    try:
        info = await InstagramReelDownloader.quick_info(url)
    except ReelError as e:
        return await _send_error(status, e)
    except Exception as e:
        return await _send_error(status, e)
    if not info:
        return await status.edit(
            "» ɴᴏ ᴍᴇᴅɪᴀ ꜰᴏᴜɴᴅ.\n"
            "» ᴄʜᴇᴄᴋ ᴛʜᴇ ʟɪɴᴋ ᴏʀ ᴛʜᴇ ᴘᴏsᴛ ᴍᴀʏ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ."
        )
    REEL_CACHE[status.id] = url
    kb = [
        [
            styled_button(
                "📺 1080p",
                callback_data=f"reelcb|1080p|{status.id}",
                style="primary",
            ),
            styled_button(
                "🖼 4K HD",
                callback_data=f"reelcb|4k|{status.id}",
                style="success",
            ),
        ]
    ]
    await smart_edit_message_text(
        status.chat.id, status.id, "» ᴄʜᴏᴏsᴇ ǫᴜᴀʟɪᴛʏ:", reply_markup=kb
    )


@app.on_callback_query(filters.regex(r"^reelcb\|"))
async def reel_cb(client: Client, cb: CallbackQuery):
    """Handle 1080p / 4K HD button presses on /reel status messages."""
    try:
        _, quality, mid = cb.data.split("|")
    except ValueError:
        return await cb.answer("Bad request", show_alert=True)
    await cb.answer()
    url = REEL_CACHE.pop(int(mid), None)
    if not url:






        try:
            await cb.message.edit("» sᴇssɪᴏɴ ᴇxᴘɪʀᴇᴅ.")
        except MessageNotModified:
            pass
        return
    await _reel_do(cb.message, url, quality)


@app.on_message(filters.command("breel"))
async def breel_cmd(client: Client, message: Message):
    """/breel <username> [limit] — bulk 4K download of recent posts."""
    if len(message.command) < 2:
        return await message.reply_text(
            "» ᴜsᴀɢᴇ: `/breel <username>`  ·  `/breel <username> <limit>`"
        )
    arg = message.command[1].strip()
    limit = 50
    if len(message.command) >= 3:
        try:
            limit = max(1, min(int(message.command[2]), 200))
        except ValueError:
            pass
    if arg.startswith("http"):
        url = arg
        tag = arg.rsplit("/", 1)[-1] or arg
    else:
        uname = arg.lstrip("@").rstrip("/")
        url = f"https://instagram.com/{uname}/"
        tag = uname
    status = await message.reply_text(f"» ꜰᴇᴛᴄʜɪɴɢ @{tag} ᴘᴏsᴛs…")
    try:
        entries = await ig_profile_entries(url, limit)
    except ReelError as e:
        return await _send_error(status, e)
    except Exception as e:
        LOGGER.error("breel: profile fetch failed", exc_info=e)
        entries = []
    if not entries:
        return await status.edit(
            "» ɴᴏ ᴘᴏsᴛs ꜰᴏᴜɴᴅ (ᴘʀɪᴠᴀᴛᴇ/ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ)."
        )
    total = len(entries)
    await status.edit(f"» ꜰᴏᴜɴᴅ {total} ᴘᴏsᴛs. ᴅᴏᴡɴʟσᴀᴅɪηɢ 4K…")
    ok = 0
    for i, (eurl, etitle) in enumerate(entries, 1):
        res = None
        try:
            res = await InstagramReelDownloader.download(eurl, "4k")
            files = res.files or []
            cap = f"📥 @{tag} • {i}/{total}" + (
                f"\n{etitle[:50]}" if etitle else ""
            )
            await _send_media(message, files, cap)
            if files:
                ok += 1
        except ReelError as e:
            LOGGER.warning("breel: post %d failed: %s", i, e)
        except Exception as e:
            LOGGER.error("breel: post %d exception", i, exc_info=e)
        finally:
            if res and res.tmpdir:
                shutil.rmtree(res.tmpdir, ignore_errors=True)
        if i % 5 == 0:
            try:
                await status.edit(f"» ᴘʀᴏɢʀᴇss: {i}/{total} ᴅᴏɴᴇ")
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
            except Exception:
                pass
    await status.edit(f"» ᴅᴏɴᴇ ✅ {ok}/{total} ᴘᴏsᴛs sᴇɴᴛ (4K).")
