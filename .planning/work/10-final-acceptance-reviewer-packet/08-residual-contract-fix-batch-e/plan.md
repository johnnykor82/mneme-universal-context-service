# Plan: 08-residual-contract-fix-batch-e

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Audit and close the narrow S24-105 residual for memory-read summary and
`MEMORY_READ_EVIDENCE` graph-edge contract evidence.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 15, 16 | Memory-read feedback, summaries, audit, traces, and graph evidence edges |
| CM-028, CM-029, CM-051, CM-062 | Audit/graph/memory-read residual and Section 24 mapping |
| S24-105 | Memory-read summary and memory-read evidence edges match contract |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to determine whether this is an
  implementation gap or a stale matrix/test-evidence gap.
- [x] Add failing tests for missing memory-read summary or evidence-edge
  contract details.
- [x] Implement minimal code only if the focused tests prove a runtime gap.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

Likely `tests/test_contract.py`, possibly `mneme_service/app.py` or
`mneme_service/storage.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "memory_read"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py tests/test_graph.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-028, CM-029, CM-051 / S24-105 | Memory-read summary and evidence edges match contract | ✓ met | `tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion` now asserts bounded redacted summary fields and `MEMORY_READ_EVIDENCE` edge weight; `tests/test_contract.py::test_mneme_cost_report_tool_creates_memory_read_audit_trace_and_updates_state` covers cost-report memory-read trace/audit/state feedback. Focused RED -> `1 failed, 1 passed, 27 deselected, 1 warning`; focused GREEN -> `2 passed, 27 deselected, 1 warning`; touched-area gate -> `59 passed, 1 warning`; full suite -> `266 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
