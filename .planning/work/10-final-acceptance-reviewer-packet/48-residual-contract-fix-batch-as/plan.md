# Plan: 48-residual-contract-fix-batch-as

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-009` by unifying `/v1/context/prepare` QUALITY cost-mode
downgrade/fail behavior with the session-start cost-mode resolver.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 4 BR-5 / CM-009 | Optional provider quality layers are disabled/downgraded explicitly and fail in strict mode. |
| Section 10 / CM-020 | Provider mode/cost mode warnings and strict failures are consistent across public flows. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify smallest safe slice. | Spark `019effd8-38a2-70b1-9fe6-8cdebfce790b` recommended context-prepare cost-mode parity first. |
| 2 | complete | Add focused RED tests for strict QUALITY failure and non-strict QUALITY downgrade warning. | RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cost_mode"` failed with missing structured downgrade and missing strict `503`. |
| 3 | complete | Use shared cost-mode resolver in context prepare and propagate warnings consistently. | GREEN: focused cost-mode pytest passed after `context_prepare` used `cost_mode_warnings_or_error()`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | Touched gate `24 passed`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_context_prepare.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cost_mode"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_contract.py -q -k "cost_mode or context_prepare or readiness"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-009 cost-mode downgrade/failure sub-residual | ✓ met | `tests/test_context_prepare.py -q -k "cost_mode"` -> `3 passed`; touched gate -> `24 passed`; compileall and diff hygiene clean. |

**Compliance Status: VERIFIED**

Provider `last_health` status remains a separate follow-up unless the row is
reclassified based on existing evidence.
