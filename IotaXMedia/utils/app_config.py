# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any, Dict

from IotaXMedia import app
from IotaXMedia.utils.cache import TTLCache

_config_cache = TTLCache(maxsize=8, ttl=3600)
_app_config: Dict[str, Any] = {}


async def get_app_config(force: bool = False) -> Dict[str, Any]:
    """Fetch Telegram server-side app config (feature flags) via MTProto.

    Cached 1h. Returns {} on any failure so callers can fall back to config.
    """
    global _app_config
    if not force:
        cached = _config_cache.get("app_config")
        if cached is not None:
            return cached
    try:
        result = await app.invoke("help.getAppConfig", hash=0)
        data = getattr(result, "config", None)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    _app_config = data or {}
    _config_cache.set("app_config", _app_config)
    return _app_config
