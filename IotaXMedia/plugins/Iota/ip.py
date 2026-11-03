# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import edit_message_text_colored, styled_button

import asyncio
import httpx
import ipaddress
import html
import os

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")
IPQUALITYSCORE_API_KEY = os.getenv("IPQUALITYSCORE_API_KEY", "")



def _flag_emoji(country_code: str | None) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    cc = country_code.upper()
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc)

def _score_badge(score: int | None) -> tuple[str, str]:
    if score is None:
        return "❓ Unknown", "░░░░░░░░░░ 0/100"
    blocks = max(0, min(10, round(score / 10)))
    bar = "█" * blocks + "░" * (10 - blocks)
    if score <= 20:
        return "✅ Low Risk", f"{bar} {score}/100"
    elif score <= 60:
        return "⚠️ Medium Risk", f"{bar} {score}/100"
    else:
        return "❌ High Risk", f"{bar} {score}/100"

def _escape(v: str | None) -> str:
    return html.escape(v or "N/A")

def _split_asn_org(org: str | None) -> tuple[str, str]:
    if not org:
        return "N/A", "N/A"

    parts = org.split(maxsplit=1)
    if parts and parts[0].startswith("AS"):
        asn = parts[0]
        isp = parts[1] if len(parts) > 1 else "N/A"
        return asn, isp
    return "N/A", org

def _build_card(ip: str, info: dict, score: int | None) -> tuple[str, InlineKeyboardMarkup, list]:
    country = info.get("country")
    flag = _flag_emoji(country)
    city = info.get("city")
    region = info.get("region")
    loc = info.get("loc")
    org = info.get("org")
    timezone = info.get("timezone")
    postal = info.get("postal")
    asn, isp = _split_asn_org(org)

    badge, bar = _score_badge(score)


    s_ip      = _escape(ip)
    s_city    = _escape(city)
    s_region  = _escape(region)
    s_country = _escape(country)
    s_postal  = _escape(postal)
    s_tz      = _escape(timezone)
    s_asn     = _escape(asn)
    s_isp     = _escape(isp)


    maps_q = loc.replace(" ", "") if loc else ""
    maps_url = f"https://maps.google.com/?q={maps_q}" if maps_q else f"https://duckduckgo.com/?q={s_ip}"
    ipinfo_url = f"https://ipinfo.io/{s_ip}"
    ipqs_url = f"https://www.ipqualityscore.com/free-ip-lookup-proxy-vpn-test/lookup/{s_ip}"
    abuse_url = f"https://www.abuseipdb.com/check/{s_ip}"

    text = (
        "<b>🔎 IP ɪɴᴛᴇʟʟɪɢᴇɴᴄᴇ</b>\n"
        f"{flag} <b>{s_ip}</b>\n"
        "\n"
        "┏━━━━━━━━━━━━━━━━━━━\n"
        f"┃ <b>ʀɪsᴋ</b> : {badge}\n"
        f"┃ <code>{bar}</code>\n"
        "┗━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        f"🏙️ <b>ᴄɪᴛʏ</b> : <code>{s_city}</code>\n"
        f"🗺️ <b>ʀᴇɢɪᴏɴ</b> : <code>{s_region}</code>\n"
        f"🌍 <b>ᴄᴏᴜɴᴛʀʏ</b> : <code>{s_country}</code>\n"
        f"📮 <b>ᴘᴏsᴛᴀʟ</b> : <code>{s_postal}</code>\n"
        f"🕒 <b>ᴛɪᴍᴇᴢᴏɴᴇ</b> : <code>{s_tz}</code>\n"
        f"🏢 <b>ISP</b> : <code>{s_isp}</code>\n"
        f"🔢 <b>ASN</b> : <code>{s_asn}</code>\n"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🗺️ ᴠɪᴇᴡ ᴏɴ ᴍᴀᴘs", url=maps_url, style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("ℹ️ ɪᴘɪɴғᴏ", url=ipinfo_url, style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("🛡️ IPQuᴀʟɪᴛʏSᴄᴏʀᴇ", url=ipqs_url, style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("🚫 AʙᴜsᴇIPDB", url=abuse_url, style=enums.ButtonStyle.PRIMARY),
            ],
        ]
    )
    keyboard_col = [
        [
            styled_button("🗺️ ᴠɪᴇᴡ ᴏɴ ᴍᴀᴘs", url=maps_url, style="primary"),
            styled_button("ℹ️ ɪᴘɪɴғᴏ", url=ipinfo_url, style="primary"),
        ],
        [
            styled_button("🛡️ IPQuᴀʟɪᴛʏSᴄᴏʀᴇ", url=ipqs_url, style="primary"),
            styled_button("🚫 AʙᴜsᴇIPDB", url=abuse_url, style="danger"),
        ],
    ]
    return text, keyboard, keyboard_col



async def fetch_ipinfo(client: httpx.AsyncClient, ip: str) -> dict | None:
    url = f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}"
    try:
        r = await client.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

async def fetch_ipqs(client: httpx.AsyncClient, ip: str) -> int | None:
    url = f"https://ipqualityscore.com/api/json/ip/{IPQUALITYSCORE_API_KEY}/{ip}"
    try:
        r = await client.get(url, timeout=12)
        if r.status_code == 200:
            data = r.json()
            fs = data.get("fraud_score")
            return int(fs) if isinstance(fs, (int, float, str)) and str(fs).isdigit() else None
    except Exception:
        pass
    return None



@app.on_message(filters.command(["ip"]))
async def ip_info_and_score(_, message):
    if len(message.command) != 2:
        await message.reply_text(
            "ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀɴ IP ᴀᴅᴅʀᴇss.\n"
            "Exᴀᴍᴘʟᴇ: <code>/ip 8.8.8.8</code>",
            disable_web_page_preview=True,
        )
        return

    ip_raw = message.command[1].strip()


    try:
        ip_obj = ipaddress.ip_address(ip_raw)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_multicast:
            await message.reply_text(
                "Tʜᴀᴛ ʟᴏᴏᴋs ʟɪᴋᴇ ᴀ <b>ɴᴏɴ-ʀᴏᴜᴛᴀʙʟᴇ</b> ᴏʀ <b>ᴘʀɪᴠᴀᴛᴇ</b> ᴀᴅᴅʀᴇss. "
                "Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴘᴜʙʟɪᴄ IP.",
                disable_web_page_preview=True,
            )
            return
    except ValueError:
        await message.reply_text(
            "Iɴᴠᴀʟɪᴅ IP ғᴏʀᴍᴀᴛ. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ IPv4 ᴏʀ IPv6 ᴀᴅᴅʀᴇss.\n"
            "Exᴀᴍᴘʟᴇ: <code>/ip 1.1.1.1</code>",
            disable_web_page_preview=True,
        )
        return

    wait_msg = await message.reply_text("ᴀɴᴀʟʏᴢɪɴɢ IP… <i>ғᴇᴛᴄʜɪɴɢ ɪɴᴛᴇʟʟɪɢᴇɴᴄᴇ</i> 🔍")

    async with httpx.AsyncClient(headers={"User-Agent": "IotaX/IpIntel/1.0"}) as client:
        ipinfo_task = fetch_ipinfo(client, ip_raw)
        ipqs_task = fetch_ipqs(client, ip_raw)
        ipinfo, score = await asyncio.gather(ipinfo_task, ipqs_task)

    if not ipinfo and score is None:
        await wait_msg.edit_text(
            "ᴜɴᴀʙʟᴇ ᴛᴏ ғᴇᴛᴄʜ ᴅᴇᴛᴀɪʟs ғᴏʀ ᴛʜᴇ ᴘʀᴏᴠɪᴅᴇᴅ IP ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ."
        )
        return

    text, keyboard, keyboard_col = _build_card(ip_raw, ipinfo or {}, score)
    try:
        r = await edit_message_text_colored(
            wait_msg.chat.id,
            wait_msg.id,
            text,
            keyboard_col,
            disable_web_page_preview=True,
        )
        if r:
            return
    except Exception:
        pass
    try:
        await wait_msg.edit_text(
            text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except MessageNotModified:
        return
