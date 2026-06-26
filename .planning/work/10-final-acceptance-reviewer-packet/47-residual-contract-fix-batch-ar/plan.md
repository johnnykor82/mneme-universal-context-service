# Plan: 47-residual-contract-fix-batch-ar

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close `CM-053` by making the non-text blob extractor policy explicit in
configuration, capabilities, and event-ingest metadata.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 17.2 / CM-053 | Non-text blob bytes are not text-extracted or sent to providers unless an explicit extractor policy is configured; such blobs are marked metadata-only. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Add focused RED tests for extractor policy config and binary BYTES_REF metadata. | RED: focused pytest failed because policy metadata/config validation was absent. |
| 2 | complete | Add explicit extractor policy setting, validation, env/TOML loading, capabilities exposure, and ingest metadata. | GREEN: focused pytest -> `2 passed, 64 deselected, 1 warning`. |
| 3 | complete | Run touched-area verification and update matrix/planning evidence. | Touched-area pytest -> `9 passed, 76 deselected, 1 warning`; compileall and `git diff --check` passed. |

## Expected File Touches

- `tests/test_contract.py`
- `tests/test_config.py`
- `mneme_service/config.py`
- `mneme_service/app.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py -q -k "extractor_policy or binary_metadata_only"`
- Touched area:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py tests/test_blobs.py -q -k "redaction or bytes_ref or extractor_policy or binary"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-053 extractor policy residual | verified | `tests/test_contract.py::test_non_text_bytes_ref_is_stored_as_binary_metadata_only`; `tests/test_config.py::test_invalid_v0_foundation_config_fails_startup`; touched-area pytest `9 passed`. |

**Compliance Status: VERIFIED.** `CM-053` is now `COMPLIANT`.
