from __future__ import annotations

import os
import threading
import time
from typing import Any


CACHE_TTL_SECONDS = int(os.environ.get("REPOGUARD_CACHE_TTL_SECONDS", "900"))
_CACHE: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def get(repo_key: str, sha: str | None) -> dict[str, Any] | None:
    if not sha:
        return None
    key = f"{repo_key}:{sha}"
    now = time.monotonic()
    with _LOCK:
        item = _CACHE.get(key)
        if item is None:
            return None
        if now - item["stored_at"] > CACHE_TTL_SECONDS:
            _CACHE.pop(key, None)
            return None
        return item["result"]


def put(repo_key: str, sha: str | None, result: dict[str, Any]) -> None:
    if not sha:
        return
    key = f"{repo_key}:{sha}"
    with _LOCK:
        _CACHE[key] = {"stored_at": time.monotonic(), "result": result}
        if len(_CACHE) > 256:
            oldest_key = min(_CACHE, key=lambda value: _CACHE[value]["stored_at"])
            _CACHE.pop(oldest_key, None)
