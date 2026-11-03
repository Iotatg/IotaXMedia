# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text
from IotaXMedia.utils.translate import get_chat_lang, set_chat_lang, translate

LANG_HELP = (
    "examples : hi, en, es, ru, ar, fr, ja, pt, de, ko, bn, ta\n"
    "use /translate off to disable auto-translate"
)


@app.on_message(filters.command(["translate", "trset"]) & filters.group)
@AdminActual
async def translate_set(client, message: Message, _):
    parts = message.text.split(None, 2)
    arg = parts[1].strip().lower() if len(parts) > 1 else ""
    if not arg or arg == "off":
        await set_chat_lang(message.chat.id, None)
        return await message.reply_text(god_text("auto-translate disabled") + ".")
    await set_chat_lang(message.chat.id, arg)
    await message.reply_text(f"✅ {god_text('auto-translate set to')} : {arg}\n{LANG_HELP}")


@app.on_message(filters.command(["tr", "translatemsg"]) & filters.group)
@language
async def translate_msg(client, message: Message, _):
    reply = message.reply_to_message
    if not reply or not reply.text:
        return await message.reply_text(god_text("reply to a message to translate") + ".")
    parts = message.text.split(None, 2)
    lang = parts[1].strip() if len(parts) > 1 else await get_chat_lang(message.chat.id)
    if not lang:
        return await message.reply_text(god_text("usage") + " : /tr <lang>\n" + LANG_HELP)
    out = await translate(reply.text, lang)
    if not out:
        return await message.reply_text(god_text("translation failed / unsupported") + ".")
    await message.reply_text(
        f"<b>{god_text('translated')} [{lang}]</b> :\n\n{out}",
        disable_web_page_preview=True,
    )
