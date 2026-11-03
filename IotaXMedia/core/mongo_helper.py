# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
mongo_helper — utilities to build an AsyncIOMotorDatabase from a raw URI.

The parent process already has the main ``Iota`` database (see
``IotaXMedia.core.mongo``). Clone children that opted into their own MongoDB
URI (via ``/setmongodb``) call ``build_mongo_for_uri`` to get their own
database handle. Clones without their own URI simply use the main one.
"""
from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient


async def build_mongo_for_uri(uri: str, db_name: Optional[str] = None) -> "AsyncIOMotorDatabase":  # type: ignore[name-defined]
    """Connect to ``uri`` and return the database handle.

    Pulls the database name from the URI path (``/foo`` -> ``foo``);
    falls back to ``Iota`` (the shared one) for parity with the parent.
    Raises if the URI is invalid or unreachable within ~12s.
    """
    uri = (uri or "").strip()
    if not uri or "<password>" in uri or "<db_password>" in uri:
        raise ValueError("invalid MongoDB URI")

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=12000)

    await client.admin.command("ping")

    if not db_name:

        path = uri.split("@")[-1].split("?")[0]

        name = path.lstrip("/") or "Iota"
        db_name = name

    return client[db_name]
