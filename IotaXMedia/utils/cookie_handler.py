# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""YouTube cookies: Render Secret Files, COOKIES_FILE/COOKIE_FILE, COOKIE_URL, local.

Render Secret Files are mounted at:
  /etc/secrets/<filename>

Examples:
  cookies.txt          → /etc/secrets/cookies.txt
  cookies              → /etc/secrets/cookies
  youtube.cookies      → /etc/secrets/youtube.cookies

Env (any one):
  COOKIES_FILE=/etc/secrets/cookies.txt
  COOKIE_FILE=/etc/secrets/cookies.txt
  COOKIE_URL=https://pastebin.com/raw/...
"""
from __future__ import annotations

import asyncio
import base64
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlsplit

import requests

from config import COOKIE_URL
from IotaXMedia.utils.errors import capture_internal_err


COOKIE_PATH = Path("IotaXMedia/assets/cookies.txt")
_SECRETS_DIR = Path("/etc/secrets")


def _env_cookie_paths() -> List[Path]:
    """Paths from env: COOKIES_FILE, COOKIE_FILE, COOKIES_PATH, COOKIE_PATH."""
    paths: List[Path] = []
    for key in ("COOKIES_FILE", "COOKIE_FILE", "COOKIES_PATH", "COOKIE_PATH"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        p = Path(raw)
        paths.append(p)

        if not p.is_absolute() and "/" not in raw and "\\" not in raw:
            paths.append(_SECRETS_DIR / raw)
    return paths


def _scan_secrets_dir() -> List[Path]:
    """Auto-detect Netscape cookie files mounted by Render Secret Files."""
    found: List[Path] = []
    if not _SECRETS_DIR.is_dir():
        return found
    try:
        names = sorted(os.listdir(_SECRETS_DIR))
    except OSError:
        return found

    preferred = []
    others = []
    for name in names:
        lower = name.lower()
        path = _SECRETS_DIR / name
        if not path.is_file():
            continue

        if (
            lower in ("cookies.txt", "cookies", "youtube_cookies.txt", "yt_cookies.txt")
            or lower.endswith(".cookies")
            or lower.endswith("cookies.txt")
            or "cookie" in lower
        ):
            preferred.append(path)
        else:
            others.append(path)
    return preferred + others


def _candidates() -> List[Path]:
    """Resolve order: env paths → /etc/secrets/* → local assets."""
    paths: List[Path] = []
    paths.extend(_env_cookie_paths())

    paths.append(_SECRETS_DIR / "cookies.txt")
    paths.append(_SECRETS_DIR / "cookies")
    paths.append(_SECRETS_DIR / "youtube.cookies")
    paths.append(_SECRETS_DIR / "cookies.cookies")
    paths.extend(_scan_secrets_dir())

    paths.append(Path("/workspace/new cookies.txt"))
    paths.append(Path("/workspace/cookies.txt"))
    paths.append(COOKIE_PATH)

    seen = set()
    out: List[Path] = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _is_valid_netscape(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 50:
            return False

        text = path.read_text(encoding="utf-8", errors="ignore")
        head = text[:800]
        stripped = head.lstrip("\ufeff \t\r\n")
        if stripped.startswith("# Netscape") or stripped.startswith("# HTTP Cookie File"):
            return True
        if "youtube.com" in text[:4000] and "\t" in text:

            return True
        return False
    except Exception:
        return False


def resolve_cookie_path() -> Optional[Path]:
    """First valid cookies file (Render secret / env / local)."""
    for p in _candidates():
        if _is_valid_netscape(p):
            return p
    return None


def get_writable_cookie_file() -> Optional[str]:
    """Return a WRITABLE copy of the resolved cookie file.

    Render mounts Secret Files (e.g. /etc/secrets/cookies.txt) as READ-ONLY.
    yt-dlp's ``cookiefile`` option writes auth tokens back to the file, so
    passing the secret path directly raises ``[Errno 30] Read-only file
    system``. Copy to a temp file yt-dlp is allowed to write to.
    """
    src = resolve_cookie_path()
    if not src or not src.is_file():
        return None
    try:
        fd, tmp = tempfile.mkstemp(prefix="iota_cookies_", suffix=".txt")
        os.close(fd)
        shutil.copy2(src, tmp)
        return tmp
    except Exception:

        return str(src)


def cookie_path_for_write() -> Path:
    return COOKIE_PATH


def _extract_paste_id(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    parts = [p for p in path.split("/") if p]
    return parts[-1] if parts else ""


def resolve_raw_cookie_url(url: str) -> str:
    url = (url or "").strip()
    low = url.lower()

    if "pastebin.com/" in low and "/raw/" not in low:
        paste_id = _extract_paste_id(url)
        return f"https://pastebin.com/raw/{paste_id}" if paste_id else url

    if "batbin.me/" in low:
        if "/api/v2/paste/" in low:
            return url
        paste_id = _extract_paste_id(url)
        return f"https://batbin.me/api/v2/paste/{paste_id}" if paste_id else url

    return url


@capture_internal_err
async def fetch_and_store_cookies():
    if not COOKIE_URL:
        raise EnvironmentError("COOKIE_URL not set in env.")

    raw_url = resolve_raw_cookie_url(COOKIE_URL)

    try:
        response = await asyncio.to_thread(
            requests.get,
            raw_url,
            timeout=15,
            headers={"User-Agent": "iota-cookie-fetcher/1.0"},
        )
        response.raise_for_status()
    except Exception as e:
        raise ConnectionError(f"Can't fetch cookies:\n{e}")

    cookies = (response.text or "").strip()

    if not cookies.startswith("# Netscape") and "youtube.com" not in cookies:
        raise ValueError("Invalid cookie format. Needs Netscape format.")

    if len(cookies) < 100:
        raise ValueError("Cookie content too short. Possibly invalid.")

    dest = cookie_path_for_write()
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.write_text(cookies, encoding="utf-8")
    except Exception as e:
        raise IOError(f"Failed to save cookies: {e}")


def sync_secret_cookies_to_assets() -> Optional[Path]:
    """Mirror secret-file cookies into assets path (best-effort, for tools expecting local path)."""
    src = resolve_cookie_path()
    if not src:
        return None
    try:
        if src.resolve() == COOKIE_PATH.resolve():
            return src
    except Exception:
        pass
    try:
        COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)

        if str(src).startswith("/etc/secrets"):
            shutil.copy2(src, COOKIE_PATH)
        elif not COOKIE_PATH.exists() or COOKIE_PATH.stat().st_size < 50:
            shutil.copy2(src, COOKIE_PATH)
    except Exception:
        pass
    return src


def _apply_inline_cookie():
    b64 = (os.environ.get("COOKIE_B64") or "").strip()
    if not b64:
        return
    try:
        text = base64.b64decode(b64).decode("utf-8", "ignore").strip()
    except Exception:
        return
    if not (text.startswith("# Netscape") or "youtube.com" in text):
        return
    try:
        COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
        COOKIE_PATH.write_text(text, encoding="utf-8")
    except Exception:
        pass


_apply_inline_cookie()
