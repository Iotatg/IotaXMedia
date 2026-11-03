# Authored By Iota Coders (auto broadcast system)
# SPDX-License-Identifier: MIT
import asyncio
import time

from pyrogram import filters

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.database import (
    autobroadcastdb,
    get_served_chats,
    get_served_users,
)
from IotaXMedia.utils.decorators.language import language

DEFAULT_INTERVAL = 240
DEFAULT_MESSAGE = (
    "🌟 𝐀𝐮𝐭𝐨 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 🌟\n\n"
    "Hello dear users! This is an automated announcement.\n"
    "Stay tuned for more updates!"
)

_state = {"running": False, "task": None}





async def _get_config() -> dict:
    doc = await autobroadcastdb.find_one({"_id": "config"})
    if not doc:
        return {
            "enabled": False,
            "interval": DEFAULT_INTERVAL,
            "message": DEFAULT_MESSAGE,
            "runs": 0,
            "last_run": None,
        }
    return doc


async def _save_config(config: dict):
    config["_id"] = "config"
    await autobroadcastdb.replace_one({"_id": "config"}, config, upsert=True)





async def _broadcast_loop():
    while True:
        config = await _get_config()
        if not config.get("enabled"):
            await asyncio.sleep(30)
            continue
        interval = int(config.get("interval", DEFAULT_INTERVAL))
        await asyncio.sleep(interval * 60)

        if not config.get("enabled"):
            continue

        message = config.get("message") or DEFAULT_MESSAGE
        sent = 0
        for chat in await get_served_chats():
            chat_id = int(chat["chat_id"])
            try:
                await app.send_message(chat_id, message)
                sent += 1
                await asyncio.sleep(0.2)
            except Exception:
                continue

        usr_sent = 0
        for user in await get_served_users():
            user_id = int(user["user_id"])
            try:
                await app.send_message(user_id, message)
                usr_sent += 1
                await asyncio.sleep(0.2)
            except Exception:
                continue

        config["runs"] = int(config.get("runs", 0)) + 1
        config["last_run"] = int(time.time())
        await _save_config(config)
        await asyncio.sleep(30)


async def _ensure_loop():
    if _state["task"] is None or _state["task"].done():
        from IotaXMedia.utils.errors import capture_task_err
        _state["task"] = asyncio.create_task(
            capture_task_err("autobroadcast.loop")(_broadcast_loop)()
        )


asyncio.create_task(_ensure_loop())





@app.on_message(filters.command("autobroadcast") & SUDOERS)
@language
async def auto_broadcast(client, message, _):
    if len(message.command) < 2:
        return await message.reply_text(
            "Usage:\n"
            "`/autobroadcast on` — start auto broadcast\n"
            "`/autobroadcast off` — stop auto broadcast\n"
            "`/autobroadcast status` — show current state\n"
            "`/autobroadcast interval <minutes>` — set interval\n"
            "`/autobroadcast msg <text>` — set broadcast message"
        )

    action = message.command[1].lower()
    config = await _get_config()

    if action == "on":
        if config.get("enabled"):
            return await message.reply_text("⬤ ᴀᴜᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ ✅")
        config["enabled"] = True
        await _save_config(config)
        await _ensure_loop()
        interval = config.get("interval", DEFAULT_INTERVAL)
        return await message.reply_text(
            f"✅ ᴀᴜᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴇɴᴀʙʟᴇᴅ\n"
            f"⏱ ᴇᴠᴇʀʏ: {interval} ᴍɪɴ"
        )

    if action == "off":
        if not config.get("enabled"):
            return await message.reply_text("⬤ ᴀᴜᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪs ᴀʟʀᴇᴀᴅʏ sᴛᴏᴘᴘᴇᴅ ⚪")
        config["enabled"] = False
        await _save_config(config)
        return await message.reply_text("⚪ ᴀᴜᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴏᴘᴘᴇᴅ")

    if action == "status":
        interval = config.get("interval", DEFAULT_INTERVAL)
        runs = config.get("runs", 0)
        last_run = config.get("last_run")
        chats = len(await get_served_chats())
        users = len(await get_served_users())
        if config.get("enabled"):
            status = "ʀᴜɴɴɪɴɢ"
            icon = "⬤"
        else:
            status = "sᴛᴏᴘᴘᴇᴅ"
            icon = "⚪"
        last_str = (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_run))
            if last_run
            else "N/A"
        )
        return await message.reply_text(
            f"{icon} ᴀᴜᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪs {status}\n"
            f"⏱ ᴛᴇʀᴠᴀʟ: ᴇᴠᴇʀʏ {interval} ᴍɪɴ\n"
            f"🔄 ʀᴜɴs sᴏ ғᴀʀ: {runs}\n"
            f"🕓 ʟᴀsᴛ ʀᴜɴ: {last_str} — {chats} ɢʀᴏᴜᴘs, {users} ᴜsᴇʀs"
        )

    if action in ("interval", "time", "setinterval"):
        if len(message.command) < 3:
            return await message.reply_text("Usage: `/autobroadcast interval <minutes>`")
        try:
            minutes = max(1, int(message.command[2]))
        except ValueError:
            return await message.reply_text("❌ Invalid interval. Use minutes as a number.")
        config["interval"] = minutes
        await _save_config(config)
        return await message.reply_text(f"✅ ɪɴᴛᴇʀᴠᴀʟ sᴇᴛ ᴛᴏ {minutes} ᴍɪɴ")

    if action in ("msg", "message", "setmsg"):
        if len(message.command) < 3:
            return await message.reply_text("Usage: `/autobroadcast msg <text>`")
        text = message.text.split(None, 2)[2]
        config["message"] = text
        await _save_config(config)
        return await message.reply_text("✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ")

    return await message.reply_text("❌ Unknown action. Use `on`, `off`, `status`, `interval`, `msg`.")
