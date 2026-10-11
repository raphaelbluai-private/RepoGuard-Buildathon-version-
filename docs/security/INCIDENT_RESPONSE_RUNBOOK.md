# RepoGuard x402 Incident Response Runbook

## Immediate containment

1. Disable traffic at the hosting layer and set `REPOGUARD_X402_ENABLED=0` or remove `REPOGUARD_PAY_TO` only through the approved secret/configuration system.
2. Preserve application, hosting, facilitator, and GitHub audit evidence. Do not paste payment signatures, tokens, or private keys into tickets or chat.
3. If repository credentials may have existed in the runtime, revoke and rotate them at the provider; the public commerce runtime does not require them.
4. If wallet authority may be compromised, stop payment acceptance and invoke the approved custody/key-rotation procedure. Never move funds automatically.
5. Record affected commit, image digest, environment, routes, time window, and non-secret correlation identifiers.

## Triage

- SSRF/credential event: capture requested provider and normalized host (not credentials), DNS results, response status, and container egress evidence.
- Payment event: capture transaction hash, network, payer, facilitator result, and stored response digest. Do not retain raw `Payment-Signature` values.
- Availability/abuse event: capture direct peer address, quota category, repository identifier, concurrency state, and hosting-layer rate-limit evidence.
- Source-integrity event: compare deployed SHA/image digest to the reviewed `x402-production` release commit and suspend deployment on mismatch.

## Recovery gate

Recovery requires a root-cause repair, a regression or hostile test, full CI, a new immutable image/commit identity, and RAPHAEL evidence review. Production restoration, repository visibility changes, mainnet activation, key rotation, and destructive cleanup require human authorization.

Gate 8 remains **NOT AUTHORIZED** until the Principal explicitly approves launch.
