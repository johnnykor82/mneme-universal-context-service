# Plan: 01-boundary-spec-amendment-and-contract-version

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Turn the approved boundary spec into Core-facing documentation and a
machine-readable contract-version surface without changing runtime adapter
behavior yet.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-005 | Public integration documentation |
| R-009 | Contract version compatibility |
| SC-007, SC-012 | Docs and contract compatibility evidence |

## Steps

- [x] Update Core docs to state Variant C: Core is host-neutral; adapters own
   host-specific behavior.
- [x] Add `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md` with REST/MCP integration
   guidance and no host-specific tutorial flow.
- [x] Add `docs/MNEME_CONTRACT_VERSION` as one SemVer line.
- [x] Wire the same contract version into OpenAPI `info.version`.
- [x] Wire `mneme_contract_version` into `/v1/health` and `/v1/capabilities`.
- [x] Add focused tests for version consistency and documentation boundary.
- [x] Record results in progress and this plan before advancing.

## Expected File Touches

`docs/MNEME_STANDALONE_SPEC.md`, `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md`,
`docs/MNEME_CONTRACT_VERSION`, `README.md`, `mneme_service/app.py`,
`mneme_service/schemas.py`, `tests/test_openapi.py`, and focused docs tests.

## Verification

- Focused contract-version tests.
- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-005 | complete | `README.md` and `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md` state Core/adapter boundary and REST/MCP adapter contract. Docs boundary gate: `tests/test_codex_adapter.py::test_readme_core_release_does_not_present_codex_adapter_docs_or_commands` -> `1 passed`. |
| R-009 | complete | `docs/MNEME_CONTRACT_VERSION` is `0.7.5`; `mneme_service/version.py` propagates it to OpenAPI, `/v1/health`, and `/v1/capabilities`. RED then GREEN focused test: `tests/test_openapi.py::test_contract_version_is_canonical_across_docs_openapi_and_runtime` -> `1 passed`. |
| SC-007, SC-012 | complete | `tests/test_openapi.py -q` -> `11 passed, 1 warning`; endpoint contract checks -> `2 passed, 1 warning`; compileall and diff hygiene exit 0. |

**Compliance Status: VERIFIED**
