"""Performance budgets and deterministic evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class PerformanceBudget:
    metric: str
    p50_ms: float
    p95_ms: float

BUDGETS = {
    "verify": PerformanceBudget("verify", p50_ms=1000, p95_ms=3000),
    "fulfillment_cached": PerformanceBudget("fulfillment_cached", p50_ms=500, p95_ms=1500),
    "fulfillment_scan": PerformanceBudget("fulfillment_scan", p50_ms=5000, p95_ms=15000),
    "settlement": PerformanceBudget("settlement", p50_ms=2000, p95_ms=5000),
    "total_cached": PerformanceBudget("total_cached", p50_ms=3000, p95_ms=7000),
    "total_scan": PerformanceBudget("total_scan", p50_ms=8000, p95_ms=20000),
}

def percentile(values: Iterable[float], p: float) -> float | None:
    ordered = sorted(float(v) for v in values)
    if not ordered:
        return None
    idx = min(len(ordered)-1, max(0, round((len(ordered)-1)*p)))
    return ordered[idx]

def evaluate(metric: str, samples_ms: Iterable[float]) -> dict:
    budget = BUDGETS[metric]
    values = list(samples_ms)
    p50 = percentile(values, 0.50)
    p95 = percentile(values, 0.95)
    return {
        "metric": metric,
        "sample_count": len(values),
        "p50_ms": p50,
        "p95_ms": p95,
        "budget_p50_ms": budget.p50_ms,
        "budget_p95_ms": budget.p95_ms,
        "passes": bool(
            p50 is not None and p95 is not None
            and p50 <= budget.p50_ms
            and p95 <= budget.p95_ms
        ),
    }
