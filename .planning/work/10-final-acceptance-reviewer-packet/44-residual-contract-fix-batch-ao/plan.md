# Plan: 44-residual-contract-fix-batch-ao

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or narrow `CM-045` by adding broader `context_search` candidate trace
metadata and explicit recency refill behavior when selected results underfill
`top_k`.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.11 / CM-045 | Context search records candidate breadth, routing strategy evidence, score breakdowns, freshness/refill behavior, and selected results. |
| Section 14.14 / CM-048 | Freshness conflict behavior remains explicit and does not auto-stale unrelated old evidence. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify the smallest safe slice. | Spark `019effbf-4c58-7f30-815d-7ecffcd2bc78` recommended candidate lineage + recency refill. |
| 2 | complete | Add focused RED tests for candidate trace breadth and recency refill. | RED: focused pytest failed because trace fields were absent and underfilled results were not refilled. |
| 3 | complete | Implement additive retrieval trace fields and bounded refill without changing successful ranking behavior. | GREEN: focused pytest -> `2 passed, 9 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `10 passed, 18 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_retrieval.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py -q -k "candidate_breadth or recency_refill"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_context_prepare.py -q -k "context_search or freshness or refill"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-045 candidate trace/refill residual | verified | `tests/test_retrieval.py::test_context_search_trace_captures_candidate_breadth_by_source`; `tests/test_retrieval.py::test_context_search_recency_refills_underfilled_results`; touched-area pytest `10 passed`. |
| CM-048 freshness behavior preservation | verified | Existing freshness tests remained green in touched-area verification. |

**Compliance Status: VERIFIED.** `CM-045` is now `COMPLIANT`; `CM-048`
remains `COMPLIANT`.
