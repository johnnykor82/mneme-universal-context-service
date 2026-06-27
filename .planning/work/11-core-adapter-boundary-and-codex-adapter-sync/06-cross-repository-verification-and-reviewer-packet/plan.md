# Plan: 06-cross-repository-verification-and-reviewer-packet

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Prove the final Core/adapter pair with automated cross-repository verification,
clean runtime smoke, and reviewer-ready evidence.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-007, R-009 | Compatibility and contract-version verification |
| SC-005, SC-006, SC-011, SC-012, SC-015 | Adapter tests, runtime smoke, artifact evidence, rollback gates |

## Steps

1. [x] Build Core wheel/sdist and record artifact SHA-256.
2. [x] Run automated cross-repository CI against the adapter checkout/revision.
3. [x] Generate verification JSON with normalized runtime refs, contract version,
   adapter supported range, commits, commands, installed packages, and result.
4. [x] Run clean temporary DB/state runtime smoke for health, capabilities, ingest,
   replay, search/fetch, and no token leakage.
5. [x] Run final Core full suite, OpenAPI, compileall, boundary, distribution,
   contract-version, hygiene, and diff checks.
6. [x] Assemble reviewer packet with spec, audit, coverage mapping, CI evidence,
   runtime smoke, and any abort/rollback gate dispositions.
7. [x] Update progress and leave next action for user approval/commit decision.
8. [x] Post-completion pre-commit hardening: sync the adapter-packaged
   `mneme-memory` skill with the live Session Resolution Contract, update patch
   evidence, and replace live Codex hooks with adapter capture-only hooks.

## Expected File Touches

Reviewer packet docs, verification artifacts or links, `.planning/progress.md`,
`.planning/findings.md`, and possibly CI artifact metadata.

## Verification

- Cross-repository verification:
  `cross_repository_verification.json` -> `result: pass`.
- Runtime smoke:
  `runtime_smoke.json` -> `result: pass`.
- Adapter verification:
  pytest `40 passed`; compileall passed; AST import-boundary passed;
  contract-drift against fresh Core OpenAPI passed; adapter `git diff --check`
  passed.
- Core final verification:
  full suite `307 passed, 1 warning`; OpenAPI suite `11 passed, 1 warning`;
  compileall passed; boundary/distribution/contract-version/hygiene checks
  passed; Core `git diff --check` passed.
- Reviewer packet:
  `docs/MNEME_CORE_ADAPTER_BOUNDARY_REVIEWER_PACKET.md` includes SC-001..SC-015
  evidence and rollback disposition.
- Post-completion hardening:
  `tests/test_setup.py::test_skill_install_writes_mneme_memory_skill` was run
  RED/GREEN for the packaged Session Resolution Contract; full adapter suite
  passed `40 passed`; adapter compileall, import boundary, contract-drift, and
  diff hygiene passed; live `/Users/openclaw/.codex/hooks.json` was backed up
  and replaced with adapter capture-only hooks.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-007, R-009 | complete | `cross_repository_verification.json` records artifact hashes, installed package identity, adapter range `>=0.7,<0.8`, commands, pip freeze, and pass result. |
| SC-005, SC-006, SC-011, SC-012, SC-015 | complete | Adapter suite passed against fresh Core wheel; runtime smoke passed with clean temp DB/state; reviewer packet records no rollback triggered. Post-completion hardening reran adapter suite and live capture-hook smoke after syncing the packaged skill; adapter commit `bd69b15e5716bb7731256aeba85ae45963be399a` was pushed to GitHub `main`. |

**Compliance Status: complete**
