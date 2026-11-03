# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT


from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.utils import infoapi
from IotaXMedia.utils.decorators import language
from IotaXMedia.utils.god_style import god_text


def _args(message: Message, n_min: int) -> str | None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return None
    return parts[1].strip()


async def _run(message: Message, fn, *a):
    wait = await message.reply_text(god_text("ꜰᴇᴛᴄʜɪɴɢ…"))
    try:
        out = await fn(*a)
    except RuntimeError as e:
        out = f"**ᴇʀʀᴏʀ:** {e}"
    except Exception:
        out = "**ᴇʀʀᴏʀ:** ᴀᴘɪ ᴅᴏᴡɴ ᴏʀ ᴛɪᴍᴇᴏᴜᴛ. ꜱʟᴏᴡ ꜰʀᴇᴇ-ᴛɪᴇʀ ʜᴏꜱᴛꜱ — ᴅᴏʙᴀʀᴀ ᴛʀʏ ᴋᴀʀᴏ."
    try:
        await wait.edit_text(out[:4000], disable_web_page_preview=True)
    except Exception:
        await message.reply_text(out[:4000], disable_web_page_preview=True)


@app.on_message(filters.command(["ip"]) & ~filters.channel)
@language
async def ip_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("ip", "8.8.8.8"))
    await _run(message, infoapi.ip_info, q)


@app.on_message(filters.command(["dns"]) & ~filters.channel)
@language
async def dns_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("dns", "google.com"))
    await _run(message, infoapi.dns_lookup, q)


@app.on_message(filters.command(["weather", "mausam"]) & ~filters.channel)
@language
async def weather_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("weather", "Delhi"))
    await _run(message, infoapi.weather, q)


@app.on_message(filters.command(["aqi", "airquality"]) & ~filters.channel)
@language
async def aqi_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("aqi", "Delhi"))
    await _run(message, infoapi.aqi_info, q)


@app.on_message(
    filters.command(["pin", "pincode"]) & ~filters.channel & (filters.group | filters.private)
)
@language
async def pin_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("pin", "411001"))
    await _run(message, infoapi.pincode_info, q)


@app.on_message(filters.command(["ifsc"]) & ~filters.channel)
@language
async def ifsc_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("ifsc", "SBIN0001234"))
    await _run(message, infoapi.ifsc_info, q)


@app.on_message(filters.command(["git", "github"]) & ~filters.channel)
@language
async def git_cmd(client, message: Message, _):
    q = _args(message, 1)
    if not q:
        return await message.reply_text(infoapi.usage("git", "Iotatg"))
    await _run(message, infoapi.git_info, q)
