# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import os
from math import ceil
from typing import Dict, List, Tuple
import tempfile

import edge_tts
from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums

from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import styled_button, send_message_colored, edit_message_text_colored

_voice_sessions: Dict[Tuple[int, int], str] = {}
_voices: List[dict] = []
_languages: List[str] = []
_VOICES_LOCK = asyncio.Lock()

PER_ROW = 4
PER_PAGE = 16
TMP_DIR = tempfile.gettempdir()

async def _init_voices() -> None:
    global _voices, _languages
    if _voices:
        return

    async with _VOICES_LOCK:
        if _voices:
            return

        raw = await edge_tts.list_voices()
        _voices = [
            {
                "short_name": v["ShortName"],
                "locale": v["Locale"],
                "gender": v["Gender"],
            }
            for v in raw
        ]
        _languages = sorted({v["locale"].split("-", 1)[0] for v in _voices})


def _paginate(items: List[str], page: int) -> Tuple[List[str], int]:
    total = len(items)
    pages = max(1, ceil(total / PER_PAGE))
    page = max(1, min(page, pages))
    start = (page - 1) * PER_PAGE
    return items[start : start + PER_PAGE], pages


def _build_keyboard(
    items: List[str],
    step: str,
    extra: Dict[str, str],
    page: int,
) -> InlineKeyboardMarkup:
    if not items:
        return InlineKeyboardMarkup([])

    page_items, total_pages = _paginate(items, page)

    rows: List[List[InlineKeyboardButton]] = []
    for i in range(0, len(page_items), PER_ROW):
        chunk = page_items[i : i + PER_ROW]
        rows.append(
            [
                InlineKeyboardButton(
                    text=item,
                    callback_data="tts:"
                    + f"s={step}"
                    + "".join(f"|{k}={v}" for k, v in extra.items())
                    + f"|p={page}|v={item}",
                style=enums.ButtonStyle.PRIMARY)
                for item in chunk
            ]
        )

    nav: List[InlineKeyboardButton] = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                "◀️ Prev",
                callback_data="tts:"
                + f"s={step}"
                + "".join(f"|{k}={v}" for k, v in extra.items())
                + f"|p={page-1}",
            style=enums.ButtonStyle.PRIMARY)
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data="tts:"
                + f"s={step}"
                + "".join(f"|{k}={v}" for k, v in extra.items())
                + f"|p={page+1}",
            style=enums.ButtonStyle.PRIMARY)
        )
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(rows)


def _build_keyboard_colored(items: List[str], step: str, extra: Dict[str, str], page: int):
    if not items:
        return []

    page_items, total_pages = _paginate(items, page)

    rows: List[List[dict]] = []
    for i in range(0, len(page_items), PER_ROW):
        chunk = page_items[i : i + PER_ROW]
        rows.append(
            [
                styled_button(
                    text=item,
                    callback_data="tts:"
                    + f"s={step}"
                    + "".join(f"|{k}={v}" for k, v in extra.items())
                    + f"|p={page}|v={item}",
                style="primary")
                for item in chunk
            ]
        )

    nav: List[dict] = []
    if page > 1:
        nav.append(
            styled_button(
                "◀️ Prev",
                callback_data="tts:"
                + f"s={step}"
                + "".join(f"|{k}={v}" for k, v in extra.items())
                + f"|p={page-1}",
                style="primary",
            )
        )
    if page < total_pages:
        nav.append(
            styled_button(
                "Next ▶️",
                callback_data="tts:"
                + f"s={step}"
                + "".join(f"|{k}={v}" for k, v in extra.items())
                + f"|p={page+1}",
                style="primary",
            )
        )
    if nav:
        rows.append(nav)

    return rows


def _session_key(chat_id: int, user_id: int) -> Tuple[int, int]:
    return chat_id, user_id


def _cleanup(path: str) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


async def _synthesize(voice: str, text: str, out_path: str) -> None:
    comm = edge_tts.Communicate(text=text, voice=voice)
    await comm.save(out_path)

@app.on_message(filters.command("voices"))
async def cmd_voices(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Please provide the text to convert.\n\nExample: `/voices Hello world`",
            parse_mode=ParseMode.MARKDOWN,
        )

    await _init_voices()

    text = " ".join(message.command[1:])
    _voice_sessions[_session_key(message.chat.id, message.from_user.id)] = text

    kb = _build_keyboard(_languages, step="lang", extra={}, page=1)
    kb_col = _build_keyboard_colored(_languages, step="lang", extra={}, page=1)
    try:
        r = await send_message_colored(message.chat.id, "🌐 **Step 1:** Select a language", kb_col, parse_mode=ParseMode.MARKDOWN)
        if r:
            return
    except Exception:
        pass
    await message.reply_text(
        "🌐 **Step 1:** Select a language",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )


@app.on_message(filters.command("tts"))
async def cmd_tts(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "❌ Usage:\n`/tts <voice_model> <text>`\nAlternatively try `/voices` for guided selection.",
            parse_mode=ParseMode.MARKDOWN,
        )

    await _init_voices()

    voice = message.command[1]
    text = " ".join(message.command[2:])

    if not any(v["short_name"] == voice for v in _voices):
        return await message.reply_text(
            f"⚠️ Unknown voice: `{voice}`\nUse `/voiceall` or `/voices` to browse voices.",
            parse_mode=ParseMode.MARKDOWN,
        )

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp = tmp_file.name

    try:
        await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
        await _synthesize(voice, text, tmp)

        await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_AUDIO)
        await client.send_audio(
            chat_id=message.chat.id,
            audio=tmp,
            caption=f"🗣️ `{voice}`",
            reply_to_message_id=message.id,
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as exc:
        await message.reply_text(f"⚠️ Failed to generate speech: {exc}")
    finally:
        _cleanup(tmp)


async def _edit_tts_text(callback: CallbackQuery, text: str, kb, kb_col):
    try:
        r = await edit_message_text_colored(
            callback.message.chat.id, callback.message.id, text, kb_col, parse_mode=ParseMode.MARKDOWN
        )
        if r:
            return
    except Exception:
        pass
    return await callback.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


@app.on_callback_query(filters.regex(r"^tts:"))
async def cb_tts(client: Client, callback: CallbackQuery):
    data = callback.data[4:]
    parts = dict(p.split("=", 1) for p in data.split("|") if "=" in p)
    step = parts.get("s")
    page = int(parts.get("p", "1"))

    await _init_voices()

    key = _session_key(callback.message.chat.id, callback.from_user.id)
    text = _voice_sessions.get(key)
    if not text:
        return await callback.answer(
            "⚠️ Session expired. Send `/voices` again.", show_alert=True
        )

    if step == "lang":
        if "v" not in parts:
            kb = _build_keyboard(_languages, "lang", {}, page)
            kb_col = _build_keyboard_colored(_languages, "lang", {}, page)
            return await _edit_tts_text(callback, "🌐 **Step 1:** Select a language", kb, kb_col)

        lang = parts["v"]
        regions = sorted(
            {
                v["locale"].split("-", 1)[1]
                for v in _voices
                if v["locale"].startswith(f"{lang}-")
            }
        )
        kb = _build_keyboard(regions, "region", {"l": lang}, 1)
        kb_col = _build_keyboard_colored(regions, "region", {"l": lang}, 1)
        return await _edit_tts_text(callback, "🌍 **Step 2:** Select a region", kb, kb_col)

    if step == "region":
        lang = parts["l"]

        if "v" not in parts:
            regions = sorted(
                {
                    v["locale"].split("-", 1)[1]
                    for v in _voices
                    if v["locale"].startswith(f"{lang}-")
                }
            )
            kb = _build_keyboard(regions, "region", {"l": lang}, page)
            kb_col = _build_keyboard_colored(regions, "region", {"l": lang}, page)
            return await _edit_tts_text(callback, "🌍 **Step 2:** Select a region", kb, kb_col)

        region = parts["v"]
        locale = f"{lang}-{region}"
        models = sorted([v["short_name"] for v in _voices if v["locale"] == locale])
        kb = _build_keyboard(models, "model", {"l": lang, "r": region}, 1)
        kb_col = _build_keyboard_colored(models, "model", {"l": lang, "r": region}, 1)
        return await _edit_tts_text(callback, "🔊 **Step 3:** Choose a voice model", kb, kb_col)

    if step == "model":
        lang = parts["l"]
        region = parts["r"]

        if "v" not in parts:
            locale = f"{lang}-{region}"
            models = sorted([v["short_name"] for v in _voices if v["locale"] == locale])
            kb = _build_keyboard(models, "model", {"l": lang, "r": region}, page)
            kb_col = _build_keyboard_colored(models, "model", {"l": lang, "r": region}, page)
            return await _edit_tts_text(callback, "🔊 **Step 3:** Choose a voice model", kb, kb_col)

        voice = parts["v"]
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp = tmp_file.name

        try:
            await client.send_chat_action(callback.message.chat.id, ChatAction.RECORD_AUDIO)
            await _synthesize(voice, text, tmp)

            await client.send_chat_action(callback.message.chat.id, ChatAction.UPLOAD_AUDIO)
            await client.send_audio(
                chat_id=callback.message.chat.id,
                audio=tmp,
                caption=f"🗣️ `{voice}`",
                reply_to_message_id=callback.message.reply_to_message.id if callback.message.reply_to_message else callback.message.id,
                parse_mode=ParseMode.MARKDOWN,
            )
            await callback.edit_message_text("✅ Audio generated successfully!")
        except Exception as exc:
            await callback.message.reply_text(f"⚠️ Generation failed: {exc}")
        finally:
            _cleanup(tmp)
            _voice_sessions.pop(key, None)
        return await callback.answer()

    await callback.answer("🤔 Unknown action. Send /voices again.", show_alert=True)


@app.on_message(filters.command("voiceall"))
async def cmd_voiceall(client: Client, message: Message):
    await _init_voices()

    sorted_voices = sorted(_voices, key=lambda v: v["short_name"])
    lines = [
        f"{v['short_name']} — {v['locale']} ({v['gender']})" for v in sorted_voices
    ]
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
        path = tmp_file.name
        tmp_file.write("\n".join(lines).encode("utf-8"))

    try:
        await message.reply_document(document=path, caption="📋 List of all available voices")
    finally:
        _cleanup(path)
