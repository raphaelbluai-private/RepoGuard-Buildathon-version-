"""Structured operational alert events for production diagnostics."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

_LOG = logging.getLogger("repoguard.ops")


def emit_alert(
    code: str,
    *,
    severity: str,
    component: str,
    transaction_id: str | None = None,
    retryable: bool | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = severity.upper()
    if normalized not in {"INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("Unsupported alert severity.")
    event = {
        "event": "repoguard_operational_alert",
        "alert_id": "rga_" + uuid.uuid4().hex,
        "code": code,
        "severity": normalized,
        "component": component,
        "occurred_at_ms": int(time.time() * 1000),
        "transaction_id": transaction_id,
        "retryable": retryable,
        "detail": detail or {},
    }
    message = json.dumps(event, sort_keys=True, separators=(",", ":"))
    getattr(_LOG, normalized.lower())(message)
    return event
