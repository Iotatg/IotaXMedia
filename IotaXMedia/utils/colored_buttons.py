# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT







"""
⚠️ CRITICAL: Telegram colored buttons require 2 things:
   1. Telegram client updated AFTER February 9, 2026
   2. Bot API HTTP calls (Kurigram/Pyrogram don't support 'style' field)

This module bypasses Kurigram and sends buttons directly via Telegram Bot API HTTP.

Supported Styles:
  • "primary" - Blue (main actions)
  • "success" - Green (positive actions like confirm)
  • "danger"  - Red (destructive actions like delete)
  • None - Default button color

Example Usage:
    buttons = [[
        styled_button("✅ Yes", callback_data="yes", style="success"),
        styled_button("❌ No", callback_data="no", style="danger")
    ]]
    
    # Try Bot API first (with colors)
    result = await send_message_colored(chat_id, "Choose:", buttons)
    
    # Fallback to Kurigram if Bot API fails (no colors)
    if not result:
        await message.reply_text("Choose:", reply_markup=buttons_to_inline_markup(buttons))
"""

import asyncio
import inspect
import json
import logging
from typing import Dict, List, Optional, Union

import aiohttp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import config

logger = logging.getLogger(__name__)


_session: Optional[aiohttp.ClientSession] = None






async def _get_session() -> aiohttp.ClientSession:
    """Get or create aiohttp session."""
    global _session
    
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        _session = aiohttp.ClientSession(timeout=timeout)
    
    return _session


async def _bot_api_call(method: str, payload: dict, token: str = None) -> Optional[dict]:
    """Make HTTP POST to Telegram Bot API.

    Args:
        method: API method (e.g., 'sendMessage')
        payload: JSON payload
        token: Bot token to authenticate with (defaults to the main BOT_TOKEN;
            clone-owned chats must pass the owning clone's token).

    Returns:
        Response 'result' field if successful, None otherwise
    """
    bot_token = token or config.BOT_TOKEN
    if not bot_token:
        logger.warning("⚠️ BOT_TOKEN not set! Colored buttons will NOT work.")
        return None


    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    session = await _get_session()
    
    try:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            
            if data.get("ok"):
                logger.debug(f" Bot API {method} success")
                return data.get("result")
            error = data.get("description", "Unknown error")

            if "BUTTON_USER_PRIVACY_RESTRICTED" in error:
                logger.debug(f" Bot API {method} skipped: {error}")
                return None

            if "can't parse entities" in error and payload.get("parse_mode"):
                logger.debug(f" Bot API {method} parse error, retrying without parse_mode")
                payload = dict(payload)
                del payload["parse_mode"]
                async with session.post(url, json=payload) as resp2:
                    data2 = await resp2.json()
                    if data2.get("ok"):
                        return data2.get("result")
                    logger.warning(f"\u274c Bot API {method} failed retry: {data2.get('description', '')}")
                return None
            logger.warning(f"\u274c Bot API {method} failed: {error}")
    
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Bot API {method} timeout")
        return None
    except Exception as e:
        logger.error(f"💥 Bot API {method} exception: {e}")
        return None


def _style_str(style) -> Optional[str]:
    """Normalize a style value (enum, str, None) to a Bot API style string."""
    if style is None:
        return None
    value = getattr(style, "value", style)
    value = str(value).split(".")[-1].lower()
    return value if value in ("primary", "success", "danger") else None


def _button_to_api(btn) -> Dict:
    """Convert one button (dict or InlineKeyboardButton) to Bot API dict."""
    if not isinstance(btn, dict):
        api_btn: Dict = {"text": getattr(btn, "text", "")}
        callback_data = getattr(btn, "callback_data", None)
        if callback_data is not None:
            api_btn["callback_data"] = (
                callback_data.decode()
                if isinstance(callback_data, bytes)
                else callback_data
            )
        url = getattr(btn, "url", None)
        if url:
            api_btn["url"] = url
        web_app = getattr(btn, "web_app", None)
        if web_app is not None:
            api_btn["web_app"] = {"url": getattr(web_app, "url", web_app)}
        siqcc = getattr(btn, "switch_inline_query_current_chat", None)
        if siqcc:
            api_btn["switch_inline_query_current_chat"] = siqcc
    else:
        api_btn = {"text": btn["text"]}
        if "callback_data" in btn:
            api_btn["callback_data"] = btn["callback_data"]
        if "url" in btn:
            api_btn["url"] = btn["url"]
        if "switch_inline_query_current_chat" in btn:
            api_btn["switch_inline_query_current_chat"] = btn[
                "switch_inline_query_current_chat"
            ]

    style = _style_str(btn.get("style") if isinstance(btn, dict) else getattr(btn, "style", None))
    if style:

        api_btn["style"] = style
    return api_btn


def _iter_rows(buttons):
    """Yield button rows from a markup or a list-of-rows."""
    if isinstance(buttons, InlineKeyboardMarkup):
        buttons = buttons.inline_keyboard
    return buttons or []


def _build_inline_keyboard(buttons: List[List[Dict]]) -> List[List[Dict]]:
    """Convert styled buttons to Bot API inline_keyboard format.

    Accepts dict buttons (``styled_button``) and ``InlineKeyboardButton``
    objects alike, and preserves the ``style`` field for colored buttons.
    """
    keyboard = []
    for row in _iter_rows(buttons):
        keyboard.append([_button_to_api(btn) for btn in row])
    return keyboard






def _extract_title(caption: str) -> str:
    """Best-effort track title extraction from a now-playing caption."""
    if not caption:
        return ""
    first = caption.splitlines()[0] if caption.splitlines() else caption

    first = first.lstrip("▶️▷❥➤►♩♪ ").strip(" []-:")
    if len(first) > 80:
        first = first[:80]
    return first


def styled_button(
    text: str,
    callback_data: str = None,
    url: str = None,
    switch_inline_query_current_chat: str = None,
    style: str = None
) -> Dict[str, str]:
    """Create a colored button dictionary.
    
    Args:
        text: Button label
        callback_data: Callback data (1-64 bytes)
        url: URL to open
        switch_inline_query_current_chat: text to insert into the current chat
            input when the button is pressed (e.g. a command like "/setstart").
        style: "primary" (blue) | "success" (green) | "danger" (red)
    
    Returns:
        Button dict with 'style' field
    """
    btn = {"text": text}
    
    if callback_data:
        btn["callback_data"] = callback_data
    if url:
        btn["url"] = url
    if switch_inline_query_current_chat:
        btn["switch_inline_query_current_chat"] = switch_inline_query_current_chat
    if style and style in ("primary", "success", "danger"):
        btn["style"] = style
    
    return btn


def buttons_to_inline_markup(buttons) -> InlineKeyboardMarkup:
    """Convert styled buttons to a pyrogram InlineKeyboardMarkup.

    Used as the Pyrogram-side fallback; the Bot API path is preferred because
    it carries the ``style`` colors. On pyrogram builds that support button
    styles (kurigram) the style is preserved here too via the ``style`` kwarg.

    Accepts:
      - InlineKeyboardMarkup (returned as-is)
      - list[list[InlineKeyboardButton]] (wrapped as-is)
      - list[list[dict]] styled buttons (converted)
    """
    if buttons is None:
        return None
    if isinstance(buttons, InlineKeyboardMarkup):
        return buttons
    keyboard = []
    for row in buttons:
        kb_row = []
        for btn in row:
            if isinstance(btn, InlineKeyboardButton):
                kb_row.append(btn)
            else:
                kwargs = {"text": btn["text"]}
                for key in (
                    "callback_data",
                    "url",
                    "web_app",
                    "login_url",
                    "user_id",
                    "switch_inline_query",
                    "switch_inline_query_current_chat",
                    "callback_game",
                ):
                    if key in btn:
                        kwargs[key] = btn[key]
                style = _style_str(btn.get("style"))
                if style:
                    kwargs["style"] = style
                kb_row.append(InlineKeyboardButton(**kwargs))
        keyboard.append(kb_row)

    return InlineKeyboardMarkup(keyboard)






async def send_message_colored(
    chat_id: Union[int, str],
    text: str,
    reply_markup: List[List[Dict]],
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = False,
    token: str = None,
) -> Optional[Dict]:
    """Send message with COLORED buttons via Bot API HTTP.
    
    Returns None if failed - use Kurigram fallback in that case.
    """
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
        "reply_markup": {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    }
    
    return await _bot_api_call("sendMessage", payload, token)


async def send_photo_colored(
    chat_id: Union[int, str],
    photo: str,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Send photo with COLORED buttons via Bot API HTTP.
    
    Supports:
    - file_id (string starting with any non-http char)
    - HTTP URL (http:// or https://)
    - Local file path (uploads as multipart/form-data)
    """
    

    is_url = photo.startswith("http://") or photo.startswith("https://")
    is_local_file = not is_url and ("/" in photo or "\\" in photo)
    
    if is_local_file:

        return await _send_photo_with_file(chat_id, photo, caption, reply_markup, parse_mode, token=token)
    else:

        payload = {
            "chat_id": chat_id,
            "photo": photo,
            "parse_mode": parse_mode
        }
        
        if caption:
            payload["caption"] = caption
        
        if reply_markup:
            payload["reply_markup"] = {
                "inline_keyboard": _build_inline_keyboard(reply_markup)
            }
        
        return await _bot_api_call("sendPhoto", payload, token)


async def send_video_colored(
    chat_id: Union[int, str],
    video: str,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Send video with COLORED buttons via Bot API HTTP.

    Supports file_id, HTTP URL, or local file path.
    """
    is_url = video.startswith("http://") or video.startswith("https://")
    is_local_file = not is_url and ("/" in video or "\\" in video)

    if is_local_file:
        import aiohttp
        url = f"https://api.telegram.org/bot{token or config.BOT_TOKEN}/sendVideo"
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("chat_id", str(chat_id))
            data.add_field("parse_mode", parse_mode)
            if caption:
                data.add_field("caption", caption)
            if reply_markup:
                data.add_field(
                    "reply_markup",
                    json.dumps({"inline_keyboard": _build_inline_keyboard(reply_markup)}),
                )
            data.add_field("video", open(video, "rb"))
            async with session.post(url, data=data, timeout=60) as resp:
                if resp.status != 200:
                    return None
                data_json = await resp.json()
                return data_json if data_json.get("ok") else None
    else:
        payload = {
            "chat_id": chat_id,
            "video": video,
            "parse_mode": parse_mode,
        }
        if caption:
            payload["caption"] = caption
        if reply_markup:
            payload["reply_markup"] = {
                "inline_keyboard": _build_inline_keyboard(reply_markup)
            }
        return await _bot_api_call("sendVideo", payload, token)


async def send_document_colored(
    chat_id: Union[int, str],
    document: str,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Send document/video with COLORED buttons via Bot API HTTP (URL or file_id)."""
    payload = {
        "chat_id": chat_id,
        "document": document,
        "parse_mode": parse_mode,
    }
    if caption:
        payload["caption"] = caption
    if reply_markup:
        payload["reply_markup"] = {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    return await _bot_api_call("sendDocument", payload, token)


async def send_animation_colored(
    chat_id: Union[int, str],
    animation: str,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Send animation (GIF/video) with COLORED buttons via Bot API HTTP (URL or file_id)."""
    payload = {
        "chat_id": chat_id,
        "animation": animation,
        "parse_mode": parse_mode,
    }
    if caption:
        payload["caption"] = caption
    if reply_markup:
        payload["reply_markup"] = {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    return await _bot_api_call("sendAnimation", payload, token)


async def answer_inline_query_colored(
    inline_query_id: str,
    results: List[Dict],
    cache_time: int = 10,
    is_personal: bool = False,
) -> Optional[Dict]:
    """Answer an inline query with results whose reply_markup can carry COLORED buttons.

    `results` items are Bot API InlineQueryResult dicts; each may include
    "reply_markup" as a styled-buttons list (e.g. ``styled_button(...)`` rows).
    """
    bot_results = []
    for res in results:
        item = dict(res)
        rm = item.pop("reply_markup", None)
        if rm:
            item["reply_markup"] = {"inline_keyboard": _build_inline_keyboard(rm)}
        bot_results.append(item)
    payload = {
        "inline_query_id": inline_query_id,
        "results": bot_results,
        "cache_time": cache_time,
        "is_personal": is_personal,
    }
    return await _bot_api_call("answerInlineQuery", payload)


async def _send_photo_with_file(
    chat_id: Union[int, str],
    file_path: str,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Send photo by uploading local file with multipart/form-data."""
    import os
    
    if not os.path.exists(file_path):
        logger.error(f"❌ Photo file not found: {file_path}")
        return None
    
    bot_token = token or config.BOT_TOKEN
    if not bot_token:
        logger.error("❌ BOT_TOKEN not set!")
        return None
    
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    session = await _get_session()
    

    try:
        with open(file_path, "rb") as fh:
            file_bytes = fh.read()
    except Exception as e:
        logger.error(f"❌ Failed reading photo file {file_path}: {e}")
        return None
    
    try:

        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field(
            "photo",
            file_bytes,
            filename=os.path.basename(file_path),
            content_type="application/octet-stream",
        )
        
        if caption:
            form.add_field("caption", caption)
        

        if parse_mode:
            form.add_field("parse_mode", parse_mode)
        
        if reply_markup:
            import json as json_lib
            reply_markup_json = json_lib.dumps({
                "inline_keyboard": _build_inline_keyboard(reply_markup)
            })
            form.add_field("reply_markup", reply_markup_json)
        
        async with session.post(url, data=form) as resp:
            data = await resp.json()
            
            if data.get("ok"):
                logger.debug(f"✅ Bot API sendPhoto (file upload) success")
                return data.get("result")
            else:
                error = data.get("description", "Unknown error")
                

                if "can't parse entities" in error and parse_mode:
                    logger.warning(f"⚠️ HTML parse error, retrying without parse_mode")
                    return await _send_photo_with_file(chat_id, file_path, caption, reply_markup, parse_mode=None, token=token)
                
                logger.warning(f"❌ Bot API sendPhoto (file upload) failed: {error}")
                return None
    
    except asyncio.TimeoutError:
        logger.error(f"⏱️ Bot API sendPhoto timeout")
        return None
    except Exception as e:
        logger.error(f"💥 Bot API sendPhoto exception: {e}")
        return None


async def edit_message_text_colored(
    chat_id: Union[int, str],
    message_id: int,
    text: str,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = False,
    token: str = None,
) -> Optional[Dict]:
    """Edit message text + buttons with COLORS via Bot API HTTP."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview
    }
    
    if reply_markup:
        payload["reply_markup"] = {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    
    return await _bot_api_call("editMessageText", payload, token)


async def edit_message_caption_colored(
    chat_id: Union[int, str],
    message_id: int,
    caption: str = None,
    reply_markup: List[List[Dict]] = None,
    parse_mode: str = "HTML",
    token: str = None,
) -> Optional[Dict]:
    """Edit message caption + buttons with COLORS via Bot API HTTP."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "parse_mode": parse_mode
    }
    
    if caption:
        payload["caption"] = caption
    
    if reply_markup:
        payload["reply_markup"] = {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    
    return await _bot_api_call("editMessageCaption", payload, token)


async def edit_reply_markup_colored(
    chat_id: Union[int, str],
    message_id: int,
    reply_markup: List[List[Dict]],
    token: str = None,
) -> Optional[Dict]:
    """Edit ONLY buttons (keeps colors persistent) via Bot API HTTP.
    
    ⭐ Use this in callback handlers to prevent color disappearing on button tap!
    """
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    }
    
    return await _bot_api_call("editMessageReplyMarkup", payload, token)


async def edit_message_media_colored(
    chat_id: Union[int, str],
    message_id: int,
    media: Dict,
    reply_markup: List[List[Dict]] = None,
    token: str = None,
) -> Optional[Dict]:
    """Edit message media + buttons with COLORS via Bot API HTTP."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "media": media
    }
    
    if reply_markup:
        payload["reply_markup"] = {
            "inline_keyboard": _build_inline_keyboard(reply_markup)
        }
    
    return await _bot_api_call("editMessageMedia", payload, token)







async def smart_send_message(
    chat_id: Union[int, str],
    text: str,
    reply_markup: Optional[List[List[Dict]]] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = False,
    message_thread_id: Optional[int] = None,
):
    """Send a message with colored buttons. Pyrogram first + Bot API edit for colors."""
    from IotaXMedia.core.call import resolve_app
    from pyrogram import enums


    _bot = resolve_app(chat_id)

    send_kwargs = dict(
        chat_id=chat_id,
        text=text,
        parse_mode=enums.ParseMode.HTML if parse_mode == "HTML" else enums.ParseMode.MARKDOWN,
        disable_web_page_preview=disable_web_page_preview,
        reply_markup=buttons_to_inline_markup(reply_markup) if reply_markup else None,
    )



    if message_thread_id is not None:
        try:
            if "message_thread_id" in inspect.signature(_bot.send_message).parameters:
                send_kwargs["message_thread_id"] = message_thread_id
        except Exception:
            pass

    msg = await _bot.send_message(**send_kwargs)
    if msg and reply_markup:
        try:
            await edit_reply_markup_colored(
                chat_id, msg.id, reply_markup, token=getattr(_bot, "bot_token", None)
            )
        except Exception:
            pass
    return msg


async def smart_send_photo(
    chat_id: Union[int, str],
    photo: str,
    caption: Optional[str] = None,
    reply_markup: Optional[List[List[Dict]]] = None,
    parse_mode: str = "HTML",
    message_thread_id: Optional[int] = None,
):
    """Send a photo with colored buttons (Pyrogram first, then Bot API edit_reply_markup)."""
    from IotaXMedia.core.call import resolve_app
    from pyrogram import enums


    _bot = resolve_app(chat_id)

    msg = await _bot.send_photo(
        chat_id=chat_id,
        photo=photo,
        caption=caption,
        parse_mode=enums.ParseMode.HTML if parse_mode == "HTML" else enums.ParseMode.MARKDOWN,
        reply_markup=buttons_to_inline_markup(reply_markup) if reply_markup else None,
    )
    if msg and reply_markup:
        try:
            await edit_reply_markup_colored(
                chat_id, msg.id, reply_markup, token=getattr(_bot, "bot_token", None)
            )
        except Exception:
            pass
    return msg


async def smart_send_stream(
    chat_id: Union[int, str],
    photo: str,
    caption: str,
    reply_markup: Optional[List[List[Dict]]] = None,
    parse_mode: str = "HTML",
):
    """
    Send a now-playing / stream update.

    Respects the per-chat album-art setting: when disabled, a pure text
    message is sent instead of a photo (reduces data load, minimalist chat).
    Routes into the chat's dedicated queue topic when one is set.
    """
    from IotaXMedia.utils.stream.thumb_settings import is_thumb_on
    from IotaXMedia.utils.topic import get_topic_id

    topic_id = await get_topic_id(int(chat_id)) if str(chat_id).lstrip("-").isdigit() else None

    from IotaXMedia.utils.translate import get_chat_lang, translate

    chat_lang = await get_chat_lang(int(chat_id)) if str(chat_id).lstrip("-").isdigit() else None
    if chat_lang:
        translated = await translate(caption, chat_lang)
        if translated:
            caption = translated

    from IotaXMedia.utils.playstats import record_play

    try:
        _title = _extract_title(caption)
        if _title:
            await record_play(int(chat_id), _title)
    except Exception:
        pass

    if await is_thumb_on(chat_id):
        return await smart_send_photo(
            chat_id, photo=photo, caption=caption, reply_markup=reply_markup,
            parse_mode=parse_mode, message_thread_id=topic_id,
        )
    return await smart_send_message(
        chat_id, text=caption, reply_markup=reply_markup,
        parse_mode=parse_mode, message_thread_id=topic_id,
    )


async def smart_edit_message_text(
    chat_id: Union[int, str],
    message_id: int,
    text: str,
    reply_markup: Optional[List[List[Dict]]] = None,
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = False,
):
    """Edit message text/caption via Pyrogram (proper HTML) then apply colored buttons via Bot API.

    Order:
      1. Pyrogram edit_message_text  — handle HTML + deliver reliably
      2. Pyrogram edit_message_caption — fallback for photo captions
      3. Bot API edit_reply_markup — apply style colors
    """
    from IotaXMedia.core.call import resolve_app
    from pyrogram import enums


    _bot = resolve_app(chat_id)

    pm = enums.ParseMode.HTML if parse_mode == "HTML" else enums.ParseMode.MARKDOWN
    rkm = buttons_to_inline_markup(reply_markup) if reply_markup else None


    msg = None
    try:
        msg = await _bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text,
            parse_mode=pm, disable_web_page_preview=disable_web_page_preview,
            reply_markup=rkm,
        )
    except Exception:
        pass


    if msg is None:
        try:
            msg = await _bot.edit_message_caption(
                chat_id=chat_id, message_id=message_id, caption=text,
                parse_mode=pm, reply_markup=rkm,
            )
        except Exception as e:
            logger.warning(f"smart_edit_message_text: both Pyrogram paths failed: {e}")
            return None


    if msg and reply_markup:
        try:
            await edit_reply_markup_colored(
                chat_id, message_id, reply_markup, token=getattr(_bot, "bot_token", None)
            )
        except Exception:
            pass
    return msg


async def smart_edit_reply_markup(
    chat_id: Union[int, str],
    message_id: int,
    reply_markup: List[List[Dict]],
):
    """Edit ONLY the buttons of a message with colors preserved.

    Bot API editMessageReplyMarkup keeps 'style' field. Pyrogram fallback loses colors.
    """
    from IotaXMedia.core.call import resolve_app


    _bot = resolve_app(chat_id)

    try:
        data = await edit_reply_markup_colored(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
            token=getattr(_bot, "bot_token", None),
        )
        if data:
            return data
    except Exception as e:
        logger.debug(f"smart_edit_reply_markup Bot API path failed: {e}")

    try:
        return await _bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=buttons_to_inline_markup(reply_markup) if reply_markup else None,
        )
    except Exception as e:
        logger.warning(f"smart_edit_reply_markup both paths failed: {e}")
        return None


async def smart_edit_message_caption(
    chat_id: Union[int, str],
    message_id: int,
    caption: str,
    reply_markup: Optional[List[List[Dict]]] = None,
    parse_mode: str = "HTML",
):
    """Edit caption/text message via Pyrogram (proper HTML) then apply colored buttons via Bot API."""
    from IotaXMedia.core.call import resolve_app
    from pyrogram import enums


    _bot = resolve_app(chat_id)

    pm = enums.ParseMode.HTML if parse_mode == "HTML" else enums.ParseMode.MARKDOWN
    rkm = buttons_to_inline_markup(reply_markup) if reply_markup else None


    msg = None
    try:
        msg = await _bot.edit_message_caption(
            chat_id=chat_id, message_id=message_id, caption=caption,
            parse_mode=pm, reply_markup=rkm,
        )
    except Exception:
        pass


    if msg is None:
        try:
            msg = await _bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=caption,
                parse_mode=pm, reply_markup=rkm,
            )
        except Exception as e:
            logger.warning(f"smart_edit_message_caption: both Pyrogram paths failed: {e}")
            return None


    if msg and reply_markup:
        try:
            await edit_reply_markup_colored(
                chat_id, message_id, reply_markup, token=getattr(_bot, "bot_token", None)
            )
        except Exception:
            pass
    return msg


async def send_with_colors(
    chat_id: Union[int, str],
    text: Optional[str] = None,
    photo: Optional[str] = None,
    btns_col: Optional[List[List[Dict]]] = None,
    btns_fb: Optional[InlineKeyboardMarkup] = None,
    reply_to_message_id: Optional[int] = None,
):
    """Send message/photo via Pyrogram (proper HTML), then apply colored buttons via Bot API.

    Two-step strategy:
      1. Send via Pyrogram (handles HTML perfectly, photos, tg:// links)
      2. Edit reply_markup via Bot API HTTP to add style colors
    """
    from IotaXMedia.core.call import resolve_app


    _bot = resolve_app(chat_id)

    markup_source = btns_fb if btns_fb is not None else btns_col
    markup = buttons_to_inline_markup(markup_source) if markup_source else None
    msg = None
    if photo:
        msg = await _bot.send_photo(
            chat_id, photo=photo, caption=text or "",
            reply_markup=markup,
            reply_to_message_id=reply_to_message_id,
        )
    elif text:
        msg = await _bot.send_message(
            chat_id, text or "", reply_markup=markup,
            reply_to_message_id=reply_to_message_id,
        )
    if msg and btns_col:
        try:
            await edit_reply_markup_colored(
                chat_id, msg.id, btns_col, token=getattr(_bot, "bot_token", None)
            )
        except Exception:
            pass
    return msg






