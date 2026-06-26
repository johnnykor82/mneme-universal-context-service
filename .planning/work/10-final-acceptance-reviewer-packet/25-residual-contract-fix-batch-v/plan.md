# Plan: 25-residual-contract-fix-batch-v

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the provider/readiness/reindex grouped Section 24 row by auditing existing
evidence for S24-37, S24-39, S24-68, S24-75, S24-87, and S24-111 and updating
the compliance matrix.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 10, 14.1, 14.8, 23, 24 | Provider modes, readiness provider opt-in/no-provider paths, reindex provider failures/cancel behavior |
| CM-020, CM-061, CM-062 | Provider/cost modes, testing acceptance, required tests |
| S24-37, S24-39, S24-68, S24-75, S24-87, S24-111 | Provider/readiness/reindex required tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Audit spec wording and existing tests for the grouped row.
- [x] Run focused provider/readiness/reindex verification.
- [x] Update matrix evidence and this plan's Spec Compliance table.

## Expected File Touches

`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, and this plan.

## Verification Commands

- Focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py tests/test_config.py tests/test_contract.py tests/test_reindex.py -q -k "minimal_mode or missing_key or require_evidence_false or provider_failure or provider_wait_timeout or reindex_cancel"`
- Full confidence gate inherited from Batch U:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-37, S24-39, S24-68, S24-75, S24-87, S24-111 | Provider/readiness/reindex required tests | compliant | Focused Batch V gate `9 passed`; full suite from Batch U `287 passed`. |

**Compliance Status: COMPLIANT**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
