# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Download-and-send multimodal helper for Iota chatbot (GLM then Gemini)."""
import base64
import logging
import os
import re
import threading
import zlib

import httpx

logger = logging.getLogger(__name__)

KIND_PHOTO = "photo"
KIND_VIDEO = "video"
KIND_AUDIO = "audio"
KIND_DOCUMENT = "document"
KIND_SKIP = "skip"

PHOTO_MAX = 5 * 1024 * 1024
VIDEO_MAX = 20 * 1024 * 1024
OTHER_MAX = 15 * 1024 * 1024

IMAGE_MIMES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
AUDIO_FORMATS = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/ogg": "ogg",
    "audio/opus": "ogg",
    "audio/ogg; codecs=opus": "ogg",
    "audio/webm": "wav",
    "audio/mp4": "mp3",
    "audio/m4a": "mp3",
    "audio/x-m4a": "mp3",
}
AUDIO_EXTS = {".wav": "wav", ".mp3": "mp3", ".ogg": "ogg", ".opus": "ogg", ".m4a": "mp3"}
AUDIO_MIME_FOR_FMT = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
}
VIDEO_MIMES = {
    "video/mp4", "video/mpeg", "video/quicktime", "video/webm",
    "video/x-matroska", "video/avi", "video/x-msvideo",
}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".mpeg", ".mpg", ".avi", ".m4v"}
PDF_MIMES = {"application/pdf"}
PDF_EXTS = {".pdf"}
_BLIND_RE = re.compile(
    r"(attach nahi|nahi hui|nahi hua|nahi hai yahan|"
    r"blank dikh|kuch dikh|kuch attach|"
    r"pdf khul nahi|khul nahi raha|khul hi nahi|"
    r"koi video nahi|koi file nahi|koi audio nahi|"
    r"file attach|video nahi|"
    r"don't see|do not see|nothing attached|"
    r"no (video|file|audio|image|attachment)|"
    r"can't (see|open|play|read)|cannot (see|open|play|read)|"
    r"not attached|didn't (get|receive|see)|did not (get|receive|see)|"
    r"unable to (see|open|play|read)|couldn't (see|open|play|read))",
    re.I,
)

MSG_TOO_BIG = "ye file badi hai yaar, chhoti bhej"
MSG_DOWNLOAD_FAIL = "abhi download nahi ho paayi"
MSG_ANALYZE_FAIL = "abhi dekh nahi paayi"
MSG_BUSY = "ek sec, pehle wali dekh rahi hoon"
EMPTY_CAPTION = "look at this"
MEDIA_SYSTEM = (
    "You are Iota, 19, from mumbai, chatting on telegram. "
    "Reply 1-2 messy lowercase hinglish lines about the actual photo, video, audio or file. "
    "Never say you are ai. No lists. No english essay."
)
ANALYZE_MAX_TOKENS = 4096

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_MAX_IN_FLIGHT = 2
_in_flight = 0
_slot_lock = threading.Lock()


def classify(message) -> str:
    if getattr(message, "sticker", None) or getattr(message, "animation", None):
        return KIND_SKIP
    if getattr(message, "photo", None):
        return KIND_PHOTO
    if getattr(message, "video", None) or getattr(message, "video_note", None):
        return KIND_VIDEO
    if getattr(message, "voice", None) or getattr(message, "audio", None):
        return KIND_AUDIO
    if getattr(message, "document", None):
        return KIND_DOCUMENT
    return KIND_SKIP


def _media_obj(message, kind):
    if kind == KIND_PHOTO:
        return getattr(message, "photo", None)
    if kind == KIND_VIDEO:
        return getattr(message, "video", None) or getattr(message, "video_note", None)
    if kind == KIND_AUDIO:
        return getattr(message, "voice", None) or getattr(message, "audio", None)
    if kind == KIND_DOCUMENT:
        return getattr(message, "document", None)
    return None


def media_meta(message, kind) -> tuple[str | None, str | None, int]:
    obj = _media_obj(message, kind)
    if obj is None:
        return None, None, 0
    mime = getattr(obj, "mime_type", None)
    filename = getattr(obj, "file_name", None)
    size = int(getattr(obj, "file_size", 0) or 0)
    return mime, filename, size


def is_image(mime: str | None, filename: str | None) -> bool:
    if mime and mime.lower() in IMAGE_MIMES:
        return True
    name = (filename or "").lower()
    return any(name.endswith(ext) for ext in IMAGE_EXTS)


def audio_format(mime: str | None, filename: str | None) -> str | None:
    if mime:
        key = mime.lower().split(";")[0].strip()
        if key in AUDIO_FORMATS:
            return AUDIO_FORMATS[key]
        full = mime.lower()
        if full in AUDIO_FORMATS:
            return AUDIO_FORMATS[full]
    name = (filename or "").lower()
    for ext, fmt in AUDIO_EXTS.items():
        if name.endswith(ext):
            return fmt
    return None


def size_limit(kind: str, mime: str | None = None, filename: str | None = None) -> int:
    if kind == KIND_PHOTO or (kind == KIND_DOCUMENT and is_image(mime, filename)):
        return PHOTO_MAX
    if kind == KIND_VIDEO or (kind == KIND_DOCUMENT and is_video(mime, filename)):
        return VIDEO_MAX
    return OTHER_MAX


def over_size(kind: str, size: int, mime: str | None = None, filename: str | None = None) -> bool:
    return size > size_limit(kind, mime, filename)


TEXT_MIMES = {
    "text/plain", "text/markdown", "text/html", "text/css",
    "text/javascript", "text/xml", "text/csv", "text/yaml",
    "text/yaml", "application/json", "application/javascript",
    "application/xml", "application/x-yaml", "application/x-httpd-php",
}
TEXT_EXTS = {".md", ".txt", ".py", ".html", ".htm", ".css", ".js", ".json",
             ".csv", ".xml", ".yaml", ".yml", ".sh", ".toml", ".ini",
             ".cfg", ".conf", ".sql", ".vue", ".tsx", ".ts", ".jsx",
             ".java", ".c", ".cpp", ".h", ".rb", ".go", ".rs", ".php",
             ".swift", ".kt", ".scala", ".r", ".m", ".lua", ".pl",
             ".pm", ".t", ".sh", ".bat", ".cmd", ".txt", ".md", ".mkd"}


def is_text_based(mime: str | None, filename: str | None) -> bool:
    if mime and mime.lower() in TEXT_MIMES:
        return True
    name = (filename or "").lower()
    return any(name.endswith(ext) for ext in TEXT_EXTS)


def is_video(mime: str | None, filename: str | None) -> bool:
    if mime and mime.lower().split(";")[0].strip() in VIDEO_MIMES:
        return True
    name = (filename or "").lower()
    return any(name.endswith(ext) for ext in VIDEO_EXTS)


def is_pdf(mime: str | None, filename: str | None) -> bool:
    if mime and mime.lower().split(";")[0].strip() in PDF_MIMES:
        return True
    name = (filename or "").lower()
    return any(name.endswith(ext) for ext in PDF_EXTS)


def read_text_content(path: str, max_bytes: int = 50000) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except Exception:
        return None


def _pdf_decode_literal(raw: bytes) -> str:
    out: list[str] = []
    i = 0
    while i < len(raw):
        if raw[i] == 92 and i + 1 < len(raw):
            nxt = raw[i + 1]
            if nxt in b"nrtbf()\\":
                mapped = {ord("n"): "\n", ord("r"): "\r", ord("t"): "\t", ord("b"): "\b", ord("f"): "\f"}
                out.append(mapped.get(nxt, chr(nxt)))
                i += 2
                continue
            if 48 <= nxt <= 55:
                j = i + 1
                octal = b""
                while j < len(raw) and len(octal) < 3 and 48 <= raw[j] <= 55:
                    octal += bytes([raw[j]])
                    j += 1
                out.append(chr(int(octal, 8)))
                i = j
                continue
            i += 2
            continue
        out.append(chr(raw[i]) if raw[i] < 128 else "?")
        i += 1
    return "".join(out)


def _pdf_from_stream(data: bytes) -> str:
    texts: list[str] = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        blob = m.group(1)
        candidates = [blob]
        try:
            candidates.append(zlib.decompress(blob))
        except Exception:
            pass
        for cand in candidates:
            for lit in re.finditer(rb"\((?:\\.|[^\\()])*\)", cand):
                decoded = _pdf_decode_literal(lit.group(0)[1:-1])
                if any(ch.isalpha() for ch in decoded):
                    texts.append(decoded)
            for hexpart in re.finditer(rb"<([0-9A-Fa-f\s]+)>", cand):
                hx = re.sub(rb"\s+", b"", hexpart.group(1))
                if len(hx) % 2:
                    hx += b"0"
                try:
                    decoded = bytes.fromhex(hx.decode("ascii")).decode("latin-1", errors="ignore")
                except Exception:
                    continue
                if any(ch.isalpha() for ch in decoded):
                    texts.append(decoded)
    return " ".join(texts)


def extract_pdf_text(path: str, max_chars: int = 20000) -> str | None:
    try:
        with open(path, "rb") as f:
            data = f.read()
        if not data.startswith(b"%PDF"):
            return None
        text = _pdf_from_stream(data)
        if not text.strip():
            bits = []
            for lit in re.finditer(rb"\((?:\\.|[^\\()])*\)", data):
                decoded = _pdf_decode_literal(lit.group(0)[1:-1])
                if any(ch.isalpha() for ch in decoded):
                    bits.append(decoded)
            text = " ".join(bits)
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:max_chars] if cleaned else None
    except Exception:
        return None


def looks_blind(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    return bool(_BLIND_RE.search(t))


def to_content_part(path: str, kind: str, mime: str | None, filename: str | None) -> dict:
    if is_text_based(mime, filename):
        content = read_text_content(path)
        if content:
            return {"type": "text", "text": content}
    if is_pdf(mime, filename):
        pdf_text = extract_pdf_text(path)
        if pdf_text:
            return {"type": "text", "text": f"[pdf]\n{pdf_text}", "_kind": kind}
    with open(path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")
    if kind == KIND_PHOTO or (kind == KIND_DOCUMENT and is_image(mime, filename)):
        use = (mime or "image/jpeg").lower()
        if use == "image/jpg":
            use = "image/jpeg"
        return {"type": "image_url", "image_url": {"url": f"data:{use};base64,{b64}"}, "_kind": kind}
    if kind == KIND_VIDEO or (kind == KIND_DOCUMENT and is_video(mime, filename)):
        use = mime or "video/mp4"
        return {"type": "video_url", "video_url": {"url": f"data:{use};base64,{b64}"}, "_kind": KIND_VIDEO}
    if kind == KIND_AUDIO or (kind == KIND_DOCUMENT and audio_format(mime, filename)):
        fmt = audio_format(mime, filename) or "ogg"
        return {"type": "input_audio", "input_audio": {"data": b64, "format": fmt}, "_kind": KIND_AUDIO}
    use = mime or "application/octet-stream"
    file_block: dict = {"file_data": f"data:{use};base64,{b64}"}
    if filename:
        file_block["filename"] = filename
    return {"type": "file", "file": file_block, "_kind": kind}


def as_file_part(part: dict, filename: str = "media.bin") -> dict:
    if part.get("type") == "file":
        return part
    if part.get("type") == "input_audio":
        block = part.get("input_audio") or {}
        data = block.get("data") or ""
        fmt = block.get("format") or "ogg"
        mime = AUDIO_MIME_FOR_FMT.get(fmt, "audio/ogg")
        return {
            "type": "file",
            "file": {
                "file_data": f"data:{mime};base64,{data}",
                "filename": filename or f"voice.{fmt}",
            },
        }
    url = ""
    if part.get("type") == "video_url":
        url = (part.get("video_url") or {}).get("url") or ""
        filename = filename or "video.mp4"
    elif part.get("type") == "image_url":
        url = (part.get("image_url") or {}).get("url") or ""
        filename = filename or "image.jpg"
    return {"type": "file", "file": {"file_data": url, "filename": filename}}


def as_input_audio_part(part: dict) -> dict:
    if part.get("type") == "input_audio":
        return part
    if part.get("type") != "file":
        return part
    block = part.get("file") or {}
    data = block.get("file_data") or ""
    filename = block.get("filename") or "voice.ogg"
    mime = "audio/ogg"
    if data.startswith("data:") and ";base64," in data:
        header, data = data.split(";base64,", 1)
        mime = header[5:]
    fmt = audio_format(mime, filename) or "ogg"
    return {"type": "input_audio", "input_audio": {"data": data, "format": fmt}}


def user_content(part: dict, user_text: str) -> list:
    caption = (user_text or "").strip() or EMPTY_CAPTION
    text = f"{MEDIA_SYSTEM}\n\n{caption}"
    return [{"type": "text", "text": text}, part]


def strip_thinking(text: str) -> str:
    cleaned = _THINK_RE.sub("", text or "")
    return cleaned.strip()


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        bits = []
        for item in content:
            if isinstance(item, str):
                bits.append(item)
            elif isinstance(item, dict):
                bits.append(str(item.get("text") or ""))
        return " ".join(bits)
    return ""


def extract_reply(data: dict) -> str:
    if not isinstance(data, dict):
        return ""
    ch = (data.get("choices") or [{}])[0] or {}
    msg = ch.get("message") or {}
    text = _content_text(msg.get("content"))
    if not text:
        text = _content_text(ch.get("text"))
    return strip_thinking(text)


def _parts_to_try(part: dict) -> list:
    kind = part.get("type")
    if kind == "video_url":
        return [part, as_file_part(part, "video.mp4")]
    if kind == "input_audio":
        return [part, as_file_part(part, "voice.ogg")]
    if kind == "file":
        filename = ((part.get("file") or {}).get("filename") or "").lower()
        mime_guess = ((part.get("file") or {}).get("file_data") or "")[:40]
        if "audio" in mime_guess or any(filename.endswith(ext) for ext in AUDIO_EXTS):
            return [part, as_input_audio_part(part)]
    return [part]


async def try_acquire_slot() -> bool:
    global _in_flight
    with _slot_lock:
        if _in_flight >= _MAX_IN_FLIGHT:
            return False
        _in_flight += 1
        return True


def release_slot() -> None:
    global _in_flight
    with _slot_lock:
        if _in_flight > 0:
            _in_flight -= 1


def _payload_for(model: str, part: dict, user_text: str) -> dict:
    clean = {k: v for k, v in part.items() if k != "_kind"}
    return {
        "model": model,
        "messages": [
            {"role": "user", "content": user_content(clean, user_text)},
        ],
        "max_tokens": ANALYZE_MAX_TOKENS,
        "temperature": 0.45,
        "thinking": {"type": "disabled"},
        "chat_template_kwargs": {"enable_thinking": False},
    }


async def analyze(
    api_url: str,
    api_key: str,
    models: list[str],
    system: str,
    user_text: str,
    part: dict,
) -> str:
    del system
    ptype = part.get("type", "?")
    kind = part.get("_kind", "?")
    if ptype in ("video_url", "input_audio"):
        gemini = [m for m in models if "gemini" in m.lower()]
        rest = [m for m in models if "gemini" not in m.lower()]
        models = gemini + rest
    if kind not in ("photo", "image"):
        logger.info("media analyze kind=%s type=%s models=%s", kind, ptype, [m.split("/")[-1] for m in models])
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    async with httpx.AsyncClient(timeout=180, verify=False) as client:
        for candidate in models:
            parts = _parts_to_try(part)
            for i, try_part in enumerate(parts):
                payload = _payload_for(candidate, try_part, user_text)
                try:
                    resp = await client.post(api_url, json=payload, headers=headers)
                    if resp.status_code >= 400 and i < len(parts) - 1:
                        logger.warning(
                            "media analyze %s part=%s http=%s",
                            candidate,
                            try_part.get("type"),
                            resp.status_code,
                        )
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    reply = extract_reply(data)
                    if reply:
                        if looks_blind(reply):
                            logger.warning(
                                "media analyze %s blind reply part=%s: %s",
                                candidate,
                                try_part.get("type"),
                                reply[:120],
                            )
                            continue
                        return reply
                    ch = (data.get("choices") or [{}])[0] or {}
                    logger.warning(
                        "media analyze %s empty finish=%s usage=%s part=%s",
                        candidate,
                        ch.get("finish_reason"),
                        data.get("usage"),
                        try_part.get("type"),
                    )
                except Exception as e:
                    logger.warning("media analyze %s failed: %s", candidate, e)
                    continue
    return ""


def unlink(path: str | None) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
