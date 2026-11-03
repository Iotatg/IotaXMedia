
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import json
import os
import traceback
from collections import deque
from datetime import datetime, timezone


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class ErrorCollector:
    def __init__(self, buffer_size: int = 500, history_file: str = "logs/errors.jsonl"):
        self.buffer_size = buffer_size
        self.history_file = history_file
        self.on_record = None
        self._buf = deque()
        self._by_fp = {}
        self._seq = 0
        self._writes = 0
        self._flag = os.path.join(os.path.dirname(history_file) or ".", ".clean_shutdown")
        self._load()
        self._had_crash = (not os.path.exists(self._flag)) and (self.last() is not None)
        try:
            if os.path.exists(self._flag):
                os.remove(self._flag)
        except Exception:
            pass

    def _fingerprint(self, err):
        tb = err.__traceback__
        while tb and tb.tb_next:
            tb = tb.tb_next
        if tb:
            fn = tb.tb_frame.f_code.co_filename
            func = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno
        else:
            fn, func, lineno = "?", "?", 0
        module = os.path.basename(str(fn))
        return f"{type(err).__name__}:{module}.{func}:{lineno}"

    def _next_id(self):
        self._seq += 1
        return f"E{self._seq:06d}"

    def record(self, label, err, tb_text=None, extras=None):
        try:
            if tb_text is None:
                tb_text = "".join(traceback.format_exception(type(err), err, err.__traceback__))
            fp = self._fingerprint(err)
            now = _now_iso()
            rec = self._by_fp.get(fp)
            if rec is not None:
                rec["count"] += 1
                rec["last_seen"] = now
                rec["short_msg"] = str(err)[:300]
                rec["label"] = label
                self._buf = deque(r for r in self._buf if r is not rec)
                self._buf.append(rec)
            else:
                rec = {
                    "id": self._next_id(),
                    "fingerprint": fp,
                    "type": type(err).__name__,
                    "label": label,
                    "short_msg": str(err)[:300],
                    "tb": tb_text,
                    "extras": extras or {},
                    "count": 1,
                    "first_seen": now,
                    "last_seen": now,
                }
                self._by_fp[fp] = rec
                self._buf.append(rec)
                while len(self._buf) > self.buffer_size:
                    old = self._buf.popleft()
                    self._by_fp.pop(old["fingerprint"], None)
            self._append_disk(rec)
            if self.on_record:
                try:
                    self.on_record(rec)
                except Exception:
                    pass
            return rec["id"]
        except Exception:
            return ""

    def _append_disk(self, rec):
        try:
            d = os.path.dirname(self.history_file) or "."
            os.makedirs(d, exist_ok=True)
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._writes += 1
            if self._writes % 500 == 0:
                self._rotate()
        except Exception:
            pass

    def _rotate(self):
        try:
            if not os.path.exists(self.history_file):
                return
            with open(self.history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) <= 50000:
                return
            keep = lines[-50000:]
            tmp = self.history_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.writelines(keep)
            os.replace(tmp, self.history_file)
        except Exception:
            pass

    def _load(self):
        if not os.path.exists(self.history_file):
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    fp = rec.get("fingerprint")
                    if fp:
                        self._by_fp[fp] = rec
            items = sorted(self._by_fp.values(), key=lambda r: r.get("last_seen", ""), reverse=True)
            self._buf = deque(items[: self.buffer_size])
            self._by_fp = {r["fingerprint"]: r for r in self._buf}
            nums = [int(r["id"][1:]) for r in self._by_fp.values()
                    if isinstance(r.get("id"), str) and r["id"][1:].isdigit()]
            self._seq = max(nums) if nums else 0
        except Exception:
            pass

    def recent(self, n=10):
        return list(self._buf)[-n:][::-1]

    def top(self, n=10):
        return sorted(self._by_fp.values(), key=lambda r: r.get("count", 0), reverse=True)[:n]

    def get(self, rec_id):
        for r in self._by_fp.values():
            if r.get("id") == rec_id:
                return r
        return None

    def last(self):
        return self._buf[-1] if self._buf else None

    def mark_clean(self):
        try:
            d = os.path.dirname(self._flag) or "."
            os.makedirs(d, exist_ok=True)
            with open(self._flag, "w") as f:
                f.write(_now_iso())
        except Exception:
            pass

    def had_crash(self):
        return getattr(self, "_had_crash", False)
