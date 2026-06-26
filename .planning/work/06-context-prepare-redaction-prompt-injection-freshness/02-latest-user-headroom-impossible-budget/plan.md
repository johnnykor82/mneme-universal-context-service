# Plan: 02-latest-user-headroom-impossible-budget

## Level

task

## Parent

`.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

## Status

complete

## Goal

Ensure context prepare never silently truncates or drops the current latest
user request and returns the exact v0 budget failure reasons.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.13 | Hard headroom reserve, latest-user preservation, impossible-budget 422 reasons |
| CM-021, CM-047 | Budget/headroom and context prepare gaps |
| S24-55, S24-70, S24-89, S24-99 | Latest-user and impossible-budget required tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests proving the latest user-authored message is preserved
  unmodified when it fits.
- [x] Add RED tests for `LATEST_USER_MESSAGE_EXCEEDS_BUDGET`.
- [x] Add RED tests for `MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET`.
- [x] Implement whole-message latest-user protection and hard
  `minimum_headroom_tokens` reserve using the Task 01 budget trace fields.
- [x] Run targeted context prepare tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `tests/test_context_prepare.py`,
`tests/test_context_assembly.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.13 / CM-047 | Latest user request is protected and hard headroom is reserved | complete | `test_context_prepare_preserves_latest_user_message_bytes_for_fitting_budget`, `test_context_prepare_latest_user_message_exceeds_budget_returns_422_reason`, `test_context_prepare_minimum_required_content_over_budget_returns_422_reason` |
| S24-55, S24-70, S24-89, S24-99 | Required latest-user/budget tests are covered | complete | S24-55/S24-70 added; S24-89 covered by Task 01 unknown-key test; S24-99 continuation-query regression remains green. |

**Compliance Status: COMPLETE**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
