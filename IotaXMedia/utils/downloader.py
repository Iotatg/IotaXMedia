# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import contextlib
import glob
import os
import re
import shutil
import subprocess
import zipfile
from typing import Dict, Optional

import aiofiles
import aiohttp
from aiohttp import TCPConnector
from yt_dlp import YoutubeDL

from IotaXMedia.core.dir import CACHE_DIR, DOWNLOAD_DIR
from IotaXMedia.utils.tuning import CHUNK_SIZE, SEM
from config import (
    API_KEY,
    API_URL,
    LITTERBOX_API_URL,
    LITTERBOX_ENABLED,
    LITTERBOX_MAX_BYTES,
    LITTERBOX_TIMEOUT,
    LITTERBOX_TTL,
    VIDEO_API_URL,
    YTPROXY_URL,
)
from IotaXMedia.logging import LOGGER

LOGGER = LOGGER(__name__)

USE_AUDIO_API = bool(API_URL and API_KEY)
USE_VIDEO_API = bool(VIDEO_API_URL and API_KEY)
_inflight: Dict[str, asyncio.Future] = {}
_inflight_lock = asyncio.Lock()
_session: Optional[aiohttp.ClientSession] = None
_session_lock = asyncio.Lock()
YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_LITTERBOX_VALID_TTL = {"1h", "12h", "24h", "72h"}
_hosted_cache: Dict[str, str] = {}
_hosted_cache_lock = asyncio.Lock()


def _latest_deno_version() -> str:
    """Best-effort lookup of the latest deno release tag (fallback pinned)."""
    try:
        import json
        import urllib.request

        req = urllib.request.Request(
            "https://api.github.com/repos/denoland/deno/releases/latest",
            headers={"User-Agent": "IotaXMedia"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            tag = json.load(r).get("tag_name")
        if tag:
            return tag
    except Exception:
        pass
    return "v1.46.3"


def _ensure_js_runtime() -> Optional[str]:
    """Return a JS runtime executable for yt-dlp signature solving.

    yt-dlp needs deno (or node) to solve YouTube's n/nsig challenges.
    Local dev has /root/.deno; on Render it is absent, so we lazily
    download a static deno build into /tmp (the only guaranteed-writable
    dir) on first need. Returns None if unavailable (downloads then rely
    on the external API fallback)."""


    os.environ.setdefault("DENO_DIR", "/tmp/deno_cache")
    for exe in ("deno", "node"):
        p = shutil.which(exe)
        if p:
            return p
    local = "/root/.deno/bin/deno"
    if os.path.isfile(local):
        return local
    install_dir = "/tmp/deno"
    target = os.path.join(install_dir, "deno")
    if os.path.isfile(target):
        return target
    try:
        os.makedirs(install_dir, exist_ok=True)
        _installed = False
        try:
            ver = _latest_deno_version()
            url = (
                "https://github.com/denoland/deno/releases/download/"
                f"{ver}/deno-x86_64-unknown-linux-gnu.zip"
            )
            zip_path = os.path.join(install_dir, "deno.zip")
            LOGGER.info(f"Auto-installing deno {ver} for yt-dlp JS solving...")
            subprocess.run(
                ["curl", "-fsSL", url, "-o", zip_path], check=True, timeout=240
            )
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(install_dir)
            _installed = True
        except Exception as e1:
            LOGGER.warning(f"deno zip install failed ({e1}); trying install.sh")
            try:

                subprocess.run(
                    "curl -fsSL https://deno.land/install.sh | sh",
                    shell=True,
                    env={**os.environ, "DENO_INSTALL": install_dir},
                    check=True,
                    timeout=300,
                )
                alt = os.path.join(install_dir, "bin", "deno")
                if os.path.isfile(alt):
                    target = alt
                _installed = True
            except Exception as e2:
                LOGGER.warning(f"deno install.sh also failed: {e2}")
        if _installed and os.path.isfile(target):
            os.chmod(target, 0o755)
            LOGGER.info(f"deno installed at {target}")
            return target
    except Exception as e:
        LOGGER.warning(f"Failed to auto-install deno (yt-dlp JS solving): {e}")
    return None


def log_download_source(title: str, source: str) -> None:
    LOGGER.info(f"Track '{title}' - Downloaded by {source}")


def extract_video_id(link: str) -> str:
    if not link:
        return ""
    s = link.strip()
    if YOUTUBE_ID_RE.match(s):
        return s
    if "v=" in s:
        return s.split("v=")[-1].split("&")[0]
    last = s.split("/")[-1].split("?")[0]
    if YOUTUBE_ID_RE.match(last):
        return last
    return ""


def get_cookie_file() -> Optional[str]:
    """Resolve a WRITABLE copy of a valid Netscape cookies file.

    Returned path is a temp copy (Render Secret Files are read-only, and
    yt-dlp's cookiefile option writes back to it)."""
    try:
        from IotaXMedia.utils.cookie_handler import get_writable_cookie_file

        return get_writable_cookie_file()
    except Exception:
        return None


def _load_netscape_cookies(path: str) -> dict:
    """Parse a Netscape cookie file into a {name: value} dict."""
    out: dict = {}
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 7 and parts[5]:
                    out[parts[5]] = parts[6]
    except Exception:
        pass
    return out


def find_cached_file(video_id: str) -> Optional[str]:
    if not video_id:
        return None
    for ext in ("mp3", "m4a", "webm", "mp4", "mkv"):
        path = f"{DOWNLOAD_DIR}/{video_id}.{ext}"
        if os.path.exists(path):
            return path
    return None


def get_ytdlp_base_opts() -> Dict[str, object]:




    _rt = _ensure_js_runtime()
    if _rt:
        _rt_dir = os.path.dirname(_rt)
        if _rt_dir and _rt_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{_rt_dir}:{os.environ.get('PATH', '')}"

    opts: Dict[str, object] = {
        "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "overwrites": True,
        "continuedl": False,
        "noprogress": True,
        "concurrent_fragment_downloads": 8,
        "http_chunk_size": 1 << 20,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "cachedir": str(CACHE_DIR),
        "ignoreerrors": False,


        "remote_components": ["ejs:github"],




        "extractor_args": {
            "youtube": {
                "player_client": [
                    "web",
                    "tv",
                    "tv_embedded",
                    "android_vr",
                    "android",
                    "ios",
                    "mediaconnect",
                ],
            },
        },
    }
    cf = get_cookie_file()
    if cf:
        opts["cookiefile"] = cf
    if YTPROXY_URL:
        opts["proxy"] = YTPROXY_URL
    return opts


async def get_http_session() -> aiohttp.ClientSession:
    global _session
    if _session and not _session.closed:
        return _session
    async with _session_lock:
        if _session and not _session.closed:
            return _session
        timeout = aiohttp.ClientTimeout(total=600, sock_connect=20, sock_read=60)
        connector = TCPConnector(limit=0, ttl_dns_cache=300, enable_cleanup_closed=True)
        _session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return _session


async def close_http_session() -> None:
    global _session
    async with _session_lock:
        if _session and not _session.closed:
            await _session.close()
        _session = None


async def download_file(url: str, out_path: str) -> Optional[str]:
    if not url:
        return None
    try:
        session = await get_http_session()
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            async with aiofiles.open(out_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    if not chunk:
                        break
                    await f.write(chunk)
        return out_path if os.path.exists(out_path) else None
    except Exception:
        return None


async def api_download_audio(link: str) -> Optional[str]:
    if not USE_AUDIO_API:
        return None
    vid = extract_video_id(link)
    if not vid:
        return None
    poll_url = f"{API_URL}/song/{vid}?api={API_KEY}"
    try:
        session = await get_http_session()
        deadline = asyncio.get_running_loop().time() + 120
        while asyncio.get_running_loop().time() < deadline:
            async with session.get(poll_url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                status = str(data.get("status", "")).lower()
                if status == "downloading":
                    await asyncio.sleep(1.0)
                    continue
                if status != "done":
                    return None
                dl_url = data.get("link")
                fmt = data.get("format", "webm")
                out_path = f"{DOWNLOAD_DIR}/{vid}.{fmt}"
                return await download_file(dl_url, out_path)
        return None
    except Exception:
        return None


async def api_download_video(link: str) -> Optional[str]:
    if not USE_VIDEO_API:
        return None
    vid = extract_video_id(link)
    if not vid:
        return None
    poll_url = f"{VIDEO_API_URL}/video/{vid}?api={API_KEY}"
    try:
        session = await get_http_session()
        deadline = asyncio.get_running_loop().time() + 120
        while asyncio.get_running_loop().time() < deadline:
            async with session.get(poll_url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                status = str(data.get("status", "")).lower()
                if status == "downloading":
                    await asyncio.sleep(1.0)
                    continue
                if status != "done":
                    return None
                dl_url = data.get("link")
                fmt = data.get("format", "mp4")
                out_path = f"{DOWNLOAD_DIR}/{vid}.{fmt}"
                return await download_file(dl_url, out_path)
        return None
    except Exception:
        return None


def get_final_path_from_info(info: Dict) -> Optional[str]:
    vid = info.get("id")
    if not vid:
        return None
    ext = info.get("ext")
    if ext:
        p = f"{DOWNLOAD_DIR}/{vid}.{ext}"
        if os.path.exists(p) and os.path.getsize(p) > 1024 and not p.endswith(".part"):
            return p
    matches = [
        m
        for m in glob.glob(f"{DOWNLOAD_DIR}/{vid}.*")
        if not m.endswith(".part") and os.path.getsize(m) > 1024
    ]
    matches = sorted(matches, key=os.path.getmtime, reverse=True)
    return matches[0] if matches else None


_LAST_YT_ERROR: str = ""


def get_last_yt_error() -> str:
    return _LAST_YT_ERROR



def _download_yt_curl_audio(link: str, vid: str) -> Optional[str]:
    try:
        from curl_cffi.requests import Session
    except ImportError:
        return None
    try:
        import json as _json
        s = Session(impersonate="chrome131")
        if YTPROXY_URL:
            s.proxies.update({"http": YTPROXY_URL, "https": YTPROXY_URL})
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })

        cookies = {}
        cf = get_cookie_file()
        if cf:
            cookies = _load_netscape_cookies(cf)

        resp = s.get(f"https://www.youtube.com/watch?v={vid}", cookies=cookies)
        if resp.status_code != 200:
            return None

        html = resp.text

        import re as _re
        match = _re.search(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', html)
        if not match:
            return None

        import json as _json
        data = _json.loads(match.group(1))
        sd = data.get("streamingData") or {}
        formats = sd.get("adaptiveFormats") or sd.get("formats") or []

        audio_formats = [f for f in formats if "audio" in str(f.get("mimeType", "")).lower()]
        if not audio_formats:
            return None

        best = sorted(audio_formats, key=lambda f: int(f.get("bitrate") or 0), reverse=True)[0]
        dl_url = best.get("url")

        if not dl_url and "signatureCipher" in best:
            from urllib.parse import parse_qs, unquote
            sc = parse_qs(best["signatureCipher"])
            dl_url = unquote(sc.get("url", [""])[0])
            sig = sc.get("s", [""])[0]
            if sig:
                dl_url += "&sig=" + sig
            else:
                sp = sc.get("sp", ["signature"])[0]
                dl_url += f"&{sp}={sig}"

        if not dl_url:
            return None

        out_path = f"{DOWNLOAD_DIR}/{vid}.webm"
        dl_resp = s.get(dl_url, stream=True)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
            LOGGER.info(f"curl-cffi download: {vid}")
            return out_path
        return None
    except Exception:
        return None



USE_CURL_DOWNLOAD = True


def _resolve_cipher_url(fmt: Dict) -> Optional[str]:
    """Resolve a format's playable URL when only a signatureCipher/cipher is present."""
    raw = fmt.get("signatureCipher") or fmt.get("cipher")
    if not raw:
        return None
    try:
        from urllib.parse import parse_qs, unquote

        sc = parse_qs(raw)
        url = unquote(sc.get("url", [""])[0])
        sig = sc.get("s", [""])[0]
        if not url:
            return None
        if sig:
            sp = sc.get("sp", ["signature"])[0]
            return f"{url}&{sp}={sig}"
        return url
    except Exception:
        return None


def _download_yt_curl_video(link: str, vid: str) -> Optional[str]:
    """Browser-impersonated YouTube *video* downloader (no yt-dlp, no cookies).

    Picks a progressive (audio+video) format from the watch page's
    ytInitialPlayerResponse and downloads it directly. Mirrors
    _download_yt_curl_audio so /vplay has the same IP-block-resistant fallback
    that /play (audio) already enjoys. Returns None on any failure."""
    try:
        from curl_cffi.requests import Session
    except ImportError:
        return None
    try:
        import json as _json
        import re as _re
        from urllib.parse import parse_qs, unquote

        s = Session(impersonate="chrome131")
        if YTPROXY_URL:
            s.proxies.update({"http": YTPROXY_URL, "https": YTPROXY_URL})
        s.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })
        cookies = {}
        cf = get_cookie_file()
        if cf:
            cookies = _load_netscape_cookies(cf)

        resp = s.get(f"https://www.youtube.com/watch?v={vid}", cookies=cookies)
        if resp.status_code != 200:
            return None

        match = _re.search(r"var\s+ytInitialPlayerResponse\s*=\s*({.*?});", resp.text)
        if not match:
            return None
        data = _json.loads(match.group(1))
        sd = data.get("streamingData") or {}

        fmts = [
            f
            for f in (sd.get("formats") or [])
            if str(f.get("mimeType", "")).lower().startswith("video") and f.get("height")
        ]
        if not fmts:
            return None
        fmts = sorted(fmts, key=lambda f: int(f.get("height") or 0), reverse=True)

        capped = [f for f in fmts if int(f.get("height") or 0) <= 1080]
        best = capped[0] if capped else fmts[0]

        dl_url = best.get("url") or _resolve_cipher_url(best)
        if not dl_url:
            return None

        out_path = f"{DOWNLOAD_DIR}/{vid}.mp4"
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        dl_resp = s.get(dl_url, stream=True)
        with open(out_path, "wb") as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
            LOGGER.info(f"curl-cffi video download: {vid}")
            return out_path
        return None
    except Exception:
        return None


async def _curl_download_video(link: str, vid: str) -> Optional[str]:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: _download_yt_curl_video(link, vid))
    return result


async def _curl_download(link: str, vid: str) -> Optional[str]:
    import asyncio as _asyncio
    loop = _asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: _download_yt_curl_audio(link, vid))
    return result


def download_with_ytdlp_sync(link: str, fmt: str) -> Optional[str]:
    global _LAST_YT_ERROR
    _LAST_YT_ERROR = ""
    try:
        opts = get_ytdlp_base_opts()
        opts["format"] = fmt
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True)
            if not info:
                return None
            path = get_final_path_from_info(info)
            if path:
                return path
            for rd in info.get("requested_downloads") or []:
                fp = rd.get("filepath")
                if fp and os.path.exists(fp) and not str(fp).endswith(".part"):
                    return fp
            return None
    except Exception as e:
        msg = str(e)
        _LAST_YT_ERROR = msg
        low = msg.lower()
        if "sign in" in low or "not a bot" in low or "403" in low or "blocked" in low:
            _LAST_YT_ERROR = (
                "YouTube download blocked from this server's IP. "
                "Set API_URL/VIDEO_API_URL in config for an API-based fallback."
            )
        LOGGER.error(f"yt-dlp download failed: {_LAST_YT_ERROR}")
        return None


async def run_with_semaphore(coro):
    async with SEM:
        return await coro


async def deduplicate_download(key: str, runner):
    async with _inflight_lock:
        if fut := _inflight.get(key):
            return await fut
        fut = asyncio.get_running_loop().create_future()
        _inflight[key] = fut
    try:
        result = await runner()
        fut.set_result(result)
        return result
    except Exception as e:
        fut.set_exception(e)
        return None
    finally:
        async with _inflight_lock:
            _inflight.pop(key, None)


async def race_ytdlp_and_api(yt_task, api_task, title: str):
    done, pending = await asyncio.wait(
        {yt_task, api_task}, return_when=asyncio.FIRST_COMPLETED
    )



    for task in done:
        result = task.result()
        if result and os.path.exists(result):
            source = "yt-dlp" if task is yt_task else "API"
            log_download_source(title, source)
            for p in pending:
                p.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await p
            return result


    for task in pending:
        try:
            result = await task
        except asyncio.CancelledError:
            with contextlib.suppress(asyncio.CancelledError):
                await task
            return None
        except Exception:
            return None
        if result and os.path.exists(result):
            source = "yt-dlp" if task is yt_task else "API"
            log_download_source(title, source)
            return result
    return None


async def upload_to_litterbox(local_path: str, title: str = "") -> Optional[str]:
    """Upload a downloaded file to Litterbox (catbox.moe temporary host).

    Returns the remote URL on success, or None on any failure (caller keeps
    using the local path). Failures are logged but never fatal.
    """
    try:
        if not os.path.exists(local_path):
            return None
        size = os.path.getsize(local_path)
        if size == 0 or size > LITTERBOX_MAX_BYTES:
            return None
        ttl = LITTERBOX_TTL if LITTERBOX_TTL in _LITTERBOX_VALID_TTL else "12h"
        session = await get_http_session()
        with open(local_path, "rb") as fh:
            form = aiohttp.FormData()
            form.add_field("reqtype", "fileupload")
            form.add_field("time", ttl)
            form.add_field(
                "fileToUpload",
                fh,
                filename=os.path.basename(local_path),
                content_type="application/octet-stream",
            )
            async with session.post(
                LITTERBOX_API_URL,
                data=form,
                timeout=aiohttp.ClientTimeout(total=LITTERBOX_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    LOGGER.warning(
                        f"Litterbox upload HTTP {resp.status} for '{title[:40]}'"
                    )
                    return None
                text = (await resp.text()).strip()
        if text.startswith("https://"):
            LOGGER.info(f"Track '{title[:40]}' - Hosted on Litterbox ({ttl}): {text}")
            return text
        LOGGER.warning(f"Litterbox returned unexpected response: {text[:120]}")
        return None
    except Exception as e:
        LOGGER.warning(f"Litterbox upload failed for '{title[:40]}': {e}")
        return None


async def _maybe_host(local_path: str, vid: str, title: str = "") -> str:
    """Return a Litterbox-hosted URL for the track when enabled/cached, else the
    local path. Never raises — falls back to the local path on any problem."""
    if not local_path:
        return local_path
    if not (LITTERBOX_ENABLED and vid):
        return local_path
    async with _hosted_cache_lock:
        if vid in _hosted_cache:
            return _hosted_cache[vid]
    url = await upload_to_litterbox(local_path, title)
    if url:
        async with _hosted_cache_lock:
            _hosted_cache[vid] = url
        return url
    return local_path


async def yt_dlp_download(link: str, type: str, title: str = "") -> Optional[str]:
    loop = asyncio.get_running_loop()
    vid = extract_video_id(link)
    if cached := find_cached_file(vid):
        if title:
            LOGGER.info(f"Track '{title}' - Served from cache")
        if LITTERBOX_ENABLED and vid:
            return await _maybe_host(cached, vid, title)
        return cached

    if type == "audio":
        key = f"audio:{link}"

        async def run():
            if USE_CURL_DOWNLOAD and vid:
                result = await _curl_download(link, vid)
                if result and os.path.exists(result) and os.path.getsize(result) > 1024:
                    LOGGER.info(f"Track '{title}' - Downloaded by curl-cffi")
                    return result

            ytdlp_task = asyncio.create_task(
                run_with_semaphore(
                    loop.run_in_executor(
                        None,
                        download_with_ytdlp_sync,
                        link,
                        "bestaudio/best",
                    )
                )
            )
            api_task = asyncio.create_task(api_download_audio(link)) if USE_AUDIO_API else None
            if api_task:
                return await _maybe_host(
                    await race_ytdlp_and_api(ytdlp_task, api_task, title or "Unknown"),
                    vid,
                    title,
                )
            result = await ytdlp_task
            if result and title:
                log_download_source(title, "yt-dlp")
            return await _maybe_host(result, vid, title)

        return await deduplicate_download(key, run)

    elif type == "video":
        key = f"video:{link}"

        async def run():
            if USE_CURL_DOWNLOAD and vid:
                result = await _curl_download_video(link, vid)
                if result and os.path.exists(result) and os.path.getsize(result) > 1024:
                    LOGGER.info(f"Track '{title}' - Downloaded by curl-cffi")
                    return result

            ytdlp_task = asyncio.create_task(
                run_with_semaphore(
                    loop.run_in_executor(
                        None,
                        download_with_ytdlp_sync,
                        link,
                        "best[ext=mp4][height<=1080]/best",
                    )
                )
            )
            api_task = asyncio.create_task(api_download_video(link)) if USE_VIDEO_API else None
            if api_task:
                return await _maybe_host(
                    await race_ytdlp_and_api(ytdlp_task, api_task, title or "Unknown"),
                    vid,
                    title,
                )
            result = await ytdlp_task
            if result and title:
                log_download_source(title, "yt-dlp")
            return await _maybe_host(result, vid, title)

        return await deduplicate_download(key, run)

    return None



def _download_direct_sync(link: str, fmt: str, vid: str) -> Optional[str]:
    """Sync direct yt-dlp download. Mirrors the proven /song downloader: no
    curl-cffi, no API race — just YoutubeDL with a format chain and robust
    file discovery. Returns a local file path or None."""
    try:
        opts = get_ytdlp_base_opts()
        opts["format"] = fmt
        opts["outtmpl"] = f"{DOWNLOAD_DIR}/%(id)s.%(ext)s"
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True) or {}
            v = info.get("id") or vid
            ext = info.get("ext")
            if v and ext:
                p = f"{DOWNLOAD_DIR}/{v}.{ext}"
                if os.path.exists(p) and os.path.getsize(p) > 1024:
                    return p
            if v:
                for e in ("webm", "m4a", "mp3", "mp4", "mkv", "opus"):
                    p = f"{DOWNLOAD_DIR}/{v}.{e}"
                    if os.path.exists(p) and os.path.getsize(p) > 1024:
                        return p
            final = get_final_path_from_info(info)
            if final and os.path.exists(final) and os.path.getsize(final) > 1024:
                return final
            if v:
                for p in sorted(
                    glob.glob(f"{DOWNLOAD_DIR}/{v}.*"),
                    key=os.path.getmtime,
                    reverse=True,
                ):
                    try:
                        if os.path.getsize(p) > 1024 and not p.endswith(".part"):
                            return p
                    except OSError:
                        continue
    except Exception:
        pass
    return None


def _reencode_audio_to_mp3(src: str) -> str:
    """Re-encode a local audio file to a clean MP3 (stereo, 48k, 192k) so
    PyTgCalls reliably detects and plays the audio stream. WebM/Opus
    containers frequently fail probing in some PyTgCalls builds and surface
    as NoAudioSourceFound — a clean MP3 avoids that entirely.

    Returns the MP3 path on success, or the original path on any failure
    (ffmpeg missing / encode error), so the caller always gets a file.
    """
    try:
        if not src or not os.path.exists(src) or os.path.getsize(src) < 1024:
            return src
        if str(src).lower().endswith(".mp3"):
            return src
        dst = f"{src}.reenc.mp3"
        proc = subprocess.run(
            [
                "ffmpeg", "-y", "-nostdin", "-i", src,
                "-vn", "-ac", "2", "-ar", "48000", "-b:a", "192k",
                dst,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
        if proc.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 1024:
            try:
                os.remove(src)
            except Exception:
                pass
            return dst
    except Exception:
        pass
    return src


async def download_direct(link: str, dl_type: str = "audio", title: str = "") -> Optional[str]:
    """Download a YouTube track/video to a local file using the same direct
    yt-dlp path as the /song command. Returns a local file path, or None.

    For audio, the result is re-encoded to a clean MP3 so PyTgCalls can
    reliably play it (WebM/Opus containers can fail probing -> NoAudioSourceFound).
    """
    loop = asyncio.get_running_loop()
    vid = extract_video_id(link)
    if not vid:
        return None
    if cached := find_cached_file(vid):
        if title:
            LOGGER.info(f"Track '{title}' - Served from cache")
        return cached
    if dl_type == "video":
        fmt_chain = (
            "best[ext=mp4][height<=1080]/best[height<=1080]/best",
            "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best",
            "137/136/22/18/best",
            "best",
        )
    else:

        fmt_chain = (
            "140/bestaudio[ext=m4a]",
            "140/bestaudio",
            "251/140/250/249/bestaudio",
            "bestaudio/best",
            "best",
        )
    for fmt in fmt_chain:
        try:
            path = await loop.run_in_executor(
                None, _download_direct_sync, link, fmt, vid
            )
        except Exception:
            path = None
        if path and os.path.exists(path) and os.path.getsize(path) > 1024:
            if title:
                LOGGER.info(f"Track '{title}' - Downloaded by yt-dlp ({fmt})")
            if dl_type == "audio":
                path = await loop.run_in_executor(None, _reencode_audio_to_mp3, path)
            return path
    return None
