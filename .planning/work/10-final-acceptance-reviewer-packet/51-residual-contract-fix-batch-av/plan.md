# Plan: 51-residual-contract-fix-batch-av

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close `CM-009` by replacing static provider `last_health="UNKNOWN"` capability
summaries with deterministic runtime provider health status that does not make
live network calls.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 4 BR-5 / CM-009 | Optional quality-layer provider availability must be explicit and honest. |
| Section 10 / CM-020 | Capabilities expose active provider status, including last health. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Inspect current provider summary and capabilities behavior. | `ProviderSettings.summary()` always emitted `last_health="UNKNOWN"`. |
| 2 | complete | Add RED tests for non-static capability `last_health` values. | RED failed with missing `ProviderHealth` import and string `last_health`. |
| 3 | complete | Add deterministic runtime health status values without live provider probes. | Focused provider-summary and capabilities tests passed after adding process-local provider health wrappers. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Touched provider/cost/capabilities gate, OpenAPI, compileall, and `git diff --check` passed. |

## Expected File Touches

- `mneme_service/config.py`
- `tests/test_config.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "provider_summary or capabilities_reflect_provider"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_context_prepare.py -q -k "provider or cost_mode or capabilities"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-009 provider last-health sub-residual | ✓ met | Provider summary focused tests -> `2 passed`; capabilities runtime failure test -> `1 passed`; touched gate -> `9 passed`; OpenAPI -> `10 passed`; compileall and diff hygiene clean. |

**Compliance Status: VERIFIED**
