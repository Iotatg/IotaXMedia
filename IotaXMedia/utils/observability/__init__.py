
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import atexit

from config import (
    OBSERVABILITY,
    ERROR_HISTORY_FILE,
    ERROR_BUFFER_SIZE,
    ERROR_RATE_ALERT_THRESHOLD,
)

from .collector import ErrorCollector
from .metrics import Metrics
from .alerts import alerts

collector = ErrorCollector(buffer_size=ERROR_BUFFER_SIZE, history_file=ERROR_HISTORY_FILE)
collector.on_record = lambda rec: alerts.check(rec["fingerprint"], rec["type"])
metrics = Metrics()
alerts.threshold = ERROR_RATE_ALERT_THRESHOLD

from .logger import get_logger, CollectorHandler

if OBSERVABILITY:
    atexit.register(collector.mark_clean)
