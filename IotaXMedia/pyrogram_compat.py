# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""Make pyrogram error imports resilient to build mismatches.

Some pyrogram 2.0.x wheels (e.g. the one pulled by certain Render build
images) omit recently-added Telegram errors such as ``ChatSendPlainForbidden``.
Importing those with ``from pyrogram.errors import X`` then raises ImportError
and aborts plugin loading.

We add a module-level ``__getattr__`` so any *missing* error name resolves to a
synthetic exception that is a subclass of pyrogram's ``RPCError``. Real Telegram
errors are always ``RPCError`` subclasses, so ``except X`` clauses keep catching
them correctly. Names that genuinely exist in the installed pyrogram are returned
normally and never touch this shim.
"""
import pyrogram.errors as _errors

_cache: dict = {}


def _missing(name: str):
    if name in _cache:
        return _cache[name]
    cls = type(name, (_errors.RPCError,), {"__module__": "pyrogram.errors"})
    _cache[name] = cls
    return cls


if not hasattr(_errors, "__getattr__"):
    try:
        _errors.__getattr__ = _missing
    except Exception:
        pass










import pyrogram.raw.types as _raw_types

_raw_cache: dict = {}


def _missing_raw_type(name: str):
    if name in _raw_cache:
        return _raw_cache[name]
    cls = type(
        name,
        (),
        {
            "__module__": "pyrogram.raw.types",
            "__init__": lambda self, **kwargs: self.__dict__.update(kwargs),
        },
    )
    _raw_cache[name] = cls
    return cls


if not hasattr(_raw_types, "__getattr__"):
    try:
        _raw_types.__getattr__ = _missing_raw_type
    except Exception:
        pass

if not hasattr(_raw_types, "InputGroupCallSlug"):
    try:
        _raw_types.InputGroupCallSlug = _missing_raw_type("InputGroupCallSlug")
    except Exception:
        pass










import pyrogram.raw.functions.phone.join_group_call as _jgc_mod
import pyrogram.raw.functions.phone as _phone_mod
from io import BytesIO as _BytesIO
from pyrogram.raw.core.primitives import Int as _Int, String as _String
from pyrogram.raw.core import TLObject as _TLObject

_JGC = _jgc_mod.JoinGroupCall


class _JoinGroupCallPatched(_JGC):
    __slots__ = ["public_key"]

    def __init__(self, *, call, join_as, params, muted=None, video_stopped=None,
                 invite_hash=None, public_key=None):
        super().__init__(
            call=call,
            join_as=join_as,
            params=params,
            muted=muted,
            video_stopped=video_stopped,
            invite_hash=invite_hash,
        )
        self.public_key = public_key

    @staticmethod
    def read(b):
        flags = _Int.read(b)
        muted = True if flags & (1 << 0) else False
        video_stopped = True if flags & (1 << 2) else False
        call = _TLObject.read(b)
        join_as = _TLObject.read(b)
        invite_hash = _String.read(b) if flags & (1 << 1) else None
        public_key = _String.read(b) if flags & (1 << 3) else None
        params = _TLObject.read(b)
        return _JoinGroupCallPatched(
            call=call,
            join_as=join_as,
            params=params,
            muted=muted,
            video_stopped=video_stopped,
            invite_hash=invite_hash,
            public_key=public_key,
        )

    def write(self):
        b = _BytesIO()
        b.write(_Int(self.ID, False))
        flags = 0
        flags |= (1 << 0) if self.muted else 0
        flags |= (1 << 2) if self.video_stopped else 0
        flags |= (1 << 1) if self.invite_hash is not None else 0
        flags |= (1 << 3) if self.public_key is not None else 0
        b.write(_Int(flags))
        b.write(self.call.write())
        b.write(self.join_as.write())
        if self.invite_hash is not None:
            b.write(_String(self.invite_hash))
        if self.public_key is not None:
            b.write(_String(str(self.public_key)))
        b.write(self.params.write())
        return b.getvalue()


if _jgc_mod.JoinGroupCall is _JGC:
    _jgc_mod.JoinGroupCall = _JoinGroupCallPatched
    if getattr(_phone_mod, "JoinGroupCall", None) is _JGC:
        _phone_mod.JoinGroupCall = _JoinGroupCallPatched








import pyrogram.utils as _pyroutils

_orig_parse_text_entities = getattr(_pyroutils, "parse_text_entities", None)


async def _parse_text_entities_compat(client, text, parse_mode, entities):
    if isinstance(parse_mode, str):
        from pyrogram import enums as _pgenums

        _pmap = {
            "html": getattr(_pgenums.ParseMode, "HTML", None),
            "markdown": getattr(_pgenums.ParseMode, "MARKDOWN", None),


            "markdownv2": getattr(_pgenums.ParseMode, "MARKDOWNV2", None)
            or getattr(_pgenums.ParseMode, "MARKDOWN_V2", None),
        }
        parse_mode = _pmap.get(parse_mode.lower()) or parse_mode
    return await _orig_parse_text_entities(client, text, parse_mode, entities)


if _orig_parse_text_entities is not None:
    try:
        _pyroutils.parse_text_entities = _parse_text_entities_compat
    except Exception:
        pass










import inspect as _inspect
from enum import Enum as _Enum


class _ButtonStyleShim(_Enum):
    DEFAULT = "default"
    PRIMARY = "primary"
    DANGER = "danger"
    SUCCESS = "success"

    def __repr__(self):
        return f"pyrogram.enums.ButtonStyle.{self.name}"


import pyrogram.enums as _pgenums

if not hasattr(_pgenums, "ButtonStyle"):
    _pgenums.ButtonStyle = _ButtonStyleShim
    try:
        _pg_all = getattr(_pgenums, "__all__", None)
        if isinstance(_pg_all, list) and "ButtonStyle" not in _pg_all:
            _pg_all.append("ButtonStyle")
    except Exception:
        pass


def _write_style_shim(self, client):
    """Serialize a button that carries a colored ``style``.

    Falls back to the stock writer when no style is set, so this is a no-op on
    builds (kurigram) that already support colors. Style is emitted as a
    ``KeyboardButtonStyle`` raw type only when the installed layer exposes it.
    """
    if getattr(self, "style", None) in (None, _ButtonStyleShim.DEFAULT):
        return _orig_ikb_write(self, client)

    _style = self.style
    _rt = None
    _raw_style = None
    try:
        import pyrogram.raw.types as _rt_mod

        _rt = _rt_mod
        _kbs = getattr(_rt, "KeyboardButtonStyle", None)
        if _kbs is not None:
            _raw_style = _kbs(
                bg_primary=_style == _ButtonStyleShim.PRIMARY,
                bg_danger=_style == _ButtonStyleShim.DANGER,
                bg_success=_style == _ButtonStyleShim.SUCCESS,
            )
    except Exception:
        _raw_style = None

    if _raw_style is None or _rt is None:
        return _orig_ikb_write(self, client)



    try:
        if self.callback_data is not None:
            data = (
                bytes(self.callback_data, "utf-8")
                if isinstance(self.callback_data, str)
                else self.callback_data
            )
            return _rt.KeyboardButtonCallback(
                text=self.text, data=data, style=_raw_style
            )
        if self.url is not None:
            return _rt.KeyboardButtonUrl(
                text=self.text, url=self.url, style=_raw_style
            )
    except Exception:
        pass
    return _orig_ikb_write(self, client)


try:
    from pyrogram.types import InlineKeyboardButton as _IKB

    _ikb_params = _inspect.signature(_IKB.__init__).parameters
    if "style" not in _ikb_params:
        _orig_ikb_init = _IKB.__init__

        def _ikb_init(self, *args, style=None, **kwargs):
            _orig_ikb_init(self, *args, **kwargs)
            self.style = style

        _IKB.__init__ = _ikb_init

        _orig_ikb_write = getattr(_IKB, "write", None)
        if _orig_ikb_write is not None:
            _IKB.write = _write_style_shim
        _IKB._iota_style_shim = True
except Exception:
    pass







_MEDIA_FLAGS = (
    "can_send_audios",
    "can_send_documents",
    "can_send_photos",
    "can_send_videos",
    "can_send_video_notes",
    "can_send_voice_notes",
)


def _patch_init_drop_unknown(cls, collapse_media=False):
    if getattr(cls, "_iota_kwargs_shim", False):
        return
    try:
        params = _inspect.signature(cls.__init__).parameters
    except (TypeError, ValueError):
        return
    known = set(params) - {"self"}
    if collapse_media and all(f in known for f in _MEDIA_FLAGS):
        return
    if not collapse_media and "can_manage_topics" in known:
        return
    orig = cls.__init__

    def _init(self, *args, **kwargs):
        extra = {k: kwargs.pop(k) for k in list(kwargs) if k not in known}
        if collapse_media and "can_send_media_messages" not in kwargs:
            media_vals = [extra[k] for k in _MEDIA_FLAGS if k in extra]
            if media_vals:
                if any(v is True for v in media_vals):
                    kwargs["can_send_media_messages"] = True
                elif all(v is False for v in media_vals):
                    kwargs["can_send_media_messages"] = False
        orig(self, *args, **kwargs)
        for k, v in extra.items():
            setattr(self, k, v)

    cls.__init__ = _init
    cls._iota_kwargs_shim = True


try:
    from pyrogram.types import ChatPermissions as _CP

    _patch_init_drop_unknown(_CP, collapse_media=True)
except Exception:
    pass

try:
    from pyrogram.types import ChatPrivileges as _CPriv

    _patch_init_drop_unknown(_CPriv, collapse_media=False)
except Exception:
    pass
