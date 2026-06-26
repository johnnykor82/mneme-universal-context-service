# Plan: 01-rest-mneme-cost-report-parity

## Level

task

## Parent

`.planning/work/08-mcp-parity-default-session-resolution-versioning/plan.md`

## Status

complete

## Goal

Add the missing REST memory-tool parity endpoint
`POST /v1/tools/mneme_cost_report` so Section 14.9 and MCP parity no longer
depend on the MCP server calling the non-tool cost route directly.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.9 | Required REST tool endpoints include `POST /v1/tools/mneme_cost_report` and shared tool envelopes. |
| Section 15 | MCP tools proxy REST; REST remains canonical. |
| CM-043 | `/v1/tools/mneme_cost_report` missing as REST tool route. |
| S24-30, S24-31 | REST/MCP parity and error mapping for required tools. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests for REST `mneme_cost_report` parity and OpenAPI route
  documentation.
- [x] Implement the REST tool endpoint with the existing cost report semantics,
  v0 tool envelope, auth, and session scope behavior.
- [x] Update MCP cost-report proxy to call `/v1/tools/mneme_cost_report`
  instead of bypassing the REST tool route.
- [x] Run focused parity verification and record exact results.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/mcp_server.py`,
`mneme_service/rest_client.py`, `tests/test_mcp_contract.py`,
`tests/test_contract.py`, `tests/test_openapi.py`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q -k "cost_report or tool_routes or parity"`
- Task gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.9 / CM-043 | REST cost-report tool endpoint exists | ✓ met | RED focused gate failed for missing `/v1/tools/mneme_cost_report`; GREEN focused gate `3 passed, 50 deselected, 1 warning`; OpenAPI now includes all `TOOL_NAMES` tool paths. |
| Section 15 / S24-30-31 | MCP cost report proxies canonical REST tool route | ✓ met | `tests/test_mcp_contract.py::test_mcp_cost_report_tool_proxies_rest_tool_route` proves MCP sends `POST /v1/tools/mneme_cost_report`; touched-area gate `53 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
