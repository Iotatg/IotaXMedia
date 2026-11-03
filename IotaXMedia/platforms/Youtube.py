# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import contextlib
import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple, Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from IotaXMedia.platforms.ytsearch import VideosSearch, Playlist

from IotaXMedia.utils.cookie_handler import resolve_cookie_path
from IotaXMedia.core.dir import DOWNLOAD_DIR
from IotaXMedia.utils.database import is_on_off
from IotaXMedia.utils.downloader import yt_dlp_download, download_direct
from IotaXMedia.utils.errors import capture_internal_err
from IotaXMedia.utils.formatters import normalize_duration, time_to_seconds
from IotaXMedia.utils.tuning import YTDLP_TIMEOUT, YOUTUBE_META_MAX, YOUTUBE_META_TTL
from IotaXMedia.utils.api_retry import retry_tg
from IotaXMedia.utils.cache import mongo_cache_get, mongo_cache_set
from config import YT_API_KEY, YTPROXY_URL
import requests
import aiohttp
import logging

logger = logging.getLogger(__name__)



SHRUTI_API_URL = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site")
SHRUTI_API_KEY = os.environ.get("SHRUTI_API_KEY", "ShrutiBotsgBDkKisTQy4dawsleMKu")
YUKI_API_URL = os.environ.get("YUKI_API_URL", "https://music.yukiapi.site")
YUKI_API_KEY = os.environ.get("YUKI_API_KEY", "")



_cache: Dict[str, Tuple[float, List[Dict]]] = {}
_cache_lock = asyncio.Lock()
_formats_cache: Dict[str, Tuple[float, List[Dict], str]] = {}
_formats_lock = asyncio.Lock()



YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")



def _cookiefile_path() -> Optional[str]:
    """Temp copy of cookies so CLI yt-dlp cannot rewrite the master file."""
    try:
        import shutil
        import tempfile

        src = resolve_cookie_path()
        if not src:
            return None
        fd, tmp = tempfile.mkstemp(prefix="yt_cookies_cli_", suffix=".txt")
        os.close(fd)
        shutil.copy2(src, tmp)
        return tmp
    except Exception:
        pass
    return None


def _cookies_args() -> List[str]:
    path = _cookiefile_path()
    if path:
        return ["--cookies", path]
    return []


def _js_runtime_args() -> List[str]:
    import shutil

    home = os.path.expanduser("~/.deno/bin/deno")
    deno = home if os.path.isfile(home) else shutil.which("deno")
    if deno:
        return ["--js-runtimes", f"deno:{deno}"]
    return []


async def _exec_proc(*args: str) -> Tuple[bytes, bytes]:

    argv = list(args)
    if argv and argv[0] == "yt-dlp":
        argv = ["python3", "-m", "yt_dlp", *argv[1:]]
    env = os.environ.copy()
    deno_home = os.path.expanduser("~/.deno/bin")
    if os.path.isdir(deno_home):
        env["PATH"] = deno_home + os.pathsep + env.get("PATH", "")
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    try:
        return await asyncio.wait_for(proc.communicate(), timeout=YTDLP_TIMEOUT)
    except asyncio.TimeoutError:
        with contextlib.suppress(Exception):
            proc.kill()
        return b"", b"timeout"



def _youtube_api_video(video_id: str) -> Optional[Dict]:
    """Fetch video metadata via YouTube Data API v3 using YT_API_KEY."""
    try:
        if not YT_API_KEY or YT_API_KEY.startswith("AIzaSy") is False:
            return None
        url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,contentDetails,statistics,status&key={YT_API_KEY}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None
        item = items[0]
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})
        stats = item.get("statistics", {})
        duration_raw = content_details.get("duration", "PT0S")

        import re as _re
        match = _re.search(r"PT(\d+H)?(\d+M)?(\d+S)?", duration_raw)
        total_sec = 0
        if match:
            h = int(match.group(1)[:-1]) if match.group(1) else 0
            m = int(match.group(2)[:-1]) if match.group(2) else 0
            s = int(match.group(3)[:-1]) if match.group(3) else 0
            total_sec = h * 3600 + m * 60 + s
        duration_min = f"{total_sec // 60}:{total_sec % 60:02d}" if total_sec > 0 else None
        thumbs = snippet.get("thumbnails", {})
        thumb = (thumbs.get("high", {}) or thumbs.get("default", {})).get("url", "")
        return {
            "title": snippet.get("title", ""),
            "id": video_id,
            "duration": duration_raw,
            "duration_sec": total_sec,
            "duration_min": duration_min,
            "thumbnail": thumb,
            "channelTitle": snippet.get("channelTitle", ""),
        }
    except Exception:
        return None


def _youtube_api_search(query: str, max_results: int = 5) -> List[Dict]:
    """Search YouTube via Data API v3."""
    try:
        if not YT_API_KEY or YT_API_KEY.startswith("AIzaSy") is False:
            return []
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={requests.utils.quote(query)}&type=video&maxResults={max_results}&key={YT_API_KEY}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        results = []
        for item in items:
            vid_id = item.get("id", {}).get("videoId", "")
            if not vid_id:
                continue
            snippet = item.get("snippet", {})
            results.append({"id": vid_id, "title": snippet.get("title", ""), "channelTitle": snippet.get("channelTitle", "")})
        return results
    except Exception:
        return []


async def _ytdlp_dump_json(target: str, *, flat: bool = False) -> Optional[Dict]:
    """Reliable metadata via yt-dlp (cookies + deno)."""
    args = [
        "yt-dlp",
        *(_cookies_args()),
        *(_js_runtime_args()),
        "--dump-json",
        "--no-warnings",
        "--no-update",
        "--skip-download",
        "--socket-timeout",
        "25",
    ]
    if YTPROXY_URL:
        args += ["--proxy", YTPROXY_URL]
    if flat:
        args.append("--flat-playlist")
    args.append(target)
    stdout, stderr = await _exec_proc(*args)
    if not stdout:
        return None
    try:
        first = stdout.decode(errors="ignore").strip().splitlines()[0]
        return json.loads(first)
    except Exception:
        return None


@capture_internal_err
async def cached_youtube_search(query: str) -> List[Dict]:
    key = f"q:{query}"
    now = time.time()


    cached = await mongo_cache_get(f"yt:{key}")
    if cached:
        return cached

    async with _cache_lock:
        if key in _cache:
            ts, val = _cache[key]
            if now - ts < YOUTUBE_META_TTL:
                return val
            _cache.pop(key, None)
        if len(_cache) > YOUTUBE_META_MAX:
            _cache.clear()

    result: List[Dict] = []
    try:
        data = await retry_tg()(VideosSearch(query, limit=1).next)()
        result = data.get("result", []) or []
    except Exception:
        result = []


    if not result:
        info = await _ytdlp_dump_json(f"ytsearch1:{query}", flat=True)
        if info:
            result = [info]

    if result:
        async with _cache_lock:
            _cache[key] = (now, result)
        await mongo_cache_set(f"yt:{key}", result, ttl=YOUTUBE_META_TTL)

    return result


async def youtube_search_multi(query: str, limit: int = 8) -> List[Dict]:
    """Multi-result YouTube search used by autoplay candidate scoring."""
    try:
        data = await retry_tg()(VideosSearch(query, limit=max(1, int(limit))).next)()
        return data.get("result", []) or []
    except Exception:
        return []



class YouTubeAPI:
    def __init__(self) -> None:
        self.base_url = "https://www.youtube.com/watch?v="
        self.playlist_url = "https://youtube.com/playlist?list="
        self._url_pattern = re.compile(r"(?:youtube\.com|youtu\.be)")

    def _prepare_link(self, link: str, videoid: Union[str, bool, None] = None) -> str:
        if isinstance(videoid, str) and videoid.strip():
            link = self.base_url + videoid.strip()

        link = (link or "").strip()


        if YOUTUBE_ID_RE.fullmatch(link):
            return self.base_url + link

        if "youtu.be" in link:
            link = self.base_url + link.split("/")[-1].split("?")[0]
        elif "youtube.com/shorts/" in link or "youtube.com/live/" in link:
            link = self.base_url + link.split("/")[-1].split("?")[0]
        elif "youtube.com/watch" in link and "v=" in link:
            vid = link.split("v=")[-1].split("&")[0].split("#")[0]
            if YOUTUBE_ID_RE.fullmatch(vid):
                return self.base_url + vid

        return link.split("&")[0]


    @capture_internal_err
    async def exists(self, link: str, videoid: Union[str, bool, None] = None) -> bool:
        return bool(self._url_pattern.search(self._prepare_link(link, videoid)))

    @capture_internal_err
    async def url(self, message: Message) -> Optional[str]:
        msgs = [message] + ([message.reply_to_message] if message.reply_to_message else [])
        for msg in msgs:
            text = msg.text or msg.caption or ""
            entities = (msg.entities or []) + (msg.caption_entities or [])
            for ent in entities:
                if ent.type == MessageEntityType.URL:
                    return text[ent.offset: ent.offset + ent.length].split("&si")[0]
                if ent.type == MessageEntityType.TEXT_LINK:
                    return ent.url.split("&si")[0]
        return None

    async def _ensure_watch_url(self, maybe_query_or_url: str) -> Optional[str]:
        prepared = self._prepare_link(maybe_query_or_url)
        if prepared.startswith("http") and self._url_pattern.search(prepared):
            return prepared
        if prepared.startswith("http"):
            return prepared
        data = await cached_youtube_search(prepared)
        if not data:
            return None
        vid = data[0].get("id")
        return self.base_url + vid if vid else None


    @capture_internal_err
    async def _fetch_video_info(self, query: str, *, use_cache: bool = True) -> Optional[Dict]:
        q = self._prepare_link(query)

        vid_from_url = None
        if q.startswith("http") or YOUTUBE_ID_RE.fullmatch(q.replace(self.base_url, "")):
            vid_candidate = q.replace(self.base_url, "").split("?")[0].split("/")[-1].split("#")[0]
            if YOUTUBE_ID_RE.fullmatch(vid_candidate):
                vid_from_url = vid_candidate

            if vid_from_url:
                api_result = await asyncio.to_thread(_youtube_api_video, vid_from_url)
                if api_result:
                    return api_result

            info = await _ytdlp_dump_json(q if q.startswith("http") else self.base_url + q)
            if info:
                return info

            try:
                target = q if q.startswith("http") else f"ytsearch1:{q}"
                info = await _ytdlp_dump_json(target, flat=not q.startswith("http"))
                if info:
                    return info
                data = await VideosSearch(q, limit=1).next()
                res = data.get("result") or []
                return res[0] if res else None
            except Exception:
                return None
        else:

            api_search_results = await asyncio.to_thread(_youtube_api_search, q, 5)
            if api_search_results:
                first = api_search_results[0]
                vid = first.get("id", "")
                if vid:
                    api_result = await asyncio.to_thread(_youtube_api_video, vid)
                    if api_result:
                        return api_result
                return {
                    "title": api_search_results[0].get("title", ""),
                    "id": api_search_results[0].get("id", ""),
                    "duration": None,
                    "thumbnail": "",
                    "channelTitle": api_search_results[0].get("channelTitle", ""),
                }

        if use_cache:
            res = await cached_youtube_search(q)
            return res[0] if res else None
        data = await VideosSearch(q, limit=1).next()
        result = data.get("result", [])
        return result[0] if result else None

    @capture_internal_err
    async def is_live(self, link: str) -> bool:
        prepared = self._prepare_link(link)
        info = await _ytdlp_dump_json(prepared)
        return bool(info and info.get("is_live"))

    @capture_internal_err
    async def details(
        self, link: str, videoid: Union[str, bool, None] = None
    ) -> Tuple[str, Optional[str], int, str, str]:
        prepared_link = self._prepare_link(link, videoid)
        info = await self._fetch_video_info(prepared_link)
        if not info:
            raise ValueError("Video not found")

        dt = info.get("duration")
        if isinstance(dt, (int, float)):
            total = int(dt)
            dt_str = f"{total // 60}:{total % 60:02d}"
            ds = total
        else:
            dt_str = dt if isinstance(dt, str) else None
            ds = int(time_to_seconds(dt_str)) if dt_str else 0
        thumbs = info.get("thumbnails") or [{}]
        thumb = (
            info.get("thumbnail")
            or (thumbs[-1].get("url") if thumbs else "")
            or ""
        )
        thumb = str(thumb).split("?")[0]
        vid = info.get("id", "")
        if not thumb and vid:
            from config import youtube_thumb
            thumb = youtube_thumb(str(vid))

        return info.get("title", ""), dt_str, ds, thumb, vid

    @capture_internal_err
    async def title(self, link: str, videoid: Union[str, bool, None] = None) -> str:
        info = await self._fetch_video_info(self._prepare_link(link, videoid))
        return info.get("title", "") if info else ""

    @capture_internal_err
    async def duration(self, link: str, videoid: Union[str, bool, None] = None) -> Optional[str]:
        info = await self._fetch_video_info(self._prepare_link(link, videoid))
        return info.get("duration") if info else None

    @capture_internal_err
    async def thumbnail(self, link: str, videoid: Union[str, bool, None] = None) -> str:
        from config import youtube_thumb

        prepared = self._prepare_link(link, videoid)
        info = await self._fetch_video_info(prepared)
        thumb = ""
        if info:
            thumbs = info.get("thumbnails") or [{}]
            thumb = (
                info.get("thumbnail")
                or (thumbs[-1].get("url") if thumbs else "")
                or ""
            )
            thumb = str(thumb).split("?")[0]
            if thumb and "telegra.ph/file/2c6d1a6f78eba6199933a" not in thumb:
                return thumb
            vid = info.get("id") or ""
            if len(str(vid)) == 11:
                return youtube_thumb(str(vid))

        if isinstance(videoid, str) and len(videoid.strip()) == 11:
            return youtube_thumb(videoid.strip())
        m = YOUTUBE_ID_RE.search(prepared.replace("https://www.youtube.com/watch?v=", ""))
        if m:
            return youtube_thumb(m.group(0))
        if prepared.startswith(self.base_url):
            vid = prepared.replace(self.base_url, "")[:11]
            if len(vid) == 11:
                return youtube_thumb(vid)
        return ""

    @capture_internal_err
    async def track(self, link: str, videoid: Union[str, bool, None] = None) -> Tuple[Dict, str]:
        prepared_link = self._prepare_link(link, videoid)

        info = await self._fetch_video_info(prepared_link)
        if not info:

            target = (
                prepared_link
                if prepared_link.startswith("http")
                else f"ytsearch1:{prepared_link}"
            )
            info = await _ytdlp_dump_json(
                target, flat=not prepared_link.startswith("http")
            )
        if not info:
            raise ValueError(f"Could not resolve track: {prepared_link}")

        thumbs = info.get("thumbnails") or [{}]
        thumb_raw = info.get("thumbnail") or (thumbs[-1].get("url") if thumbs else "") or ""
        thumb = str(thumb_raw).split("?")[0]
        vidid = info.get("id", "") or info.get("vidid", "")
        link_out = (
            info.get("webpage_url")
            or info.get("link")
            or info.get("url")
            or (self.base_url + vidid if vidid else prepared_link)
        )
        if link_out and not str(link_out).startswith("http") and vidid:
            link_out = self.base_url + vidid
        if not thumb and vidid:
            from config import youtube_thumb
            thumb = youtube_thumb(str(vidid))
        dur = info.get("duration")
        duration_min = normalize_duration(dur)

        details = {
            "title": info.get("title", ""),
            "link": link_out,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumb,
        }
        return details, vidid


    @capture_internal_err
    async def video(self, link: str, videoid: Union[str, bool, None] = None) -> Tuple[int, str]:
        link = self._prepare_link(link, videoid)

        for fmt in (
            "bestaudio[ext=m4a]/bestaudio/best",
            "best[height<=?720][width<=?1280]/best",
        ):
            args = [
                "yt-dlp",
                *(_cookies_args()),
                *(_js_runtime_args()),
                "-g",
                "-f",
                fmt,
                "--no-warnings",
                "--no-update",
            ]
            if YTPROXY_URL:
                args += ["--proxy", YTPROXY_URL]
            stdout, stderr = await _exec_proc(*args, link)
            if stdout:
                url = stdout.decode().strip().split("\n")[0].strip()
                if url.startswith("http"):
                    return 1, url
        return 0, (stderr.decode() if stderr else "no stream url")

    @capture_internal_err
    async def playlist(
        self, link: str, limit: int, user_id, videoid: Union[str, bool, None] = None
    ) -> List[str]:
        if videoid:
            link = self.playlist_url + str(videoid)
        link = self._prepare_link(link).split("&")[0]

        try:
            plist = await Playlist.get(link)
            items = [video.get("id") for video in plist.get("videos", [])[:limit] if video.get("id")]
            if items:
                return items
        except Exception:
            pass

        stdout, _ = await _exec_proc(
            "yt-dlp",
            *(_cookies_args()), *(_js_runtime_args()),
            "-i",
            "--get-id",
            "--flat-playlist",
            "--playlist-end",
            str(limit),
            "--skip-download",
            link,
        )
        items = stdout.decode().strip().split("\n") if stdout else []
        return [i for i in items if i]

    @capture_internal_err
    async def formats(
        self, link: str, videoid: Union[str, bool, None] = None
    ) -> Tuple[List[Dict], str]:
        link = self._prepare_link(link, videoid)
        key = f"f:{link}"
        now = time.time()

        async with _formats_lock:
            cached = _formats_cache.get(key)
            if cached and now - cached[0] < YOUTUBE_META_TTL:
                return cached[1], cached[2]

        opts = {"quiet": True}
        if cf := _cookiefile_path():
            opts["cookiefile"] = cf

        out: List[Dict] = []
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(link, download=False)
                for fmt in info.get("formats", []):
                    if "dash" in str(fmt.get("format", "")).lower():
                        continue
                    if not any(k in fmt for k in ("filesize", "filesize_approx")):
                        continue
                    if not all(k in fmt for k in ("format", "format_id", "ext", "format_note")):
                        continue
                    size = fmt.get("filesize") or fmt.get("filesize_approx")
                    if not size:
                        continue
                    out.append(
                        {
                            "format": fmt["format"],
                            "filesize": size,
                            "format_id": fmt["format_id"],
                            "ext": fmt["ext"],
                            "format_note": fmt["format_note"],
                            "yturl": link,
                        }
                    )
        except Exception:
            pass

        async with _formats_lock:
            if len(_formats_cache) > YOUTUBE_META_MAX:
                _formats_cache.clear()
            _formats_cache[key] = (now, out, link)

        return out, link

    @capture_internal_err
    async def slider(
        self, link: str, query_type: int, videoid: Union[str, bool, None] = None
    ) -> Tuple[str, Optional[str], str, str]:
        data = await VideosSearch(self._prepare_link(link, videoid), limit=10).next()
        results = data.get("result", [])
        if not results or query_type >= len(results):
            raise IndexError(
                f"Query type index {query_type} out of range (found {len(results)} results)"
            )
        r = results[query_type]
        return (
            r.get("title", ""),
            r.get("duration"),
            r.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
            r.get("id", ""),
        )




    @staticmethod
    def _extract_vid(link: str) -> Optional[str]:
        if YOUTUBE_ID_RE.fullmatch(link or ""):
            return link
        s = link.replace("https://www.youtube.com/watch?v=", "")
        if "v=" in s:
            s = s.split("v=")[-1].split("&")[0].split("#")[0]
        if "youtu.be/" in s:
            s = s.split("youtu.be/")[-1].split("?")[0]
        if YOUTUBE_ID_RE.fullmatch(s):
            return s
        return None

    @staticmethod
    def _cleanup(path: str) -> None:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    async def _shruti_download(self, vid: str, media_type: str, path: str) -> bool:
        tag = media_type.upper()



        for attempt in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{SHRUTI_API_URL}/download",
                        params={"url": vid, "type": media_type, "api_key": SHRUTI_API_KEY},
                        timeout=aiohttp.ClientTimeout(total=300 if media_type == "audio" else 600),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(
                                f"[SHRUTI][{tag}] HTTP {resp.status} for {vid} (attempt {attempt + 1})"
                            )
                            if 400 <= resp.status < 500:
                                return False
                            await asyncio.sleep(1)
                            continue
                        with open(path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(131072):
                                f.write(chunk)
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    logger.info(f"[SHRUTI] {tag} download completed for {vid}")
                    return True
                self._cleanup(path)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[SHRUTI][{tag}] Exception for {vid} (attempt {attempt + 1}): {e}")
                self._cleanup(path)
                await asyncio.sleep(1)
        return False

    async def _yuki_download(self, vid: str, media_type: str, path: str) -> bool:
        tag = media_type.upper()
        if not YUKI_API_URL or not YUKI_API_KEY:
            return False
        quality = "480" if media_type == "video" else "128"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{YUKI_API_URL.rstrip('/')}/stream/{vid}",
                    params={"key": YUKI_API_KEY, "type": media_type, "quality": quality},
                    timeout=aiohttp.ClientTimeout(total=300 if media_type == "audio" else 600),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"[YUKI][{tag}] HTTP {resp.status} for {vid}")
                        return False
                    with open(path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                logger.info(f"[YUKI] {tag} download completed for {vid}")
                return True
            self._cleanup(path)
            return False
        except Exception as e:
            logger.warning(f"[YUKI][{tag}] Exception for {vid}: {e}")
            self._cleanup(path)
            return False

    async def _api_download_audio(self, video_id: str):
        vid = self._extract_vid(video_id) or video_id
        if not vid or len(vid) < 3:
            return None
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        path = os.path.join(DOWNLOAD_DIR, f"{vid}.mp3")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        if await self._shruti_download(vid, "audio", path):
            return path
        if await self._yuki_download(vid, "audio", path):
            return path
        return None

    async def _api_download_video(self, video_id: str):
        vid = self._extract_vid(video_id) or video_id
        if not vid or len(vid) < 3:
            return None
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        path = os.path.join(DOWNLOAD_DIR, f"{vid}.mp4")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        if await self._shruti_download(vid, "video", path):
            return path
        if await self._yuki_download(vid, "video", path):
            return path
        return None

    @capture_internal_err
    async def download(
        self,
        link: str,
        mystic,
        *,
        video: Union[bool, str, None] = None,
        videoid: Union[str, bool, None] = None,
    ) -> Union[Tuple[str, Optional[bool]], Tuple[None, None]]:
        link = self._prepare_link(link, videoid)

        if video:
            if await self.is_live(link):
                status, stream_url = await self.video(link)
                if status == 1:
                    return stream_url, None
                return None, None



            _vid = self._extract_vid(link) or (
                videoid if isinstance(videoid, str) and YOUTUBE_ID_RE.fullmatch(videoid or "") else None
            )
            if _vid:
                _api = await self._api_download_video(_vid)
                if _api:
                    return _api, True


            p = await download_direct(link, "video", await self.title(link))
            if p:
                return p, True

            stdout, _ = await _exec_proc(
                "yt-dlp",
                *(_cookies_args()), *(_js_runtime_args()),
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                link,
            )
            if stdout:
                return stdout.decode().split("\n")[0], None
            return None, None



        _vid = self._extract_vid(link) or (
            videoid if isinstance(videoid, str) and YOUTUBE_ID_RE.fullmatch(videoid or "") else None
        )
        if _vid:
            _api = await self._api_download_audio(_vid)
            if _api:
                return _api, True


        title = ""
        try:
            title = await self.title(link) or ""
        except Exception:
            title = ""


        p = await download_direct(link, "audio", title or "audio")
        if p:



            if str(p).startswith(("http://", "https://")):
                return p, None
            if os.path.exists(p) and os.path.getsize(p) > 1024:
                return p, True

        status, stream_url = await self.video(link)
        if status == 1 and stream_url and str(stream_url).startswith("http"):
            return stream_url, None
        return None, None











INNERTUBE_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
INNERTUBE_CLIENT_REMIX = {
    "clientName": "WEB_REMIX",
    "clientVersion": "1.20240101.01.00",
    "hl": "en",
    "gl": "US",
}
INNERTUBE_HEADERS_REMIX = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://music.youtube.com/",
}


def _related_extract_vid(url_or_query: str) -> Optional[str]:
    if not url_or_query:
        return None
    m = re.search(
        r"(?:v=|/shorts/|youtu\.be/|/embed/|/v/|/live/)([A-Za-z0-9_-]{11})",
        url_or_query,
    )
    if m:
        return m.group(1)
    s = str(url_or_query).strip()
    if YOUTUBE_ID_RE.fullmatch(s):
        return s
    return None


def _ytm_text(node) -> str:
    if isinstance(node, dict):
        return node.get("simpleText") or "".join(
            x.get("text", "") for x in node.get("runs", [])
        )
    return ""


def _extract_ytm_tracks(data: dict) -> List[Dict]:
    tracks: List[Dict] = []
    seen: set = set()

    def find_renderers(node):
        if isinstance(node, dict):
            renderer = None
            byline = None
            if "playlistPanelVideoRenderer" in node:
                renderer = node["playlistPanelVideoRenderer"]
                byline = renderer.get("shortBylineText") or renderer.get("longBylineText")
            elif "compactVideoRenderer" in node:
                renderer = node["compactVideoRenderer"]
                byline = renderer.get("shortBylineText") or renderer.get("ownerText")
            if renderer:
                vid = renderer.get("videoId")
                title = _ytm_text(renderer.get("title"))
                artist = _ytm_text(byline)
                dur = _ytm_text(renderer.get("lengthText"))
                thumbs = (renderer.get("thumbnail") or {}).get("thumbnails", [])
                thumb = thumbs[-1]["url"] if thumbs else ""
                if vid and title and vid not in seen:
                    seen.add(vid)
                    tracks.append(
                        {
                            "video_id": vid,
                            "title": title,
                            "artist": artist,
                            "duration": dur or "N/A",
                            "thumbnail": thumb,
                            "url": f"https://www.youtube.com/watch?v={vid}",
                        }
                    )
            for v in node.values():
                find_renderers(v)
        elif isinstance(node, list):
            for item in node:
                find_renderers(item)

    find_renderers(data)
    return tracks


async def get_related_suggestions(
    argument: str, limit: int = 5, exclude_ids=None
) -> List[Dict]:
    """Fetch related-track suggestions for a video id / URL / title.

    Primary: Innertube ``music.youtube.com/.../next`` with ``RDAMVM{vid}``
    (YTM radio mix) — quota-free, so the autoplay loop never silently drops
    the VC.

    Last resort: YouTube Data API search.

    ``exclude_ids`` (seed + recent history) is honoured first.
    """
    if not argument:
        return []
    vid = _related_extract_vid(argument)
    if not vid:
        try:
            hits = await asyncio.to_thread(_youtube_api_search, argument, 1)
            if hits:
                vid = hits[0].get("id")
        except Exception:
            vid = None
    excluded: set = set(exclude_ids or [])
    if vid:
        excluded.add(vid)
    suggestions: List[Dict] = []
    extracted: List[Dict] = []


    if len(suggestions) < limit and vid:
        try:
            url = f"https://music.youtube.com/youtubei/v1/next?key={INNERTUBE_KEY}"
            body = {
                "context": {"client": INNERTUBE_CLIENT_REMIX},
                "videoId": vid,
                "playlistId": f"RDAMVM{vid}",
                "isAutomix": True,
            }
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url, json=body, headers=INNERTUBE_HEADERS_REMIX
                ) as resp:
                    if resp.status == 200:
                        ytm = _extract_ytm_tracks(await resp.json())
                        extracted.extend(ytm)
                        for t in ytm:
                            svid = t.get("video_id")
                            if (
                                svid
                                and svid not in excluded
                                and not any(
                                    s.get("video_id") == svid for s in suggestions
                                )
                            ):
                                suggestions.append(t)
                                if len(suggestions) >= limit:
                                    break
                        logger.info(
                            "[Suggest] YTM radio +%d for %s (total %d)",
                            len(ytm),
                            vid,
                            len(suggestions),
                        )
        except Exception as e:
            logger.warning("[Suggest] YTM radio failed for %s: %s", vid, e)


    if len(suggestions) < limit:
        try:
            query = argument if not vid else f"similar music to {vid}"
            for item in await asyncio.to_thread(_youtube_api_search, query, limit * 3) or []:
                item_vid = item.get("id")
                if (
                    item_vid
                    and item_vid not in excluded
                    and not any(s.get("video_id") == item_vid for s in suggestions)
                ):
                    suggestions.append(
                        {
                            "video_id": item_vid,
                            "title": item.get("title", "N/A"),
                            "artist": item.get("channelTitle", "N/A"),
                            "duration": "N/A",
                            "thumbnail": "",
                            "url": f"https://www.youtube.com/watch?v={item_vid}",
                        }
                    )
                    if len(suggestions) >= limit:
                        break
        except Exception as e:
            logger.warning("[Suggest] Fallback search failed: %s", e)
    if not suggestions and extracted and vid:
        suggestions = [t for t in extracted if t.get("video_id") != vid]
    return suggestions[:limit]
