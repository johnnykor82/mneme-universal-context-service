# Plan: 53-residual-contract-fix-batch-ax

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-033` and `CM-056` by adding a SQLite backup/restore verification
path using SQLite backup API and blob hash/schema validation.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 13.5-13.6 / CM-033 | Backup/restore procedure must preserve SQLite-owned blob data and verify blob hash integrity. |
| Section 18 / CM-056 | Hot backup should use SQLite backup API; restore must verify schema and blob hash integrity. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to confirm backup/restore residual. | Spark `019efff5-c931-7681-a0c2-0ff7a0797050` confirmed real CM-033/CM-056 gaps. |
| 2 | complete | Add RED tests for hot backup, verified restore, corrupt blob rejection, and CLI parser surface. | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q -k "backup or restore"` failed before implementation with `3 failed, 33 deselected, 1 warning`. |
| 3 | complete | Add storage backup/restore primitives and CLI maintenance commands. | Focused pytest passed after implementation: `3 passed, 33 deselected, 1 warning`. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched pytest `36 passed, 1 warning`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_storage.py`
- `tests/test_config.py`
- `mneme_service/storage.py`
- `mneme_service/cli.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q -k "backup or restore"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-033/CM-056 backup/restore verification sub-residual | ✓ met | `Store.backup_to()`, `Store.restore_from_backup()`, `Store.verify_backup()`, `mneme maintenance backup|restore`; `tests/test_storage.py::test_backup_restore_roundtrip_preserves_sqlite_and_blob_hashes`, `tests/test_storage.py::test_restore_from_backup_rejects_corrupt_blob_hash`, `tests/test_config.py::test_maintenance_backup_restore_cli_parses_paths`; focused gate `3 passed`, touched gate `36 passed`, compile/diff clean. |

**Compliance Status: VERIFIED**
