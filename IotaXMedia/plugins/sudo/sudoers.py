# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums

from config import BANNED_USERS, OWNER_ID
from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.database import add_sudo, remove_sudo
from IotaXMedia.utils.decorators.language import language
from IotaXMedia.utils.extraction import extract_user
from IotaXMedia.utils.replies import NOT_ON_LIST
from IotaXMedia.utils.permissions import mention
from IotaXMedia.utils.colored_buttons import (
    edit_message_caption_colored,
    send_video_colored,
    styled_button,
)



@app.on_message(filters.command(["addsudo"], prefixes=["/", "!", "."]) & filters.user(OWNER_ID))
@language
async def add_sudo_user(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)
    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention), parse_mode="HTML")

    if await add_sudo(user.id):
        if user.id not in SUDOERS:
            SUDOERS.add(user.id)
        return await message.reply_text(_["sudo_2"].format(user.mention), parse_mode="HTML")

    await message.reply_text(_["sudo_8"])



@app.on_message(filters.command(["delsudo", "rmsudo"], prefixes=["/", "!", "."]) & filters.user(OWNER_ID))
@language
async def remove_sudo_user(client, message: Message, _):
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text(_["general_1"])

    user = await extract_user(message)
    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"].format(user.mention), parse_mode="HTML")

    if await remove_sudo(user.id):
        if user.id in SUDOERS:
            SUDOERS.remove(user.id)
        return await message.reply_text(_["sudo_4"].format(user.mention), parse_mode="HTML")

    await message.reply_text(_["sudo_8"])



@app.on_message(filters.command(["sudolist", "listsudo", "sudoers"], prefixes=["/", "!", "."]) & ~filters.user(list(BANNED_USERS)))
async def sudoers_list(client, message: Message):
    keyboard = [[InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="sudo_list_view", style=enums.ButtonStyle.PRIMARY)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    keyboard_col = [[styled_button("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="sudo_list_view", style="primary")]]
    caption = "**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**\n\n**» ɴᴏᴛᴇ:**  ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀs ᴄᴀɴ ᴠɪᴇᴡ."

    try:
        r = await send_video_colored(
            message.chat.id,
            "https://files.catbox.moe/x7v3k6.mp4",
            caption=caption,
            reply_markup=keyboard_col,
            parse_mode="markdown",
        )
        if r:
            return
    except Exception:
        pass
    await message.reply_video(
        video="https://files.catbox.moe/x7v3k6.mp4",
        caption=caption,
        reply_markup=reply_markup
    )



@app.on_callback_query(filters.regex("^sudo_list_view$"))
async def view_sudo_list_callback(client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer(NOT_ON_LIST, show_alert=True)

    owner = await app.get_users(OWNER_ID)
    caption = f"**˹ʟɪsᴛ ᴏғ ʙᴏᴛ ᴍᴏᴅᴇʀᴀᴛᴏʀs˼**\n\n**🌹Oᴡɴᴇʀ** ➥ {mention(owner.id, owner.first_name)}\n\n"
    keyboard = [[InlineKeyboardButton("๏ ᴠɪᴇᴡ ᴏᴡɴᴇʀ ๏", url=f"tg://openmessage?user_id={OWNER_ID}", style=enums.ButtonStyle.PRIMARY)]]
    keyboard_col = [[styled_button("๏ ᴠɪᴇᴡ ᴏᴡɴᴇʀ ๏", url=f"tg://openmessage?user_id={OWNER_ID}", style="primary")]]

    count = 0
    for user_id in SUDOERS:
        if user_id == OWNER_ID:
            continue
        try:
            user = await app.get_users(user_id)
            count += 1
            caption += f"**🎁 Sᴜᴅᴏ {count} »** {mention(user.id, user.first_name)}\n"
            keyboard.append([
                InlineKeyboardButton(f"๏ ᴠɪᴇᴡ sᴜᴅᴏ {count} ๏", url=f"tg://openmessage?user_id={user_id}", style=enums.ButtonStyle.PRIMARY)
            ])
            keyboard_col.append([
                styled_button(f"๏ ᴠɪᴇᴡ sᴜᴅᴏ {count} ๏", url=f"tg://openmessage?user_id={user_id}", style="primary")
            ])
        except Exception:
            continue

    if count == 0:
        caption += "_No additional sudoers yet._"

    keyboard.append([InlineKeyboardButton("๏ ʙᴀᴄᴋ ๏", callback_data="sudo_list_back", style=enums.ButtonStyle.PRIMARY)])
    keyboard_col.append([styled_button("๏ ʙᴀᴄᴋ ๏", callback_data="sudo_list_back", style="primary")])

    try:
        r = await edit_message_caption_colored(
            callback_query.message.chat.id,
            callback_query.message.id,
            caption,
            keyboard_col,
            parse_mode="markdown",
        )
        if r:
            return
    except Exception:
        pass
    try:
        await callback_query.message.edit_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    except MessageNotModified:
        return



@app.on_callback_query(filters.regex("^sudo_list_back$"))
async def back_to_sudo_list_menu(client, callback_query: CallbackQuery):
    keyboard = [[InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="sudo_list_view", style=enums.ButtonStyle.PRIMARY)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    keyboard_col = [[styled_button("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="sudo_list_view", style="primary")]]
    caption = "**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**\n\n**» ɴᴏᴛᴇ:**  ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀs ᴄᴀɴ ᴠɪᴇᴡ."

    try:
        r = await edit_message_caption_colored(
            callback_query.message.chat.id,
            callback_query.message.id,
            caption,
            keyboard_col,
            parse_mode="markdown",
        )
        if r:
            return
    except Exception:
        pass
    try:
        await callback_query.message.edit_caption(
            caption=caption,
            reply_markup=reply_markup
        )
    except MessageNotModified:
        return



@app.on_message(filters.command("delallsudo", prefixes=["/", "!", "%", ",", ".", "@", "#"]) & filters.user(OWNER_ID))
@language
async def remove_all_sudo_users(client, message: Message, _):
    removed_count = 0
    for user_id in list(SUDOERS):
        if user_id != OWNER_ID:
            if await remove_sudo(user_id):
                if user_id in SUDOERS:
                    SUDOERS.remove(user_id)
                removed_count += 1
    await message.reply_text(f"Removed {removed_count} users from the sudo list.")
