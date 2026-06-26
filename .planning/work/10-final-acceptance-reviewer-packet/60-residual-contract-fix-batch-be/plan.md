# Plan: 60-residual-contract-fix-batch-be

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the remaining `CM-056` destructive-migration backup-control residual.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 18 | Startup must create a backup or require explicit `--no-backup-before-migrate` before destructive migrations. |
| CM-056 | Storage, migrations, and concurrency final compliance evidence. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing tests for destructive-migration backup guard and CLI/config knobs | complete | RED before implementation: `3 failed, 38 deselected, 1 warning`; GREEN after implementation: `3 passed, 38 deselected, 1 warning`. |
| Implement minimal storage/config/serve wiring for backup or explicit bypass before destructive migrations | complete | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q` -> `41 passed, 1 warning`. |
| Update matrix/planning evidence | complete | `CM-056` set `COMPLIANT`; counts updated to `COMPLIANT: 52`, `PARTIAL: 12`. |
| Run touched-area and hygiene checks | complete | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` -> exit 0; `git diff --check` -> exit 0; `rg -n "\| CM-056 .*\| PARTIAL \|" docs/MNEME_V0_COMPLIANCE_MATRIX.md` -> no matches. |

## Expected File Touches

- `mneme_service/storage.py`
- `mneme_service/config.py`
- `mneme_service/cli.py`
- `mneme_service/app.py`
- `tests/test_storage.py`
- `tests/test_config.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 18 destructive migration backup guard | ✓ met | `tests/test_storage.py::test_destructive_migration_requires_backup_or_explicit_bypass`, `tests/test_storage.py::test_destructive_migration_allows_explicit_no_backup_bypass`, `tests/test_config.py::test_serve_cli_accepts_destructive_migration_backup_controls`. |
| CM-056 | ✓ met | `docs/MNEME_V0_COMPLIANCE_MATRIX.md` row `CM-056` set `COMPLIANT` with Batch BE evidence. |

**Compliance Status: VERIFIED**
