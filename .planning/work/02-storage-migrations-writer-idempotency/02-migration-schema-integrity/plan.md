# Plan: 02-migration-schema-integrity

## Level

task

## Parent

`.planning/work/02-storage-migrations-writer-idempotency/plan.md`

## Status

complete

## Goal

Implement v0 SQLite schema versioning and startup integrity checks without
destructive migrations.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 18 / CM-056 | `PRAGMA user_version`, `schema_migrations`, ordered/idempotent migrations |
| Section 18 / S24-41, 42, 56, 71 | Upgrade existing DBs, refuse unknown newer schema, mismatch/integrity failures |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Introduce a current schema version constant and `schema_migrations` table.
  - Verification: `tests/test_storage.py::test_store_initializes_schema_version_migration_history_and_busy_timeout`.
- [x] Add startup compatibility checks for missing, mismatched, and newer schema versions.
  - Verification: `tests/test_storage.py::test_store_refuses_unknown_newer_schema_version` and `test_store_refuses_user_version_and_migration_history_mismatch`.
- [x] Keep migrations idempotent for currently supported v0 alpha databases.
  - Verification: `tests/test_storage.py::test_store_reopening_current_database_keeps_migration_history_idempotent`.
- [x] Ensure integrity check behavior is governed by `startup_integrity_check`.
  - Verification: `tests/test_storage.py::test_store_startup_integrity_check_can_be_explicitly_disabled`.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 18 / CM-056 | ✓ met for current migration foundation | `CURRENT_SCHEMA_VERSION`, `schema_migrations`, `PRAGMA user_version`, `PRAGMA integrity_check`, and fail-closed mismatch/newer checks implemented in `mneme_service/storage.py`; `tests/test_storage.py` included in focused suite. |
| S24-41 / 42 / 56 / 71 | ✓ met for v0 initial-schema scope | New/current DB migration history, unknown-newer refusal, mismatch refusal, and startup integrity toggle covered by `tests/test_storage.py`; previous published schema fixture remains future once a published previous version exists. |

**Compliance Status: VERIFIED**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
