"""Persistent deterministic scan cache for the hardened commerce path."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_DEFAULT_DB = str(Path(__file__).resolve().parent / "repoguard-cache.sqlite3")
CACHE_DB_PATH = os.environ.get("REPOGUARD_CACHE_DB", _DEFAULT_DB)
CACHE_TTL_SECONDS = int(os.environ.get("REPOGUARD_CACHE_TTL_SECONDS", "900"))
CACHE_MAX_ENTRIES = int(os.environ.get("REPOGUARD_CACHE_MAX_ENTRIES", "256"))
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    path = Path(CACHE_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scan_cache (
            cache_key TEXT PRIMARY KEY,
            repo_key TEXT NOT NULL,
            commit_sha TEXT NOT NULL,
            stored_at_epoch REAL NOT NULL,
            result_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_scan_cache_stored_at ON scan_cache(stored_at_epoch)"
    )
    conn.commit()
    return conn


def cache_key(repo_key: str, commit_sha: str) -> str:
    return f"{repo_key}@{commit_sha}"


def get(repo_key: str, commit_sha: str | None) -> dict[str, Any] | None:
    if not repo_key or not commit_sha:
        return None
    key = cache_key(repo_key, commit_sha)
    with _LOCK, _connect() as conn:
        row = conn.execute(
            "SELECT stored_at_epoch, result_json FROM scan_cache WHERE cache_key=?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        if time.time() - float(row["stored_at_epoch"]) > CACHE_TTL_SECONDS:
            conn.execute("DELETE FROM scan_cache WHERE cache_key=?", (key,))
            conn.commit()
            return None
        try:
            parsed = json.loads(str(row["result_json"]))
        except ValueError:
            conn.execute("DELETE FROM scan_cache WHERE cache_key=?", (key,))
            conn.commit()
            return None
        return parsed if isinstance(parsed, dict) else None


def put(repo_key: str, commit_sha: str | None, result: dict[str, Any]) -> None:
    if not repo_key or not commit_sha or not isinstance(result, dict) or not result.get("ok", True):
        return
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    with _LOCK, _connect() as conn:
        conn.execute(
            """
            INSERT INTO scan_cache(cache_key, repo_key, commit_sha, stored_at_epoch, result_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
              stored_at_epoch=excluded.stored_at_epoch,
              result_json=excluded.result_json
            """,
            (cache_key(repo_key, commit_sha), repo_key, commit_sha, time.time(), payload),
        )
        count = int(conn.execute("SELECT COUNT(*) FROM scan_cache").fetchone()[0])
        overflow = max(0, count - CACHE_MAX_ENTRIES)
        if overflow:
            conn.execute(
                """
                DELETE FROM scan_cache
                WHERE cache_key IN (
                    SELECT cache_key FROM scan_cache
                    ORDER BY stored_at_epoch ASC
                    LIMIT ?
                )
                """,
                (overflow,),
            )
        conn.commit()


def stats() -> dict[str, int]:
    with _LOCK, _connect() as conn:
        count = int(conn.execute("SELECT COUNT(*) FROM scan_cache").fetchone()[0])
    return {
        "entries": count,
        "ttl_seconds": CACHE_TTL_SECONDS,
        "max_entries": CACHE_MAX_ENTRIES,
    }
