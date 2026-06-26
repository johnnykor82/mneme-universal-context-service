# Plan: 73-full-suite-red-fix-batch-br

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

in_progress

## Goal

Resolve the two red full-suite contract assertions found during final
verification without broad behavior changes.

## Trigger

`env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` produced
`2 failed, 330 passed, 1 warning`.

Failing tests:

- `tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces`
- `tests/test_parity_recovery.py::test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak`

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 16 | Audit/read trace evidence must accurately describe memory reads |
| Sections 14.6, 14.10-14.12 | Graph, routing, and retrieval traces must be explicit and truthful |
| Sections 23-25 | Final acceptance requires a green full suite and traceability |
| CM-061, CM-062, CM-063 | Test and traceability evidence |

## Steps

| Step | Status | Verification |
|---|---|---|
| Reproduce both failing assertions and inspect related trace payloads | complete | Full suite produced `2 failed, 330 passed, 1 warning`; focused parity test reproduced |
| Identify whether failures are stale tests or runtime contract bugs | complete | Both failures were stale assertions after richer graph/turn-complete and retrieval trace evidence |
| Apply the smallest safe source or test fix | complete | Updated only expected event ids/strategies in two tests |
| Run focused failing tests | complete | `2 passed, 1 warning` |
| Run touched-area tests | complete | `5 passed, 48 deselected, 1 warning` |
| Return to final verification task | complete | Full suite rerun belongs to Task 72 |

## Expected File Touches

- `tests/test_mcp_contract.py`
- `tests/test_parity_recovery.py`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 16 | complete | `fetch_event` trace expectation now follows the actual neighbor evidence exposed by the response |
| Sections 14.6, 14.10-14.12 | complete | Provider pipeline retrieval trace now expects explicit `GRAPH_DEPENDENCY` before reranking |
| CM-061, CM-062, CM-063 | complete | Focused gate `2 passed`; touched-area gate `5 passed, 48 deselected` |

**Compliance Status: COMPLETE**
