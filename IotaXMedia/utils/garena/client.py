# Authored By Iota Coders (Garena protocol client for Free Fire player lookup)
# SPDX-License-Identifier: MIT
"""
Garena Free Fire player-info client.

This client talks to the same Garena backend that the official Free Fire
game/site uses to resolve a player's public profile by UID:

    1. ``oauth/guest/token/grant``  →  guest access_token + open_id
    2. ``MajorLogin``                →  session bearer token + game server url
    3. ``/GetPlayerPersonalShow``    →  AccountPersonalShow protobuf payload

The wire format is Garena's own AES-CBC(protobuf) envelope.  Region guest
accounts are cached for ``TOKEN_TTL`` seconds to avoid hammering the login
queue.
"""
from __future__ import annotations

import asyncio
import base64
import json
import threading
import time
import os
from typing import Dict, Optional, Tuple

import httpx
from google.protobuf import json_format

from IotaXMedia.logging import LOGGER
from IotaXMedia.utils.garena import (
    AccountPersonalShow_pb2,
    FreeFire_pb2,
    main_pb2,
)
from Crypto.Cipher import AES

logger = LOGGER(__name__)




_MAIN_KEY = base64.b64decode("WWcmdGMlREV1aDYlWmNeOA==")
_MAIN_IV = base64.b64decode("Nm95WkRyMjJFM3ljaGpNJQ==")
_RELEASE_VERSION = "OB54"
_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
_CLIENT_SECRET = os.getenv("GARENA_CLIENT_SECRET", "")
_CLIENT_ID = "100067"
_TOKEN_URL = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
_TOKEN_TTL = 6 * 60 * 60


_ACCOUNTS: Dict[str, str] = {
    "IND": "uid=3692279677&password=473AFFEF67F708CBB0962A958BB2809DA0843EA41BDB70D738FD9527EA04B27B",
    "BR": "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649",
    "US": "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649",
    "SAC": "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649",
    "NA": "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649",
    "EUROPE": "uid=3692292847&password=FC22F6812C850FF7D8DB8C5474A106B6FE22CB10C0A6673837216A32675E5649",
    "VN": "uid=3686689562&password=AD9C4A2B51A749481913F72A36F68A9F231520E9AC29B244DB47A64FD7353A12",
    "ID": "uid=3692307512&password=4AA06E1DB3F998ABDBDA74578D26B0C84700EC5C079751E7C8F1626048DDBCAE",
    "TH": "uid=3692333198&password=0ED64C5A89E09B8BE538829B0304FE5F5F7EA3BBE645A341C73ECA49143D2211",
    "TW": "uid=3692312456&password=1A062FD700DA8F826AF84A37EE2B62121B79516AF71666949C72FFF42D1C554A",
    "SG": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
    "BD": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
    "ME": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
    "PK": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
    "CIS": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
    "RU": "uid=3692265171&password=A2A5E3C252A35B2BB30698BD1469A759417A68A069CF6980ED959EB01D352E28",
}

SUPPORTED_REGIONS = set(_ACCOUNTS.keys())
REGION_ALIASES = {"EU": "EUROPE"}


_sessions: Dict[str, Dict] = {}
_sessions_lock = threading.RLock()





def _pad(data: bytes) -> bytes:
    pad_len = AES.block_size - (len(data) % AES.block_size)
    return data + bytes([pad_len] * pad_len)


def _encrypt(plaintext: bytes) -> bytes:
    cipher = AES.new(_MAIN_KEY, AES.MODE_CBC, _MAIN_IV)
    return cipher.encrypt(_pad(plaintext))


async def _json_to_proto(json_str: str, proto_message) -> bytes:
    json_format.ParseDict(json.loads(json_str), proto_message)
    return proto_message.SerializeToString()


def _decode_proto(data: bytes, message_type) -> object:
    instance = message_type()
    instance.ParseFromString(data)
    return instance





async def _grant_token(account: str) -> Tuple[Optional[str], Optional[str]]:
    """Get a guest access_token + open_id for a region account."""
    payload = (
        account
        + "&response_type=token&client_type=2&client_secret="
        + _CLIENT_SECRET
        + "&client_id="
        + _CLIENT_ID
    )
    headers = {
        "User-Agent": _USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        "Connection": "Keep-Alive",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(_TOKEN_URL, data=payload, headers=headers)
        data = resp.json()
    return data.get("access_token"), data.get("open_id")


async def _major_login(token: str, open_id: str) -> Dict:
    """MajorLogin → returns session dict with token + server_url."""
    body = json.dumps(
        {
            "open_id": open_id,
            "open_id_type": "4",
            "login_token": token,
            "orign_platform_type": "4",
        }
    )
    payload = _encrypt(await _json_to_proto(body, FreeFire_pb2.LoginReq()))
    headers = {
        "User-Agent": _USER_AGENT,
        "Content-Type": "application/octet-stream",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": _RELEASE_VERSION,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(_LOGIN_URL, data=payload, headers=headers)
        msg = _decode_proto(resp.content, FreeFire_pb2.LoginRes)
    data = json.loads(json_format.MessageToJson(msg))
    return data


async def _get_session(region: str) -> Tuple[str, str]:
    """Return (bearer_token, server_url) for a region, cached + lazy."""
    region = _normalize_region(region)
    now = time.time()
    with _sessions_lock:
        cached = _sessions.get(region)
        if cached and now < cached.get("expires_at", 0):
            return cached["token"], cached["server"]


    account = _ACCOUNTS.get(region, _ACCOUNTS["SG"])
    last_err = None
    for attempt in range(6):
        try:
            token, open_id = await _grant_token(account)
            if not token or not open_id:
                raise RuntimeError("guest grant returned no token")
            login = await _major_login(token, open_id)
            session_token = login.get("token")
            if not session_token:
                raise RuntimeError("MajorLogin returned no session token")
            server = login.get("serverUrl") or ""
            if server and not server.startswith(("http://", "https://")):
                server = "https://" + server
            if not server:
                raise RuntimeError("MajorLogin returned no server url")
            with _sessions_lock:
                _sessions[region] = {
                    "token": f"Bearer {session_token}",
                    "server": server,
                    "expires_at": now + _TOKEN_TTL,
                }
            return _sessions[region]["token"], server
        except Exception as e:  # noqa: BLE001
            last_err = e
            await asyncio.sleep(2 + attempt * 2)

    raise RuntimeError(
        f"Failed to acquire Garena session for region {region}: {last_err}"
    )


async def prewarm_sessions(regions=None):
    """Warm bearer sessions in the background so first lookup is fast."""
    targets = regions or list(SUPPORTED_REGIONS)
    for region in targets:
        try:
            await _get_session(region)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"prewarm region {region} failed: {e}")


async def _session_janitor():
    """Periodically refresh expiring sessions."""
    while True:
        await asyncio.sleep(_TOKEN_TTL // 2)
        for region in list(_sessions.keys()):
            with _sessions_lock:
                cached = _sessions.get(region)
                if cached and time.time() > cached.get("expires_at", 0) - 300:
                    _sessions.pop(region, None)
                    logger.debug(f"refreshing session for region {region}")
        await prewarm_sessions(list(_sessions.keys()) or list(SUPPORTED_REGIONS))


def start_background_tasks():
    """Idempotent start of background session maintenance."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    if not getattr(start_background_tasks, "_started", False):
        start_background_tasks._started = True
        asyncio.get_running_loop().create_task(prewarm_sessions())
        asyncio.get_running_loop().create_task(_session_janitor())


def _normalize_region(region: str) -> str:
    value = str(region or "").strip().upper()
    value = REGION_ALIASES.get(value, value)
    if value not in SUPPORTED_REGIONS:
        raise ValueError(f"Unsupported region: {value or 'missing'}")
    return value





async def fetch_player_info(uid, region: Optional[str] = None):
    """Fetch AccountPersonalShow payload for a UID.

    If region is omitted, probes gateway clusters (IND, SG, BR, ID, VN, TH, TW).
    Returns the parsed JSON dict.
    """
    uid = str(uid).strip()

    if region:
        safe_region = _normalize_region(region)
        try:
            return await _fetch_region(uid, safe_region)
        except Exception as e:
            logger.debug(f"ffinfo region {safe_region} failed: {e}")
            raise ValueError(f"Player not found for UID '{uid}' in region {safe_region}.")


    gateways = ["IND", "SG", "BR", "ID", "VN", "TH", "TW"]
    for reg in gateways:
        try:
            data = await _fetch_region(uid, reg)
            basic = data.get("basicInfo") or {}
            if basic.get("nickname"):
                return data
        except Exception:
            continue
    raise ValueError(f"Player account not found for UID '{uid}'.")


async def _fetch_region(uid: str, region: str) -> Dict:
    token, server = await _get_session(region)
    if not server:
        raise RuntimeError(f"No game server for region {region}")

    payload = await _json_to_proto(
        json.dumps({"a": uid, "b": "7"}), main_pb2.GetPlayerPersonalShow()
    )
    body = _encrypt(payload)
    headers = {
        "User-Agent": _USER_AGENT,
        "Content-Type": "application/octet-stream",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Expect": "100-continue",
        "Authorization": token,
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": _RELEASE_VERSION,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(server + "/GetPlayerPersonalShow", data=body, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Garena server returned HTTP {resp.status_code}")
        msg = _decode_proto(resp.content, AccountPersonalShow_pb2.AccountPersonalShowInfo)
    return json.loads(json_format.MessageToJson(msg))


async def check_banned(uid) -> Dict:
    """Free Fire account ban status via Garena's public antihack API."""
    url = "https://ff.garena.com/api/antihack/check_banned"
    params = {"lang": "en", "uid": str(uid)}
    headers = {
        "User-Agent": _USER_AGENT,
        "X-Requested-With": "B6FksShzIgjfrYImLpTsadjS86sddhFH",
        "Referer": "https://ff.garena.com/en/support/",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
