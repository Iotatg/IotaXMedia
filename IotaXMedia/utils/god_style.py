# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
ULTRA GOD-LEVEL Unicode style (RARE+ edition) for IotaXMedia.

Owner pack locks:
  t → ϯ   a → α   l → ℓ
  plus Old Italic caps, Greek mix, chaos vault ornaments.

HTML tags, {n} slots, URLs, @handles, /commands stay untouched.
"""
from __future__ import annotations

import html
import re
from typing import Optional



_ULTRA_LOWER = {
    "a": "α",
    "b": "ʙ",
    "c": "ᴄ",
    "d": "ᴅ",
    "e": "є",
    "f": "ғ",
    "g": "ɢ",
    "h": "н",
    "i": "ɪ",
    "j": "ᴊ",
    "k": "κ",
    "l": "ℓ",
    "m": "ᴍ",
    "n": "η",
    "o": "σ",
    "p": "ρ",
    "q": "ǫ",
    "r": "ʀ",
    "s": "ѕ",
    "t": "ϯ",
    "u": "υ",
    "v": "ν",
    "w": "ω",
    "x": "χ",
    "y": "γ",
    "z": "ʐ",
}

_ULTRA_UPPER = {
    "A": "𐌀",
    "B": "𐌁",
    "C": "𐌂",
    "D": "𐌃",
    "E": "𐌄",
    "F": "𐌅",
    "G": "Ǥ",
    "H": "𐌇",
    "I": "𐌉",
    "J": "𐌊",
    "K": "𐌋",
    "L": "𐌌",
    "M": "𐌍",
    "N": "𐌍",
    "O": "𐌏",
    "P": "𐌐",
    "Q": "𐌒",
    "R": "𐌓",
    "S": "𐌔",
    "T": "ϯ",
    "U": "𐌖",
    "V": "𐌗",
    "W": "𐌘",
    "X": "𐌙",
    "Y": "𐌚",
    "Z": "𐌛",
}


_SC_TO_ULTRA = {

    "ᴀ": "α",
    "a": "α",
    "α": "α",
    "ɑ": "α",

    "ʙ": "ʙ",
    "b": "ʙ",

    "ᴄ": "ᴄ",
    "c": "ᴄ",
    "ϲ": "ᴄ",

    "ᴅ": "ᴅ",
    "d": "ᴅ",

    "ᴇ": "є",
    "e": "є",
    "є": "є",
    "ɛ": "є",

    "ғ": "ғ",
    "f": "ғ",
    "ꜰ": "ғ",

    "ɢ": "ɢ",
    "g": "ɢ",

    "ʜ": "н",
    "h": "н",
    "н": "н",

    "ɪ": "ɪ",
    "i": "ɪ",
    "ɩ": "ɪ",

    "ᴊ": "ᴊ",
    "j": "ᴊ",

    "ᴋ": "κ",
    "k": "κ",
    "κ": "κ",

    "ʟ": "ℓ",
    "l": "ℓ",
    "ℓ": "ℓ",
    "ʟ": "ℓ",

    "ᴍ": "ᴍ",
    "m": "ᴍ",

    "ɴ": "η",
    "n": "η",
    "η": "η",

    "ᴏ": "σ",
    "o": "σ",
    "σ": "σ",
    "ο": "σ",

    "ᴘ": "ρ",
    "p": "ρ",
    "ρ": "ρ",

    "ǫ": "ǫ",
    "q": "ǫ",
    "ԛ": "ǫ",

    "ʀ": "ʀ",
    "r": "ʀ",

    "s": "ѕ",
    "ꜱ": "ѕ",
    "ѕ": "ѕ",
    "ꜱ": "ѕ",

    "ᴛ": "ϯ",
    "t": "ϯ",
    "τ": "ϯ",
    "ϯ": "ϯ",
    "т": "ϯ",

    "ᴜ": "υ",
    "u": "υ",
    "υ": "υ",

    "ν": "ν",
    "v": "ν",
    "ᴠ": "ν",

    "ᴡ": "ω",
    "w": "ω",
    "ω": "ω",

    "x": "χ",
    "χ": "χ",
    "х": "χ",

    "ʏ": "γ",
    "y": "γ",
    "γ": "γ",

    "ᴢ": "ʐ",
    "z": "ʐ",
    "ʐ": "ʐ",
}


SYM = {
    "star": "𖤍",
    "seal": "⚚",
    "tri": "⟁",
    "delta": "⌬",
    "flower": "⚘",
    "spark": "✧",
    "frame_tl": "╔",
    "frame_tr": "╗",
    "frame_bl": "╚",
    "frame_br": "╝",
    "frame_h": "═",
    "frame_v": "║",
    "dash": "━━",
    "arrow": "⇢",
    "bullet": "✦",
    "cross": "✘",
    "crown": "♛",
    "fleur": "⚜️",
    "yin": "☯",
    "khanda": "☬",
    "skull": "༒︎",
    "pent": "𖤐",
    "sun": "𖤓",
    "moon": "𖤏",
    "node": "𖤎",
    "brace_l": "⟆",
    "brace_r": "⟅",
    "angle_l": "⫷",
    "angle_r": "⫸",
    "bolt": "⚡",
    "diamond": "⟡",
}

_DIGITS = {
    "0": "⓿",
    "1": "❶",
    "2": "❷",
    "3": "❸",
    "4": "❹",
    "5": "❺",
    "6": "❻",
    "7": "❼",
    "8": "❽",
    "9": "❾",
}

_PROTECT = re.compile(
    r"("
    r"<[^>]+>"
    r"|&[a-zA-Z]+;"
    r"|&#\d+;"
    r"|&#x[0-9a-fA-F]+;"
    r"|\{[0-9]+\}"
    r"|https?://[^\s<>\"']+"
    r"|t\.me/[^\s<>\"']+"
    r"|@[A-Za-z0-9_]{3,}"

    r"|(?<![A-Za-z0-9_])/[A-Za-z][A-Za-z0-9_]*"
    r"|`[^`]*`"
    r")"
)


_GOD_LOWER = _ULTRA_LOWER
_GOD_UPPER = _ULTRA_UPPER
_SC_TO_GOD = _SC_TO_ULTRA


def _map_char(ch: str, *, title: bool = False) -> str:
    if ch in _ULTRA_LOWER:
        return _ULTRA_LOWER[ch]
    if ch in _ULTRA_UPPER:
        return _ULTRA_UPPER[ch] if title else _ULTRA_LOWER.get(ch.lower(), ch)
    if ch in _SC_TO_ULTRA:
        return _SC_TO_ULTRA[ch]
    if ch.isalpha():
        low = ch.lower()
        if low in _ULTRA_LOWER:
            return _ULTRA_LOWER[low]
    return ch


def _ultra_chunk(chunk: str, *, fancy_digits: bool = False) -> str:
    out = []
    for ch in chunk:
        if ch.isupper() and ch.isalpha():
            out.append(_map_char(ch, title=True))
        elif ch.islower() or ch in _SC_TO_ULTRA or ch in _ULTRA_LOWER:
            out.append(_map_char(ch, title=False))
        elif fancy_digits and ch.isdigit():
            out.append(_DIGITS.get(ch, ch))
        elif ch in _SC_TO_ULTRA:
            out.append(_SC_TO_ULTRA[ch])
        else:
            out.append(ch)
    return "".join(out)


def god_text(text: str, *, fancy_digits: bool = False, protect: bool = True) -> str:
    """ULTRA convert free text; preserves protected spans. Alias: ultra_text."""
    if not text:
        return text
    if not protect:
        return _ultra_chunk(text, fancy_digits=fancy_digits)
    parts = []
    last = 0
    for m in _PROTECT.finditer(text):
        parts.append(_ultra_chunk(text[last : m.start()], fancy_digits=fancy_digits))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_ultra_chunk(text[last:], fancy_digits=fancy_digits))
    return "".join(parts)


ultra_text = god_text


def god_text_raw(text: str, *, fancy_digits: bool = False) -> str:
    """ULTRA convert with no URL/command protection (menu labels, bot cmds)."""
    return god_text(text, fancy_digits=fancy_digits, protect=False)


def god_label(text: str) -> str:
    return god_text_raw(text, fancy_digits=False)


ultra_label = god_label

_KEEP_HTML = re.compile(
    r"</?(?:b|strong|i|em|u|ins|s|strike|del|code|pre|a|blockquote|tg-spoiler|tg-emoji)(?:\s[^<>]*)?>"
    r"|&(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);",
    re.I,
)
_MATH_BOLD = {chr(65 + i): chr(0x1D400 + i) + "\u200c" for i in range(26)}


def _escape_stray_html(text: str) -> str:
    if not text:
        return text
    parts = []
    last = 0
    for m in _KEEP_HTML.finditer(text):
        parts.append(text[last : m.start()].replace("&", "&amp;").replace("<", "&lt;"))
        parts.append(m.group(0))
        last = m.end()
    parts.append(text[last:].replace("&", "&amp;").replace("<", "&lt;"))
    return "".join(parts)


def _zip_chunk(chunk: str) -> str:
    out = []
    for ch in chunk:
        if "A" <= ch <= "Z":
            out.append(_MATH_BOLD[ch])
        elif ch in _ULTRA_LOWER:
            out.append(_ULTRA_LOWER[ch])
        else:
            out.append(ch)
    return "".join(out)


def fancy_output(text: Optional[str]) -> Optional[str]:
    """Convert plain ASCII letters of outgoing text to zip-style unicode.

    HTML tags, entities, URLs, @handles and /commands stay untouched.
    Stray ``<`` / ``&`` are escaped so parse_mode=HTML does not swallow
    usage placeholders. Already-styled (non-ASCII) letters are left as-is.
    """
    if not text or not isinstance(text, str):
        return text
    text = _escape_stray_html(text)
    parts = []
    last = 0
    for m in _PROTECT.finditer(text):
        parts.append(_zip_chunk(text[last : m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_zip_chunk(text[last:]))
    return "".join(parts)




def tag_fire_vibes() -> str:
    return f"{SYM['brace_l']}{SYM['bolt']}{SYM['pent']}𐌅ɪʀє_ᴠɪʙєѕ{SYM['pent']}{SYM['bolt']}{SYM['brace_l']}"


def tag_soul_king() -> str:
    return f"{SYM['delta']}{SYM['crown']}{SYM['sun']}𐌔συℓ_κɪηɢ{SYM['sun']}{SYM['crown']}{SYM['delta']}"


def tag_dark_flow() -> str:
    return f"{SYM['tri']}{SYM['khanda']}{SYM['moon']}ᴅαʀκ_𐌅ℓσω{SYM['moon']}{SYM['khanda']}{SYM['tri']}"


def chaos_banner(inner: str) -> str:
    """CHAOS++ wrapper around already-styled or plain text."""
    core = god_text(inner) if inner.isascii() else inner
    return (
        f"{SYM['skull']}{SYM['star']}{SYM['seal']}{SYM['tri']}"
        f"{core}"
        f"{SYM['tri']}{SYM['seal']}{SYM['star']}{SYM['skull']}"
    )


def queue_card(position, title: str, duration: str, requester: str) -> str:
    """ULTRA GOD signature — added to queue frame (ϯ + α)."""
    pos = str(position)
    pos_f = _DIGITS.get(pos, pos) if len(pos) == 1 else pos
    head = god_text("added to queue")
    t = god_text("title")
    d = god_text("duration")
    r = god_text("requested by")
    now = god_text("now playing")
    foot = god_text("vibes on")
    return (
        f"{SYM['frame_tl']}{SYM['frame_h']}{SYM['dash']}"
        f"{SYM['star']}{SYM['seal']}{SYM['tri']}"
        f"{head} {SYM['arrow']} {pos_f}"
        f"{SYM['tri']}{SYM['seal']}{SYM['star']}"
        f"{SYM['dash']}{SYM['frame_h']}{SYM['frame_tr']}\n"
        f"{SYM['frame_v']} {SYM['spark']} {t}: 『{title}』{SYM['spark']} {SYM['frame_v']}\n"
        f"{SYM['frame_v']} {SYM['delta']} {d}: {duration} {SYM['delta']} {SYM['frame_v']}\n"
        f"{SYM['frame_v']} {SYM['tri']} {r}: −『{requester}』{SYM['tri']} {SYM['frame_v']}\n"
        f"{SYM['frame_v']} {SYM['flower']} {now} {SYM['flower']} {SYM['frame_v']}\n"
        f"{SYM['frame_bl']}{SYM['frame_h']}{SYM['dash']}"
        f"{SYM['star']}{SYM['seal']}{SYM['tri']}{foot}"
        f"{SYM['tri']}{SYM['seal']}{SYM['star']}"
        f"{SYM['dash']}{SYM['frame_h']}{SYM['frame_br']}"
    )


def stream_card(
    title: str,
    duration: str,
    requester: str,
    *,
    title_url: Optional[str] = None,
    requester_id: Optional[int] = None,
    stream_type: Optional[str] = None,
) -> str:
    """ULTRA now-playing / started streaming inline."""



    title = str(title) if title is not None else ""
    requester = str(requester) if requester is not None else ""
    duration = str(duration) if duration is not None else ""
    t = god_text("title")
    d = god_text("duration")
    r = god_text("requested by")
    ty = god_text("stream type")
    head = god_text("started streaming")
    title_disp = (
        f'<a href="{title_url}">{html.escape(title)}</a>' if title_url else title
    )

    anon_label = god_text("anonymous")
    is_anon = requester in (anon_label, "anonymous") or requester.lower() == "anonymous"
    if requester_id and not is_anon:
        requester_disp = (
            f'<a href="tg://user?id={requester_id}">{html.escape(requester)}</a>'
        )
    else:
        requester_disp = html.escape(requester)
    body = (
        f"{head}:\n\n"
        f"{SYM['spark']} {t}: 『{title_disp}』\n"
        f"{SYM['delta']} {d}: {duration}\n"
        f"{SYM['tri']} {r}: {requester_disp}"
    )
    if stream_type:
        body += f"\n{SYM['pent']} {ty}: {stream_type}"
    return body


def player_card(
    bot_name: str,
    title: str,
    stream_type: str,
    requester: str,
    extra: str = "",
) -> str:
    head = god_text("player")
    st = god_text("streaming")
    ty = god_text("stream type")
    rq = god_text("requested by")
    return (
        f"{SYM['star']}{SYM['seal']}{SYM['pent']} "
        f"<b>{bot_name} {head}</b> "
        f"{SYM['pent']}{SYM['seal']}{SYM['star']}\n\n"
        f"{SYM['spark']} <b>{st} :</b> {title}\n"
        f"{SYM['delta']} <b>{ty} :</b> {stream_type}\n"
        f"{SYM['tri']} <b>{rq} :</b> {requester}\n"
        f"{extra}"
    )


def btn(text: str, *, deco: str = "") -> str:
    core = god_label(text)
    if deco == "close":
        return f"๏ {core} ๏"
    if deco == "back":
        return f"๏ {core} ๏"
    if deco == "star":
        return f"{SYM['star']} {core} {SYM['star']}"
    if deco == "seal":
        return f"{SYM['seal']} {core} {SYM['seal']}"
    if deco == "tri":
        return f"{SYM['tri']} {core} {SYM['tri']}"
    if deco == "ultra":
        return f"{SYM['pent']} {core} {SYM['pent']}"
    if deco == "chaos":
        return f"{SYM['skull']} {core} {SYM['skull']}"
    return core



BTN_CLOSE = btn("close", deco="close")
BTN_BACK = btn("back", deco="back")
BTN_AUDIO = f"αυᴅɪσ {SYM['spark']}"
BTN_VIDEO = f"νɪᴅєσ {SYM['delta']}"
BTN_LIVE = f"ℓɪνє ѕϯʀєαᴍ {SYM['tri']}"
BTN_QUEUE = f"{SYM['seal']} ǫυєυє"
BTN_CHANNEL = f"🍂 {god_label('channel')} 🍂"
BTN_SUPPORT = f"❄️{god_label('support')}❄️"
BTN_HELP = f"{god_label('help')} & {god_label('commands')} ❓"
BTN_SOURCE = f"💗 {god_label('source code')} 💗"
BTN_ADD = f"˹{god_label('kidnap me babes')}˼"
BTN_ULTRA = f"{SYM['star']}{SYM['seal']} Uℓϯʀα Gσᴅ {SYM['seal']}{SYM['star']}"
