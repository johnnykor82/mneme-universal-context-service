# Plan: 46-residual-contract-fix-batch-aq

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-053` by recording internal redaction provenance metadata for event
ingest redactions.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 17.2 / CM-053 | Redaction records internal metadata including kind, field, and hash of original where safe. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify smallest safe slice. | Spark `019effcf-1502-7231-acaa-ce7021cb7796` recommended event-ingest redaction provenance metadata only. |
| 2 | complete | Add focused RED expectations for redaction metadata and no-op omission. | RED: focused pytest failed because redaction metadata was absent. |
| 3 | complete | Add metadata-emitting redaction helper and use it in foreground ingest. | GREEN: focused pytest -> `2 passed, 42 deselected, 1 warning`. |
| 4 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `10 passed, 55 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_contract.py`
- `mneme_service/security.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "redaction_metadata or secret_profile"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py -q -k "redaction or secret or bytes_ref"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-053 redaction metadata sub-residual | verified | `tests/test_contract.py::test_event_ingest_redacts_default_secret_profile_before_persistence_and_search`; `tests/test_contract.py::test_event_ingest_omits_redaction_metadata_when_no_redaction_needed`; touched-area pytest `10 passed`. |

**Compliance Status: VERIFIED for this sub-slice.** `CM-053` remains `PARTIAL`
pending explicit extractor-policy behavior for non-text blobs.

Note: This slice does not attempt to close extractor-policy behavior for
non-text binaries; that remains a follow-up if `CM-053` stays partial.
