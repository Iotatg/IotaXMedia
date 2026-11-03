# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Clone string-session generator — pyrogram handlers.

Adds the ``/string`` command to a clone bot. Generates a Pyrogram string
session through a phone -> OTP -> (2FA) flow in PM only, then sends the
generated session back in PM so the owner can paste it into ``/setstring``.

``/setstring`` is intentionally NOT modified — this generator is purely a
session producer; saving + restart stays the owner's manual step.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pyrogram import filters
from pyrogram.types import Message

from IotaXMedia.utils.replies import NOT_YOURS

from .. import session_gen as sg
from ._common import CLONE_HANDLER_GROUP

if TYPE_CHECKING:
    from ..runtime_child import CloneRuntime


_HELP = (
    "Generate a Pyrogram string session.\n\n"
    "This flow is PM-only. Steps:\n"
    "1. Send your phone number in international format, e.g. +911234567890\n"
    "2. Send the OTP Telegram delivered to you (spaces are ok, e.g. 5 4 0 5 5)\n"
    "3. If 2FA is enabled, send your 2FA password\n"
    "4. Copy the session string and apply it with /setstring <session>\n\n"
    "Send /cancel at any time to abort the flow."
)


async def _reply(message: Message, text: str) -> None:
    """Send a reply, swallowing any send failure (Telegram can refuse silently)."""
    try:
        await message.reply_text(text)
    except Exception:
        return None


def _is_owner(message: Message, owner_id: int) -> bool:
    user = message.from_user
    if user is None:
        return False
    return int(user.id) == int(owner_id or 0)


async def register(runtime, owner_filter=None) -> None:
    app = runtime.app
    cfg = runtime.config



    if cfg is None:
        try:
            from ..db import get_clone, get_all_clone_settings
            from ..runtime_child import CloneConfig
            rec = await get_clone(runtime.token)
            if rec:
                settings = await get_all_clone_settings(runtime.token)
                cfg = CloneConfig(rec, settings)
                runtime.config = cfg
        except Exception:
            cfg = None

    owner_id = int(getattr(cfg, "owner_id", 0) or 0) if cfg else 0
    from IotaXMedia.misc import SUDOERS




    open_to_all = owner_filter is not None

    import config as _cfg

    manager = sg.SessionGenManager(api_id=int(_cfg.API_ID), api_hash=str(_cfg.API_HASH))
    if not open_to_all:
        manager.set_owner(owner_id)

    async def _allowed(_client, message: Message) -> bool:
        if message.from_user is None:
            return False
        if open_to_all:
            return True
        if _is_owner(message, owner_id):
            return True
        try:
            return bool(await SUDOERS(_client, message))
        except Exception:
            return False

    def _uid(message: Message) -> int:
        return int(message.from_user.id)


    @app.on_message(
        filters.command(["string", "session", "genstring"]) & filters.group,
        group=CLONE_HANDLER_GROUP,
    )
    async def _string_group_guard(_client, message: Message):
        return await _reply(
            message,
            "String Session Generator is PM-only.\n\n"
            "For your account safety, send /string to me in a private chat.",
        )


    @app.on_message(
        filters.command(["string", "session", "genstring"]) & filters.private,
        group=CLONE_HANDLER_GROUP,
    )
    async def _string_cmd(_client, message: Message):
        if not await _allowed(_client, message):
            return await _reply(
                message,
                NOT_YOURS,
            )
        uid = _uid(message)
        manager.start(uid)
        return await _reply(message, _HELP)


    @app.on_message(
        filters.private
        & ~filters.command(["string", "session", "genstring", "cancel", "stringcancel"])
        & filters.create(
            lambda _, __, m: m.from_user is not None and manager.is_active(int(m.from_user.id))
        ),
        group=CLONE_HANDLER_GROUP,
    )
    async def _string_step(_client, message: Message):
        uid = _uid(message)
        if not manager.is_active(uid):
            return None
        text = message.text or ""
        if not text:
            return await _reply(
                message,
                "This flow only accepts text. Run /cancel to abort.",
            )
        st = manager.get(uid)
        if st is None:
            return None
        import time as _t

        if _t.monotonic() - st.updated > manager._ttl:
            await manager.drop(uid)
            return await _reply(
                message,
                "Flow expired. Run /string to start again.",
            )

        if st.stage == sg.STAGE_PHONE:
            status, _payload = await sg.start_phone(manager, uid, text)
            return await _reply(message, _phone_reply(status))

        if st.stage == sg.STAGE_OTP:
            status, _payload = await sg.submit_otp(manager, uid, text)
            return await _reply(message, _otp_reply(status, _payload))

        if st.stage == sg.STAGE_PASSWORD:
            status, payload = await sg.submit_password(manager, uid, text)
            return await _reply(message, _password_reply(status, payload))

        return None


    @app.on_message(
        filters.command(["cancel", "stringcancel"]) & filters.private,
        group=CLONE_HANDLER_GROUP,
    )
    async def _cancel_cmd(_client, message: Message):
        if not await _allowed(_client, message):
            return await _reply(message, NOT_YOURS)
        uid = _uid(message)
        if not manager.is_active(uid):
            return await _reply(message, "No active /string flow to cancel.")
        await manager.drop(uid)
        return await _reply(message, "String-session flow cancelled.")



def _session_ok(payload) -> str:
    return (
        "String session generated successfully!\n\n"
        "Copy your session below (treat it like a password — never share it):\n\n"
        f"<code>{payload}</code>\n\n"
        "Next step: /setstring <session-above> to apply it to this clone."
    )


def _phone_reply(status: str) -> str:
    if status == sg.OK:
        return "Enter the OTP code Telegram sent you."
    if status == sg.ERR_INVALID_PHONE:
        return "Send a valid phone number, for example: +911234567890"
    if status == sg.ERR_SEND_FAILED:
        return "Could not send the OTP. Run /string to retry."
    return "Unexpected error. Run /string to restart."


def _otp_reply(status: str, payload) -> str:
    if status == sg.OK and payload:
        return _session_ok(payload)
    if status == sg.PASSWORD_NEEDED:
        return "Two-step verification is on. Send your 2FA password:"
    if status == sg.ERR_INVALID_CODE:
        return "Invalid OTP. Send the correct code, or /string to restart."
    if status == sg.ERR_SIGNIN_FAILED:
        return "OTP sign-in failed. Run /string to restart."
    if status == sg.ERR_NEED_ACTIVE:
        return "No active flow. Run /string to start."
    return "Unexpected error. Run /string to restart."


def _password_reply(status: str, payload) -> str:
    if status == sg.OK and payload:
        return _session_ok(payload)
    if status == sg.ERR_BAD_PASSWORD:
        return "Password verification failed. Run /string to restart."
    if status == sg.ERR_SIGNIN_FAILED:
        return "Could not export the session. Run /string to restart."
    if status == sg.ERR_NEED_ACTIVE:
        return "No active flow. Run /string to start."
    return "Unexpected error. Run /string to restart."
