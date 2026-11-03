
# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
import logging
import traceback


class CollectorHandler(logging.Handler):
    def emit(self, record):
        try:
            if record.exc_info:
                err = record.exc_info[1]
                tb_text = "".join(traceback.format_exception(*record.exc_info))
            else:
                err = RuntimeError(record.getMessage())
                tb_text = record.getMessage()
            from IotaXMedia.utils.observability import collector
            collector.record(
                f"LOG:{record.name}",
                err,
                tb_text,
                {"level": record.levelname},
            )
        except Exception:
            pass


def get_logger(category: str = "CORE"):
    lg = logging.getLogger(f"IotaXMedia.obs.{category}")
    if not any(isinstance(h, CollectorHandler) for h in lg.handlers):
        h = CollectorHandler()
        h.setLevel(logging.WARNING)
        lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    return lg
