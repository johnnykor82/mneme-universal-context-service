# Plan: 49-residual-contract-fix-batch-at

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Keep `RECENCY_REFILL` for explicit context search while preventing
`/v1/readiness/session` with a query from treating query-unrelated recent events
as readiness evidence when provider calls are not explicitly allowed.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.1 / CM-034 | Readiness provider-call opt-in behavior is enforced at runtime. |
| Section 24 grouped row 59/84 | Readiness distinguishes no-evidence from success and does not make provider calls unless explicitly allowed. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Reproduce touched-area readiness failure after Batch AS. | `tests/test_contract.py::test_readiness_provider_calls_require_explicit_opt_in` failed: readiness accepted recency refill as evidence. |
| 2 | complete | Use existing focused RED coverage for readiness no-provider query evidence. | Existing test remained RED before implementation. |
| 3 | complete | Disable recency refill only for readiness query search, preserving context-search behavior. | `tests/test_contract.py::test_readiness_provider_calls_require_explicit_opt_in tests/test_retrieval.py::test_context_search_recency_refills_underfilled_results -q` -> `2 passed`. |
| 4 | complete | Run touched verification, compile, and diff hygiene. | AS touched gate -> `24 passed`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/app.py`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/work/10-final-acceptance-reviewer-packet/49-residual-contract-fix-batch-at/plan.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_readiness_provider_calls_require_explicit_opt_in tests/test_retrieval.py::test_context_search_recency_refills_underfilled_results -q`
- AS touched gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_contract.py -q -k "cost_mode or context_prepare or readiness"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-034 readiness provider-call opt-in sub-residual | ✓ met | Focused readiness/provider opt-in test passed and context-search recency refill behavior remained covered. |
| S24 grouped 59/84 readiness no-evidence semantics | ✓ met | Touched readiness gate passed with `24 passed, 39 deselected`. |

**Compliance Status: VERIFIED**
