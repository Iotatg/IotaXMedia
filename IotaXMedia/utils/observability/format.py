
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import html

MAX_MSG = 4096


def esc(t):
    return html.escape(str(t))


def chunk(text, limit=MAX_MSG):
    if len(text) <= limit:
        return [text]
    return [text[i:i + limit] for i in range(0, len(text), limit)]


def fmt_recent(records, n=10):
    rows = []
    for r in records[:n]:
        rows.append(
            f"• <b>{esc(r.get('type',''))}</b> ×{r.get('count',1)}\n"
            f"  <code>{esc(r.get('fingerprint',''))}</code>\n"
            f"  🕒 {esc(r.get('last_seen','?'))} · {esc(r.get('label',''))}"
        )
    if not rows:
        return "✅ No errors recorded."
    return "📋 <b>Recent Errors</b> (newest first):\n\n" + "\n\n".join(rows)


def fmt_top(records, n=10):
    total = sum(r.get("count", 1) for r in records) or 1
    rows = []
    for i, r in enumerate(records[:n], 1):
        pct = round(100 * r.get("count", 1) / total)
        rows.append(
            f"{i}. <b>{esc(r.get('type',''))}</b> ×{r.get('count',1)} ({pct}%)\n"
            f"   <code>{esc(r.get('fingerprint',''))}</code>"
        )
    if not rows:
        return "✅ No errors to rank."
    return "📊 <b>Top Errors by Frequency</b>:\n\n" + "\n\n".join(rows)


def fmt_crashlog(rec):
    if not rec:
        return "❌ No record found."
    return (
        f"💥 <b>Error {esc(rec.get('id',''))}</b>\n"
        f"📍 <b>Type:</b> <code>{esc(rec.get('type',''))}</code>\n"
        f"🧬 <code>{esc(rec.get('fingerprint',''))}</code>\n"
        f"🔁 Count: {rec.get('count',1)}\n"
        f"🕒 First: {esc(rec.get('first_seen',''))}\n"
        f"🕒 Last: {esc(rec.get('last_seen',''))}\n"
        f"📌 Extras: <code>{esc(rec.get('extras',{}))}</code>\n\n"
        f"<b>Traceback:</b>\n<pre>{esc(rec.get('tb',''))}</pre>"
    )


def fmt_health(snap, ping_ms, active_chats, queue_depth, memory_mb):
    up = snap.get("uptime", 0)
    h = int(up // 3600); m = int((up % 3600) // 60)
    c = snap.get("counters", {})
    return (
        "🩺 <b>Bot Health</b>\n"
        f"⏱ Uptime: {h}h {m}m\n"
        f"🏓 Ping: {ping_ms:.1f} ms\n"
        f"💬 Active chats: {active_chats}\n"
        f"🎶 Queue depth: {queue_depth}\n"
        f"🧠 Memory: {memory_mb:.1f} MB\n"
        f"⚡ Commands served: {c.get('commands_served',0)}\n"
        f"❌ Errors total: {c.get('errors_total',0)}"
    )


def fmt_stats(snap, api_latency, error_rate):
    c = snap.get("counters", {})
    return (
        "📈 <b>Bot Stats</b>\n"
        f"⚡ Commands served: {c.get('commands_served',0)}\n"
        f"🎶 Songs played: {c.get('songs_played',0)}\n"
        f"❌ Errors total: {c.get('errors_total',0)}\n"
        f"🌐 API calls: {c.get('api_calls',0)}\n"
        f"⏱ Avg API latency: {api_latency:.1f} ms\n"
        f"🔥 Error rate: {error_rate:.2f}/min"
    )
