# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import CallbackQuery

from IotaXMedia import app
from IotaXMedia.utils.stream.thumb_settings import is_thumb_on, set_thumb, toggle_thumb
from IotaXMedia.utils.decorators import ActualAdminCB, AdminActual
from IotaXMedia.utils.colored_buttons import (
    styled_button,
    send_message_colored,
    buttons_to_inline_markup,
)
from IotaXMedia.utils.god_style import god_text, SYM


@app.on_callback_query(filters.regex(r"^THUMB_SET (.+) (\d)$"))
@ActualAdminCB
async def thumb_set_callback(client, callback: CallbackQuery, _):
    try:
        chat_id = int(callback.matches[0].group(1))
        desired = callback.matches[0].group(2) == "1"
    except (IndexError, ValueError):
        return await callback.answer("Invalid data", show_alert=True)

    await set_thumb(chat_id, desired)
    state = god_text("enabled") if desired else god_text("disabled")
    await callback.answer(f"thumbnail {state}", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^THUMB_TOGGLE (.+)$"))
@ActualAdminCB
async def thumb_toggle_callback(client, callback: CallbackQuery, _):
    try:
        chat_id = int(callback.matches[0].group(1))
    except (IndexError, ValueError):
        return await callback.answer("Invalid data", show_alert=True)

    new_status = await toggle_thumb(chat_id)
    state = god_text("enabled") if new_status else god_text("disabled")
    await callback.answer(f"thumbnail {state}", show_alert=True)


@app.on_message(filters.command("thumb") & filters.group)
@AdminActual
async def thumb_command(client, message, _):
    """
    /thumb — stream visual settings panel. Toggle album-art (thumbnail)
    display in stream updates. Setting is saved individually per chat.
    """
    chat_id = message.chat.id
    current = await is_thumb_on(chat_id)
    status = god_text("on") if current else god_text("off")
    text = (
        f"{SYM['frame_v']} {god_text('thumbnail settings')} {SYM['frame_v']}\n\n"
        f"{SYM['arrow']} /thumb : {god_text('manage stream visual settings')}.\n\n"
        f"{SYM['bullet']} {god_text('basic commands')} :\n\n"
        f"💮 {god_text('toggle album art display')}. "
        f"{god_text('disabling it reduces data load and maintains a minimalist chat look')}.\n\n"
        f"{SYM['bullet']} {god_text('basic commands')} :\n\n"
        f"• {god_text('enable')} : {god_text('display artwork with stream info')}.\n"
        f"• {god_text('disable')} : {god_text('send pure text-based updates')}.\n"
        f"• {god_text('close')} : {god_text('dismiss the configuration')}.\n\n"
        f"๏ {god_text('current status')} : {status}\n"
        f"๏ {god_text('note')} : {god_text('settings are saved individually per chat')}."
    )
    enable_btn = styled_button(
        god_text("enable"), callback_data=f"THUMB_SET {chat_id} 1", style="success"
    )
    disable_btn = styled_button(
        god_text("disable"), callback_data=f"THUMB_SET {chat_id} 0", style="danger"
    )
    close_btn = styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger")
    markup = [[enable_btn, disable_btn], [close_btn]]
    try:
        result = await send_message_colored(chat_id, text, markup)
        if not result:
            await app.send_message(
                chat_id, text, reply_markup=buttons_to_inline_markup(markup)
            )
    except Exception:
        pass
