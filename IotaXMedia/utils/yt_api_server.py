# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""YouTube download API server (lightweight, cookieless, threaded).

Implements the polling protocol expected by downloader.py:
  GET /song/<vid>?api=<key>   ->  audio
  GET /video/<vid>?api=<key>  ->  video

Response:
  {"status":"downloading"}              -> retry in 1s
  {"status":"done","link":"...","format":"..."}  -> fetch /dl/<fname>
"""

import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from IotaXMedia.core.dir import DOWNLOAD_DIR
from IotaXMedia.logging import LOGGER

LOG = LOGGER(__name__)
PORT = int(os.environ.get("YT_PROXY_PORT", "9091"))
API_KEY = os.environ.get("YT_API_KEY", "local")

DOWNLOAD_ROOT = os.path.join(DOWNLOAD_DIR, "api_downloads")

os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

_store: dict[str, dict] = {}
_lock = threading.Lock()


def _yt_dl(vid: str, kind: str) -> str | None:
    """Download via yt-dlp (deno JS solving; web/tv clients)."""
    import glob as _g

    from IotaXMedia.utils.downloader import _ensure_js_runtime, get_ytdlp_base_opts


    _ensure_js_runtime()

    from yt_dlp import YoutubeDL

    fmt = "bestaudio/best" if kind == "audio" else "best[height<=1080]/best"
    link = f"https://www.youtube.com/watch?v={vid}"
    opts = get_ytdlp_base_opts()
    opts["format"] = fmt
    opts["outtmpl"] = f"{DOWNLOAD_ROOT}/%(id)s.%(ext)s"
    opts["socket_timeout"] = 60
    opts["retries"] = 2
    opts["fragment_retries"] = 2
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True) or {}
            _vid = info.get("id")
            ext = info.get("ext")
            if _vid and ext:
                p = f"{DOWNLOAD_ROOT}/{_vid}.{ext}"
                if os.path.isfile(p) and os.path.getsize(p) > 1024:
                    return p
            if _vid:
                for f in sorted(_glob.glob(f"{DOWNLOAD_ROOT}/{_vid}.*"),
                               key=os.path.getmtime, reverse=True):
                    if os.path.isfile(f) and os.path.getsize(f) > 1024 and not f.endswith(".part"):
                        return f
    except Exception:
        pass
    return None


def _bg_download(vid: str, kind: str):
    key = f"{kind}:{vid}"
    LOG.info(f"API background download starting: {vid} ({kind})")
    filepath = _yt_dl(vid, kind)
    with _lock:
        if filepath:
            fname = os.path.basename(filepath)
            ext = fname.rsplit(".", 1)[-1] if "." in fname else ("mp4" if kind == "video" else "webm")
            _store[key] = {"status": "done", "file": fname, "format": ext}
            LOG.info(f"API download OK: {vid} ({kind})")
        else:
            _store[key] = {"status": "failed"}
            LOG.warning(f"API download FAIL: {vid} ({kind})")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _fmt, *_args):
        pass

    def _err(self, c, b=b"{}"):
        self.send_response(c)
        self.end_headers()
        self.wfile.write(b)

    def _json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        p = urlparse(self.path)
        if p.path in ("/", "/ping", "/health"):
            return self._json({"ok": True})

        qs = parse_qs(p.query)
        _sent_key = qs.get("api", [""])[0]

        if p.path.startswith("/dl/"):
            fname = os.path.basename(p.path[len("/dl/"):])
            fp = os.path.join(DOWNLOAD_ROOT, fname)
            if os.path.isfile(fp):
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(fp, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._err(404)
            return

        if _sent_key != API_KEY:
            return self._err(403)

        if p.path.startswith("/song/") or p.path.startswith("/video/"):
            parts = p.path.strip("/").split("/")
            if len(parts) < 2:
                return self._err(400)
            kind, vid = parts[0], parts[1]
            self._handle_polling(vid, kind)
            return

        self._err(404)

    def _handle_polling(self, vid: str, kind: str):
        key = f"{kind}:{vid}"
        with _lock:
            ent = _store.get(key)
            if ent is None:
                _store[key] = {"status": "downloading", "file": "", "format": ""}
                threading.Thread(target=_bg_download, args=(vid, kind), daemon=True).start()
                return self._json({"status": "downloading"})
            st = ent.get("status", "")
            if st == "done":
                link = f"http://localhost:{PORT}/dl/{ent['file']}"
                return self._json({"status": "done", "link": link, "format": ent.get("format", "webm")})
            if st == "failed":
                return self._json({"status": "failed"})
            return self._json({"status": "downloading"})


_server: HTTPServer | None = None


def start():
    global _server
    _server = HTTPServer(("0.0.0.0", PORT), Handler)
    LOG.info(f"YT API server started on 0.0.0.0:{PORT}")
    _server.serve_forever()


def stop():
    global _server
    if _server:
        _server.shutdown()


def launch_thread():
    t = threading.Thread(target=start, daemon=True)
    t.start()
    return t