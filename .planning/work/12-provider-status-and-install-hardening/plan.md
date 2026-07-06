# Plan: 12-provider-status-and-install-hardening

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Fix post-install provider/status defects found by the 2026-07-06 full diagnostic
without changing the approved Core/Adapter architecture: Mneme Core keeps using
explicit configured providers only; Codex-specific hook normalization remains in
the standalone adapter.

## Planning Gate

- [x] User confirmed host-agent LLM fallback must not be added to Core.
- [x] User approved applying the remaining fixes.
- [x] Current work is mapped to existing v0 spec/provider/operations and Phase
  11 Core/Adapter boundary requirements.

**Gate Status: CLEARED - 2026-07-06**

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-core-embedding-status-accounting` | complete | Add RED/GREEN tests and fix successful embedding status and metrics accounting so indexed events are not reported as `PENDING`. |
| `02-provider-health-and-llm-degradation` | complete | Improve provider health/status reporting so configured/enabled providers are distinct from live timeout/degraded state. |
| `03-adapter-user-prompt-normalization-and-timeouts` | complete | Update Codex adapter hooks so `UserPromptSubmit` becomes canonical `USER_MESSAGE` where safe, and full-provider hooks use sufficient timeout. |
| `04-docs-install-diagnostics-and-release` | complete | Update install/provider docs and run release verification before committing/pushing Core and adapter. |

## Scope Boundaries

- Do not add host-agent LLM fallback to Mneme Core.
- Do not make Core Codex-specific.
- Do not inspect or edit live SQLite directly as verification.
- Do not revert unrelated dirty worktree files.
- Do not change secrets or print tokens.

## Verification Gates

- Core focused tests for embeddings, metrics, provider health, and enrichment.
- Core full suite: `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`.
- Core compile check: `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`.
- Core diff hygiene: `git diff --check`.
- Adapter focused tests for hook normalization/setup timeout.
- Adapter full suite and compileall.
- Adapter import-boundary and contract-drift checks where available.
- Installed runtime smoke if commits are produced.

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Canonical Sections 10, 14.8, 19 | Provider modes, reindex/maintenance, operational metrics must report real provider/indexing state. | complete | Focused embedding tests passed; full Core suite `307 passed, 1 warning`; compileall and diff hygiene passed. |
| Canonical Sections 12, 14.1, 15 | Fetch/capabilities/MCP-visible data must not misrepresent degraded provider state. | complete | Focused config/enrichment/openapi/release-doc tests `17 passed, 53 deselected`; full Core suite `307 passed, 1 warning`. |
| Extension R-003, R-004, SC-005 | Codex-specific normalization and hook behavior belongs in adapter. | complete | Adapter focused hook tests passed; full adapter suite `42 passed`; adapter compileall and diff hygiene passed. |

**Compliance Status: complete**

## Errors

| Time | Step | Error | Resolution |
|---|---|---|---|
