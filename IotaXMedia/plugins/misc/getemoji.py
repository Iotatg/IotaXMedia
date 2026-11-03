# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
Owner-only utility: extract Telegram custom (premium) emoji IDs.

Usage:
  • Reply to any message that contains custom emojis (e.g. a premium user's
    message) and send /getemoji — it lists every custom_emoji_id found.
  • Or send a message containing a custom emoji and use /getemoji on it.

The bot does NOT need Premium; incoming messages already carry the
custom_emoji_id inside their entities. This just reads and prints them.
"""
from pyrogram import filters
from pyrogram.types import Message, MessageEntity

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS


def _utf16_substring(text: str, offset: int, length: int) -> str:
    """Telegram entity offset/length are in UTF-16 code units."""
    encoded = text.encode("utf-16-le")
    start = offset * 2
    end = start + length * 2
    return encoded[start:end].decode("utf-16-le")


@app.on_message(filters.command(["getemoji", "emojiid", "ceid"]) & SUDOERS)
async def get_emoji_id(client, message: Message):
    target = message.reply_to_message or message
    source_text = target.text or target.caption or ""
    entities = list(target.entities or []) + list(target.caption_entities or [])
    found = [e for e in entities if e.type == "custom_emoji"]


    sticker = getattr(target, "sticker", None)
    sticker_id = getattr(sticker, "custom_emoji_id", None) if sticker else None

    if not found and not sticker_id:
        return await message.reply_text(
            "Is message mein koi custom emoji (premium emoji) nahi mila.\n\n"
            "Kaise use karein:\n"
            "• Kisi premium user YA kisi bot ke custom emoji wale message par reply karke /getemoji bhejo.\n"
            "• Dusre bot ka message group mein ho (ya forward karke bhejo) — bot-to-bot DM nahi chalega.\n"
            "• Ya khud koi custom emoji likh kar /getemoji bhejo.\n\n"
            "Note: bot ko Premium ki zarurat nahi — incoming message ke entities/sticker mein "
            "custom_emoji_id already milta hai.",
            disable_web_page_preview=True,
        )

    count = len(found) + (1 if sticker_id else 0)
    notice = await message.reply_text(
        f"🔍 {count} custom emoji ID(s) nikaal raha hoon...",
        disable_web_page_preview=True,
    )

    summary_lines = []
    for ent in found:
        emoji_char = _utf16_substring(source_text, ent.offset, ent.length)
        text = f"{emoji_char}\n{ent.custom_emoji_id}"
        try:
            await app.send_message(
                message.chat.id,
                text,
                entities=[
                    MessageEntity(
                        type="custom_emoji",
                        offset=0,
                        length=ent.length,
                        custom_emoji_id=ent.custom_emoji_id,
                    )
                ],
                reply_to_message_id=message.id,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
        summary_lines.append(f"<code>{ent.custom_emoji_id}</code>")

    if sticker_id:
        try:
            await app.send_sticker(message.chat.id, sticker.file_id, reply_to_message_id=message.id)
        except Exception:
            pass
        summary_lines.append(f"<code>{sticker_id}</code>")

    try:
        await notice.delete()
    except Exception:
        pass

    await message.reply_text(
        f"⚡ {count} custom emoji ID(s):\n\n" + "\n".join(summary_lines),
        parse_mode="html",
        disable_web_page_preview=True,
    )
