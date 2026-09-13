"""Execute the Day-2 real x402 Base Sepolia acceptance test.

Required environment variables:
  REPOGUARD_TESTNET_URL      Full paid endpoint URL ending in /v1/scan
  EVM_PRIVATE_KEY            Temporary buyer-wallet private key (never commit)

Optional:
  REPOGUARD_TEST_REPO        Public GitHub repository to scan

The buyer wallet must have Base Sepolia test USDC (and any gas balance required
by the current network/payment path).  The script pays twice for the same repo:
the first call should execute the scan; the second should return cache_hit=true.
"""

from __future__ import annotations

import asyncio
import os
import sys

from eth_account import Account

from x402 import x402Client
from x402.http import x402HTTPClient
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def _paid_scan(http: x402HttpxClient, url: str, repo: str):
    response = await http.post(url, json={"repo": repo})
    await response.aread()
    return response


async def main() -> int:
    url = _required("REPOGUARD_TESTNET_URL")
    private_key = _required("EVM_PRIVATE_KEY")
    repo = os.environ.get(
        "REPOGUARD_TEST_REPO",
        "raphaelbluai-private/RepoGuard-Buildathon-version-",
    ).strip()

    if not url.endswith("/v1/scan"):
        raise RuntimeError("REPOGUARD_TESTNET_URL must target /v1/scan")

    account = Account.from_key(private_key)
    client = x402Client()
    register_exact_evm_client(client, EthAccountSigner(account))
    payment_client = x402HTTPClient(client)

    async with x402HttpxClient(client) as http:
        first = await _paid_scan(http, url, repo)
        if not first.is_success:
            print(f"FIRST_CALL_FAILED status={first.status_code} body={first.text}")
            return 2

        first_body = first.json()
        first_settlement = payment_client.get_payment_settle_response(
            lambda name: first.headers.get(name)
        )
        print(
            "FIRST_CALL_OK",
            {
                "status": first.status_code,
                "repo": first_body.get("repo"),
                "commit": first_body.get("commit"),
                "scan_status": first_body.get("status"),
                "cache_hit": first_body.get("cache_hit"),
                "payment_settlement": str(first_settlement),
            },
        )

        second = await _paid_scan(http, url, repo)
        if not second.is_success:
            print(f"SECOND_CALL_FAILED status={second.status_code} body={second.text}")
            return 3

        second_body = second.json()
        second_settlement = payment_client.get_payment_settle_response(
            lambda name: second.headers.get(name)
        )
        print(
            "SECOND_CALL_OK",
            {
                "status": second.status_code,
                "repo": second_body.get("repo"),
                "commit": second_body.get("commit"),
                "scan_status": second_body.get("status"),
                "cache_hit": second_body.get("cache_hit"),
                "payment_settlement": str(second_settlement),
            },
        )

        if first_body.get("cache_hit") is not False:
            print("ACCEPTANCE_FAIL: first paid call must execute a fresh scan")
            return 4
        if second_body.get("cache_hit") is not True:
            print("ACCEPTANCE_FAIL: second paid call for identical SHA must hit cache")
            return 5

    print("DAY2_TESTNET_ACCEPTANCE_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
