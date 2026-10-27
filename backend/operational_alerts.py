"""Structured operational alert events for production diagnostics."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

_LOG = logging.getLogger("repoguard.ops")
_SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "SIGNATURE", "AUTHORIZATION", "PRIVATE_KEY", "API_KEY")


def _redact(value: Any, key: str | None = None) -> Any:
    if key and any(marker in key.upper() for marker in _SECRET_MARKERS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, tuple):
        return [_redact(v) for v in value]
    return value


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
        "detail": _redact(detail or {}),
    }
    message = json.dumps(event, sort_keys=True, separators=(",", ":"))
    getattr(_LOG, normalized.lower())(message)
    return event
