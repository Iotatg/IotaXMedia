# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone customization — start/ping/stats media, custom messages, channel &
support links, string session override, per-clone MongoDB, chatbot
personality and bot display name. Everything lives in the shared clone
settings collection so the parent process can read/modify it and the child
process can sync from Mongo on boot.
"""
from __future__ import annotations

from typing import Any, List, Optional

from .db import get_clone_setting, set_clone_setting, del_clone_setting


def _clone_id(token_or_id: str) -> str:
    """Normalize either a bot token or a telegram bot-id into the clone id."""
    if not token_or_id:
        return ""
    s = str(token_or_id).strip()
    return s









_MEDIA_TYPES = ("photo", "video", "animation", "document")


def media_payload(file_id: str, media_type: Optional[str] = None):
    """Build the storable value: a typed dict when possible, else a bare string."""
    fid = str(file_id).strip() if file_id else ""
    if not fid:
        return None
    mtype = str(media_type or "").strip().lower()
    if mtype in _MEDIA_TYPES:
        return {"file_id": fid, "type": mtype}
    return fid


def parse_media(value) -> tuple:
    """Normalize any stored/mirrored media value into (media_type, file_id).

    ``media_type`` is None for legacy bare strings (senders then assume photo).
    ``file_id`` is None when there is nothing usable stored.
    """
    if not value:
        return None, None
    if isinstance(value, dict):
        fid = str(value.get("file_id") or "").strip() or None
        mtype = str(value.get("type") or "").strip().lower()
        return (mtype if mtype in _MEDIA_TYPES else None), fid
    fid = str(value).strip()
    return None, (fid or None)


async def get_start_media(clone_id: str) -> Any:
    """Raw stored start media: legacy bare string or typed dict (see parse_media)."""
    return await get_clone_setting(_clone_id(clone_id), "start_media")


async def set_start_media(
    clone_id: str, file_id: str, media_type: Optional[str] = None
) -> Any:
    """Store start media; returns the value written (None if cleared)."""
    payload = media_payload(file_id, media_type)
    if payload is None:
        await del_start_media(clone_id)
        return None
    await set_clone_setting(_clone_id(clone_id), "start_media", payload)
    return payload


async def del_start_media(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "start_media")


async def get_start_message(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "start_message")


async def set_start_message(clone_id: str, text: str) -> None:
    if not text:
        await del_start_message(clone_id)
        return
    await set_clone_setting(_clone_id(clone_id), "start_message", str(text))


async def del_start_message(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "start_message")



async def get_ping_media(clone_id: str) -> Any:
    """Raw stored ping media: legacy bare string or typed dict (see parse_media)."""
    return await get_clone_setting(_clone_id(clone_id), "ping_media")


async def set_ping_media(
    clone_id: str, file_id: str, media_type: Optional[str] = None
) -> Any:
    """Store ping media; returns the value written (None if cleared)."""
    payload = media_payload(file_id, media_type)
    if payload is None:
        await del_ping_media(clone_id)
        return None
    await set_clone_setting(_clone_id(clone_id), "ping_media", payload)
    return payload


async def del_ping_media(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "ping_media")



async def get_stats_media(clone_id: str) -> Any:
    """Raw stored stats media: legacy bare string or typed dict (see parse_media)."""
    return await get_clone_setting(_clone_id(clone_id), "stats_media")


async def set_stats_media(
    clone_id: str, file_id: str, media_type: Optional[str] = None
) -> Any:
    """Store stats media; returns the value written (None if cleared)."""
    payload = media_payload(file_id, media_type)
    if payload is None:
        await del_stats_media(clone_id)
        return None
    await set_clone_setting(_clone_id(clone_id), "stats_media", payload)
    return payload


async def del_stats_media(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "stats_media")



async def get_clone_channel(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "channel_link")


async def set_clone_channel(clone_id: str, link: str) -> None:
    if not link:
        await del_clone_setting(_clone_id(clone_id), "channel_link")
        return
    await set_clone_setting(_clone_id(clone_id), "channel_link", str(link))


async def get_clone_support(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "support_link")


async def set_clone_support(clone_id: str, link: str) -> None:
    if not link:
        await del_clone_setting(_clone_id(clone_id), "support_link")
        return
    await set_clone_setting(_clone_id(clone_id), "support_link", str(link))


async def set_clone_string(clone_id: str, session: str) -> bool:
    """Returns False if session string is empty.
    NOTE: validation (sign-in attempt) happens inside the child process."""
    if not session:
        await del_clone_string(clone_id)
        return False
    await set_clone_setting(_clone_id(clone_id), "string_session", str(session))
    return True


async def del_clone_string(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "string_session")


async def set_clone_mongo(clone_id: str, uri: str) -> bool:
    if not uri:
        await del_clone_mongo(clone_id)
        return False
    await set_clone_setting(_clone_id(clone_id), "mongo_uri", str(uri))
    return True


async def del_clone_mongo(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "mongo_uri")



async def get_clone_chatbot(clone_id: str) -> bool:
    return bool(await get_clone_setting(_clone_id(clone_id), "chatbot", False))


async def set_clone_chatbot(clone_id: str, enabled: bool) -> None:
    await set_clone_setting(_clone_id(clone_id), "chatbot", bool(enabled))


async def get_clone_name(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "display_name")


async def set_clone_name(clone_id: str, name: str) -> None:
    if not name:
        await del_clone_setting(_clone_id(clone_id), "display_name")
        return
    await set_clone_setting(_clone_id(clone_id), "display_name", str(name))



async def set_clone_logger(clone_id: str, chat_id) -> None:
    await set_clone_setting(_clone_id(clone_id), "log_chat", str(chat_id))


async def del_clone_logger(clone_id: str) -> None:
    await del_clone_setting(_clone_id(clone_id), "log_chat")


async def get_clone_channel_name(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "channel_name")


async def set_clone_channel_name(clone_id: str, name: str) -> None:
    await set_clone_setting(_clone_id(clone_id), "channel_name", name.strip())


async def del_clone_channel_name(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "channel_name")


async def get_clone_support_name(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "support_name")


async def set_clone_support_name(clone_id: str, name: str) -> None:
    await set_clone_setting(_clone_id(clone_id), "support_name", name.strip())


async def del_clone_support_name(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "support_name")


async def get_clone_owner_name(clone_id: str) -> Optional[str]:
    return await get_clone_setting(_clone_id(clone_id), "owner_name")


async def set_clone_owner_name(clone_id: str, name: str) -> None:
    await set_clone_setting(_clone_id(clone_id), "owner_name", name.strip())


async def del_clone_owner_name(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "owner_name")


async def is_btn_enabled(clone_id: str, key: str) -> bool:
    value = await get_clone_setting(_clone_id(clone_id), f"btn_{key}", True)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("0", "false", "off", "no")


async def set_btn_enabled(clone_id: str, key: str, enabled: bool) -> None:
    await set_clone_setting(_clone_id(clone_id), f"btn_{key}", bool(enabled))


async def get_extra_buttons(clone_id: str) -> List[dict]:
    value = await get_clone_setting(_clone_id(clone_id), "extra_buttons", [])
    if isinstance(value, list):
        return [b for b in value if isinstance(b, dict) and b.get("name") and b.get("url")]
    return []


async def add_extra_button(clone_id: str, name: str, url: str) -> None:
    buttons = await get_extra_buttons(clone_id)
    name = name.strip()
    url = url.strip()
    buttons = [b for b in buttons if str(b.get("name", "")).lower() != name.lower()]
    buttons.append({"name": name[:32], "url": url[:256]})
    await set_clone_setting(_clone_id(clone_id), "extra_buttons", buttons[:12])


async def del_extra_button(clone_id: str, name: str) -> bool:
    buttons = await get_extra_buttons(clone_id)
    kept = [b for b in buttons if str(b.get("name", "")).lower() != name.strip().lower()]
    if len(kept) == len(buttons):
        return False
    await set_clone_setting(_clone_id(clone_id), "extra_buttons", kept)
    return True


async def clear_extra_buttons(clone_id: str) -> bool:
    return await del_clone_setting(_clone_id(clone_id), "extra_buttons")
