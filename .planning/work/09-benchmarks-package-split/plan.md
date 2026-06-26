# Plan: 09-benchmarks-package-split

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Finalize benchmark methodology and enforce clean engine/core versus adapter
package boundaries.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 4, 7, 10, 19, 26 | Traceability, package split, providers, operations, non-goals |
| CM-010, CM-011, CM-016, CM-064 | Boundary and release gaps |
| Section 24 quality/benchmark-related acceptance | Review-ready evidence |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-benchmark-methodology-quality-report` | complete | Add benchmark methodology and structured quality-report evidence without unsupported cost-savings claims. |
| `02-core-adapter-release-boundary` | complete | Enforce or prove core package/release exclusion of development-only adapters. |
| `03-docs-honest-integration-nongoals` | complete | Polish install/provider/adapter docs so they declare actual integration depth and v0 non-goals. |
| `04-phase-verification-evidence` | complete | Run focused/full verification and update matrix, Section 24 mapping, progress, findings, and roadmap. |

## Expected File Touches

| Area | Expected files |
|---|---|
| Benchmarks | `mneme_service/benchmarks.py`, `tests/test_benchmarks.py`, benchmark docs/checklists |
| Packaging boundary | `pyproject.toml`, `tests/test_codex_adapter.py`, `docs/PUBLICATION_CHECKLIST.md` |
| Honest docs | `README.md`, `docs/INSTALLATION.md`, `docs/PUBLICATION_CHECKLIST.md`, `adapters/codex/*` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Phase 9 focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_codex_adapter.py tests/test_config.py -q`
- Packaging/docs gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- Benchmark outputs include methodology inputs and labeled quality metrics when
  labels are supplied.
- Token/cost savings claims remain absent unless backed by comparative
  baseline evidence.
- Core package metadata or publication checks prove host-specific adapter code
  is excluded from core release artifacts, or explicitly marked
  development-only.
- Docs do not overclaim automatic Codex prompt insertion or model-callable MCP
  writes.
- Section 26 non-goals remain visible in release-facing docs.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 4, 7, 10, 19, 26 | ✓ met | Benchmark reports include explicit methodology and labeled quality metrics; docs avoid token/cost savings claims without comparative baseline; package discovery excludes host adapters; release docs preserve non-goals and tools-only integration depth. |
| CM-010, CM-011, CM-016, CM-064 | ✓ met | Matrix updated to Phase 9 baseline; CM-010/011/016 moved to `COMPLIANT`; CM-064 remains `OUT_OF_SCOPE/FUTURE` with docs regression coverage. Phase 9 focused `35 passed, 1 warning`; full suite `256 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**
