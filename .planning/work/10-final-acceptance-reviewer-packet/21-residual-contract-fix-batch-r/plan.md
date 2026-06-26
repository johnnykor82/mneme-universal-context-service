# Plan: 21-residual-contract-fix-batch-r

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close two narrow Section 24 contract-proof residuals with focused tests:
scoped-token `GLOBAL` search isolation without an explicit project header
(S24-25) and batch-first streaming burst ingestion bounded by
`max_batch_events` (S24-58).

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 5, 14.3, 18, 24 | Project/global scope isolation, adapter batch-first ingestion, writer-lane batch guidance, required tests |
| CM-001, CM-002, CM-013, CM-014, CM-056, CM-062 | Project isolation, scoped principals, event ingestion, storage/writer lane, required tests |
| S24-25 | `global_scope_respects_project_isolation` |
| S24-58 | `event_ingest_batch_first_handles_streaming_bursts` |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Review existing scoped retrieval and ingest tests for reusable helpers.
- [x] Add a focused scoped-token `GLOBAL` search isolation contract test.
- [x] Add a focused batch-first burst ingestion contract test.
- [x] Implement the smallest runtime/test adjustment needed.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`tests/test_retrieval.py`, `tests/test_contract.py`, possibly
`mneme_service/app.py` only if existing behavior fails the contract,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_contract.py -q -k "global_scope or streaming_bursts or batch_first"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_contract.py tests/test_codex_ingest.py -q -k "scope or batch or ingest or burst"`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-25 | Global scope respects project isolation for scoped principals | compliant | `tests/test_retrieval.py::test_global_scope_respects_project_isolation_for_scoped_token_without_header`; focused Batch R gate `2 passed`; touched-area gate `15 passed`; full suite `284 passed`. |
| S24-58 | Batch-first event ingest handles streaming bursts | compliant | `tests/test_contract.py::test_event_ingest_batch_first_handles_streaming_bursts`; focused Batch R gate `2 passed`; touched-area gate `15 passed`; full suite `284 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
| 1 | Spark initial S24-58 test | Test appeared to show oversized batch persisted one event after returning `413`. Root cause was the test performing `context_search` before the final export, which adds a memory-read audit event. | Kept the oversized-event disjointness assertion and changed the final export check to assert expected burst ids remain present without relying on total event count after audit creation. |
