# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Git self-update helpers. GitPython is optional — import never fatal."""
from __future__ import annotations

import asyncio
import shlex
from typing import Tuple

try:
    from git import Repo  # noqa: F401
    from git.exc import GitCommandError, InvalidGitRepositoryError  # noqa: F401
except ImportError:
    Repo = None  # type: ignore
    GitCommandError = OSError  # type: ignore
    InvalidGitRepositoryError = OSError  # type: ignore

try:
    import config  # noqa: F401
except Exception:
    config = None  # type: ignore

from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.get_event_loop().run_until_complete(install_requirements())


def git():
    """Best-effort self-update from the upstream repo. Never fatal: the bot
    must keep running even when there is no git repo, no network, or the
    upstream remote does not exist yet."""
    LOGGER(__name__).info("Git self-update disabled for local development.")
    return
