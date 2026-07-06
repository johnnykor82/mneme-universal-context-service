# Roadmap: Mneme v0 Compliance

## Project Goal

Bring the current Mneme alpha implementation into verifiable compliance with
`docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5.

## Planning Gate

- [x] `.planning/spec.md` wrapper created around the already approved canonical spec
- [x] Canonical source, baseline audit, implementation plan, and legacy context recorded
- [x] Spec Format Assessment completed for the non-template canonical spec
- [x] All phases listed below with estimated effort
- [x] `plan.md` exists for every phase
- [x] Detailed task `plan.md` files exist for the current phase
- [x] Future phase stub `plan.md` files exist
- [x] User has reviewed and explicitly approved this `.planning/` structure

**Gate Status: CLEARED - 2026-06-22**

Execution may proceed under the active path. Commit/push still require separate
explicit permission.

## Extension Planning Gate: Phase 11 Core/Adapter Boundary

- [x] Extension spec approved for planning:
  `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md`
- [x] Extension Spec Format Assessment recorded in `.planning/spec.md`
- [x] Phase 11 added to roadmap
- [x] Phase 11 `plan.md` exists
- [x] Detailed task `plan.md` files exist for Phase 11
- [x] User has reviewed and explicitly approved the Phase 11 plan structure

**Gate Status: CLEARED - 2026-06-27**

Phase 11 implementation may proceed under the active path. Commit/push still
require separate explicit permission.

## Active Phase

Active Phase: none

## Phases

### 01-contract-security-foundation
- Status: complete
- Goal: Establish the v0 public contract and security boundary before deeper lifecycle work.
- Spec coverage: Sections 8, 9, 12.6-12.7, 14.1, 16, 17.1, 20, 21, 23-25, 27-30
- Matrix rows: CM-017, CM-018, CM-019, CM-020, CM-027, CM-028, CM-034, CM-052, CM-058, CM-059, CM-061, CM-062, CM-065
- Effort: 1-2 focused implementation cycles after approval
- Plan: `.planning/work/01-contract-security-foundation/plan.md`

### 02-storage-migrations-writer-idempotency
- Status: complete
- Goal: Add startup schema integrity, migrations, serialized writer behavior, and the idempotency ledger.
- Spec coverage: Sections 18, 22
- Matrix rows: CM-056, CM-060
- Effort: 1 focused implementation cycle
- Plan: `.planning/work/02-storage-migrations-writer-idempotency/plan.md`

### 03-blob-bytes-ref-export-delete-multipart
- Status: complete
- Goal: Implement owned SQLite blob/BYTES_REF lifecycle, multipart ingest, export, delete, and GC semantics.
- Spec coverage: Sections 13, 14.2, 14.3, 14.8
- Matrix rows: CM-031, CM-032, CM-033, CM-036, CM-042, CM-059, CM-060, CM-062
- Effort: 1-2 focused implementation cycles
- Plan: `.planning/work/03-blob-bytes-ref-export-delete-multipart/plan.md`

### 04-session-lifecycle-readiness-retention
- Status: complete
- Goal: Complete session get/close/generated-id behavior, readiness, retention cleanup, and lifecycle audit.
- Spec coverage: Sections 12.1, 13.6, 14.1, 14.2, 14.14, 16, 22
- Matrix rows: CM-022, CM-033, CM-034, CM-035, CM-042, CM-048, CM-051, CM-055, CM-056, CM-058, CM-060, CM-061, CM-062
- Effort: 1 focused implementation cycle
- Plan: `.planning/work/04-session-lifecycle-readiness-retention/plan.md`

### 05-state-segments-lineage-graph-routing
- Status: complete
- Goal: Align execution state, segment REST, lineage, graph traversal, classifier, and routing intelligence.
- Spec coverage: Sections 12.5, 12.8, 12.9, 14.5, 14.5.1, 14.6, 14.10-14.12
- Matrix rows: CM-026, CM-029, CM-030, CM-039, CM-040, CM-044, CM-045, CM-046
- Effort: 2 focused implementation cycles
- Plan: `.planning/work/05-state-segments-lineage-graph-routing/plan.md`

### 06-context-prepare-redaction-prompt-injection-freshness
- Status: complete
- Goal: Complete context prepare budget semantics, latest-user protection, evidence wrappers, redaction, and freshness.
- Spec coverage: Sections 11, 14.13, 14.14, 17.2, 17.3
- Matrix rows: CM-021, CM-047, CM-048, CM-053, CM-054
- Effort: 1-2 focused implementation cycles
- Plan: `.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

### 07-operations-metrics-maintenance-reindex
- Status: complete
- Goal: Add metrics, maintenance jobs, provider retry/backoff, reindex lifecycle, and operational observability.
- Spec coverage: Sections 14.7, 14.8, 19
- Matrix rows: CM-020, CM-041, CM-042, CM-057
- Effort: 1 focused implementation cycle
- Plan: `.planning/work/07-operations-metrics-maintenance-reindex/plan.md`

### 08-mcp-parity-default-session-resolution-versioning
- Status: complete
- Goal: Complete MCP default-session UX, session-resolution metadata, versioning, and REST/MCP error parity.
- Spec coverage: Sections 14.9, 15
- Matrix rows: CM-043, CM-049, CM-050
- Effort: 1 focused implementation cycle
- Plan: `.planning/work/08-mcp-parity-default-session-resolution-versioning/plan.md`

### 09-benchmarks-package-split
- Status: complete
- Goal: Finalize benchmark methodology and enforce clean core/adapter package boundaries.
- Spec coverage: Sections 4, 7, 10, 19, 26
- Matrix rows: CM-010, CM-011, CM-016, CM-064
- Effort: 0.5-1 focused implementation cycle
- Plan: `.planning/work/09-benchmarks-package-split/plan.md`

### 10-final-acceptance-reviewer-packet
- Status: complete
- Goal: Prove Mneme fully complies with `docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5 and produce the final reviewer packet.
- Spec coverage: Sections 23-25, 27-30
- Matrix rows: CM-012, CM-061, CM-062, CM-063, CM-065
- Effort: 0.5-1 focused implementation cycle
- Plan: `.planning/work/10-final-acceptance-reviewer-packet/plan.md`

### 11-core-adapter-boundary-and-codex-adapter-sync
- Status: complete
- Goal: Restore and enforce the Core/Adapter boundary by moving Codex-specific behavior to the standalone adapter, adding contract/version enforcement, and proving cross-repository compatibility.
- Spec coverage: `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` Sections 4-12, R-001 through R-009, SC-001 through SC-015
- Matrix rows: post-v0 extension; not part of `docs/MNEME_V0_COMPLIANCE_MATRIX.md` closure, but must preserve final v0 compliance
- Effort: 3-6 focused implementation cycles after Planning Gate approval, plus adapter checkout/repository coordination
- Plan: `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

### 12-provider-status-and-install-hardening
- Status: complete
- Goal: Fix post-install provider/status defects from the 2026-07-06 diagnostic while preserving the approved Core/Adapter boundary.
- Spec coverage: Sections 10, 12, 14.1, 14.8, 15, 19 plus Phase 11 extension R-003/R-004.
- Matrix rows: post-v0 hardening; must preserve final v0 compliance and published adapter compatibility.
- Effort: 1 focused implementation cycle.
- Plan: `.planning/work/12-provider-status-and-install-hardening/plan.md`

## Transition Criteria

| Transition | Criteria |
|---|---|
| Planning -> Phase 1 execution | User explicitly approves this `.planning/` plan |
| Phase 1 -> Phase 2 | Contract/security foundation tests pass and matrix rows are updated with evidence |
| Phase 2 -> Phase 3 | Migration, startup integrity, writer lane, and idempotency tests pass |
| Phase 3 -> Phase 4 | Blob/BYTES_REF/export/delete/multipart tests pass |
| Phase 4 -> Phase 5 | Session lifecycle, readiness, retention, and auth/audit tests pass |
| Phase 5 -> Phase 6 | State, segment, lineage, graph, and routing tests pass |
| Phase 6 -> Phase 7 | Context prepare, redaction, prompt-injection, and freshness tests pass |
| Phase 7 -> Phase 8 | Metrics, maintenance, provider, and reindex tests pass |
| Phase 8 -> Phase 9 | MCP/REST parity and session-resolution tests pass |
| Phase 9 -> Phase 10 | Package/benchmark docs are review-ready |
| Phase 10 -> v0 acceptance | Final Acceptance Contract below is satisfied with evidence |
| v0 acceptance -> Phase 11 planning | Core/Adapter Boundary Refactor spec approved for planning |
| Phase 11 planning -> Phase 11 execution | User explicitly approves the Phase 11 plan and clears the Extension Planning Gate |
| Phase 11 -> post-refactor acceptance | Core boundary checks, adapter tests, cross-repository CI, runtime smoke, and reviewer packet evidence all pass |
| Phase 12 -> release update | Provider/status focused tests, full Core and adapter verification, docs/install diagnostics, and runtime smoke pass |

## Verification Gates

- Focused tests for the active phase.
- Full local test suite: `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`.
- Compile check: `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`.
- Diff hygiene: `git diff --check`.
- Compliance update: matrix row evidence and Section 24 mapping updated.
- Phase 11 extension checks: boundary policy, distribution boundary,
  contract-version consistency, adapter import boundary, adapter contract drift,
  cross-repository CI evidence JSON, and clean runtime smoke.

## Final Acceptance Contract

The roadmap is not complete until all of these are true:

- Every MUST requirement in `docs/MNEME_STANDALONE_SPEC.md` is implemented, or
  has an explicit user-approved v0 release decision recorded as non-goal,
  future, or intentionally deferred.
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md` is updated so every in-scope row is
  `COMPLIANT`; no `BLOCKER` or `HIGH` in-scope gaps remain open.
- Every Section 24 required contract test number 1-119 is implemented or mapped
  to an equivalent composite test, and the full mapped suite passes.
- `/openapi.json` is parseable and documents every implemented public REST
  endpoint, schema, auth behavior, and error envelope required for v0.
- Full verification passes: pytest, compileall, diff hygiene, and any final
  phase-specific contract checks.
- The reviewer packet includes the canonical spec, final matrix, roadmap/plan
  evidence, verification log, and any explicit accepted deferrals.

## Progress Summary

| Metric | Value |
|---|---|
| Total phases | 12 |
| Complete | 12 |
| In progress | 0 |
| Pending | 0 |
| Cancelled | 0 |
| Last updated | 2026-07-06 |

## Decisions Made

| Decision | Rationale | Date |
|---|---|---|
| Use `01-contract-security-foundation` as the first phase | Audit moved project isolation, safe token handling, and auth-failure audit into foundation work with contract/OpenAPI | 2026-06-22 |
| Treat root planning files as legacy input only | Current user instruction forbids using root planning files as `.planning/` substitutes | 2026-06-22 |
| Add Phase 11 as an extension rather than replacing `.planning/spec.md` | Preserve completed v0 compliance history while planning the approved Core/Adapter boundary refactor | 2026-06-27 |

## Risks And Open Questions

| Risk / Question | Impact | Resolution | Status |
|---|---|---|---|
| Dirty worktree contains prior Phase 1A code/tests | Plan must not overwrite or revert prior/user work | Reconcile by reading diffs during Phase 1 task 01 after approval | open |
| Current matrix counts differ by baseline versus Phase 1A update | Reporting can become confusing | Track both counts in findings and use current file evidence during execution | open |
