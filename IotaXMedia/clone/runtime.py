# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Clone runtime — manages per-clone bots *in-process*.

Architecture
------------
* Parent bot (the real IotaXMusic bot) holds a single ``CloneManager``.
* For each clone, the manager builds a fresh module namespace (see
  ``runtime_inproc.CloneNamespace``) and runs the clone's full ``init()`` as an
  asyncio task in the SAME process — a true replica of the main bot (same
  commands, same music system), with clone customization applied per-clone.
* The parent keeps status in MongoDB; ``health_check`` revives any clone whose
  task died. A supervisor background task runs periodic health checks.
* Stopping a clone signals its shutdown event; the task's ``finally`` stops the
  clone's app + userbot cleanly.

This replaces the old subprocess-spawn system (``_CLONE_BOOTSTRAP_CODE`` /
``Popen``) completely.
"""
from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional

from IotaXMedia.logging import LOGGER

from .db import (
    get_clone,
    get_clone_by_id,
    get_all_clones,
    get_clones_by_owner,
    add_clone,
    update_clone,
    delete_clone_but_settings,
    set_clone_status,
)

logger = LOGGER(__name__)


class CloneManager:
    """Holds the in-process clone tasks and supervises them."""

    def __init__(self) -> None:

        self._clones: Dict[str, "InProcessClone"] = {}
        self._supervisor_task: Optional[asyncio.Task] = None
        self._started = False
        self._lock = asyncio.Lock()
        self._boot_lock = asyncio.Lock()

        self._crash: Dict[str, int] = {}
        self._last_start: Dict[str, float] = {}


    async def start_clone(self, token: str) -> bool:
        """Start a single clone by bot token. Idempotent."""
        token = token.strip()
        async with self._lock:
            existing = self._clones.get(token)
            if existing is not None and existing.is_running():
                return True
        async with self._boot_lock:


            async with self._lock:
                existing = self._clones.get(token)
                if existing is not None and existing.is_running():
                    return True
            from .runtime_inproc import InProcessClone

            clone = InProcessClone(token)
            ok = await clone.start()




            try:
                rec = await get_clone(token)
            except Exception:
                rec = None
            still_wanted = rec is not None and str(
                (rec.get("status") or "running")
            ) not in ("stopped", "deleted")
            if ok and not still_wanted:
                logger.info(
                    f"Clone {token[:10]}… record deleted/stopped during boot — "
                    "shutting it down."
                )
                try:
                    await clone.stop()
                except Exception:
                    pass
                return False
            if ok:
                self._clones[token] = clone
                self._last_start[token] = time.time()
                await set_clone_status(token, "running")
                return True
            await set_clone_status(token, "stopped", error="boot failed")
            return False

    async def stop_clone(self, token: str) -> bool:
        """Stop a clone's task. Returns False if not running."""
        token = token.strip()
        async with self._lock:
            clone = self._clones.pop(token, None)
        if clone is None:
            await set_clone_status(token, "stopped")
            return False
        if not clone.is_running():
            await set_clone_status(token, "stopped")
            return False
        try:
            await clone.stop()
            await set_clone_status(token, "stopped")
            return True
        except Exception as e:
            logger.error(f"stop_clone {token[:10]}… failed: {e}")
            await set_clone_status(token, "stopped", error=str(e))
            return False

    async def restart_clone(self, token: str) -> bool:
        await self.stop_clone(token)
        await asyncio.sleep(0.5)
        return await self.start_clone(token)

    async def remove_clone(self, token: str) -> bool:
        """Stop a clone AND remove its record from the parent DB."""
        await self.stop_clone(token)
        return await delete_clone_but_settings(token)


    def is_running(self, token: str) -> bool:
        clone = self._clones.get(token.strip())
        return bool(clone is not None and clone.is_running())

    async def get_running_count(self) -> int:
        return sum(1 for c in self._clones.values() if c.is_running())

    async def health_check(self) -> None:
        """Re-spawn any clones marked running but whose task died.

        Crash backoff: a clone that keeps dying is not respawned instantly —
        we wait ``min(300, 15 * crashes)`` seconds since its last start so a
        permanently-broken token does not spin in an infinite crash loop.
        """
        try:
            for clone in await get_all_clones():
                token = clone["_id"]
                status = clone.get("status")
                proc = self._clones.get(token)
                if status != "running":
                    continue
                if proc is not None and proc.is_running():

                    self._crash[token] = 0
                    continue

                crashes = self._crash.get(token, 0) + 1
                self._crash[token] = crashes
                self._clones.pop(token, None)
                last = self._last_start.get(token, 0.0)
                wait = min(300, 15 * crashes)
                elapsed = time.time() - last
                if elapsed < wait:
                    logger.warning(
                        f"Clone {clone.get('username') or token[:10]}… died "
                        f"({crashes}x); backing off {wait - int(elapsed)}s"
                    )
                    continue
                logger.warning(
                    f"Clone {clone.get('username') or token[:10]}… died, respawning"
                )
                await self.start_clone(token)
        except Exception as e:
            logger.error(f"health_check: {e}")

    async def start_supervisor(self) -> None:
        if self._started:
            return
        self._started = True

        async def loop():
            while True:
                try:
                    await self.health_check()
                except Exception as e:
                    logger.error(f"supervisor loop: {e}")
                await asyncio.sleep(60)

        self._supervisor_task = asyncio.create_task(loop())

    async def stop_supervisor(self) -> None:
        if self._supervisor_task:
            self._supervisor_task.cancel()
            try:
                await self._supervisor_task
            except (asyncio.CancelledError, Exception):
                pass
            self._supervisor_task = None
        self._started = False

    async def start_all_pending(self) -> None:
        """On parent boot — revive every persisted clone.

        A redeploy shuts the parent down, which marks in-memory clones
        "stopped"; without reviving those the clone bot would silently
        disappear after every deploy. Since deleting a clone removes its
        record entirely (there is no separate "deleted" status), reviving
        every record here is safe and keeps clones alive across restarts.
        """
        try:
            for clone in await get_all_clones():
                token = clone["_id"]
                await self.start_clone(token)
        except Exception as e:
            logger.error(f"start_all_pending: {e}")

    async def shutdown(self) -> None:
        """Stop all running clones when the parent shuts down."""
        await self.stop_supervisor()
        tokens = list(self._clones.keys())
        await asyncio.gather(*(self.stop_clone(t) for t in tokens), return_exceptions=True)



CloneManagerInstance: Optional[CloneManager] = None


def get_clone_manager() -> CloneManager:
    global CloneManagerInstance
    if CloneManagerInstance is None:
        CloneManagerInstance = CloneManager()
    return CloneManagerInstance


async def get_clone_by_id_or_token(token_or_id: str) -> Optional[dict]:
    if not token_or_id:
        return None
    from .db import get_clone

    doc = await get_clone(token_or_id)
    if doc:
        return doc

    try:
        return await get_clone_by_id(int(token_or_id))
    except (TypeError, ValueError):
        return None



async def list_my_clones(owner_id: int) -> List[dict]:
    return await get_clones_by_owner(int(owner_id))


async def total_clones() -> int:
    from .db import count_clones

    return await count_clones()
