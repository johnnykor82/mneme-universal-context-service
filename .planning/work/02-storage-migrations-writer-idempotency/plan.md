# Plan: 02-storage-migrations-writer-idempotency

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Implement the durable storage substrate: migrations, startup integrity, writer
lane, queue limits, and request idempotency ledger.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 18, 22 | Storage, migrations, concurrency, idempotency |
| CM-056, CM-060 | Blocker storage/idempotency gaps |
| S24-1, 4-7, 9, 40-42, 56, 65, 71, 82, 113 | Required tests |

## Active Task

Active Task: none

## Tasks

### 01-baseline-storage-red-tests
- Status: complete
- Goal: Reconcile current storage behavior and add RED tests for Phase 2 gaps.
- Plan: `./01-baseline-storage-red-tests/plan.md`

### 02-migration-schema-integrity
- Status: complete
- Goal: Add schema versioning, schema_migrations, startup consistency checks, and unknown-newer refusal.
- Plan: `./02-migration-schema-integrity/plan.md`

### 03-idempotency-key-ledger
- Status: complete
- Goal: Implement `Idempotency-Key` ledger for current mutating endpoints without overreaching future routes.
- Plan: `./03-idempotency-key-ledger/plan.md`

### 04-writer-lane-storage-busy
- Status: complete
- Goal: Add serialized write boundary, busy timeout evidence, and current-scope `RATE_LIMITED`/`STORAGE_BUSY` behavior.
- Plan: `./04-writer-lane-storage-busy/plan.md`

### 05-phase-verification-evidence
- Status: complete
- Goal: Run Phase 2/full verification and update matrix/Section 24 evidence.
- Plan: `./05-phase-verification-evidence/plan.md`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 18, 22 / CM-056 / CM-060 | ✓ met for Phase 2 scope | `tests/test_storage.py`, idempotency contract tests, writer/busy tests, and matrix updates; full pytest `180 passed`, compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Notes

- Future blob/retention/maintenance endpoint idempotency is planned in later
  feature phases; Phase 2 implements the ledger/helper contract and applies it
  to current mutating endpoints.
