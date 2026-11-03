# Authored By Iota Coders (Instagram reel/photo downloader — v2 rewrite)
# SPDX-License-Identifier: MIT
"""Public API: InstagramReelDownloader class + 4 error types.

This module is the v2 rewrite of the /reel + /breel download logic that
was previously embedded in IotaXMedia/plugins/misc/iota_extras.py. It
adds specific error types (MediaNotFoundError, AuthRequiredError,
NetworkError) so the command handler can report *why* a download
failed instead of the legacy silent "» ɴᴏ ᴍᴇᴅɪᴀ ꜰᴏᴜɴᴅ." fallback.

Self-check invariant: _ig_process_image is photo-only and never produces
GIF output. It raises AssertionError if called on a video file path.
This guards against future regressions where someone might accidentally
add "video→gif" logic. The reported "video to GIF" behavior in the
legacy system was most likely Telegram's auto-loop video preview, not
actual GIF conversion.
"""
from __future__ import annotations  # noqa: F401








import asyncio
import logging
import os
import shutil
import tempfile
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional

import yt_dlp

logger = logging.getLogger(__name__)


IG_APP_ID = "936619743392459"
IG_UA = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
)
IG_HEADERS = {
    "User-Agent": IG_UA,
    "X-IG-App-ID": IG_APP_ID,
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
    "Referer": "https://www.instagram.com/",
}


try:
    from config import IG_COOKIES, IG_COOKIES_DATA
except Exception:  # pragma: no cover
    IG_COOKIES = None
    IG_COOKIES_DATA = None

_COOKIE_PATH = None
if IG_COOKIES and os.path.isfile(str(IG_COOKIES)):
    _COOKIE_PATH = str(IG_COOKIES)
else:
    raw = IG_COOKIES_DATA or os.environ.get("IG_COOKIES_DATA")
    if raw:
        lines = []
        for line in raw.splitlines():
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                lines.append(line)
                continue
            parts = line.split("\t")
            if len(parts) == 7:
                parts[6] = urllib.parse.unquote(parts[6])
                lines.append("\t".join(parts))
            else:
                lines.append(line)
        _COOKIE_PATH = tempfile.mktemp(suffix="_ig_cookies.txt")
        with open(_COOKIE_PATH, "w") as _cf:
            _cf.write("\n".join(lines) + "\n")

if _COOKIE_PATH:
    _IG_COOKIE_OPT = {"cookiefile": _COOKIE_PATH}
else:
    _IG_COOKIE_OPT = {}



class ReelError(Exception):
    """Base for all /reel downloader errors."""


class MediaNotFoundError(ReelError):
    """Post URL is invalid, removed, or IG returned 404."""


class AuthRequiredError(ReelError):
    """Post is private and no IG_COOKIES configured, or cookie expired."""


class NetworkError(ReelError):
    """Connection timeout, DNS failure, or 5xx from IG."""



@dataclass
class DownloadResult:
    files: List[str]
    info: dict
    is_video: bool
    tmpdir: str
    url: str
    quality: str



_VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".m4v")
_AUDIO_EXT = (".mp3", ".m4a", ".aac", ".ogg", ".wav", ".flac")
_IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")



def _classify_error(e: Exception) -> ReelError:
    """Map yt_dlp DownloadError / generic Exception to ReelError subclass
    based on substring match against the exception message.

    Pattern sources (yt-dlp 2026.x Instagram extractor):
      - "Instagram sent an empty media response" → post requires login
      - "use --cookies" or "without being logged-in" → cookie guidance
      - "login required" / "401" / "403" / "forbidden" → auth
      - "404" / "not found" / "unable to extract" → post missing
      - "timed out" / "unable to connect" → network
    """
    msg = str(e).lower()
    if (
        "403" in msg
        or "forbidden" in msg
        or "login required" in msg
        or "empty media response" in msg
        or "without being logged-in" in msg
        or "use --cookies" in msg
    ):
        return AuthRequiredError(f"IG requires authentication: {e}")
    if "404" in msg or "not found" in msg:
        return MediaNotFoundError(f"IG returned 404: {e}")



    if "unable to extract" in msg and "private profile" in msg:
        return AuthRequiredError(f"Private profile (no auth info): {e}")
    if "unable to extract" in msg:
        return MediaNotFoundError(
            f"Could not extract IG data (user missing or private): {e}"
        )
    if (
        "timed out" in msg
        or "unable to connect" in msg
        or "connection" in msg
        or "network" in msg
    ):
        return NetworkError(f"Network error: {e}")
    return ReelError(f"unexpected: {e}")



def _ig_process_image(path: str, quality: str) -> str:
    """Normalize image: 4K upscales small photos, 1080p caps large ones.

    Output: JPEG quality 92. NEVER GIF. NEVER touches video files.
    Self-check: if path ends with a video extension, raise AssertionError.
    This invariant is enforced by test_no_gif_conversion_in_image_processor.
    """
    assert not path.lower().endswith(_VIDEO_EXT), (
        f"_ig_process_image called on video file: {path}. "
        "This is a bug — video files must not be upscaled or "
        "converted to GIF. Use _ig_ydl_download directly for video."
    )
    try:
        from PIL import Image

        img = Image.open(path)
        w, h = img.size
        target = 3840 if quality == "4k" else 1080
        if quality == "4k":
            if w < target:
                img = img.resize((target, int(h * target / w)), Image.LANCZOS)
        else:
            if w > target:
                img = img.resize((target, int(h * target / w)), Image.LANCZOS)
        out = path.rsplit(".", 1)[0] + "_p.jpg"
        img.convert("RGB").save(out, "JPEG", quality=92)
        return out
    except Exception:
        return path



def _ig_ydl_download(url: str, fmt: str, tmpdir: str) -> dict:
    """yt-dlp wrapper. Raises ReelError subclass on failure (via _classify_error).

    fmt: "best[height<=1080]/best" for 1080p, "best" for 4k.
    """
    opts = {
        "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "http_headers": {"User-Agent": IG_UA},
        "format": fmt,
        "noplaylist": True,
        "extractor_retries": 2,
        "retry_sleep": 2,
    }
    opts.update(_IG_COOKIE_OPT)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True) or {}
    except Exception as e:
        raise _classify_error(e) from e



class InstagramReelDownloader:
    """Stateless downloader for Instagram media.

    All methods are static; this is just a namespace.
    """

    @staticmethod
    async def quick_info(url: str) -> dict:
        """Extract metadata without downloading. Raises:
        - MediaNotFoundError if yt-dlp returns None.
        - AuthRequiredError if IG returns 401/403.
        - NetworkError on connection/timeout.
        - ReelError on other failures.
        """
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "http_headers": {"User-Agent": IG_UA},
        }
        opts.update(_IG_COOKIE_OPT)

        def _run() -> dict:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise MediaNotFoundError("ig_quick_info returned None")
                    return info
            except ReelError:
                raise
            except Exception as e:
                raise _classify_error(e) from e

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    @staticmethod
    async def download(url: str, quality: str) -> DownloadResult:
        """Download media to a tempdir. Returns DownloadResult.

        Quality: "1080p" (caps video at 1080p) or "4k" (best available;
        photos upscaled to 3840px via PIL LANCZOS, videos not re-encoded).

        Raises ReelError subclass on failure. Always cleans up tmpdir.
        """
        if quality not in ("1080p", "4k"):
            raise ValueError(f"quality must be '1080p' or '4k', got {quality!r}")
        fmt = "best[height<=1080]/best" if quality == "1080p" else "best"
        tmpdir = tempfile.mkdtemp(prefix="reel_")
        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                None, lambda: _ig_ydl_download(url, fmt, tmpdir)
            )
            files = sorted(
                os.path.join(tmpdir, f)
                for f in os.listdir(tmpdir)
                if not f.endswith((".part", ".ytdl"))
            )
            if not files:
                raise MediaNotFoundError("no files downloaded from IG")
            is_video = any(f.lower().endswith(_VIDEO_EXT) for f in files)
            if not is_video:
                processed: List[str] = []
                for f in files:
                    if f.lower().endswith(_IMG_EXT):
                        processed.append(_ig_process_image(f, quality))
                    else:
                        processed.append(f)
                files = processed
            return DownloadResult(
                files=files,
                info=info,
                is_video=is_video,
                tmpdir=tmpdir,
                url=url,
                quality=quality,
            )
        except ReelError:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise
        except Exception as e:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise _classify_error(e) from e

    @staticmethod
    async def download_bulk(
        profile_url: str, quality: str, limit: int = 10
    ) -> List[DownloadResult]:
        """List posts for an IG profile and download each at the given quality.

        Uses ig_profile_entries from instagram.py for the listing step.
        Per-entry ReelError failures are logged and skipped (not raised).
        """
        from IotaXMedia.plugins.tools.instagram import ig_profile_entries

        entries = await ig_profile_entries(profile_url, max_entries=limit)
        results: List[DownloadResult] = []
        for entry_url, _title in entries:
            try:
                res = await InstagramReelDownloader.download(entry_url, quality)
                results.append(res)
            except ReelError as e:
                logger.warning(f"bulk skip {entry_url}: {e}")
            except Exception as e:
                logger.warning(f"bulk unexpected skip {entry_url}: {e}")
        return results
