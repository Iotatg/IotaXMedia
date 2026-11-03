# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from typing import Optional

from IotaXMedia.utils.cache import TTLCache

_lang_cache: TTLCache = TTLCache(256, 1800)


async def get_chat_lang(chat_id: int) -> Optional[str]:
    cached = _lang_cache.get(chat_id)
    if cached is not None:
        return cached
    try:
        from IotaXMedia.core.mongo import mongodb

        doc = await mongodb.translate.find_one({"chat_id": chat_id}, {"lang": 1})
        lang = str(doc["lang"]) if doc and doc.get("lang") else None
    except Exception:
        lang = None
    _lang_cache[chat_id] = lang
    return lang


async def set_chat_lang(chat_id: int, lang: Optional[str]) -> None:
    try:
        from IotaXMedia.core.mongo import mongodb

        if lang:
            await mongodb.translate.update_one(
                {"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True
            )
        else:
            await mongodb.translate.delete_one({"chat_id": chat_id})
    except Exception:
        pass
    _lang_cache[chat_id] = lang


async def translate(text: str, to_lang: str) -> Optional[str]:
    """Translate text via MTProto messages.translateText. Returns None on failure."""
    if not text or not to_lang:
        return None
    try:
        from IotaXMedia import app

        res = await app.translate_text(text=text, to_language=to_lang)
        out = getattr(res, "result", None)
        return out if out and out != text else None
    except Exception:
        return None
