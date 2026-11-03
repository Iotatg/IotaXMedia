# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Clone customization commands — only the clone owner can run them."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pyrogram import filters
from pyrogram.types import Message

from .. import customization as cust
from ._common import CLONE_HANDLER_GROUP, get_clone_db
from IotaXMedia.logging import LOGGER

import config as _cfg




_CMD_HELP = {
    "setstart": (
        "sєᴛ ᴧ ᴄυsᴛσϻ /start ϻєᴅɪᴧ (ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ/ɢɪғ) ᴊσ ʀєᴘʟʏ ᴛσ ᴅєɢᴧ ᴛσ ʀєᴘʟʏ ᴋꝛєηє ᴘꝛ ᴛᴧɢ ꝛєᴘʟʏ.",
        "ᴜsᴧɢє: ᴋɪsɪ ᴘʜσᴛσ/ᴠɪᴅєσ/ɢɪғ ᴄσ ϻєssᴧɢє ᴘꝛ ꝛᴇᴘʟʏ ᴋꝛєηє /setstart ʟɪᴋʜєη.",
    ),
    "delstart": (
        "ꝛєsєᴛ /start ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ (ᴍυʟ ᴘʜσᴛσ ʜᴧᴛᴧηє).",
        "ᴜsᴧɢє: ʙᴧs /delstart ʟɪᴋʜєη.",
    ),
    "setstartmsg": (
        "sєᴛ ᴧ ᴄυsᴛσϻ /start ᴛєxᴛ ϻєssᴧɢє (ᴘʜσᴛσ ᴋє sᴧᴛʜ ϻєssᴧɢє).",
        "ᴜsᴧɢє: /setstartmsg <ᴛᴇxᴛ>",
    ),
    "delstartmsg": (
        "ꝛєsєᴛ /start ᴛєxᴛ ϻєssᴧɢє ᴛσ ᴅєғᴧυʟᴛ.",
        "ᴜsᴧɢє: ʙᴧs /delstartmsg ʟɪᴋʜєη.",
    ),
    "setpingpic": (
        "sєᴛ ᴧ ᴄυsᴛσϻ /ping ϻєᴅɪᴧ (ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ).",
        "ᴜsᴧɢє: ᴋɪsɪ ϻєᴅɪᴧ ᴄσ ꝛᴇᴘʟʏ ᴋꝛєηє /setpingpic ʟɪᴋʜєη.",
    ),
    "delpingpic": (
        "ꝛєsєᴛ /ping ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ.",
        "ᴜsᴧɢє: ʙᴧs /delpingpic ʟɪᴋʜєη.",
    ),
    "setstatspic": (
        "sєᴛ ᴧ ᴄυsᴛσϻ /stats ϻєᴅɪᴧ (ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ).",
        "ᴜsᴧɢє: ᴋɪsɪ ϻєᴅɪᴧ ᴄσ ꝛᴇᴘʟʏ ᴋꝛєηє /setstatspic ʟɪᴋʜєη.",
    ),
    "delstatspic": (
        "ꝛєsєᴛ /stats ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ.",
        "ᴜsᴧɢє: ʙᴧs /delstatspic ʟɪᴋʜєη.",
    ),
    "setchannel": (
        "sєᴛ ʏσυꝛ ᴄʟσηє'ѕ υᴘᴅᴧᴛє ᴄʜᴧηηєʟ ʟɪηᴋ (ꝛєᴅɪꝛєᴄᴛ ʟɪηᴋ).",
        "ᴜsᴧɢє: /setchannel <ᴛ.ϻє ʟɪηᴋ>",
    ),
    "setsupport": (
        "sєᴛ ʏσυꝛ ᴄʟσηє'ѕ sυᴘᴘσꝛᴛ ɢꝛσυᴘ ʟɪηᴋ.",
        "ᴜsᴧɢє: /setsupport <ᴛ.ϻє ʟɪηᴋ>",
    ),
    "setstring": (
        "sєᴛ ᴧ ᴄυsᴛσϻ ᴧssɪsᴛᴧηᴛ sᴛʀɪηɢ sᴇssɪᴏη ғσꝛ ᴠσɪᴄє ᴄʜᴧᴛ ϻυsɪᴄ.",
        "ᴜsᴧɢє: /setstring <ᴘʏꝛσɢꝛᴧϻ sᴛʀɪηɢ sᴇssɪᴏη>",
    ),
    "delstring": (
        "ꝛєϻσᴠє ᴧssɪsᴛᴧηᴛ sᴛʀɪηɢ sᴇssɪᴏη (ᴍυsɪᴄ ᴅɪsᴧʙʟє ʜσ ᴊᴧʏєɢᴧ).",
        "ᴜsᴧɢє: ʙᴧs /delstring ʟɪᴋʜєη.",
    ),
    "setmongodb": (
        "sᴛσꝛє ʏσυꝛ ᴄʟσηє'ѕ υsєꝛs/ᴄʜᴧᴛs/ᴄυsᴛσϻ sєᴛᴛɪηɢs ʏσυꝛ σᴡη ϻσηɢσᴅʙ ϻєη.",
        "ᴜsᴧɢє: /setmongodb <ϻσηɢσ ᴜʀɪ>",
    ),
    "delmongodb": (
        "ꝛєᴠєꝛᴛ ᴛσ sʜᴧꝛєᴅ ᴅᴧᴛᴧʙᴧsє (ᴍυʟ ϻσηɢσ).",
        "ᴜsᴧɢє: ʙᴧs /delmongodb ʟɪᴋʜєη.",
    ),
    "name": (
        "sєᴛ ʏσυꝛ ᴄʟσηє'ѕ ʙσᴛ ηᴧϻє (ᴅɪsᴘʟᴧʏ ηᴧϻє).",
        "ᴜsᴧɢє: /name <ηᴧϻє>",
    ),
    "setlogger": (
        "sєᴛ ᴛʜɪs ɢꝛσυᴘ/ᴄʜᴧηηєʟ ᴧs ʏσυꝛ ᴄʟσηє'ѕ ʟσɢ ᴄʜᴧᴛ (ᴧᴅᴅ ϻє ᴧs ᴧᴅϻɪη ғɪꝛsᴛ).",
        "ᴜsᴧɢє: ɪs ɢꝛσυᴘ/ᴄʜᴧηηєʟ ϻєη ʀєᴘʟʏ ᴋꝛєηє /setlogger ʟɪᴋʜєη.",
    ),
    "dellogger": (
        "ꝛєϻσᴠє ᴛʜє ʟσɢ ᴄʜᴧᴛ ᴧηᴅ ᴅɪsᴧʙʟє ᴧᴄᴛɪᴠɪᴛʏ ʟσɢs.",
        "ᴜsᴧɢє: ʙᴧs /dellogger ʟɪᴋʜєη.",
    ),
    "setchannelname": (
        "sєᴛ ᴄʜᴧηηєʟ ʙυᴛᴛση ηᴧϻє.",
        "ᴜsᴧɢє: /setchannelname <ηᴧϻє>",
    ),
    "setsupportname": (
        "sєᴛ sυᴘᴘσꝛᴛ ʙυᴛᴛση ηᴧϻє.",
        "ᴜsᴧɢє: /setsupportname <ηᴧϻє>",
    ),
    "setownername": (
        "sєᴛ σᴡηєꝛ ʙυᴛᴛση ηᴧϻє.",
        "ᴜsᴧɢє: /setownername <ηᴧϻє>",
    ),
    "addbtn": (
        "ᴧᴅᴅ ᴧ ᴄυsᴛσϻ /start ʙυᴛᴛση.",
        "ᴜsᴧɢє: /addbtn <ηᴧϻє> <ʟɪηᴋ>",
    ),
    "delbtn": (
        "ꝛєϻσᴠє ᴧ ᴄυsᴛσϻ /start ʙυᴛᴛση.",
        "ᴜsᴧɢє: /delbtn <ηᴧϻє>",
    ),
}


def _cmd_help(name: str) -> str:
    """What a clone command does + how to use it — shown when used with no args."""
    desc, usage = _CMD_HELP.get(name, ("", ""))
    return f"/{name} — {desc}\n\n{usage}"


def _set_cfg(runtime, name: str, value) -> None:
    """Update the clone config in memory so the display reflects immediately.

    In clone mode ``runtime.config`` IS ``config.CLONE_CONFIG`` (same object),
    so this keeps both in sync. On the main bot the runtime uses a lightweight
    ``_MainCfg`` and we additionally mirror into ``config.CLONE_CONFIG`` if it
    was loaded from the settings store.
    """
    try:
        setattr(runtime.config, name, value)
    except Exception:
        pass
    cc = getattr(_cfg, "CLONE_CONFIG", None)
    if cc is not None:
        try:
            setattr(cc, name, value)
        except Exception:
            pass

if TYPE_CHECKING:
    from ..runtime_child import CloneRuntime


_SUPPORT = "https://t.me/iotasupport"


class _MainCfg:
    """Placeholder config for the primary bot's customization commands.

    The clone handlers read ``cfg.chatbot_enabled`` / ``cfg.display_name`` and
    set them; for the main bot we just need a mutable object with those
    attributes so the same handlers work without a real clone config.
    """

    owner_id = 0
    chatbot_enabled = False
    display_name = None


async def register(runtime, owner_filter=None) -> None:
    app = runtime.app
    cfg = runtime.config






    if cfg is None:
        try:
            from ..db import get_clone, get_all_clone_settings
            from ..runtime_child import CloneConfig
            rec = await get_clone(runtime.token)
            if rec:
                settings = await get_all_clone_settings(runtime.token)
                cfg = CloneConfig(rec, settings)
                runtime.config = cfg
        except Exception as e:
            LOGGER(__name__).warning(f"clone config self-heal failed: {e}")







    owner_id = int(getattr(cfg, "owner_id", 0) or 0) if cfg else 0
    from IotaXMedia.misc import SUDOERS

    async def _check_owner(client, message: Message) -> bool:
        """Return True if the sender may customize this clone; reply + False otherwise."""
        user = message.from_user
        uid = user.id if user else None

        if uid and uid == owner_id:
            return True



        if uid:
            try:
                if await SUDOERS(client, message):
                    return True
            except Exception:
                pass
        await message.reply_text(
            "🚫 ʏσυ ᴅση'ᴛ σᴡη ᴛʜɪs ᴄʟσηє σꝛ ᴧꝛє ησᴛ ᴧυᴛʜσꝛɪᴢєᴅ ᴛσ ᴄυsᴛσϻɪᴢє ɪᴛ.\n"
            "ᴛʜє ᴄʟσηє σᴡηєꝛ ɴєєᴅs ᴛσ ꝛυη ᴛʜєsє ᴄσϻϻᴧηᴅs."
        )
        return False

    def _owner_only(func):
        async def _w(client, message: Message, *a, **k):
            if not await _check_owner(client, message):
                return
            try:
                return await func(client, message, *a, **k)
            except Exception as _e:


                LOGGER(__name__).error(
                    f"clone cmd /{func.__name__} failed: {_e}", exc_info=True
                )
                try:
                    await message.reply_text(f"⚠️ ᴇʀʀᴏʀ: <code>{_e}</code>")
                except Exception:
                    pass
        return _w


    @app.on_message(filters.command(["setstart", "setupic"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setstart(client, message: Message):
        extracted = await _extract_media(message)
        if not extracted:
            return await message.reply_text(_cmd_help("setstart"))
        media_type, fid = extracted
        stored = await cust.set_start_media(runtime.token, fid, media_type)
        _set_cfg(runtime, "start_media", stored)
        await message.reply_text("✅ /start ᴍᴇᴅɪᴀ sᴇᴛ.")

    @app.on_message(filters.command(["delstart", "delstartpic"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delstart(client, message: Message):
        await cust.del_start_media(runtime.token)
        _set_cfg(runtime, "start_media", None)
        await message.reply_text("✅ /start ᴍᴇᴅɪᴀ ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ.")


    @app.on_message(filters.command(["setstartmsg", "setstartmessage"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setstartmsg(client, message: Message):
        text = message.text.split(None, 1)
        if len(text) < 2:
            return await message.reply_text(_cmd_help("setstartmsg"))
        await cust.set_start_message(runtime.token, text[1])
        _set_cfg(runtime, "start_message", text[1])
        await message.reply_text("✅ /start ᴍᴇssᴀɢᴇ sᴇᴛ.")

    @app.on_message(filters.command(["delstartmsg", "delstartmessage"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delstartmsg(client, message: Message):
        await cust.del_start_message(runtime.token)
        _set_cfg(runtime, "start_message", None)
        await message.reply_text("✅ /start ᴍᴇssᴀɢᴇ ʀᴇsᴇᴛ.")


    @app.on_message(filters.command(["setpingpic", "setpingimg"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setpingpic(client, message: Message):
        extracted = await _extract_media(message)
        if not extracted:
            return await message.reply_text(_cmd_help("setpingpic"))
        media_type, fid = extracted
        stored = await cust.set_ping_media(runtime.token, fid, media_type)
        _set_cfg(runtime, "ping_media", stored)
        await message.reply_text("✅ /ping ᴍᴇᴅɪᴀ sᴇᴛ.")

    @app.on_message(filters.command(["delpingpic", "delpingimg"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delpingpic(client, message: Message):
        await cust.del_ping_media(runtime.token)
        _set_cfg(runtime, "ping_media", None)
        await message.reply_text("✅ /ping ᴍᴇᴅɪᴀ ʀᴇsᴇᴛ.")

    @app.on_message(filters.command(["setstatspic", "setstatsimg"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setstatspic(client, message: Message):
        extracted = await _extract_media(message)
        if not extracted:
            return await message.reply_text(_cmd_help("setstatspic"))
        media_type, fid = extracted
        stored = await cust.set_stats_media(runtime.token, fid, media_type)
        _set_cfg(runtime, "stats_media", stored)
        await message.reply_text("✅ /stats ᴍᴇᴅɪᴀ sᴇᴛ.")

    @app.on_message(filters.command(["delstatspic", "delstatsimg"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delstatspic(client, message: Message):
        await cust.del_stats_media(runtime.token)
        _set_cfg(runtime, "stats_media", None)
        await message.reply_text("✅ /stats ᴍᴇᴅɪᴀ ʀᴇsᴇᴛ.")


    @app.on_message(filters.command("setchannel"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setchannel(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setchannel"))
        link = parts[1].strip()
        if "t.me" not in link and "telegram.me" not in link:
            return await message.reply_text("ɢɪᴠᴇ ᴍᴇ ᴀ ᴠᴀʟɪᴅ ᴛ.ᴍᴇ ʟɪɴᴋ.")
        await cust.set_clone_channel(runtime.token, link)
        _set_cfg(runtime, "channel_link", link)
        await message.reply_text("✅ ʏᴏᴜʀ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ ʜᴀs ʙᴇᴇɴ sᴇᴛ.")

    @app.on_message(filters.command("setsupport"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setsupport(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setsupport"))
        link = parts[1].strip()
        if "t.me" not in link and "telegram.me" not in link:
            return await message.reply_text("ɢɪᴠᴇ ᴍᴇ ᴀ ᴠᴀʟɪᴅ ᴛ.ᴍᴇ ʟɪɴᴋ.")
        await cust.set_clone_support(runtime.token, link)
        _set_cfg(runtime, "support_link", link)
        await message.reply_text("✅ ʏᴏᴜʀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ʟɪɴᴋ ʜᴀs ʙᴇᴇɴ sᴇᴛ.")


    @app.on_message(filters.command(["setstring", "setsession"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setstring(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setstring"))
        session = parts[1].strip()
        if len(session) < 60:
            return await message.reply_text("❌ sᴇssɪᴏɴ sᴛʀɪɴɢ sᴇᴇᴍs ᴛᴏᴏ sʜᴏʀᴛ.")
        await cust.set_clone_string(runtime.token, session)
        await message.reply_text(
            "✅ sᴛʀɪɴɢ sᴀᴠᴇᴅ.\n"
            "♻️ ʏᴏᴜʀ ᴄʟᴏɴᴇ ᴡɪʟʟ ʀᴇsᴛᴀʀᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ɪɴ ~𝟷 ᴍɪɴᴜᴛᴇ — "
            "ɴᴏ ɴᴇᴇᴅ ᴛᴏ ʀᴜɴ /restart."
        )

        runtime.request_shutdown()

    @app.on_message(filters.command(["delstring", "delsession"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delstring(client, message: Message):
        await cust.del_clone_string(runtime.token)
        await message.reply_text("✅ sᴛʀɪɴɢ ʀᴇᴍᴏᴠᴇᴅ. ᴍᴜsɪᴄ ᴅɪsᴀʙʟᴇᴅ ɢᴀʏᴀ ᴀʙ.")
        runtime.request_shutdown()


    @app.on_message(filters.command(["setmongodb", "setmongo"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setmongo(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setmongodb"))



        return await message.reply_text(
            "⚠️ ᴘᴇʀ-ᴄʟᴏɴᴇ ᴍᴏɴɢᴏᴅʙ ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ʏᴇᴛ.\n"
            "ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ᴡɪʟʟ ᴄᴏɴᴛɪɴᴜᴇ ᴛᴏ ʙᴇ sᴀᴠᴇᴅ ɪɴ ᴛʜᴇ ᴍᴀɪɴ ᴅᴀᴛᴀʙᴀsᴇ.\n"
            "ɴᴏᴛʜɪɴɢ ᴡᴀs ᴄʜᴀɴɢᴇᴅ."
        )

    @app.on_message(filters.command(["delmongodb", "delmongo"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delmongo(client, message: Message):
        await cust.del_clone_mongo(runtime.token)
        await message.reply_text(
            "✅ ʀᴇᴠᴇʀᴛᴇᴅ ᴛᴏ ᴛʜᴇ sʜᴀʀᴇᴅ ᴅᴀᴛᴀʙᴀsᴇ. ʀᴜɴ /restart ᴛᴏ ᴀᴘᴘʟʏ."
        )


    @app.on_message(filters.command("chatbot"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _chatbot(client, message: Message):
        live = runtime.config or cfg
        current = bool(getattr(live, "chatbot_enabled", False))
        new = not current
        await cust.set_clone_chatbot(runtime.token, new)
        if live is not None:
            live.chatbot_enabled = new
        await message.reply_text(
            f"🤖 ᴄʜᴀᴛʙᴏᴛ: {'ᴇɴᴀʙʟᴇᴅ' if new else 'ᴅɪsᴀʙʟᴇᴅ'}"
        )


    @app.on_message(filters.command(["name", "setname", "botname"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setname(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("name"))
        name = parts[1].strip()[:32]
        await cust.set_clone_name(runtime.token, name)
        live = runtime.config or cfg
        if live is not None:
            live.display_name = name
        await message.reply_text(f"✅ ɴᴀᴍᴇ sᴇᴛ ᴛᴏ {name}.")


    @app.on_message(filters.command(["setlogger", "logger"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setlogger(client, message: Message):
        chat_id = None
        if message.reply_to_message:
            chat_id = message.reply_to_message.chat.id
        else:
            parts = message.text.split(None, 1)
            if len(parts) >= 2:
                chat_id = parts[1].strip().lstrip("@")
        if not chat_id:
            return await message.reply_text(_cmd_help("setlogger"))
        await cust.set_clone_logger(runtime.token, chat_id)
        _set_cfg(runtime, "log_chat", str(chat_id))
        await message.reply_text("✅ ʟσɢ ᴄʜᴧᴛ sєᴛ. (ᴧᴄᴛɪᴠɪᴛʏ ʟσɢ ᴄᴧᴘᴛυꝛє ᴄσϻɪηɢ sσση)")

    @app.on_message(filters.command(["dellogger"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _dellogger(client, message: Message):
        await cust.del_clone_logger(runtime.token)
        _set_cfg(runtime, "log_chat", None)
        await message.reply_text("✅ ʟσɢ ᴄʜᴧᴛ ꝛєϻσᴠєᴅ.")

    @app.on_message(filters.command("setchannelname"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setchannelname(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setchannelname"))
        name = parts[1].strip()[:32]
        await cust.set_clone_channel_name(runtime.token, name)
        _set_cfg(runtime, "channel_name", name)
        await message.reply_text("✅ ᴄʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ sᴇᴛ.")

    @app.on_message(filters.command("delchannelname"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delchannelname(client, message: Message):
        await cust.del_clone_channel_name(runtime.token)
        _set_cfg(runtime, "channel_name", None)
        await message.reply_text("✅ ᴄʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ ʀᴇᴍᴏᴠᴇᴅ.")

    @app.on_message(filters.command("setsupportname"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setsupportname(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setsupportname"))
        name = parts[1].strip()[:32]
        await cust.set_clone_support_name(runtime.token, name)
        _set_cfg(runtime, "support_name", name)
        await message.reply_text("✅ sᴜᴘᴘᴏʀᴛ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ sᴇᴛ.")

    @app.on_message(filters.command("delsupportname"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delsupportname(client, message: Message):
        await cust.del_clone_support_name(runtime.token)
        _set_cfg(runtime, "support_name", None)
        await message.reply_text("✅ sᴜᴘᴘᴏʀᴛ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ ʀᴇᴍᴏᴠᴇᴅ.")

    @app.on_message(filters.command("setownername"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _setownername(client, message: Message):
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("setownername"))
        name = parts[1].strip()[:32]
        await cust.set_clone_owner_name(runtime.token, name)
        _set_cfg(runtime, "owner_name", name)
        await message.reply_text("✅ ᴏᴡɴᴇʀ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ sᴇᴛ.")

    @app.on_message(filters.command("delownername"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delownername(client, message: Message):
        await cust.del_clone_owner_name(runtime.token)
        _set_cfg(runtime, "owner_name", None)
        await message.reply_text("✅ ᴏᴡɴᴇʀ ʙᴜᴛᴛᴏɴ ɴᴀᴍᴇ ʀᴇᴍᴏᴠᴇᴅ.")

    def _register_btn_toggle(en_cmd, dis_cmd, key, label):
        @app.on_message(filters.command(en_cmd), group=CLONE_HANDLER_GROUP)
        @_owner_only
        async def _en(client, message: Message, k=key, lab=label):
            await cust.set_btn_enabled(runtime.token, k, True)
            _set_cfg(runtime, f"btn_{k}", True)
            await message.reply_text(f"✅ {lab} ʙᴜᴛᴛᴏɴ ᴇɴᴀʙʟᴇᴅ.")

        @app.on_message(filters.command(dis_cmd), group=CLONE_HANDLER_GROUP)
        @_owner_only
        async def _dis(client, message: Message, k=key, lab=label):
            await cust.set_btn_enabled(runtime.token, k, False)
            _set_cfg(runtime, f"btn_{k}", False)
            await message.reply_text(f"✅ {lab} ʙᴜᴛᴛᴏɴ ᴅɪsᴀʙʟᴇᴅ.")

    _register_btn_toggle("enhelpbtn", "dishelpbtn", "help", "ʜᴇʟᴘ")
    _register_btn_toggle("enclonebtn", "disclonebtn", "clone", "ᴀᴅᴅ ᴍᴇ")
    _register_btn_toggle("ensupportbtn", "dissupportbtn", "support", "sᴜᴘᴘᴏʀᴛ")
    _register_btn_toggle("enchannelbtn", "dischannelbtn", "channel", "ᴄʜᴀɴɴᴇʟ")
    _register_btn_toggle("enownerbtn", "disownerbtn", "owner", "ᴏᴡɴᴇʀ")

    @app.on_message(filters.command("addbtn"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _addbtn(client, message: Message):
        parts = (message.text or "").split(None, 2)
        if len(parts) < 3:
            return await message.reply_text(_cmd_help("addbtn"))
        name, url = parts[1].strip(), parts[2].strip()
        if not url.startswith(("http://", "https://", "tg://", "t.me")):
            return await message.reply_text("ɢɪᴠᴇ ᴀ ᴠᴀʟɪᴅ ʟɪɴᴋ.")
        await cust.add_extra_button(runtime.token, name, url)
        _set_cfg(runtime, "extra_buttons", await cust.get_extra_buttons(runtime.token))
        await message.reply_text(f"✅ ʙᴜᴛᴛᴏɴ {name} ᴀᴅᴅᴇᴅ.")

    @app.on_message(filters.command("delbtn"), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _delbtn(client, message: Message):
        parts = (message.text or "").split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(_cmd_help("delbtn"))
        ok = await cust.del_extra_button(runtime.token, parts[1].strip())
        if ok:
            _set_cfg(runtime, "extra_buttons", await cust.get_extra_buttons(runtime.token))
            return await message.reply_text("✅ ʙᴜᴛᴛᴏɴ ʀᴇᴍᴏᴠᴇᴅ.")
        await message.reply_text("ʙᴜᴛᴛᴏɴ ɴᴏᴛ ғᴏᴜɴᴅ.")

    @app.on_message(filters.command(["clearbtns", "delallbtn"]), group=CLONE_HANDLER_GROUP)
    @_owner_only
    async def _clearbtns(client, message: Message):
        await cust.clear_extra_buttons(runtime.token)
        _set_cfg(runtime, "extra_buttons", [])
        await message.reply_text("✅ ᴀʟʟ ᴄᴜsᴛᴏᴍ ʙᴜᴛᴛᴏɴs ʀᴇᴍᴏᴠᴇᴅ.")






    _hmap = getattr(app.dispatcher, "handlers", None) or getattr(
        app.dispatcher, "groups", None
    )
    _registered = len((_hmap or {}).get(CLONE_HANDLER_GROUP, []))
    LOGGER(__name__).info(
        "[CLONE-FIX] handler registration complete: %d clone handlers on group %s",
        _registered,
        CLONE_HANDLER_GROUP,
    )


_IMAGE_MIME_PREFIX = "image/"
_IMAGE_DOC_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _document_is_image(doc) -> bool:
    """True when a document carries an image (sent as uncompressed photo/file)."""
    mime = (getattr(doc, "mime_type", None) or "").lower()
    if mime.startswith(_IMAGE_MIME_PREFIX):
        return True
    fname = (getattr(doc, "file_name", None) or "").lower()
    return fname.endswith(_IMAGE_DOC_EXTS)


async def _extract_media(message: Message) -> Optional[tuple]:
    """Return (media_type, file_id) of the replied media, or None.

    media_type is one of "photo" | "video" | "animation" | "document" (image
    documents). Anything else we can't type (audio, voice, video_note, ...)
    yields (None, file_id) so it is stored as a legacy bare file_id and sent
    exactly like before.
    """
    reply = message.reply_to_message
    if not reply:
        return None
    for attr, mtype in (("photo", "photo"), ("video", "video"), ("animation", "animation")):
        media = getattr(reply, attr, None)
        if media:
            fid = getattr(media, "file_id", None)
            if fid:
                return mtype, str(fid)
    doc = reply.document
    if doc:
        fid = getattr(doc, "file_id", None)
        if fid:
            return ("document" if _document_is_image(doc) else None), str(fid)
    audio = reply.audio
    if audio:
        fid = getattr(audio, "file_id", None)
        if fid:
            return None, str(fid)
    return None
