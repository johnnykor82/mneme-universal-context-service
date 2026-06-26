# Plan: 08-mcp-parity-default-session-resolution-versioning

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Complete MCP/REST parity, trusted default-session behavior, session-resolution
metadata, and MCP versioning.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.9, 15 | MCP tool contract, REST parity, session resolution, errors |
| CM-043, CM-049, CM-050 | MCP parity gaps |
| S24-28, 30-31, 57, 60, 83, 90, 117 | Required tests |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-rest-mneme-cost-report-parity` | complete | Add missing REST `/v1/tools/mneme_cost_report` parity endpoint and OpenAPI evidence. |
| `02-tool-envelope-session-resolution` | complete | Add `session_resolution` metadata to session-bound REST/MCP tool envelopes with explicit argument source. |
| `03-mcp-default-session-stale` | complete | Add trusted immutable MCP default-session support, stale-default validation, and omission behavior without mutable global state. |
| `04-mcp-error-version-parity` | complete | Align MCP/REST error mapping and version/schema reporting/rejection behavior. |
| `05-phase-verification-evidence` | complete | Run focused/full verification and update matrix, Section 24 mapping, progress, findings, and roadmap. |

## Expected File Touches

| Area | Expected files |
|---|---|
| REST tool parity | `mneme_service/app.py`, `mneme_service/schemas.py`, `tests/test_contract.py`, `tests/test_openapi.py`, `tests/test_mcp_contract.py` |
| MCP default session | `mneme_service/mcp_server.py`, `mneme_service/rest_client.py`, `tests/test_mcp_contract.py` |
| Error/version parity | `mneme_service/rest_client.py`, `mneme_service/app.py`, `mneme_service/tool_names.py`, `tests/test_mcp_contract.py`, `tests/test_openapi.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Phase 8 focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
- MCP-only regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- REST exposes every required Section 14.9 tool endpoint, including
  `/v1/tools/mneme_cost_report`.
- Session-bound REST and MCP tool results include `session_resolution.source`
  and resolved `session_id`.
- MCP accepts omitted `session_id` only from trusted immutable default context
  or host-injected context, never from mutable cross-project state.
- Stale trusted default sessions return MCP-only `DEFAULT_SESSION_STALE` with
  discovery guidance instead of empty results.
- MCP error mapping includes the v0 table and retryable flags for retryable
  storage/rate/provider failures.
- Capabilities/versioning evidence proves `mcp_tool_versions` and schema
  version behavior without renaming v0 tools.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 14.9, 15 | ✓ met | REST/MCP cost-report parity, session-resolution metadata, trusted/default and host-injected MCP sessions, stale-default error, MCP error mapping, and tool schema-version rejection are implemented and tested. |
| CM-043, CM-049, CM-050 | ✓ met | Matrix rows moved to `COMPLIANT` with Phase 8 evidence. |
| S24-28, 30-31, 57, 60, 83, 90, 117 | ✓ met | Matrix Section 24 rows moved to `COMPLIANT`; Phase 8 focused gate `61 passed, 1 warning`; full suite `252 passed, 1 warning`. |

**Compliance Status: VERIFIED**
