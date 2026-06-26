# Plan: 52-residual-contract-fix-batch-aw

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-017` by adding env and serve-CLI parity for the Section 8
`max_writer_queue_depth` writer-lane configuration key.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 / CM-017 | Config file, env, and CLI precedence must cover v0 daemon settings. |
| Section 18 / CM-056 | Writer queue depth is an explicit bounded writer-lane control. |

## Steps

| Step | Status | Action | Verification |
|---|---|---|---|
| 1 | complete | Use Spark/read-only audit to identify a narrow `CM-017` parity gap. | Spark `019efff1-5053-7371-9d83-70a34e2a9e9b` found missing env/CLI wiring for `max_writer_queue_depth`. |
| 2 | complete | Add RED tests for config/env/CLI precedence and serve flag parsing. | RED failed because `--max-writer-queue-depth` was unrecognized. |
| 3 | complete | Add `MNEME_MAX_WRITER_QUEUE_DEPTH` and `--max-writer-queue-depth` wiring. | Focused config pytest passed. |
| 4 | complete | Run touched verification and update matrix/planning evidence. | Full `tests/test_config.py`, compileall, and `git diff --check` passed. |

## Expected File Touches

- `tests/test_config.py`
- `mneme_service/config.py`
- `mneme_service/cli.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`
- `.planning/progress.md`

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "writer_queue_depth or serve_cli_accepts_core_parity_knobs"`
- Touched:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| CM-017 max_writer_queue_depth env/CLI parity sub-residual | ✓ met | Focused config gate -> `2 passed`; full config tests -> `24 passed`; compileall and diff hygiene clean. |

**Compliance Status: VERIFIED**
