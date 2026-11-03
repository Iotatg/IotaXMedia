# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import aiohttp
from pyrogram.errors import FloodWait, RetryAfter, TimedOut

logger = logging.getLogger(__name__)

T = TypeVar("T")


_TRANSIENT = (TimedOut, aiohttp.ClientError, asyncio.TimeoutError)


async def tg_call(
    coro_factory: Callable[[], Awaitable[T]],
    *,
    retries: int = 5,
    base: float = 1.0,
    max_wait: float = 30.0,
) -> T:
    """Run an awaitable with exponential backoff + exact FloodWait/RetryAfter handling.

    Usage:
        result = await tg_call(lambda: youtube.search(query))
        # or decorate:  @retry_tg()
    """
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await coro_factory()
        except FloodWait as e:
            wait = float(getattr(e, "value", 0) or 0)
            logger.warning("FloodWait %ss (attempt %d/%d)", wait, attempt, retries)
            await asyncio.sleep(min(wait, 60.0))
        except RetryAfter as e:
            wait = float(getattr(e, "value", 0) or 0)
            logger.warning("RetryAfter %ss (attempt %d/%d)", wait, attempt, retries)
            await asyncio.sleep(min(wait, 60.0))
        except _TRANSIENT as e:
            last = e
            wait = min(base * (2 ** (attempt - 1)), max_wait)
            logger.warning(
                "Transient %s (attempt %d/%d) retry in %.1fs",
                type(e).__name__,
                attempt,
                retries,
                wait,
            )
            await asyncio.sleep(wait)
    if last:
        raise last
    raise RuntimeError("tg_call exhausted retries without a captured exception")


def retry_tg(retries: int = 5, base: float = 1.0, max_wait: float = 30.0):
    """Decorator: apply tg_call retry/backoff to an async function."""

    def deco(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs):
            return await tg_call(
                lambda: func(*args, **kwargs),
                retries=retries,
                base=base,
                max_wait=max_wait,
            )

        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        return wrapper

    return deco
