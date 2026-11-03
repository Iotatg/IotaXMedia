# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT






import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())




try:
    import pyrogram.utils as _pu

    if getattr(_pu, "MIN_CHANNEL_ID", 0) > -100999999999999:
        _pu.MIN_CHANNEL_ID = -100999999999999
    if getattr(_pu, "MAX_USER_ID", 0) < 999999999999:
        _pu.MAX_USER_ID = 999999999999
    del _pu
except Exception:
    pass



import pyrogram as _pyro

if not hasattr(_pyro, "crypto_executor"):
    from concurrent.futures.thread import ThreadPoolExecutor

    _pyro.crypto_executor = ThreadPoolExecutor(1, thread_name_prefix="CryptoWorker")
del _pyro





import IotaXMedia.pyrogram_compat  # noqa: F401

from IotaXMedia.core.bot import MusicBotClient
from IotaXMedia.core.dir import StorageManager
from IotaXMedia.core.git import git
from IotaXMedia.core.userbot import Userbot
from IotaXMedia.misc import dbb, heroku

from .logging import LOGGER

StorageManager()
git()
dbb()
heroku()

app = MusicBotClient()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
JioSaavn = JioSaavnAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
