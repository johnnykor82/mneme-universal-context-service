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
