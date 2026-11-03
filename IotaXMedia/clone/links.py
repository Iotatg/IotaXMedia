# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Clone-aware channel / support link resolution.

In clone mode (``config.CLONE_MODE`` True and a ``CloneConfig`` loaded into
``config.CLONE_CONFIG``) these return the clone owner's configured links,
falling back to the main bot's links when the clone has not set its own.
On the main bot ``config.CLONE_CONFIG`` is either unset or holds the main
bot's own settings, so these simply return the main bot's links unchanged.

This keeps every shared panel / markup builder (start, ping, help, playlists)
in sync with the clone's ``/setchannel`` / ``/setsupport`` values without
having to thread the clone config through each call site.
"""
from config import SUPPORT_CHAT, SUPPORT_CHANNEL

import config as _cfg


def clone_channel_link() -> str:
    if getattr(_cfg, "CLONE_MODE", False):
        cc = getattr(_cfg, "CLONE_CONFIG", None)
        if cc is not None:
            link = getattr(cc, "channel_link", None)
            if link:
                return link
    return SUPPORT_CHANNEL


def clone_support_link() -> str:
    if getattr(_cfg, "CLONE_MODE", False):
        cc = getattr(_cfg, "CLONE_CONFIG", None)
        if cc is not None:
            link = getattr(cc, "support_link", None)
            if link:
                return link
    return SUPPORT_CHAT
