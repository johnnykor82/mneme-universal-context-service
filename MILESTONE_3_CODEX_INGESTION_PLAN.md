# Milestone 3 Codex Transcript Ingestion Plan

**Goal:** Add the first safe `EVENT_INGEST` path for Codex-like sessions so Mneme can be populated through REST and later queried through MCP memory tools.

**Scope:** This milestone creates an offline/reference transcript importer inside this project. It does not modify live Codex configuration, live Hermes, or live `hermes-mneme`.

## Architecture

REST remains the canonical lifecycle and ingestion surface. The Codex ingestion adapter normalizes a provided transcript JSON file into:

- `mneme.session.v0` for `POST /v1/sessions/start`;
- `mneme.event_batch.v0` containing `mneme.event.v0` events for `POST /v1/events`;
- optional `mneme.turn.v0` records for `POST /v1/turns/complete`.

MCP remains read-side memory tooling. The importer does not add MCP write tools and does not let the model mutate canonical transcript state.

## Input Contract

Use an explicit local JSON shape for the first importer:

```json
{
  "session": {
    "session_id": "codex-session-1",
    "agent_id": "codex",
    "runtime": "CODEX",
    "project_id": "mneme",
    "started_at": "2026-06-12T12:00:00Z",
    "metadata": {"cwd": "/repo"}
  },
  "turns": [
    {
      "turn_id": "turn-1",
      "started_at": "2026-06-12T12:00:00Z",
      "completed_at": "2026-06-12T12:00:10Z",
      "messages": [
        {"role": "USER", "text": "Continue"},
        {"role": "ASSISTANT", "text": "Done"}
      ]
    }
  ]
}
```

The adapter may accept optional message fields such as `event_id`, `timestamp`, `type`, `content`, `tool`, `metadata`, and `parent_event_ids`, but it must produce stable ids when those fields are absent.

## Tasks

### Task 1: Add Codex Transcript Normalizer

- [x] Write RED tests for session payload normalization, stable event ids, role/type mapping, and optional turn completion payloads.
- [x] Implement the minimum dependency-free normalizer.
- [x] Verify focused tests pass.

### Task 2: Add REST Ingestion Client Path

- [x] Write RED tests that use `httpx.ASGITransport` against the FastAPI app.
- [x] Verify the adapter calls session start before event ingest.
- [x] Verify replay is idempotent after restart or repeated import.
- [x] Verify unknown-session ingest is prevented by bootstrapping the session first.
- [x] Verify service redaction precedes storage/search for imported secrets.
- [x] Implement the minimum async import flow.
- [x] Verify focused tests pass.

### Task 3: Add CLI Import Command and Documentation

- [x] Add `mneme codex-ingest --input ... --base-url ... --token ... --timeout ...`.
- [x] Document offline/reference usage under `adapters/codex/`.
- [x] State clearly that the command imports a provided transcript file and does not modify live Codex config.
- [x] Verify CLI parser and docs tests.

### Task 4: Full Verification

- [x] Run focused Codex ingestion tests.
- [x] Run full pytest.
- [x] Run `py_compile`.
- [x] Update `task_plan.md`, `progress.md`, and `findings.md`.

## Non-Goals

- No live Codex configuration changes.
- No live Hermes or live `hermes-mneme` changes.
- No MCP ingestion tools.
- No automatic prompt replacement or deep Codex context-engine integration.
- No parsing of private Codex internal logs unless the user explicitly supplies or approves a source path later.

## Acceptance Criteria

- A provided transcript JSON can be imported into Mneme through REST.
- Imported events are searchable through existing REST/MCP memory tools.
- Re-importing the same transcript produces duplicates rather than duplicate stored events.
- Secret-like content is redacted by the service before storage and search.
- CLI and docs are clear that the path is offline/reference ingestion.
