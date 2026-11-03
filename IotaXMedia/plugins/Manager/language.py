# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram import enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from IotaXMedia import app
from IotaXMedia.utils.database import get_lang, set_lang
from IotaXMedia.utils.decorators import ActualAdminCB, language, languageCB
from IotaXMedia.utils.colored_buttons import edit_reply_markup_colored, send_message_colored, styled_button
from config import BANNED_USERS
from strings import get_string, languages_present


def languages_keyboard(_):
    rows = []
    row = []

    for idx, code in enumerate(languages_present):
        row.append(
            InlineKeyboardButton(
                text=languages_present[code],
                callback_data=f"languages:{code}",
            style=enums.ButtonStyle.PRIMARY)
        )
        if (idx + 1) % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="SETTINGS_PRIVATE_BACK", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER),
        ]
    )

    return InlineKeyboardMarkup(rows)


def languages_keyboard_col(_):
    rows = []
    row = []

    for idx, code in enumerate(languages_present):
        row.append(styled_button(languages_present[code], callback_data=f"languages:{code}", style="primary"))
        if (idx + 1) % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    rows.append(
        [
            styled_button(_["BACK_BUTTON"], callback_data="SETTINGS_PRIVATE_BACK", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ]
    )

    return rows


@app.on_message(filters.command(["lang", "setlang", "language"]) & ~filters.user(list(BANNED_USERS)))
@language
async def langs_command(client, message: Message, _):
    keyboard = languages_keyboard(_)
    keyboard_col = languages_keyboard_col(_)
    try:
        r = await send_message_colored(message.chat.id, _["lang_1"], keyboard_col)
        if r:
            return
    except Exception:
        pass
    try:
        await message.reply_text(_["lang_1"], reply_markup=keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text(_["lang_1"], reply_markup=keyboard)


@app.on_callback_query(filters.regex("LG") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def languagecb(client, CallbackQuery: CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    keyboard = languages_keyboard(_)
    keyboard_col = languages_keyboard_col(_)
    try:
        r = await edit_reply_markup_colored(
            CallbackQuery.message.chat.id, CallbackQuery.message.id, keyboard_col
        )
        if r:
            return
    except Exception:
        pass
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"languages:(.*?)") & ~filters.user(list(BANNED_USERS)))
@ActualAdminCB
async def language_markup(client, CallbackQuery: CallbackQuery, _):
    lang_code = CallbackQuery.data.split(":")[1]
    old_lang = await get_lang(CallbackQuery.message.chat.id)
    if str(old_lang) == str(lang_code):
        return await CallbackQuery.answer(_["lang_4"], show_alert=True)

    try:
        _ = get_string(lang_code)
        await CallbackQuery.answer(_["lang_2"], show_alert=True)
    except:
        _ = get_string(old_lang)
        return await CallbackQuery.answer(_["lang_3"], show_alert=True)

    await set_lang(CallbackQuery.message.chat.id, lang_code)
    keyboard = languages_keyboard(_)
    keyboard_col = languages_keyboard_col(_)
    try:
        r = await edit_reply_markup_colored(
            CallbackQuery.message.chat.id, CallbackQuery.message.id, keyboard_col
        )
        if r:
            return
    except Exception:
        pass
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)
