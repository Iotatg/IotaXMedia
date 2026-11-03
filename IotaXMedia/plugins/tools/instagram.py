# Authored By Iota Coders (Instagram profile + media tools)
# SPDX-License-Identifier: MIT
import asyncio
import os
import re
import shutil
import tempfile

import httpx
import yt_dlp
from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.logging import LOGGER
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.decorators.language import language

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
                import urllib.parse

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


def _parse_username(url_or_name: str) -> str:
    """Strip a full IG url down to a bare handle, or pass through."""
    value = url_or_name.strip().strip("@").rstrip("/")
    m = re.search(r"(?:instagram\.com/)?([A-Za-z0-9._]+)(?:\?.*)?$", value)
    return m.group(1) if m else value


def _extract_count(pattern: str, text: str) -> int:
    m = re.search(pattern, text, re.I)
    return _parse_count(m.group(1)) if m else 0


def _parse_count(text: str) -> int:
    """Parse '291.6M' / '500K' / '1234' to int."""
    text = text.strip().replace(",", "").replace(" ", "").upper()
    try:
        if text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        elif text.endswith("K"):
            return int(float(text[:-1]) * 1_000)
        elif text.endswith("B"):
            return int(float(text[:-1]) * 1_000_000_000)
        return int(float(text))
    except ValueError:
        return 0


async def _ig_profile(username: str) -> dict:
    username = _parse_username(username)
    errors = []


    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            resp = await client.get(
                f"https://imginn.com/{username}/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
        if resp.status_code in (404, 410):
            raise ValueError(f"Instagram user '{username}' not found.")
        elif resp.status_code == 200:
            html = resp.text
            title_m = re.search(r"<title>([^<]+)</title>", html)
            desc_m = re.search(
                r'meta\s+property=\"og:description\"\s+content=\"([^\"]+)\"', html
            )
            img_m = re.search(
                r'meta\s+property=\"og:image\"\s+content=\"([^\"]+)\"', html
            )

            full_name = ""
            followers = 0
            following = 0
            posts = 0
            bio = ""

            if title_m:
                title_text = title_m.group(1)
                name_m = re.search(r"^(.+)\(@", title_text)
                if name_m:
                    full_name = name_m.group(1).strip()
                else:
                    name_match = re.match(r"^(.+)\s+View", title_text)
                    if name_match:
                        full_name = name_match.group(1).strip()

            if desc_m:
                desc = desc_m.group(1)
                followers = _extract_count(r"([\d,.]+[KMB]?)\s*Followers?", desc)
                following = _extract_count(r"([\d,.]+[KMB]?)\s*Following", desc)
                posts = _extract_count(r"([\d,.]+[KMB]?)\s*Posts?", desc)
                bio = desc.split(" Followers")[0].rstrip(",.").strip() if followers else desc
                if bio and "," in bio:
                    bio = bio.split(",")[0].strip()

            profile_pic = img_m.group(1) if img_m else ""
            if full_name or followers:
                return {
                    "username": username,
                    "full_name": full_name,
                    "is_private": False,
                    "is_verified": False,
                    "biography": bio,
                    "edge_followed_by": {"count": followers},
                    "edge_follow": {"count": following},
                    "edge_owner_to_timeline_media": {"count": posts},
                    "profile_pic_url_hd": profile_pic,
                }
        else:
            errors.append(f"imginn: HTTP {resp.status_code}")
    except Exception as e:
        errors.append(f"imginn: {e}")


    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://www.instagram.com/api/v1/users/web_profile_info/",
                    params={"username": username},
                    headers=IG_HEADERS,
                )
            if resp.status_code == 429:
                await asyncio.sleep(2 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            user = (data.get("data") or {}).get("user") or {}
            if user:
                return user
        except Exception as e:
            errors.append(f"API: {e}")
            await asyncio.sleep(1)


    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(
                {"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": 1}
            ).extract_info(
                f"https://www.instagram.com/{username}/", download=False
            ),
        )
        if info:
            user = {
                "username": info.get("uploader") or username,
                "full_name": info.get("channel") or info.get("uploader") or "",
                "is_private": False,
                "is_verified": False,
                "biography": info.get("description") or "",
                "edge_followed_by": {"count": info.get("follower_count") or info.get("channel_follower_count") or 0},
                "edge_follow": {"count": 0},
                "edge_owner_to_timeline_media": {"count": 0},
                "profile_pic_url_hd": info.get("thumbnail") or "",
            }
            return user
    except Exception as e:
        errors.append(f"yt-dlp: {e}")

    raise ValueError(
        f"Could not fetch Instagram profile for '{username}'. "
        f"(Errors: {'; '.join(errors[-3:])})"
    )


@app.on_message(filters.command("igprofile"))
@language
async def ig_profile(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /igprofile <username>")
    username = message.command[1]
    msg = await message.reply_text("🔍 𝐅єᴛᴄʜɪηɢ ɪɴsᴛᴀɢʀᴀᴍ ᴘʀᴏғɪʟᴇ...")
    try:
        user = await _ig_profile(username)
    except ValueError as e:
        return await msg.edit_text(f"❌ {e}")
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to fetch profile: {e}")

    name = user.get("full_name") or ""
    followers = user.get("edge_followed_by", {}).get("count", 0)
    following = user.get("edge_follow", {}).get("count", 0)
    posts = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
    is_private = "𝐘𝐞𝐬 ✅" if user.get("is_private") else "𝐍σ ❌"
    is_verified = "𝐘𝐞𝐬 ✅" if user.get("is_verified") else "𝐍σ ❌"
    bio = user.get("biography") or "N/A"
    pic = user.get("profile_pic_url_hd") or user.get("profile_pic_url")

    text = [
        f"**{name}** (@{user.get('username')})",
        f"𝐅ᴏʟʟᴏᴡᴇʀs : {followers}",
        f"𝐅ᴏʟʟᴏᴡɪɴɢ : {following}",
        f"𝐏ᴏsᴛs : {posts}",
        f"𝐀ᴄᴄᴏᴜɴᴛ 𝐓ʏᴘᴇ : {'𝐏ʀɪᴠᴀᴛᴇ' if user.get('is_private') else '𝐏ᴜʙʟɪᴄ'}",
        f"𝐕ᴇʀɪғɪᴇᴅ : {is_verified}",
        f"𝐀ᴄᴛɪᴠᴇ 𝐒ᴛᴏʀʏ : {is_private}",
        f"✍️ 𝐁ɪᴏ : {bio}",
    ]
    text = "\n".join(text)
    try:
        if pic:
            await msg.delete()
            await message.reply_photo(pic, caption=text)
        else:
            await msg.edit_text(text)
    except Exception:
        try:
            await msg.edit_text(text)
        except Exception:
            pass


@app.on_message(filters.command("iginfo") & SUDOERS)
@language
async def ig_info(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /iginfo <username>")
    username = message.command[1]
    msg = await message.reply_text("🔍 𝐅єᴛᴄʜɪηɢ ɪɴsᴛᴀɢʀᴀᴍ ᴘʀᴏғɪʟᴇ...")
    try:
        user = await _ig_profile(username)
    except ValueError as e:
        return await msg.edit_text(f"❌ {e}")
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to fetch profile: {e}")
    name = user.get("full_name") or ""
    followers = user.get("edge_followed_by", {}).get("count", 0)
    bio = user.get("biography") or "N/A"
    pic = user.get("profile_pic_url_hd") or user.get("profile_pic_url")
    text = (
        f"**{name}** (@{user.get('username')})\n"
        f"𝐅ᴏʟʟᴏᴡᴇʀs : {followers}\n"
        f"𝐁ɪᴏ : {bio}"
    )
    try:
        if pic:
            await msg.delete()
            await message.reply_photo(pic, caption=text)
        else:
            await msg.edit_text(text)
    except Exception:
        pass


@app.on_message(filters.command(["igdl", "igv"]))
@language
async def ig_download(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /igdl <instagram URL>")
    url = message.command[1]
    if "instagram.com" not in url:
        return await message.reply_text(
            "❌ Please provide a valid Instagram URL (e.g. https://www.instagram.com/p/...)"
        )
    msg = await message.reply_text("📥 𝐃σᴡɴʟσᴀᴅɪηɢ ɪɴsᴛᴀɢʀᴀᴍ ᴍᴇᴅɪᴀ...")

    tmpdir = tempfile.mkdtemp(prefix="igdl_")
    opts = {
        "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "http_headers": {"User-Agent": IG_UA},
        "format": "best",
        "noplaylist": True,
    }
    opts.update(_IG_COOKIE_OPT)
    try:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(
            None, lambda: _ydl_extract(url, opts, tmpdir)
        )
        files = sorted(
            os.path.join(tmpdir, f) for f in os.listdir(tmpdir)
        )
        if not files:
            return await msg.edit_text("❌ No media found.")
        file_path = files[0]
        duration = (info or {}).get("duration") or "N/A"
        plays = (info or {}).get("view_count") or "N/A"
        caption = (
            f"𝐃ᴜʀᴀᴛɪᴏɴ : {duration}s\n"
            f"𝐏ʟᴀʏs : {plays}"
        )
        await msg.edit_text(caption)
        if file_path.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
            await message.reply_video(file_path, caption=caption)
        else:
            await message.reply_document(file_path, caption=caption)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
    finally:
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


def _ydl_extract(url: str, opts: dict, tmpdir: str) -> dict:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info or {}





async def ig_quick_info(url: str):
    """Extract metadata without downloading (used to confirm media)."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "http_headers": {"User-Agent": IG_UA},
    }
    opts.update(_IG_COOKIE_OPT)

    def _run():
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run)


def _ig_ydl_download(url: str, fmt: str, tmpdir: str) -> dict:
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
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=True) or {}


def _ig_process_image(path: str, quality: str) -> str:
    """Normalize image: 4K upscales small photos, 1080p caps large ones."""
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


async def ig_reel_download(url: str, quality: str) -> dict:
    """Download Instagram media and return local file list.

    quality: "1080p" (capped) or "4k" (photos upscaled).
    Returns {"files": [...], "info": {...}, "is_video": bool, "tmpdir": str|None}
    """
    tmpdir = tempfile.mkdtemp(prefix="reel_")
    try:
        fmt = "best[height<=1080]/best" if quality == "1080p" else "best"
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
            shutil.rmtree(tmpdir, ignore_errors=True)
            return {"files": [], "info": info, "is_video": False, "tmpdir": None}
        video_ext = (".mp4", ".mov", ".webm", ".mkv", ".m4v")
        is_video = any(f.lower().endswith(video_ext) for f in files)
        if not is_video:
            processed = []
            for f in files:
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    processed.append(_ig_process_image(f, quality))
                else:
                    processed.append(f)
            files = processed
        return {"files": files, "info": info, "is_video": is_video, "tmpdir": tmpdir}
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


async def ig_profile_entries(url: str, max_entries: int = 50):
    """List post URLs for an Instagram profile (used by /breel).

    Returns a list of (webpage_url, title) tuples, capped at max_entries.
    Raises ReelError on failure so callers can surface actionable errors
    (e.g. "private profile, configure IG_COOKIES") instead of getting
    a silent empty list.
    """


    from IotaXMedia.plugins.tools.instagram_reel import (
        _classify_error,
        MediaNotFoundError,
    )

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
        "playlistend": max_entries,
        "http_headers": {"User-Agent": IG_UA},
    }
    opts.update(_IG_COOKIE_OPT)

    def _run():
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _run)
    except Exception as e:



        classified = _classify_error(e)
        LOGGER(__name__).error(
            "ig_profile_entries: %s: %s", type(classified).__name__, e
        )
        raise classified from e
    if not info:


        raise MediaNotFoundError(
            f"ig_profile_entries returned None for {url!r}"
        )
    entries = info.get("entries") or []
    out = []
    for e in entries:
        if not e:
            continue
        u = e.get("url") or e.get("webpage_url")
        if u:
            out.append((u, e.get("title") or e.get("id") or ""))
        if len(out) >= max_entries:
            break
    return out
