# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""GIPHY-backed GIF provider for mood replies (ported from iota)."""
import logging
import random
import time

import aiohttp

from config import GIPHY_API_KEY as _CONFIGURED_KEY

logger = logging.getLogger(__name__)

_PUBLIC_DEMO_KEY = "dc6zaTOxFJmzC"
GIPHY_API_KEY = _CONFIGURED_KEY or _PUBLIC_DEMO_KEY
GIPHY_SEARCH_URL = "https://api.giphy.com/v1/gifs/search"

_cache: dict = {}
_CACHE_TTL = 600

_SEARCH_TERMS = {
    "happy": "anime happy excited",
    "sad": "anime sad crying",
    "love": "anime love heart cute",
    "laugh": "anime laughing lol",
    "angry": "anime angry mad rage",
    "cute": "anime cute aww",
    "dance": "anime dance happy",
    "cool": "anime cool sunglasses",
    "surprise": "anime surprised shocked",
    "default": "anime wave hello",
    "slap": "anime slap",
    "punch": "anime punch",
    "kiss": "anime kiss",
    "hug": "anime hug",
    "bite": "anime bite",
    "pat": "anime head pat",
    "welcome": "anime welcome wave",
    "funny": "funny meme reaction",
}


async def _giphy_search(query: str, limit: int = 20) -> list:
    now = time.time()
    cached = _cache.get(query)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    try:
        async with aiohttp.ClientSession() as s:
            params = {
                "q": query,
                "api_key": GIPHY_API_KEY,
                "limit": limit,
                "rating": "pg-13",
                "lang": "en",
            }
            async with s.get(
                GIPHY_SEARCH_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=6),
            ) as r:
                if r.status != 200:
                    return []
                data = await r.json()
    except Exception as e:
        logger.debug(f"GIPHY search failed for '{query}': {e}")
        return []

    urls = []
    for item in data.get("data", []):
        try:
            gif_url = (
                item.get("images", {}).get("downsized", {}).get("url")
                or item.get("images", {}).get("original", {}).get("url")
            )
            if gif_url:
                urls.append(gif_url)
        except (KeyError, TypeError, AttributeError):
            continue

    if urls:
        _cache[query] = (now, urls)
    return urls


async def get_gif_for_mood(mood: str):
    query = _SEARCH_TERMS.get(mood, _SEARCH_TERMS["default"])
    try:
        urls = await _giphy_search(query)
        if urls:
            return random.choice(urls)
    except Exception as e:
        logger.debug(f"get_gif_for_mood error for '{mood}': {e}")
    return None
