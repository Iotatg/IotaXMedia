# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Extend Pyrogram channel-id range for modern Telegram supergroups.

Stock pyrogram 2.0.x uses MIN_CHANNEL_ID = -1002147483647 (signed 32-bit
channel ids). New supergroups can exceed that (e.g. -1003915834221), which
makes resolve_peer raise ``ValueError: Peer id invalid`` and blocks VC join.

Must be applied before any Client is constructed.
"""


def apply() -> None:
    try:
        import pyrogram.utils as u
    except Exception:
        return


    wide_min = -100999999999999
    if getattr(u, "MIN_CHANNEL_ID", 0) > wide_min:
        u.MIN_CHANNEL_ID = wide_min


    if getattr(u, "MAX_USER_ID", 0) < 999999999999:
        u.MAX_USER_ID = 999999999999
