# Plan: 68-residual-contract-fix-batch-bm

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Close the `CM-003` release-facing product-boundary residual by making the core
README describe the engine/core package without presenting Codex adapter docs
as part of the core release surface, while preserving development-checkout
adapter guidance elsewhere.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 2 | Mneme core is host-runtime-neutral and packaged separately from adapters. |
| CM-003 | Product boundary, request-only context, no hidden prompt mutation, and core/adapter release boundary. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing documentation-boundary test for core README release surface | complete | `test_readme_core_release_does_not_present_codex_adapter_docs_or_commands`. |
| Update README wording minimally so adapter docs are not presented as core release docs | complete | Removed core README adapter-doc link list while preserving separate core/adapter repo/package guidance. |
| Run focused docs tests, update matrix/planning evidence, and run hygiene checks | complete | Focused gate `3 passed, 14 deselected`; touched docs gate `17 passed`; `git diff --check` exit 0. |

## Expected File Touches

- `README.md`
- `tests/test_codex_adapter.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Verification Commands

- Focused RED/GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q -k "core_package_discovery or publication_docs_gate or readme_core_release"`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 2 / CM-003 | Core release docs and package boundary keep host adapters separable | ✓ met | `tests/test_codex_adapter.py::test_core_package_discovery_excludes_host_adapters`; `tests/test_codex_adapter.py::test_readme_core_release_does_not_present_codex_adapter_docs_or_commands`; `tests/test_codex_adapter.py` -> `17 passed`. |

**Compliance Status: VERIFIED**
