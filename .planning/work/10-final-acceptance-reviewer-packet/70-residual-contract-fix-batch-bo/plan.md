# Plan: 70-residual-contract-fix-batch-bo

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Implement the narrow shared `CM-017`/`CM-039` residual: first-class
`retrieval.routing` config for default mode and mode weights, with validation,
env/serve CLI parity, example config, and runtime use in context search scoring.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 | `retrieval.routing` config keys and routing-weight validation. |
| Sections 14.5.1, 14.11 | Runtime-neutral routing modes and score breakdowns use configured weights. |
| CM-017, CM-039 | Config model and routing intelligence residuals. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing tests for TOML/env/CLI routing config and runtime score-breakdown propagation | complete | Focused gate after implementation: `3 passed, 42 deselected, 1 warning`. |
| Implement minimal settings fields, parser/env/CLI wiring, validation, example config, and runtime use | complete | `routing_default_mode`/`routing_mode_weights` added; partial TOML weights overlay defaults; context search uses configured weights/default mode. |
| Run focused/touched verification, update matrix/planning evidence, and hygiene checks | complete | Touched gate `6 passed, 58 deselected, 1 warning`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/config.py`
- `mneme_service/cli.py`
- `mneme_service/app.py`
- `mneme.example.toml`
- `tests/test_config.py`
- `tests/test_retrieval.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Verification Commands

- Focused RED/GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_retrieval.py -q -k "routing_config or score_breakdown"`
- Touched config/routing gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_retrieval.py tests/test_context_prepare.py -q -k "routing or score_breakdown or context_prepare_continuation"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 8 / CM-017 | Routing config is modeled, validated, and exposed through config/env/CLI | ✓ met | `tests/test_config.py::test_routing_config_from_toml_supported`, `test_routing_cli_overrides_default_mode_and_weight`, `test_routing_env_override_sets_default_mode_and_dependency_weight`, `test_invalid_routing_config_rejects_bad_modes_and_weights`. |
| Sections 14.5.1, 14.11 / CM-039 | Runtime score breakdowns use configured routing weights/default mode | ✓ met | `tests/test_retrieval.py::test_context_search_uses_configured_default_mode_when_not_supplied`, `test_context_search_accepts_mode_and_reports_score_breakdown`. |

**Compliance Status: VERIFIED**
