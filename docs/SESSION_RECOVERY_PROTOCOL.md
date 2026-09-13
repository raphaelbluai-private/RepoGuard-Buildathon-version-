# REPO GUARD SESSION RECOVERY PROTOCOL

**Governance:** RAPHAEL Master Spec v1.6  
**Status:** Binding continuity procedure  
**Applies to:** New chats, agents, coding environments, devices, and operators

## Governing Principle

**The repository carries the build. The conversation does not carry the build.**

A new session must recover RepoGuard from the canonical repository before modifying code or status.

## Recovery Order

1. Open `.build-state.json`.
2. Open `docs/BUILD_HANDOFF.md`.
3. Verify canonical repository: `raphaelbluai-private/RepoGuard-Buildathon-version-`.
4. Verify active branch: `x402-production`.
5. Fetch the live branch HEAD.
6. Compare live HEAD with `recorded_head_sha` in `.build-state.json`.
7. If live HEAD is newer, inspect intervening commits/diff and reconcile state before building.
8. Load governing documents referenced by `.build-state.json`, especially:
   - `docs/governance/RAPHAEL_MASTER_SPEC_v1.6_GOVERNANCE.md`
   - `docs/governance/RAPHAEL_SECURITY_GOVERNANCE_PROTOCOL.md`
   - `docs/REPO_GUARD_CONTINUOUS_COMPLETION_BUILD_TASK.md`
9. Load only relevant historical mission-assurance documents needed to explain current state; do not let them override v1.6.
10. Reconstruct/verify the RAPHAEL MASTER TREE when status is ambiguous or requested.
11. Verify current CI/test/deployment evidence against the actual current commit; historical Green does not automatically transfer.
12. Continue from `next_work_package` unless live repository evidence proves a newer valid continuation point.

## Evidence Precedence

When sources disagree, use this precedence:

1. Live canonical repository contents and branch history.
2. Current governing RAPHAEL v1.6 controls.
3. Current `.build-state.json` and `docs/BUILD_HANDOFF.md`, reconciled to live HEAD.
4. Current validation/CI/runtime/deployment/evidence records.
5. Current-session Principal instructions and decisions.
6. Prior chats, summaries, screenshots, or memory.

## Status Truth Rule

Use only evidence-supported states:

- `PASSED`
- `FAILED`
- `BLOCKED`
- `NOT RUN`
- `DEFERRED`
- `EXPIRED`
- `SUPERSEDED`
- `NOT APPLICABLE`
- `WAIVED / RISK ACCEPTED`

Do not promote code to Green because it exists.

## Deferred External Gates

External credentials, accounts, wallets, marketplace access, production domains, or other unavailable dependencies may be marked BLOCKED/DEFERRED without stopping unrelated construction.

Continue valid independent architecture, code, tests, fixtures, static review, security work, continuity, and evidence preparation.

## End-of-Batch Rule

Before operational handoff after a meaningful batch:

1. durably record approved source changes;
2. run and record applicable validation;
3. update `.build-state.json` to the latest checkpoint;
4. update `docs/BUILD_HANDOFF.md`;
5. update Master Tree statuses using evidence;
6. record exact next work package;
7. record any external/deferred gates with owner and next action.

## Standard Recovery Invocation

> Recover RepoGuard from the canonical repository. Read `.build-state.json` and `docs/BUILD_HANDOFF.md`, verify the live `x402-production` HEAD, inspect any commits newer than the recorded checkpoint, load the RAPHAEL Master Spec v1.6 governance and continuous completion task, reconcile validation evidence, verify the Master Tree if needed, and continue from the exact next work package. Do not ask for prior-chat copy/paste unless repository evidence is genuinely insufficient.