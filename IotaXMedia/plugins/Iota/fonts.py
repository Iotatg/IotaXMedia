# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import enums
from IotaXMedia.utils.font_styles import Fonts
from IotaXMedia import app
from IotaXMedia.utils.colored_buttons import (
    edit_reply_markup_colored,
    send_message_colored,
    styled_button,
)


@app.on_message(filters.command(["font", "fonts"]))
async def style_buttons(c, m, cb=False):
    if cb:
        message = m.message
        text = message.text.replace("`", "")
    else:
        if len(m.command) < 2:
            return await m.reply("❌ Please provide text to style.\n\nExample: `/font Hello World!`", quote=True)
        message = m
        text = m.text.split(" ", 1)[1]

    buttons = [
        [
            InlineKeyboardButton("𖤍 Uℓϯʀα Gσᴅ", callback_data="style+ultra", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="style+typewriter", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="style+outline", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("𝐒𝐞𝐫𝐢𝐟", callback_data="style+serif", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝑺𝒆𝒓𝒊𝒇", callback_data="style+bold_cool", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝑆𝑒𝑟𝑖𝑓", callback_data="style+cool", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("Sᴍᴀʟʟ Cᴀᴘs", callback_data="style+small_cap", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="style+script", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="style+script_bolt", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("ᵗⁱⁿʸ", callback_data="style+tiny", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("ᑕOᗰIᑕ", callback_data="style+comic", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝗦𝗮𝗻𝘀", callback_data="style+sans", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("𝙎𝙖𝙣𝙨", callback_data="style+slant_sans", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝘚𝘢𝘯𝘴", callback_data="style+slant", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝖲𝖺𝗇𝗌", callback_data="style+sim", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", callback_data="style+circles", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("🅒︎🅘︎🅡︎🅒︎🅛︎🅔︎🅢︎", callback_data="style+circle_dark", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="style+gothic", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="style+gothic_bolt", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", callback_data="style+cloud", style=enums.ButtonStyle.PRIMARY),
            InlineKeyboardButton("H̆̈ă̈p̆̈p̆̈y̆̈", callback_data="style+happy", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("S̑̈ȃ̈d̑̈", callback_data="style+sad", style=enums.ButtonStyle.PRIMARY),
        ],
        [
            InlineKeyboardButton("๏ ᴄℓσѕє ๏", callback_data="close_reply", style=enums.ButtonStyle.DANGER),
            InlineKeyboardButton("ηєχϯ ➻", callback_data="nxt", style=enums.ButtonStyle.PRIMARY),
        ],
    ]

    buttons_col = [
        [
            styled_button("𖤍 Uℓϯʀα Gσᴅ", callback_data="style+ultra", style="primary"),
            styled_button("𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛", callback_data="style+typewriter", style="primary"),
            styled_button("𝕆𝕦𝕥𝕝𝕚𝕟𝕖", callback_data="style+outline", style="primary"),
        ],
        [
            styled_button("𝐒𝐞𝐫𝐢𝐟", callback_data="style+serif", style="primary"),
            styled_button("𝑺𝒆𝒓𝒊𝒇", callback_data="style+bold_cool", style="primary"),
            styled_button("𝑆𝑒𝑟𝑖𝑓", callback_data="style+cool", style="primary"),
        ],
        [
            styled_button("Sᴍᴀʟʟ Cᴀᴘs", callback_data="style+small_cap", style="primary"),
            styled_button("𝓈𝒸𝓇𝒾𝓅𝓉", callback_data="style+script", style="primary"),
            styled_button("𝓼𝓬𝓻𝓲𝓹𝓽", callback_data="style+script_bolt", style="primary"),
        ],
        [
            styled_button("ᵗⁱⁿʸ", callback_data="style+tiny", style="primary"),
            styled_button("ᑕOᗰIᑕ", callback_data="style+comic", style="primary"),
            styled_button("𝗦𝗮𝗻𝘀", callback_data="style+sans", style="primary"),
        ],
        [
            styled_button("𝙎𝙖𝙣𝙨", callback_data="style+slant_sans", style="primary"),
            styled_button("𝘚𝘢𝘯𝘴", callback_data="style+slant", style="primary"),
            styled_button("𝖲𝖺𝗇𝗌", callback_data="style+sim", style="primary"),
        ],
        [
            styled_button("Ⓒ︎Ⓘ︎Ⓡ︎Ⓒ︎Ⓛ︎Ⓔ︎Ⓢ︎", callback_data="style+circles", style="primary"),
            styled_button("🅒︎🅘︎🅡︎🅒︎🅛︎🅔︎🅢︎", callback_data="style+circle_dark", style="primary"),
            styled_button("𝔊𝔬𝔱𝔥𝔦𝔠", callback_data="style+gothic", style="primary"),
        ],
        [
            styled_button("𝕲𝖔𝖙𝖍𝖎𝖈", callback_data="style+gothic_bolt", style="primary"),
            styled_button("C͜͡l͜͡o͜͡u͜͡d͜͡s͜͡", callback_data="style+cloud", style="primary"),
            styled_button("H̆̈ă̈p̆̈p̆̈y̆̈", callback_data="style+happy", style="primary"),
        ],
        [
            styled_button("S̑̈ȃ̈d̑̈", callback_data="style+sad", style="primary"),
        ],
        [
            styled_button("๏ ᴄℓσѕє ๏", callback_data="close_reply", style="danger"),
            styled_button("ηєχϯ ➻", callback_data="nxt", style="primary"),
        ],
    ]

    if cb:
        try:
            r = await edit_reply_markup_colored(m.message.chat.id, m.message.id, buttons_col)
            if r:
                return
        except Exception:
            pass
        await m.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    else:
        try:
            r = await send_message_colored(
                m.chat.id, f"`{text}`", buttons_col, parse_mode="markdown"
            )
            if r:
                return
        except Exception:
            pass
        await m.reply_text(f"`{text}`", reply_markup=InlineKeyboardMarkup(buttons), quote=True)



@app.on_callback_query(filters.regex("^nxt"))
async def nxt(c, m):
    await m.answer()
    if m.data == "nxt":
        buttons = [
            [
                InlineKeyboardButton("🇸 🇵 🇪 🇨 🇮 🇦 🇱 ", callback_data="style+special", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("🅂🅀🅄🄰🅁🄴🅂", callback_data="style+squares", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", callback_data="style+squares_bold", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", callback_data="style+andalucia", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("爪卂几ᘜ卂", callback_data="style+manga", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("S̾t̾i̾n̾k̾y̾", callback_data="style+stinky", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", callback_data="style+bubbles", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("U͟n͟d͟e͟r͟l͟i͟n͟e͟", callback_data="style+underline", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("꒒ꍏꀷꌩꌃꀎꁅ", callback_data="style+ladybug", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("R҉a҉y҉s҉", callback_data="style+rays", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("B҈i҈r҈d҈s҈", callback_data="style+birds", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("S̸l̸a̸s̸h̸", callback_data="style+slash", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("s⃠t⃠o⃠p⃠", callback_data="style+stop", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", callback_data="style+skyline", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("A͎r͎r͎o͎w͎s͎", callback_data="style+arrows", style=enums.ButtonStyle.PRIMARY),
            ],
            [
                InlineKeyboardButton("ዪሀክቿነ", callback_data="style+qvnes", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("S̶t̶r̶i̶k̶e̶", callback_data="style+strike", style=enums.ButtonStyle.PRIMARY),
                InlineKeyboardButton("F༙r༙o༙z༙e༙n༙", callback_data="style+frozen", style=enums.ButtonStyle.PRIMARY),
            ],
            [InlineKeyboardButton("๏ ᴄℓσѕє ๏", callback_data="close_reply", style=enums.ButtonStyle.DANGER), InlineKeyboardButton("๏ ʙαᴄκ ๏", callback_data="nxt+0", style=enums.ButtonStyle.PRIMARY)],
        ]
        buttons_col = [
            [
                styled_button("🇸 🇵 🇪 🇨 🇮 🇦 🇱 ", callback_data="style+special", style="primary"),
                styled_button("🅂🅀🅄🄰🅁🄴🅂", callback_data="style+squares", style="primary"),
                styled_button("🆂︎🆀︎🆄︎🅰︎🆁︎🅴︎🆂︎", callback_data="style+squares_bold", style="primary"),
            ],
            [
                styled_button("ꪖꪀᦔꪖꪶꪊᥴ𝓲ꪖ", callback_data="style+andalucia", style="primary"),
                styled_button("爪卂几ᘜ卂", callback_data="style+manga", style="primary"),
                styled_button("S̾t̾i̾n̾k̾y̾", callback_data="style+stinky", style="primary"),
            ],
            [
                styled_button("B̥ͦu̥ͦb̥ͦb̥ͦl̥ͦe̥ͦs̥ͦ", callback_data="style+bubbles", style="primary"),
                styled_button("U͟n͟d͟e͟r͟l͟i͟n͟e͟", callback_data="style+underline", style="primary"),
                styled_button("꒒ꍏꀷꌩꌃꀎꁅ", callback_data="style+ladybug", style="primary"),
            ],
            [
                styled_button("R҉a҉y҉s҉", callback_data="style+rays", style="primary"),
                styled_button("B҈i҈r҈d҈s҈", callback_data="style+birds", style="primary"),
                styled_button("S̸l̸a̸s̸h̸", callback_data="style+slash", style="primary"),
            ],
            [
                styled_button("s⃠t⃠o⃠p⃠", callback_data="style+stop", style="primary"),
                styled_button("S̺͆k̺͆y̺͆l̺͆i̺͆n̺͆e̺͆", callback_data="style+skyline", style="primary"),
                styled_button("A͎r͎r͎o͎w͎s͎", callback_data="style+arrows", style="primary"),
            ],
            [
                styled_button("ዪሀክቿነ", callback_data="style+qvnes", style="primary"),
                styled_button("S̶t̶r̶i̶k̶e̶", callback_data="style+strike", style="primary"),
                styled_button("F༙r༙o༙z༙e༙n༙", callback_data="style+frozen", style="primary"),
            ],
            [styled_button("๏ ᴄℓσѕє ๏", callback_data="close_reply", style="danger"), styled_button("๏ ʙαᴄκ ๏", callback_data="nxt+0", style="primary")],
        ]
        try:
            r = await edit_reply_markup_colored(m.message.chat.id, m.message.id, buttons_col)
            if r:
                return
        except Exception:
            pass
        await m.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    else:
        await style_buttons(c, m, cb=True)

@app.on_callback_query(filters.regex("^style"))
async def style(c, m):
    await m.answer()
    _, style = m.data.split('+')

    style_map = {
        "ultra": Fonts.god,
        "god": Fonts.god,
        "typewriter": Fonts.typewriter,
        "outline": Fonts.outline,
        "serif": Fonts.serief,
        "bold_cool": Fonts.bold_cool,
        "cool": Fonts.cool,
        "small_cap": Fonts.smallcap,
        "script": Fonts.script,
        "script_bolt": Fonts.bold_script,
        "tiny": Fonts.tiny,
        "comic": Fonts.comic,
        "sans": Fonts.san,
        "slant_sans": Fonts.slant_san,
        "slant": Fonts.slant,
        "sim": Fonts.sim,
        "circles": Fonts.circles,
        "circle_dark": Fonts.dark_circle,
        "gothic": Fonts.gothic,
        "gothic_bolt": Fonts.bold_gothic,
        "cloud": Fonts.cloud,
        "happy": Fonts.happy,
        "sad": Fonts.sad,
        "special": Fonts.special,
        "squares": Fonts.square,
        "squares_bold": Fonts.dark_square,
        "andalucia": Fonts.andalucia,
        "manga": Fonts.manga,
        "stinky": Fonts.stinky,
        "bubbles": Fonts.bubbles,
        "underline": Fonts.underline,
        "ladybug": Fonts.ladybug,
        "rays": Fonts.rays,
        "birds": Fonts.birds,
        "slash": Fonts.slash,
        "stop": Fonts.stop,
        "skyline": Fonts.skyline,
        "arrows": Fonts.arrows,
        "qvnes": Fonts.rvnes,
        "strike": Fonts.strike,
        "frozen": Fonts.frozen,
    }

    cls = style_map.get(style)
    if not cls:
        return await m.message.reply("❌ Unknown style type.")

    if not m.message.reply_to_message or not m.message.reply_to_message.text:
        return await m.message.reply("❌ Please reply to a text message to stylize it.")

    try:
        text = m.message.reply_to_message.text.split(" ", 1)[1]
    except IndexError:
        text = m.message.reply_to_message.text

    stylized = cls(text)
    await m.message.edit_text(stylized, reply_markup=m.message.reply_markup)
