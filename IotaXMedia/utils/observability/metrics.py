
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import time
import threading


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {}
        self._gauges = {}
        self._start = time.time()
        self._api_lat = []
        self._err_times = []
        self._lat_lock = threading.Lock()

    def inc(self, name, by=1):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + by

    def gauge(self, name, value):
        with self._lock:
            self._gauges[name] = value

    def record_error(self):
        self.inc("errors_total")
        with self._lat_lock:
            self._err_times.append(time.time())
            if len(self._err_times) > 1000:
                self._err_times.pop(0)

    def record_api_latency(self, ms):
        with self._lat_lock:
            self._api_lat.append(ms)
            if len(self._api_lat) > 200:
                self._api_lat.pop(0)

    def api_latency_avg(self):
        with self._lat_lock:
            return sum(self._api_lat) / len(self._api_lat) if self._api_lat else 0.0

    def error_rate(self, window=300):
        now = time.time()
        with self._lat_lock:
            return sum(1 for t in self._err_times if now - t <= window)

    def uptime(self):
        return time.time() - self._start

    def snapshot(self):
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges), "uptime": self.uptime()}
