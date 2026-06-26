# Plan: 17-residual-contract-fix-batch-n

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the Section 24 audit-disable residual by making audit mode a daemon
configuration only, rejecting production `DISABLED_TEST_ONLY`, and proving
public REST/MCP payloads cannot disable audit per call.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 16 | Memory-read audit modes are daemon configuration, not public request bypass |
| CM-028, CM-051, CM-062 | Audit schema/lifecycle residuals |
| S24-33 | `audit_disabled_only_by_test_daemon_config` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm minimal audit-mode scope.
- [x] Add failing tests for production rejection, test-only disabled mode, and
  ignored public audit-disable payload fields.
- [x] Implement minimal daemon-level `audit_mode` handling.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`mneme_service/config.py`, `mneme_service/app.py`, `tests/test_config.py`,
`tests/test_contract.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py -q -k "audit_disabled or audit_mode or memory_tools_audit"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_mcp_contract.py -q -k "audit or memory_read or memory_tools_write_audit"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-33 | Audit disable is only available through explicit test daemon configuration and not public payloads | ✓ met | `tests/test_config.py::test_audit_disabled_only_by_explicit_test_daemon_config`, `tests/test_contract.py::test_audit_disabled_only_by_test_daemon_config_and_not_public_payload`; RED -> `2 failed, 1 passed, 53 deselected, 1 warning`; focused GREEN -> `3 passed, 53 deselected, 1 warning`; touched-area gate -> `6 passed, 75 deselected, 1 warning`; full suite -> `280 passed, 1 warning`; compileall and `git diff --check` clean. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
