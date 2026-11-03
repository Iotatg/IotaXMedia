# Authored By Iota Coders (Free Fire player lookup via Garena backend)
# SPDX-License-Identifier: MIT
import asyncio
import time

from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.garena.client import (
    check_banned,
    fetch_player_info,
    start_background_tasks,
)
from IotaXMedia.utils.decorators.language import language

FF = "\n".join(
    [
        "★ ɪɴғᴏ ʙʏ : ˹𝐈ᴏᴛᴀ ✘ 𝙼ᴜꜱɪᴄ˼ ♪",
        "☆ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : IotaXMedia",
    ]
)

start_background_tasks()


def _timefmt(ts):
    if not ts:
        return "N/A"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))
    except Exception:
        return str(ts)


def _player_section(basic, social):
    lines = ["╭──〔 🎮 ᴘʟᴀʏᴇʀ ɪɴғᴏ 〕──╮"]
    name = basic.get("nickname") or "Unknown"
    uid = (
        basic.get("accountId")
        or basic.get("externalId")
        or basic.get("externalUid")
        or "N/A"
    )
    region = basic.get("region") or "N/A"
    level = basic.get("level", 0)
    exp = basic.get("exp", 0)
    liked = basic.get("liked", 0)
    badge = basic.get("badgeCnt", 0)
    elite = "𝐘𝐞𝐬 ✅" if basic.get("hasElitePass") else "𝐍σ ❌"
    created = _timefmt(basic.get("createAt"))
    last_login = _timefmt(basic.get("lastLoginAt"))
    lines.append(f"├ 👤 𝐍ᴧϻє : {name}")
    lines.append(f"├ 🆔 𝐔𝐈𝐃 : {uid}")
    lines.append(f"├ 🌎 𝐑єɢɪση : {region}")
    lines.append(f"├ ⭐ 𝐋єᴠєʟ : {level}")
    lines.append(f"├ ✨ 𝐄xᴘ : {exp}")
    if liked:
        lines.append(f"├ ❤️ 𝐋ɪᴋᴇs : {liked}")
    if badge:
        lines.append(f"├ 🎖 𝐁ᴧᴅɢєs : {badge}")
    lines.append(f"├ 🎟 𝐄ʟɪᴛє 𝐏ᴧss : {elite}")
    lines.append(f"├ 📅 𝐂ꝛєᴧᴛєᴅ : {created}")
    lines.append(f"└ 🕑 𝐋ᴧsᴛ 𝐋σɢɪη : {last_login}")
    bio = (social or {}).get("signature")
    if bio:
        lines.append("")
        lines.append(f"✍️ 𝐁ɪσ : {bio}")
    return "\n".join(lines)


def _rank_section(basic):
    lines = ["╭──〔 🏆 ʀᴀɴᴋ ɪɴғᴏ 〕──╮"]
    lines.append(f"├ 📈 𝐁𝐑 𝐏σɪηᴛs : {basic.get('rankingPoints', 0)}")
    lines.append(f"├ 🏅 𝐁𝐑 𝐑ᴧηᴋ : {basic.get('rank', 0)}")
    lines.append(f"├ 📊 𝐂𝐒 𝐏σɪηᴛs : {basic.get('csRankingPoints', 0)}")
    lines.append(f"└ 🏅 𝐂𝐒 𝐑ᴧηᴋ : {basic.get('csRank', 0)}")
    return "\n".join(lines)


def _guild_section(clan, captain):
    lines = ["╭──〔 🏰 ɢᴜɪʟᴅ ɪɴғᴏ 〕──╮"]
    if not clan or not clan.get("clanId"):
        lines.append("└ ⚠️ 𝐍σ 𝐆ᴜɪʟᴅ")
        return "\n".join(lines)
    cap_name = (captain or {}).get("nickname") or "Unknown"
    cap_id = (
        (captain or {}).get("accountId")
        or (captain or {}).get("externalId")
        or "N/A"
    )
    lines.append(f"├ 🏰 𝐍ᴧϻє : {clan.get('clanName') or 'Unknown'}")
    lines.append(f"├ 🆔 𝐈𝐃 : {clan.get('clanId')}")
    lines.append(f"├ ⭐ 𝐋єᴠєʟ : {clan.get('clanLevel', 0)}")
    lines.append(
        f"├ 👥 𝐌єϻʙєꝛs : {clan.get('memberNum', 0)}/{clan.get('capacity', 0)}"
    )
    lines.append(f"├ 👑 𝐎ᴡηêꝛ : {cap_name}")
    lines.append(f"└ 🆔 𝐎ᴡηêꝛ 𝐈𝐃 : {cap_id}")
    return "\n".join(lines)


def _pet_section(pet):
    lines = ["╭──〔 🐾 ᴘᴇᴛ ɪɴғᴏ 〕──╮"]
    if not pet or not pet.get("id"):
        lines.append("└ ⚠️ 𝐍σ 𝐏єᴛ")
        return "\n".join(lines)
    lines.append(f"├ ⭐ 𝐋єᴠєʟ : {pet.get('level', 0)}")
    lines.append(f"└ ✨ 𝐄xᴘ : {pet.get('exp', 0)}")
    return "\n".join(lines)


def _health_section(credit, diamond):
    lines = ["╭──〔 💎 ACCOUT HEALTH 〕──╮"]
    if credit and credit.get("creditScore"):
        score = credit.get("creditScore")
    else:
        score = "N/A"
    if diamond and diamond.get("diamondCost"):
        cost = diamond.get("diamondCost")
    else:
        cost = "N/A"
    lines.append(f"├ 💯 𝐂ꝛєᴅɪᴛ 𝐒ᴄσꝛє : {score}")
    lines.append(f"└ 🪙 𝐂σɪɴs : {cost}")
    return "\n".join(lines)


def _format_profile(data):
    basic = data.get("basicInfo") or {}
    sections = [
        _player_section(basic, data.get("socialInfo")),
        "",
        _rank_section(basic),
        "",
        _guild_section(data.get("clanBasicInfo"), data.get("captainBasicInfo")),
        "",
        _pet_section(data.get("petInfo")),
        "",
        _health_section(data.get("creditScoreInfo"), data.get("diamondCostRes")),
        "",
        FF,
    ]
    return "\n".join(sections)


@app.on_message(filters.command("ffinfo") & (SUDOERS | filters.group))
@language
async def ffinfo(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ffinfo <UID>")
    uid = message.command[1]
    msg = await message.reply_text("🔍 𝐅єᴛᴄʜɪηɢ ᴘʟᴀʏᴇʀ ᴅᴇᴛᴀɪʟs...")
    try:
        data = await fetch_player_info(uid)
    except ValueError as e:
        return await msg.edit_text(f"❌ {e}")
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to fetch player info: {e}")
    text = _format_profile(data)
    try:
        await msg.edit_text(text, disable_web_page_preview=True)
    except Exception:
        await msg.reply_text(text, disable_web_page_preview=True)


@app.on_message(filters.command("ffban") & (SUDOERS | filters.group))
@language
async def ffban(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /ffban <UID>")
    uid = message.command[1]
    msg = await message.reply_text("🔍 𝐂ʜєᴄᴋɪηɢ ᴀᴄᴄσᴜηᴛ sᴛᴀᴛᴜs...")
    try:
        data = await check_banned(uid)
    except Exception as e:
        return await msg.edit_text(f"❌ Failed to check ban status: {e}")
    status = data.get("is_banned", 0)
    msg_id = data.get("message_id", "")
    if status == 0:
        text = "✅ **Account Status:** ACTIVE (Not Banned)"
    elif status == 1:
        text = "⛔ **Account Status:** BANNED"
    else:
        text = f"⚠️ **Account Status:** Unknown ({status})"
    if msg_id:
        text += f"\n🗂 Reason ID: {msg_id}"
    text += f"\n\n★ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : IotaXMedia"
    try:
        await msg.edit_text(text)
    except Exception:
        await msg.reply_text(text)
