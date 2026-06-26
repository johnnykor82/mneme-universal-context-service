# Plan: 01-budget-contract-token-accounting

## Level

task

## Parent

`.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

## Status

complete

## Goal

Align `/v1/context/prepare` budget contract handling with Sections 11 and
14.13 before touching latest-user and wrapper behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 11 | Tokenizer metadata and STANDARD/QUALITY guardrails |
| Section 14.13 | Canonical `budget_split` keys, deprecated headroom behavior, cascade trace fields |
| CM-021, CM-047 | Tokenization and context prepare gaps |
| S24-18-22, S24-89, S24-99, S24-119 | Budget packing and trace evidence |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for unknown `budget_split` keys, deprecated
  `policy.headroom_ratio` normalization/warnings, and trace budget fields.
- [x] Add RED tests for STANDARD/QUALITY behavior when only
  `CHAR_APPROXIMATE` tokenization is available for a model-bound prepare.
- [x] Implement canonical key validation/normalization with minimal changes to
  the current prepare path.
- [x] Implement deterministic budget cascade trace fields needed by later
  latest-user and wrapper tasks.
- [x] Run targeted context prepare tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`,
`tests/test_context_prepare.py`, `tests/test_context_assembly.py`,
possibly `tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 11 / CM-021 | Tokenizer quality guardrails are explicit | partial | `test_context_prepare_warns_when_standard_cost_mode_uses_char_approximate`; full S24-20 reject-or-downgrade semantics remain a residual Phase 6 risk because the current slice emits `COST_MODE_DOWNGRADED` for changed STANDARD/QUALITY prepare instead of full 422/downgrade-to-MINIMAL behavior. |
| Section 14.13 / CM-047 | Canonical budget keys/defaults and trace fields are enforced | complete | `test_context_prepare_rejects_unknown_budget_split_keys`, `test_context_prepare_deprecated_headroom_ratio_is_normalized`, `test_context_prepare_uses_canonical_budget_split_defaults_when_omitted`, execution state trace assertions |
| S24-18-22, S24-89, S24-99, S24-119 | Required budget/trace tests are covered or mapped | partial | S24-18, S24-89, S24-99, and S24-119 have additional coverage; S24-20 remains partial/residual and S24-21/S24-22 stay covered by existing tests. |

**Compliance Status: COMPLETE FOR TASK 01 WITH S24-20 RESIDUAL RECORDED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
