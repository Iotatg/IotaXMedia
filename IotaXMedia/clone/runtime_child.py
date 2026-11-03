# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone state + config snapshots.

In the current (in-process) architecture the clone bot runs the full
``__main__.init()`` as an asyncio task in the main process. ``CloneRuntime`` is
the per-clone state holder that ``init()`` populates and the clone handlers read;
``CloneConfig`` is the hydrated customization snapshot.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional


class CloneConfig:
    """Per-clone configuration snapshot, hydrated from Mongo at boot."""

    def __init__(self, record: Dict[str, Any], settings: Dict[str, Any]) -> None:
        self.token = record["_id"]
        self.bot_id = int(record.get("bot_id") or 0)
        self.username = (record.get("username") or "").lstrip("@")
        self.owner_id = int(record.get("owner_id") or 0)
        self.status = record.get("status") or "pending"

        self.display_name = settings.get("display_name")
        self.start_media = settings.get("start_media")
        self.start_message = settings.get("start_message")
        self.ping_media = settings.get("ping_media")
        self.stats_media = settings.get("stats_media")
        self.channel_link = settings.get("channel_link")
        self.support_link = settings.get("support_link")
        self.channel_name = settings.get("channel_name")
        self.support_name = settings.get("support_name")
        self.owner_name = settings.get("owner_name")
        self.string_session = settings.get("string_session")
        self.mongo_uri = settings.get("mongo_uri")
        self.chatbot_enabled = bool(settings.get("chatbot", False))
        self.btn_help = settings.get("btn_help", True)
        self.btn_clone = settings.get("btn_clone", True)
        self.btn_support = settings.get("btn_support", True)
        self.btn_channel = settings.get("btn_channel", True)
        self.btn_owner = settings.get("btn_owner", True)
        self.extra_buttons = settings.get("extra_buttons") or []

    def has_music(self) -> bool:
        return bool(self.string_session)


class CloneRuntime:
    """Per-clone runtime state populated by ``__main__.init()``."""

    def __init__(self, token: str) -> None:
        self.token = token.strip()
        self.config: Optional[CloneConfig] = None
        self.app: Optional[Any] = None
        self.userbot: Optional[Any] = None
        self.call: Optional[Any] = None
        self.mongo: Optional[Any] = None
        self._boot_time: float = 0.0
        self._shutting_down = asyncio.Event()

    def request_shutdown(self) -> None:
        if not self._shutting_down.is_set():
            self._shutting_down.set()
