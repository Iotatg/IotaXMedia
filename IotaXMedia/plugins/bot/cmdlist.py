# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils.decorators import language
from IotaXMedia.utils.god_style import god_text

GROUPS = [
    ("❥ " + god_text("community & chat"), [
        ("/boost", god_text("show chat boost level + next perk")),
        ("/topic", god_text("create a forum queue topic; now-playing routes there")),
        ("/reactions", god_text("show total reactions on the live track")),
        ("/like", god_text("react ❤ on the live now-playing card")),
        ("/stats", god_text("per-chat plays + top tracks")),
        ("/translate <lang>", god_text("auto-translate now-playing to a language")),
        ("/tr <lang>", god_text("translate a replied message")),
    ]),
    ("❥ " + god_text("playback control"), [
        ("/playat HH:MM <song>", god_text("schedule a track to auto-play later")),
        ("/sleep <mins>", god_text("stop playback after N minutes")),
        ("/pin", god_text("pin the live now-playing card")),
        ("/unpin", god_text("unpin the now-playing card")),
    ]),
    ("❥ " + god_text("modern surface"), [
        ("/player", god_text("open the Mini-App web player (needs IOTAX_MINIAPP_URL)")),
        ("/tip <stars>", god_text("send a Telegram Stars tip invoice")),
        ("/gift <id>", god_text("send a chat gift (Bot API 9.x+)")),
        ("/story", god_text("post replied media as a Story (Bot API 8.x+, private)")),
    ]),
    ("❥ " + god_text("info utilities"), [
        ("/ip <address>", god_text("ip location + isp details")),
        ("/dns <domain>", god_text("dns records (a/aaaa/mx/txt/ns)")),
        ("/weather <city>", god_text("live weather + 9h outlook")),
        ("/aqi <city>", god_text("air quality index + pollutants")),
        ("/pin <pincode>", god_text("post offices for an indian pincode")),
        ("/ifsc <code>", god_text("bank branch details by ifsc")),
        ("/git <user>", god_text("github profile + recent repos")),
    ]),
]


@app.on_message(filters.command(["cmdlist", "newcmds"]) & filters.group)
@language
async def cmdlist_command(client, message: Message, _):
    text = f"🆕 {god_text('new commands in iotaxmedia')} :\n\n"
    for title, rows in GROUPS:
        text += f"{title} :\n"
        for cmd, desc in rows:
            text += f"  <code>{cmd}</code> — {desc}\n"
        text += "\n"
    text += god_text("admin-gated commands need admin rights in the chat")
    await message.reply_text(text, disable_web_page_preview=True)
