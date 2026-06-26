# Plan: 54-residual-contract-fix-batch-ay

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow or close `CM-055` by adding an owner-only SQLite database file
permission policy aligned with spec Section 17.4 at-rest protection guidance.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 17.4 / CM-055 | v0 does not require mandatory encryption, but guidance requires SQLite/env/token files to use or recommend `0600` permissions and Mneme data directories to use or recommend `0700`. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to confirm CM-055 owner-only permission residual and scope. | Spark `019f002f-03fc-7fb2-9953-c5d38c780c62` confirmed missing SQLite/data-directory permission policy and recommended this narrow slice. |
| 2 | complete | Add RED storage test for SQLite database file mode being owner-only after `Store` initialization. | Focused storage pytest failed before implementation: `1 failed, 2 passed, 9 deselected`. |
| 3 | complete | Add minimal DB file permission enforcement in storage initialization without changing DB contents or public APIs. | Focused storage pytest passed after implementation: `3 passed, 9 deselected`. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched permission gate `6 passed, 44 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_storage.py`
- `mneme_service/storage.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py -q -k "permission or schema_version"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py tests/test_codex_adapter.py -q -k "permission or runtime_files or schema_version"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-055 owner-only SQLite DB permission sub-residual | ✓ met | `Store._enforce_owner_only_permissions()` enforces POSIX `0700` on the DB parent directory and `0600` on the SQLite DB file; `tests/test_storage.py::test_store_enforces_owner_only_database_file_permissions`; focused gate `3 passed`; touched permission gate `6 passed`; compile/diff clean. |

**Compliance Status: VERIFIED**
