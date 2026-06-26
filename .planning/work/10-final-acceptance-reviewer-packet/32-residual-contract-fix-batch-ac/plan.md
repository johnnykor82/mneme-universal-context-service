# Plan: 32-residual-contract-fix-batch-ac

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow typed schema residual for `mneme.message.v0` and
`mneme.turn.v0` OpenAPI contract coverage without changing runtime
compatibility.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.2 / CM-023 | Message schema typed shape and authority/latest-user contract evidence |
| Section 12.4 / CM-025 | Turn schema typed shape for completion, usage, outcome, and error fields |
| Section 20 | OpenAPI documents public schemas |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add failing OpenAPI contract assertions for `Message`, `MessageContentPart`, and richer `TurnCompleteRequest` fields. | RED: `tests/test_openapi.py -q -k "core_route_request_and_response_models"` failed for missing `Message` schema, then missing required `schema_version`. |
| 2 | complete | Add minimal Pydantic schema models, wire them into existing OpenAPI generation, and enforce message role/content-part validation. | GREEN: focused OpenAPI test passed; runtime validation RED/GREEN covered `invalid_message_role_and_part_type`. |
| 3 | complete | Update compliance matrix and planning evidence for CM-023/CM-025 if row-specific gaps are closed. | Matrix count check reports `COMPLIANT 39`, `PARTIAL 25`, `OUT_OF_SCOPE/FUTURE 1`; `git diff --check` passed. |

## Expected File Touches

- `tests/test_openapi.py`
- `mneme_service/schemas.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "core_route_request_and_response_models"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_context_prepare.py -q -k "openapi or turn_complete or context_prepare"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-023 message schema | ✓ met | `tests/test_openapi.py::test_openapi_documents_core_route_request_and_response_models` plus `tests/test_context_prepare.py::test_context_prepare_rejects_invalid_message_role_and_part_type`; latest-user tests remain green in touched-area gate. |
| CM-025 typed turn schema subrequirement | ✓ met | Richer `TurnCompleteRequest` OpenAPI fields are documented; derived state/segment/graph/provider/usage updates remain as a separate row-level CM-025 implementation gap. |
| Section 20 OpenAPI typed schemas | ✓ met | Focused OpenAPI test passed and touched-area gate passed with `30 passed, 37 deselected, 1 warning`. |

**Compliance Status: VERIFIED**
