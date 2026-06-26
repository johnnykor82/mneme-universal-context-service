# Plan: 06-auth-failure-audit-safe-token-docs

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Persist auth-failure audit records and update safe docs/scripts away from
bearer tokens in command-line arguments.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 9 | Safe token handling and MCP startup paths |
| Section 12.7 | `AUTH_FAILURE` audit principal shape |
| Section 16 | Audit cannot be disabled per public request |
| CM-019, CM-028, CM-051, CM-052 | Token and audit gaps |
| S24-32, S24-33, S24-34, S24-118 | Audit records and unauthenticated principal |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Add tests for pre-token `AUTH_FAILURE` audit record persistence.
  - Verification: audit row has principal name/role `UNAUTHENTICATED`.
- [x] Ensure public requests cannot disable audit.
  - Verification: test-only unaudited mode is daemon-config-only.
- [x] Replace safe-path docs/scripts that recommend `--token` args.
  - Verification: `rg -n -- "--token|MNEME_AUTH_TOKEN" README.md docs scripts adapters` shows only legacy/development mentions with safe alternatives.
- [x] Ensure token values are not logged or exposed in OpenAPI/examples.
  - Verification: targeted docs/tests assert no literal secret leakage.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 9 / CM-019 | ~ partial | Safe docs/templates no longer recommend token-in-argv for daemon/MCP/Codex flows; legacy CLI flags remain for compatibility |
| Section 12.7 / CM-028 | ~ partial | Auth-failure audit records persist with schema version and `UNAUTHENTICATED` principal |
| Section 16 / CM-051 | ~ partial | Memory read audit behavior retained and tested; public request payloads cannot disable current audit path |
| Section 17.1 / CM-052 | ~ partial | Token values are not emitted in generated safe docs/templates; OpenAPI bearer auth has no raw authorization header parameter |
| S24-32 / 33 / 34 / 118 | ~ partial | Focused auth-failure, memory-read audit, and safe docs/template tests pass |

**Compliance Status: COMPLETE FOR TASK 06; MATRIX EVIDENCE FINALIZED IN TASK 07**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- `--token` may remain as a legacy/development option, but not as a recommended safe path.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py::test_safe_docs_and_generated_templates_do_not_recommend_token_argv tests/test_contract.py::test_auth_failure_audit_uses_unauthenticated_principal tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion -q`
  -> `3 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py tests/test_codex_adapter.py tests/test_mcp_contract.py::test_codex_mcp_usage_docs_are_tools_only_and_config_is_valid -q`
  -> `35 passed`.
- Verification:
  token-argv `rg` over safe docs/templates returned no matches.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `43 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_codex_adapter.py tests/test_codex_hooks.py -q`
  -> `50 passed`.
