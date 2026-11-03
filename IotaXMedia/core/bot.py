# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import html
import sys
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode

import config
from ..logging import LOGGER


class MusicBotClient(Client):
    def __init__(self):
        token = config.BOT_TOKEN



        if getattr(config, "CLONE_MODE", False):
            bot_id = token.split(":", 1)[0] if ":" in token else str(hash(token))
            name = f"clone_{bot_id}"
        else:
            name = "˹𝐈ᴏᴛᴀ ✘ 𝙼ᴜꜱɪᴄ˼"
        super().__init__(
            name=name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=token,
            workers=48,
            max_concurrent_transmissions=7,



            in_memory=bool(getattr(config, "CLONE_MODE", False)),



            parse_mode=ParseMode.HTML,
        )
        LOGGER(__name__).info("Bot client initialized.")

    def _style_text(self, text):
        try:
            from IotaXMedia.utils.god_style import fancy_output

            return fancy_output(text)
        except Exception:
            return text

    async def send_message(self, chat_id, text, *args, **kwargs):
        return await super().send_message(
            chat_id, self._style_text(text), *args, **kwargs
        )

    async def send_photo(self, chat_id, photo, caption="", *args, **kwargs):
        if caption:
            caption = self._style_text(caption)
        return await super().send_photo(chat_id, photo, caption, *args, **kwargs)

    async def send_document(self, chat_id, document, thumb=None, caption="", *args, **kwargs):
        if caption:
            caption = self._style_text(caption)
        return await super().send_document(
            chat_id, document, thumb, caption, *args, **kwargs
        )

    async def send_video(self, chat_id, video, caption="", *args, **kwargs):
        if caption:
            caption = self._style_text(caption)
        return await super().send_video(chat_id, video, caption, *args, **kwargs)

    async def send_animation(self, chat_id, animation, caption="", *args, **kwargs):
        if caption:
            caption = self._style_text(caption)
        return await super().send_animation(
            chat_id, animation, caption, *args, **kwargs
        )

    async def send_audio(self, chat_id, audio, caption="", *args, **kwargs):
        if caption:
            caption = self._style_text(caption)
        return await super().send_audio(chat_id, audio, caption, *args, **kwargs)

    async def edit_message_text(self, chat_id, message_id, text, *args, **kwargs):
        return await super().edit_message_text(
            chat_id, message_id, self._style_text(text), *args, **kwargs
        )

    async def edit_message_caption(self, chat_id, message_id, caption, *args, **kwargs):
        return await super().edit_message_caption(
            chat_id, message_id, self._style_text(caption), *args, **kwargs
        )

    async def answer_callback_query(self, callback_query_id, text=None, *args, **kwargs):
        if text:
            text = self._style_text(text)
        return await super().answer_callback_query(
            callback_query_id, text, *args, **kwargs
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username, self.id = me.username, me.id
        self.name = f"{me.first_name} {me.last_name or ''}".strip()
        self.mention = (
            f'<a href="tg://user?id={me.id}">'
            f"{html.escape(me.first_name or self.name)}</a>"
        )

        is_clone = bool(getattr(config, "CLONE_MODE", False))

        if is_clone:



            LOGGER(__name__).info(
                f"✅ Clone bot started as {self.name} (@{self.username})"
            )
            return

        if not config.LOGGER_ID:
            LOGGER(__name__).warning(
                "⚠️ LOGGER_ID not set – skipping log-group verification. "
                "Set LOGGER_ID in your .env to enable startup logging."
            )
        else:
            try:
                await self.send_message(
                    config.LOGGER_ID,
                    (
                        f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                        f"ɪᴅ : <code>{self.id}</code>\n"
                        f"ɴᴀᴍᴇ : {self.name}\n"
                        f"ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                    ),
                )
            except (errors.ChannelInvalid, errors.PeerIdInvalid):
                LOGGER(__name__).error("❌ Bot cannot access the log group/channel – add & promote it first!")
                sys.exit()
            except Exception as exc:
                LOGGER(__name__).error(f"❌ Bot has failed to access the log group.\nReason: {type(exc).__name__}")
                sys.exit()

            try:
                member = await self.get_chat_member(config.LOGGER_ID, self.id)
                if member.status != ChatMemberStatus.ADMINISTRATOR:
                    LOGGER(__name__).error("❌ Promote the bot as admin in the log group/channel.")
                    sys.exit()
            except Exception as e:
                LOGGER(__name__).error(f"❌ Could not check admin status: {e}")
                sys.exit()


        try:
            from IotaXMedia.utils.bot_commands import (
                DEFAULT_COMMANDS,
                owner_command_list,
            )
            from pyrogram.types import BotCommandScopeDefault, BotCommandScopeChat

            await self.set_bot_commands(
                DEFAULT_COMMANDS, scope=BotCommandScopeDefault()
            )
            if config.OWNER_ID and config.OWNER_ID != 0:
                await self.set_bot_commands(
                    owner_command_list(),
                    scope=BotCommandScopeChat(config.OWNER_ID),
                )
            LOGGER(__name__).info("✅ Bot command menu set (owner-scoped).")
        except Exception as exc:
            LOGGER(__name__).warning(f"⚠️ Could not set bot command menu: {exc}")

        LOGGER(__name__).info(f"✅ Music Bot started as {self.name} (@{self.username})")
