# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Iota extras.

Commands added (none existed previously):
    /admin            – admin mention / report-to-admins
    /atag             – alias of /admin
    /dlsticker <link> – download a whole sticker pack by t.me/addstickers/<name>
    /pinned           – fetch the most recent pinned message of the chat
    /users            – member breakdown (online/offline/bots/deleted/premium)
    /groupinfo @user  – remote group info by username
    /gcstats          – quick stats of the current chat
    /unbanall         – unban everyone banned in this chat
    /unmuteall        – unmute everyone restricted in this chat
    /unpinall         – unpin every pinned message in this chat
    /st <file_id>     – send a sticker by its file_id
    /rtag [text]      – mention everyone in chat (reply-to-message target)
    /rstop            – cancel an in-progress /rtag
    /rmwarns          – alias of Iota's existing /resetwarns
    /privacy          – static privacy-policy card

All handlers use the shared IotaXMedia globals (``app``, ``userbot``,
``mongodb``) and the existing decorator/permission helpers, so there are no
import collisions with the main-bot modules.
"""
from __future__ import annotations

import asyncio
import os
import time

from pyrogram import Client, enums, filters
from pyrogram.errors import ChatAdminRequired, FloodWait, UserAdminInvalid, UserNotParticipant
from pyrogram.types import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.permissions import mention
from IotaXMedia.utils.decorator import bot_can_ban
from IotaXMedia.utils.permissions import mention
from IotaXMedia.utils.colored_buttons import styled_button, edit_message_text_colored, send_message_colored

try:
    from config import BOT_USERNAME, OWNER_ID
except Exception:  # pragma: no cover
    BOT_USERNAME = ""
    OWNER_ID = 0
    OWNER_ID = 0





async def _is_chat_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id in SUDOERS:
        return True
    try:
        m = await client.get_chat_member(chat_id, user_id)
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception:
        return False





@app.on_message(filters.command(["admin", "atag"]) & filters.group)
async def admin_tag_cmd(client: Client, message: Message):
    if not message.from_user:
        return

    chat_id = message.chat.id
    caller_id = message.from_user.id

    try:
        admin_members = [
            a async for a in client.get_chat_members(
                chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
        ]
    except Exception as e:
        return await message.reply_text(f"⚠️ Couldn't fetch admins: <code>{e}</code>")

    admin_ids = [a.user.id for a in admin_members if a.user and not a.user.is_bot]


    if caller_id in admin_ids or caller_id in SUDOERS:
        note = message.text.split(None, 1)[1].strip() if len(message.command) > 1 else ""
        mentions = "".join(f"[\u2063](tg://user?id={i})" for i in admin_ids)
        body = "🛡 **ᴀᴅᴍɪɴ ᴛᴀɢ**\n" + (f"{note}\n" if note else "")
        try:
            await message.reply_text(body + mentions, disable_web_page_preview=True)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(body + mentions, disable_web_page_preview=True)
        return


    reply = message.reply_to_message
    if not reply:
        return await message.reply_text("» ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʀᴇᴘᴏʀᴛ ᴛʜᴇᴍ ᴛᴏ ᴀᴅᴍɪɴs.")
    target = (
        mention(reply.from_user.id, reply.from_user.first_name)
        if reply.from_user else "ᴛʜᴀᴛ ᴜsᴇʀ"
    )
    text = f"» **{target} ʀᴇᴘᴏʀᴛᴇᴅ ᴛᴏ ᴀᴅᴍɪɴs!**\n"
    text += "".join(f"[\u2063](tg://user?id={i})" for i in admin_ids)
    try:
        await message.reply_text(text, disable_web_page_preview=True, parse_mode="markdown")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text(text, disable_web_page_preview=True, parse_mode="markdown")





@app.on_message(filters.command("dlsticker"))
async def dlsticker_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "» ᴜsᴀɢᴇ: `/dlsticker <stickerset_link>`\n"
            "_e.g. `/dlsticker https://t.me/addstickers/PackName`_"
        )
    arg = message.command[1].strip()
    if "addstickers/" in arg:
        short_name = arg.split("addstickers/")[-1].rstrip("/? ")
    elif "t.me/addemoji" in arg:
        return await message.reply_text("» ᴇᴍᴏᴊɪ ᴘᴀᴄᴋs are not downloadable here.")
    else:
        short_name = arg.lstrip("@")
    if not short_name:
        return await message.reply_text("» ᴄᴏᴜʟᴅɴ'ᴛ ᴘᴀʀsᴇ ᴛʜᴇ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ ɴᴀᴍᴇ.")

    status = await message.reply_text("» ғᴇᴛᴄʜɪɴɢ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ…")
    import pyrogram
    try:
        stickerset = await client.invoke(
            pyrogram.raw.functions.messages.GetStickerSet(
                stickerset=pyrogram.raw.types.InputStickerSetShortName(short_name=short_name),
                hash=0,
            )
        )
    except Exception as e:
        return await status.edit(f"» sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ ɴᴏᴛ ғᴏᴜɴᴅ: <code>{e}</code>")

    docs = getattr(stickerset, "documents", []) or []
    if not docs:
        return await status.edit("» ᴇᴍᴘᴛʏ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ.")
    await status.edit(f"» sᴇɴᴅɪɴɢ {len(docs)} sᴛɪᴄᴋᴇʀs…")
    sent = 0
    for doc in docs:
        try:
            await client.send_document(
                message.chat.id,
                document=pyrogram.raw.types.InputDocument(
                    id=doc.id,
                    access_hash=doc.access_hash,
                    file_reference=doc.file_reference,
                ),
            )
            sent += 1
            if sent % 10 == 0:
                await asyncio.sleep(1)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass
    await status.edit(f"» ᴅᴏɴᴇ — sᴇɴᴛ {sent}/{len(docs)} sᴛɪᴄᴋᴇʀs.")





@app.on_message(filters.command("pinned") & filters.group)
async def pinned_cmd(client: Client, message: Message):
    try:
        pinned = await client.get_chat(message.chat.id)
    except Exception as e:
        return await message.reply_text(f"⚠️ {e}")
    if not pinned.pinned_message:
        return await message.reply_text("» ɴᴏ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
    try:
        await pinned.pinned_message.reply(f"» 📌 **ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ:**", quote=True)
    except Exception:
        await message.reply_text(pinned.pinned_message.link or "(unable to forward)")





@app.on_message(filters.command("users") & filters.group)
async def users_cmd(client: Client, message: Message):
    if not await _is_chat_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("» ᴏɴʟʏ ᴀᴅᴍɪɴs.")
    status = await message.reply_text("» ᴀɴᴀʟʏsɪɴɢ ᴍᴇᴍʙᴇʀs…")
    t0 = time.perf_counter()
    bots = deleted = premium = restricted = total = 0
    try:
        async for m in client.get_chat_members(message.chat.id):
            total += 1
            u = m.user
            if not u:
                continue
            if u.is_bot:
                bots += 1
            if u.is_deleted:
                deleted += 1
            if u.is_premium:
                premium += 1
    except Exception as e:
        return await status.edit(f"⚠️ {e}")
    secs = time.perf_counter() - t0
    await status.edit(
        f"» **{message.chat.title}** ᴍᴇᴍʙᴇʀs\n"
        f"• ᴛᴏᴛᴀʟ: {total}\n"
        f"• ʙᴏᴛs: {bots}\n"
        f"• ᴅᴇʟᴇᴛᴇᴅ: {deleted}\n"
        f"• ᴘʀᴇᴍɪᴜᴍ: {premium}\n"
        f"• ᴛɪᴍᴇ: {secs:.2f}s"
    )





@app.on_message(filters.command("groupinfo"))
async def groupinfo_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("» ᴜsᴀɢᴇ: `/groupinfo @username`")
    uname = message.command[1].strip()
    try:
        chat = await client.get_chat(uname)
    except Exception as e:
        return await message.reply_text(f"» ᴇʀʀᴏʀ: <code>{e}</code>")
    members = await client.get_chat_members_count(chat.id)
    await message.reply_text(
        f"» **ᴜsᴇʀɴᴀᴍᴇ** {uname}\n"
        f"• ɴᴀᴍᴇ: `{chat.title}`\n"
        f"• ɪᴅ: `{chat.id}`\n"
        f"• ᴍᴇᴍʙᴇʀs: `{members}`\n"
        f"• ᴜsᴇʀɴᴀᴍᴇ: @{chat.username}\n"
        f"• ᴅᴇsᴄ: {(chat.description or 'N/A')[:300]}"
    )





@app.on_message(filters.command("gcstats") & filters.group)
async def gcstats_cmd(client: Client, message: Message):
    chat = await client.get_chat(message.chat.id)
    txt = (
        f"» **ɢʀᴏᴜᴘ ɪɴғᴏ**\n"
        f"• ɴᴀᴍᴇ: **{chat.title}**\n"
        f"• ɪᴅ: `{chat.id}`\n"
        f"• ᴛʏᴘᴇ: `{chat.type}`\n"
        f"• ᴍᴇᴍʙᴇʀs: `{await client.get_chat_members_count(chat.id)}`\n"
        f"• ᴜsᴇʀɴᴀᴍᴇ: @{chat.username}\n" if chat.username else ""
    )
    await message.reply_text(txt or "» ᴜɴᴀʙʟᴇ ᴛᴏ ɢᴀᴛʜᴇʀ sᴛᴀᴛs.")





@app.on_message(filters.command("unbanall") & filters.group)
@bot_can_ban
async def unbanall_cmd(client: Client, message: Message):
    if not await _is_chat_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("» ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ.")
    status = await message.reply_text("» ᴜɴʙᴀɴɴɪɴɢ…")
    count = 0
    try:
        async for m in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.BANNED):
            try:
                await client.unban_chat_member(message.chat.id, m.user.id)
                count += 1
            except Exception:
                pass
    except Exception as e:
        return await status.edit(f"» {e}")
    await status.edit(f"» ᴜɴʙᴀɴɴᴇᴅ {count} ᴜsᴇʀs.")


@app.on_message(filters.command("unmuteall") & filters.group)
@bot_can_ban
async def unmuteall_cmd(client: Client, message: Message):
    if not await _is_chat_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("» ʏᴏᴜ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ.")
    full = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
    )
    status = await message.reply_text("» ᴜɴᴍᴜᴛɪɴɢ…")
    count = 0
    try:
        async for m in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.RESTRICTED):
            try:
                await client.restrict_chat_member(message.chat.id, m.user.id, permissions=full)
                count += 1
            except Exception:
                pass
    except Exception as e:
        return await status.edit(f"» {e}")
    await status.edit(f"» ᴜɴᴍᴜᴛᴇᴅ {count} ᴍᴇᴍʙᴇʀs.")


@app.on_message(filters.command("unpinall") & filters.group)
async def unpinall_cmd(client: Client, message: Message):
    if not await _is_chat_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("» ʏᴏᴜ ʟᴀᴄᴋ ᴜɴᴘɪɴ ᴘᴇʀᴍɪssɪᴏɴ.")
    try:
        me = await client.get_chat_member(message.chat.id, (await client.get_me()).id)
        if not (me.status == enums.ChatMemberStatus.ADMINISTRATOR and getattr(me.privileges, "can_pin_messages", False)):
            return await message.reply_text("» ɢɪᴠᴇ ᴍᴇ ᴘɪɴ ᴘᴇʀᴍɪssɪᴏɴ.")
    except Exception:
        return await message.reply_text("» ᴄᴏᴜʟᴅɴ'ᴛ ᴠᴇʀɪғʏ ʙᴏᴛ ʀɪɢʜᴛs.")
    buttons_col = [
        [styled_button("✔ ʏᴇs", callback_data="iota_unpin=yes", style="success"),
         styled_button("✖ ɴᴏ", callback_data="iota_unpin=no", style="danger")]
    ]
    try:
        r = await send_message_colored(
            message.chat.id, "» ᴜɴᴘɪɴ ᴀʟʟ?", buttons_col
        )
        if r:
            return
    except Exception:
        pass
    await message.reply_text(
        "» ᴜɴᴘɪɴ ᴀʟʟ?",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✔ ʏᴇs", callback_data="iota_unpin=yes", style=enums.ButtonStyle.SUCCESS),
              InlineKeyboardButton("✖ ɴᴏ", callback_data="iota_unpin=no", style=enums.ButtonStyle.DANGER)]]
        ),
    )


@app.on_callback_query(filters.regex(r"^iota_unpin=(yes|no)$"))
async def unpinall_cb(client: Client, cq):
    if not await _is_chat_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("» ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ.", show_alert=True)
    if cq.data.split("=")[-1] == "yes":
        try:
            await client.unpin_all_chat_messages(cq.message.chat.id)
        except Exception as e:
            return await cq.message.edit_text(f"» {e}")
    text = "✅ ᴀʟʟ ᴜɴᴘɪɴɴᴇᴅ." if cq.data.endswith("=yes") else "» ᴇᴅɪᴛ ᴄᴀɴᴄᴇʟ."
    close_col = [[styled_button("ᴄʟᴏsᴇ", callback_data="iota_close", style="danger")]]
    try:
        r = await edit_message_text_colored(cq.message.chat.id, cq.message.id, text, close_col)
        if r:
            return
    except Exception:
        pass
    await cq.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="iota_close", style=enums.ButtonStyle.DANGER)]]),
    )


@app.on_callback_query(filters.regex(r"^iota_close$"))
async def iota_close_cb(_, cq):
    try:
        await cq.message.delete()
    except Exception:
        pass





@app.on_message(filters.command("st"))
async def st_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("» ᴜsᴀɢᴇ: `/st <file_id>`")
    try:
        await client.send_sticker(message.chat.id, sticker=message.command[1])
    except Exception as e:
        await message.reply_text(f"» {e}")





RTAG_CHATS: set[int] = set()


@app.on_message(filters.command("rtag") & filters.group, group=11)
async def rtag_cmd(client: Client, message: Message):
    if not await _is_chat_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("» ᴀᴅᴍɪɴs ᴏɴʟʏ.")
    replied = message.reply_to_message
    if len(message.command) < 2 and not replied:
        return await message.reply_text("» ɢɪᴠᴇ ᴛᴇxᴛ ᴏʀ ʀᴇᴘʟʏ. `/rtag Hi all`")
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    if message.chat.id in RTAG_CHATS:
        return await message.reply_text("» ᴀʟʀᴇᴀᴅʏ ᴛᴀɢɢɪɴɢ. `/rstop` ᴛᴏ ʜᴀʟᴛ.")
    RTAG_CHATS.add(message.chat.id)
    try:
        chunk = ""
        n = 0
        async for m in client.get_chat_members(message.chat.id):
            if message.chat.id not in RTAG_CHATS:
                break
            u = m.user
            if not u or u.is_bot or u.is_deleted:
                continue
            chunk += f"[{u.first_name}](tg://user?id={u.id})  "
            n += 1
            if n == 7:
                await message.reply_text((text + "\n" + chunk) if text else chunk, disable_web_page_preview=True)
                await asyncio.sleep(3)
                chunk = ""
                n = 0
        if chunk:
            await message.reply_text((text + "\n" + chunk) if text else chunk, disable_web_page_preview=True)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    finally:
        RTAG_CHATS.discard(message.chat.id)


@app.on_message(filters.command("rstop") & filters.group)
async def rstop_cmd(client: Client, message: Message):
    if message.chat.id in RTAG_CHATS:
        RTAG_CHATS.discard(message.chat.id)
        return await message.reply_text("» ᴛᴀɢɢɪɴɢ sᴛᴏᴘᴘᴇᴅ.")
    await message.reply_text("» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀɢ.")





@app.on_message(filters.command(["rmwarns"]))
async def rmwarns_alias(client: Client, message: Message):
    await message.reply_text(
        "» ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴡᴀʀɴs ᴜsᴇ ᴛʜᴇ ʙᴏᴛ's ᴏᴡɴ `/resetwarns` — ᴏᴘᴇʀᴀᴛᴇs ᴏɴ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ."
    )





@app.on_message(filters.command("privacy"))
async def privacy_cmd(client: Client, message: Message):
    await message.reply_text(
        "**➻ ɪᴏᴛᴀxᴍᴜsɪᴄ ᴘʀɪᴠᴀᴄʏ ᴘᴏʟɪᴄʏ**\n\n"
        "• ʏᴏᴜʀ ᴅᴀᴛᴀ ɪs sᴛᴏʀᴇᴅ ᴏɴʟʏ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴍᴜsɪᴄ ᴘʟᴀʏʙᴀᴄᴋ ᴀɴᴅ ᴄʜᴀᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ.\n"
        "• ɴᴏ ᴘᴇʀsᴏɴᴀʟ ᴄʜᴀᴛs ᴀʀᴇ ʀᴇᴀᴅ; ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ʜᴀɴᴅʟᴇʀs ᴀʀᴇ ᴘʀᴏᴄᴇssᴇᴅ.\n"
        "• ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ ᴡɪᴛʜ ᴄᴏɴᴄᴇʀɴs.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("ᴏᴡɴᴇʀ", url=f"tg://user?id={OWNER_ID}", style=enums.ButtonStyle.PRIMARY) if OWNER_ID else
              InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="iota_close", style=enums.ButtonStyle.DANGER)]]
        ),
    )


