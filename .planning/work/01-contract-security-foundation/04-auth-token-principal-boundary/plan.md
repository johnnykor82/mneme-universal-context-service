# Plan: 04-auth-token-principal-boundary

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Make authentication default-safe and derive principals/scopes from configured
owner or static scoped tokens.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 9 | Bearer auth default, token file/env paths, insecure-dev restrictions |
| Section 17.1 | Threat model boundary for local token and cross-project leakage |
| Section 21 | 401/403 error envelopes |
| CM-018, CM-019, CM-052, CM-059 | Auth/token/security rows |
| S24-29, S24-59, S24-118 | Discovery guidance, readiness auth, auth-failure principal |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Add tests for auth required by default, including loopback.
  - Verification: missing/invalid token returns `401 UNAUTHENTICATED`.
- [x] Add tests for non-loopback insecure-dev rejection.
  - Verification: invalid config/startup path fails closed.
- [x] Implement env/token-file/static-token principal derivation.
  - Verification: tests assert OWNER `*` scope and scoped ADAPTER role behavior.
- [x] Return uniform auth/forbidden error envelopes.
  - Verification: contract tests inspect `error.code`, `retryable`, and details.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 9 / CM-018 / CM-019 | ~ partial | Added token-file loading, `[[auth.static_tokens]]`, owner fallback principal, and scoped ADAPTER authentication; full scope enforcement continues in task 05 |
| Section 17.1 / CM-052 | ~ partial | Added non-loopback insecure-dev rejection and principal derivation without token leakage |
| Section 21 / CM-059 | ~ partial | Auth failure retains uniform `401 UNAUTHENTICATED`; `403 FORBIDDEN` envelope is present and will be broadened in task 05 |
| S24-29 / 59 / 118 | ~ partial | Added auth token/principal tests and retained readiness/auth-failure tests; discovery leakage checks continue in task 05 |

**Compliance Status: COMPLETE FOR TASK 04; PHASE 1 SECURITY ROWS REMAIN PARTIAL**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- Do not add enterprise RBAC or dynamic token admin APIs; those are future scope.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `38 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_codex_adapter.py tests/test_codex_hooks.py -q`
  -> `50 passed`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m py_compile mneme_service/config.py mneme_service/security.py mneme_service/app.py mneme_service/cli.py`
  -> passed.
