# Plan: 19-residual-contract-fix-batch-p

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the S24-19 contract-proof residual by adding a focused context-prepare
test for budget cascade from unused execution-state budget to protected tail
and then to retrieved evidence.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 11, 14.13, 23 | Context-prepare budget accounting and traceability |
| CM-021, CM-047, CM-062 | Budget accounting, context prepare, required tests |
| S24-19 | `context_prepare_cascades_unused_budget_to_tail_then_evidence` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to isolate the residual.
- [x] Add a failing focused regression test for S24-19.
- [x] Implement the smallest runtime/test adjustment needed.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_context_prepare.py`, possibly `mneme_service/app.py` if the trace
does not currently expose enough budget evidence, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cascades_unused_budget or budget_split"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_retrieval.py -q -k "context_prepare or budget or freshness or wrapper"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-19 | Context prepare cascades unused budget from state to tail then evidence | compliant | `tests/test_context_prepare.py::test_context_prepare_cascades_unused_budget_to_tail_then_evidence`; Batch P touched-area gate `22 passed`; full suite `281 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
