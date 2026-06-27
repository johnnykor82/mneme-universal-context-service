# Mneme Core/Adapter Boundary Reviewer Packet

Status: Phase 11 implementation evidence ready for reviewer acceptance
Date: 2026-06-27

## Scope

This packet covers the approved Core/Adapter Boundary Refactor:
`docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md`.

The v0 Core compliance packet remains `docs/MNEME_V0_REVIEWER_PACKET.md`.
This packet is the post-v0 boundary-correction evidence proving that Mneme Core
is host-neutral and Codex behavior is adapter-owned.

## Evidence Index

| Evidence | Path |
|---|---|
| Approved boundary spec | `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` |
| Host adapter contract | `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md` |
| Dependency extraction audit | `docs/reviews/core_adapter_dependency_audit.md` |
| Deleted-test coverage mapping | `docs/reviews/core_adapter_test_coverage_mapping.md` |
| Adapter patch evidence | `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/02-codex-adapter-sync-first/mneme-codex-adapter-sync.patch` |
| Cross-repository verification | `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/06-cross-repository-verification-and-reviewer-packet/cross_repository_verification.json` |
| Runtime smoke evidence | `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/06-cross-repository-verification-and-reviewer-packet/runtime_smoke.json` |
| Phase plan evidence | `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md` |

## Verification Summary

Core verification:

- Full Core suite: `307 passed, 1 warning`.
- OpenAPI suite: `11 passed, 1 warning`.
- Compile: `mneme_service`, `tests`, and `scripts` passed compileall.
- Boundary checks: `check_core_boundary.py`, `check_distribution_boundary.py`,
  `check_contract_version.py`, and `check_publication_hygiene.py` passed.
- Core wheel SHA-256:
  `f199bcb36f3c31ba80845959871d0b134be751c16f7071ab5fc32bfed99e8a50`.
- Core sdist SHA-256:
  `7bd22e4e81b66a8ca2d956580874d53ae8644298f1a0556e4a8f165636ed985e`.

Adapter verification:

- Adapter suite against the freshly built Core wheel: `40 passed`.
- Adapter compileall: passed.
- Adapter AST import-boundary check: passed.
- Adapter Core contract-drift check against fresh Core OpenAPI: passed.
- Adapter patch evidence includes CI steps for import-boundary and
  contract-drift checks.

Combined runtime smoke:

- Core daemon started from the installed wheel against a clean temporary DB.
- Codex adapter imported a transcript through REST.
- Replay was idempotent: first ingest accepted 3 events, replay accepted 0 and
  reported 3 duplicates.
- `context_search` and `fetch_event` returned expected evidence.
- Token and fake secret leakage checks passed.

## Success Criteria

| ID | Status | Evidence |
|---|---|---|
| SC-001 | complete | Core boundary and distribution checks pass; Core no longer contains `mneme_service/codex_*`, `adapters/codex`, Codex skill files, or Codex tests. |
| SC-002 | complete | Adapter patch evidence owns hooks, ingest, setup/status/service, docs, and `mneme-memory` skill. |
| SC-003 | complete | Full Core suite passes without Codex-specific tests: `307 passed`. |
| SC-004 | complete | `docs/reviews/core_adapter_test_coverage_mapping.md` maps deleted Codex Core tests to generic Core or adapter coverage. |
| SC-005 | complete | Adapter pytest against fresh Core wheel: `40 passed`. |
| SC-006 | complete | `runtime_smoke.json` records health, capabilities, ingest, replay, search, fetch, and leakage checks. |
| SC-007 | complete | README, installation docs, and `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md` describe REST/MCP direct integration and adapter ownership. |
| SC-008 | complete | Core CI runs source boundary, distribution boundary, contract-version, and publication-hygiene checks. |
| SC-009 | complete | Publication hygiene check passed against source plus wheel/sdist artifacts. |
| SC-010 | complete | Distribution boundary check passed against wheel and sdist artifacts. |
| SC-011 | complete | `cross_repository_verification.json` records Core artifact hashes, Core contract version, adapter revision, and installed package identity. |
| SC-012 | complete | `docs/MNEME_CONTRACT_VERSION` is `0.7.5`; adapter declares `>=0.7,<0.8`; contract-version and contract-drift checks pass. |
| SC-013 | complete | `docs/reviews/core_adapter_dependency_audit.md` records move/promote/delete/defer decisions. |
| SC-014 | complete | Adapter AST import-boundary check passes and is wired into adapter CI patch evidence. |
| SC-015 | complete | No rollback was triggered; local build-isolation and localhost sandbox issues were resolved without changing product behavior. Commit/push remains a separate owner approval. |

## Reviewer Decision

Recommended decision: `ACCEPT_PHASE11_CORE_ADAPTER_BOUNDARY_EVIDENCE`.

Publication note: Core and adapter patches are verified locally, but committing
and pushing both repositories remains a separate explicit owner action.
