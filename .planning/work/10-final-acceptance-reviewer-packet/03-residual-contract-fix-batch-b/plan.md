# Plan: 03-residual-contract-fix-batch-b

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Implement a bounded context-prepare residual fix for S24-20: model-bound
STANDARD/QUALITY context prepare must reject or downgrade `CHAR_APPROXIMATE`
token estimates instead of silently treating them as good enough.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 11, 14.13 | Tokenization quality and context prepare budget accounting |
| CM-021, CM-047, CM-062 | Tokenizer-quality residual and Section 24 mapping |
| S24-20 | `context_prepare_rejects_char_approx_for_standard_quality_model_bound_prepare` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for model-bound STANDARD/QUALITY prepare with
  `CHAR_APPROXIMATE` tokenizer quality.
- [x] Implement minimal reject/downgrade semantics consistent with the spec and
  existing local fallback behavior.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py` if needed,
`tests/test_context_prepare.py`, `tests/test_context_assembly.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q -k "tokenizer_quality or char_approx"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 11, 14.13 / CM-021, CM-047 | Tokenizer quality reject/downgrade semantics | ✓ met | `validate_prepare` rejects explicit model-bound STANDARD/QUALITY prepare using local `CHAR_APPROXIMATE` with `422 VALIDATION_ERROR` and downgrade metadata; non-model-bound local diagnostics still return warning-only. |
| S24-20 / CM-062 | Section 24 tokenizer-quality required test | ✓ met | `tests/test_context_prepare.py::test_context_prepare_rejects_char_approx_for_standard_quality_model_bound_prepare`; focused gate `2 passed, 17 deselected, 1 warning`; touched-area gate `47 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
