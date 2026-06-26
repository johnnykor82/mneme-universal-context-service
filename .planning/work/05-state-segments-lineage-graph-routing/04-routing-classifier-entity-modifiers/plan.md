# Plan: 04-routing-classifier-entity-modifiers

## Level

task

## Parent

`.planning/work/05-state-segments-lineage-graph-routing/plan.md`

## Status

complete

## Goal

Align runtime-neutral intent classification, entity contradiction/modifier
logic, routing modes, score breakdowns, and memory-read feedback with the
deterministic v0 contract.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.9, 14.5.1, 14.11 | Entity modifiers, intent priority chain, routing modes, scoring |
| CM-030, CM-039, CM-045 | Entity/routing/search gaps |
| S24-93, 97-103, 112 | Priority chain, scoring breakdown, modifiers, feedback, whitespace window |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests for deterministic intent priority chain.
- [x] Add RED tests for entity contradiction using whitespace word windows,
  not model tokens.
- [x] Add RED tests for deterministic entity modifiers and conflict ordering.
- [x] Add RED tests for routing modes changing score breakdown without scope
  leaks.
- [x] Add RED tests for continuation query construction from execution state.
- [x] Add RED tests for memory-read feedback updating state/graph without
  polluting retrieval.
- [x] Implement or refine classifier/routing helpers conservatively.
- [x] Ensure traces/debug metadata are redacted and deterministic.
- [x] Run focused classifier/retrieval/contract tests and compile check.

## Expected File Touches

`mneme_service/classifier.py`, `mneme_service/app.py`,
`mneme_service/state.py`, `mneme_service/storage.py`,
`tests/test_classifier.py`, `tests/test_retrieval.py`,
`tests/test_contract.py`, `tests/test_context_prepare.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_classifier.py tests/test_retrieval.py tests/test_contract.py tests/test_context_prepare.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-93 | Intent classifier priority chain matches contract | complete | `tests/test_classifier.py::test_classifier_priority_chain_prefers_switch_over_other_signals`. |
| S24-97 | Routing modes change score breakdown without scope leak | complete | `tests/test_retrieval.py::test_context_search_accepts_mode_and_reports_score_breakdown`; Phase 5 project/scope regressions remained green. |
| S24-98 | Memory tool feedback updates state/graph safely | complete | `tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion`. |
| S24-99 | Continuation query built from execution state | complete | `tests/test_context_prepare.py::test_context_prepare_continuation_query_uses_execution_state`. |
| S24-101 | Entity modifiers deterministic conflict order | complete | `tests/test_classifier.py::test_extract_entity_modifiers_are_deterministic_and_ordered`. |
| S24-102 | Routing score formula uses default weights/breakdown | complete | `tests/test_retrieval.py::test_context_search_accepts_mode_and_reports_score_breakdown`, `tests/test_retrieval.py::test_context_search_trace_reports_router_mode_and_weights`. |
| S24-103 | Entity modifier schema/behavior matches contract | complete | `tests/test_classifier.py::test_extract_entity_modifiers_are_deterministic_and_ordered`. |
| S24-112 | Entity contradiction uses whitespace window | complete | `tests/test_classifier.py::test_entity_contradiction_uses_five_whitespace_word_window`. |

**Compliance Status: COMPLETE FOR TASK 04**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| RED | Task 04 focused tests before implementation | `extract_entity_modifiers` import missing; routing score breakdown absent; memory-read state/graph feedback absent. | Added deterministic classifier helpers, mode-aware score breakdowns, memory-read evidence edges/state summaries, and continuation query provenance. |
| GREEN | Phase 5 subset after first implementation | Goal history changed after memory-read feedback; graph dependency ranking changed expected tool-chain order. | Switched memory-read summary persistence through `commit_execution_state` to avoid goal-history rows, and weighted graph dependencies by edge type plus deterministic type weights. |

## Evidence

- Targeted RED/GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_classifier.py tests/test_retrieval.py::test_context_search_trace_reports_router_mode_and_weights tests/test_retrieval.py::test_context_search_accepts_mode_and_reports_score_breakdown tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion tests/test_context_prepare.py::test_context_prepare_continuation_query_uses_execution_state -q`
  -> `13 passed, 1 warning`.
- Focused Task 04:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_classifier.py tests/test_retrieval.py tests/test_contract.py tests/test_context_prepare.py -q`
  -> `40 passed, 1 warning`.
- Phase 5 focused subset:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py tests/test_classifier.py tests/test_context_prepare.py -q`
  -> `65 passed, 1 warning`.
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Diff hygiene:
  `git diff --check`
  -> passed.

## Residual Notes

- Task 04 uses deterministic built-in routing defaults and accepts explicit
  request `mode`. A broader config schema for routing defaults/patterns remains
  a later config/ops hardening item, not a blocker for the v0 deterministic
  default contract covered here.
