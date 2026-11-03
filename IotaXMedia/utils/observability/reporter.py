
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from config import LOGGER_ID
import html


def _esc(t):
    return html.escape(str(t))


async def _send(text):
    if not LOGGER_ID:
        return
    try:
        from pyrogram.enums import ParseMode
        from IotaXMedia import app
        await app.send_message(LOGGER_ID, text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception:
        pass


async def send_boot_crash(rec):
    if not rec:
        return
    tb_escaped = _esc(rec.get('tb', '') or '')[:3500]
    msg = (
        "💥 <b>Last run crashed (unclean shutdown)</b>\n"
        f"📍 <code>{_esc(rec.get('type',''))}</code>\n"
        f"🧬 <code>{_esc(rec.get('fingerprint',''))}</code>\n"
        f"🕒 {_esc(rec.get('last_seen',''))}\n\n"
        f"<pre>{tb_escaped}</pre>"
    )
    await _send(msg)


async def send_spike(fp, etype, count, window):
    msg = (
        f"⚠ <b>Error spike detected</b>\n"
        f"<code>{_esc(etype)}</code> ×{count} in {window}s\n"
        f"🧬 <code>{_esc(fp)}</code>"
    )
    await _send(msg)
