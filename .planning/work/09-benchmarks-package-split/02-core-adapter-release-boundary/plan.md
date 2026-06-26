# Plan: 02-core-adapter-release-boundary

## Level

task

## Parent

`.planning/work/09-benchmarks-package-split/plan.md`

## Status

complete

## Goal

Prove the core package/release boundary is clean enough for v0 without a risky
repo move: host-specific adapter code may remain in the development checkout
only if core distribution artifacts exclude it and docs say so.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 4 BR-6 | Honest integration depth; do not overclaim adapter depth. |
| Section 4 BR-7 | Core and adapters are separable. |
| Section 7 | Public core release artifacts must not require host-specific adapters. |
| CM-010, CM-011, CM-016 | Adapter/core release-boundary gaps. |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add failing tests/checks that core package discovery excludes
  `adapters/*` from core distribution packages.
- [x] Add or update release/publication checks that mark `adapters/codex` as
  development-only unless packaged separately.
- [x] Avoid moving adapter directories unless tests show release exclusion is
  insufficient.
- [x] Run focused packaging/adapter verification and record exact results.

## Expected File Touches

`pyproject.toml`, `tests/test_codex_adapter.py`,
`docs/PUBLICATION_CHECKLIST.md`, possibly `README.md`.

## Verification Commands

- RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`
- Optional package metadata inspection:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_benchmarks.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 4, 7 / CM-010, CM-011, CM-016 | Core/adapter boundary is release-safe and honest | ✓ met | `tests/test_codex_adapter.py::test_core_package_discovery_excludes_host_adapters` asserts `pyproject.toml` package discovery is exactly `["mneme_service*"]`, excludes `adapters`, and publication docs require separate adapter packaging. `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_benchmarks.py -q` -> `16 passed, 1 warning`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
