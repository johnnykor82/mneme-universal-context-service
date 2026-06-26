# Plan: 64-residual-contract-fix-batch-bi

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close `CM-014` by mapping trusted Codex `Stop` hook imports through
`/v1/turns/complete` when a `turn_id` is available, then advertise Codex hooks
as full `EVENT_INGEST` lifecycle only after the behavior is test-backed.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 5.1 | `EVENT_INGEST+` adapters map bootstrap, ingest events, after response, and complete turn lifecycle. |
| CM-014 | Host adapter lifecycle contract. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing Codex hook tests for Stop turn completion and capability claim | complete | RED before implementation: `4 failed, 1 warning`; GREEN after implementation: `4 passed, 1 warning`. |
| Implement minimal Stop-hook turn completion call and capability update | complete | `Stop` imports with `turn_id` now call `/v1/turns/complete`; Codex hook capability now declares `EVENT_INGEST`. |
| Update matrix/planning and run hygiene checks | complete | Touched Codex lifecycle gate `32 passed, 48 deselected, 1 warning`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/codex_hooks.py`
- `mneme_service/app.py`
- `tests/test_codex_hooks.py`
- `tests/test_openapi.py`
- `tests/test_contract.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 5.1 Codex EVENT_INGEST lifecycle | ✓ met | `test_codex_hook_imports_through_rest_and_replay_is_idempotent`; `test_codex_hook_import_capture_file_replays_real_capture_through_rest`. |
| CM-014 | ✓ met | Matrix row `CM-014` set `COMPLIANT` with Batch BI evidence. |

**Compliance Status: VERIFIED**
