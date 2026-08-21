from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    price_usd: str
    purpose: str
    includes_safe_to_ship: bool = False
    returns_full_findings: bool = False
    paid: bool = True


PRODUCTS = {
    "repo_preflight": Product(
        sku="repo_preflight",
        price_usd="0.00",
        paid=False,
        purpose="Check source reachability, support, and repository identity before spending.",
    ),
    "verify_commit": Product(
        sku="verify_commit",
        price_usd="0.01",
        purpose="Confirm current repository HEAD still matches a previously trusted commit.",
    ),
    "safe_to_ship": Product(
        sku="safe_to_ship",
        price_usd="0.03",
        purpose="Return the canonical machine-readable ship/no-ship verdict without full findings.",
        includes_safe_to_ship=True,
    ),
    "repo_scan": Product(
        sku="repo_scan",
        price_usd="0.07",
        purpose="Run the full deterministic readiness and security scan.",
        includes_safe_to_ship=True,
        returns_full_findings=True,
    ),
    "explain_findings": Product(
        sku="explain_findings",
        price_usd="0.10",
        purpose="Return a structured remediation sequence mapped to deterministic findings.",
    ),
    "attest_scan": Product(
        sku="attest_scan",
        price_usd="0.15",
        purpose="Return durable commit-bound, hash-verifiable scan evidence.",
        includes_safe_to_ship=True,
    ),
}


def get_product(sku: str) -> Product:
    try:
        return PRODUCTS[sku]
    except KeyError as exc:
        raise ValueError(f"Unknown RepoGuard product: {sku}") from exc


def discovery_catalog() -> list[dict]:
    return [
        {
            "sku": p.sku,
            "price_usd": p.price_usd,
            "paid": p.paid,
            "purpose": p.purpose,
        }
        for p in PRODUCTS.values()
    ]
