# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message
from config import *
import config
from IotaXMedia import app
from IotaXMedia.core.call import StreamController
from IotaXMedia.utils import bot_sys_stats
from IotaXMedia.utils.decorators.language import language
from IotaXMedia.utils.inline import supp_markup
from config import BANNED_USERS


@app.on_message(filters.command("ping", prefixes=["/", "."]) & ~filters.user(list(BANNED_USERS)))
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    pytgping = await StreamController.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    body = _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping)



    cc = getattr(config, "CLONE_CONFIG", None)
    if cc is not None:
        from IotaXMedia.clone import customization as cust

        clone_id = getattr(cc, "token", None) or config.BOT_TOKEN
        ping_media = await cust.get_ping_media(clone_id) or getattr(cc, "ping_media", None)
        media_type, mid = cust.parse_media(ping_media)
        if mid:
            try:
                if media_type == "video":
                    return await message.reply_video(
                        video=mid, caption=body, reply_markup=supp_markup(_)
                    )
                if media_type == "animation":
                    return await message.reply_animation(
                        animation=mid, caption=body, reply_markup=supp_markup(_)
                    )
                if media_type == "document":
                    return await message.reply_document(
                        document=mid, caption=body, reply_markup=supp_markup(_)
                    )
                return await message.reply_photo(
                    photo=mid, caption=body, reply_markup=supp_markup(_)
                )
            except Exception:
                pass
    response = await message.reply_text(_["ping_1"].format(app.mention))
    await response.edit_text(body, reply_markup=supp_markup(_))
