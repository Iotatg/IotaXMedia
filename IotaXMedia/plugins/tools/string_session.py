# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""String Session Generator for Iota (PM only).

DEPRECATED: the /string flow now lives in
``IotaXMedia/clone/handlers/session_gen.py`` (registered on the main bot
via ``__main__.register`` and on each clone via ``clone.handlers.register_all``).
The /string group-guard and PM command below intentionally no-op so this
plugin does not double-respond alongside the new handler set. The phone →
OTP → 2FA state machine has moved to ``session_gen.py``; the older
in-memory ``_sessions`` dict and step handler are kept here only to avoid
breaking any imports that still reference this module by name, but they
are never wired to a live update.
"""
import time

from pyrogram import Client, filters
from pyrogram.types import Message

from IotaXMedia import app  # noqa: F401  (import kept for any legacy import sites)


@app.on_message(filters.command(["session", "string"]) & filters.group)
async def string_session_group_guard(_: Client, message: Message):



    return


@app.on_message(filters.command(["session", "string"]) & filters.private)
async def string_session_cmd(_: Client, message: Message):




    return

