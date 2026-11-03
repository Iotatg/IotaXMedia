# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
from typing import Union

from IotaXMedia.misc import db
from IotaXMedia.utils.formatters import check_duration, normalize_duration, seconds_to_min
from config import autoclean, time_to_seconds


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
    owner_app=None,
):
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0



    try:
        if owner_app is None:
            from IotaXMedia import app as _lazy_app

            owner_app = _lazy_app
        from IotaXMedia.core.call import set_chat_owner

        set_chat_owner(chat_id, owner_app.id)
        set_chat_owner(original_chat_id, owner_app.id)
        print(
            f"[OWNER-STAMP] chat={original_chat_id} bot={owner_app.id} "
            f"session={getattr(owner_app, 'name', '?')}",
            flush=True,
        )
    except Exception as e:
        print(f"[OWNER-STAMP] chat={original_chat_id} FAILED: {e!r}", flush=True)
    put = {
        "title": title,
        "dur": normalize_duration(duration),
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        if chat_id not in db:
            db[chat_id] = []
        db[chat_id].append(put)
    autoclean.append(file)
    try:
        from IotaXMedia.plugins.tools.history import push_history
        from IotaXMedia.utils.errors import capture_task_err
        asyncio.create_task(
            capture_task_err("queue.push_history")(push_history)(
                chat_id, title, str(vidid or ""), str(user or "")
            )
        )
    except Exception:
        pass


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
    owner_app=None,
):
    if "20.212.146.162" in vidid:
        try:
            dur = await asyncio.get_event_loop().run_in_executor(
                None, check_duration, vidid
            )
            duration = seconds_to_min(dur)
        except:
            duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
            dur = 0
    else:
        dur = 0
    try:
        if owner_app is None:
            from IotaXMedia import app as _lazy_app

            owner_app = _lazy_app
        from IotaXMedia.core.call import set_chat_owner

        set_chat_owner(chat_id, owner_app.id)
        set_chat_owner(original_chat_id, owner_app.id)
        print(
            f"[OWNER-STAMP] chat={original_chat_id} bot={owner_app.id} "
            f"session={getattr(owner_app, 'name', '?')}",
            flush=True,
        )
    except Exception as e:
        print(f"[OWNER-STAMP] chat={original_chat_id} FAILED: {e!r}", flush=True)
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
    }
    autoclean.append(file)
    if forceplay:
        check = db.get(chat_id)
        if check:
            check.insert(0, put)
        else:
            db[chat_id] = []
            db[chat_id].append(put)
    else:
        db[chat_id].append(put)
