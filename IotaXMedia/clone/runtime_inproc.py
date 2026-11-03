# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
In-process clone runtime.

Replaces the old subprocess-spawn clone system (``_CLONE_BOOTSTRAP_CODE`` /
``Popen``) with a true in-process multi-client architecture: each clone bot is a
full replica of the main bot, run as an asyncio task in the SAME process.

Isolation
---------
A child process gets isolation because every module import happens in fresh
process memory. To replicate that in-process we re-execute the ``config`` module
and the whole ``IotaXMedia`` package into a *fresh module tree* (same module
names, fresh objects) while the clone boots. During that window ``sys.modules``
is temporarily swapped so ``import config`` and ``from IotaXMedia import app``
inside the re-imported modules resolve to the clone's own objects — exactly like
the child process, minus the process boundary.

The swap is released once the clone's plugins + clone handlers are registered
(the point where no more ``IotaXMedia.*`` imports happen during boot). Handler
closures keep the fresh module tree alive; a later global lazy import that
captures ``app``/``config`` would bind the main bot's objects instead, so boot is
serialized (one clone at a time) to keep windows from overlapping.
"""
from __future__ import annotations

import asyncio
import builtins
import contextvars
import os
import sys
import time
import traceback
import types
from typing import Any, Dict, Optional

from IotaXMedia.logging import LOGGER

logger = LOGGER(__name__)

_PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_PKG_DIR)


def _is_scoped(name: str) -> bool:
    return name == "config" or name == "IotaXMedia" or name.startswith("IotaXMedia.")











_CLONE_CTX: "contextvars.ContextVar[Optional[str]]" = contextvars.ContextVar(
    "iotax_clone_token", default=None
)
_CLONE_TREES: Dict[str, Dict[str, types.ModuleType]] = {}





_WINDOW_SAVED: Optional[Dict[str, types.ModuleType]] = None
_ORIG_IMPORT = builtins.__import__


def _clone_import(
    name: str,
    globals=None,
    locals=None,
    fromlist=(),
    level: int = 0,
) -> Any:
    if level == 0 and (name == "config" or name.startswith("IotaXMedia")):
        token = _CLONE_CTX.get()
        if token is not None:
            tree = _CLONE_TREES.get(token)
            if tree is not None:
                if fromlist:
                    mod = tree.get(name)
                    if mod is not None:
                        return mod
                else:
                    top = name.split(".", 1)[0]
                    mod = tree.get(top)
                    if mod is not None:
                        return mod
        elif _WINDOW_SAVED is not None:


            if fromlist:
                mod = _WINDOW_SAVED.get(name)
                if mod is not None:
                    return mod
            else:
                top = name.split(".", 1)[0]
                mod = _WINDOW_SAVED.get(top)
                if mod is not None:
                    return mod
    return _ORIG_IMPORT(name, globals, locals, fromlist, level)


if __import__ is not _clone_import:
    builtins.__import__ = _clone_import


class CloneNamespace:
    """Builds a fresh ``config`` + ``IotaXMedia`` module tree for one clone.

    ``begin()`` saves and evicts the global ``config``/``IotaXMedia.*`` modules
    and presets ``CLONE_MODE``/``CLONE_TOKEN`` env; imports made inside the
    window then produce fresh modules with the clone's token. ``end()`` restores
    the global modules exactly as they were.
    """

    def __init__(self, token: str, root: str = _REPO_ROOT) -> None:
        self.token = token.strip()
        self.root = root
        self._saved: Dict[str, Optional[types.ModuleType]] = {}
        self._env: Dict[str, Optional[str]] = {}
        self.active = False

    def begin(self) -> None:
        for name in list(sys.modules):
            if _is_scoped(name):
                self._saved[name] = sys.modules.pop(name)
        self._env = {
            k: os.environ.get(k)
            for k in ("CLONE_MODE", "CLONE_TOKEN", "BOT_TOKEN")
        }
        os.environ["CLONE_MODE"] = "1"
        os.environ["CLONE_TOKEN"] = self.token
        os.environ["BOT_TOKEN"] = self.token
        global _WINDOW_SAVED
        _WINDOW_SAVED = {
            n: m for n, m in self._saved.items() if m is not None
        }
        self.active = True

    def end(self) -> None:
        for name in list(sys.modules):
            if _is_scoped(name):
                sys.modules.pop(name, None)
        for name, mod in self._saved.items():
            if mod is not None:
                sys.modules[name] = mod
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        global _WINDOW_SAVED
        _WINDOW_SAVED = None
        self.active = False

    def import_fresh(self, name: str) -> types.ModuleType:
        if not self.active:
            raise RuntimeError("CloneNamespace not active")
        return __import__(name, globals(), locals(), [], 0)

    def exec_main_module(self) -> types.ModuleType:
        """Exec ``IotaXMedia/__main__.py`` into a fresh namespace and return it.

        Exec'd directly (not imported under ``IotaXMedia.__main__``) so it works
        regardless of how the host process was launched.
        """
        path = os.path.join(_PKG_DIR, "__main__.py")
        mod = types.ModuleType("IotaXMedia.__main__")
        mod.__file__ = path
        mod.__package__ = "IotaXMedia"
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        exec(compile(src, path, "exec"), mod.__dict__)
        return mod


class InProcessClone:
    """One clone bot running as an asyncio task in the main process."""

    def __init__(self, token: str) -> None:
        self.token = token.strip()
        self.ns = CloneNamespace(token)
        self.task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        self.plugins_ready = asyncio.Event()
        self.app: Any = None
        self.config_mod: Any = None
        self._boot_time: float = 0.0


    async def start(self) -> bool:
        if self.task is not None and not self.task.done():
            return True







        ctx_token = _CLONE_CTX.set(self.token)
        self.ns.begin()
        boot_ok = False
        try:
            self.config_mod = self.ns.import_fresh("config")
            iota = self.ns.import_fresh("IotaXMedia")
            self.app = iota.app
            main_mod = self.ns.exec_main_module()
            self._boot_time = time.time()
            self.task = asyncio.create_task(
                self._run(main_mod.init),
                name=f"clone_{self.token.split(':')[0]}",
            )

            if not await self._wait_ready(timeout=120):
                await self.stop()
                logger.error(
                    f"Clone {self.token[:12]}… failed to become ready "
                    "(check earlier clone logs)"
                )
                return False


            try:
                from IotaXMedia.clone.handlers.customization import CLONE_HANDLER_GROUP

                _disp = self.app.dispatcher
                _hmap = getattr(_disp, "handlers", None) or getattr(_disp, "groups", None)
                _ch = (_hmap or {}).get(CLONE_HANDLER_GROUP, [])
                logger.info(
                    f"[CLONE_BOOT] {self.token[:12]}… clone customization "
                    f"handlers={len(_ch)} registered — clone online"
                )
            except Exception as _e:
                logger.info(f"[CLONE_BOOT] marker log skipped: {_e}")
            boot_ok = True
        except Exception as exc:
            logger.error(
                f"Clone {self.token[:12]}… namespace boot failed: {exc}\n"
                + traceback.format_exc()
            )
            try:
                await self.stop()
            except Exception:
                pass
            return False
        finally:



            if boot_ok:
                self._capture_tree()
            else:
                _CLONE_TREES.pop(self.token, None)
            self.ns.end()
            _CLONE_CTX.reset(ctx_token)
        return True

    def _capture_tree(self) -> None:
        """Snapshot the fresh module tree so lazy imports inside this clone's
        task context resolve to its own objects after the window closes."""
        tree: Dict[str, types.ModuleType] = {}
        for name in list(sys.modules):
            if _is_scoped(name):
                tree[name] = sys.modules[name]
        if tree:
            _CLONE_TREES[self.token] = tree

    async def _run(self, init) -> None:
        token = _CLONE_CTX.set(self.token)
        try:
            await init(_shutdown_event=self.shutdown_event, _on_ready=self.plugins_ready)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error(
                f"Clone {self.token[:12]}… task crashed:\n" + traceback.format_exc()
            )
        finally:
            _CLONE_CTX.reset(token)

    async def _wait_ready(self, timeout: float) -> bool:
        deadline = time.time() + timeout
        while not self.plugins_ready.is_set():
            if self.task is not None and self.task.done():
                return False
            if time.time() > deadline:
                return False
            await asyncio.sleep(0.25)
        return True

    async def stop(self) -> None:
        self.shutdown_event.set()
        if self.task is None:
            _CLONE_TREES.pop(self.token, None)
            return




        try:
            if self.app is not None:
                await asyncio.wait_for(self.app.stop(), timeout=15)
        except Exception:
            pass


        if not self.task.done():
            self.task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(self.task), timeout=15)
        except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
            pass



        _CLONE_TREES.pop(self.token, None)

    def is_running(self) -> bool:
        return bool(self.task is not None and not self.task.done())
