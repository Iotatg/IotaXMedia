
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import asyncio
import time
from collections import defaultdict, deque

ALERT_WINDOW = 300
ALERT_COOLDOWN = 600

_PENDING = set()


class AlertManager:
    def __init__(self, threshold=10):
        self.threshold = threshold
        self._buckets = defaultdict(deque)
        self._last_alert = {}

    def check(self, fingerprint, etype):
        now = time.time()
        dq = self._buckets[fingerprint]
        dq.append(now)
        while dq and now - dq[0] > ALERT_WINDOW:
            dq.popleft()
        if len(dq) >= self.threshold:
            last = self._last_alert.get(fingerprint, 0)
            if now - last > ALERT_COOLDOWN:
                self._last_alert[fingerprint] = now
                try:
                    from IotaXMedia.utils.observability.reporter import send_spike
                    t = asyncio.ensure_future(send_spike(fingerprint, etype, len(dq), ALERT_WINDOW))
                    _PENDING.add(t)
                    t.add_done_callback(_PENDING.discard)
                except Exception:
                    pass


alerts = AlertManager()
