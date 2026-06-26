# Plan: 03-docs-honest-integration-nongoals

## Level

task

## Parent

`.planning/work/09-benchmarks-package-split/plan.md`

## Status

complete

## Goal

Polish release-facing docs so Mneme describes actual TOOLS_ONLY/Codex adapter
depth, keeps MCP writes and compaction ownership as v0 non-goals, and avoids
claims that core automatically mutates Codex prompts.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 4, 5, 7 | Honest integration depth and package boundaries. |
| Section 26 | Known limitations and non-goals remain visible. |
| CM-010, CM-064 | Honest adapter/core claims and non-goal visibility. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing docs tests for required non-goal and integration-depth
  language if missing.
- [x] Update README/install/publication/adapter docs without introducing
  token-in-argv or prompt-insertion overclaims.
- [x] Run focused docs/adapter verification and record exact results.

## Expected File Touches

`README.md`, `docs/INSTALLATION.md`, `docs/PUBLICATION_CHECKLIST.md`,
`adapters/codex/MNEME_CODEX_MCP_USAGE.md`, `tests/test_codex_adapter.py`,
possibly `tests/test_config.py`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_config.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 4, 5, 26 / CM-010, CM-064 | Docs are honest about integration depth and v0 non-goals | ✓ met | `tests/test_codex_adapter.py::test_release_docs_describe_benchmark_smoke_methodology_without_savings_claims` verifies release docs describe local fake benchmark methodology, no external provider calls, no comparative baseline, no token/cost proof, and no automatic prompt replacement. `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_config.py -q` -> `31 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
