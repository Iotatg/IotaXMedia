# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import time

import psutil
from pyrogram import filters
from pyrogram.enums import ParseMode

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.errors import capture_err, send_large_error
from IotaXMedia.utils.observability import collector, metrics
from IotaXMedia.utils.observability.format import (
    fmt_recent,
    fmt_top,
    fmt_crashlog,
    fmt_health,
    fmt_stats,
    chunk,
)


async def _boot_crash_report(client):
    try:
        if collector.had_crash():
            from IotaXMedia.utils.observability.reporter import send_boot_crash
            await send_boot_crash(collector.last())
    except Exception:
        pass





try:
    asyncio.get_event_loop().create_task(_boot_crash_report(app))
except Exception:
    pass


@app.on_message(filters.command(["errors"]) & SUDOERS)
@capture_err
async def errors_cmd(client, message):  # noqa
    n = 10
    if len(message.command) > 1:
        try:
            n = int(message.command[1])
        except Exception:
            pass
    text = fmt_recent(collector.recent(n), n)
    for part in chunk(text):
        await message.reply_text(part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["errorstats"]) & SUDOERS)
@capture_err
async def errorstats_cmd(client, message):
    text = fmt_top(collector.top(10), 10)
    for part in chunk(text):
        await message.reply_text(part, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["crashlog"]) & SUDOERS)
@capture_err
async def crashlog_cmd(client, message):
    rid = message.command[1] if len(message.command) > 1 else None
    rec = collector.get(rid) if rid else collector.last()
    text = fmt_crashlog(rec)
    if rec and len(text) > 4096:
        await send_large_error(
            rec.get("tb", ""), f"💥 Error {rec.get('id','')}", f"crashlog_{rec.get('id','')}"
        )
        await message.reply_text("⚠ Traceback bahut lamba hai — pura log LOGGER channel par bheja gaya.", quote=True)
        return
    await message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["health"]) & SUDOERS)
@capture_err
async def health_cmd(client, message):
    t0 = time.time()
    try:
        await app.get_me()
        ping = (time.time() - t0) * 1000
    except Exception:
        ping = -1.0
    mem = psutil.Process().memory_info().rss / 1024 / 1024
    qd = 0
    try:
        from IotaXMedia.utils.stream.stream import db
        qd = sum(len(v) for v in db.values())
    except Exception:
        pass
    ac = 0
    try:
        from IotaXMedia.utils.database import get_served_chats
        ac = len(await get_served_chats())
    except Exception:
        pass
    text = fmt_health(metrics.snapshot(), ping, ac, qd, mem)
    await message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@app.on_message(filters.command(["botstats", "iostat"]) & SUDOERS)
@capture_err
async def stats_cmd(client, message):
    text = fmt_stats(metrics.snapshot(), metrics.api_latency_avg(), metrics.error_rate())
    await message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
