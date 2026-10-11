import pytest

from x402_payments import BASE_MAINNET, BASE_SEPOLIA, validate_facilitator_url, validate_payment_boundary


WALLET = "0x000000000000000000000000000000000000dEaD"


@pytest.mark.parametrize(
    "url",
    [
        "http://x402.org/facilitator",
        "https://x402.org.evil.example/facilitator",
        "https://user@x402.org/facilitator",
        "https://x402.org:8443/facilitator",
        "https://x402.org/facilitator?redirect=evil",
    ],
)
def test_facilitator_url_fails_closed(url):
    with pytest.raises(RuntimeError, match="approved HTTPS"):
        validate_facilitator_url(url)


def test_testnet_payment_boundary_is_valid():
    result = validate_payment_boundary(
        pay_to=WALLET,
        network=BASE_SEPOLIA,
        facilitator_url="https://x402.org/facilitator",
        allow_mainnet=False,
    )
    assert result["network"] == BASE_SEPOLIA


def test_mainnet_payment_boundary_requires_explicit_release_authority():
    with pytest.raises(RuntimeError, match="mainnet is blocked"):
        validate_payment_boundary(
            pay_to=WALLET,
            network=BASE_MAINNET,
            facilitator_url="https://api.cdp.coinbase.com/platform/v2/x402",
            allow_mainnet=False,
        )
