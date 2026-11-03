# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Wrapper to run IotaXMedia package as a flat module from repo root.

Allows running `python wrapper.py` from the project root directory,
launching IotaXMedia regardless of nested package layout.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


sys.path.insert(0, str(REPO_ROOT))



from IotaXMedia.__main__ import init  # noqa: E402

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(init())
