# Plan: 14-residual-contract-fix-batch-k

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the Section 24 readiness residual by enforcing the provider-call boundary:
`require_evidence=false` remains provider-free, and `require_evidence=true`
uses local retrieval unless `allow_provider_calls=true` explicitly opts in.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.1 | `/v1/readiness/session` auth/session/evidence and provider opt-in behavior |
| CM-034, CM-062 | Readiness Section 24 residuals |
| S24-59 | `readiness_session_distinguishes_auth_missing_session_and_no_evidence` |
| S24-84 | `readiness_require_evidence_false_checks_session_only` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact residuals and minimal
  implementation scope.
- [x] Add failing tests for `allow_provider_calls=false` local-only evidence
  readiness and explicit `allow_provider_calls=true` provider usage.
- [x] Implement minimal readiness provider-call gating and status metadata.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `tests/test_contract.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "readiness"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py tests/test_reindex.py tests/test_openapi.py -q -k "readiness or provider or reindex or openapi"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-59 | Auth, missing session, no-evidence, and provider-call status are distinguished | ✓ met | `tests/test_contract.py::test_session_readiness_requires_auth_session_and_evidence`, `tests/test_contract.py::test_readiness_provider_calls_require_explicit_opt_in`; focused RED -> `3 failed, 1 passed, 30 deselected, 1 warning`; focused GREEN -> `4 passed, 30 deselected, 1 warning`; touched-area gate -> `30 passed, 45 deselected, 1 warning`; full suite -> `276 passed, 1 warning`. |
| S24-84 | `require_evidence=false` checks session only and provider-free | ✓ met | `tests/test_contract.py::test_readiness_require_evidence_false_checks_session_only_without_provider_calls`, `tests/test_contract.py::test_readiness_evidence_false_uses_local_search_without_provider_calls`; focused GREEN -> `4 passed, 30 deselected, 1 warning`; full suite -> `276 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
