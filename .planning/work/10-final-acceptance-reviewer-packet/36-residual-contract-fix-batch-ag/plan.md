# Plan: 36-residual-contract-fix-batch-ag

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or explicitly retire the remaining turn-completion provider/usage metrics
residual in `CM-025` and `CM-037` by adding the smallest missing verification
or implementation needed for `/v1/turns/complete`.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.4, 14.4 / CM-025 | Turn completion records final status and lifecycle metadata. |
| Section 14.4 / CM-037 | Turn completion updates derived state, segments, graph edges, provider metrics, and usage counters when possible. |
| Section 14.7 / CM-041 | Cost/usage report reflects turn-completion usage. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect current turn usage, provider metric, and cost-report implementation to determine whether the residual is missing behavior or missing evidence only. | Found usage counters already aggregated from turns, but provider breakdown stayed empty even when adapters supplied provider/model/cost metadata. |
| 2 | complete | Add focused failing verification for any missing required usage/provider field, or update matrix evidence if no runtime gap remains. | RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_cost_export_delete_and_restart_idempotency"` failed because `provider_breakdown` was `[]`. |
| 3 | complete | Implement the smallest runtime change if the focused verification is red. | GREEN: same focused command -> `1 passed, 42 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_metrics.py -q -k "turn_complete or cost or metrics or provider"` -> `12 passed, 33 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_contract.py` or `tests/test_metrics.py`
- `mneme_service/app.py` or `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused command selected after Step 1.
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_metrics.py -q -k "turn_complete or cost or metrics or provider"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-025 provider/usage residual | verified | `tests/test_contract.py::test_turn_complete_cost_export_delete_and_restart_idempotency` now verifies provider/model/cost metadata from turn usage appears in `provider_breakdown`. |
| CM-037 provider/usage residual | verified | Batch AG touched-area gate `12 passed`; `/v1/turns/complete` completion usage now feeds both aggregate usage counters and provider breakdown when possible. |

**Compliance Status: VERIFIED.** `CM-025` and `CM-037` are reclassified
`COMPLIANT` in the compliance matrix.
