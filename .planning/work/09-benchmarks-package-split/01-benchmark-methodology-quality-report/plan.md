# Plan: 01-benchmark-methodology-quality-report

## Level

task

## Parent

`.planning/work/09-benchmarks-package-split/plan.md`

## Status

complete

## Goal

Make benchmark output and documentation review-ready: methodology is explicit,
labeled quality reports are available when labels are supplied, and Mneme does
not claim token/cost savings without comparative baseline evidence.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 10 | Cost savings claims require benchmark baseline evidence. |
| Section 19 | Benchmark command and quality/coverage reporting expectations. |
| Section 24 quality/benchmark tests | Labeled benchmark quality report evidence. |
| CM-020, CM-057, CM-062 | Cost/operations/acceptance evidence affected by benchmark claims. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for benchmark methodology fields and labeled quality
  report output.
- [x] Implement or document structured benchmark methodology in the benchmark
  command/output.
- [x] Ensure docs/tests prevent unsupported token/cost-savings claims.
- [x] Run focused benchmark verification and record exact results.

## Expected File Touches

`mneme_service/benchmarks.py`, `tests/test_benchmarks.py`,
`README.md`, `docs/PUBLICATION_CHECKLIST.md`, possibly
`docs/TESTING_AND_CI.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py -q`
- Task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_config.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 10, 19 | Benchmark methodology and no unsupported savings claims | ✓ met | `tests/test_benchmarks.py` asserts `methodology`, local fake provider mode, `comparative_baseline=NOT_RUN`, `*_reduction_claim=NOT_CLAIMED`, and absence of `token_savings`/`cost_savings` strings. |
| CM-020, CM-057, CM-062 | Benchmark/quality evidence updated | ✓ met | `mneme_service/benchmarks.py` emits `mneme.benchmark_quality_report.v0` with synthetic labels, precision@k, recall@k, MRR, and confusion counts; `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_config.py -q` -> `22 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
