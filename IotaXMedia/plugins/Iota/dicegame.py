# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from IotaXMedia import app
from IotaXMedia.utils.permissions import mention
from IotaXMedia.utils.god_style import god_text


@app.on_message(filters.command("dice"))
async def roll_dice(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "🎲")
        m = x.dice.value
        await message.reply_text(
            f"🎲 {god_text('ʜᴇʏ')} {mention(message.from_user.id, message.from_user.first_name)}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}",
            quote=True, parse_mode="markdown"
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")


@app.on_message(filters.command("dart"))
async def throw_dart(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "🎯")
        m = x.dice.value
        await message.reply_text(
            f"🎯 {god_text('ʜᴇʏ')} {message.from_user.mention}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}", quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")


@app.on_message(filters.command("basket"))
async def shoot_basket(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "🏀")
        m = x.dice.value
        await message.reply_text(
            f"🏀 {god_text('ʜᴇʏ')} {message.from_user.mention}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}", quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")


@app.on_message(filters.command("jackpot"))
async def spin_jackpot(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "🎰")
        m = x.dice.value
        await message.reply_text(
            f"🎰 {god_text('ʜᴇʏ')} {message.from_user.mention}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}", quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")


@app.on_message(filters.command("ball"))
async def roll_ball(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "🎳")
        m = x.dice.value
        await message.reply_text(
            f"🎳 {god_text('ʜᴇʏ')} {message.from_user.mention}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}", quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")


@app.on_message(filters.command("football"))
async def kick_football(bot, message):
    try:
        x = await bot.send_dice(message.chat.id, "⚽")
        m = x.dice.value
        await message.reply_text(
            f"⚽ {god_text('ʜᴇʏ')} {message.from_user.mention}, {god_text('ʏᴏᴜʀ sᴄᴏʀᴇ ɪs')}: {m}", quote=True
        )
    except Exception as e:
        await message.reply_text(f"❌ {god_text('ᴇʀʀᴏʀ')}: {str(e)}")
