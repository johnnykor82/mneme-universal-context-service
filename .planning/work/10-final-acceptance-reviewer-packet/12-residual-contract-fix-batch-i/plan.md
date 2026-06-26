# Plan: 12-residual-contract-fix-batch-i

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the narrow Section 24 indexing-compression residuals by adding explicit
contract evidence for raw tool-output preservation, embedding model-id
isolation, and deterministic excerpt fallback when no summary provider is used.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 12.3, 14.3, 14.11 | Selective indexing compression, fetchable raw content, vector retrieval |
| CM-036, CM-045, CM-062 | Event ingest/retrieval Section 24 indexing residuals |
| S24-95 | `selective_indexing_compression_preserves_fetchable_raw_tool_output` |
| S24-96 | `vector_retrieval_filters_by_embedding_model_id` |
| S24-104 | `deterministic_index_excerpt_is_stable_when_summary_provider_unavailable` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to confirm exact residuals and minimal
  implementation scope.
- [x] Add explicit focused tests for embedding model-id isolation and
  deterministic excerpt fallback.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_embeddings.py`, `docs/MNEME_V0_COMPLIANCE_MATRIX.md`,
`.planning/findings.md`, `.planning/progress.md`, and this plan. Source changes
are not expected unless tests reveal a real behavior gap.

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py -q -k "active_model_id or deterministic_excerpt or compresses_tool_output"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_retrieval.py tests/test_contract.py -q -k "embedding or context_search or fetch_event or non_text_bytes_ref"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-95 | Selective indexing compression preserves fetchable raw tool output | ✓ met | `tests/test_embeddings.py::test_event_ingest_indexes_redacted_content_and_compresses_tool_output_without_changing_raw_event`; touched-area gate -> `51 passed, 1 warning`; full suite -> `272 passed, 1 warning`. |
| S24-96 | Vector retrieval filters by embedding model id | ✓ met | `tests/test_embeddings.py::test_embedding_search_isolated_to_active_model_id`; focused gate -> `2 passed, 11 deselected, 1 warning`; touched-area gate -> `51 passed, 1 warning`; full suite -> `272 passed, 1 warning`. |
| S24-104 | Deterministic index excerpt is stable when summary provider unavailable | ✓ met | `tests/test_embeddings.py::test_deterministic_index_excerpt_is_stable_without_summary_provider`; focused gate -> `2 passed, 11 deselected, 1 warning`; touched-area gate -> `51 passed, 1 warning`; full suite -> `272 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
