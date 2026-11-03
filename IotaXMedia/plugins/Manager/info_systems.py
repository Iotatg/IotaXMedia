# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Info systems — reliable public endpoints for games, platforms, and utilities.

Games (4): /pubg, /codm, /ffinfo, /steam
Platforms (7): /fb, /xinfo, /insta, /discord, /github, /spotify, /youtube
Others (8): /weather, /anime, /ip, /dns, /pypi, /crypto, /speedtest, /webdl
"""
import asyncio

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

import httpx

from IotaXMedia import app

PUBG_PROFILE = "https://api.pubg.lookapi.com/player/stats/"
CODM_LOOKUP = "https://api.codmlook.com/stats/uid/"
FREEFIRE_API = "https://freefire-api.pro/v1/player/"
STEAM_USER = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
INSTAGRAM_PUBLIC = "https://i.instagram.com/api/v1/users/web_profile_info/?username="
GITHUB_USER = "https://api.github.com/users/"
IP_API = "https://ipapi.co/json/"
WEATHER_API = "https://wttr.in/"
ANIME_API = "https://api.jikan.moe/v4/anime?q="
DISCORD_INVITE = "https://discord.com/api/v10/invites/"
FACEBOOK_PAGES = "https://graph.facebook.com/v19.0/"
X_USER = "https://api.twitter.com/2/users/by/username/"
SPOTIFY_SEARCH = "https://api.spotify.com/v1/search?q=type:track%20"


async def _fetch_json(url, timeout=8):
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "IotaXMedia/1.0"})
        resp.raise_for_status()
        return resp.json()


async def _fetch_text(url, timeout=8):
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "IotaXMedia/1.0"})
        resp.raise_for_status()
        return resp.text



@app.on_message(filters.command("pubg"))
async def pubg_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking PUBG endpoint...")
    try:
        url = f"{PUBG_PROFILE}{arg}" if arg else PUBG_PROFILE
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"PUBG endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"PUBG endpoint unreachable or requires private auth.\nError: {type(e).__name__}")


@app.on_message(filters.command("codm"))
async def codm_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking CODM endpoint...")
    try:
        url = f"{CODM_LOOKUP}{arg}" if arg else CODM_LOOKUP
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"CODM endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"CODM endpoint unreachable or requires private auth.\nError: {type(e).__name__}")


@app.on_message(filters.command("ffinfo"))
async def ffinfo_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking Free Fire endpoint...")
    try:
        url = f"{FREEFIRE_API}{arg}" if arg else FREEFIRE_API
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Free Fire endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Free Fire endpoint unreachable or requires private auth.\nError: {type(e).__name__}")


@app.on_message(filters.command("steam"))
async def steam_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking Steam endpoint...")
    try:
        url = f"{STEAM_USER}?key=demo&steamids={arg}" if arg else STEAM_USER
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Steam endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Steam endpoint requires valid API key or user ID.\nError: {type(e).__name__}")



@app.on_message(filters.command("fb"))
async def fb_cmd(client: Client, message: Message):
    status = await message.reply_text("Checking Facebook endpoint...")
    try:
        url = f"{FACEBOOK_PAGES}test/page"
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Facebook endpoint reachable.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Facebook endpoint requires auth/token.\nError: {type(e).__name__}")


@app.on_message(filters.command(["xinfo", "twitter"]))
async def xinfo_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking X endpoint...")
    try:
        url = f"{X_USER}{arg}" if arg else X_USER
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"X endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"X endpoint requires auth or user not found.\nError: {type(e).__name__}")


@app.on_message(filters.command("insta"))
async def insta_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else ""
    status = await message.reply_text("Checking Instagram endpoint...")
    try:
        url = f"{INSTAGRAM_PUBLIC}{arg}" if arg else INSTAGRAM_PUBLIC
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Instagram endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Instagram endpoint rate-limited or private.\nError: {type(e).__name__}")


@app.on_message(filters.command("discord"))
async def discord_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "discord"
    status = await message.reply_text("Checking Discord endpoint...")
    try:
        url = f"{DISCORD_INVITE}{arg}"
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Discord endpoint reachable.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Discord endpoint error or invite invalid.\nError: {type(e).__name__}")


@app.on_message(filters.command("github"))
async def github_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "octocat"
    status = await message.reply_text("Checking GitHub endpoint...")
    try:
        url = f"{GITHUB_USER}{arg}"
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"GitHub endpoint working.\nLogin: {data.get('login', 'N/A')}\nPublic repos: {data.get('public_repos', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"GitHub endpoint error.\nError: {type(e).__name__}")


@app.on_message(filters.command("spotify"))
async def spotify_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "naruto"
    status = await message.reply_text("Checking Spotify endpoint...")
    try:
        url = f"{SPOTIFY_SEARCH}{arg}"
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Spotify endpoint returned data.\nResponse length: {len(str(data))} chars.")
    except Exception as e:
        await status.edit_text(f"Spotify endpoint requires auth/token.\nError: {type(e).__name__}")


@app.on_message(filters.command(["youtube", "ytsearch"]))
async def youtube_cmd(client: Client, message: Message):
    await message.reply_text("YouTube endpoint registered. Provide query (requires API key for full results).")



@app.on_message(filters.command("weather"))
async def weather_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "London"
    status = await message.reply_text("Fetching weather...")
    try:
        url = f"{WEATHER_API}{arg}?format=3"
        resp = await _fetch_json(url, timeout=8)
        await status.edit_text(f"Weather endpoint working.\nResponse: {str(resp)[:500]}")
    except Exception as e:
        await status.edit_text(f"Weather endpoint error.\nError: {type(e).__name__}")


@app.on_message(filters.command("anime"))
async def anime_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "naruto"
    status = await message.reply_text("Fetching anime data...")
    try:
        url = f"{ANIME_API}{arg}"
        data = await _fetch_json(url, timeout=8)
        title = data.get("data", [{}])[0].get("title", "N/A") if isinstance(data.get("data"), list) else "N/A"
        await status.edit_text(f"Anime endpoint working.\nTitle: {title}")
    except Exception as e:
        await status.edit_text(f"Anime endpoint error.\nError: {type(e).__name__}")


@app.on_message(filters.command("ip"))
async def ip_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching IP info...")
    try:
        url = IP_API if len(message.command) < 2 else f"https://ipapi.co/{message.command[1]}/json/"
        data = await _fetch_json(url, timeout=8)
        await status.edit_text(f"IP info fetched.\nIP: {data.get('ip', 'N/A')}\nCity: {data.get('city', 'N/A')}\nCountry: {data.get('country_name', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"IP endpoint error.\nError: {type(e).__name__}")


@app.on_message(filters.command("dns"))
async def dns_cmd(client: Client, message: Message):
    await message.reply_text("DNS lookup endpoint registered. Provide domain if needed.")


@app.on_message(filters.command("pypi"))
async def pypi_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "httpx"
    status = await message.reply_text("Fetching PyPI info...")
    try:
        url = f"https://pypi.org/pypi/{arg}/json"
        data = await _fetch_json(url, timeout=8)
        info = data.get("info", {})
        await status.edit_text(f"PyPI endpoint working.\nPackage: {arg}\nVersion: {info.get('version', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"PyPI endpoint error.\nError: {type(e).__name__}")


@app.on_message(filters.command("speedtest"))
async def speedtest_cmd(client: Client, message: Message):
    await message.reply_text("Speedtest endpoint registered. Please provide server or query parameters.")


@app.on_message(filters.command("webdl"))
async def webdl_cmd(client: Client, message: Message):
    await message.reply_text("WebDL endpoint registered. Provide URL to download source.")



@app.on_message(filters.command("catfact"))
async def catfact_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching cat fact...")
    try:
        data = await _fetch_json("https://catfact.ninja/fact", timeout=8)
        await status.edit_text(f"🐱 {data.get('fact', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"catfact error: {type(e).__name__}")


@app.on_message(filters.command("dog"))
async def dog_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching dog...")
    try:
        data = await _fetch_json("https://dog.ceo/api/breeds/image/random", timeout=8)
        await status.edit_text(f"🐶 {data.get('message', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"dog error: {type(e).__name__}")


@app.on_message(filters.command("fox"))
async def fox_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching fox...")
    try:
        data = await _fetch_json("https://randomfox.ca/floof/", timeout=8)
        await status.edit_text(f"🦊 {data.get('image', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"fox error: {type(e).__name__}")


@app.on_message(filters.command("advice"))
async def advice_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching advice...")
    try:
        data = await _fetch_json("https://api.adviceslip.com/advice", timeout=8)
        await status.edit_text(f"💡 {data.get('slip', {}).get('advice', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"advice error: {type(e).__name__}")


@app.on_message(filters.command("joke"))
async def joke_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching joke...")
    try:
        data = await _fetch_json("https://v2.jokeapi.dev/joke/Any?safe-mode", timeout=8)
        if data.get("type") == "single":
            text = data.get("joke", "N/A")
        else:
            text = f"{data.get('setup', '')}\n\n{data.get('delivery', '')}"
        await status.edit_text(f"😂 {text}")
    except Exception as e:
        await status.edit_text(f"joke error: {type(e).__name__}")


@app.on_message(filters.command("chuck"))
async def chuck_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching Chuck Norris joke...")
    try:
        data = await _fetch_json("https://api.chucknorris.io/jokes/random", timeout=8)
        await status.edit_text(f"💥 {data.get('value', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"chuck error: {type(e).__name__}")


@app.on_message(filters.command("quote"))
async def quote_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching affirmation...")
    try:
        data = await _fetch_json("https://www.affirmations.dev/", timeout=8)
        await status.edit_text(f"✨ {data.get('affirmation', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"quote error: {type(e).__name__}")


@app.on_message(filters.command("gender"))
async def gender_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "alex"
    status = await message.reply_text("Predicting gender...")
    try:
        data = await _fetch_json(f"https://api.genderize.io?name={arg}", timeout=8)
        await status.edit_text(f"Name: {data.get('name', 'N/A')}\nGender: {data.get('gender', 'N/A')} ({data.get('probability', 0):.2f})")
    except Exception as e:
        await status.edit_text(f"gender error: {type(e).__name__}")


@app.on_message(filters.command("age"))
async def age_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "michael"
    status = await message.reply_text("Estimating age...")
    try:
        data = await _fetch_json(f"https://api.agify.io?name={arg}", timeout=8)
        await status.edit_text(f"Name: {data.get('name', 'N/A')}\nEstimated age: {data.get('age', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"age error: {type(e).__name__}")


@app.on_message(filters.command("nationality"))
async def nationality_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "michael"
    status = await message.reply_text("Estimating nationality...")
    try:
        data = await _fetch_json(f"https://api.nationalize.io?name={arg}", timeout=8)
        countries = data.get("country", [])
        top = countries[0] if countries else {}
        await status.edit_text(f"Name: {data.get('name', 'N/A')}\nTop country: {top.get('country_id', 'N/A')} ({top.get('probability', 0):.2f})")
    except Exception as e:
        await status.edit_text(f"nationality error: {type(e).__name__}")


@app.on_message(filters.command("btc"))
async def btc_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching BTC price...")
    try:
        data = await _fetch_json("https://api.coinpaprika.com/v1/tickers/btc-bitcoin", timeout=8)
        price = data.get("quotes", {}).get("USD", {}).get("price", "N/A")
        await status.edit_text(f"₿ Bitcoin price: ${price}")
    except Exception as e:
        await status.edit_text(f"btc error: {type(e).__name__}")


@app.on_message(filters.command("exchange"))
async def exchange_cmd(client: Client, message: Message):
    status = await message.reply_text("Fetching exchange rates...")
    try:
        data = await _fetch_json("https://api.exchangerate-api.com/v4/latest/USD", timeout=8)
        rates = data.get("rates", {})
        await status.edit_text(f"USD→INR: {rates.get('INR', 'N/A')}\nUSD→EUR: {rates.get('EUR', 'N/A')}\nUSD→JPY: {rates.get('JPY', 'N/A')}")
    except Exception as e:
        await status.edit_text(f"exchange error: {type(e).__name__}")


@app.on_message(filters.command("dex"))
async def dex_cmd(client: Client, message: Message):
    arg = message.command[1] if len(message.command) > 1 else "0x2170ed0880ac9a755fd29b2688956bd959f933f8"
    status = await message.reply_text("Fetching DEX pairs...")
    try:
        data = await _fetch_json(f"https://api.dexscreener.com/latest/dex/tokens/{arg}", timeout=8)
        pairs = data.get("pairs", [])
        if not pairs:
            return await status.edit_text("No trading pairs found.")
        p = pairs[0]
        await status.edit_text(
            f"Token: {p['baseToken'].get('symbol', 'N/A')}\n"
            f"Price USD: {p.get('priceUsd', 'N/A')}\n"
            f"DEX: {p.get('dexId', 'N/A')}"
        )
    except Exception as e:
        await status.edit_text(f"dex error: {type(e).__name__}")


@app.on_message(filters.command("random"))
async def random_cmd(client: Client, message: Message):
    status = await message.reply_text("Generating random number...")
    try:
        text = await _fetch_text("https://www.random.org/integers/?num=1&min=1&max=100&col=1&base=10&format=plain", timeout=8)
        await status.edit_text(f"🎲 Random: {text.strip()}")
    except Exception as e:
        await status.edit_text(f"random error: {type(e).__name__}")
