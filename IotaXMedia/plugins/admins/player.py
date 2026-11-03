# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import os

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram import enums

from IotaXMedia import app
import config
from IotaXMedia.utils.decorators import AdminActual, language
from IotaXMedia.utils.god_style import god_text


def _miniapp_url() -> str:
    return getattr(config, "MINIAPP_URL", "") or os.getenv("IOTAX_MINIAPP_URL", "")


@app.on_message(filters.command(["player", "mini"]) & filters.group)
@AdminActual
async def player_command(client, message, _):
    url = _miniapp_url()
    if not url:
        return await message.reply_text(
            god_text("mini-app player not configured")
            + ".\nset IOTAX_MINIAPP_URL (or config.MINIAPP_URL) to a hosted web app."
        )
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(god_text("open player"), web_app=WebAppInfo(url=url), style=enums.ButtonStyle.PRIMARY)]]
    )
    await message.reply_text(
        f"🎛 {god_text('mini-app player')}\n" + god_text("tap to open the web player"),
        reply_markup=markup,
    )
