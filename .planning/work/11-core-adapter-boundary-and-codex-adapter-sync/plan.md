# Plan: 11-core-adapter-boundary-and-codex-adapter-sync

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Implement the approved Core/Adapter Boundary Refactor so Mneme Core remains
host-neutral, Codex behavior lives in `mneme-codex-adapter`, and Core/adapter
compatibility is enforced through public REST/MCP contracts and automated
cross-repository verification.

## Planning Gate

- [x] Approved extension spec recorded in `.planning/spec.md`
- [x] Phase 11 roadmap entry exists
- [x] Phase 11 plan exists
- [x] Detailed task plans exist for all Phase 11 tasks
- [x] User has reviewed and approved this Phase 11 plan

**Gate Status: CLEARED - 2026-06-27**

Implementation may proceed under the active path.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-001, R-002 | Core package/repository boundary |
| R-003, R-004 | Codex adapter owns and syncs Codex behavior |
| R-005 | Public integration documentation |
| R-006 | Boundary enforcement tests and policies |
| R-007 | Combined compatibility verification |
| R-008 | Dependency extraction audit |
| R-009 | Contract version compatibility |
| SC-001..SC-015 | Final success criteria |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-boundary-spec-amendment-and-contract-version` | complete | Amend Core docs/spec pointers and add machine-readable contract-version surface. |
| `02-codex-adapter-sync-first` | complete | Make the standalone Codex adapter own and pass current Codex behavior before Core cleanup. |
| `03-dependency-extraction-audit` | complete | Audit Core-side Codex modules and decide move/promote/delete/defer per unit. |
| `04-core-cleanup-and-coverage-preservation` | complete | Remove Codex-specific Core artifacts only after adapter/audit gates pass, preserving generic Core coverage. |
| `05-boundary-ci-and-publication-hygiene` | complete | Add structural boundary, distribution, import, contract-drift, and hygiene checks. |
| `06-cross-repository-verification-and-reviewer-packet` | complete | Prove the final Core/adapter pair with automated cross-repo CI, runtime smoke, and reviewer evidence. |

## Verification Gates

- Phase 11 Planning Gate is cleared before edits.
- Adapter sync and dependency audit pass before Core cleanup.
- Core cleanup preserves generic REST/MCP coverage for deleted Codex tests.
- Boundary checks run in CI.
- Cross-repository CI and clean runtime smoke prove the final pair.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-001, R-005, R-009 | partial | Task 01 complete: contract version and host adapter contract docs are in place. |
| R-003, R-004, R-007 | complete | Task 02 complete: adapter patch passes isolated verification against fresh Core wheel and was published as adapter commit `bd69b15e5716bb7731256aeba85ae45963be399a`. |
| R-008 | complete | Task 03 audit recorded in `docs/reviews/core_adapter_dependency_audit.md`; no new shared SDK/schema package required. |
| R-001, R-002, R-006 | complete | Task 04/05 complete: Core cleanup is enforced by source, distribution, contract-version, publication-hygiene, and CI checks. |
| SC-001, SC-003, SC-004, SC-010 | complete | Core no longer ships Codex implementation/docs/skill/tests; generic replacement coverage is mapped in `docs/reviews/core_adapter_test_coverage_mapping.md`. |
| SC-008, SC-009, SC-012, SC-014 | complete | Task 05 complete: Core CI and adapter patch evidence include the required boundary, contract, and hygiene checks. |
| R-007, SC-002, SC-005, SC-007, SC-011, SC-013, SC-015 | complete | Task 06 complete: cross-repository verification, runtime smoke, reviewer packet, rollback disposition, and adapter publication are recorded. |

**Compliance Status: complete**
