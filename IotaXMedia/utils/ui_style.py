# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Shared output styling: bold headers inside <blockquote> with fancy glyphs."""
from __future__ import annotations

import re

from IotaXMedia.utils.god_style import god_text, god_label, SYM

_TITLE_RE = re.compile(r"^\s*(?:<b>\s*)?(?:<u>)?(.*?)(?:</u>\s*)?(?:</b>)?\s*$", re.I)


def fancy(text: str) -> str:
    """Convert plain text to the IotaXMedia signature glyph set."""
    return god_text(str(text))


def bullet(label: str, desc: str, *, desc_fancy: bool = True) -> str:
    body = fancy(desc) if desc_fancy else desc
    return f"{SYM['arrow']} {label} : {body}"


def section(title: str, body: str, *, expandable: bool = False) -> str:
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    head = f"{SYM['bullet']} <b>{fancy(title)} :</b>"
    if body:
        return f"{tag}{head}\n{body}</blockquote>"
    return f"{tag}{head}</blockquote>"


def note(text: str) -> str:
    return f"<blockquote><b>❏ {fancy(text)}</b></blockquote>"


def button(text: str, *, deco: str = "star") -> str:
    core = god_label(text)
    if deco == "star":
        return f"{SYM['star']} {core}"
    if deco == "seal":
        return f"{SYM['seal']} {core}"
    if deco == "tri":
        return f"{SYM['tri']} {core}"
    return core


def _normalise(text: str) -> str:
    lines = text.strip("\n").splitlines()
    out = []
    header_done = False
    for line in lines:
        stripped = line.strip()
        if not header_done and stripped:
            if stripped.lower().startswith(("<b><u>", "<b>")):
                candidate = re.sub(r"</?b>|</?u>", "", stripped).strip()
                if candidate:
                    if not candidate.startswith((SYM["bullet"], "➤", "⌬", "✧", "♛", "✘", "⚚", "⟁")):
                        candidate = f"{SYM['bullet']} {candidate}"
                    out.append(f"<b>{candidate} :</b>")
                    header_done = True
                    continue
            if stripped.endswith(":") and len(stripped) <= 64 and "<" not in stripped:
                out.append(f"{SYM['bullet']} <b>{stripped}</b>")
                header_done = True
                continue
        if stripped.startswith("• "):
            line = line.replace("• ", f"{SYM['arrow']} ", 1)
        out.append(line)
    return "\n".join(out)


def style_help_text(text: str, *, expandable: bool = False) -> str:
    """Wrap a help block in a bold-header blockquote and normalise bullets."""
    if not text:
        return text
    if "<blockquote" in text:
        return text
    body = _normalise(text)
    tag = "<blockquote expandable>" if expandable else "<blockquote>"
    return f"{tag}{body}</blockquote>"