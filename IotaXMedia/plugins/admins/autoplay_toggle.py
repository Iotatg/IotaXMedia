# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import CallbackQuery

from IotaXMedia import app
from IotaXMedia.utils.god_style import god_text
from IotaXMedia.utils.stream.autoplay import (
    toggle_autoplay,
    set_autoplay,
    is_autoplay_on,
    AUTO,
)
from IotaXMedia.utils.decorators import ActualAdminCB, AdminActual
from IotaXMedia.utils.colored_buttons import (
    styled_button,
    send_message_colored,
    buttons_to_inline_markup,
    edit_reply_markup_colored,
)


@app.on_callback_query(filters.regex(r"^AUTOPLAY_TOGGLE (.+)$"))
@ActualAdminCB
async def autoplay_toggle_callback(client, callback: CallbackQuery, _):
    try:
        chat_id = int(callback.matches[0].group(1))
    except (IndexError, ValueError):
        return await callback.answer("ᴇʀʀᴏʀ", show_alert=True)

    new_status = await toggle_autoplay(chat_id)

    label = AUTO if new_status else god_text("autoplay") + " 🔴"
    style = "success" if new_status else "danger"
    toggle_btn = styled_button(label, callback_data=f"AUTOPLAY_TOGGLE {chat_id}", style=style)

    try:
        close_btn = styled_button("✖", callback_data="close", style="danger")
        control_row = [
            styled_button("▷", callback_data=f"ADMIN Resume|{chat_id}", style="success"),
            styled_button("II", callback_data=f"ADMIN Pause|{chat_id}", style="primary"),
            styled_button("↻", callback_data=f"ADMIN Replay|{chat_id}", style="primary"),
            styled_button("‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style="primary"),
            styled_button("▢", callback_data=f"ADMIN Stop|{chat_id}", style="danger"),
        ]
        new_markup = [control_row, [toggle_btn], [close_btn]]
        result = await edit_reply_markup_colored(
            chat_id=callback.message.chat.id,
            message_id=callback.message.id,
            reply_markup=new_markup,
        )
        if not result:
            await callback.message.edit_reply_markup(
                reply_markup=buttons_to_inline_markup(new_markup)
            )
    except Exception:
        pass

    await callback.answer(label, show_alert=True)


@app.on_callback_query(filters.regex(r"^AUTOPLAY_SET (.+) (\d)$"))
@ActualAdminCB
async def autoplay_set_callback(client, callback: CallbackQuery, _):
    try:
        chat_id = int(callback.matches[0].group(1))
        desired = callback.matches[0].group(2) == "1"
    except (IndexError, ValueError):
        return await callback.answer("ᴇʀʀᴏʀ", show_alert=True)

    await set_autoplay(chat_id, desired)
    state = "ᴇɴᴀʙʟᴇᴅ" if desired else "ᴅɪsᴀʙʟᴇᴅ"
    await callback.answer(f"{AUTO} {state}", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


@app.on_message(filters.command("autoplay") & filters.group)
@AdminActual
async def autoplay_command(client, message, _):
    chat_id = message.chat.id
    current = await is_autoplay_on(chat_id)
    status = "ᴏɴ 🔥" if current else "ᴏғғ ❌"
    text = (
        f"{AUTO} ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ\n\n"
        f"ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs : {status}\n\n"
        f"ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ :"
    )
    enable_btn = styled_button("ᴇɴᴀʙʟᴇ", callback_data=f"AUTOPLAY_SET {chat_id} 1", style="success")
    disable_btn = styled_button("ᴅɪsᴀʙʟᴇ", callback_data=f"AUTOPLAY_SET {chat_id} 0", style="danger")
    markup = [[enable_btn, disable_btn]]
    try:
        result = await send_message_colored(chat_id, text, markup)
        if not result:
            await app.send_message(chat_id, text, reply_markup=buttons_to_inline_markup(markup))
    except Exception:
        pass
