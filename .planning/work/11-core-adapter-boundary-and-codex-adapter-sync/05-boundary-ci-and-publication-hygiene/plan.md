# Plan: 05-boundary-ci-and-publication-hygiene

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Add automated checks that prevent Core/adapter boundary drift and publication
hygiene regressions.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-006, R-007, R-009 | Boundary, compatibility verification, contract version |
| SC-008, SC-009, SC-010, SC-012, SC-014 | CI, hygiene, distribution, contract, import boundary |

## Steps

1. [x] Add `scripts/host_boundary_policy.json` with required schema.
2. [x] Add structural Core source/package boundary check.
3. [x] Add wheel/sdist distribution boundary check.
4. [x] Add contract-version consistency check.
5. [x] Add publication hygiene check and allowlist file.
6. [x] Ensure adapter CI has AST import-boundary and contract-drift checks.
7. [x] Wire required checks into automated CI, not a manual release gate.

## Expected File Touches

`scripts/check_core_boundary.py`, `scripts/check_distribution_boundary.py`,
`scripts/check_contract_version.py`, `scripts/check_publication_hygiene.py`,
`scripts/host_boundary_policy.json`,
`scripts/publication_hygiene_allowlist.json`, CI workflow files, tests.

## Verification

- Focused script/boundary tests:
  `env TMPDIR=<tmp> .venv/bin/python -m pytest tests/test_boundary_scripts.py tests/test_core_adapter_boundary.py -q`
  -> `13 passed, 1 warning`.
- Core guard scripts:
  `scripts/check_core_boundary.py` -> passed;
  `scripts/check_distribution_boundary.py <artifacts>` -> passed;
  `scripts/check_contract_version.py` -> passed;
  `scripts/check_publication_hygiene.py <artifacts>` -> passed.
- Core full suite:
  `env TMPDIR=<tmp> .venv/bin/python -m pytest -q`
  -> `307 passed, 1 warning`.
- Core compile:
  `env TMPDIR=<tmp> .venv/bin/python -m compileall -q mneme_service tests scripts`
  -> exit 0.
- Adapter patch evidence now wires both AST import-boundary and Core
  contract-drift CI steps; local adapter checks passed:
  `scripts/check_no_core_internal_imports.py` -> exit 0;
  `scripts/check_core_contract_drift.py --openapi <core-openapi>` ->
  `PASS: core contract drift check`;
  adapter `git diff --check` -> exit 0.
- `git diff --check` in Core -> exit 0.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-006, R-009 | complete | Core boundary, distribution, contract-version, and publication-hygiene scripts are checked in, covered by deterministic fixture tests, and wired into Core CI. |
| R-007 | partial | Adapter patch evidence wires import-boundary and contract-drift checks; full cross-repository verification remains Task 06. |
| SC-008, SC-009, SC-010, SC-012, SC-014 | complete | Core CI builds artifacts and runs boundary/distribution/contract/hygiene checks; adapter patch evidence includes AST import-boundary and Core OpenAPI contract-drift CI steps. |

**Compliance Status: complete for Task 05; combined cross-repository acceptance remains Task 06**
