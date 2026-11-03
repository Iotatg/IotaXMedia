# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from config import YOUTUBE_IMG_URL, youtube_thumb


def _is_valid_thumb_url(url: str) -> bool:
    if not url or not str(url).startswith("http"):
        return False
    if "telegra.ph/file/2c6d1a6f78eba6199933a" in url:
        return False
    return True


async def get_thumb(videoid: str, fallback_url: str | None = None) -> str:
    """
    Return the track's real platform thumbnail URL (YouTube / Spotify / etc.)
    directly. No branding or generated card is applied.
    """
    videoid = (videoid or "").strip()
    if len(videoid) == 11:
        thumbnail = youtube_thumb(videoid, "hqdefault")
    elif _is_valid_thumb_url(fallback_url or ""):
        thumbnail = str(fallback_url).split("?")[0]
    else:
        thumbnail = YOUTUBE_IMG_URL
    return thumbnail
