# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from IotaXMedia.utils.colored_buttons import styled_button

import config
from IotaXMedia import app
from IotaXMedia.clone.links import clone_channel_link, clone_support_link


def _btn_on(cc, key, default=True):
    if cc is None:
        return default
    value = getattr(cc, f"btn_{key}", default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("0", "false", "off", "no")


def _clone_cfg():
    if not bool(getattr(config, "CLONE_MODE", False)):
        return None
    return getattr(config, "CLONE_CONFIG", None)


def _extra_button_rows(cc):
    rows = []
    extras = getattr(cc, "extra_buttons", None) if cc else None
    if isinstance(extras, list):
        for extra in extras:
            if isinstance(extra, dict) and extra.get("name") and extra.get("url"):
                rows.append([styled_button(text=extra["name"], url=extra["url"], style="primary")])
    return rows


def start_panel(_):
    channel = clone_channel_link()
    support = clone_support_link()
    cc = _clone_cfg()
    channel_name = (getattr(cc, "channel_name", None) if cc else None) or _["S_B_2"]
    support_name = (getattr(cc, "support_name", None) if cc else None) or _["S_B_4"]
    buttons = []
    if _btn_on(cc, "clone") and getattr(app, "username", None):
        buttons.append(
            [
                styled_button(
                    text=_["S_B_1"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style="success",
                ),
            ]
        )
    row = []
    if _btn_on(cc, "channel"):
        row.append(styled_button(text=channel_name, url=channel, style="primary"))
    if _btn_on(cc, "support"):
        row.append(styled_button(text=support_name, url=support, style="primary"))
    if row:
        buttons.append(row)
    buttons.extend(_extra_button_rows(cc))
    return buttons


def private_panel(_):
    is_clone = bool(getattr(config, "CLONE_MODE", False))
    channel = clone_channel_link()
    support = clone_support_link()
    cc = _clone_cfg()
    owner_id = getattr(config, "OWNER_ID", None)
    if cc is not None:
        clone_owner = getattr(cc, "owner_id", None)
        if clone_owner:
            owner_id = clone_owner
    has_owner = bool(owner_id) and str(owner_id).isdigit() and int(owner_id) > 0
    channel_name = (getattr(cc, "channel_name", None) if cc else None) or _["S_B_2"]
    support_name = (getattr(cc, "support_name", None) if cc else None) or _["S_B_4"]
    owner_name = (getattr(cc, "owner_name", None) if cc else None) or _["S_B_7"]
    buttons = []
    if _btn_on(cc, "clone") and getattr(app, "username", None):
        buttons.append(
            [
                styled_button(
                    text=_["S_B_1"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style="success",
                )
            ]
        )
    help_row = []
    if _btn_on(cc, "help"):
        help_row.append(styled_button(text=_["S_B_3"], callback_data="open_help", style="primary"))
        help_row.append(
            styled_button(
                text=_["S_B_8"],
                callback_data="chelp_open" if not is_clone else "open_help",
                style="danger",
            )
        )
    if help_row:
        buttons.append(help_row)
    mid = []
    if has_owner and _btn_on(cc, "owner"):
        mid.append(styled_button(text=owner_name, url=f"tg://user?id={owner_id}", style="primary"))
    if _btn_on(cc, "support"):
        mid.append(styled_button(text=support_name, url=support, style="primary"))
    if mid:
        buttons.append(mid)
    bottom = []
    if _btn_on(cc, "channel"):
        bottom.append(styled_button(text=channel_name, url=channel, style="primary"))
        bottom.append(
            styled_button(
                text=_["S_B_9"],
                url=getattr(config, "REPO_URL", None) or "https://github.com/Iotatg/Iota",
                style="primary",
            )
        )
    if bottom:
        buttons.append(bottom)
    buttons.extend(_extra_button_rows(cc))
    return buttons
