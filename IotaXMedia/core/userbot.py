# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import Client

import config

from ..logging import LOGGER

assistants = []







ASSISTANT_WATCHES = []
assistantids = []

GROUPS_TO_JOIN = [
    "im_iota",
    "https://t.me/im_iota",
]



class Userbot:
    def __init__(self):






        is_clone = bool(getattr(config, "CLONE_MODE", False))
        if is_clone:
            bot_id = (
                config.BOT_TOKEN.split(":", 1)[0]
                if ":" in config.BOT_TOKEN
                else str(hash(config.BOT_TOKEN))
            )
            suffix = f"clone_{bot_id}"
            names = [f"{suffix}_assis{i}" for i in range(1, 6)]
            in_memory = True
        else:
            names = ["IotaAssis1", "IotaAssis2", "IotaAssis3", "IotaAssis4", "IotaAssis5"]
            in_memory = False




        self.one = Client(
            names[0],
            config.API_ID,
            config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=False,
            in_memory=in_memory,
        )
        self.two = Client(
            names[1],
            config.API_ID,
            config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
            in_memory=in_memory,
        )
        self.three = Client(
            names[2],
            config.API_ID,
            config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
            in_memory=in_memory,
        )
        self.four = Client(
            names[3],
            config.API_ID,
            config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
            in_memory=in_memory,
        )
        self.five = Client(
            names[4],
            config.API_ID,
            config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
            in_memory=in_memory,
        )

    async def start_assistant(self, client: Client, index: int):
        string_attr = [
            config.STRING1,
            config.STRING2,
            config.STRING3,
            config.STRING4,
            config.STRING5,
        ][index - 1]
        if not string_attr:
            return

        try:
            await client.start()
            from pyrogram import filters as _filters
            from pyrogram.handlers import MessageHandler as _MessageHandler
            for _cb, _group in ASSISTANT_WATCHES:
                try:
                    client.add_handler(
                        _MessageHandler(_cb, _filters.group & _filters.incoming & ~_filters.service),
                        group=_group,
                    )
                except Exception:
                    pass
            for group in GROUPS_TO_JOIN:
                try:
                    await client.join_chat(group)
                except Exception:
                    pass

            assistants.append(index)

            if config.LOGGER_ID:
                try:
                    await client.send_message(
                        config.LOGGER_ID, f"Iota's Assistant {index} Started"
                    )
                except Exception:
                    LOGGER(__name__).warning(
                        f"Assistant {index} can't access the log group – continuing without it."
                    )

            me = await client.get_me()
            client.id, client.name, client.username = me.id, me.first_name, me.username
            assistantids.append(me.id)

            LOGGER(__name__).info(f"Assistant {index} Started as {client.name}")

        except Exception as e:
            LOGGER(__name__).error(f"Failed to start Assistant {index}: {e}")

    async def start(self):
        LOGGER(__name__).info("Starting Iota's Assistants...")
        await self.start_assistant(self.one, 1)
        await self.start_assistant(self.two, 2)
        await self.start_assistant(self.three, 3)
        await self.start_assistant(self.four, 4)
        await self.start_assistant(self.five, 5)

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        try:
            if config.STRING1:
                await self.one.stop()
            if config.STRING2:
                await self.two.stop()
            if config.STRING3:
                await self.three.stop()
            if config.STRING4:
                await self.four.stop()
            if config.STRING5:
                await self.five.stop()
        except Exception as e:
            LOGGER(__name__).error(f"Error while stopping assistants: {e}")
