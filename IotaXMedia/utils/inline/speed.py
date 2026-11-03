# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from IotaXMedia.utils.colored_buttons import styled_button


def speed_markup(_, chat_id):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🕒 0.5x",
                    callback_data=f"SpeedUP {chat_id}|0.5",
                style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(
                    text="🕓 0.75x",
                    callback_data=f"SpeedUP {chat_id}|0.75",
                style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton(
                    text=_["P_B_4"],
                    callback_data=f"SpeedUP {chat_id}|1.0",
                style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton(
                    text="🕤 1.5x",
                    callback_data=f"SpeedUP {chat_id}|1.5",
                style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton(
                    text="🕛 2.0x",
                    callback_data=f"SpeedUP {chat_id}|2.0",
                style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                style=enums.ButtonStyle.DANGER),
            ],
        ]
    )
    return upl


def speed_markup_colored(_, chat_id):
    return [
        [
            styled_button("🕒 0.5x", callback_data=f"SpeedUP {chat_id}|0.5", style="primary"),
            styled_button("🕓 0.75x", callback_data=f"SpeedUP {chat_id}|0.75", style="primary"),
        ],
        [
            styled_button(_["P_B_4"], callback_data=f"SpeedUP {chat_id}|1.0", style="success"),
        ],
        [
            styled_button("🕤 1.5x", callback_data=f"SpeedUP {chat_id}|1.5", style="primary"),
            styled_button("🕛 2.0x", callback_data=f"SpeedUP {chat_id}|2.0", style="primary"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]
