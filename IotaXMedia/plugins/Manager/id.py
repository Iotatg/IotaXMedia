# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.plugins.Manager.anonymous import (
    ANON_ID_PLACEHOLDER,
    is_anonymous,
)
import config


@app.on_message(filters.command("id"))
async def get_id(client, message: Message):
    chat, user, reply = message.chat, message.from_user, message.reply_to_message
    out = []

    if message.link:
        out.append(f"**[ᴍᴇssᴀɢᴇ ɪᴅ:]({message.link})** `{message.id}`")
    else:
        out.append(f"**ᴍᴇssᴀɢᴇ ɪᴅ:** `{message.id}`")

    out.append(f"**[ʏᴏᴜʀ ɪᴅ:](tg://user?id={user.id})** `{user.id}`")

    if len(message.command) == 2:
        try:
            target = message.text.split(maxsplit=1)[1]
            tgt_user = await client.get_users(target)
            if tgt_user and not tgt_user.is_bot and await is_anonymous(tgt_user.id):
                out.append(f"**ᴜsᴇʀ ɪᴅ:** {ANON_ID_PLACEHOLDER}")
            else:
                out.append(f"**[ᴜsᴇʀ ɪᴅ:](tg://user?id={tgt_user.id})** `{tgt_user.id}`")
        except Exception:
            return await message.reply_text("**ᴛʜɪs ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ.**", quote=True, parse_mode="markdown")

    if chat.username and chat.type != "private":
        out.append(f"**[ᴄʜᴀᴛ ɪᴅ:](https://t.me/{chat.username})** `{chat.id}`")
    else:
        out.append(f"**ᴄʜᴀᴛ ɪᴅ:** `{chat.id}`")

    if reply:
        if reply.link:
            out.append(f"**[ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪᴅ:]({reply.link})** `{reply.id}`")
        else:
            out.append(f"**ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪᴅ:** `{reply.id}`")

        if reply.from_user:
            replied_user = reply.from_user
            if not replied_user.is_bot and await is_anonymous(replied_user.id):
                out.append(f"**ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ:** {ANON_ID_PLACEHOLDER}")
            else:
                out.append(
                    f"**[ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ:](tg://user?id={replied_user.id})** "
                    f"`{replied_user.id}`"
                )

        if reply.forward_from_chat:
            out.append(
                f"ᴛʜᴇ ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀɴɴᴇʟ **{reply.forward_from_chat.title}** "
                f"ʜᴀs ɪᴅ `{reply.forward_from_chat.id}`"
            )

        if reply.sender_chat:
            out.append(f"ɪᴅ ᴏғ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴄʜᴀᴛ/ᴄʜᴀɴɴᴇʟ: `{reply.sender_chat.id}`")

    await message.reply_text(
        "\n".join(out),
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN,
    )
