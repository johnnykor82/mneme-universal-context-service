# Plan: 56-residual-contract-fix-batch-ba

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-033`/`CM-057` by adding the Section 13.6 CLI blob-GC trigger
`mneme maintenance blob-gc` over the existing safe/idempotent blob GC primitive.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.6 / CM-033 | Orphan blob GC must be safe/idempotent and run when explicitly invoked by `/v1/maintenance/blob-gc`, a CLI command such as `mneme maintenance blob-gc`, startup maintenance when configured, or retention cleanup. |
| Section 19 / CM-057 | Operations surface should expose maintenance commands and reviewable evidence. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Confirm existing storage GC primitive and missing CLI surface. | Local audit and Spark `019f003a-aea8-71d2-9336-673c4f81f535` confirmed safe/idempotent REST/storage GC exists and CLI trigger was missing. |
| 2 | complete | Add RED CLI parser/dispatch tests for `maintenance blob-gc`. | Focused config pytest failed before implementation: `1 failed, 1 passed, 24 deselected, 1 warning`. |
| 3 | complete | Add minimal CLI parser and dispatch using `Store.garbage_collect_blobs()`. | Focused config pytest passed after implementation: `2 passed, 24 deselected, 1 warning`. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched gate `4 passed, 41 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_config.py`
- `mneme_service/cli.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "blob_gc or backup_restore"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_blobs.py -q -k "blob_gc or backup_restore or maintenance_blob_gc"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-033/CM-057 CLI blob-GC trigger residual | ✓ met | `mneme maintenance blob-gc --db ... --project-isolation-key ... --execute`; `Store.garbage_collect_blobs()` dispatch; `tests/test_config.py::test_maintenance_blob_gc_cli_parses_and_runs`; focused/touched gates passed; compile/diff clean. |

**Compliance Status: VERIFIED**
