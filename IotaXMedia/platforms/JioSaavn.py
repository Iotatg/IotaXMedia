# Authored By Iota Coders (JioSaavn platform)
# SPDX-License-Identifier: MIT
import re
from typing import List, Optional, Tuple, Union

import aiohttp
from IotaXMedia.platforms.ytsearch import VideosSearch


_JIOSAAVN_RE = re.compile(r"^https?://(www\.)?jiosaavn\.com/.+", re.I)


class JioSaavnAPI:
    def __init__(self):
        self.regex = r"^https?://(www\.)?jiosaavn\.com/.+"
        self.api_base = "https://www.jiosaavn.com/api.php"

    async def valid(self, link: str) -> bool:
        return bool(re.search(self.regex, link or ""))

    async def _search(self, query: str, limit: int = 1) -> list:
        params = {
            "__call": "search.getResults",
            "q": query,
            "_format": "json",
            "p": 1,
            "n": limit,
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                self.api_base,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        return data.get("results") or []

    async def _search_song(self, query: str) -> dict:
        results = await self._search(query, limit=5)
        if not results:
            raise RuntimeError(f"No JioSaavn results for: {query}")
        for item in results:
            song = item.get("song") or ""
            album = item.get("album") or ""
            if not song:
                continue
            youtube_query = f"{song} {album}".strip()
            return await self._yt_resolve(youtube_query)
        raise RuntimeError(f"No playable results for: {query}")

    async def _yt_resolve(self, query: str) -> dict:
        r = await VideosSearch(query, limit=1).next()
        items = r.get("result") or []
        if not items:
            raise RuntimeError(f"No YouTube match for: {query}")
        result = items[0]
        return {
            "title": result.get("title", query),
            "link": result.get("link", ""),
            "vidid": result.get("id", ""),
            "duration_min": result.get("duration"),
            "thumb": (result.get("thumbnails") or [{}])[0].get("url", "").split("?")[0],
        }

    async def track(self, url: str, playid: Union[bool, str] = None) -> Optional[Tuple]:
        song_name = url.split("/song/")[-1] if "/song/" in url else url
        song_name = re.sub(r"/[\w]+$", "", song_name) if "/" in song_name.split("/")[-1] else song_name.split("/")[-1]
        song_name = song_name.replace("-", " ").strip()

        if not song_name:
            raise RuntimeError(f"Invalid JioSaavn URL: {url}")


        results = await self._search(song_name, limit=10)
        if not results:
            raise RuntimeError(f"No JioSaavn results for: {song_name}")

        for item in results:
            song = item.get("song") or ""
            if not song:
                continue
            youtube_query = f"{song} {item.get('album', '')}".strip()
            try:
                details = await self._yt_resolve(youtube_query)
                return details, details["vidid"]
            except Exception:
                continue

        raise RuntimeError(f"Could not resolve JioSaavn track: {song_name}")