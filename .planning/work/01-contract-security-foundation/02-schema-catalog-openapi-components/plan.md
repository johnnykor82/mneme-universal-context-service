# Plan: 02-schema-catalog-openapi-components

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Define or complete typed v0 public schemas and make `/openapi.json` advertise
the implemented contract truthfully.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.6 | Control request/result schemas |
| Section 12.7 | Audit record schema |
| Section 20 | OpenAPI is REST schema source of truth |
| Section 21 | Error envelope schemas and examples |
| CM-027, CM-028, CM-058, CM-059 | OpenAPI/schema/error gaps |
| S24-43, S24-85 | Parseable OpenAPI and public core schemas |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Inventory currently documented OpenAPI components and missing public schemas.
  - Verification: generated OpenAPI contains expected component names or explicit gaps.
- [x] Add typed schema models for first-phase public responses/errors and shared envelopes.
  - Verification: `tests/test_openapi.py -q` covers component names and route schemas.
- [x] Ensure auth/security schemes and route errors are documented in OpenAPI.
  - Verification: OpenAPI test asserts bearer scheme and error envelope references.
- [x] Keep unsupported future features advertised as false or absent.
  - Verification: capabilities/OpenAPI tests reject overclaiming.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 12.6 / CM-027 | ~ partial | Added `ToolRequestPayload` and `ToolResponseEnvelope` OpenAPI coverage for `/v1/tools/*`; deeper route-specific models remain in later phases |
| Section 12.7 / CM-028 | ~ partial | `ErrorEnvelope` and audit schema components exist; full route-wide audit schema evidence remains in task 06 |
| Section 20 / CM-058 | ~ partial | `tests/test_openapi.py` covers parseable OpenAPI, core route models, tool envelopes, and bearer security without raw auth header parameters |
| Section 21 / CM-059 | ~ partial | Core and tool routes document common `ErrorEnvelope` responses; future blob/range/storage-busy/rate-limit envelopes remain pending |
| S24-43 / S24-85 | ~ partial | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q` -> `5 passed, 1 warning` |

**Compliance Status: COMPLETE FOR PHASE 1 FOUNDATION SCOPE; OVERALL ROWS REMAIN PARTIAL**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- Full blob/session/state/segment schemas may be completed in later feature phases if not yet implemented, but OpenAPI must not misrepresent behavior.
- Added permissive Pydantic request/response models for health, session start,
  event ingest, session readiness, and shared memory tool envelopes.
- Hid the raw dependency `authorization` header from OpenAPI so bearer auth is
  represented by `BearerAuth` security scheme instead of a duplicate header
  parameter.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_openapi.py tests/test_contract.py -q`
  -> `32 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces -q`
  -> `2 passed`.
