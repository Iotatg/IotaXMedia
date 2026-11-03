# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import re
from typing import Union

from pyrogram import Client, filters, types
from pyrogram.types import Message

from IotaXMedia import app
from IotaXMedia.misc import SUDOERS
from IotaXMedia.utils.database import get_lang
from IotaXMedia.utils.decorators.language import LanguageStart, languageCB
from IotaXMedia.utils.inline.help import (
    action_sub_menu,
    clone_back_markup,
    clone_help_panel,
    first_page,
    help_main_menu,
    help_music_page,
    help_mgmt_page,
    private_help_panel,
    topic_back_markup,
)
from IotaXMedia.utils.inline.start import private_panel
from IotaXMedia.utils.colored_buttons import buttons_to_inline_markup, smart_edit_message_text, smart_send_photo
from IotaXMedia.utils.ui_style import style_help_text
from config import BANNED_USERS, HELP_IMG_URL, SUPPORT_CHAT
import config
from strings import get_string, helpers
from IotaXMedia.clone.links import clone_support_link


def _is_authorized(user_id: int) -> bool:
    """Owner / sudoers see the restricted (owner-only) help sections."""
    return bool(user_id in SUDOERS)



@app.on_message(filters.command(["help"]) & filters.private & ~filters.user(list(BANNED_USERS)))
@app.on_callback_query(filters.regex("open_help") & ~filters.user(list(BANNED_USERS)))
@LanguageStart
async def helper_private(client: Client, update: Union[Message, types.CallbackQuery], _):
    is_cb = isinstance(update, types.CallbackQuery)
    language = await get_lang(update.from_user.id)
    _ = get_string(language)

    is_authorized = _is_authorized(update.from_user.id)
    keyboard = first_page(_, is_authorized)
    caption = _["help_1"].format(clone_support_link())

    if is_cb:
        await update.answer()
        await smart_edit_message_text(
            update.message.chat.id,
            update.message.id,
            text=caption,
            reply_markup=keyboard,
        )
    else:
        await update.delete()
        await smart_send_photo(
            update.chat.id,
            photo=HELP_IMG_URL,
            caption=caption,
            reply_markup=keyboard,
        )



@app.on_message(filters.command(["help"]) & filters.group & ~filters.user(list(BANNED_USERS)))
@LanguageStart
async def help_com_group(client: Client, message: Message, _):


    if getattr(config, "CLONE_MODE", False):
        await smart_send_photo(
            message.chat.id,
            photo=HELP_IMG_URL,
            caption=_["help_1"].format(clone_support_link()),
            reply_markup=help_main_menu(_),
        )
        return
    keyboard = private_help_panel(_)
    await message.reply_text(
        _["help_2"],
        reply_markup=buttons_to_inline_markup(keyboard),
        disable_web_page_preview=True
    )



@app.on_callback_query(filters.regex(r"^ht_(\d+)_(music|mgmt)_(\d+)$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def help_topic_cb(client: Client, cb: types.CallbackQuery, _):
    number = int(cb.data.split("_")[1])
    prefix = cb.data.split("_")[2]
    page = int(cb.data.split("_")[3])

    if number == 1:
        await smart_edit_message_text(
            cb.message.chat.id, cb.message.id,
            text=_["S_B_M"],
            reply_markup=action_sub_menu(_, f"h_{prefix}_{page}"),
        )
        return

    help_text = getattr(helpers, f"HELP_{number}", None)
    if not help_text:
        from IotaXMedia.utils.god_style import god_text
        return await cb.answer(god_text("Invalid help topic."), show_alert=True)

    await smart_edit_message_text(
        cb.message.chat.id, cb.message.id,
        text=style_help_text(help_text),
        reply_markup=topic_back_markup(_, f"h_{prefix}_{page}"),
    )




@app.on_callback_query(filters.regex(r"^h_(music|mgmt)_(\d+)$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def help_submenu_cb(client: Client, cb: types.CallbackQuery, _):
    prefix = cb.data.split("_")[1]
    page = int(cb.data.split("_")[2])
    is_authorized = _is_authorized(cb.from_user.id)

    if prefix == "music":
        keyboard = help_music_page(_, page, is_authorized)
    else:
        keyboard = help_mgmt_page(_, page, is_authorized)

    await cb.answer()
    await smart_edit_message_text(
        cb.message.chat.id, cb.message.id,
        text=_["help_1"].format(clone_support_link()),
        reply_markup=keyboard,
    )




@app.on_callback_query(filters.regex("^help_main$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def help_main_cb(client: Client, cb: types.CallbackQuery, _):
    await cb.answer()
    await smart_edit_message_text(
        cb.message.chat.id, cb.message.id,
        text=_["help_1"].format(clone_support_link()),
        reply_markup=help_main_menu(_),
    )



@app.on_callback_query(filters.regex("action_prom_1") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def action_prom_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=helpers.HELP_1_PROMO,
        reply_markup=topic_back_markup(_, "help_main"),
    )

@app.on_callback_query(filters.regex("action_pun_1") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def action_pun_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=helpers.HELP_1_PUNISH,
        reply_markup=topic_back_markup(_, "help_main"),
    )



@app.on_callback_query(filters.regex("back_to_main") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def back_to_main_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    out = private_panel(_)
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=_["start_2"].format(
            CallbackQuery.from_user.mention, app.mention
        ),
        reply_markup=out,
    )



@app.on_callback_query(filters.regex("chelp_open") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_open_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_HELP_MENU),
        reply_markup=clone_help_panel(_),
    )


@app.on_callback_query(filters.regex("ccustomize_open") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def ccustomize_open_cb(client: Client, CallbackQuery: types.CallbackQuery, _):




    if not getattr(config, "CLONE_MODE", False):
        return
    await CallbackQuery.answer()
    text = (
            "<blockquote><b>✦ sєᴛᴛɪηɢs ᴄσϻϻᴧηᴅs :</b>\n\n"
            "/setstart — sєᴛ ᴧ ᴄυsᴛσϻ /start ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ.\n"
            "/delstart — ꝛєsєᴛ /start ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ.\n"
            "/setstartmsg TEXT — sєᴛ ᴧ ᴄυsᴛσϻ /start ϻєssᴧɢє.\n"
            "/delstartmsg — ꝛєsєᴛ /start ϻєssᴧɢє ᴛσ ᴅєғᴧυʟᴛ.\n"
            "/setpingpic — sєᴛ ᴧ ᴄυsᴛσϻ /ping ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ.\n"
            "/delpingpic — ꝛєsєᴛ /ping ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ.\n"
            "/setstatspic — sєᴛ ᴧ ᴄυsᴛσϻ /stats ᴘɪᴄᴛυꝛє/ᴠɪᴅєσ.\n"
            "/delstatspic — ꝛєsєᴛ /stats ϻєᴅɪᴧ ᴛσ ᴅєғᴧυʟᴛ.\n"
            "/setchannel LINK — sєᴛ ʏσυꝛ σᴡη υᴘᴅᴧᴛє ᴄʜᴧηηєʟ ʟɪηᴋ.\n"
            "/setsupport LINK — sєᴛ ʏσυꝛ σᴡη sυᴘᴘσꝛᴛ ɢꝛσυᴘ ʟɪηᴋ.\n"
            "/setchannelname NAME — sєᴛ ᴄʜᴧηηєʟ ʙυᴛᴛση ηᴧϻє.\n"
            "/delchannelname — ꝛєsєᴛ ᴄʜᴧηηєʟ ʙυᴛᴛση ηᴧϻє.\n"
            "/setsupportname NAME — sєᴛ sυᴘᴘσꝛᴛ ʙυᴛᴛση ηᴧϻє.\n"
            "/delsupportname — ꝛєsєᴛ sυᴘᴘσꝛᴛ ʙυᴛᴛση ηᴧϻє.\n"
            "/setownername NAME — sєᴛ σᴡηєꝛ ʙυᴛᴛση ηᴧϻє.\n"
            "/delownername — ꝛєsєᴛ σᴡηєꝛ ʙυᴛᴛση ηᴧϻє.\n"
            "/enhelpbtn /dishelpbtn — sʜσᴡ σꝛ ʜɪᴅє ʜєʟᴘ ʙυᴛᴛση.\n"
            "/enclonebtn /disclonebtn — sʜσᴡ σꝛ ʜɪᴅє ᴧᴅᴅ ᴍє ʙυᴛᴛση.\n"
            "/ensupportbtn /dissupportbtn — sʜσᴡ σꝛ ʜɪᴅє sυᴘᴘσꝛᴛ ʙυᴛᴛση.\n"
            "/enchannelbtn /dischannelbtn — sʜσᴡ σꝛ ʜɪᴅє ᴄʜᴧηηєʟ ʙυᴛᴛση.\n"
            "/enownerbtn /disownerbtn — sʜσᴡ σꝛ ʜɪᴅє σᴡηєꝛ ʙυᴛᴛση.\n"
            "/addbtn NAME LINK — ᴧᴅᴅ ᴧ ᴄυsᴛσϻ /start ʙυᴛᴛση.\n"
            "/delbtn NAME — ꝛєϻσᴠє ᴧ ᴄυsᴛσϻ /start ʙυᴛᴛση.\n"
            "/clearbtns — ꝛєϻσᴠє ᴧʟʟ ᴄυsᴛσϻ /start ʙυᴛᴛσηs.\n"
            "/setstring SESSION— sєᴛ ᴧ ᴄυsᴛσϻ ᴧssɪsᴛᴧηᴛ ᴘєꝛsσηᴧʟɪᴛʏ.\n"
            "/delstring — ꝛєsєᴛ ᴧssɪsᴛᴧηᴛ ᴛσ ᴅєғᴧυʟᴛ.\n"
            "/setmongodb URI — sᴛσꝛє ʏσυꝛ ᴄʟσηє's υsєꝛs/ᴄʜᴧᴛs/sєᴛᴛɪηɢs ɪη ʏσυꝛ σᴡη ϻσηɢσᴅʙ.\n"
            "/delmongodb — ꝛєᴠєꝛᴛ ᴛσ ᴛʜє sʜᴧꝛєᴅ ᴅᴧᴛᴧʙᴧsє.\n"
            "/name NAME — sєᴛ ʏσυꝛ ᴄʟσηє'ѕ ʙσᴛ ηᴧϻє.\n"
            "/setlogger — sєᴛ ᴛʜɪs ɢꝛσυᴘ/ᴄʜᴧηηєʟ ᴧs ʏσυꝛ ᴄʟσηє'ѕ ʟσɢ ᴄʜᴧᴛ (ᴧᴅᴅ ϻє ᴧs ᴧᴅϻɪη ғɪꝛsᴛ).\n"
            "/dellogger — ꝛєϻσᴠє ᴛʜє ʟσɢ ᴄʜᴧᴛ ᴧηᴅ ᴅɪsᴧʙʟє ᴧᴄᴛɪᴠɪᴛʏ ʟσɢs."
            "</blockquote>"
        )
    try:
        await CallbackQuery.message.reply_text(text, disable_web_page_preview=True)
    except Exception:
        from IotaXMedia.utils.colored_buttons import smart_send_message

        await smart_send_message(CallbackQuery.message.chat.id, text)


@app.on_callback_query(filters.regex("chelp_start") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_start_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_START),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_ping") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_ping_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_PING),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_stats") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_stats_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_STATS),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_channel") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_channel_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_CHANNEL_SUPPORT),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_assistant") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_assistant_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_ASSISTANT),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_database") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_database_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_DATABASE),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("chelp_extras") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def chelp_extras_cb(client: Client, CallbackQuery: types.CallbackQuery, _):
    await smart_edit_message_text(
        CallbackQuery.message.chat.id,
        CallbackQuery.message.id,
        text=style_help_text(helpers.CLONE_EXTRAS),
        reply_markup=clone_back_markup(_),
    )


@app.on_callback_query(filters.regex("^help_playbtns$") & ~filters.user(list(BANNED_USERS)))
@languageCB
async def help_playbtns_cb(client: Client, cb: types.CallbackQuery, _):
    text = helpers.PLAY_BUTTONS_HELP
    await smart_edit_message_text(
        cb.message.chat.id,
        cb.message.id,
        text=text,
        reply_markup=topic_back_markup(_, "h_mgmt_1"),
    )
