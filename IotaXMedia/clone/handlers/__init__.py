# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone handlers.

The clone runs the FULL main plugin set as a true replica of the main bot.
Only the clone-owner customization commands live in this sub-package; they are
registered in ``CLONE_HANDLER_GROUP`` so the main plugins can't shadow them.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import customization
from . import session_gen

if TYPE_CHECKING:
    from ..runtime_child import CloneRuntime


async def register_all(runtime: "CloneRuntime") -> None:
    """Register the clone customization handler set."""
    await customization.register(runtime)
    await session_gen.register(runtime)
