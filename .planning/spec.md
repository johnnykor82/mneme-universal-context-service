# Specification Manifest: Mneme Universal Context Service v0 Compliance

> Status: approved wrapper manifest
> Canonical spec status: Final v0.7.5 - Approved for v0 implementation
> Canonical approval: Ivan Konstantinov, 2026-06-21
> Planning gate: CLEARED - 2026-06-22
> Version: planning-wrapper-2026-06-22

## Canonical Sources

This file is a planning manifest, not a replacement specification.

| Role | Path | Authority |
|---|---|---|
| Canonical source of truth | `docs/MNEME_STANDALONE_SPEC.md` | Normative v0 requirements |
| Baseline compliance audit | `docs/MNEME_V0_COMPLIANCE_MATRIX.md` | Current implementation evidence and gaps |
| Implementation roadmap input | `docs/MNEME_V0_COMPLIANCE_IMPLEMENTATION_PLAN.md` | Approved phase/order input |
| Legacy project history | `task_plan.md`, `findings.md`, `progress.md` | Context only, not a `.planning/` substitute |

`docs/MNEME_STANDALONE_SPEC.md` is immutable for this workflow unless the user
explicitly authorizes a spec change. This wrapper may be edited only to keep
planning pointers and traceability current.

## Approved Extension Scope: Core/Adapter Boundary Refactor

| Role | Path | Authority |
|---|---|---|
| Extension source of truth | `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` | Approved Core/Adapter boundary refactor requirements |
| External review evidence | `.planning/findings.md` | Summary of v0.5 approval cycle: Kimi, DeepSeek, and Owl approved; GLM v0.5 unavailable due provider 429 after approving v0.4 |
| Planning scope | `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md` | Phase 11 plan, pending Planning Gate approval |

`docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` is approved for
spec-driven planning as of 2026-06-27. It is now immutable for Phase 11
implementation unless the user explicitly authorizes a scope/spec change.

### Extension Spec Format Assessment

The extension spec is reviewer-facing rather than the native
`spec-driven-planning` template.

| Template area | Extension location | Assessment |
|---|---|---|
| Objective and problem | Sections 1-3 | Present |
| Architecture decision | Section 4 | Present; Variant C is normative |
| Goals and non-goals | Sections 5-6, 15 | Present |
| Requirements | Section 7, R-001 through R-009 | Present with stable IDs |
| Repository/package layout | Sections 8-9 | Present |
| Migration plan | Section 10 | Present as six phases |
| Verification | Sections 11-12 | Present with success criteria SC-001 through SC-015 |
| Risks and approval gate | Sections 13-17 | Present |

Risk: the extension includes cross-repository adapter work that may require a
separate local checkout and explicit filesystem/network approval before
execution. Mitigation: Phase 11 Task 02 starts by locating and approving the
adapter checkout path before any adapter edits.

### Extension Mapping Approach

Phase 11 plan items must map:

`Extension R/SC ID -> spec section -> implementation evidence -> test/check evidence -> reviewer packet evidence`.

The extension's hard boundaries are:

- Core remains host-neutral.
- Codex behavior moves to `mneme-codex-adapter`.
- Adapter must not import `mneme_service.*`.
- Contract/version compatibility must be machine-readable and CI-enforced.
- Implementation cannot begin until the Phase 11 Planning Gate is explicitly
  cleared.

## Spec Format Assessment

The canonical spec is approved but does not use the `spec-driven-planning`
template directly.

| Template area | Canonical location | Assessment |
|---|---|---|
| Objective and executive summary | Sections 0-1 | Present, renamed |
| Boundary and non-goals | Sections 2, 5, 26 | Present |
| Personas and use cases | Section 3 | Present |
| Requirements | Sections 4-22, 27-28 | Present as prose and normative tables, not FR/NFR rows |
| Architecture | Sections 6-7, 18-19 | Present |
| Commands | Section 19 | Present for v0 developer/core |
| Testing and acceptance | Sections 23-24, 29-30 | Present and detailed |
| Traceability | Section 25 plus compliance matrix | Present |
| Change log | Section 0 review summaries | Present, non-template |

Extra canonical sections such as the compliance gap register and reviewer
finding coverage matrix affect scope, verification, and review readiness.

Risk: plan files cannot rely on generated FR-NNN ids from the template without
changing meaning. Mitigation: every plan uses stable references in this order:
spec section, compliance matrix row, Section 24 test number, implementation
evidence, test evidence.

Proceeding basis: the user has approved Final v0.7.5 as the target spec and
approved this `.planning/` roadmap for execution on 2026-06-22.

## Planning Requirement Alias Index

These aliases exist only for planning convenience. The canonical text remains
the spec section named in each alias.

| Alias | Canonical coverage |
|---|---|
| REQ-FINAL-SPEC | Sections 0, 30 |
| REQ-CONFIG | Section 8 |
| REQ-AUTH-SCOPE | Sections 9, 17.1 |
| REQ-CAPABILITIES-READINESS | Section 14.1 |
| REQ-SCHEMAS | Section 12 |
| REQ-OPENAPI | Section 20 |
| REQ-ERRORS | Sections 15, 21 |
| REQ-IDEMPOTENCY | Section 22 |
| REQ-AUDIT | Sections 12.7, 16 |
| REQ-BLOB | Section 13 |
| REQ-STORAGE | Section 18 |
| REQ-SESSIONS-RETENTION | Sections 12.1, 14.2 |
| REQ-STATE-SEGMENTS-GRAPH-ROUTING | Sections 12.5-12.9, 14.5-14.12 |
| REQ-CONTEXT-SECURITY | Sections 14.13-14.14, 17.2-17.3 |
| REQ-OPERATIONS | Sections 14.8, 19 |
| REQ-MCP | Section 15 |
| REQ-ACCEPTANCE | Sections 23-25, 27-29 |

## Mapping Approach

Each executable plan item must map:

`Spec section -> compliance matrix row -> Section 24 test number -> task plan -> verification evidence`.

Evidence is acceptable only when it names code/docs changed, commands run, and
observed results. Passing alpha tests alone is not v0 compliance.

## Change Log

| Date | Change | Reason | Approved By |
|---|---|---|---|
| 2026-06-22 | Created approved wrapper manifest around Final v0.7.5 | Restore `spec-driven-planning` workflow without rewriting the approved spec | Ivan Konstantinov |
| 2026-06-22 | Cleared planning gate metadata after user approval | Start implementation under `.planning/` workflow | Ivan Konstantinov |
| 2026-06-27 | Added approved extension scope for Core/Adapter Boundary Refactor v0.5 | Prepare Phase 11 planning after external review approvals | Ivan Konstantinov |
