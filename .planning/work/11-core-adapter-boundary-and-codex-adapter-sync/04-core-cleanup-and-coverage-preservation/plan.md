# Plan: 04-core-cleanup-and-coverage-preservation

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Remove Codex-specific implementation from Core only after adapter sync and
dependency audit gates pass, while preserving generic Core contract coverage.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-001, R-002 | Core package and repository boundary |
| R-006 | Boundary enforcement foundation |
| SC-001, SC-003, SC-004, SC-010 | Host-neutral Core and preserved coverage |

## Steps

1. [x] Confirm Task 02 adapter sync and Task 03 audit gates are complete.
2. [x] Remove or move Core-side Codex modules, docs, skill files, and tests.
3. [x] Add generic REST/MCP Core tests replacing deleted Codex-specific Core test
   coverage.
4. [x] Record a 1:1 mapping table from each deleted Codex-specific Core test to a
   replacement generic test or explicit no-Core-behavior rationale.
5. [x] Update Core CLI/package discovery to expose only Core commands/modules.
6. [x] Run focused and full Core verification.

## Expected File Touches

`mneme_service/codex_*.py`, `adapters/codex/`, `.agents/skills/mneme-memory/`,
`tests/test_codex_*`, Core docs, package metadata, generic contract tests, and
reviewer evidence docs.

## Verification

- Focused boundary/script tests:
  `env TMPDIR=<tmp> .venv/bin/python -m pytest tests/test_core_adapter_boundary.py tests/test_boundary_scripts.py -q`
  -> `12 passed, 1 warning`.
- Core full suite:
  `env TMPDIR=<tmp> .venv/bin/python -m pytest -q`
  -> `306 passed, 1 warning`.
- Core compileall:
  `env TMPDIR=<tmp> .venv/bin/python -m compileall -q mneme_service tests scripts`
  -> exit 0.
- Clean wheel/sdist build via `setuptools.build_meta` into a temporary external
  artifact directory -> succeeded.
- Boundary scripts:
  `scripts/check_core_boundary.py` -> passed;
  `scripts/check_distribution_boundary.py <artifacts>` -> passed;
  `scripts/check_contract_version.py` -> passed;
  `scripts/check_publication_hygiene.py <artifacts>` -> passed.
- `git diff --check` -> exit 0.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-001, R-002, R-006 | complete | Core-side Codex modules, docs, skill, CLI commands, and tests removed; generic boundary tests and scripts enforce host-neutral Core. |
| SC-001, SC-003, SC-004, SC-010 | complete | `docs/reviews/core_adapter_test_coverage_mapping.md` maps deleted Codex tests to generic Core or adapter coverage; full Core suite and distribution boundary checks pass. |

**Compliance Status: complete**
