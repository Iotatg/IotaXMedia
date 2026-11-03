# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import os
import random
import time
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import Message
from IotaXMedia.platforms.ytsearch import VideosSearch

import config
from IotaXMedia import app
from IotaXMedia.clone.links import clone_support_link
from IotaXMedia.misc import _boot_
from IotaXMedia.plugins.sudo.sudoers import sudoers_list
from IotaXMedia.utils import bot_sys_stats
from IotaXMedia.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    get_served_chats,
    get_served_users,
    is_banned_user,
    is_on_off,
)
from IotaXMedia.utils.decorators.language import LanguageStart
from IotaXMedia.utils.formatters import get_readable_time
from IotaXMedia.utils.inline.start import private_panel, start_panel
from IotaXMedia.utils.inline.help import first_page
from IotaXMedia.utils.colored_buttons import (
    buttons_to_inline_markup,
    smart_send_message,
    smart_send_photo,
    styled_button,
)
from config import BANNED_USERS, AYUV, START_IMG_URL, HELP_IMG_URL, STREAM_IMG_URL, STICKERS
from strings import get_string


async def delete_sticker_after_delay(message: Message, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def _clone_start_override():
    """Return the effective /start customization for the current bot.

    Reads from Mongo (the source of truth) so a /setstart done on the clone
    bot is always reflected, even if the in-process clone's in-memory
    ``config.CLONE_CONFIG`` mirror is stale. Falls back to the in-memory
    mirror when Mongo has nothing.
    """
    cc = getattr(config, "CLONE_CONFIG", None)
    if cc is None:
        return None
    clone_id = getattr(cc, "token", None) or config.BOT_TOKEN
    from IotaXMedia.clone import customization as cust

    raw_media = await cust.get_start_media(clone_id)
    message_text = await cust.get_start_message(clone_id)
    if raw_media is None:
        raw_media = getattr(cc, "start_media", None)
    if message_text is None:
        message_text = getattr(cc, "start_message", None)


    media_type, media_file_id = cust.parse_media(raw_media)
    if not media_file_id and not message_text:
        return None
    return {
        "type": media_type,
        "file_id": media_file_id,
        "message": message_text,
        "name": (await cust.get_clone_name(clone_id)) or getattr(cc, "display_name", None) or "ɪᴏᴛᴀ",
    }


async def _send_custom_start_media(message: Message, media_type, file_id, caption, kb) -> bool:
    """Deliver the custom /start media dispatched on its persisted type.

    ``kb`` is the styled-button panel; buttons are attached to every attempt.
    Returns True when delivered, False so callers degrade to the text fallback.
    """
    try:
        if media_type == "video":
            await message.reply_video(
                video=file_id,
                caption=caption,
                reply_markup=buttons_to_inline_markup(kb),
                parse_mode="HTML",
            )
            return True
        if media_type == "animation":
            await message.reply_animation(
                animation=file_id,
                caption=caption,
                reply_markup=buttons_to_inline_markup(kb),
                parse_mode="HTML",
            )
            return True
        if media_type == "document":
            await message.reply_document(
                document=file_id,
                caption=caption,
                reply_markup=buttons_to_inline_markup(kb),
                parse_mode="HTML",
            )
            return True

        try:
            await smart_send_photo(message.chat.id, file_id, caption=caption, reply_markup=kb)
            return True
        except Exception:
            await message.reply_photo(
                photo=file_id,
                caption=caption,
                reply_markup=buttons_to_inline_markup(kb),
                parse_mode="HTML",
            )
            return True
    except Exception:
        return False


async def fetch_user_pfp(user_id: int, fallback: str) -> str:
    try:
        chat = await app.get_chat(user_id)
        if chat.photo and getattr(chat.photo, "big_file_id", None):
            os.makedirs("downloads", exist_ok=True)
            path = await app.download_media(
                chat.photo.big_file_id,
                file_name=f"downloads/pp_{user_id}.png",
            )
            if path:
                return path
    except Exception:
        pass
    return fallback


@app.on_message(filters.command(["start"]) & filters.private & ~filters.user(list(BANNED_USERS)))
@LanguageStart
async def start_pm(client, message: Message, _):
    try:
        await add_served_user(message.from_user.id)
    except Exception:
        pass

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = first_page(_)
            return await smart_send_photo(
                message.chat.id,
                photo=HELP_IMG_URL,
                caption=_["help_1"].format(clone_support_link()),
                reply_markup=keyboard,
            )

        if name.startswith("clone"):
            from strings import helpers as _helpers
            from IotaXMedia.utils.inline.help import clone_help_panel

            is_clone = bool(getattr(config, "CLONE_MODE", False))
            if is_clone:
                caption = (
                    "㋡ <b>𐌉σᴛᴧx ᴄℓσηє ʙσᴛ</b>\n\n"
                    "➤ ʏσυ'ʀє ση α ᴄℓσηєᴅ ɪηѕᴛαηᴄє.\n"
                    "➤ ᴄυѕᴛσᴍɪᴢє ѕᴛαʀᴛ / ρɪηɢ / ѕᴛαᴛѕ / ѕᴛʀɪηɢ νɪα ᴄℓσηє ᴄσᴍᴍαηᴅѕ.\n"
                    "➤ ᴛαᴘ нєʟρ ғσʀ ғυʟʟ ᴄαᴘαʙɪʟɪᴛɪєѕ.\n\n"
                    "🫧 ᴘσωєʀєᴅ ʙγ 𐌉σᴛᴧx 𐌍єᴅɪα"
                )
                keyboard = first_page(_)
            else:
                caption = _.get("clone_1") or _helpers.CLONE_HELP_MENU
                keyboard = clone_help_panel(_)
            return await smart_send_photo(
                message.chat.id,
                photo=HELP_IMG_URL,
                caption=caption,
                reply_markup=keyboard,
            )

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            if config.LOGGER_ID and await is_on_off(2):
                username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
                await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=(
                        f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n"
                        f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                        f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
                    ),
                    parse_mode="HTML",
                )
            return

        if name.startswith("inf"):
            m = await message.reply_text("🔎")
            try:
                vid_id = str(name).replace("info_", "", 1)
                query = f"https://www.youtube.com/watch?v={vid_id}"
                results = VideosSearch(query, limit=1)
                data = await results.next()
                result = (data.get("result") or [None])[0]
                if not result:
                    await m.edit_text("No results found.")
                    return

                title = result.get("title") or "Unknown"
                duration = result.get("duration") or "Unknown"
                views = (result.get("viewCount") or {}).get("short") or "Unknown"
                thumbnail = ((result.get("thumbnails") or [{}])[0].get("url") or "").split("?")[0]
                channellink = (result.get("channel") or {}).get("link") or "https://youtube.com"
                channel = (result.get("channel") or {}).get("name") or "Unknown"
                link = result.get("link") or query
                published = result.get("publishedTime") or "Unknown"

                searched_text = _["start_6"].format(title, duration, views, published, channellink, channel, app.mention)
                key = [
                    [
                        styled_button(text=_["S_B_6"], url=link, style="primary"),
                        styled_button(text=_["S_B_4"], url=clone_support_link(), style="primary"),
                    ]
                ]

                await m.delete()

                await smart_send_photo(
                    message.chat.id,
                    photo=thumbnail or HELP_IMG_URL,
                    caption=searched_text,
                    reply_markup=key,
                )

                if config.LOGGER_ID and await is_on_off(2):
                    username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=(
                            f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n"
                            f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                            f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
                        ),
                    )
            except Exception as e:
                await m.edit_text(f"Error: {e}")
            return

    out = private_panel(_)





    ov = await _clone_start_override()
    if ov is not None:
        caption = ov["message"] or (
            f"ʜєʏ {message.from_user.mention if message.from_user else 'ᴜsєꝛ'},\n"
            f"ᴛʜɪs ɪs ˹{ov['name']}˹ ᴍᴜsɪᴄ˼ ♪ !"
        )
        kb = private_panel(_)
        if ov["file_id"]:
            if await _send_custom_start_media(message, ov["type"], ov["file_id"], caption, kb):
                return


        try:
            await smart_send_message(message.chat.id, caption, reply_markup=kb)
        except Exception:
            await message.reply_text(caption, reply_markup=buttons_to_inline_markup(kb), disable_web_page_preview=True)
        return

    if STICKERS:
        try:
            sticker_message = await message.reply_sticker(sticker=random.choice(STICKERS))
            asyncio.create_task(delete_sticker_after_delay(sticker_message, 2))
        except Exception:
            pass

    served_chats_coro = get_served_chats()
    served_users_coro = get_served_users()
    stats_coro = bot_sys_stats()
    served_chats, served_users, (UP, CPU, RAM, DISK) = await asyncio.gather(
        served_chats_coro, served_users_coro, stats_coro
    )

    photo_arg = await fetch_user_pfp(message.from_user.id, START_IMG_URL)

    try:
        await smart_send_photo(
            message.chat.id,
            photo_arg,
            caption=random.choice(AYUV).format(
                message.from_user.mention, app.mention, UP, DISK, CPU, RAM, len(served_users), len(served_chats)
            ),
            reply_markup=out,
        )
    except Exception:
        await message.reply_photo(
            photo=photo_arg,
            caption=random.choice(AYUV).format(
                message.from_user.mention, app.mention, UP, DISK, CPU, RAM, len(served_users), len(served_chats)
            ),
            reply_markup=buttons_to_inline_markup(out),
            parse_mode="HTML",
        )

    if config.LOGGER_ID and await is_on_off(2):
        username = f"@{message.from_user.username}" if message.from_user.username else "(none)"
        await app.send_message(
            chat_id=config.LOGGER_ID,
            text=(
                f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n"
                f"<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n"
                f"<b>ᴜsᴇʀɴᴀᴍᴇ :</b> {username}"
            ),
            parse_mode="HTML",
        )


@app.on_message(filters.command(["start"]) & filters.group & ~filters.user(list(BANNED_USERS)))
@LanguageStart
async def start_gp(client, message: Message, _):




    ov = await _clone_start_override()
    if ov is not None:
        caption = ov["message"] or (
            f"ʜєʏ {message.from_user.mention if message.from_user else 'ᴜsєꝛ'},\n"
            f"ᴛʜɪs ɪs ˹{ov['name']}˹ ᴍᴜsɪᴄ˼ ♪ !"
        )
        kb = start_panel(_)
        if ov["file_id"]:
            if await _send_custom_start_media(message, ov["type"], ov["file_id"], caption, kb):
                return
        try:
            await smart_send_message(message.chat.id, caption, reply_markup=kb)
        except Exception:
            await message.reply_text(caption, reply_markup=buttons_to_inline_markup(kb), disable_web_page_preview=True)
        return
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    photo_arg = await fetch_user_pfp(message.from_user.id, START_IMG_URL)
    try:
        await smart_send_photo(
            message.chat.id,
            photo_arg,
            caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=out,
        )
    except Exception:
        try:
            await message.reply_photo(
                photo=photo_arg,
                caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=buttons_to_inline_markup(out),
                parse_mode="HTML",
            )
        except Exception:
            await message.reply_text(
                _["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=buttons_to_inline_markup(out) if out else None,
            )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)

            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except Exception:
                    pass

            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)

                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            clone_support_link(),
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                photo_arg = await fetch_user_pfp(message.from_user.id, STREAM_IMG_URL)
                try:
                    await smart_send_photo(
                        message.chat.id,
                        photo_arg,
                        caption=_["start_3"].format(
                            message.from_user.mention,
                            app.mention,
                            message.chat.title,
                            app.mention,
                        ),
                        reply_markup=out,
                    )
                except Exception:
                    try:
                        await message.reply_photo(
                            photo=photo_arg,
                            caption=_["start_3"].format(
                                message.from_user.mention,
                                app.mention,
                                message.chat.title,
                                app.mention,
                            ),
                            reply_markup=buttons_to_inline_markup(out),
                            parse_mode="HTML",
                        )
                    except Exception:
                        await message.reply_text(
                            _["start_3"].format(
                                message.from_user.mention,
                                app.mention,
                                message.chat.title,
                                app.mention,
                            ),
                            reply_markup=buttons_to_inline_markup(out),
                        )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()

        except Exception as ex:
            print(ex)
