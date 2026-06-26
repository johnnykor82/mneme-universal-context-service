# Plan: 13-residual-contract-fix-batch-j

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the Section 24 session-discovery residuals by adding spec pagination
controls and explicit discovery no-leak evidence while preserving existing
`limit` compatibility.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.10 | Session discovery, scoped/redacted recovery, pagination, best-guess semantics |
| CM-044, CM-062 | Session discovery Section 24 residuals |
| S24-26 | `resolve_session_filters_and_paginates` |
| S24-27 | `list_sessions_filters_and_paginates` |
| S24-29 | `not_found_guides_discovery_without_leaking_metadata` |
| S24-78 | `resolve_session_best_guess_semantics_are_stable` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact residuals and minimal
  implementation scope.
- [x] Add failing REST/MCP tests for `page_size`, `page_token`,
  `next_page_token`, `matches_truncated`, and no-leak guidance.
- [x] Implement minimal stable pagination support for session discovery while
  accepting legacy `limit`.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/storage.py`, `mneme_service/app.py`,
`mneme_service/mcp_server.py`, `tests/test_contract.py`,
`tests/test_mcp_contract.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py -q -k "session_discovery or resolve_session or list_sessions"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py tests/test_openapi.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-26 | Resolve session filters and paginates without silent truncation | ✓ met | `tests/test_contract.py::test_session_discovery_filters_and_paginates_without_silent_truncation`; focused RED -> `1 failed, 5 passed, 51 deselected, 1 warning`; focused GREEN -> `6 passed, 51 deselected, 1 warning`; touched-area gate -> `65 passed, 1 warning`; full suite -> `274 passed, 1 warning`. |
| S24-27 | List sessions filters and paginates without silent truncation | ✓ met | `tests/test_contract.py::test_session_discovery_filters_and_paginates_without_silent_truncation`, `tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity`; touched-area gate -> `65 passed, 1 warning`; full suite -> `274 passed, 1 warning`. |
| S24-29 | Not-found guidance is scoped/redacted and does not leak metadata | ✓ met | `tests/test_contract.py::test_not_found_discovery_guidance_is_scoped_and_redacted`; focused GREEN -> `6 passed, 51 deselected, 1 warning`; full suite -> `274 passed, 1 warning`. |
| S24-78 | Resolve-session best-guess semantics remain deterministic | ✓ met | Existing best-guess tests stayed green in focused Batch J gate: `tests/test_contract.py::test_resolve_session_best_guess_prefers_exact_project_path_before_recency`, `tests/test_contract.py::test_resolve_session_best_guess_is_null_for_recency_only_ambiguity`; touched-area gate -> `65 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
