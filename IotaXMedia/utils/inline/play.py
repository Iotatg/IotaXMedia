# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import time
from pyrogram import enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from IotaXMedia.utils.colored_buttons import styled_button
from IotaXMedia.utils.formatters import time_to_seconds
from IotaXMedia.utils.god_style import god_text
import config
from IotaXMedia.clone.links import clone_support_link

LAST_UPDATE_TIME = {}


def _autoplay_on(chat_id: int) -> bool:
    """Best-effort autoplay state for sync markup builders.

    Lazy import: utils.stream.autoplay pulls in core.call which imports this
    module, so a module-level import would be circular.
    """
    try:
        from IotaXMedia.utils.stream.autoplay import AUTO_STATE

        return AUTO_STATE.get(int(chat_id), True)
    except Exception:
        return True


def track_markup(_, videoid, user_id, channel, fplay):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            , style=enums.ButtonStyle.DANGER)
        ],
    ])


def should_update_progress(chat_id):
    now = time.time()
    last = LAST_UPDATE_TIME.get(chat_id, 0)
    if now - last >= 6:
        LAST_UPDATE_TIME[chat_id] = now
        return True
    return False


def generate_progress_bar(played_sec, duration_sec):
    if duration_sec == 0:
        percentage = 0
    else:
        percentage = min((played_sec / duration_sec) * 100, 100)

    bar_length = 10
    filled = int(round(bar_length * percentage / 100))
    return "▰" * filled + "▱" * (bar_length - filled)


def control_buttons(_, chat_id):
    return [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=enums.ButtonStyle.DANGER),
        ],
        [
            InlineKeyboardButton(text="νσℓ −", callback_data=f"ADMIN VolDown|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="⌬ νσℓ", callback_data=f"ADMIN VolShow|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="νσℓ +", callback_data=f"ADMIN VolUp|{chat_id}", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(text="-𝟷𝟻ˢ", callback_data=f"stream_admin Seek|-15|{chat_id}", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(text="𝟷𝟻ˢ+", callback_data=f"stream_admin Seek|15|{chat_id}", style=enums.ButtonStyle.PRIMARY),
        ],
    ]


def stream_markup_timer(_, chat_id, played, dur, force=False):
    if not force and not should_update_progress(chat_id):
        return None

    duration_sec = time_to_seconds(dur)
    if duration_sec <= 0:

        return stream_markup(_, chat_id)

    played_sec = time_to_seconds(played)
    bar = generate_progress_bar(played_sec, duration_sec)

    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text=f"{played} {bar} {dur}", callback_data="GetTimer", style=enums.ButtonStyle.PRIMARY)]] +
        control_buttons(_, chat_id) +
        [[InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER)]]
    )


def stream_markup(_, chat_id):
    return InlineKeyboardMarkup(
        control_buttons(_, chat_id) +
        [[InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER)]]
    )


def stream_markup_colored(_, chat_id):
    return [
        [
            styled_button("▷", callback_data=f"stream_admin Resume|{chat_id}", style="success"),
            styled_button("II", callback_data=f"stream_admin Pause|{chat_id}", style="primary"),
            styled_button("↻", callback_data=f"stream_admin Replay|{chat_id}", style="success"),
            styled_button("‣‣I", callback_data=f"stream_admin Skip|{chat_id}", style="primary"),
            styled_button("▢", callback_data=f"stream_admin Stop|{chat_id}", style="danger"),
        ],
        [
            styled_button("-𝟷𝟻", callback_data=f"stream_admin VolDown|{chat_id}", style="primary"),
            styled_button("𝟷𝟻+", callback_data=f"stream_admin VolUp|{chat_id}", style="primary"),
        ],
        [
            styled_button(
                god_text("autoplay") + (" 🟢" if _autoplay_on(chat_id) else " 🔴"),
                callback_data=f"AUTOPLAY_TOGGLE {chat_id}",
                style="success" if _autoplay_on(chat_id) else "danger",
            ),
            styled_button("ᴛʜᴜᴍʙɴᴀɪʟ", callback_data=f"THUMB_TOGGLE {chat_id}", style="primary"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"IotaPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"
            , style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"IotaPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
            , style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            , style=enums.ButtonStyle.DANGER),
        ],
    ])


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY)
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}"
            , style=enums.ButtonStyle.DANGER)
        ],
    ])


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    short_query = query[:20]
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=f"slider B|{query_type}|{short_query}|{user_id}|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {short_query}|{user_id}",
            style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton(
                text="▷",
                callback_data=f"slider F|{query_type}|{short_query}|{user_id}|{channel}|{fplay}",
            style=enums.ButtonStyle.PRIMARY),
        ],
    ])




def track_markup_colored(_, videoid, user_id, channel, fplay):
    return [
        [
            styled_button(_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style="primary"),
            styled_button(_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style="success"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style="danger"),
        ],
    ]


def playlist_markup_colored(_, videoid, user_id, ptype, channel, fplay):
    return [
        [
            styled_button(_["P_B_1"], callback_data=f"IotaPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}", style="primary"),
            styled_button(_["P_B_2"], callback_data=f"IotaPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}", style="success"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style="danger"),
        ],
    ]


def livestream_markup_colored(_, videoid, user_id, mode, channel, fplay):
    return [
        [
            styled_button(_["P_B_3"], callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}", style="danger"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style="danger"),
        ],
    ]


def slider_markup_colored(_, videoid, user_id, query, query_type, channel, fplay):
    short_query = query[:20]
    return [
        [
            styled_button(_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style="primary"),
            styled_button(_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style="success"),
        ],
        [
            styled_button("◁", callback_data=f"slider B|{query_type}|{short_query}|{user_id}|{channel}|{fplay}", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data=f"forceclose {short_query}|{user_id}", style="danger"),
            styled_button("▷", callback_data=f"slider F|{query_type}|{short_query}|{user_id}|{channel}|{fplay}", style="primary"),
        ],
    ]


def botplaylist_markup_colored(_):
    return [
        [
            styled_button(_["S_B_4"], url=clone_support_link(), style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def close_markup_colored(_):
    return [
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def ended_markup_colored():
    return [
        [
            styled_button("____________________", callback_data="GetTimer", style="primary"),
        ],
    ]


def song_markup_colored(_, vidid):
    return [
        [
            styled_button(_["SG_B_2"], callback_data=f"song_helper audio|{vidid}", style="primary"),
            styled_button(_["SG_B_3"], callback_data=f"song_helper video|{vidid}", style="success"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def queue_markup_colored(_, DURATION, CPLAY, videoid, played, dur):
    from config import DURATION_LIMIT_MIN
    return [
        [
            styled_button(_["QU_B_2"].format(played, dur), callback_data="GetTimer", style="primary"),
        ],
        [
            styled_button(_["QU_B_1"], callback_data=f"GetQueued {CPLAY}|{videoid}", style="success"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


def queue_back_markup_colored(_, CPLAY):
    return [
        [
            styled_button(_["BACK_BUTTON"], callback_data=f"queue_back_timer {CPLAY}", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]


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


def stream_markup_timer_colored(_, chat_id, played, dur, force=False):
    if not force and not should_update_progress(chat_id):
        return None

    duration_sec = time_to_seconds(dur)
    if duration_sec <= 0:

        return stream_markup_colored(_, chat_id)

    played_sec = time_to_seconds(played)
    bar = generate_progress_bar(played_sec, duration_sec)
    return [
        [styled_button(f"{played} {bar} {dur}", callback_data="GetTimer", style="primary")],
        [
            styled_button("▷", callback_data=f"stream_admin Resume|{chat_id}", style="success"),
            styled_button("II", callback_data=f"stream_admin Pause|{chat_id}", style="primary"),
            styled_button("↻", callback_data=f"stream_admin Replay|{chat_id}", style="success"),
            styled_button("‣‣I", callback_data=f"stream_admin Skip|{chat_id}", style="primary"),
            styled_button("▢", callback_data=f"stream_admin Stop|{chat_id}", style="danger"),
        ],
        [
            styled_button("-𝟷𝟻", callback_data=f"stream_admin VolDown|{chat_id}", style="primary"),
            styled_button("𝟷𝟻+", callback_data=f"stream_admin VolUp|{chat_id}", style="primary"),
        ],
        [
            styled_button(
                god_text("autoplay") + (" 🟢" if _autoplay_on(chat_id) else " 🔴"),
                callback_data=f"AUTOPLAY_TOGGLE {chat_id}",
                style="success" if _autoplay_on(chat_id) else "danger",
            ),
            styled_button("ᴛʜᴜᴍʙɴᴀɪʟ", callback_data=f"THUMB_TOGGLE {chat_id}", style="primary"),
        ],
        [
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ],
    ]