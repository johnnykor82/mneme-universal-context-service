# Plan: 22-residual-contract-fix-batch-s

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow Section 24 OpenAPI residual for S24-43 and S24-85 by adding
machine-checked public examples and schema-source-of-truth assertions for core
REST request/response/error contracts.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 20 | OpenAPI is REST schema source of truth, parseable, documents security/error envelopes, and keeps examples in sync |
| Section 21 | Common failure cases use uniform error envelopes |
| CM-027, CM-058, CM-062 | Control schemas, OpenAPI/SDK readiness, required tests |
| S24-43 | `openapi_schema_is_parseable_and_matches_examples` |
| S24-85 | `public_core_schemas_are_defined_in_openapi` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Inspect current OpenAPI tests and component schemas for missing examples.
- [x] Add focused tests that assert core public schemas include success examples
      and common error envelope examples.
- [x] Add the smallest OpenAPI/schema metadata needed to satisfy the tests.
- [x] Run focused and touched-area OpenAPI verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_openapi.py`, `mneme_service/schemas.py`, possibly
`mneme_service/app.py` only for custom OpenAPI examples/error response metadata,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "examples or public_core_schemas or parseable"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_mcp_contract.py -q -k "openapi or schema or session_resolution or tool_envelope"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-43 | OpenAPI schema is parseable and matches examples | compliant | `tests/test_openapi.py::test_openapi_schema_is_parseable_and_matches_examples`; focused Batch S gate `2 passed`; touched-area gate `13 passed`; full suite `285 passed`. |
| S24-85 | Public core schemas are defined in OpenAPI | compliant | `tests/test_openapi.py::test_openapi_documents_core_route_request_and_response_models`; focused Batch S gate `2 passed`; touched-area gate `13 passed`; full suite `285 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | Focused OpenAPI test collection | `IndentationError` in `tests/test_openapi.py` after inserting the examples test below the bearer-security loop. | Fixed the single indentation error and reran focused verification. |
