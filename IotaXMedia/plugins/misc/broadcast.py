# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from IotaXMedia.utils.decorators.language import language
from IotaXMedia.utils.formatters import alpha_to_int
from config import adminlist
import config

IS_BROADCASTING = False


@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):


    if getattr(config, "CLONE_MODE", False):
        return
    global IS_BROADCASTING
    query = ""
    x = y = 0
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        query = message.text.split(None, 1)[1]
        if "-pin" in query:
            query = query.replace("-pin", "")
        if "-nobot" in query:
            query = query.replace("-nobot", "")
        if "-pinloud" in query:
            query = query.replace("-pinloud", "")
        if "-assistant" in query:
            query = query.replace("-assistant", "")
        if "-user" in query:
            query = query.replace("-user", "")
        if "-silent" in query:
            query = query.replace("-silent", "")
        if query.strip() == "":
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    await message.reply_text(_["broad_1"])
    silent = "-silent" in message.text

    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = []
        schats = await get_served_chats()
        for chat in schats:
            chats.append(int(chat["chat_id"]))
        pin_loud = "-pinloud" in message.text
        explicit_pin = "-pin" in message.text or pin_loud
        for i in chats:
            try:
                m = (
                    await app.forward_messages(
                        i, y, x, disable_notification=silent
                    )
                    if message.reply_to_message
                    else await app.send_message(
                        i, text=query, disable_notification=silent
                    )
                )
                if explicit_pin:
                    try:
                        await m.pin(disable_notification=not pin_loud)
                        pin += 1
                    except:
                        continue
                elif not silent:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except:
                        pass
                sent += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                continue
        try:
            await message.reply_text(_["broad_3"].format(sent, pin))
        except:
            pass

    if "-user" in message.text:
        susr = 0
        served_users = []
        susers = await get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                m = (
                    await app.forward_messages(
                        i, y, x, disable_notification=silent
                    )
                    if message.reply_to_message
                    else await app.send_message(
                        i, text=query, disable_notification=silent
                    )
                )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                pass
        try:
            await message.reply_text(_["broad_4"].format(susr))
        except:
            pass

    if "-assistant" in message.text:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from IotaXMedia.core.userbot import assistants

        for num in assistants:
            sent = 0
            client = await get_client(num)
            async for dialog in client.get_dialogs():
                try:
                    if dialog.chat.id > 0:
                        continue
                    m = (
                        await client.forward_messages(
                            dialog.chat.id, y, x, disable_notification=silent
                        ) if message.reply_to_message else await client.send_message(
                            dialog.chat.id, text=query, disable_notification=silent
                        )
                    )
                    sent += 1
                    if str(dialog.chat.id).startswith("-") and (
                        "-pin" in message.text or "-pinloud" in message.text
                    ):
                        try:
                            await m.pin(
                                disable_notification="-pinloud" not in message.text
                            )
                        except:
                            pass
                    await asyncio.sleep(3)
                except FloodWait as fw:
                    flood_time = int(fw.value)
                    if flood_time > 200:
                        continue
                    await asyncio.sleep(flood_time)
                except:
                    continue
            text += _["broad_7"].format(num, sent)
        try:
            await aw.edit_text(text)
        except:
            pass
    IS_BROADCASTING = False


async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if getattr(user.privileges, 'can_manage_video_chats', False):
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue


asyncio.create_task(auto_clean())
