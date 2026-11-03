# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram import enums

from IotaXMedia import app
from IotaXMedia.utils.database import (
    add_nonadmin_chat,
    get_authuser,
    get_authuser_names,
    get_playmode,
    get_playtype,
    get_upvote_count,
    is_nonadmin_chat,
    is_skipmode,
    remove_nonadmin_chat,
    set_playmode,
    set_playtype,
    set_upvotes,
    skip_off,
    skip_on,
)
from IotaXMedia.utils.decorators.admins import ActualAdminCB
from IotaXMedia.utils.decorators.language import language, languageCB
from IotaXMedia.utils.colored_buttons import (
    edit_message_text_colored,
    edit_reply_markup_colored,
    send_message_colored,
    styled_button,
)
from IotaXMedia.utils.inline.settings import (
    auth_users_markup,
    auth_users_markup_colored,
    playmode_users_markup,
    playmode_users_markup_colored,
    setting_markup,
    setting_markup_colored,
    vote_mode_markup,
    vote_mode_markup_colored,
)
from IotaXMedia.utils.inline.start import private_panel
from config import BANNED_USERS, OWNER_ID



async def _edit_settings_markup_colored(chat_id, message_id, btns_col, btns_fb):
    try:
        r = await edit_reply_markup_colored(chat_id, message_id, btns_col)
        if r:
            return
    except Exception:
        pass
    try:
        return await app.edit_message_reply_markup(
            chat_id, message_id, reply_markup=InlineKeyboardMarkup(btns_fb)
        )
    except MessageNotModified:
        return


@app.on_message(filters.command(["settings", "setting"]) & filters.group & ~filters.user(list(BANNED_USERS)))
@language
async def settings_mar(client, message: Message, _):
    buttons = setting_markup(_)
    buttons_col = setting_markup_colored(_)
    text = _["setting_1"].format(app.mention, message.chat.id, message.chat.title)
    try:
        r = await send_message_colored(message.chat.id, text, buttons_col)
        if r:
            return
    except Exception:
        pass
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))



@app.on_callback_query(filters.regex(r"^SETTINGS_BACK$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def settings_cb(client, callback: CallbackQuery, _):
    try:
        await callback.answer(_["set_cb_5"])
    except Exception:
        pass
    buttons = setting_markup(_)
    buttons_col = setting_markup_colored(_)
    text = _["setting_1"].format(app.mention, callback.message.chat.id, callback.message.chat.title)
    try:
        r = await edit_message_text_colored(
            callback.message.chat.id, callback.message.id, text, buttons_col
        )
        if r:
            return
    except Exception:
        pass
    try:
        await callback.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except MessageNotModified:
        return



@app.on_callback_query(filters.regex(r"^SETTINGS_PRIVATE_BACK$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def settings_back_markup(client, callback: CallbackQuery, _):
    try:
        await callback.answer()
    except Exception:
        pass

    if callback.message.chat.type == ChatType.PRIVATE:
        await app.resolve_peer(OWNER_ID)
        buttons = private_panel(_)
        try:
            r = await edit_message_text_colored(
                callback.message.chat.id,
                callback.message.id,
                _["start_2"].format(callback.from_user.mention, app.mention),
                buttons,
            )
            if r:
                return
        except Exception:
            pass
        try:
            await callback.edit_message_text(
                _["start_2"].format(callback.from_user.mention, app.mention),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        except MessageNotModified:
            return
    else:
        buttons = setting_markup(_)
        buttons_col = setting_markup_colored(_)
        await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )



@app.on_callback_query(
    filters.regex(
        r"^(SEARCH_MODE_INFO|PLAY_TYPE_INFO|CHANNEL_MODE_INFO|AUTH_USERS_INFO|CURRENT_VOTE_INFO|VOTE_MODE_INFO|PLAYBACK_SETTINGS|AUTH_SETTINGS|VOTE_SETTINGS)$"
    ) & ~filters.user(list(BANNED_USERS))
)
@languageCB
async def without_admin_rights(client, callback: CallbackQuery, _):
    command = callback.matches[0].group(1)
    if command == "SEARCH_MODE_INFO":
        try:
            return await callback.answer(_["setting_2"], show_alert=True)
        except Exception:
            return
    if command == "CHANNEL_MODE_INFO":
        try:
            return await callback.answer(_["setting_5"], show_alert=True)
        except Exception:
            return
    if command == "PLAY_TYPE_INFO":
        try:
            return await callback.answer(_["setting_6"], show_alert=True)
        except Exception:
            return
    if command == "AUTH_USERS_INFO":
        try:
            return await callback.answer(_["setting_3"], show_alert=True)
        except Exception:
            return
    if command == "VOTE_MODE_INFO":
        try:
            return await callback.answer(_["setting_8"], show_alert=True)
        except Exception:
            return
    if command == "CURRENT_VOTE_INFO":
        current = await get_upvote_count(callback.message.chat.id)
        try:
            return await callback.answer(_["setting_9"].format(current), show_alert=True)
        except Exception:
            return
    if command == "PLAYBACK_SETTINGS":
        try:
            await callback.answer(_["set_cb_2"], show_alert=True)
        except Exception:
            pass
        playmode = await get_playmode(callback.message.chat.id)
        Direct = True if playmode == "Direct" else None
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        Group = True if not is_non_admin else None
        playty = await get_playtype(callback.message.chat.id)
        Playtype = None if playty == "Everyone" else True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
        buttons_col = playmode_users_markup_colored(_, Direct, Group, Playtype)
    if command == "AUTH_SETTINGS":
        try:
            await callback.answer(_["set_cb_1"], show_alert=True)
        except Exception:
            pass
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        buttons = auth_users_markup(_, True) if not is_non_admin else auth_users_markup(_)
        buttons_col = auth_users_markup_colored(_, True) if not is_non_admin else auth_users_markup_colored(_)
    if command == "VOTE_SETTINGS":
        mode = await is_skipmode(callback.message.chat.id)
        current = await get_upvote_count(callback.message.chat.id)
        buttons = vote_mode_markup(_, current, mode)
        buttons_col = vote_mode_markup_colored(_, current, mode)
    try:
        return await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )
    except MessageNotModified:
        return



@app.on_callback_query(filters.regex(r"^(INCREASE_VOTE_COUNT|DECREASE_VOTE_COUNT)$") & ~filters.user(list(BANNED_USERS)))
@ActualAdminCB
async def vote_count_adjust(client, callback: CallbackQuery, _):
    command = callback.matches[0].group(1)
    
    if not await is_skipmode(callback.message.chat.id):
        return await callback.answer(_["setting_10"], show_alert=True)
    
    current = await get_upvote_count(callback.message.chat.id)
    
    if command == "DECREASE_VOTE_COUNT":
        final = current - 2
        if final < 2:
            final = 2
            await callback.answer(_["setting_11"], show_alert=True)
        await set_upvotes(callback.message.chat.id, final)
    else:
        final = current + 2
        if final > 15:
            final = 15
            await callback.answer(_["setting_12"], show_alert=True)
        await set_upvotes(callback.message.chat.id, final)
    
    buttons = vote_mode_markup(_, final, True)
    buttons_col = vote_mode_markup_colored(_, final, True)

    try:
        return await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )
    except MessageNotModified:
        return



@app.on_callback_query(
    filters.regex(r"^(TOGGLE_SEARCH_MODE|TOGGLE_CHANNEL_MODE|TOGGLE_PLAY_TYPE)$") & ~filters.user(list(BANNED_USERS))
)
@ActualAdminCB
async def playmode_ans(client, callback: CallbackQuery, _):
    command = callback.matches[0].group(1)
    
    if command == "TOGGLE_CHANNEL_MODE":
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(callback.message.chat.id)
            Group = None
        else:
            await remove_nonadmin_chat(callback.message.chat.id)
            Group = True
        playmode = await get_playmode(callback.message.chat.id)
        Direct = True if playmode == "Direct" else None
        playty = await get_playtype(callback.message.chat.id)
        Playtype = None if playty == "Everyone" else True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
        buttons_col = playmode_users_markup_colored(_, Direct, Group, Playtype)
    
    elif command == "TOGGLE_SEARCH_MODE":
        try:
            await callback.answer(_["set_cb_3"], show_alert=True)
        except Exception:
            pass
        playmode = await get_playmode(callback.message.chat.id)
        if playmode == "Direct":
            await set_playmode(callback.message.chat.id, "Inline")
            Direct = None
        else:
            await set_playmode(callback.message.chat.id, "Direct")
            Direct = True
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        Group = True if not is_non_admin else None
        playty = await get_playtype(callback.message.chat.id)
        Playtype = False if playty == "Everyone" else True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
        buttons_col = playmode_users_markup_colored(_, Direct, Group, Playtype)
    
    elif command == "TOGGLE_PLAY_TYPE":
        try:
            await callback.answer(_["set_cb_3"], show_alert=True)
        except Exception:
            pass
        playty = await get_playtype(callback.message.chat.id)
        if playty == "Everyone":
            await set_playtype(callback.message.chat.id, "Admin")
            Playtype = False
        else:
            await set_playtype(callback.message.chat.id, "Everyone")
            Playtype = True
        playmode = await get_playmode(callback.message.chat.id)
        Direct = True if playmode == "Direct" else None
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        Group = True if not is_non_admin else None
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
        buttons_col = playmode_users_markup_colored(_, Direct, Group, Playtype)
    
    try:
        return await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )
    except MessageNotModified:
        return



@app.on_callback_query(filters.regex(r"^(TOGGLE_AUTH_MODE|VIEW_AUTH_USERS)$") & ~filters.user(list(BANNED_USERS)))
@ActualAdminCB
async def authusers_mar(client, callback: CallbackQuery, _):
    command = callback.matches[0].group(1)
    
    if command == "VIEW_AUTH_USERS":
        _authusers = await get_authuser_names(callback.message.chat.id)
        if not _authusers:
            try:
                return await callback.answer(_["setting_4"], show_alert=True)
            except Exception:
                return
        else:
            try:
                await callback.answer(_["set_cb_4"], show_alert=True)
            except Exception:
                pass
            counter = 0
            await callback.edit_message_text(_["auth_6"])
            msg = _["auth_7"].format(callback.message.chat.title)
            for note in _authusers:
                _note = await get_authuser(callback.message.chat.id, note)
                user_id = _note["auth_user_id"]
                admin_id = _note["admin_id"]
                admin_name = _note["admin_name"]
                try:
                    user_obj = await app.get_users(user_id)
                    user_name = user_obj.first_name
                    counter += 1
                except Exception:
                    continue
                msg += f"{counter}➤ {user_name}[<code>{user_id}</code>]\n"
                msg += f"   {_['auth_8']} {admin_name}[<code>{admin_id}</code>]\n\n"
            upl = [
                [
                    InlineKeyboardButton(text=_["BACK_BUTTON"], callback_data="AUTH_SETTINGS", style=enums.ButtonStyle.PRIMARY),
                    InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=enums.ButtonStyle.DANGER)
                ]
            ]
            upl_col = [
                [
                    styled_button(_["BACK_BUTTON"], callback_data="AUTH_SETTINGS", style="primary"),
                    styled_button(_["CLOSE_BUTTON"], callback_data="close", style="danger"),
                ]
            ]
            try:
                r = await edit_message_text_colored(
                    callback.message.chat.id, callback.message.id, msg, upl_col
                )
                if r:
                    return
            except Exception:
                pass
            try:
                return await callback.edit_message_text(
                    msg, reply_markup=InlineKeyboardMarkup(upl)
                )
            except MessageNotModified:
                return
    
    try:
        await callback.answer(_["set_cb_3"], show_alert=True)
    except Exception:
        pass
    
    if command == "TOGGLE_AUTH_MODE":
        is_non_admin = await is_nonadmin_chat(callback.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(callback.message.chat.id)
            buttons = auth_users_markup(_)
            buttons_col = auth_users_markup_colored(_)
        else:
            await remove_nonadmin_chat(callback.message.chat.id)
            buttons = auth_users_markup(_, True)
            buttons_col = auth_users_markup_colored(_, True)
    
    try:
        return await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )
    except MessageNotModified:
        return



@app.on_callback_query(filters.regex(r"^TOGGLE_VOTE_MODE$") & ~filters.user(list(BANNED_USERS)))
@ActualAdminCB
async def vote_change(client, callback: CallbackQuery, _):
    try:
        await callback.answer(_["set_cb_3"], show_alert=True)
    except Exception:
        pass
    
    mod = None
    if await is_skipmode(callback.message.chat.id):
        await skip_off(callback.message.chat.id)
    else:
        mod = True
        await skip_on(callback.message.chat.id)
    
    current = await get_upvote_count(callback.message.chat.id)
    buttons = vote_mode_markup(_, current, mod)
    buttons_col = vote_mode_markup_colored(_, current, mod)
    
    try:
        return await _edit_settings_markup_colored(
            callback.message.chat.id, callback.message.id, buttons_col, buttons
        )
    except MessageNotModified:
        return
