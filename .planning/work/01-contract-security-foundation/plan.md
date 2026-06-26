# Plan: 01-contract-security-foundation

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Establish the v0 REST/OpenAPI/config/capabilities contract and enforce the
minimum auth/project-isolation/audit boundary required before later lifecycle
features can safely build on it.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 / CM-017 | Config defaults and validation for v0 foundation limits |
| Section 9 / CM-018 / CM-019 | Auth defaults, safe token handling, principals, project isolation |
| Section 12.6-12.7 / CM-027 / CM-028 | Public control schemas and audit record schema |
| Section 14.1 / CM-034 | Health, readiness, metrics advertisement, capabilities |
| Section 16 / CM-051 | Durable memory-read/auth audit behavior |
| Section 20 / CM-058 | OpenAPI as REST schema source of truth |
| Section 21 / CM-059 | Uniform REST error envelope |
| Sections 23-25 / CM-061 / CM-062 | Required tests and traceability |

## Active Task

Active Task: none

## Tasks

### 01-baseline-diff-and-red-tests
- Status: complete
- Goal: Reconcile prior dirty Phase 1A work and define RED tests for remaining first-phase gaps.
- Plan: `./01-baseline-diff-and-red-tests/plan.md`

### 02-schema-catalog-openapi-components
- Status: complete
- Goal: Complete the v0 schema catalog and OpenAPI component/route coverage needed for this phase.
- Plan: `./02-schema-catalog-openapi-components/plan.md`

### 03-config-capabilities-provider-status
- Status: complete
- Goal: Finish truthful config/capabilities/provider/status reporting without overclaiming unsupported features.
- Plan: `./03-config-capabilities-provider-status/plan.md`

### 04-auth-token-principal-boundary
- Status: complete
- Goal: Enforce auth defaults, safe token sources, insecure-dev guardrails, and principal derivation.
- Plan: `./04-auth-token-principal-boundary/plan.md`

### 05-project-scope-enforcement
- Status: complete
- Goal: Enforce effective project scope on current session, discovery, memory, export, delete, and future-ready blob paths.
- Plan: `./05-project-scope-enforcement/plan.md`

### 06-auth-failure-audit-safe-token-docs
- Status: complete
- Goal: Persist auth-failure audit records and remove unsafe token-in-argv guidance from safe docs/scripts.
- Plan: `./06-auth-failure-audit-safe-token-docs/plan.md`

### 07-phase-verification-evidence
- Status: complete
- Goal: Run focused/full verification and update compliance evidence without clearing future phases.
- Plan: `./07-phase-verification-evidence/plan.md`

## Section 24 Tests Targeted

Primary: 25, 26, 27, 29, 32, 33, 34, 37, 38, 39, 43, 59, 77, 84, 85, 111,
117, 118.

Spillover if touched: 1, 6, 7, 9, 10, 31, 48, 79, 113.

## Likely Files

`mneme_service/app.py`, `config.py`, `errors.py`, `security.py`, `storage.py`,
`schemas.py`, `mcp_server.py`, `rest_client.py`, focused tests, token-safety
docs/scripts, `README.md`, and `docs/MNEME_V0_COMPLIANCE_MATRIX.md`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_openapi.py tests/test_contract.py tests/test_security.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 8 / CM-017 | ~ partial | Config foundation, token-file/static-token settings, provider validation, and Phase 1 tests pass; later storage/blob/retention runtime keys remain |
| Section 9 / CM-018 / CM-019 / CM-052 | ~ partial | CM-018 now compliant; principals, scoped tokens, project visibility, safe docs/templates, and non-loopback insecure-dev guard implemented; later route families and token-file permissions remain |
| Sections 12.6-12.7 / CM-027 / CM-028 | ~ partial | Core/tool OpenAPI envelopes and expanded audit schema implemented; later route-specific schemas and forensic audit behavior remain |
| Section 14.1 / CM-034 | ~ partial | Capabilities truthfully advertise Phase 1 support and unsupported future features; metrics/blob/retention/reindex remain |
| Sections 16, 20, 21 / CM-051 / CM-058 / CM-059 | ~ partial | Auth/memory audit, OpenAPI security/schema foundation, and provider/auth error envelopes verified; later error families remain |
| Sections 23-25 / CM-061 / CM-062 / CM-065 | ~ partial | Phase 1 matrix and Section 24 evidence updated; final acceptance waits for all later phases |

**Compliance Status: PHASE 1 COMPLETE; OVERALL V0 COMPLIANCE PARTIAL**

## Notes

- Do not begin this phase until the roadmap Planning Gate is explicitly approved.
- Prior Phase 1A dirty-worktree changes must be reviewed before editing the same files.
