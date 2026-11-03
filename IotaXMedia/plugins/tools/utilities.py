# Authored By Iota Coders (utility & info commands)
# SPDX-License-Identifier: MIT
import asyncio

import httpx
from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.decorators.language import language


async def _get(url: str, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()


@app.on_message(filters.command("crypto") & (SUDOERS | filters.group))
@language
async def crypto(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /crypto <symbol>  e.g. /crypto bitcoin")
    symbol = message.command[1].lower()
    msg = await message.reply_text("🔄 Fetching...")
    try:
        data = await _get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": symbol,
                "per_page": 1,
                "price_change_percentage": "24h",
            },
        )
        if not data:
            return await msg.edit_text("❌ Invalid cryptocurrency.")
        coin = data[0]
        text = (
            f"💰 {coin['name']} ({coin['symbol'].upper()})\n"
            f"💵 Price: ${coin['current_price']:,.2f}\n"
            f"📈 24h Change: {coin['price_change_percentage_24h']:.2f}%\n"
            f"🏔 High 24h: ${coin['high_24h']:,.2f}\n"
            f"📉 Low 24h: ${coin['low_24h']:,.2f}\n"
            f"🔢 Market Rank: #{coin['market_cap_rank']}\n"
            f"📊 Market Cap: ${coin['market_cap']:,.0f}"
        )
        await msg.edit_text(text)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("dns") & (SUDOERS | filters.group))
@language
async def dns_lookup(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /dns <domain>")
    domain = message.command[1]
    msg = await message.reply_text("🔄 Resolving...")
    try:
        data = await _get(
            "https://dns.google/resolve",
            params={"name": domain, "type": "A"},
        )
        answers = data.get("Answer", [])
        if not answers:
            return await msg.edit_text(f"❌ No A records found for {domain}.")
        lines = [f"🌐 **DNS Lookup** — {domain}"]
        seen = set()
        for a in answers[:10]:
            val = a.get("data")
            if val and val not in seen:
                seen.add(val)
                lines.append(f"• {val}")
        await msg.edit_text("\n".join(lines))
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("currency") & (SUDOERS | filters.group))
@language
async def currency_conv(client, message, _):
    args = message.command
    if len(args) < 4:
        return await message.reply_text(
            "Usage: /currency <amount> <from> <to>  e.g. /currency 100 usd eur"
        )
    try:
        amount = float(args[1])
    except ValueError:
        return await message.reply_text("❌ Invalid amount.")
    frm = args[2].upper()
    to = args[3].upper()
    msg = await message.reply_text("🔄 Converting...")
    try:
        data = await _get("https://open.er-api.com/v6/latest/" + frm)
        rates = data.get("rates", {})
        base = data.get("base_code", frm)
        if to not in rates or base != frm:
            return await msg.edit_text(f"❌ Unsupported currency: {to if to not in rates else frm}")
        converted = amount * rates[to]
        await msg.edit_text(
            f"💱 **Currency Conversion**\n\n"
            f"💰 {amount:,.2f} {frm} = **{converted:,.2f} {to}**\n"
            f"📈 Rate: 1 {frm} = {rates[to]:,.4f} {to}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("country") & (SUDOERS | filters.group))
@language
async def country_info(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /country <name>")
    name = " ".join(message.command[1:])
    msg = await message.reply_text("🔄 Fetching...")
    try:
        data = await _get(f"https://restcountries.com/v3.1/name/{name}")
        if not data:
            return await msg.edit_text(f"❌ Country '{name}' not found.")
        c = data[0]
        flags = c.get("flag", "")
        name_official = c.get("name", {}).get("official", "N/A")
        capital = ", ".join(c.get("capital", [])) or "N/A"
        region = c.get("region", "N/A")
        subregion = c.get("subregion", "N/A")
        population = f"{c.get('population', 0):,}"
        area = f"{c.get('area', 0):,.0f} km²"
        languages = ", ".join(c.get("languages", {}).values()) or "N/A"
        currencies = ", ".join(
            f"{v['name']} ({v.get('symbol','')})"
            for v in c.get("currencies", {}).values()
        ) or "N/A"
        await msg.edit_text(
            f"{flags} **{c.get('name', {}).get('common', name)}**\n\n"
            f"🏛 Official: {name_official}\n"
            f"📍 Capital: {capital}\n"
            f"🌍 Region: {region} / {subregion}\n"
            f"👥 Population: {population}\n"
            f"🗺 Area: {area}\n"
            f"🗣 Languages: {languages}\n"
            f"💱 Currencies: {currencies}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("wiki") & (SUDOERS | filters.group))
@language
async def wiki_search(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /wiki <query>")
    query = " ".join(message.command[1:])
    msg = await message.reply_text("🔄 Searching...")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                headers={"User-Agent": "IotaXMediaBot/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
        abstract = (data.get("AbstractText") or "").strip()
        heading = data.get("Heading") or query
        url = data.get("AbstractURL") or ""
        info_url = data.get("Infobox") or ""

        if not abstract and info_url:
            abstract = "No short description available."

        text = f"📖 **{heading}**\n\n{abstract}"
        if url:
            text += f"\n\n🔗 {url}"
        await msg.edit_text(text, disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("npm") & (SUDOERS | filters.group))
@language
async def npm_pkg(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /npm <package>")
    pkg = message.command[1]
    msg = await message.reply_text("🔄 Fetching...")
    try:
        data = await _get(f"https://registry.npmjs.org/{pkg}")
        latest = data.get("dist-tags", {}).get("latest", "N/A")
        desc = data.get("description") or "N/A"
        author = (data.get("author") or {}).get("name", "N/A") if isinstance(data.get("author"), dict) else data.get("author", "N/A")
        versions = len(data.get("versions", {}))
        homepage = data.get("homepage") or "N/A"
        await msg.edit_text(
            f"📦 **{pkg}**\n\n"
            f"🆕 Latest: {latest}\n"
            f"📝 Description: {desc}\n"
            f"👤 Author: {author}\n"
            f"🔢 Versions: {versions}\n"
            f"🏠 Homepage: {homepage}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("time") & (SUDOERS | filters.group))
@language
async def time_info(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /time <timezone>  e.g. /time Asia/Kolkata")
    tz = message.command[1]
    msg = await message.reply_text("🔄 Fetching...")
    try:
        data = await _get("https://timeapi.io/api/time/current/zone", params={"timeZone": tz})
        if data.get("dateTime") is None and data.get("year") is None:
            return await msg.edit_text(f"❌ Invalid timezone: {tz}")
        utc = data.get("utcOffset", "N/A")
        dt = data.get("dateTime") or f"{data.get('year')}-{data.get('month'):02d}-{data.get('day'):02d} {data.get('hour'):02d}:{data.get('minute'):02d}:{data.get('seconds'):02d}"
        await msg.edit_text(
            f"🕒 **Current Time** — {tz}\n\n"
            f"📅 {dt}\n"
            f"⏱ UTC Offset: {utc}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@app.on_message(filters.command("hn") & (SUDOERS | filters.group))
@language
async def hackernews(client, message, _):
    msg = await message.reply_text("🔄 Fetching top stories...")
    try:
        ids = await _get("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10")
        hits = ids.get("hits", [])
        if not hits:
            return await msg.edit_text("❌ No stories found.")
        lines = ["📰 **Hacker News — Top Stories**"]
        for i, h in enumerate(hits[:10], 1):
            title = h.get("title") or "Untitled"
            points = h.get("points", 0)
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            lines.append(f"{i}. {title}\n   ⭐ {points} | 🔗 {url}")
        await msg.edit_text("\n\n".join(lines), disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
