# Plan: 04-redaction-profile-timeout-binary-safety

## Level

task

## Parent

`.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

## Status

complete

## Goal

Bring redaction profile, timeout posture, multiline secret handling, and
binary metadata-only behavior closer to Sections 17.2 and 17.3.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 17.2 | Default redaction profile, ordering, multiline handling, timeout safety, binary metadata-only handling |
| Section 17.3 | Redacted evidence remains data-only and safe for prompt inclusion |
| CM-053, CM-054 | Redaction and prompt-injection gaps |
| S24-55, S24-95, S24-96, S24-104, S24-115, S24-119 | Redaction/compression/fetchability tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for JWT, AWS/GitHub/token-like, PEM/multiline, and nested
  secret redaction fixtures.
- [x] Add RED tests proving redaction timeout never persists or returns
  unredacted plaintext.
- [x] Add RED tests for binary metadata-only handling where raw content cannot
  be safely inspected.
- [x] Implement minimal redaction/profile changes and timeout-safe posture
  without broad refactors.
- [x] Run targeted redaction/context/MCP tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/security.py`, `mneme_service/app.py`,
`mneme_service/config.py`, `tests/test_contract.py`, and
`tests/test_config.py`. Existing `tests/test_context_prepare.py`,
`tests/test_mcp_contract.py`, `tests/test_blobs.py`, and
`tests/test_embeddings.py` were used as regression gates.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_context_prepare.py tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 17.2 / CM-053 | Redaction profile and timeout behavior are bounded and safe | ✓ met for Task 04 scope | Added coverage for Bearer, JWT-like, AWS, GitHub, Google API key, PEM, `.env`, database URL, and nested sensitive JSON fields. `max_redaction_time_ms` now drives foreground event-ingest redaction and returns `422` with `reason=REDACTION_TIMEOUT` without echoing plaintext. Non-text `BYTES_REF` events are marked `redaction_scope=BINARY_METADATA_ONLY`. Config rejects non-positive `max_redaction_time_ms`. |
| Section 17.3 / CM-054 | Redacted evidence remains prompt-injection aware | ✓ met | Existing Task 03 wrappers remained green under expanded redaction: `tests/test_context_prepare.py tests/test_mcp_contract.py` included in focused gate. |
| S24-55, S24-95, S24-96, S24-104, S24-115, S24-119 | Required redaction/compression tests are covered or mapped | ✓ met for direct Task 04 coverage | Focused expanded gate `102 passed, 1 warning`; full suite `223 passed, 1 warning`; compileall and `git diff --check` passed. |

**Compliance Status: VERIFIED FOR TASK 04 SCOPE**

Residual note: Section 17.2's optional redaction metadata with internal kind,
field, and hash of original remains a later hardening item unless the final
compliance matrix treats it as mandatory for v0 closure.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | ASVS reference file read via `security-guidance` expected paths | Installed skill index referenced `data/asvs/*.md`, but those files were not present under the local skill directory. | Continued with canonical Mneme Section 17.2/17.3 and recorded security reasoning in this task instead of blocking on missing skill references. |
| 2 | Spark read-only binary inventory (`Kepler`) | Stream disconnected before completion. | Closed/ignored the failed agent and performed the narrow binary inspection in the parent thread; later used Spark `Lagrange` for read-only diff review. |
| 3 | RED/first GREEN focused tests | Expected RED failures for missing profile/timeout/binary behavior; first GREEN also over-redacted `token_estimate`/`credential_type`. | Narrowed JSON key matching, added benign-key regression assertions, and reran focused/full verification. |
