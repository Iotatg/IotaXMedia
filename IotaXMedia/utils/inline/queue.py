# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from typing import Union
from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from IotaXMedia.utils.colored_buttons import styled_button


def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur_val: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style=enums.ButtonStyle.DANGER,
            ),
        ]
    ]
    dur_buttons = [
        [
            InlineKeyboardButton(
                text=_["QU_B_2"].format(played, dur_val),
                callback_data="GetTimer",
                style=enums.ButtonStyle.PRIMARY,
            )
        ],
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style=enums.ButtonStyle.DANGER,
            ),
        ],
    ]
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" else dur_buttons)
    return upl


def queue_markup_colored(_, DURATION, CPLAY, videoid, played=None, dur_val=None):
    if DURATION == "Unknown":
        return [
            [
                styled_button(_["QU_B_1"], callback_data=f"GetQueued {CPLAY}|{videoid}", style="primary"),
                styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
            ],
        ]
    return [
        [
            styled_button(_["QU_B_2"].format(played, dur_val), callback_data="GetTimer", style="primary"),
        ],
        [
            styled_button(_["QU_B_1"], callback_data=f"GetQueued {CPLAY}|{videoid}", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=f"queue_back_timer {CPLAY}",
                style=enums.ButtonStyle.PRIMARY,
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style=enums.ButtonStyle.DANGER,
            ),
            ]
        ]
    )
    return upl


def queue_back_markup_colored(_, CPLAY):
    return [
        [
            styled_button(_["BACK_BUTTON"], callback_data=f"queue_back_timer {CPLAY}", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"stream_admin Resume|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="II", callback_data=f"stream_admin Pause|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="‣‣I", callback_data=f"stream_admin Skip|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="▢", callback_data=f"stream_admin Stop|{chat_id}", style=enums.ButtonStyle.DANGER),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER)],
    ]
    return buttons


def aq_markup_colored(_, chat_id):
    return [
        [
            styled_button("▷", callback_data=f"stream_admin Resume|{chat_id}", style="primary"),
            styled_button("II", callback_data=f"stream_admin Pause|{chat_id}", style="primary"),
            styled_button("‣‣I", callback_data=f"stream_admin Skip|{chat_id}", style="primary"),
            styled_button("▢", callback_data=f"stream_admin Stop|{chat_id}", style="danger"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]