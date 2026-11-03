# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import os
from ..logging import LOGGER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



if os.environ.get("RENDER", "").lower() in ("1", "true", "yes"):
    BASE_DIR = os.path.join("/tmp", "IotaXMedia")

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
COUPLE_DIR = os.path.join(BASE_DIR, "couples")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
BACKUP_DIR = os.path.join(BASE_DIR, "IotaXMediaBackup")

def StorageManager():

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(COUPLE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    LOGGER(__name__).info("Directories Updated.")
