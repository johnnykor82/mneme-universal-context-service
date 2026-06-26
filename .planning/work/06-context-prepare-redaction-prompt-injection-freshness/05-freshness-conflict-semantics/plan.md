# Plan: 05-freshness-conflict-semantics

## Level

task

## Parent

`.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

## Status

complete

## Goal

Add honest adapter/source-supplied freshness and conflict semantics without
letting Mneme core claim independent current file or git verification.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.14 | Freshness values, adapter/source conflict rule, no independent current-source claims |
| CM-048, CM-054 | Freshness and prompt-safety gaps |
| S24-69, S24-70, S24-89, S24-99, S24-119 | Freshness/conflict evidence in context prepare traces |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests that retrieval/context evidence carries `freshness` when
  supplied by adapter/source metadata.
- [x] Add RED tests that adapter-supplied conflicts emit
  `FRESHNESS_CONFLICT` and drop or downgrade conflicting memory evidence.
- [x] Add RED tests that old Mneme evidence is not automatically labeled
  `STALE_OR_CONFLICTING` without source-supplied conflict metadata.
- [x] Implement freshness propagation and conflict trace warnings with scoped
  metadata only.
- [x] Run targeted retrieval/context tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `tests/test_retrieval.py`,
`tests/test_context_prepare.py`, possibly `tests/test_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_context_prepare.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.14 / CM-048 | Freshness and conflict semantics are adapter/source supplied | ✓ met | `context_search` results include `freshness`; context-prepare wrappers and trace selected events include `freshness`; explicit `CURRENT` + `conflicting_event_ids` drops conflicting memory evidence and records `FRESHNESS_CONFLICT`; old evidence without source metadata is not auto-marked `STALE_OR_CONFLICTING`. |
| S24-69, S24-70, S24-89, S24-99, S24-119 | Freshness/conflict trace tests are covered or mapped | ✓ met for Task 05 scope | Task 05 focused gate `49 passed, 1 warning`; full suite `226 passed, 1 warning`; compileall and `git diff --check` passed. |

**Compliance Status: VERIFIED FOR TASK 05 SCOPE**

Residual note: warning shape remains endpoint-specific (`context_prepare`
strings vs memory-tool warning objects), and freshness-conflict drops do not
refill from a larger secondary candidate set.

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | RED Task 05 tests | Expected failures: retrieval/context evidence lacked `freshness`, explicit conflicts were not dropped, and old evidence had no freshness field. | Added source-supplied freshness helpers, conflict filtering, trace warnings, and wrapper/result freshness propagation. |
| 2 | First GREEN conflict trace | `dropped_events` lost `FRESHNESS_CONFLICT` because budget packing overwrote earlier freshness drops. | Preserved freshness drops and extended with budget drops instead of replacing. |
