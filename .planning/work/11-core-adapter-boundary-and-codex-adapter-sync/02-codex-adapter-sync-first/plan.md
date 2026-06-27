# Plan: 02-codex-adapter-sync-first

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Make the standalone Codex adapter the working source of truth before removing
any Core-side Codex code.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-003 | Adapter owns Codex implementation |
| R-004 | Adapter syncs with current Core contract |
| R-007 | Adapter is verified against fresh Core artifact |
| SC-002, SC-005, SC-011, SC-014 | Adapter ownership, tests, artifact, import boundary |

## Steps

1. [x] Locate the local `mneme-codex-adapter` checkout or request explicit path
   approval before editing outside the Core workspace.
2. [x] Build the current Core artifact from this branch for adapter verification.
3. [x] Trace Core-side `mneme_service.codex_*` behavior needed by the adapter.
4. [x] Port/copy Codex hook, ingest, setup/status/service, docs, and skill behavior
   into adapter-owned modules as needed.
5. [x] Update adapter expectations for `COMPLETED`, current context-prepare shape,
   LaunchAgent status behavior, and contract version range.
6. [x] Add AST import-boundary and OpenAPI/REST-MCP contract-drift checks.
7. [x] Run adapter tests in a clean environment against the freshly built Core
   artifact.

## Expected File Touches

Adapter repository source/tests/docs/CI/package metadata. Core files should be
read-only during this task except for planning/progress evidence.

## Verification

- Adapter import-boundary check:
  `/private/tmp/mneme-adapter-verify-venv-phase11/bin/python scripts/check_no_core_internal_imports.py`
  -> exit 0.
- Adapter contract-drift check against Core OpenAPI fixture:
  `/private/tmp/mneme-adapter-verify-venv-phase11/bin/python scripts/check_core_contract_drift.py --openapi /private/tmp/mneme-openapi-phase11/openapi.json`
  -> `PASS: core contract drift check`.
- Adapter compile and pytest in a clean env with the fresh Core wheel:
  `env TMPDIR=/private/tmp /private/tmp/mneme-adapter-verify-venv-phase11/bin/python -m pytest -q`
  -> `40 passed`;
  `env TMPDIR=/private/tmp /private/tmp/mneme-adapter-verify-venv-phase11/bin/python -m compileall -q mneme_codex_adapter tests scripts`
  -> exit 0.
- Evidence records Core artifact path/hash/version and adapter revision:
  `verification.json`.
- Adapter patch preserved as evidence and published to GitHub:
  `mneme-codex-adapter-sync.patch`;
  adapter commit `bd69b15e5716bb7731256aeba85ae45963be399a`.

## Abort Gate

If adapter tests cannot pass without `mneme_service.*` imports, stop before Core
cleanup and produce a gap report.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-003, R-004, R-007 | complete | Standalone adapter patch in `/private/tmp/mneme-codex-adapter-phase11` owns synced Codex behavior and passes against the fresh Core wheel. See `verification.json`, `mneme-codex-adapter-sync.patch`, and published adapter commit `bd69b15e5716bb7731256aeba85ae45963be399a`. |
| SC-002, SC-005, SC-011, SC-014 | complete | Isolated adapter pytest `40 passed`; import-boundary script exit 0; Core wheel `/private/tmp/mneme-core-dist-phase11/mneme_context_service-0.1.0-py3-none-any.whl` sha256 `20c5ea772459b0d44689bf140bd8cf1ef0888720a0d7a50b0087b61a557fbb94`. |

**Compliance Status: verified and published**
