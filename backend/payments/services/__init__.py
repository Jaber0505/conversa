"""Payment services for business logic.

This package exposes service classes without importing submodules at import time
to avoid side effects during Django test discovery under alternative module
paths (e.g., implicit namespace 'app.payments').
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["PaymentService", "RefundService"]


def __getattr__(name: str) -> Any:  # lazy attribute loading
    if name == "PaymentService":
        return importlib.import_module(".payment_service", __name__).PaymentService
    if name == "RefundService":
        return importlib.import_module(".refund_service", __name__).RefundService
    raise AttributeError(name)
