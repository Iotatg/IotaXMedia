# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import styled_button
from IotaXMedia.utils.god_style import god_label, SYM, BTN_BACK, BTN_CLOSE
from IotaXMedia.utils.ui_style import button

TOTAL_SECTIONS = 35

RESTRICTED_HELP_SECTIONS = {4, 5, 8, 9, 14}

MUSIC_SECTIONS = [2, 3, 6, 10, 15, 20, 22, 23, 24, 25, 26, 30, 31]
MANAGEMENT_SECTIONS = [1, 7, 11, 12, 13, 16, 17, 18, 19, 21, 27, 28, 29, 32, 33, 34, 35]
RESTRICTED_MUSIC = [4]
RESTRICTED_MANAGEMENT = [5, 8, 9, 14]

ITEMS_PER_PAGE = 9

_BTN_MUSIC = f"{SYM['star']} {god_label('Music')}"
_BTN_MGMT = f"{SYM['seal']} {god_label('Management')}"
_BTN_NEXT = f"{god_label('Next')} ➻"
_BTN_MENU = f"{SYM['tri']} {god_label('Menu')}"
_BTN_BACK_NAV = BTN_BACK


def _padded(sections, is_authorized, restricted_extra):
    result = list(sections)
    if is_authorized:
        for r in restricted_extra:
            if r not in result:
                result.append(r)
    return result


def _make_buttons(_, sections, prefix, page):
    buttons = []
    row = []
    for sec in sections:
        text = _[f"H_B_{sec}"]
        row.append(styled_button(text, callback_data=f"ht_{sec}_{prefix}_{page}", style="primary"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons


def _make_nav(_, page, total, prefix):
    nav = []
    if page > 1:
        nav.append(styled_button(_BTN_BACK_NAV, callback_data=f"h_{prefix}_{page-1}", style="primary"))
    if page < total:
        nav.append(styled_button(_BTN_NEXT, callback_data=f"h_{prefix}_{page+1}", style="primary"))
    else:
        nav.append(styled_button(_BTN_MENU, callback_data="help_main", style="primary"))
        nav.append(styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"))
    return nav


def help_subpage(_, page, total, chunk, prefix):
    buttons = _make_buttons(_, chunk, prefix, page)
    nav = _make_nav(_, page, total, prefix)
    buttons.append(nav)
    return buttons


def help_main_menu(_, is_authorized=False):
    import config as _cfg

    is_clone = bool(getattr(_cfg, "CLONE_MODE", False))
    buttons = [
        [
            styled_button(_BTN_MUSIC, callback_data="h_music_1", style="primary"),
            styled_button(_BTN_MGMT, callback_data="h_mgmt_1", style="success"),
        ],
    ]
    if is_clone:

        buttons.append(
            [
                styled_button(
                    button("customize clone"),
                    callback_data="ccustomize_open",
                    style="danger",
                ),
            ]
        )
    else:
        buttons.append(
            [
                styled_button(
                    _.get("S_B_8", "㋡ 𐌂ℓσηє"),
                    callback_data="chelp_open",
                    style="danger",
                ),
            ]
        )
    buttons.append(
        [
            styled_button(_["BACK_BUTTON"], callback_data="back_to_main", style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ]
    )
    return buttons


def help_music_page(_, page, is_authorized=False):
    sections = _padded(MUSIC_SECTIONS, is_authorized, RESTRICTED_MUSIC)
    total = max(1, (len(sections) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    start = (page - 1) * ITEMS_PER_PAGE
    chunk = sections[start:start + ITEMS_PER_PAGE]
    return help_subpage(_, page, total, chunk, "music")


def help_mgmt_page(_, page, is_authorized=False):
    sections = _padded(MANAGEMENT_SECTIONS, is_authorized, RESTRICTED_MANAGEMENT)
    total = max(1, (len(sections) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    start = (page - 1) * ITEMS_PER_PAGE
    chunk = sections[start:start + ITEMS_PER_PAGE]
    buttons = help_subpage(_, page, total, chunk, "mgmt")
    if page == 1:
        buttons.insert(
            0,
            [
                styled_button(
                    button("bot play buttons"),
                    callback_data="help_playbtns",
                    style="primary",
                ),
            ],
        )
    return buttons


def topic_back_markup(_, back_cb):
    return [
        [
            styled_button(_["BACK_BUTTON"], callback_data=back_cb, style="primary"),
            styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
        ]
    ]




first_page = help_main_menu
second_page = help_mgmt_page


def generate_help_buttons(_, start, end, current_page, is_authorized=False):
    buttons = []
    row = []
    for i in range(start, end + 1):
        if i in RESTRICTED_HELP_SECTIONS and not is_authorized:
            continue
        row.append(styled_button(_[f"H_B_{i}"], callback_data=f"ht_{i}_P_{current_page}", style="primary"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons


def action_sub_menu(_, back_cb):
    return [
        [
            styled_button(_["H_B_S_1"], callback_data="action_prom_1", style="primary"),
            styled_button(_["H_B_S_2"], callback_data="action_pun_1", style="primary"),
        ],
        [
            styled_button(_["BACK_BUTTON"], callback_data=back_cb, style="primary"),
        ]
    ]


def help_back_markup(_, current_page):
    return topic_back_markup(_, f"help_back_{current_page}")


def private_help_panel(_):
    return [
        [
            styled_button(_["S_B_3"], url=f"https://t.me/{app.username}?start=help", style="primary"),
        ],
    ]


def clone_help_panel(_):
    return [
        [
            styled_button(button("start"), callback_data="chelp_start", style="primary"),
            styled_button(button("ping"), callback_data="chelp_ping", style="primary"),
        ],
        [
            styled_button(button("stats"), callback_data="chelp_stats", style="primary"),
            styled_button(f"{button('channel')}/{button('support', deco='')}", callback_data="chelp_channel", style="primary"),
        ],
        [
            styled_button(button("assistant"), callback_data="chelp_assistant", style="primary"),
            styled_button(button("database"), callback_data="chelp_database", style="primary"),
        ],
        [
            styled_button(button("extras"), callback_data="chelp_extras", style="primary"),
        ],
        [
            styled_button(_["BACK_BUTTON"], callback_data="help_back_1", style="primary"),
        ],
    ]


def clone_back_markup(_):
    return [
        [
            styled_button(_["BACK_BUTTON"], callback_data="chelp_open", style="primary"),
        ],
    ]