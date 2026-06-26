# Plan: 27-residual-contract-fix-batch-x

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the remaining Section 24 storage/concurrency grouped row
`40, 41, 42, 56, 65, 71, 82, 113` with direct evidence for retryable
`503 STORAGE_BUSY`, successful batch visibility, and v0 migration/background
priority applicability.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 18 | SQLite storage, migrations, writer lane, background priority, retryable busy behavior |
| Section 23 | Migration/concurrency acceptance corpus applicability |
| Section 24 tests 40, 41, 42, 56, 65, 71, 82, 113 | Required storage/concurrency contract tests |
| CM-056, CM-061, CM-062 | Storage/concurrency and acceptance traceability rows |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add direct contract evidence that a storage busy condition returns `503 STORAGE_BUSY` with `retryable=true`. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "storage_busy or writer_queue"` -> `2 passed, 38 deselected, 1 warning` |
| 2 | complete | Audit successful-batch visibility and background priority evidence, then update Section 24 matrix row. | `rg -n "\\| [0-9, ]+ \\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md` -> no output |
| 3 | complete | Record Batch X evidence in planning/progress and run touched-area verification. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_reindex.py -q -k "schema or migration or integrity or busy or writer_queue or streaming_bursts or reindex_drain"` -> `10 passed, 52 deselected, 1 warning` |

## Expected File Touches

- `tests/test_contract.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

No production/source-code changes are expected.

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "storage_busy or writer_queue"`
- Touched storage/concurrency:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_reindex.py -q -k "schema or migration or integrity or busy or writer_queue or streaming_bursts or reindex_drain"`
- Section 24 residual audit:
  `rg -n "\\| [0-9, ]+ \\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 18 retryable busy behavior | ✓ met | `tests/test_contract.py::test_storage_busy_returns_retryable_503`; focused gate `2 passed`. |
| Section 24 tests 40, 41, 42, 56, 65, 71, 82, 113 | ✓ met | Section 24 residual audit has no remaining `PARTIAL` grouped rows; touched gate `10 passed`. |
| CM-056, CM-061, CM-062 traceability | ✓ met | Matrix updated with Batch X evidence; CM-056 remains top-level `PARTIAL` only for broader Section 18 backup/restore/destructive-migration controls. |

**Compliance Status: VERIFIED**
