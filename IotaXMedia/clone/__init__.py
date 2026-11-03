# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
IotaXMedia.clone — clone bot subsystem.

Lets a real owner clone the music bot (and its commands/customization) into
independent child bot instances, each driven by the cloner's own bot token.
Runs each clone inside its own process via the multiprocessing worker in
``runtime``. A clone can optionally use its own MongoDB ``setmongodb`` URI
for full isolation.

Importing this package is safe and cheap — heavy work (spawn child
processes) happens lazily through ``CloneManager``.
"""
from __future__ import annotations

from .db import (
    get_clone,
    get_all_clones,
    add_clone,
    update_clone,
    delete_clone,
    count_clones,
    get_clone_owner,
    get_clones_by_owner,
    set_clone_status,
    get_clone_setting,
    set_clone_setting,
    del_clone_setting,
    purge_clones,
)
from .runtime import CloneManager
from .customization import (
    get_start_media,
    set_start_media,
    del_start_media,
    get_start_message,
    set_start_message,
    del_start_message,
    get_ping_media,
    set_ping_media,
    del_ping_media,
    get_stats_media,
    set_stats_media,
    del_stats_media,
    get_clone_channel,
    set_clone_channel,
    get_clone_support,
    set_clone_support,
    set_clone_string,
    del_clone_string,
    set_clone_mongo,
    del_clone_mongo,
    get_clone_chatbot,
    set_clone_chatbot,
    get_clone_name,
    set_clone_name,
)

__all__ = [
    "CloneManager",

    "get_clone",
    "get_all_clones",
    "add_clone",
    "update_clone",
    "delete_clone",
    "count_clones",
    "get_clone_owner",
    "get_clones_by_owner",
    "set_clone_status",
    "get_clone_setting",
    "set_clone_setting",
    "del_clone_setting",
    "purge_clones",

    "get_start_media",
    "set_start_media",
    "del_start_media",
    "get_start_message",
    "set_start_message",
    "del_start_message",
    "get_ping_media",
    "set_ping_media",
    "del_ping_media",
    "get_stats_media",
    "set_stats_media",
    "del_stats_media",
    "get_clone_channel",
    "set_clone_channel",
    "get_clone_support",
    "set_clone_support",
    "set_clone_string",
    "del_clone_string",
    "set_clone_mongo",
    "del_clone_mongo",
    "get_clone_chatbot",
    "set_clone_chatbot",
    "get_clone_name",
    "set_clone_name",
]
