# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from IotaXMedia.utils.colored_buttons import styled_button


class StatsCallbacks:
    SHOW_OVERVIEW = "stats:overview"
    SHOW_BOT_STATS = "stats:bot"
    BACK = "stats:back"
    CLOSE = "stats:close"


def build_stats_keyboard(_, is_sudo: bool) -> InlineKeyboardMarkup:
    non_sudo_row = [
        InlineKeyboardButton(
            text=_["SA_B_1"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
        style=enums.ButtonStyle.PRIMARY)
    ]
    sudo_row = [
        InlineKeyboardButton(
            text=_["SA_B_2"],
            callback_data=StatsCallbacks.SHOW_BOT_STATS,
        style=enums.ButtonStyle.PRIMARY),
        InlineKeyboardButton(
            text=_["SA_B_3"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
        style=enums.ButtonStyle.PRIMARY),
    ]
    rows = [
        sudo_row if is_sudo else non_sudo_row,
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
            style=enums.ButtonStyle.DANGER)
        ],
    ]
    return InlineKeyboardMarkup(rows)


def build_back_keyboard(_) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=StatsCallbacks.BACK,
            style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
            style=enums.ButtonStyle.DANGER),
        ]
    ]
    return InlineKeyboardMarkup(rows)


def build_stats_keyboard_colored(_, is_sudo: bool) -> list:
    non_sudo_row = [
        styled_button(
            _["SA_B_1"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
            style="primary",
        )
    ]
    sudo_row = [
        styled_button(
            _["SA_B_2"],
            callback_data=StatsCallbacks.SHOW_BOT_STATS,
            style="success",
        ),
        styled_button(
            _["SA_B_3"],
            callback_data=StatsCallbacks.SHOW_OVERVIEW,
            style="primary",
        ),
    ]
    rows = [
        sudo_row if is_sudo else non_sudo_row,
        [
            styled_button(
                _["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
                style="danger",
            )
        ],
    ]
    return rows


def build_back_keyboard_colored(_) -> list:
    rows = [
        [
            styled_button(
                _["BACK_BUTTON"],
                callback_data=StatsCallbacks.BACK,
                style="primary",
            ),
            styled_button(
                _["CLOSE_BUTTON"],
                callback_data=StatsCallbacks.CLOSE,
                style="danger",
            ),
        ]
    ]
    return rows
