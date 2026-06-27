# Plan: 03-dependency-extraction-audit

## Level

task

## Parent

`.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md`

## Status

complete

## Goal

Audit Core-side Codex modules before deletion so generic Core behavior is
preserved and adapter-only behavior moves out of Core.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| R-008 | Dependency extraction audit |
| SC-013, SC-015 | Audit complete and abort gates respected |

## Steps

1. [x] Inspect `mneme_service/codex_hooks.py`, `codex_ingest.py`, and
   `codex_setup.py`.
2. [x] Create `docs/reviews/core_adapter_dependency_audit.md`.
3. [x] Record one Markdown row per relevant unit/function with decision:
   `move to adapter`, `promote to Core`, `delete as Codex-specific`, or
   `defer`.
4. [x] Prefer adapter-first decisions; promote only logic already used by Core or
   required to preserve public Core REST/MCP contracts.
5. [x] For each `promote to Core` row, identify target file/API and generic Core
   tests required before deletion.
6. [x] Stop if the audit discovers scope that requires a new SDK/schema package or
   new feature outside the approved refactor.

## Expected File Touches

`docs/reviews/core_adapter_dependency_audit.md`, `.planning/findings.md`,
`.planning/progress.md`, and possibly task plans if the audit finds in-scope
unplanned work.

## Verification

- Audit file exists and has required columns:
  `docs/reviews/core_adapter_dependency_audit.md`.
- Every Core-side Codex module has a disposition:
  `mneme_service/codex_ingest.py`, `mneme_service/codex_hooks.py`,
  `mneme_service/codex_setup.py`, Core CLI Codex command wiring,
  `adapters/codex/`, `.agents/skills/mneme-memory/SKILL.md`, and
  `tests/test_codex_*.py` are covered.
- Every `promote to Core` row names target API/file and required tests:
  audit found no required `promote to Core` rows; public REST/MCP contracts
  already cover the generic behavior.
- `git diff --check` -> exit 0.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| R-008 | complete | `docs/reviews/core_adapter_dependency_audit.md` contains the required disposition table and coverage-preservation section. |
| SC-013, SC-015 | complete | Audit found no hidden generic behavior requiring a new SDK/schema package; abort gate is clear for Task 04 Core cleanup after generic coverage mapping. |

**Compliance Status: verified**
