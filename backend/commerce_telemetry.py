"""RepoGuard machine-commerce telemetry.

Persists low-volume transaction/audit events locally for Sprint 001. Sensitive
payment payloads are not stored. PAYMENT-RESPONSE is retained only as a digest
plus decoded settlement fields when safely available.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

TELEMETRY_DB_PATH = os.environ.get(
    "REPOGUARD_TELEMETRY_DB",
    str(Path(__file__).resolve().parent / "repoguard-commerce.sqlite3"),
)
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    path = Path(TELEMETRY_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS commerce_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            status_code INTEGER,
            network TEXT,
            transaction_hash TEXT,
            payer TEXT,
            cache_hit INTEGER,
            detail TEXT
        )
        """
    )
    conn.commit()
    return conn


def record_event(
    event_type: str,
    *,
    status_code: int | None = None,
    network: str | None = None,
    transaction_hash: str | None = None,
    payer: str | None = None,
    cache_hit: bool | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    with _LOCK:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO commerce_events
                (created_at, event_type, status_code, network, transaction_hash,
                 payer, cache_hit, detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(time.time()),
                    event_type,
                    status_code,
                    network,
                    transaction_hash,
                    payer,
                    None if cache_hit is None else int(cache_hit),
                    json.dumps(detail or {}, separators=(",", ":")),
                ),
            )
            conn.commit()


def _decode_payment_response(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    candidates = [value]
    try:
        padded = value + "=" * (-len(value) % 4)
        candidates.append(base64.b64decode(padded).decode("utf-8"))
    except Exception:
        pass
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            continue
    return {}


def record_x402_response(status_code: int, headers: dict[str, str]) -> None:
    normalized = {k.lower(): v for k, v in headers.items()}
    required = normalized.get("payment-required")
    payment_response = normalized.get("payment-response") or normalized.get(
        "x-payment-response"
    )

    if status_code == 402 and required:
        record_event("payment_challenge", status_code=status_code)
        return

    if payment_response:
        decoded = _decode_payment_response(payment_response)
        tx = decoded.get("transaction") or decoded.get("transactionHash")
        network = decoded.get("network")
        payer = decoded.get("payer")
        digest = hashlib.sha256(payment_response.encode("utf-8")).hexdigest()
        success = bool(decoded.get("success", status_code < 400))
        record_event(
            "payment_settled" if success else "payment_settlement_failed",
            status_code=status_code,
            network=str(network) if network else None,
            transaction_hash=str(tx) if tx else None,
            payer=str(payer) if payer else None,
            detail={"payment_response_sha256": digest},
        )


def record_scan_served(*, cache_hit: bool, status_code: int = 200) -> None:
    record_event("scan_served", status_code=status_code, cache_hit=cache_hit)


def summary() -> dict[str, int]:
    with _LOCK:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT event_type, COUNT(*) FROM commerce_events GROUP BY event_type"
            ).fetchall()
            cache_hits = conn.execute(
                "SELECT COUNT(*) FROM commerce_events WHERE event_type='scan_served' AND cache_hit=1"
            ).fetchone()[0]
    counts = {str(name): int(count) for name, count in rows}
    return {
        "payment_challenges": counts.get("payment_challenge", 0),
        "payments_settled": counts.get("payment_settled", 0),
        "payment_settlement_failures": counts.get("payment_settlement_failed", 0),
        "scans_served": counts.get("scan_served", 0),
        "cache_hits": int(cache_hits),
    }
