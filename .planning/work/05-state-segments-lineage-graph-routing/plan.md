# Plan: 05-state-segments-lineage-graph-routing

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Align state history, segments, lineage, graph traversal, classifier, and
routing intelligence with Final v0.7.5.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.5, 12.8, 12.9, 14.5-14.12 | State, segments, lineage, graph, routing |
| CM-026, CM-029, CM-030, CM-039, CM-040, CM-044-046 | Structural memory gaps |
| S24-10-13, 23-24, 61, 78-80, 88, 93-94, 97-103, 105-110, 112, 116 | Required tests |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-execution-state-update-history` | complete | Add explicit REST execution-state update, provenance, PATCH/REPLACE semantics, state hashes, and append-only history. |
| `02-graph-traversal-limits-anchors` | complete | Add deterministic graph traversal limits, warnings, bounded importance boost, and anchor/evidence edge behavior. |
| `03-segment-rest-contract` | complete | Add direct segment start/close/list/get/events endpoints, final segment/event-summary schemas, generated-id rules, and lifecycle enums. |
| `04-routing-classifier-entity-modifiers` | complete | Align runtime-neutral intent priority chain, deterministic entity contradiction/modifiers, routing modes, score breakdown, and memory-read feedback. |
| `05-session-discovery-lineage-search` | complete | Stabilize session discovery, lineage-aware search/session resolution semantics, and caller-visible scope behavior. |
| `06-phase-verification-evidence` | complete | Run focused/full verification and update compliance matrix, Section 24 mapping, findings, progress, and roadmap evidence. |

## Expected File Touches

| Area | Expected files |
|---|---|
| REST contract | `mneme_service/app.py`, `mneme_service/schemas.py` |
| State/classifier/routing | `mneme_service/state.py`, `mneme_service/classifier.py`, possibly new routing helpers |
| Storage/graph/segments | `mneme_service/storage.py`, `mneme_service/segments.py` |
| Tests | `tests/test_state.py`, `tests/test_segments.py`, `tests/test_graph.py`, `tests/test_contract.py`, `tests/test_retrieval.py`, `tests/test_openapi.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Focused Phase 5:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
- MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- Execution-state updates must reject unknown fields and require provenance.
- State hashes must be deterministic over canonical redacted state objects.
- Segment endpoints must enforce project/session visibility and generated-id
  idempotency rules.
- Graph traversal must stop at configured limits and report warnings instead
  of silently overexpanding.
- Routing/classifier behavior must be deterministic without providers.
- Any score/routing/debug metadata must avoid project-scope leaks.
- Every Phase 5 Section 24 mapping must either pass directly or be recorded as
  an explicit residual gap.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 12.5, 12.8, 12.9, 14.5-14.12 | partial | Task 01 added explicit execution-state update, provenance validation, state hashes, and append-only history. Task 02 added deterministic bounded graph traversal metadata and warnings. Task 03 added direct segment REST endpoints and generated-id idempotency behavior. Task 04 added deterministic intent/modifier helpers, routing mode score breakdowns, continuation query construction, and memory-read state/graph feedback. Task 05 added stable session-resolution best-guess semantics and explicit SESSION/LINEAGE/PROJECT search scope behavior. |
| CM-026, CM-029, CM-030, CM-039, CM-040, CM-044-046 | complete | Matrix rows updated with Phase 5 evidence after focused verification `70 passed, 1 warning`, MCP regression `16 passed`, full suite `210 passed, 1 warning`, compileall, and diff hygiene. Rows remain `PARTIAL` where their spec sections intentionally carry later-phase residual gaps. |
| S24-10-13, 23-24, 61, 78-80, 88, 93-94, 97-103, 105-110, 112, 116 | partial | S24-10, S24-11, S24-12, S24-13, S24-23, S24-24, S24-61, S24-78, S24-79, S24-88, S24-93, S24-94, S24-97, S24-98, S24-99, S24-101, S24-102, S24-103, S24-110, S24-112, and S24-116 covered. S24-80, S24-100, S24-105, S24-106, S24-107, and S24-109 remain partial/residual. |

**Compliance Status: COMPLETE FOR PHASE 5 GATES WITH RESIDUAL GAPS RECORDED**

## Planning Evidence

- Spark worker `019ef560-2f59-7f42-b342-4d7de2ab7a74` performed a read-only
  Phase 5 decomposition review and recommended the state -> graph -> segment
  -> routing/entity -> discovery order.
- Parent review adopted that order and added `06-phase-verification-evidence`
  to keep matrix/Section 24 updates explicit before Phase 5 closes.
