# Plan: 18-residual-contract-fix-batch-o

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the cost-mode/cost-report residual by ensuring the session cost report
includes explicit counterfactual baseline methodology fields.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 10, 11, 14.7, 23 | Cost mode downgrade/strict behavior and cost baseline methodology |
| CM-020, CM-041, CM-062 | Provider/cost and required-test residuals |
| S24-38, S24-45 | Cost-mode downgrade/strict fail and baseline methodology |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm the minimal baseline fields.
- [x] Add failing cost-report baseline methodology assertions.
- [x] Implement minimal `baseline` metadata in cost reports.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/storage.py`, `mneme_service/schemas.py`, `tests/test_contract.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "cost_report or quality_cost_mode"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_benchmarks.py tests/test_openapi.py -q -k "cost or benchmark or openapi"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-38/S24-45 | Cost-mode downgrade/strict behavior and baseline methodology are explicit | compliant | `tests/test_contract.py::test_quality_cost_mode_strict_fails_and_non_strict_downgrades`; `tests/test_contract.py::test_turn_complete_cost_export_delete_and_restart_idempotency`; Batch O touched-area gate `15 passed`; full suite `280 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | Focused Batch O test after adding assertions | `KeyError: 'enrichment_tokens'` because enrichment metrics track calls/failures only. | Keep `usage.llm_enrichment_tokens` explicit but set to `0` until storage has a real token metric. |
