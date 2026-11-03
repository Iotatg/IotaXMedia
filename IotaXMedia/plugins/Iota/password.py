# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import random
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import styled_button, edit_message_text_colored
import config


@app.on_message(filters.command(["genpassword", "genpw"]))
async def password(bot, message):
    processing = await message.reply_text("Pʀᴏᴄᴇꜱꜱɪɴɢ...")

    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+"
    
    if len(message.command) > 1:
        input_length = message.text.split(" ", 1)[1]
    else:
        input_length = random.choice(["5", "6", "7", "8", "9", "10", "12", "14"])

    try:
        length = int(input_length)
        if length < 1:
            raise ValueError("Length must be positive.")
    except ValueError:
        return await processing.edit_text("Please enter a valid positive number for the password length.")

    generated_password = "".join(random.choices(characters, k=length))

    reply_text = (
        f"<b>Lɪᴍɪᴛ:</b> {length}\n"
        f"<b>Pᴀꜱꜱᴡᴏʀᴅ:</b> <code>{generated_password}</code>"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("𝗔𝗗𝗗 𝗠𝗘", url=f"https://t.me/{getattr(config, 'BOT_USERNAME', '')}?startgroup=true", style=enums.ButtonStyle.PRIMARY)]
    ])
    buttons_col = [[styled_button("𝗔𝗗𝗗 𝗠𝗘", url=f"https://t.me/{getattr(config, 'BOT_USERNAME', '')}?startgroup=true", style="success")]]

    try:
        r = await edit_message_text_colored(
            processing.chat.id, processing.id, reply_text, buttons_col, parse_mode="HTML"
        )
        if r:
            return
    except Exception:
        pass
    await processing.edit_text(reply_text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)
