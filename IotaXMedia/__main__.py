# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import importlib
import os
import time

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from IotaXMedia import LOGGER, app, userbot
from IotaXMedia.core.call import StreamController
from IotaXMedia.misc import sudo
from IotaXMedia.plugins import ALL_MODULES
from IotaXMedia.utils.database import get_banned_users, get_gbanned, VC_START_DIAG
from config import BANNED_USERS


async def init(_shutdown_event: "asyncio.Event | None" = None, _on_ready: "asyncio.Event | None" = None):
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).warning(
            "No assistant session set – VC playback is disabled. "
            "Add STRING_SESSION to .env to enable it. Bot is still running."
        )

    LOGGER("IotaXMedia").info(
        "YouTube downloader: yt-dlp (web/tv clients with deno JS solving, "
        "external API fallback)"
    )

    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception:
        pass

    is_clone = bool(getattr(config, "CLONE_MODE", False))

    await app.start()


    clone_runtime = None
    if is_clone:
        from IotaXMedia.clone.runtime_child import CloneRuntime, CloneConfig
        from IotaXMedia.clone.db import get_clone, get_all_clone_settings

        clone_runtime = CloneRuntime(config.BOT_TOKEN)
        clone_runtime.app = app
        clone_runtime._boot_time = time.time()







    if is_clone and clone_runtime is not None:
        try:
            from IotaXMedia.core.mongo import mongodb

            from IotaXMedia.clone.db import get_all_clone_settings, get_clone
            from IotaXMedia.clone.runtime_child import CloneConfig

            _rec = await get_clone(clone_runtime.token)
            if _rec:
                _settings = await get_all_clone_settings(clone_runtime.token)
                clone_runtime.config = CloneConfig(_rec, _settings)
                config.CLONE_CONFIG = clone_runtime.config
                LOGGER("IotaXMedia").info(
                    f"clone config preloaded for {str(clone_runtime.token)[:12]}… "
                    f"(has_music={clone_runtime.config.has_music()})"
                )
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"early clone config load failed: {e}")


    if (
        is_clone
        and clone_runtime is not None
        and clone_runtime.config is not None
        and not clone_runtime.config.has_music()
    ):
        import builtins as _bi

        _psc = getattr(_bi, "_IOTAX_PARENT_SC", None)
        _pdb = getattr(_bi, "_IOTAX_PARENT_DB", None)
        _pas = getattr(_bi, "_IOTAX_PARENT_ASSISTANTS", None)




        _bi._IOTAX_CLONE_BORROW = True
        if _pdb is not None:
            import IotaXMedia.misc as _misc

            _misc.db = _pdb
        if _psc is not None:
            import IotaXMedia.core.call as _cc

            _cc.StreamController = _psc
            LOGGER("IotaXMedia.core.userbot").info(
                "Clone has no STRING — borrowing MAIN bot's assistant for VC."
            )



            _pmisc2 = getattr(_bi, "_IOTAX_PARENT_MISC", None)
            if _pmisc2 is not None:
                setattr(_cc, "db", _pmisc2.db)
            import IotaXMedia.utils.database as _cdb0

            _pdbmod0 = getattr(_bi, "_IOTAX_PARENT_DBMOD", None)
            if _pdbmod0 is not None:
                for _attr in ("autoend", "counter"):
                    setattr(_cc, _attr, getattr(_pdbmod0, _attr, {}))
        if _pas is not None:
            import IotaXMedia.core.userbot as _ub

            _ub.assistants[:] = list(_pas)
            _paids = getattr(_bi, "_IOTAX_PARENT_ASSISTANTIDS", None)
            if _paids is not None:
                _ub.assistantids[:] = list(_paids)



        _pub = getattr(_bi, "_IOTAX_PARENT_USERBOT", None)
        if _pub is not None:



            from IotaXMedia import userbot as _inst

            for _n in ("one", "two", "three", "four", "five"):
                setattr(_inst, _n, getattr(_pub, _n))









        _pdbmod = getattr(_bi, "_IOTAX_PARENT_DBMOD", None)
        if _pdbmod is not None:
            import importlib as _il

            _cdb = _il.import_module("IotaXMedia.utils.database")
            if _cdb is not _pdbmod:
                for _name in (
                    "db", "active", "activevideo", "assistantdict", "autoend",
                    "count", "channelconnect", "langm", "loop", "maintenance",
                    "nonadmin", "pause", "playmode", "playtype", "skipmode",
                    "mute", "volume",
                ):
                    if hasattr(_pdbmod, _name):
                        setattr(_cdb, _name, getattr(_pdbmod, _name))
                LOGGER("IotaXMedia").info(
                    "Clone adopted MAIN bot's playback state "
                    "(queue/active-chat/assistant maps shared)."
                )







        _pcfg = getattr(_bi, "_IOTAX_PARENT_CONFIGMOD", None)
        if _pcfg is not None:
            import config as _ccfg

            for _name in ("autoclean", "BANNED_USERS"):
                _pv = getattr(_pcfg, _name, None)
                if _pv is not None:
                    setattr(_ccfg, _name, _pv)
        _pmisc = getattr(_bi, "_IOTAX_PARENT_MISC", None)
        if _pmisc is not None:
            import IotaXMedia.misc as _cmisc

            if getattr(_cmisc, "SUDOERS", None) is not None and hasattr(
                _pmisc, "SUDOERS"
            ):
                _cmisc.SUDOERS = _pmisc.SUDOERS
        _pdp = getattr(_bi, "_IOTAX_PARENT_DPPLAY", None)
        if _pdp is not None and hasattr(_pdp, "links"):
            import IotaXMedia.utils.decorators.play as _cdp

            _cdp.links = _pdp.links



    for route in ALL_MODULES:
        importlib.import_module("IotaXMedia.plugins" + route)

    LOGGER("IotaXMedia.plugins").info("Iota's modules loaded...")




    if is_clone and clone_runtime is not None and clone_runtime.config is None:
        try:
            record = await get_clone(clone_runtime.token)
            if record:
                settings = await get_all_clone_settings(clone_runtime.token)
                clone_runtime.config = CloneConfig(record, settings)
                config.CLONE_CONFIG = clone_runtime.config
                LOGGER("IotaXMedia").info(
                    f"clone config loaded for {str(clone_runtime.token)[:12]}…"
                )
            else:
                LOGGER("IotaXMedia").warning(
                    f"[CLONE] NO clone record found for token "
                    f"{str(clone_runtime.token)[:12]}… — handlers will use "
                    "defaults and owner-only commands stay restricted."
                )
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"clone config load failed: {e}")








    if is_clone and clone_runtime is not None:
        try:
            from IotaXMedia.clone.handlers import register_all as clone_register_all
            await clone_register_all(clone_runtime)
            LOGGER("IotaXMedia").info(
                f"[CLONE] clone handlers registered OK "
                f"(config={type(clone_runtime.config).__name__})"
            )
        except Exception:
            import traceback
            LOGGER("IotaXMedia").error(
                "Clone handlers FAILED to register:\n" + traceback.format_exc()
            )






    if not is_clone:
        try:
            from IotaXMedia.clone.handlers.customization import (
                register as reg_cust_main,
            )
            from IotaXMedia.clone.runtime_child import CloneConfig
            from IotaXMedia.clone.db import get_all_clone_settings
            from IotaXMedia.misc import SUDOERS





            try:
                _settings = await get_all_clone_settings(config.BOT_TOKEN or "main")
            except Exception:
                _settings = {}
            config.CLONE_CONFIG = CloneConfig(
                {
                    "_id": config.BOT_TOKEN or "main",
                    "owner_id": config.OWNER_ID,
                    "username": "",
                },
                _settings or {},
            )

            class _MainRuntime:
                app = app
                token = config.BOT_TOKEN or "main"
                config = config.CLONE_CONFIG

                def request_shutdown(self):
                    return None

            await reg_cust_main(_MainRuntime(), owner_filter=SUDOERS)
            from IotaXMedia.clone.handlers.session_gen import (
                register as reg_sess_main,
            )
            await reg_sess_main(_MainRuntime(), owner_filter=SUDOERS)
        except Exception as e:
            import traceback
            LOGGER("IotaXMedia").error(
                "Main-bot customization handlers FAILED to register:\n"
                + traceback.format_exc()
            )





    if _on_ready is not None:
        _on_ready.set()







    if is_clone:
        clone_session = (
            clone_runtime
            and clone_runtime.config
            and clone_runtime.config.string_session
        )
        if clone_session:
            try:
                from pyrogram import Client as _CloneUBClient

                clone_ub = _CloneUBClient(
                    name=f"clone_ub_{clone_runtime.config.bot_id}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=clone_session,
                    no_updates=True,
                    in_memory=True,
                )
                await clone_ub.start()
                from pytgcalls import PyTgCalls

                clone_runtime.userbot = clone_ub
                from IotaXMedia.core.call import StreamController as _clone_SC

                _ptc = PyTgCalls(clone_ub)
                await _ptc.start()
                _clone_SC.one = _ptc
                import IotaXMedia.core.userbot as _ub

                if 1 not in _ub.assistants:
                    _ub.assistants.append(1)
                    try:
                        _me = await clone_ub.get_me()
                        _ub.assistantids.append(_me.id)
                    except Exception:
                        pass



                from IotaXMedia import userbot as _ub_inst

                _ub_inst.one = clone_ub
                await _clone_SC.decorators()
                clone_runtime.call = _ptc
                LOGGER("IotaXMedia.core.userbot").info(
                    f"Clone {clone_runtime.config.username} userbot + PyTgCalls ready"
                )
            except Exception as e:
                VC_START_DIAG["userbot_error"] = str(e)
                LOGGER("IotaXMedia.core.userbot").error(
                    f"Clone userbot start failed (VC music disabled): {e}"
                )
                if clone_runtime.userbot is not None:
                    try:
                        await clone_runtime.userbot.stop()
                    except Exception:
                        pass
                    clone_runtime.userbot = None
        else:
            LOGGER("IotaXMedia.core.userbot").info(
                "Clone has no STRING session — borrowing MAIN bot's assistant "
                "for voice-chat music (set /setstring for an independent one)."
            )
    elif any([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]):
        try:
            await userbot.start()
        except Exception as e:
            VC_START_DIAG["userbot_error"] = str(e)
            LOGGER("IotaXMedia.core.userbot").error(
                f"Assistant userbot start failed (VC music disabled): {e}"
            )
        else:



            try:
                from IotaXMedia.plugins.tools.assistant_chat import register as _register_assistant_chat

                _register_assistant_chat()
            except Exception as e:
                LOGGER("IotaXMedia.plugins.tools.assistant_chat").warning(
                    f"assistant_chat register failed: {e}"
                )



            try:
                from IotaXMedia.plugins.tools.sticker_reply_assis import register as _register_sticker_assis

                _register_sticker_assis()
            except Exception as e:
                LOGGER("IotaXMedia.plugins.tools.sticker_reply_assis").warning(
                    f"sticker_reply_assis register failed: {e}"
                )
        try:
            await StreamController.start()





            import builtins as _bi
            from IotaXMedia.misc import db as _pdb
            from IotaXMedia.core.userbot import (
                assistants as _pas,
                assistantids as _paids,
            )
            from IotaXMedia import userbot as _pub

            _bi._IOTAX_PARENT_SC = StreamController
            _bi._IOTAX_PARENT_DB = _pdb
            _bi._IOTAX_PARENT_ASSISTANTS = _pas
            _bi._IOTAX_PARENT_ASSISTANTIDS = _paids
            _bi._IOTAX_PARENT_USERBOT = _pub




            import sys as _sys

            _bi._IOTAX_PARENT_DBMOD = _sys.modules.get("IotaXMedia.utils.database")
            _bi._IOTAX_PARENT_CONFIGMOD = _sys.modules.get("config")
            from IotaXMedia import misc as _pmisc

            _bi._IOTAX_PARENT_MISC = _pmisc
            import IotaXMedia.utils.decorators.play as _pdp

            _bi._IOTAX_PARENT_DPPLAY = _pdp
        except Exception as e:
            LOGGER("IotaXMedia.core.userbot").error(
                f"PyTgCalls start failed (VC music disabled): {e}"
            )
    else:
        LOGGER("IotaXMedia.core.userbot").info(
            "No STRING session — running text-only, VC music off."
        )

    if not is_clone:
        try:
            await StreamController.stream_call(
                "http://docs.evostream.com/sample_content/assets/sintel1m720p.mp4"
            )
        except NoActiveGroupCall:
            LOGGER("IotaXMedia").warning(
                "Log group voice chat is off (or LOGGER_ID unset) — continuing without VC health-check."
            )
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"Startup stream check skipped: {e}")

    try:
        if getattr(app, "username", None):
            config.BOT_USERNAME = app.username
    except Exception:
        pass



    if not is_clone:
        try:
            await StreamController.decorators()
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"StreamController decorators skipped: {e}")

    _stop_health = None
    _stop_yt_api = None
    if not is_clone:
        try:
            from IotaXMedia.utils.keep_alive import (
                start_health_server,
                stop_health_server,
                render_keepalive_job,
                local_keepalive_job,
            )
            await start_health_server()
            asyncio.create_task(render_keepalive_job(interval=300))
            asyncio.create_task(local_keepalive_job(interval=120))
            _stop_health = stop_health_server
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"Health/keep-alive not started: {e}")



        try:
            from IotaXMedia.utils.yt_api_server import launch_thread
            launch_thread()
            LOGGER("IotaXMedia").info(
                "yt-dlp download API server started (cookieless mediaconnect + deno)."
            )
        except Exception as e:
            LOGGER("IotaXMedia").warning(f"yt-dlp download API server not started: {e}")

    LOGGER("IotaXMedia").info(
        ("CLONE " if is_clone else "")
        + "Iota Music Robot Started Successfully..."
    )

    if not is_clone:
        try:
            from IotaXMedia.clone.runtime import get_clone_manager

            mgr = get_clone_manager()
            await mgr.start_all_pending()
            await mgr.start_supervisor()
            LOGGER("IotaXMedia.clone.runtime").info(
                "Clone manager: pending clones revived + supervisor running."
            )
        except Exception as e:
            LOGGER("IotaXMedia.clone.runtime").warning(
                f"Clone manager not started: {e}"
            )

    try:
        if _shutdown_event is not None:


            await _shutdown_event.wait()
        else:
            await idle()
    finally:
        if clone_runtime is not None:
            clone_runtime._shutting_down.set()
        try:
            if _stop_health:
                await _stop_health()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        if is_clone:
            if clone_runtime is not None and clone_runtime.userbot is not None:
                try:
                    await clone_runtime.userbot.stop()
                except Exception:
                    pass
        else:
            try:
                await userbot.stop()
            except Exception:
                pass

            try:
                from IotaXMedia.clone.runtime import get_clone_manager

                await get_clone_manager().shutdown()
            except Exception:
                pass
        LOGGER("IotaXMedia").info("Stopping bot ...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())