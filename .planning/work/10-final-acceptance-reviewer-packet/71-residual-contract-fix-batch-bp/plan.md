# Plan: 71-residual-contract-fix-batch-bp

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the remaining `CM-030` ambiguity by advertising deterministic delta
extraction/entity-modifier support in capabilities, without adding provider
extraction or changing the already-tested deterministic lifecycle.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 12.9 | `mneme.entity_modifier.v0` schema and source policy. |
| Section 14.5.1 | Delta extraction is optional; if enabled it must be deterministic, redacted, active-entity-only, and provider-assisted extraction is guarded/fallback-only. |
| CM-030 | Entity modifier schema and lifecycle. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused capability assertions for deterministic delta extraction support and provider extraction unsupported/guarded | complete | Focused gate `2 passed, 1 warning`. |
| Add minimal typed capability field and response data | complete | `/v1/capabilities.delta_extraction` advertises deterministic `mneme.entity_modifier.v0` support and provider-guarded disabled policy. |
| Run focused/touched verification, update matrix/planning evidence, and hygiene checks | complete | Touched gate `9 passed, 70 deselected, 1 warning`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/schemas.py`
- `mneme_service/app.py`
- `tests/test_openapi.py`
- `tests/test_contract.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py::test_capabilities_advertise_v0_foundation_without_overclaiming tests/test_contract.py::test_auth_health_capabilities_and_session_idempotency -q`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_state.py tests/test_classifier.py -q -k "capabilities or entity_modifier or entity_contradiction"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 12.9 / 14.5.1 / CM-030 | Entity modifier deterministic lifecycle and advertised extraction policy | ✓ met | `tests/test_openapi.py::test_capabilities_advertise_v0_foundation_without_overclaiming`; `tests/test_contract.py::test_auth_health_capabilities_and_session_idempotency`; `tests/test_state.py` entity-modifier tests; `tests/test_classifier.py` entity-modifier tests. |

**Compliance Status: VERIFIED**
