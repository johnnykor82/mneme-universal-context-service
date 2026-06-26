# Plan: 58-residual-contract-fix-batch-bc

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow or close the `CM-057` structured logging residual by emitting safe
structured HTTP access logs with the fields required by spec Section 19.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 19 / CM-057 | Structured logs must include request id, trace id where applicable, endpoint, status/error code, project scope where safe, latency, and background job id; logs must not include tokens, provider secrets, or unredacted evidence content. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Audit current middleware/logging surface. | No structured access logger exists; metrics middleware already computes endpoint/status/latency. |
| 2 | complete | Add RED test for safe structured HTTP log fields. | Focused pytest failed before implementation: `1 failed, 2 deselected, 1 warning`. |
| 3 | complete | Add minimal structured access log emission without logging request/response bodies or auth headers. | Focused pytest passed after implementation: `1 passed, 2 deselected, 1 warning`. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched gate `2 passed, 48 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_metrics.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py -q -k "structured_access_log"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py tests/test_contract.py -q -k "structured_access_log or metrics_and_reindex"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-057 structured logging residual | ✓ met | `mneme_service.access` structured JSON log emits request id, optional trace id, endpoint, status/error code, safe scope metadata, latency, and background job id without tokens/body content; `tests/test_metrics.py::test_structured_access_log_includes_safe_operational_fields`; focused/touched gates passed; compile/diff clean. |

**Compliance Status: VERIFIED**
