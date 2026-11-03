# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums

from config import SUPPORT_CHAT
from IotaXMedia.utils.colored_buttons import styled_button
from IotaXMedia.clone.links import clone_support_link


def botplaylist_markup(_):
    buttons = [
        [
            InlineKeyboardButton(text=_["S_B_4"], url=clone_support_link(), style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER),
        ],
    ]
    return buttons


def botplaylist_markup_colored(_):
    return [
        [
            styled_button(_["S_B_4"], url=clone_support_link(), style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def close_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                style=enums.ButtonStyle.DANGER),
            ]
        ]
    )
    return upl


def close_markup_colored(_):
    return [
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def supp_markup(_):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["S_B_4"],
                    url=clone_support_link(),
                style=enums.ButtonStyle.PRIMARY),
            ]
        ]
    )
    return upl


def supp_markup_colored(_):
    return [
        [
            styled_button(_["S_B_4"], url=clone_support_link(), style="primary"),
        ],
    ]
