# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone string-session generator — pure logic, no pyrogram handlers.

A single ``SessionGenManager`` instance lives inside one clone process and
tracks the in-flight phone -> OTP -> (2FA) -> session flow for that clone's
owner. Each per-stage function takes the current ``SessionGenState`` and
returns a tagged result the handler can map to a user-facing message without
knowing anything about pyrogram.

Concurrency: Pyrogram handler dispatch is single-task per chat for a given
client, so no locking is required inside the manager. The state dict is keyed
by ``user_id`` and replaces the prior entry on every new start (a new
``/string`` call drops the previous in-memory ``pyrogram.Client`` so it can
never collide with a new flow).

Tests stub the pyrogram ``Client`` entirely — no network, no DB.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from pyrogram import Client
from pyrogram.errors import (
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    SessionPasswordNeeded,
)


STAGE_NONE = ""
STAGE_PHONE = "phone"
STAGE_OTP = "otp"
STAGE_PASSWORD = "password"

DEFAULT_TTL = 600.0

ERR_INVALID_PHONE = "invalid_phone"
ERR_SEND_FAILED = "send_failed"
ERR_INVALID_CODE = "invalid_code"
ERR_SIGNIN_FAILED = "signin_failed"
ERR_BAD_PASSWORD = "bad_password"
ERR_NEED_ACTIVE = "need_active"

OK = "ok"
PASSWORD_NEEDED = "password_needed"

_ACTIVE_USERS: set = set()


def is_flow_active(user_id: int) -> bool:
    try:
        return int(user_id) in _ACTIVE_USERS
    except Exception:
        return False


@dataclass
class SessionGenState:
    stage: str = STAGE_NONE
    client: Optional[Client] = None
    phone: Optional[str] = None
    code_hash: Optional[str] = None
    updated: float = 0.0
    owner_id: int = 0


class SessionGenManager:
    """In-memory tracker for a session-generation flow.

    One instance is created per register() call. When ``set_owner`` is used
    (clones), start/get only accept that owner. When owner is unset (main
    bot), every user_id gets an independent state keyed by that user.
    """

    def __init__(self, api_id: int, api_hash: str, ttl: float = DEFAULT_TTL) -> None:
        self._api_id = int(api_id)
        self._api_hash = str(api_hash or "")
        self._ttl = float(ttl)
        self._states: Dict[int, SessionGenState] = {}
        self._owner_id: int = 0

    def set_owner(self, owner_id: int) -> None:
        self._owner_id = int(owner_id or 0)

    @property
    def owner_id(self) -> int:
        return self._owner_id

    def start(self, user_id: int) -> SessionGenState:
        """Reset any prior state for user_id and return a fresh phone-stage state."""
        uid = int(user_id)
        if self._owner_id and uid != self._owner_id:
            return SessionGenState()
        old = self._states.get(uid)
        if old is not None:
            self._safe_disconnect(old.client)
            _ACTIVE_USERS.discard(uid)
        st = SessionGenState(
            stage=STAGE_PHONE,
            updated=time.monotonic(),
            owner_id=uid,
        )
        self._states[uid] = st
        _ACTIVE_USERS.add(uid)
        return st

    def get(self, user_id: int) -> Optional[SessionGenState]:
        uid = int(user_id)
        if self._owner_id and uid != self._owner_id:
            return None
        return self._states.get(uid)

    def is_active(self, user_id: int) -> bool:
        st = self.get(user_id)
        return bool(st and st.stage in (STAGE_PHONE, STAGE_OTP, STAGE_PASSWORD))

    def touch(self, user_id: int) -> None:
        st = self.get(user_id)
        if st is not None:
            st.updated = time.monotonic()

    async def drop(self, user_id: int) -> None:
        uid = int(user_id)
        st = self._states.pop(uid, None)
        _ACTIVE_USERS.discard(uid)
        if st is None:
            return
        self._safe_disconnect(st.client)

    def expire_stale(self) -> list:
        """Drop every state whose ``updated`` is older than TTL. Returns the dropped user_ids."""
        if self._ttl <= 0:
            return []
        now = time.monotonic()
        dropped: list = []
        for uid, st in list(self._states.items()):
            if now - st.updated > self._ttl:
                self._safe_disconnect(st.client)
                self._states.pop(uid, None)
                _ACTIVE_USERS.discard(uid)
                dropped.append(uid)
        return dropped

    def _safe_disconnect(self, client: Optional[Client]) -> None:
        if client is None:
            return
        try:
            if client.is_connected:



                pass
        except Exception:
            pass









def _normalize_phone(raw: str) -> Optional[str]:
    if raw is None:
        return None
    phone = str(raw).strip().replace(" ", "")
    if not phone:
        return None
    if not phone.startswith("+"):
        phone = "+" + phone
    if len(phone) < 8 or len(phone) > 16:
        return None
    if not phone[1:].isdigit():
        return None
    return phone


async def start_phone(
    manager: SessionGenManager,
    user_id: int,
    raw_phone: str,
) -> Tuple[str, Any]:
    """Validate phone, build client, send_code. Returns (status, payload)."""
    st = manager.get(user_id)
    if st is None or st.stage != STAGE_PHONE:
        return ERR_NEED_ACTIVE, None
    phone = _normalize_phone(raw_phone)
    if not phone:
        return ERR_INVALID_PHONE, None
    client = Client(
        f"sess_{user_id}_{int(time.time() * 1000)}",
        api_id=manager._api_id,
        api_hash=manager._api_hash,
        in_memory=True,
    )
    try:
        await client.connect()
    except Exception:
        try:
            await client.disconnect()
        except Exception:
            pass
        return ERR_SEND_FAILED, None
    try:
        sent = await client.send_code(phone)
    except PhoneNumberInvalid:
        try:
            await client.disconnect()
        except Exception:
            pass
        return ERR_INVALID_PHONE, None
    except Exception:
        try:
            await client.disconnect()
        except Exception:
            pass
        return ERR_SEND_FAILED, None
    st.client = client
    st.phone = phone
    st.code_hash = sent.phone_code_hash
    st.stage = STAGE_OTP
    manager.touch(user_id)
    return OK, sent


async def submit_otp(
    manager: SessionGenManager,
    user_id: int,
    code: str,
) -> Tuple[str, Any]:
    st = manager.get(user_id)
    if st is None or st.stage != STAGE_OTP or st.client is None:
        return ERR_NEED_ACTIVE, None
    code_clean = "".join((code or "").split())
    if not code_clean or not code_clean.isdigit():
        return ERR_INVALID_CODE, None
    try:
        await st.client.sign_in(st.phone, st.code_hash, phone_code=code_clean)
    except SessionPasswordNeeded:
        st.stage = STAGE_PASSWORD
        manager.touch(user_id)
        return PASSWORD_NEEDED, None
    except PhoneCodeInvalid:
        manager.touch(user_id)
        return ERR_INVALID_CODE, None
    except Exception:
        await _drop_state(manager, user_id)
        return ERR_SIGNIN_FAILED, None

    return await _export_and_drop(manager, user_id)


async def submit_password(
    manager: SessionGenManager,
    user_id: int,
    password: str,
) -> Tuple[str, Any]:
    st = manager.get(user_id)
    if st is None or st.stage != STAGE_PASSWORD or st.client is None:
        return ERR_NEED_ACTIVE, None
    pw = (password or "")
    if not pw:
        return ERR_BAD_PASSWORD, None
    try:
        await st.client.check_password(pw)
    except SessionPasswordNeeded:


        await _drop_state(manager, user_id)
        return ERR_BAD_PASSWORD, None
    except Exception:
        await _drop_state(manager, user_id)
        return ERR_SIGNIN_FAILED, None
    return await _export_and_drop(manager, user_id)


async def _export_and_drop(manager: SessionGenManager, user_id: int) -> Tuple[str, Any]:
    st = manager.get(user_id)
    if st is None or st.client is None:
        return ERR_NEED_ACTIVE, None
    try:
        sess = await st.client.export_session_string()
    except Exception:
        await _drop_state(manager, user_id)
        return ERR_SIGNIN_FAILED, None
    await _drop_state(manager, user_id)
    return OK, str(sess or "")


async def _drop_state(manager: SessionGenManager, user_id: int) -> None:
    await manager.drop(user_id)
