# Plan: 55-residual-contract-fix-batch-az

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close or further narrow `CM-055` by adding explicit derivative-retention
evidence and the required Section 17.4 at-rest guidance documentation.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 17.4 / CM-055 | v0 uses SQLite without mandatory encryption, but docs must identify database/blob paths, recommend `0600`/`0700` permissions, mention optional SQLCipher/OS-encrypted volume strategy, and avoid enterprise-confidentiality claims without encryption. |
| Section 14.2 / CM-055 | Retention/privacy cleanup must remove eligible session content and derived searchable records while preserving safe forensic anchors. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/local audit to confirm remaining CM-055 residuals. | Spark `019f002f-03fc-7fb2-9953-c5d38c780c62` identified derivative-retention coverage and at-rest guidance as remaining residuals. |
| 2 | complete | Add RED/GREEN regression coverage that retention cleanup deletes derived rows linked to eligible old events. | Focused contract test passed, confirming existing cleanup removes linked embedding, graph, trace, and state-history rows. |
| 3 | complete | Add concise installation at-rest guidance matching Section 17.4. | Docs test failed before update with missing `0600` guidance, then passed after adding Section 17.4 guidance. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Focused gate `2 passed, 1 warning`; touched gate `3 passed, 58 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0. |

## Expected File Touches

- `tests/test_contract.py`
- `docs/INSTALLATION.md`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`
- `.planning/findings.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_codex_adapter.py -q -k "retention_cleanup_deletes_eligible_events_and_orphan_blobs or at_rest"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-055 derivative-retention/docs residual | ✓ met | `tests/test_contract.py::test_retention_cleanup_deletes_eligible_events_and_orphan_blobs` now asserts derived embedding, graph, trace, and state-history cleanup; `docs/INSTALLATION.md` documents database/blob path, `0600`/`0700`, OS-encrypted volume/SQLCipher strategy, and no enterprise-confidentiality claim; focused/touched gates passed; compile/diff clean. |

**Compliance Status: VERIFIED**
