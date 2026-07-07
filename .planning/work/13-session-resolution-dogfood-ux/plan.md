# Plan: 13-session-resolution-dogfood-ux

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Fix the dogfood session-resolution failure observed on 2026-07-07 where an
agent could not find the active Mneme session for a Codex thread even though
the session existed in local Mneme.

## Planning Gate

- [x] User approved diagnosis before implementation.
- [x] External thread diagnostic confirmed the failing behavior.
- [x] Scope is limited to session-resolution UX and does not change Core/Adapter
  boundary decisions.

**Gate Status: CLEARED - 2026-07-07**

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-core-resolver-and-skill-guidance` | complete | Add RED/GREEN coverage and fix exact thread/session anchor resolution, discovery ranking before pagination, and adapter skill fallback guidance. |
| `02-verification-and-release-prep` | complete | Run focused/full verification and prepare commit/push/install steps if approved. |

## Diagnostic Evidence

- Other Codex thread `019ed9cf-12b6-7281-9085-5652bace533e` called only
  `resolve_session` with `project_path=/Users/openclaw/.hermes/plugins`,
  semantic PR query, and no `thread_id`.
- That agent did not have `list_sessions` exposed as a callable MCP tool.
- Local REST `list_sessions` shows the session exists as
  `019ed9cf-12b6-7281-9085-5652bace533e`.
- `resolve_session(thread_id=019ed9cf..., query=...)` returned `NOT_FOUND`;
  `resolve_session(thread_id=019ed9cf...)` resolved correctly.
- `resolve_session(project_path=/Users/openclaw/.hermes/plugins, limit=3)`
  paged newer subproject smoke sessions before the older exact project session.

## Scope Boundaries

- Do not read or modify SQLite directly.
- Do not change approved v0 spec semantics.
- Do not make Core Codex-specific beyond host-neutral `thread_id`,
  `project_path`, and metadata discovery behavior.
- Do not commit/push without separate user approval.

## Expected Files

- Core:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_contract.py`
- Adapter:
  - `mneme_codex_adapter/skills/mneme-memory/SKILL.md`
  - `.agents/skills/mneme-memory/SKILL.md`
  - `tests/test_setup.py`

## Verification Gates

- Core RED/GREEN focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "resolve_session"`
- Core full:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Core compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Core diff hygiene:
  `git diff --check`
- Adapter focused skill-install test:
  `env TMPDIR=/private/tmp /Users/openclaw/.hermes/plugins/_mneme-universal-context-service/.venv/bin/python -m pytest tests/test_setup.py -q -k "skill_install_writes_mneme_memory_skill"`
- Adapter full suite and diff hygiene.
- Live REST/MCP smoke for `thread_id` resolution if local daemon is available.

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Spec Section 15 | MCP session-resolution UX must help agents resolve valid sessions without unsafe guessing. | complete | Core focused resolver tests passed; full Core suite `310 passed, 1 warning`; live REST smoke resolved exact `thread_id` as `EXACT_THREAD_ID`. |
| Phase 11 Skill Contract | Codex adapter skill must instruct agents how to establish a valid session id before memory reads. | complete | Adapter skill-install test passed; full adapter suite `42 passed`; shared Codex skill updated locally. |

## Errors

| Time | Step | Error | Resolution |
|---|---|---|---|
