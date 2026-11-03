# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Async client for the nubcoders YT-DLP wrapper API.

Public service: https://api.nubcoders.com — sign up via the Telegram bot to
get a personal token. Quota: 1,000 req/day on ``/info`` (the download/stream
endpoint); ``/search`` is free & unlimited. Token validity: 28 days.

Endpoints used:
- GET ``/info?token=…&q=URL_OR_QUERY`` → video metadata + ``stream_url`` +
  ``suggested[]`` (related tracks, replaces the old Innertube YTM radio).
- GET ``/search?q=…&max_results=…``     → free search (no token, scrape-based).
- GET ``/rate-limit-status?token=…``    → quota check.
- GET ``/health``                       → service health (no token).

The ``stream_url`` is a long-lived resolver link (verified stable for
5+ minutes); it can be handed straight to PyTgCalls/ffmpeg as a remote
media source — no local download required.
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


def _mask_key(key: Optional[str]) -> str:
    if not key:
        return "<unset>"
    if len(key) <= 10:
        return key[:2] + "***"
    return f"{key[:6]}…{key[-4:]}"


class NubApi:
    """Thin async wrapper around api.nubcoders.com.

    Falls back gracefully when the token is missing: every method returns
    ``None`` / ``[]`` instead of raising, so callers can keep using their
    existing Shruti / Inflex / yt-dlp fallbacks without try/except noise.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str,
        *,
        timeout: int = 30,
    ):
        self.base = api_url.rstrip("/") or "https://api.nubcoders.com"
        self.api_key = api_key or ""
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def enabled(self) -> bool:
        """True when a token is configured — feature is opt-in via env."""
        return bool(self.api_key)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            session = await self._get_session()
            url = f"{self.base}{path}"
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(
                        "[NUB] %s HTTP %d (key=%s)", path, resp.status, _mask_key(self.api_key)
                    )
                    return None
                return await resp.json(content_type=None)
        except Exception as e:
            logger.warning("[NUB] %s exception: %s", path, e)
            return None

    async def get_info(self, url_or_query: str) -> Optional[Dict[str, Any]]:
        """Return full info dict for a YouTube URL or search query.

        Result includes at least: ``stream_url``, ``title``, ``duration``,
        ``channel_name``, ``video_id``, ``thumbnail``, ``youtube_link`` and
        ``suggested[]`` (related tracks — replaces YTM Innertube radio).
        """
        return await self._get(
            "/info", {"token": self.api_key, "q": url_or_query, "max_results": 1}
        )

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Free text search — no token consumed, returns a list of videos.

        Each item has at least: ``title``, ``video_id``, ``url``, ``channel``,
        ``duration`` / ``time``, ``thumbnail``.
        """
        if not query:
            return []
        try:
            session = await self._get_session()
            url = f"{self.base}/search"
            async with session.get(
                url, params={"q": query, "max_results": max_results}
            ) as resp:
                if resp.status != 200:
                    logger.warning("[NUB] /search HTTP %d", resp.status)
                    return []
                data = await resp.json(content_type=None)
            return list(data.get("results") or [])
        except Exception as e:
            logger.warning("[NUB] /search exception: %s", e)
            return []

    async def get_rate_limit(self) -> Optional[Dict[str, Any]]:
        """Quota snapshot — ``requests_used`` / ``daily_limit`` / ``remaining``."""
        return await self._get("/rate-limit-status", {"token": self.api_key})


def extract_vid_from_url(url: str) -> Optional[str]:
    """Pull an 11-char YouTube video id out of a ``youtube.com/watch?v=…``
    or ``youtu.be/…`` URL. Returns ``None`` if no id found.
    """
    import re

    if not url:
        return None
    m = re.search(
        r"(?:v=|/shorts/|youtu\.be/|/embed/|/v/|/live/)([A-Za-z0-9_-]{11})",
        url,
    )
    return m.group(1) if m else None
