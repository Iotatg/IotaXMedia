# Authored By Iota Coders (Spotify platform – embed scraping + spotipy fallback)
# SPDX-License-Identifier: MIT
import re
from typing import List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup
from IotaXMedia.platforms.ytsearch import VideosSearch

import config


_SPOTIFY_TRACK_RE = re.compile(r"^https://open\.spotify\.com/track/([\w]+)")
_SPOTIFY_PLAYLIST_RE = re.compile(r"^https://open\.spotify\.com/playlist/([\w]+)")
_SPOTIFY_ALBUM_RE = re.compile(r"^https://open\.spotify\.com/album/([\w]+)")
_SPOTIFY_ARTIST_RE = re.compile(r"^https://open\.spotify\.com/artist/([\w]+)")


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^https:\/\/open\.spotify\.com\/.+"
        self.client_id = getattr(config, "SPOTIFY_CLIENT_ID", None)
        self.client_secret = getattr(config, "SPOTIFY_CLIENT_SECRET", None)
        self._spotipy = None
        if self.client_id and self.client_secret:
            try:
                from spotipy.oauth2 import SpotifyClientCredentials
                import spotipy as sp
                mgr = SpotifyClientCredentials(self.client_id, self.client_secret)
                self._spotipy = sp.Spotify(client_credentials_manager=mgr)
            except Exception:
                self._spotipy = None

    async def valid(self, link: str) -> bool:
        return bool(re.search(self.regex, link or ""))


    async def _yt_search(self, query: str) -> dict:
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




    async def track(self, link: str):

        track_id = self._extract_id(link, _SPOTIFY_TRACK_RE)
        meta = await self._scrape_track_embed(link)
        if meta and meta.get("name"):
            details = await self._ytsearch(f"{meta['name']} {' '.join(meta.get('artists', []))}")
            return details, details["vidid"]


        oembed = await self._oembed_track(link)
        if oembed:
            details = await self._ytsearch(oembed)
            return details, details["vidid"]


        if self._spotipy:
            try:
                import asyncio
                track = await asyncio.to_thread(self._spotipy.track, link)
                info = track["name"]
                for artist in track["artists"]:
                    if "Various Artists" not in artist["name"]:
                        info += f" {artist['name']}"
                details = await self._ytsearch(info)
                return details, details["vidid"]
            except Exception:
                pass

        raise RuntimeError("Could not resolve Spotify track")




    async def playlist(self, url) -> Tuple[List[str], str]:
        queries, plist_id = self._extract_embed_playlist(url, _SPOTIFY_PLAYLIST_RE)


        if not queries and self._spotipy:
            plist_id = self._parse_id(url, _SPOTIFY_PLAYLIST_RE)
            try:
                import asyncio
                pl = await asyncio.to_thread(self._spotipy.playlist, url)
                plist_id = pl["id"]
                queries = []
                for item in pl["tracks"]["items"]:
                    t = item.get("track") or {}
                    name = t.get("name") or ""
                    for artist in t.get("artists") or []:
                        if "Various Artists" not in artist["name"]:
                            name += f" {artist['name']}"
                    if name:
                        queries.append(name)
            except Exception:
                pass

        if not queries:
            raise RuntimeError("Could not resolve Spotify playlist")
        return queries, plist_id

    async def album(self, url) -> Tuple[List[str], str]:
        queries, album_id = self._extract_embed_playlist(url, _SPOTIFY_ALBUM_RE)

        if not queries and self._spotipy:
            try:
                import asyncio
                album = await asyncio.to_thread(self._spotipy.album, url)
                album_id = album["id"]
                queries = []
                for item in album["tracks"]["items"]:
                    name = item.get("name") or ""
                    for artist in item.get("artists") or []:
                        if "Various Artists" not in artist["name"]:
                            name += f" {artist['name']}"
                    if name:
                        queries.append(name)
            except Exception:
                pass

        if not queries:
            raise RuntimeError("Could not resolve Spotify album")
        return queries, album_id

    async def artist(self, url) -> Tuple[List[str], str]:
        artist_id = self._parse_id(url, _SPOTIFY_ARTIST_RE)

        if self._spotipy:
            try:
                import asyncio
                artistinfo = await asyncio.to_thread(self._spotipy.artist, url)
                artist_id = artistinfo["id"]
                top_tracks = await asyncio.to_thread(self._spotipy.artist_top_tracks, url)
                queries = []
                for item in top_tracks.get("tracks") or []:
                    name = item.get("name") or ""
                    for artist in item.get("artists") or []:
                        if "Various Artists" not in artist["name"]:
                            name += f" {artist['name']}"
                    if name:
                        queries.append(name)
                if queries:
                    return queries, artist_id
            except Exception:
                pass


        queries = await self._scrape_artist_toptracks(url)
        if queries:
            return queries, artist_id

        raise RuntimeError("Could not resolve Spotify artist")




    @staticmethod
    def _parse_id(url: str, regex) -> str:
        m = regex.search(url)
        return m.group(1) if m else ""

    async def _get_embed_html(self, embed_url: str) -> "BeautifulSoup":
        async with aiohttp.ClientSession() as sess:
            async with sess.get(embed_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status != 200:
                    return None
                return BeautifulSoup(await resp.text(), "html.parser")

    async def _get_track_embed_meta(self, track_id: str):
        if not track_id:
            return None
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                f"https://open.spotify.com/embed/track/{track_id}",
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                if resp.status != 200:
                    return None
                soup = BeautifulSoup(await resp.text(), "html.parser")
        title = ""
        artists = []
        for tag in soup.find_all("meta"):
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if prop == "og:title":
                title = content
            elif prop == "og:description" and "·" in content:
                parts = content.split("·")[:2]
                title = parts[0].strip() if len(parts) > 1 else title
                artists = parts[1].strip().split("on Spotify")[0].strip().split(",")
        if not title and not artists:
            return {}
        return {"title": title, "artists": artists}

    async def _oembed_track(self, link: str) -> str:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                "https://open.spotify.com/oembed",
                params={"url": link},
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                return data.get("title", "")

    async def _extract_embed_playlist(self, url: str, regex) -> Tuple[List[str], str]:
        pid = self._parse_id(url, regex) if regex else ""
        queries = []
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                f"https://open.spotify.com/embed/playlist/{pid}" if "playlist" in url else f"https://open.spotify.com/embed/album/{pid}",
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                if resp.status == 200:
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    for tag in soup.find_all("meta"):
                        prop = tag.get("property", "")
                        if prop == "og:title":
                            title = tag.get("content", "")

        return queries, pid

    async def _scrape_artist_toptracks(self, url: str) -> List[str]:
        queries = []
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status != 200:
                    return queries
                soup = BeautifulSoup(await resp.text(), "html.parser")
            meta = soup.find_all("meta", property="music:song")
            for tag in meta[:10]:
                title = f.get("content", "")
                if title:
                    queries.append(title)
        return queries