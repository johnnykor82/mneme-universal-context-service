# Plan: 61-residual-contract-fix-batch-bf

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-017` by adding env and `mneme serve` CLI parity for already-existing
later-phase `Settings` fields. This batch does not design new routing/provider
policy settings.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 | Configuration model and precedence: CLI > env > config file > defaults. |
| CM-017 | Configuration model parity and runtime validation. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused config tests for env/serve CLI parity on existing maintenance/reindex/metrics/audit/daemon fields | complete | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "later_phase_config_parity or serve_cli_accepts_later_phase_config"` -> `2 passed, 27 deselected, 1 warning`. |
| Implement minimal config/CLI parity for already-existing `Settings` fields | complete | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q` -> `29 passed, 1 warning`. |
| Run touched-area checks and update matrix/planning evidence | complete | `compileall` exit 0; `git diff --check` exit 0; matrix row `CM-017` narrowed with Batch BF evidence. |

## Expected File Touches

- `mneme_service/config.py`
- `mneme_service/cli.py`
- `tests/test_config.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 8 existing setting parity | ✓ met | `test_later_phase_config_parity_env_precedence`; `test_serve_cli_accepts_later_phase_config`. |
| CM-017 existing-settings parity slice | ✓ met | Matrix `CM-017` now records existing-field env/CLI parity; broader `CM-017` remains `PARTIAL` for newly modeled routing/provider-policy keys and additional runtime validation. |

**Compliance Status: VERIFIED**
