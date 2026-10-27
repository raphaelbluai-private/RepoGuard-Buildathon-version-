"""Durable payment-operations assurance for RepoGuard x402 commerce.

The ledger stores only safe digests/identifiers. Raw payment signatures, private
keys, and credentials are never persisted.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PAYMENT_DB_PATH = os.environ.get(
    "REPOGUARD_PAYMENT_DB",
    str(Path(__file__).resolve().parent / "repoguard-payments.sqlite3"),
)
_LOCK = threading.Lock()
_CURRENT_TRANSACTION_ID: ContextVar[str | None] = ContextVar("repoguard_payment_transaction_id", default=None)

CHALLENGED = "CHALLENGED"
PRESENTED = "PRESENTED"
VERIFIED = "VERIFIED"
FULFILLMENT_STARTED = "FULFILLMENT_STARTED"
FULFILLED = "FULFILLED"
SETTLEMENT_PENDING = "SETTLEMENT_PENDING"
SETTLED = "SETTLED"
RECEIPT_ISSUED = "RECEIPT_ISSUED"
VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
FULFILLMENT_FAILED_RETRIABLE = "FULFILLMENT_FAILED_RETRIABLE"
FULFILLMENT_FAILED_TERMINAL = "FULFILLMENT_FAILED_TERMINAL"
SETTLEMENT_FAILED_RETRIABLE = "SETTLEMENT_FAILED_RETRIABLE"
SETTLEMENT_FAILED_TERMINAL = "SETTLEMENT_FAILED_TERMINAL"
REPLAY_REJECTED = "REPLAY_REJECTED"
IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
EXPIRED = "EXPIRED"

TERMINAL_STATES = {
    RECEIPT_ISSUED,
    VERIFICATION_REJECTED,
    FULFILLMENT_FAILED_TERMINAL,
    SETTLEMENT_FAILED_TERMINAL,
    REPLAY_REJECTED,
    IDEMPOTENCY_CONFLICT,
    EXPIRED,
}

_ALLOWED: dict[str, set[str]] = {
    CHALLENGED: {PRESENTED, EXPIRED, IDEMPOTENCY_CONFLICT},
    PRESENTED: {VERIFIED, VERIFICATION_REJECTED, REPLAY_REJECTED, IDEMPOTENCY_CONFLICT, EXPIRED},
    VERIFIED: {
        FULFILLMENT_STARTED,
        FULFILLMENT_FAILED_RETRIABLE,
        FULFILLMENT_FAILED_TERMINAL,
        REPLAY_REJECTED,
    },
    FULFILLMENT_STARTED: {
        FULFILLED,
        FULFILLMENT_FAILED_RETRIABLE,
        FULFILLMENT_FAILED_TERMINAL,
    },
    FULFILLED: {SETTLEMENT_PENDING, SETTLED, SETTLEMENT_FAILED_RETRIABLE, SETTLEMENT_FAILED_TERMINAL},
    SETTLEMENT_PENDING: {SETTLED, SETTLEMENT_FAILED_RETRIABLE, SETTLEMENT_FAILED_TERMINAL},
    SETTLEMENT_FAILED_RETRIABLE: {SETTLEMENT_PENDING, SETTLED, SETTLEMENT_FAILED_TERMINAL},
    SETTLED: {RECEIPT_ISSUED},
    FULFILLMENT_FAILED_RETRIABLE: {FULFILLMENT_STARTED, EXPIRED},
}


class PaymentOperationError(RuntimeError):
    def __init__(self, code: str, message: str, *, transaction_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.transaction_id = transaction_id


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    idempotency_key: str
    request_hash: str
    payment_proof_digest: str | None
    sku: str
    price_usd: str
    network: str
    facilitator_url: str
    state: str
    retryable: bool | None
    failure_code: str | None
    transaction_hash: str | None
    cache_hit: bool | None
    receipt_id: str | None
    response_json: str | None
    created_at_ms: int
    updated_at_ms: int


def set_current_transaction(transaction_id: str | None) -> Token:
    return _CURRENT_TRANSACTION_ID.set(transaction_id)


def reset_current_transaction(token: Token) -> None:
    _CURRENT_TRANSACTION_ID.reset(token)


def current_transaction_id() -> str | None:
    return _CURRENT_TRANSACTION_ID.get()


def record_control_event(
    event_type: str,
    *,
    transaction_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    with _LOCK, _connect() as conn:
        _record_control_event_locked(
            conn,
            event_type,
            transaction_id=transaction_id,
            detail=detail,
        )
        conn.commit()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _connect() -> sqlite3.Connection:
    path = Path(PAYMENT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_transactions (
            transaction_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            request_hash TEXT NOT NULL,
            payment_proof_digest TEXT UNIQUE,
            sku TEXT NOT NULL,
            price_usd TEXT NOT NULL,
            network TEXT NOT NULL,
            facilitator_url TEXT NOT NULL,
            state TEXT NOT NULL,
            retryable INTEGER,
            failure_code TEXT,
            transaction_hash TEXT,
            cache_hit INTEGER,
            receipt_id TEXT,
            response_json TEXT,
            created_at_ms INTEGER NOT NULL,
            updated_at_ms INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_control_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at_ms INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            transaction_id TEXT,
            detail_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            occurred_at_ms INTEGER NOT NULL,
            previous_state TEXT,
            new_state TEXT NOT NULL,
            failure_code TEXT,
            retryable INTEGER,
            transaction_hash TEXT,
            cache_hit INTEGER,
            receipt_id TEXT,
            detail_json TEXT NOT NULL,
            FOREIGN KEY(transaction_id) REFERENCES payment_transactions(transaction_id)
        )
        """
    )
    conn.commit()
    return conn


def canonical_request_hash(*, sku: str, body: Any) -> str:
    payload = json.dumps(
        {"sku": sku, "body": body},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def payment_proof_digest(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.encode("utf-8")
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.b64decode(padded)
        parsed = json.loads(decoded)
        raw = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except Exception:
        pass
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _row(row: sqlite3.Row | None) -> Transaction | None:
    if row is None:
        return None
    return Transaction(
        transaction_id=row["transaction_id"],
        idempotency_key=row["idempotency_key"],
        request_hash=row["request_hash"],
        payment_proof_digest=row["payment_proof_digest"],
        sku=row["sku"],
        price_usd=row["price_usd"],
        network=row["network"],
        facilitator_url=row["facilitator_url"],
        state=row["state"],
        retryable=None if row["retryable"] is None else bool(row["retryable"]),
        failure_code=row["failure_code"],
        transaction_hash=row["transaction_hash"],
        cache_hit=None if row["cache_hit"] is None else bool(row["cache_hit"]),
        receipt_id=row["receipt_id"],
        response_json=row["response_json"],
        created_at_ms=int(row["created_at_ms"]),
        updated_at_ms=int(row["updated_at_ms"]),
    )


def get_transaction(transaction_id: str) -> Transaction | None:
    with _LOCK, _connect() as conn:
        return _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE transaction_id=?",
            (transaction_id,),
        ).fetchone())


def get_by_idempotency(idempotency_key: str) -> Transaction | None:
    with _LOCK, _connect() as conn:
        return _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE idempotency_key=?",
            (idempotency_key,),
        ).fetchone())


def get_by_payment_digest(digest: str) -> Transaction | None:
    with _LOCK, _connect() as conn:
        return _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE payment_proof_digest=?",
            (digest,),
        ).fetchone())


def _record_control_event_locked(
    conn: sqlite3.Connection,
    event_type: str,
    *,
    transaction_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO payment_control_events
        (occurred_at_ms, event_type, transaction_id, detail_json)
        VALUES (?, ?, ?, ?)
        """,
        (
            _now_ms(),
            event_type,
            transaction_id,
            json.dumps(detail or {}, sort_keys=True, separators=(",", ":")),
        ),
    )


def _transition_locked(
    conn: sqlite3.Connection,
    tx: Transaction,
    new_state: str,
    *,
    failure_code: str | None = None,
    retryable: bool | None = None,
    transaction_hash: str | None = None,
    cache_hit: bool | None = None,
    receipt_id: str | None = None,
    response_json: str | None = None,
    detail: dict[str, Any] | None = None,
) -> Transaction:
    if tx.state == new_state:
        return tx
    allowed = _ALLOWED.get(tx.state, set())
    if new_state not in allowed:
        raise PaymentOperationError(
            "INVALID_STATE_TRANSITION",
            f"Payment transaction cannot transition from {tx.state} to {new_state}.",
            transaction_id=tx.transaction_id,
        )
    now = _now_ms()
    conn.execute(
        """
        UPDATE payment_transactions
        SET state=?, retryable=?, failure_code=?,
            transaction_hash=COALESCE(?, transaction_hash),
            cache_hit=COALESCE(?, cache_hit),
            receipt_id=COALESCE(?, receipt_id),
            response_json=COALESCE(?, response_json),
            updated_at_ms=?
        WHERE transaction_id=?
        """,
        (
            new_state,
            None if retryable is None else int(retryable),
            failure_code,
            transaction_hash,
            None if cache_hit is None else int(cache_hit),
            receipt_id,
            response_json,
            now,
            tx.transaction_id,
        ),
    )
    conn.execute(
        """
        INSERT INTO payment_transitions
        (transaction_id, occurred_at_ms, previous_state, new_state, failure_code,
         retryable, transaction_hash, cache_hit, receipt_id, detail_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx.transaction_id,
            now,
            tx.state,
            new_state,
            failure_code,
            None if retryable is None else int(retryable),
            transaction_hash,
            None if cache_hit is None else int(cache_hit),
            receipt_id,
            json.dumps(detail or {}, sort_keys=True, separators=(",", ":")),
        ),
    )
    return _row(conn.execute(
        "SELECT * FROM payment_transactions WHERE transaction_id=?",
        (tx.transaction_id,),
    ).fetchone())


def transition(transaction_id: str, new_state: str, **kwargs: Any) -> Transaction:
    with _LOCK, _connect() as conn:
        tx = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE transaction_id=?",
            (transaction_id,),
        ).fetchone())
        if tx is None:
            raise PaymentOperationError("TRANSACTION_NOT_FOUND", "Payment transaction not found.")
        updated = _transition_locked(conn, tx, new_state, **kwargs)
        conn.commit()
        assert updated is not None
        return updated


def begin_transaction(
    *,
    idempotency_key: str | None,
    request_hash: str,
    payment_digest: str | None,
    sku: str,
    price_usd: str,
    network: str,
    facilitator_url: str,
    challenged: bool = False,
) -> Transaction:
    key = (idempotency_key or "").strip()
    if not key:
        key = "rg-auto-" + uuid.uuid4().hex

    with _LOCK, _connect() as conn:
        existing = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE idempotency_key=?",
            (key,),
        ).fetchone())
        if existing is not None:
            if existing.request_hash != request_hash or existing.sku != sku:
                _record_control_event_locked(
                    conn,
                    "idempotency_conflict",
                    transaction_id=existing.transaction_id,
                )
                if existing.state not in TERMINAL_STATES:
                    existing = _transition_locked(
                        conn,
                        existing,
                        IDEMPOTENCY_CONFLICT,
                        failure_code="IDEMPOTENCY_KEY_REUSED_FOR_DIFFERENT_REQUEST",
                        retryable=False,
                    )
                    conn.commit()
                raise PaymentOperationError(
                    "IDEMPOTENCY_CONFLICT",
                    "Idempotency key is already bound to a different request.",
                    transaction_id=existing.transaction_id,
                )
            return existing

        if payment_digest:
            reused = _row(conn.execute(
                "SELECT * FROM payment_transactions WHERE payment_proof_digest=?",
                (payment_digest,),
            ).fetchone())
            if reused is not None:
                _record_control_event_locked(
                    conn,
                    "replay_attempt",
                    transaction_id=reused.transaction_id,
                    detail={"sku": sku},
                )
                conn.commit()
                raise PaymentOperationError(
                    "REPLAY_REJECTED",
                    "Payment proof has already been presented.",
                    transaction_id=reused.transaction_id,
                )

        now = _now_ms()
        state = CHALLENGED if challenged else PRESENTED
        transaction_id = "rgtx_" + uuid.uuid4().hex
        conn.execute(
            """
            INSERT INTO payment_transactions
            (transaction_id, idempotency_key, request_hash, payment_proof_digest,
             sku, price_usd, network, facilitator_url, state, created_at_ms, updated_at_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                key,
                request_hash,
                payment_digest,
                sku,
                price_usd,
                network,
                facilitator_url,
                state,
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO payment_transitions
            (transaction_id, occurred_at_ms, previous_state, new_state, detail_json)
            VALUES (?, ?, NULL, ?, ?)
            """,
            (transaction_id, now, state, "{}"),
        )
        conn.commit()
        tx = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE transaction_id=?",
            (transaction_id,),
        ).fetchone())
        assert tx is not None
        return tx


def bind_presented_payment(transaction_id: str, payment_digest: str) -> Transaction:
    with _LOCK, _connect() as conn:
        tx = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE transaction_id=?",
            (transaction_id,),
        ).fetchone())
        if tx is None:
            raise PaymentOperationError("TRANSACTION_NOT_FOUND", "Payment transaction not found.")
        reused = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE payment_proof_digest=? AND transaction_id<>?",
            (payment_digest, transaction_id),
        ).fetchone())
        if reused is not None:
            raise PaymentOperationError(
                "REPLAY_REJECTED",
                "Payment proof has already been presented.",
                transaction_id=reused.transaction_id,
            )
        conn.execute(
            "UPDATE payment_transactions SET payment_proof_digest=?, updated_at_ms=? WHERE transaction_id=?",
            (payment_digest, _now_ms(), transaction_id),
        )
        tx = _row(conn.execute(
            "SELECT * FROM payment_transactions WHERE transaction_id=?",
            (transaction_id,),
        ).fetchone())
        assert tx is not None
        if tx.state == CHALLENGED:
            tx = _transition_locked(conn, tx, PRESENTED)
        conn.commit()
        return tx


def issue_receipt(transaction_id: str) -> Transaction:
    tx = get_transaction(transaction_id)
    if tx is None:
        raise PaymentOperationError("TRANSACTION_NOT_FOUND", "Payment transaction not found.")
    if tx.state == RECEIPT_ISSUED:
        return tx
    if tx.state != SETTLED:
        raise PaymentOperationError(
            "RECEIPT_REQUIRES_SETTLEMENT",
            "Payment receipt can only be issued after settlement.",
            transaction_id=transaction_id,
        )
    material = f"{tx.transaction_id}|{tx.transaction_hash or ''}|{tx.request_hash}|{tx.sku}"
    receipt_id = "rgrcpt_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    return transition(transaction_id, RECEIPT_ISSUED, receipt_id=receipt_id)


def decode_settlement_header(value: str | None) -> dict[str, Any]:
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


def metrics() -> dict[str, Any]:
    with _LOCK, _connect() as conn:
        total = int(conn.execute("SELECT COUNT(*) FROM payment_transactions").fetchone()[0])
        by_state = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                "SELECT state, COUNT(*) FROM payment_transactions GROUP BY state"
            ).fetchall()
        }
        transition_counts = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                "SELECT new_state, COUNT(*) FROM payment_transitions GROUP BY new_state"
            ).fetchall()
        }
        sku_volume = {
            str(r[0]): int(r[1])
            for r in conn.execute(
                """
                SELECT sku, COUNT(*) FROM payment_transactions
                WHERE state IN (?, ?) GROUP BY sku
                """,
                (SETTLED, RECEIPT_ISSUED),
            ).fetchall()
        }
        revenue_by_sku = {
            str(r[0]): round(float(r[1]), 6)
            for r in conn.execute(
                """
                SELECT sku, SUM(CAST(price_usd AS REAL)) FROM payment_transactions
                WHERE state IN (?, ?) GROUP BY sku
                """,
                (SETTLED, RECEIPT_ISSUED),
            ).fetchall()
        }
        cache = conn.execute(
            """
            SELECT
              SUM(CASE WHEN cache_hit=1 AND state IN (?, ?) THEN 1 ELSE 0 END),
              SUM(CASE WHEN state IN (?, ?) THEN 1 ELSE 0 END)
            FROM payment_transactions
            """,
            (SETTLED, RECEIPT_ISSUED, SETTLED, RECEIPT_ISSUED),
        ).fetchone()
        replay_attempts = int(conn.execute(
            "SELECT COUNT(*) FROM payment_control_events WHERE event_type='replay_attempt'"
        ).fetchone()[0])
        rows = conn.execute(
            """
            SELECT transaction_id, occurred_at_ms, new_state
            FROM payment_transitions
            ORDER BY transaction_id, occurred_at_ms, id
            """
        ).fetchall()

    timeline: dict[str, dict[str, int]] = {}
    for row in rows:
        timeline.setdefault(str(row[0]), {})[str(row[2])] = int(row[1])

    verify_latencies: list[int] = []
    fulfillment_latencies: list[int] = []
    settlement_latencies: list[int] = []
    total_latencies: list[int] = []
    for states in timeline.values():
        if PRESENTED in states and VERIFIED in states:
            verify_latencies.append(max(0, states[VERIFIED] - states[PRESENTED]))
        if FULFILLMENT_STARTED in states and FULFILLED in states:
            fulfillment_latencies.append(max(0, states[FULFILLED] - states[FULFILLMENT_STARTED]))
        if SETTLEMENT_PENDING in states and SETTLED in states:
            settlement_latencies.append(max(0, states[SETTLED] - states[SETTLEMENT_PENDING]))
        start = states.get(PRESENTED) or states.get(CHALLENGED)
        end = states.get(RECEIPT_ISSUED) or states.get(SETTLED)
        if start is not None and end is not None:
            total_latencies.append(max(0, end - start))

    def percentile(values: list[int], p: float) -> int | None:
        if not values:
            return None
        ordered = sorted(values)
        index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
        return ordered[index]

    challenged = transition_counts.get(CHALLENGED, 0)
    presented = transition_counts.get(PRESENTED, 0)
    settled = transition_counts.get(SETTLED, 0)
    settlement_failures = transition_counts.get(SETTLEMENT_FAILED_RETRIABLE, 0) + transition_counts.get(SETTLEMENT_FAILED_TERMINAL, 0)
    fulfillment_failures = transition_counts.get(FULFILLMENT_FAILED_RETRIABLE, 0) + transition_counts.get(FULFILLMENT_FAILED_TERMINAL, 0)
    settlement_attempts = settled + settlement_failures
    verified = transition_counts.get(VERIFIED, 0)
    cache_hits = int(cache[0] or 0)
    successful = int(cache[1] or 0)

    def latency(values: list[int]) -> dict[str, int | None]:
        return {"p50": percentile(values, 0.50), "p95": percentile(values, 0.95)}

    return {
        "transactions": total,
        "challenge_rate": challenged / max(1, challenged + presented),
        "payment_success_rate": settled / presented if presented else 0.0,
        "settlement_failure_rate": settlement_failures / settlement_attempts if settlement_attempts else 0.0,
        "fulfillment_failure_rate": fulfillment_failures / verified if verified else 0.0,
        "latency_ms": {
            "verify": latency(verify_latencies),
            "fulfillment": latency(fulfillment_latencies),
            "settlement": latency(settlement_latencies),
            "total": latency(total_latencies),
        },
        "sku_volume": sku_volume,
        "revenue_by_sku_usd": revenue_by_sku,
        "replay_attempts": replay_attempts,
        "cache_assisted_fulfillment_rate": cache_hits / successful if successful else 0.0,
        "states": by_state,
    }
