# Progress: Mneme v0 Compliance Planning

## 2026-06-22 - Restore `spec-driven-planning` Workflow

- Loaded and followed `spec-driven-planning`.
- Loaded `mneme-memory` for session-start evidence only.
- Confirmed `.planning/` was missing.
- Created `.planning/work` directory structure before any implementation work.
- Read canonical inputs:
  - `docs/MNEME_STANDALONE_SPEC.md`
  - `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
  - `docs/MNEME_V0_COMPLIANCE_IMPLEMENTATION_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
- Resolved Mneme project memory as ambiguous; used newest matching session only
  as corroborating evidence.
- Spawned read-only explorer agents for independent extraction of spec,
  matrix/plan, and root history facts. No agent edited files.
- Created `.planning/spec.md`, `.planning/roadmap.md`,
  `.planning/findings.md`, `.planning/progress.md`, current phase plan, current
  task plans, and future phase stubs.
- No production/source code, tests, runtime config, commits, pushes, or live
  Hermes/live `hermes-mneme` changes were made.

**Planning Gate:** NOT CLEARED. Waiting for explicit user approval.

## 2026-06-22 - Planning Gate Approved, Phase 1 Started

- User explicitly approved starting implementation from the `.planning/`
  roadmap.
- Updated roadmap Planning Gate to `CLEARED - 2026-06-22`.
- Active phase is `01-contract-security-foundation`.
- Active task is `01-baseline-diff-and-red-tests`.
- Commit/push remain prohibited without separate explicit permission.

## 2026-06-22 - Phase 1 Task 01 Baseline Inventory Complete

- Reconciled current dirty Phase 1A files without reverting user or prior work.
- Added RED/GREEN evidence for S24-118 auth-failure audit persistence with
  `UNAUTHENTICATED` principal.
- Added RED/GREEN evidence for S24-25 `GLOBAL` search project filtering through
  `X-Mneme-Project-Isolation-Key`.
- Re-ran focused post-compaction verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_auth_failure_audit_uses_unauthenticated_principal tests/test_contract.py::test_global_scope_respects_project_isolation_header -q`
  -> `2 passed, 1 warning`.
- Advanced active Phase 1 task to `02-schema-catalog-openapi-components`.

## 2026-06-22 - Phase 1 Task 02 OpenAPI Foundation Complete

- Added typed OpenAPI components for health, session start, event ingest,
  session readiness, and shared memory tool request/response envelopes.
- Documented common `ErrorEnvelope` responses for core and memory-tool routes.
- Removed raw `authorization` header parameters from generated OpenAPI while
  keeping the `BearerAuth` security scheme.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_openapi.py tests/test_contract.py -q`
  -> `32 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces -q`
  -> `2 passed`.
- Advanced active Phase 1 task to `03-config-capabilities-provider-status`.

## 2026-06-22 - Phase 1 Task 03 Config/Provider Status Complete

- Added provider runtime availability reporting in capabilities without leaking
  API keys.
- Added startup fail-fast for enabled HTTP providers that require API keys when
  no injected fake/test provider is supplied.
- Added strict `QUALITY` fail-closed behavior with `503 PROVIDER_UNAVAILABLE`
  and non-strict `COST_MODE_DOWNGRADED` warnings.
- Made `require_evidence=false` readiness session-only/provider-free even when
  the caller includes a query.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `35 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py tests/test_parity_recovery.py tests/test_retrieval.py -q`
  -> `33 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
- Advanced active Phase 1 task to `04-auth-token-principal-boundary`.

## 2026-06-22 - Phase 1 Task 04 Auth Token/Principal Boundary Complete

- Added config support for `MNEME_AUTH_TOKEN_FILE`, `[auth].token_file`,
  `[auth].token_env`, and `[[auth.static_tokens]]`.
- Added `Principal` derivation for default owner bearer tokens and static
  scoped tokens.
- Added REST auth support for static scoped tokens while preserving
  auth-failure audit records.
- Added serve CLI guard against `--insecure-dev` on non-loopback binds.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `38 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_codex_adapter.py tests/test_codex_hooks.py -q`
  -> `50 passed`.
- Advanced active Phase 1 task to `05-project-scope-enforcement`.

## 2026-06-22 - Phase 1 Task 05 Project Scope Enforcement Complete

- Added principal-aware project-scope helpers and visible-session filtering.
- Scoped tokens now restrict session start, discovery, `GLOBAL` search, memory
  tools, costs, export, and delete.
- Updated capabilities to truthfully advertise current project-isolation
  support.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py tests/test_config.py -q`
  -> `42 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_retrieval.py tests/test_parity_recovery.py tests/test_context_prepare.py -q`
  -> `28 passed, 1 warning`.
- Advanced active Phase 1 task to
  `06-auth-failure-audit-safe-token-docs`.

## 2026-06-22 - Phase 1 Task 06 Auth Audit/Safe Token Docs Complete

- Retained and verified `AUTH_FAILURE` audit persistence with
  `UNAUTHENTICATED` principal.
- Removed recommended token-in-argv usage from safe public docs and generated
  Codex wrapper/hook templates.
- Added a regression guard against reintroducing token-in-argv recommendations
  in safe docs/templates.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `43 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_codex_adapter.py tests/test_codex_hooks.py -q`
  -> `50 passed`.
- Advanced active Phase 1 task to `07-phase-verification-evidence`.

## 2026-06-22 - Phase 1 Complete

- Ran Phase 1 focused verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_openapi.py tests/test_contract.py tests/test_security.py -q`
  -> `45 passed, 1 warning`.
- Ran MCP verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
- Ran full verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `167 passed, 1 warning`.
- Ran compile and diff hygiene:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` and Section 24 mapping with
  Phase 1 evidence.
- Matrix summary after Phase 1:
  `COMPLIANT=4`, `PARTIAL=52`, `MISSING=8`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Marked `01-contract-security-foundation` complete and advanced the roadmap
  active phase pointer to `02-storage-migrations-writer-idempotency`.

## 2026-06-22 - Phase 2 Detailed Planning Started

- Expanded `02-storage-migrations-writer-idempotency` from a stub into five
  executable task plans:
  `01-baseline-storage-red-tests`,
  `02-migration-schema-integrity`,
  `03-idempotency-key-ledger`,
  `04-writer-lane-storage-busy`, and
  `05-phase-verification-evidence`.
- Marked Phase 2 status `in_progress`; no Phase 2 production code has been
  changed yet.

## 2026-06-22 - Phase 2 Implementation Slices Complete, Verification Active

- Added storage migration/startup integrity foundation in `mneme_service/storage.py`:
  schema version constant, `schema_migrations`, `PRAGMA user_version`,
  `PRAGMA integrity_check`, newer-schema refusal, and mismatch refusal.
- Added durable `Idempotency-Key` ledger and route helpers for current mutating
  endpoints: `/v1/sessions/start`, `/v1/events`, `/v1/turns/complete`,
  `/v1/context/prepare`, and `DELETE /v1/sessions/{session_id}`.
- Added current-process bounded writer lane and retryable REST error surfaces
  for `RATE_LIMITED` and `STORAGE_BUSY`.
- Updated capabilities storage status from `NOT_IMPLEMENTED` to current schema
  version/migration status.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py tests/test_openapi.py -q`
  -> `40 passed, 1 warning`.
- Marked Phase 2 tasks 01-04 complete and advanced active task to
  `05-phase-verification-evidence`.

## 2026-06-22 - Phase 2 Complete

- Added batch conflict preflight so a later event conflict does not leave
  earlier batch events partially stored.
- Ran focused Phase 2 verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_security.py tests/test_openapi.py -q`
  -> `41 passed, 1 warning`.
- Ran MCP verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
- Ran full verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `180 passed, 1 warning`.
- Ran compile and diff hygiene:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` and Section 24 mapping with
  Phase 2 evidence.
- Matrix summary after Phase 2:
  `COMPLIANT=4`, `PARTIAL=53`, `MISSING=7`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Marked `02-storage-migrations-writer-idempotency` complete and advanced the
  roadmap active phase pointer to
  `03-blob-bytes-ref-export-delete-multipart`.
- Phase 3 is active but still a stub; detailed Phase 3 task plans must be
  created before any Phase 3 production implementation.

## 2026-06-22 - Phase 3 Detailed Planning Started

- Expanded `03-blob-bytes-ref-export-delete-multipart` from a stub into six
  executable task plans:
  `01-blob-storage-endpoints`,
  `02-bytes-ref-event-validation`,
  `03-multipart-event-ingest`,
  `04-session-export-delete-blob-lifecycle`,
  `05-maintenance-blob-gc`, and
  `06-phase-verification-evidence`.
- Active task is now `01-blob-storage-endpoints`.
- No Phase 3 production or test implementation has been changed yet.

## 2026-06-22 - Phase 3 Task 01 Complete

- Added RED tests for direct blob endpoints and storage tables; initial RED
  failures were `/v1/blobs` 404 and missing `blobs`/`blob_references` tables.
- Implemented server-owned SQLite blob tables, blob upload/metadata/content
  range/delete routes, `415 UNSUPPORTED_MEDIA_TYPE` and
  `416 RANGE_NOT_SATISFIABLE` envelopes, scoped blob access, and blob
  upload/delete idempotency.
- Updated OpenAPI schemas and capabilities to advertise direct blob store and
  range reads while keeping export bundle disabled until its later task.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `14 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `01-blob-storage-endpoints` complete and advanced active task to
  `02-bytes-ref-event-validation`.

## 2026-06-22 - Phase 3 Task 02 Complete

- Replaced permissive arbitrary BYTES_REF acceptance with tests requiring a
  previously uploaded visible `mneme-blob://` reference.
- Added cross-project and default `file://` BYTES_REF rejection coverage.
- Implemented JSON event-ingest BYTES_REF validation for URI, storage owner,
  existence, session/project scope, hash, size, and media type.
- Added blob reference attach/detach storage methods with duplicate-safe
  `ref_count` behavior.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_storage.py tests/test_openapi.py -q`
  -> `45 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `02-bytes-ref-event-validation` complete and advanced active task to
  `03-multipart-event-ingest`.

## 2026-06-22 - Phase 3 Task 03 Complete

- Implemented multipart `/v1/events` parsing for `payload` plus
  `blob.<client_part_id>` parts while preserving JSON ingestion and OpenAPI
  documentation.
- Added digest-aware multipart idempotency, placeholder rewrite to
  `mneme-blob://` BYTES_REF, original/normalized content hash metadata,
  part-count and byte-limit validation, and unsupported-media handling.
- Added `Store.put_blob_records_and_events` to commit blob rows, event rows,
  and blob references in one writer-lane transaction for multipart canonical
  writes.
- Added rollback coverage for invalid multipart event metadata, event-id
  conflict, and forced multipart transaction failure.
- Added runtime `python-multipart>=0.0.9` dependency declaration.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_storage.py tests/test_openapi.py -q`
  -> `54 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `03-multipart-event-ingest` complete and advanced active task to
  `04-session-export-delete-blob-lifecycle`.

## 2026-06-22 - Phase 3 Task 04 Complete

- Added v0 JSON session export shape with `mneme.session_export.v0`, stable
  blob metadata omission reasons, empty `blob_contents`, and scoped export
  denial for cross-project tokens.
- Added `format` query validation with `422 VALIDATION_ERROR` for unknown
  export formats.
- Added `tar_bundle` export with `mneme.session_export_manifest.v0`,
  `manifest.json`, and `blobs/<blob_id>.bin` entries through a spooled
  `StreamingResponse`.
- Updated session delete to remove blob references and session-owned blob rows
  in the delete transaction.
- Updated capabilities to advertise `supports_export_bundle=true` and
  `supported_export_formats=["json", "tar_bundle"]`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py -q`
  -> `50 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `04-session-export-delete-blob-lifecycle` complete and advanced active
  task to `05-maintenance-blob-gc`.

## 2026-06-22 - Phase 3 Task 05 Complete

- Added scoped `/v1/maintenance/blob-gc` with dry-run, candidate/deleted/skipped
  counts, owner-only daemon-wide GC, project/session scope enforcement, and
  `Idempotency-Key` replay/conflict behavior.
- Added `BlobGcRequest`/`BlobGcResponse` schemas and OpenAPI route coverage.
- Added storage GC candidate/deletion selection bounded by session/project.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_openapi.py -q`
  -> `23 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `05-maintenance-blob-gc` complete and advanced active task to
  `06-phase-verification-evidence`.

## 2026-06-22 - Phase 3 Complete

- Ran focused Phase 3 verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py tests/test_storage.py -q`
  -> `61 passed, 1 warning`.
- Ran MCP regression:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
- Ran full verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `202 passed, 1 warning`.
- Ran compile and diff hygiene:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` for Phase 3 evidence:
  CM-031 and CM-032 are now `COMPLIANT`; CM-033 and CM-042 moved from
  `MISSING` to `PARTIAL`; CM-036, CM-059, CM-060, CM-061, CM-062, and
  Section 24 mapping now include blob/multipart/export evidence.
- Matrix summary after Phase 3:
  `COMPLIANT=6`, `PARTIAL=55`, `MISSING=3`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Marked `03-blob-bytes-ref-export-delete-multipart` complete and advanced the
  roadmap active phase pointer to
  `04-session-lifecycle-readiness-retention`.
- Phase 4 is active but still a stub; detailed Phase 4 task plans must be
  created before any Phase 4 production implementation.

## 2026-06-23 - Phase 4 Detailed Planning And Task 01 Complete

- Expanded `04-session-lifecycle-readiness-retention` from a stub into five
  executable task plans:
  `01-session-lifecycle-endpoints`,
  `02-readiness-capabilities-contract`,
  `03-retention-cleanup-endpoint`,
  `04-retention-storage-audit-delete`, and
  `05-phase-verification-evidence`.
- Used Spark worker `019ef53b-a876-7942-ace8-a519f26dfa9d` for a read-only
  planning consistency review; aligned Phase 4 matrix-row coverage for
  CM-034, CM-055, CM-056, CM-058, and CM-061 before implementation.
- Used Spark worker `019ef53d-1495-7770-a535-bec01e316dd8` for focused RED
  tests in `tests/test_contract.py` and `tests/test_openapi.py`.
- Implemented Task 01:
  redacted `GET /v1/sessions/{session_id}`, nondestructive
  `POST /v1/sessions/{session_id}/close`, generated session ids only with
  `Idempotency-Key`, session-id validation, and typed session lifecycle
  OpenAPI schemas.
- Also corrected a stale alpha BYTES_REF contract test to require an owned
  `/v1/blobs` upload and returned `mneme-blob://` reference, matching the
  completed Phase 3 owned blob protocol.
- Verification:
  targeted lifecycle RED/GREEN command -> `5 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
  -> `21 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `48 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `01-session-lifecycle-endpoints` complete and advanced active task to
  `02-readiness-capabilities-contract`.

## 2026-06-23 - Phase 4 Task 02 Complete

- Used Spark worker `019ef547-ff05-7143-809b-05c210e40924` for a narrow
  readiness/capabilities test-coverage inspection.
- Added readiness contract coverage for unknown-session `404`, session-only
  `require_evidence=false`, and provider-free readiness behavior.
- Extended OpenAPI readiness assertions to include `401`, `404`, `412`, and
  `422` error envelopes.
- No production code changes were needed for Task 02; current route behavior
  already matched the added assertions.
- Verification:
  targeted readiness/OpenAPI command -> `3 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
  -> `22 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed.
- Marked `02-readiness-capabilities-contract` complete and advanced active task
  to `03-retention-cleanup-endpoint`.

## 2026-06-23 - Phase 4 Task 03 Complete

- Added retention cleanup contract tests for active-session default skip,
  idempotency replay, ENDED-session timestamp cutoff/candidate counting,
  scoped visible-project enforcement, scoped force-active rejection, and
  OpenAPI route/schema documentation.
- Implemented typed `RetentionCleanupRequest` and
  `RetentionCleanupResponse` schemas.
- Implemented `POST /v1/sessions/{session_id}/retention/cleanup` with
  existing session/project scope checks, optional schema-version validation,
  default body semantics (`dry_run=false`, `force_active_cleanup=false`),
  OWNER-only forced active cleanup, and idempotency replay/conflict.
- Added storage-side `retention_candidate_counts` for truthful event
  eligibility preview by timestamp cutoff. Actual event/derivative/blob
  deletion remains intentionally deferred to Task 04.
- Left `supports_retention_cleanup=false` until Task 04 implements full
  deletion/audit lifecycle, avoiding premature capability advertisement.
- Verification:
  targeted retention/OpenAPI command -> `4 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
  -> `25 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `52 passed, 1 warning`.
- A Spark read-only auditor was spawned for Task 03 but was closed while still
  running, so no auditor findings are recorded as evidence.
- Marked `03-retention-cleanup-endpoint` complete and advanced active task to
  `04-retention-storage-audit-delete`.

## 2026-06-23 - Phase 4 Task 04 Complete

- Added retention storage/audit tests for eligible event/blob cleanup,
  anonymized forensic audit anchors after privacy delete, and observable scoped
  session-close retention sweeps.
- Implemented `Store.cleanup_retention` to delete eligible session events by
  cutoff, remove event-derived embedding/graph/trace/state-history records,
  detach blob references, and let scoped blob GC delete newly orphaned blobs.
- Extended retention cleanup responses with spec-facing `status`,
  flattened deletion counters, `skipped_active_session`, and
  `in_flight_reads_blocked`.
- Implemented explicit `RETENTION_CLEANUP` audit for manual endpoint calls and
  `SYSTEM_DAEMON` `RETENTION_CLEANUP` audit for session-close sweeps.
- Changed `supports_retention_cleanup` to `true` after actual cleanup/delete
  behavior became tested.
- Implemented privacy-delete forensic anchor conversion for sensitive audit
  actions, preserving action/tool/timestamp/principal class and salted hashes
  while removing raw session id, event ids, trace ids, request payloads,
  result payloads, and content.
- Verification:
  targeted Task 04 command -> `3 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_blobs.py tests/test_openapi.py -q`
  -> `55 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked `04-retention-storage-audit-delete` complete and advanced active task
  to `05-phase-verification-evidence`.

## 2026-06-23 - Phase 4 Complete

- Completed Phase 4 Task 05 verification/evidence update.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` to Phase 4 status, including
  lifecycle/readiness/retention implementation evidence, Phase 4 verification
  commands, and Section 24 mapping for S24-2, 3, 46, 48-50, 59, 64, 67,
  73-74, 84, 86, 91-92, and 111.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_blobs.py tests/test_openapi.py tests/test_storage.py -q`
  -> `55 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `196 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked `04-session-lifecycle-readiness-retention` complete and advanced the
  roadmap active phase pointer to `05-state-segments-lineage-graph-routing`.
- Phase 5 is still a stub. It must be expanded into detailed task plans before
  any Phase 5 production/test implementation begins.

## 2026-06-23 - Phase 5 Detailed Planning Complete

- Used Spark worker `019ef560-2f59-7f42-b342-4d7de2ab7a74` for a read-only
  Phase 5 decomposition review.
- Expanded `05-state-segments-lineage-graph-routing` from a stub into six
  executable task plans:
  `01-execution-state-update-history`,
  `02-graph-traversal-limits-anchors`,
  `03-segment-rest-contract`,
  `04-routing-classifier-entity-modifiers`,
  `05-session-discovery-lineage-search`, and
  `06-phase-verification-evidence`.
- Active Phase remains `05-state-segments-lineage-graph-routing`; active task
  is now `01-execution-state-update-history`.
- No production code or tests were changed during Phase 5 planning.

## 2026-06-23 - Phase 5 Task 01 Complete

- Added explicit execution-state update tests for PATCH/REPLACE behavior,
  required provenance, unknown-field rejection, and OpenAPI request/response
  schemas.
- Implemented typed `ExecutionStateUpdateRequest` and
  `ExecutionStateUpdateResponse`.
- Added `POST /v1/sessions/{session_id}/execution_state` with session/project
  scope checks, schema-version validation, mode validation, allowed-field
  validation, provenance validation, and redaction before persistence.
- Extended state history persistence with additive columns for mode,
  changed fields, state hash, previous state hash, provenance, and summary.
- Implemented deterministic `sha256:<hex>` state hashing over existing
  canonical JSON.
- Verification:
  targeted RED/GREEN command -> `3 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_openapi.py -q`
  -> `14 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
  -> `48 passed, 1 warning`;
  `git diff --check` -> passed.
- Marked `01-execution-state-update-history` complete and advanced active task
  to `02-graph-traversal-limits-anchors`.

## 2026-06-23 - Phase 5 Task 02 Complete

- Added graph traversal limit tests for deterministic expansion order,
  max-events warning, depth-limit warning, and bounded importance boost.
- Reworked `expand_graph` into a deterministic traversal result that returns
  event depth, `importance_boost`, `truncated`, `truncation_reason`, and
  REST/MCP-compatible warning envelopes.
- Kept existing typed parent-derived graph edges and audit behavior intact.
  `SEGMENT_ANCHOR` and `MEMORY_READ_EVIDENCE` edge expansion remain with later
  Phase 5 tasks.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q`
  -> `5 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
  -> `50 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked `02-graph-traversal-limits-anchors` complete and advanced active task
  to `03-segment-rest-contract`.

## 2026-06-23 - Phase 5 Task 03 Complete

- Added direct segment REST tests for manual start/close/list/get/events,
  generated segment ids requiring `Idempotency-Key`, and OpenAPI request/
  response schemas.
- Implemented typed segment request/response schemas and direct
  `/v1/segments/start`, `/v1/segments`, `/v1/segments/{segment_id}`,
  `/v1/segments/{segment_id}/events`, and
  `/v1/segments/{segment_id}/close` routes with session/project scope checks.
- Preserved existing tool-envelope segment behavior while mapping direct REST
  active segments to public `OPEN` status and manual starts to
  `created_by=ADAPTER`.
- Recorded residual Task 03 gaps for `SEGMENT_ANCHOR` graph edges and broader
  lifecycle enum/edge-case coverage.
- Verification:
  targeted RED/GREEN command -> `2 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py -q`
  -> `12 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py -q`
  -> `52 passed, 1 warning`;
  `git diff --check` -> passed.
- Marked `03-segment-rest-contract` complete and advanced active task to
  `04-routing-classifier-entity-modifiers`.

## 2026-06-23 - Phase 5 Task 04 Complete

- Used Spark worker `019ef571-7d4d-7402-9dd3-fb6dbf1f0725` for a read-only
  Task 04 requirement/gap checklist covering Sections 12.9, 14.5.1, 14.11,
  Section 16, and Section 24 IDs S24-93, S24-97-103, and S24-112.
- Added deterministic classifier coverage and implementation for priority
  chain precedence, five-whitespace-word entity contradiction, replacement
  patterns, and ordered `mneme.entity_modifier.v0` objects.
- Replaced routing mode weights with Section 14.11 defaults, accepted explicit
  request `mode`, attached per-result and trace `score_breakdown` objects, and
  preserved scope reporting.
- Added continuation query construction for `/v1/context/prepare` from
  `execution_state.goal`, `current_step`, `active_entities`, and
  `last_tool_output_summary`, with trace `query_built_from` evidence.
- Added direct `MEMORY_READ` feedback: bounded redacted execution-state
  `last_tool`/`last_tool_output_summary` updates and `MEMORY_READ_EVIDENCE`
  graph edges, while keeping retrieval filters excluding memory reads.
- Verification:
  targeted RED/GREEN command -> `13 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_classifier.py tests/test_retrieval.py tests/test_contract.py tests/test_context_prepare.py -q`
  -> `40 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py tests/test_classifier.py tests/test_context_prepare.py -q`
  -> `65 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked `04-routing-classifier-entity-modifiers` complete and advanced active
  task to `05-session-discovery-lineage-search`.

## 2026-06-23 - Phase 5 Task 05 Complete

- Used Spark worker `019ef581-a6d8-71a2-b8e6-7c346d7e9873` for a read-only
  Task 05 gap map over session discovery, best-guess semantics, lineage
  visibility, PROJECT/GLOBAL scope, pagination, and MCP parity.
- Added S24-78 resolve-session best-guess tests covering deterministic exact
  project-path preference before recency and `null` best-guess when ambiguity
  differs only by recency.
- Implemented deterministic `resolve_session` ordering and
  `best_guess_session_id` semantics with `SESSION_RESOLUTION_AMBIGUOUS`
  warnings.
- Added explicit `PROJECT` context-search scope bounded to the current
  session's project isolation key, and made `SESSION` current-session-only
  while preserving explicit `LINEAGE` carry-over behavior.
- Prevented canonical `MEMORY_READ` events from reappearing as graph
  dependency or graph expansion evidence after memory-tool feedback edges.
- Verification:
  targeted RED/GREEN command -> `5 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_retrieval.py tests/test_mcp_contract.py tests/test_session_lineage.py -q`
  -> `49 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py tests/test_classifier.py tests/test_context_prepare.py tests/test_session_lineage.py tests/test_mcp_contract.py -q`
  -> `86 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked `05-session-discovery-lineage-search` complete and advanced active
  task to `06-phase-verification-evidence`.

## 2026-06-23 - Phase 5 Task 06 Complete And Phase 6 Planned

- Completed Phase 5 verification/evidence task.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` with Phase 5 OpenAPI inventory,
  verification gates, matrix row evidence, status changes for CM-030 and
  CM-038, and Section 24 mapping updates.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_segments.py tests/test_graph.py tests/test_contract.py tests/test_retrieval.py tests/test_openapi.py tests/test_classifier.py tests/test_context_prepare.py tests/test_session_lineage.py -q`
  -> `70 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `210 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  -> passed;
  `git diff --check` -> passed.
- Marked Phase 5 and `06-phase-verification-evidence` complete, advanced
  roadmap active phase to
  `06-context-prepare-redaction-prompt-injection-freshness`.
- Used Spark worker `019ef590-cf31-7bd2-9c40-d12a5ca085ab` for a read-only
  Phase 6 stub audit and expanded Phase 6 into six detailed task plans:
  budget/token accounting, latest-user/headroom, evidence wrappers, redaction,
  freshness, and phase verification.

## 2026-06-23 - Phase 6 Task 01 Complete

- Used Spark worker `019ef596-deb7-78e1-b8cd-005a9c1b8406` for bounded
  implementation of canonical context-prepare budget split handling.
- Added canonical `budget_split` validation and defaults:
  `headroom_ratio=0.10`, `execution_state_ratio=0.12`,
  `protected_tail_ratio=0.28`, `retrieved_evidence_ratio=0.45`, and
  `hints_ratio=0.05` when the split is omitted; supplied splits default
  omitted `hints_ratio` to `0.0` and reject unknown keys.
- Added deprecated `policy.headroom_ratio` normalization with
  `DEPRECATED_FIELD_NORMALIZED`, deterministic budget trace fields,
  `execution_state_compression_level`, and changed-prepare
  `COST_MODE_DOWNGRADED` evidence for char-approximate STANDARD/QUALITY
  prepare.
- Updated internal payload builders and tests from legacy
  `retrieved_context_ratio`/`recent_tail_ratio` to canonical
  `retrieved_evidence_ratio`/`protected_tail_ratio`; the only remaining legacy
  key use is the negative unknown-key test.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q`
  -> `11 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
  -> `6 passed, 1 warning`;
  focused contract/context/parity gate -> `56 passed, 1 warning`;
  full suite -> `214 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Recorded S24-20 as residual: current behavior warns on changed
  STANDARD/QUALITY char-approximate prepare, but full reject/downgrade-to-
  MINIMAL semantics still need final Phase 6 resolution.
- Marked `01-budget-contract-token-accounting` complete and advanced active
  task to `02-latest-user-headroom-impossible-budget`.

## 2026-06-23 - Phase 6 Task 02 Complete

- Used Spark worker `019ef5a1-89ea-7ae3-ab6b-832b7f51bcf5` for bounded
  implementation of latest-user hard protection and impossible-budget errors.
- Added whole-message latest user preservation, `latest_user_message_index`,
  and protected-tail packing that excludes the protected latest user from
  historical tail truncation.
- Added exact `422 VALIDATION_ERROR` reasons:
  `LATEST_USER_MESSAGE_EXCEEDS_BUDGET` and
  `MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET`.
- Added tests for byte-for-byte latest user preservation, latest-user over
  budget, and minimum-required over budget; adjusted a collision-budget fixture
  to keep exercising retrieved-evidence dropping rather than the new minimum
  failure path.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q`
  -> `14 passed, 1 warning`;
  focused contract/MCP/parity/resume gate -> `47 passed, 1 warning`;
  full suite -> `217 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `02-latest-user-headroom-impossible-budget` complete and advanced
  active task to `03-evidence-wrappers-trust-labels`.

## 2026-06-23 - Phase 6 Task 03 Complete

- Used Spark worker `019ef5a6-90e6-77a2-8189-a551ae596e75` for a read-only
  Task 03 wrapper/trust-label audit, then implemented the shared rendering
  change in the parent thread.
- Added XML data-only wrappers for retrieved evidence:
  `<mneme_untrusted_evidence event_id="..." source_trust="..." event_type="...">`.
- Added XML escaping for event ids, trust labels, event type, and evidence
  text, and switched retrieved-event token accounting to the wrapped rendered
  text.
- Added additive trace `source_trust` metadata for selected retrieved events.
- Added tests for hostile evidence wrapper escaping and trace source-trust
  recording; adjusted budget fixtures for wrapper overhead.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_mcp_contract.py -q`
  -> `32 passed, 1 warning`;
  full suite -> `219 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `03-evidence-wrappers-trust-labels` complete and advanced active task
  to `04-redaction-profile-timeout-binary-safety`.

## 2026-06-24 - Phase 6 Task 04 Complete

- Used Spark worker `019ef5ad-db01-7331-a33f-1b82e9d3477e` for a read-only
  Task 04 redaction/binary audit and Spark worker
  `019ef9e9-6841-7121-a8c4-cfb5ed27392e` for read-only diff review.
  Spark worker `019ef5b1-9173-73f1-8673-c149663efeef` failed with a stream
  disconnect during a binary inventory, so the parent performed that narrow
  inspection directly.
- Expanded the default redaction profile in `mneme_service/security.py` for
  Authorization headers, Bearer tokens, OpenAI-style keys, GitHub tokens, AWS
  access keys, Google API keys, JWT-like tokens, private-key PEM blocks,
  database/URL credentials, `.env` assignments, and sensitive JSON fields.
- Added foreground event-ingest timeout handling using
  `settings.max_redaction_time_ms`; timeout now rejects with `422` and
  `reason=REDACTION_TIMEOUT` without echoing plaintext.
- Added positive startup validation for `indexing.max_redaction_time_ms`.
- Added non-text `BYTES_REF` event marking with
  `redaction_scope=BINARY_METADATA_ONLY` while preserving existing metadata-only
  content text for indexing/search.
- Added RED/GREEN coverage in `tests/test_contract.py` for expanded secret
  fixtures, timeout rejection, benign key false positives, and binary
  metadata-only storage; added config validation coverage in
  `tests/test_config.py`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_context_prepare.py tests/test_mcp_contract.py -q`
  -> `55 passed, 1 warning`;
  expanded touched-area gate
  `tests/test_contract.py tests/test_context_prepare.py tests/test_mcp_contract.py tests/test_config.py tests/test_blobs.py tests/test_embeddings.py -q`
  -> `102 passed, 1 warning`;
  full suite -> `223 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `04-redaction-profile-timeout-binary-safety` complete and advanced
  active task to `05-freshness-conflict-semantics`.

## 2026-06-24 - Phase 6 Task 05 Complete

- Used Spark worker `019ef9ef-ac9c-7841-a2fe-2af8b2e2766c` for a read-only
  Section 14.14 audit and Spark worker
  `019ef9f4-55af-7822-aba8-efbf1e938d9b` for read-only Task 05 diff review.
- Added source-supplied freshness propagation for retrieval/context evidence:
  `context_search` results include `freshness`, context-prepare trace selected
  events include `freshness`, and retrieved evidence wrappers include a
  `freshness` attribute.
- Added explicit conflict handling: `CURRENT` evidence with
  `conflicting_event_ids` drops matching memory evidence before packing and
  emits `FRESHNESS_CONFLICT` in context-prepare response/trace warnings.
- Added guard coverage proving old Mneme evidence is not automatically marked
  `STALE_OR_CONFLICTING` without source-supplied conflict metadata.
- Verification:
  Task 05 RED/GREEN focused set -> `3 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_context_prepare.py tests/test_contract.py -q`
  -> `49 passed, 1 warning`;
  full suite -> `226 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `05-freshness-conflict-semantics` complete and advanced active task
  to `06-phase-verification-evidence`.

## 2026-06-24 - Phase 6 Complete

- Ran Phase 6 verification gates:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_retrieval.py tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q`
  -> `75 passed, 1 warning`;
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`;
  full suite -> `226 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` with Phase 6 evidence,
  Section 24 mapping updates, and matrix counts:
  `COMPLIANT=6`, `PARTIAL=58`, `MISSING=0`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Marked `06-phase-verification-evidence` and the Phase 6 plan complete.
- Advanced roadmap active phase to
  `07-operations-metrics-maintenance-reindex`.
- Next required action: expand the Phase 7 stub into detailed task plans before
  starting production/test implementation for operations, metrics,
  maintenance, and reindex work.

## 2026-06-24 - Phase 7 Planning Expanded

- Used Spark worker `019ef9fa-9f61-7cd0-8271-000a8760729a` for a read-only
  Phase 7 operations/metrics/maintenance/reindex audit.
- Expanded `.planning/work/07-operations-metrics-maintenance-reindex/plan.md`
  from a phase stub into six detailed tasks:
  `01-operations-contract-openapi-capabilities`,
  `02-metrics-endpoint-observability-counters`,
  `03-reindex-create-poll-scope-idempotency`,
  `04-reindex-cancel-provider-safety`,
  `05-reindex-engine-resiliency-priority`, and
  `06-phase-verification-evidence`.
- Active Task is now `01-operations-contract-openapi-capabilities`.

## 2026-06-24 - Phase 7 Task 01 Complete

- Used Spark worker `019efa06-1860-7670-8ef0-e460b4254498` for read-only
  contract review of Sections 14.7, 14.8, 19, 20, and 21.
- Added typed OpenAPI/capabilities coverage for `/v1/metrics`,
  `/v1/maintenance/reindex`, `/v1/maintenance/reindex/{job_id}`, and
  `/v1/maintenance/reindex/{job_id}/cancel`.
- Added schemas `MetricsResponse`, `ReindexRequest`,
  `ReindexCancelRequest`, `ReindexJobProgress`, and `ReindexJobResponse`.
- Added minimal runtime contract support for Prometheus text metrics and
  in-process reindex create/poll/cancel job records, with scoped
  project/session/all access checks and v0 error envelopes.
- Verification:
  RED OpenAPI slice -> `1 failed, 1 passed, 6 deselected, 1 warning`;
  focused new slice -> `4 passed, 32 deselected, 1 warning`;
  required Task 01 gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_config.py tests/test_contract.py -q`
  -> `54 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `01-operations-contract-openapi-capabilities` complete and advanced
  active task to `02-metrics-endpoint-observability-counters`.

## 2026-06-24 - Phase 7 Task 02 Complete

- Used Spark worker `019efa0b-2da5-7d81-9c3f-59f5db5d4d32` for read-only
  metrics data-source inventory.
- Added `tests/test_metrics.py` RED/GREEN coverage for required Prometheus
  family names and secret/evidence-safe output.
- Implemented lightweight HTTP request count/latency instrumentation and
  Prometheus text export for required operational and retrieval-intelligence
  metric families.
- Added storage aggregate snapshot helpers for numeric provider counters,
  embedding status counts, blob bytes/count, retention sweeps, intent labels,
  segment rollover traces, routing modes, and indexing compression counts.
- Verification:
  RED metrics check -> `1 failed, 1 passed, 1 warning`;
  GREEN metrics check -> `2 passed, 1 warning`;
  focused Task 02 gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py tests/test_openapi.py tests/test_contract.py -q`
  -> `38 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `02-metrics-endpoint-observability-counters` complete and advanced
  active task to `03-reindex-create-poll-scope-idempotency`.

## 2026-06-25 - Phase 7 Task 03 Complete

- Used Spark worker `019efa10-e761-7460-a5db-c46bc2517cd3` for read-only
  reindex persistence/idempotency/scope audit.
- Added `tests/test_reindex.py` coverage for scoped create/poll permissions,
  out-of-scope poll `404`, `Idempotency-Key` replay/conflict,
  `PROVIDER_UNAVAILABLE` default behavior, `WAITING_FOR_PROVIDER` enqueue mode,
  `QUEUED` provider-backed jobs, candidate progress fields, and persistence
  across app restart.
- Added persistent `reindex_jobs` storage and candidate counting in
  `mneme_service/storage.py`.
- Updated `/v1/maintenance/reindex` create/poll in `mneme_service/app.py` for
  normalized idempotency, provider availability behavior, persistent jobs, and
  scope-safe polling.
- Verification:
  RED reindex check -> `4 failed, 1 warning`;
  GREEN reindex check -> `4 passed, 1 warning`;
  focused task/regression gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_openapi.py tests/test_embeddings.py tests/test_metrics.py tests/test_contract.py -q`
  -> `53 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `03-reindex-create-poll-scope-idempotency` complete and advanced
  active task to `04-reindex-cancel-provider-safety`.

## 2026-06-25 - Phase 7 Task 04 Complete

- Used Spark worker `019efd97-2eb4-7e92-8ca0-bca1fbe6e47d` for read-only
  review of the cancel/provider-safety boundary.
- Added cancel tests for `WAITING_FOR_PROVIDER`, `QUEUED`, manually seeded
  `RUNNING`, final-state idempotency, repeated `CANCELLED` replay, no provider
  calls during cancel, zero progress after queued cancel, metrics status
  bucket, and session-scoped `REINDEX_CANCEL` audit evidence.
- Updated cancel endpoint to persist `CANCELLED` status and emit safe audit for
  session-scoped jobs.
- Recorded plan correction: full S24-75 worker-path proof is transferred to
  Task 05 because no reindex execution engine exists before that task.
- Verification:
  RED audit check -> `1 failed, 6 deselected, 1 warning`;
  focused Task 04 gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_metrics.py -q`
  -> `10 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `04-reindex-cancel-provider-safety` complete and advanced active task
  to `05-reindex-engine-resiliency-priority`.

## 2026-06-25 - Phase 7 Task 05 Complete

- Used Spark worker `019efd9c-e8ff-76a2-b352-4dfd1dc28970` for read-only
  review of the minimal reindex drain engine; fixed the high-value residuals it
  found before closing the task.
- Added deterministic internal `app.state.run_reindex_job_once(job_id)` drain
  hook for bounded reindex execution without adding a public route.
- Added storage support for listing reindex candidates and updating event
  `ingestion.embedding_status` after failed derived indexing.
- Added tests for cancelled-job drain skipping provider calls, provider failure
  marking job/event failed, provider wait timeout failure, bounded
  max-events-per-transaction slices, foreground write between slices, and
  reindex-level circuit blocking future provider calls after failure budget.
- Verification:
  RED drain check -> `3 failed, 7 deselected, 1 warning`;
  GREEN drain check -> `3 passed, 7 deselected, 1 warning`;
  RED failure/timeout check -> `2 failed, 9 deselected, 1 warning`;
  GREEN failure/timeout check -> `2 passed, 9 deselected, 1 warning`;
  RED circuit check -> `1 failed, 11 deselected, 1 warning`;
  GREEN circuit check -> `1 passed, 11 deselected, 1 warning`;
  focused Task 05 gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_storage.py tests/test_embeddings.py -q`
  -> `32 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `05-reindex-engine-resiliency-priority` complete and advanced active
  task to `06-phase-verification-evidence`.

## 2026-06-25 - Phase 7 Task 06 And Phase Complete

- Used Spark worker `019efda7-2157-7362-b2f0-4450c1baefd6` for read-only
  Phase 7 compliance/matrix/Section 24 evidence review before updating final
  phase artifacts.
- Ran required Phase 7 verification:
  focused operations/reindex gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_metrics.py tests/test_openapi.py tests/test_contract.py tests/test_config.py tests/test_embeddings.py tests/test_storage.py -q`
  -> `88 passed, 1 warning`;
  MCP regression
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`;
  full suite
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `243 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` to Phase 7 baseline with
  metrics/reindex OpenAPI paths, `reindex_jobs` storage evidence, impacted CM
  row evidence, and Section 24 reindex/metrics mapping.
- Kept broad rows such as CM-020, CM-041, CM-042, CM-057, CM-058, CM-060,
  CM-061, CM-062, and CM-063 `PARTIAL` where row-level scope still extends
  into later phases or final acceptance, while marking S24-52/63 directly
  compliant.
- Marked Phase 7 complete and advanced active roadmap phase to
  `08-mcp-parity-default-session-resolution-versioning`.

## 2026-06-25 - Phase 8 Planning Expanded And Task 01 Complete

- Expanded Phase 8 from stub into five detailed tasks:
  `01-rest-mneme-cost-report-parity`,
  `02-tool-envelope-session-resolution`,
  `03-mcp-default-session-stale`,
  `04-mcp-error-version-parity`, and
  `05-phase-verification-evidence`.
- Used Spark worker `019efdad-2c54-7692-aac2-d0ef63f31957` for read-only
  Phase 8 gap/planning review; its findings matched the parent plan: missing
  REST `mneme_cost_report`, missing `session_resolution`, no trusted default
  session/stale-default path, incomplete error mapping, and versioning gaps.
- Task 01 added `POST /v1/tools/mneme_cost_report`, changed MCP
  `mneme_cost_report` to proxy that canonical REST tool route, and extended
  OpenAPI/tool parity tests.
- Verification:
  RED focused parity slice -> `3 failed, 50 deselected, 1 warning`;
  GREEN focused parity slice -> `3 passed, 50 deselected, 1 warning`;
  Phase 8 touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
  -> `53 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `01-rest-mneme-cost-report-parity` complete and advanced active task
  to `02-tool-envelope-session-resolution`.

## 2026-06-25 - Phase 8 Task 02 Complete

- Used Spark worker `019efdb2-9d0b-7b23-a81a-8ba8646db7dc` for read-only
  inventory of session-bound tool routes and session-resolution helper shape.
- Added typed optional `SessionResolution` to `ToolResponseEnvelope`.
- Added `session_resolution.source="EXPLICIT_ARGUMENT"` for session-bound REST
  and MCP tools, and `RESOLVED_BY_TOOL` for concrete `resolve_session`
  outcomes while keeping non-session-bound `list_sessions` unannotated.
- Verification:
  RED/GREEN session-resolution slice
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q -k "session_resolution or resolve_session"`
  -> RED `1 failed, 3 passed, 50 deselected, 1 warning`, then GREEN
  `4 passed, 50 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
  -> `54 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `02-tool-envelope-session-resolution` complete and advanced active
  task to `03-mcp-default-session-stale`.

## 2026-06-25 - Phase 8 Task 03 Complete

- Added trusted immutable MCP default-session support through
  `create_mcp_server(default_session_id=...)` and CLI/env
  `--default-session-id` / `MNEME_MCP_DEFAULT_SESSION_ID`.
- Added `default_session_source="HOST_INJECTED"` factory support for trusted
  host proxies/adapters without exposing a model-visible source override in MCP
  tool arguments.
- Session-bound MCP tools now accept omitted `session_id` only when immutable
  default context is configured; explicit session arguments still take
  precedence and there is no mutable global current-session state.
- First omitted-session call validates the trusted default with authenticated
  `GET /v1/sessions/{session_id}` and returns MCP-only
  `DEFAULT_SESSION_STALE` with discovery guidance if missing/out of scope.
- Verification:
  RED default-session slice -> `2 failed, 19 deselected`;
  GREEN focused gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q -k "default_session or host_injected or omitted_session or stale or session_resolution or mcp_cli"`
  -> `7 passed, 15 deselected`;
  task gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py -q`
  -> `50 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `03-mcp-default-session-stale` complete and advanced active task to
  `04-mcp-error-version-parity`.

## 2026-06-25 - Phase 8 Task 04 Complete

- Used Spark worker `019efdbb-8c69-7723-ae9c-c55622c4e480` for read-only
  review of MCP error mapping and minimal version/schema evidence.
- Added missing REST-client fallback mappings for `415 UNSUPPORTED_MEDIA_TYPE`
  and `416 RANGE_NOT_SATISFIABLE`, while preserving server-sent error envelope
  codes such as `STORAGE_BUSY`.
- Added shared REST tool request schema-version validation for
  `mneme.tool_request.v0`; unsupported tool schema versions now fail with
  `422 VALIDATION_ERROR` on multiple tool routes.
- Verification:
  RED focused slice -> `2 failed, 1 passed, 58 deselected, 1 warning`;
  GREEN focused slice
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q -k "error_mapping or retryable or mcp_tool_versions or schema_version or storage_busy"`
  -> `3 passed, 58 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q`
  -> `61 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `04-mcp-error-version-parity` complete and advanced active task to
  `05-phase-verification-evidence`.

## 2026-06-25 - Phase 8 Task 05 And Phase Complete

- Ran required Phase 8 verification:
  focused MCP parity gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py tests/test_openapi.py -q`
  -> `61 passed, 1 warning`;
  full suite
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `252 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` to Phase 8 baseline with
  `/v1/tools/mneme_cost_report`, MCP default-session/session-resolution/error
  mapping/version evidence, and Section 24 MCP rows.
- Moved CM-043, CM-049, and CM-050 to `COMPLIANT`; matrix row counts are now
  `COMPLIANT=9`, `PARTIAL=55`, `MISSING=0`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Marked Phase 8 complete and advanced active roadmap phase to
  `09-benchmarks-package-split`.
## 2026-06-25 - Phase 9 Task 01 Complete

- Added TDD coverage for local benchmark methodology and labeled quality
  reports in `tests/test_benchmarks.py`.
- Updated `mneme_service/benchmarks.py` so `mneme benchmark` emits
  `methodology` and `quality_report` fields while explicitly avoiding
  token/cost savings claims without a comparative baseline.
- Used Spark worker `019efdc8-d002-7fe0-bb03-81097ff21806` for read-only docs
  scan; it found no mandatory Task 01 doc fix and deferred benchmark caveat
  mirroring to Task 03.
- Verification:
  RED focused benchmark -> `3 failed, 1 passed, 1 warning`;
  GREEN focused benchmark
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py -q`
  -> `4 passed, 1 warning`;
  task gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_config.py -q`
  -> `22 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `01-benchmark-methodology-quality-report` complete and advanced
  active Phase 9 task to `02-core-adapter-release-boundary`.

## 2026-06-25 - Phase 9 Task 02 Complete

- Used Spark worker `019efdcc-536d-7333-8927-9fd737fdc61b` for read-only
  packaging-boundary inspection; it confirmed current setuptools discovery
  excludes `adapters/*` via `include = ["mneme_service*"]` and recommended an
  executable regression test.
- Added `tests/test_codex_adapter.py::test_core_package_discovery_excludes_host_adapters`
  to lock core package discovery to `mneme_service*` and assert publication
  docs require a separate Codex adapter repository/package.
- Verification:
  focused adapter suite
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`
  -> `12 passed`;
  task gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_benchmarks.py -q`
  -> `16 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `02-core-adapter-release-boundary` complete and advanced active Phase
  9 task to `03-docs-honest-integration-nongoals`.

## 2026-06-25 - Phase 9 Task 03 Complete

- Added docs-contract coverage in `tests/test_codex_adapter.py` to require
  release docs to state benchmark smoke methodology, fake providers, no
  external provider calls, no comparative baseline, no token/cost proof, and
  no automatic prompt replacement.
- Updated `docs/INSTALLATION.md`, `docs/TESTING_AND_CI.md`, and
  `docs/BENCHMARKS.md` with benchmark methodology and no-savings-proof caveats;
  `docs/BENCHMARKS.md` now shows the new methodology and quality-report fields.
- Verification:
  RED focused docs slice -> `1 failed, 3 passed, 27 deselected, 1 warning`;
  GREEN focused docs slice
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_config.py -q -k "benchmark_smoke or prompt_replacement or publication_docs"`
  -> `4 passed, 27 deselected, 1 warning`;
  task gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_config.py -q`
  -> `31 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Marked `03-docs-honest-integration-nongoals` complete and advanced active
  Phase 9 task to `04-phase-verification-evidence`.

## 2026-06-25 - Phase 9 Task 04 And Phase Complete

- Ran Phase 9 focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_codex_adapter.py tests/test_config.py -q`
  -> `35 passed, 1 warning`.
- Ran full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `256 passed, 1 warning`.
- Ran compileall and diff hygiene successfully:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  and `git diff --check` both exited 0 with no output.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` to Phase 9 baseline:
  `COMPLIANT=12`, `PARTIAL=52`, `MISSING=0`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Moved CM-010, CM-011, and CM-016 to `COMPLIANT`; updated CM-020, CM-057,
  CM-061, CM-062, CM-063, and CM-064 with Phase 9 evidence; moved Section 24
  mapping row `72, 77, 108` to `COMPLIANT`.
- Marked Phase 9 complete and advanced active roadmap phase to
  `10-final-acceptance-reviewer-packet`.

## 2026-06-25 - Phase 10 Planning Expanded And Residual Audit Started

- Expanded `10-final-acceptance-reviewer-packet` from a phase stub into a
  detailed active phase plan with five tasks:
  residual matrix/Section 24 audit, two bounded residual fix batches, final
  verification/matrix, and reviewer packet acceptance.
- Created task plan files under `.planning/work/10-final-acceptance-reviewer-packet/`.
- Started Spark read-only residual audits:
  `019efdd8-0131-7483-9b71-3d9521f53903` for CM-002..020,
  `019efdd8-57a5-77b3-a4ed-396df371f148` for CM-021..042,
  `019efdd8-a461-7770-9b7a-ceaaf7a76e39` for CM-044..060,
  and `019efdd8-edfc-7103-b651-9cde204fbdea` for CM-061/062/063/065 plus
  Section 24 numbering.

## 2026-06-25 - Phase 10 Task 01 Complete And Batch A Complete

- Completed residual matrix/Section 24 audit. Section 24 numbers 1-119 are all
  mapped, with 39 compliant IDs and 80 partial IDs after Phase 9.
- Identified explicit scope-decision blockers for final acceptance:
  CM-013/CM-014 require either implementation or user-approved deferral for
  missing host lifecycle/Hermes hook depth; CM-061/CM-062 cannot close until
  residual Section 24 partials are resolved or accepted.
- Completed Batch A security/idempotency fixes:
  token files must be owner-only, execution-state update supports durable
  `Idempotency-Key` replay/conflict, and segment close supports durable
  `Idempotency-Key` replay/conflict.
- Verification:
  RED focused Batch A -> `6 failed, 2 passed, 30 deselected, 1 warning`;
  GREEN focused Batch A
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_state.py tests/test_segments.py -q -k "token_file or idempotency"`
  -> `8 passed, 30 deselected, 1 warning`;
  batch gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_state.py tests/test_segments.py tests/test_contract.py -q`
  -> `66 passed, 1 warning`;
  compileall and `git diff --check` passed.

## 2026-06-25 - Phase 10 Batch B Complete

- Added explicit S24-20 test and implementation for model-bound
  STANDARD/QUALITY `/v1/context/prepare` when only local `CHAR_APPROXIMATE`
  token estimates are available.
- Behavior: explicit `policy.model_bound=true` now returns
  `422 VALIDATION_ERROR` with reason
  `CHAR_APPROXIMATE_MODEL_BOUND_PREPARE`, `token_estimate_quality`, and
  `effective_cost_mode=MINIMAL`; non-model-bound diagnostics still return
  warning-only downgrade behavior.
- Verification:
  RED focused -> `1 failed, 1 passed, 17 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q -k "tokenizer_quality or char_approx"`
  -> `2 passed, 17 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_contract.py -q`
  -> `47 passed, 1 warning`;
  compileall and `git diff --check` passed.

## 2026-06-25 - Phase 10 Post Batch A/B Full Verification

- Re-ran full suite after Batch A and Batch B:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
  -> `263 passed, 1 warning`.
- Re-ran compile and diff hygiene:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
  and `git diff --check` both exited 0 with no output.
- Final verification remains pending because the matrix still contains real
  residual `PARTIAL` rows and explicit final-acceptance scope decisions.
- Added Phase 10 Batch C for the narrow CM-060 residual: reindex cancel should
  support durable `Idempotency-Key` ledger replay/conflict while preserving
  existing final-state idempotency.

## 2026-06-25 - Phase 10 Batch C Complete

- Used Spark worker `019efdeb-e7b5-78c0-b703-89c97471e23b` for read-only
  route/test inspection of reindex cancel idempotency.
- Added `tests/test_reindex.py::test_reindex_cancel_idempotency_key_replays_and_conflicts`.
- Added `Idempotency-Key` replay/conflict support to
  `POST /v1/maintenance/reindex/{job_id}/cancel` while preserving existing
  final-state cancel behavior for calls without an idempotency key.
- Verification:
  RED focused -> `1 failed, 12 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py -q -k "cancel and idempotency"`
  -> `1 passed, 12 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_reindex.py tests/test_contract.py tests/test_openapi.py -q`
  -> `49 passed, 1 warning`;
  full suite -> `264 passed, 1 warning`;
  compileall and `git diff --check` passed.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md`: CM-060 is now `COMPLIANT`;
  matrix row counts are `COMPLIANT=13`, `PARTIAL=51`, `MISSING=0`,
  `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1`.

## 2026-06-25 - Phase 10 Batch D Started

- Added Phase 10 Batch D for the narrow S24-80 residual: segment invalid enum
  rejection.
- Started Spark worker `019efdf2-0cd2-7ad2-98bf-abc5fccd921a` for read-only
  inspection of segment enum spec text, implementation, and test gaps.

## 2026-06-25 - Phase 10 Batch D Complete

- Spark inspection confirmed S24-80 covers event `importance` plus segment
  `created_by` enum validation, and also found adjacent segment status/outcome
  enum drift.
- Added `tests/test_segments.py::test_event_importance_and_segment_created_by_enums_validate`.
- Added event `importance` validation/defaulting, segment `created_by`
  validation/persistence, status-filter validation, spec-aligned close outcome
  values, and automatic segment `created_by="AUTOMATIC"`.
- Verification:
  RED focused -> `1 failed, 8 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "event_importance or enum"`
  -> `1 passed, 8 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py tests/test_contract.py -q`
  -> `45 passed, 1 warning`;
  full suite -> `265 passed, 1 warning`;
  compileall and `git diff --check` passed.

## 2026-06-25 - Phase 10 Batch E Started

- Added Phase 10 Batch E for the S24-105 memory-read summary/evidence-edge
  residual.
- Started Spark worker `019efdfa-9a11-76f0-ab83-f14d8b716879` for read-only
  inspection of the spec text, implementation, and current tests.

## 2026-06-25 - Phase 10 Batch E Complete

- Spark inspection found a real runtime gap: `/v1/tools/mneme_cost_report`
  returned cost data without a `MEMORY_READ` trace/audit/state feedback path.
- Strengthened `tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion`
  to assert S24-105 summary fields, redaction, first-sentence behavior, token
  cap, and `MEMORY_READ_EVIDENCE` weight.
- Added `tests/test_contract.py::test_mneme_cost_report_tool_creates_memory_read_audit_trace_and_updates_state`.
- Implemented `mneme_cost_report` memory-read audit/trace/state feedback by
  routing it through `audit_memory_tool`.
- Verification:
  RED focused -> `1 failed, 1 passed, 27 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "memory_read or mneme_cost_report"`
  -> `2 passed, 27 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py tests/test_graph.py -q`
  -> `59 passed, 1 warning`;
  full suite -> `266 passed, 1 warning`;
  compileall and `git diff --check` passed.

## 2026-06-25 - Phase 10 Batch F Started

- Added Phase 10 Batch F as an audit-first task for residual S24-100,
  S24-106, and S24-107 segmentation drift metadata/scoring/domain-shift
  coverage.
- Started Spark worker `019efe00-b311-73e0-afce-227d604eb597` for read-only
  inspection of the spec, implementation, tests, and whether the cluster is a
  bounded fix or real architectural blocker.

## 2026-06-25 - Phase 10 Batch F Complete

- Spark classified S24-100/106/107 as a real but bounded segment drift
  residual rather than a final blocker.
- Added `tests/test_segments.py::test_trusted_tool_domain_shift_contributes_to_segment_drift_score_trace`.
- Added config-driven drift threshold/weighted score handling to the intent
  classifier path, trusted ADAPTER-scoped tool-domain shift metadata, drift
  components/weights/threshold fields in `SEGMENT_DRIFT` traces, and
  `TOOL_DOMAIN_SHIFT` rollover reason.
- Verification:
  RED focused -> `1 failed, 9 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "tool_domain_shift or drift_score"`
  -> `1 passed, 9 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_session_drift.py tests/test_retrieval.py tests/test_contract.py tests/test_classifier.py -q`
  -> `59 passed, 1 warning`;
  full suite -> `267 passed, 1 warning`;
  compileall and `git diff --check` passed.

## 2026-06-25 - Phase 10 Batch G Started

- Added Phase 10 Batch G for the narrow S24-8 turn-complete final status
  residual.
- Started Spark worker `019efe0c-752a-72d1-bd31-5421763b8bd5` for read-only
  inspection of turn schema/status requirements and current tests.

## 2026-06-25 - Phase 10 Batch G Complete

- Spark confirmed S24-8 as a real `/v1/turns/complete` gap: final
  `FAILED`, `INTERRUPTED`, and `CANCELLED` statuses were not explicitly tested
  and the route returned the older `RECORDED` ack shape.
- Added `tests/test_contract.py::test_turn_complete_accepts_failed_interrupted_cancelled_and_rejects_conflicts`.
- Added `Store.get_turn` and minimal turn-complete status validation,
  compatible replay, incompatible conflict, and
  `mneme.turn_complete_result.v0` response shape.
- Updated Codex ingest contract expectation from old `RECORDED` ack to final
  `COMPLETED` turn result.
- Verification:
  RED focused -> `1 failed, 1 passed, 28 deselected, 1 warning`;
  GREEN focused
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete"`
  -> `2 passed, 28 deselected, 1 warning`;
  touched-area gate
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
  -> `38 passed, 1 warning`;
  Codex ingest compatibility gate -> `4 passed, 31 deselected, 1 warning`;
  full suite -> `268 passed, 1 warning`;
  compileall and `git diff --check` passed.
## 2026-06-25 - Phase 10 Batch H Started

- Added Phase 10 Batch H for the narrow S24-109/S24-119 execution-state
  residual cluster.
- Spark read-only audit confirmed this is not only matrix cleanup: tests need
  explicit canonical JSON byte hash evidence and trace needs an
  `EXECUTION_STATE_TRUNCATED` warning when state compression falls to
  `TRUNCATED`.

## 2026-06-25 - Phase 10 Batch H Complete

- Added `tests/test_state.py::test_state_history_hash_uses_canonical_json_bytes`
  to prove state-history hashes use canonical JSON bytes and maintain hash-chain
  evidence.
- Added
  `tests/test_context_assembly.py::test_context_prepare_trace_reports_truncated_execution_state_compression_level`
  and propagated `EXECUTION_STATE_TRUNCATED` into both the response trace
  summary and stored trace when execution-state context is truncated.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_context_assembly.py -q -k "canonical_json_bytes or compression_level"`
    -> RED `1 failed, 1 passed, 14 deselected, 1 warning`; GREEN `2 passed,
    14 deselected, 1 warning`.
  - Regression check:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_resume_fill.py::test_first_context_prepare_after_resume_forces_prior_context_once tests/test_state.py tests/test_context_assembly.py -q -k "first_context_prepare or canonical_json_bytes or compression_level"`
    -> `3 passed, 14 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_context_assembly.py tests/test_context_prepare.py tests/test_openapi.py -q`
    -> `39 passed, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `270 passed,
    1 warning`.

## 2026-06-25 - Phase 10 Batch I Started

- Added Phase 10 Batch I for the narrow S24-95/S24-96/S24-104
  indexing-compression residual cluster.
- Spark read-only audit found current implementation likely already covers raw
  tool-output preservation and embedding model-id filtering; remaining work is
  explicit test evidence for deterministic excerpt fallback and final
  model-isolation assertions.

## 2026-06-25 - Phase 10 Batch I Complete

- Added `tests/test_embeddings.py::test_embedding_search_isolated_to_active_model_id`
  to prove vector retrieval only uses rows from the active embedding model id.
- Added
  `tests/test_embeddings.py::test_deterministic_index_excerpt_is_stable_without_summary_provider`
  to prove provider-free excerpt fallback is stable and preserves deterministic
  head/tail/truncation-marker boundaries.
- No production source changes were required for Batch I.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py -q -k "active_model_id or deterministic_excerpt or compresses_tool_output"`
    -> `2 passed, 11 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_retrieval.py tests/test_contract.py -q`
    -> `51 passed, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `272 passed,
    1 warning`.

## 2026-06-25 - Phase 10 Batch J Started

- Added Phase 10 Batch J for the S24-26/S24-27/S24-29/S24-78
  session-discovery residual cluster.
- Spark read-only audit confirmed a real implementation gap: `resolve_session`
  and `list_sessions` currently use `limit` only, but spec requires
  `page_size`, `page_token`, `next_page_token`, and no silent truncation.
- Batch J will preserve `limit` as a compatibility alias while adding the
  canonical pagination contract and explicit scoped/redacted no-leak tests.

## 2026-06-25 - Phase 10 Batch J Complete

- Added stable session-discovery pagination with `page_size`, `page_token`,
  `next_page_token`, and `matches_truncated`, while preserving legacy `limit`.
- Added MCP forwarding for canonical pagination arguments without changing old
  request bodies when optional pagination fields are omitted.
- Added explicit tests for discovery pagination/no silent truncation and
  scoped/redacted not-found guidance.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py -q -k "session_discovery or resolve_session or list_sessions"`
    -> RED `1 failed, 5 passed, 51 deselected, 1 warning`; GREEN `6 passed,
    51 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py tests/test_openapi.py -q`
    -> `65 passed, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `274 passed,
    1 warning`.

## 2026-06-25 - Phase 10 Batch K Started

- Added Phase 10 Batch K for the S24-59/S24-84 readiness residual cluster.
- Spark read-only audit confirmed the exact remaining gap: readiness currently
  has session-only `require_evidence=false` coverage, but
  `require_evidence=true` may still call embedding providers for query
  vectorization without explicit `allow_provider_calls=true`.

## 2026-06-25 - Phase 10 Batch K Complete

- Readiness now uses local-only retrieval when `allow_provider_calls=false` and
  only passes embedding/reranker providers into readiness retrieval when
  `allow_provider_calls=true`.
- Readiness responses now expose `provider_calls_allowed` and
  `provider_calls_used` inside `checks`.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "readiness"`
    -> RED `3 failed, 1 passed, 30 deselected, 1 warning`; GREEN `4 passed,
    30 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py tests/test_reindex.py tests/test_openapi.py -q -k "readiness or provider or reindex or openapi"`
    -> `30 passed, 45 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `276 passed,
    1 warning`.

## 2026-06-25 - Phase 10 Batch L Started

- Added Phase 10 Batch L for the session export `include_audit` residual.
- Target behavior: JSON export returns `audit_records: []` by default and
  includes durable audit evidence only when the authorized caller explicitly
  requests `include_audit=true`.

## 2026-06-25 - Phase 10 Batch L Complete

- Added `tests/test_blobs.py::test_session_export_json_excludes_audit_by_default_and_includes_on_request`.
- Implemented the `include_audit` query parameter for JSON session export and
  made `Store.export_session(..., include_audit=False)` default to no audit
  records.
- Updated existing REST/MCP audit-evidence tests to request
  `include_audit=true` explicitly.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py -q -k "export or memory_tools_audit or cost_report"`
    -> RED `1 failed, 7 passed, 45 deselected, 1 warning`; GREEN `8 passed,
    45 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_blobs.py tests/test_contract.py tests/test_openapi.py -q -k "export or audit or openapi"`
    -> `17 passed, 44 deselected, 1 warning`.
  - MCP regression:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q -k "memory_tools_write_audit"`
    -> `1 passed, 24 deselected`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `277 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch M Started

- Added Phase 10 Batch M for S24-44 trace/cost typed schema evidence.
- Target behavior: existing trace and cost REST payloads keep their runtime
  shape, but OpenAPI advertises concrete v0 response schemas.

## 2026-06-25 - Phase 10 Batch M Complete

- Added `TraceResponse` and `CostReportResponse` OpenAPI response models and
  attached them to the existing trace/cost REST endpoints.
- Added `tests/test_openapi.py::test_openapi_documents_trace_and_cost_response_models`.
- Kept models compatibility-flexible after the touched-area gate exposed
  current trace/cost payloads that omit some future/canonical fields.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "trace or cost or core_v0"`
    -> RED `1 failed, 1 passed, 7 deselected, 1 warning`; GREEN `2 passed,
    7 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_mcp_contract.py -q -k "trace or cost or openapi or memory_tools_write_audit"`
    -> `14 passed, 54 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `278 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch N Started

- Added Phase 10 Batch N for S24-33 audit-disable daemon config behavior.
- Target behavior: default audit remains full, production config rejects
  `DISABLED_TEST_ONLY`, explicit test daemon config may disable durable memory
  audit evidence, and public request payload fields cannot bypass audit.

## 2026-06-25 - Phase 10 Batch N Complete

- Added `audit_mode` and `allow_unaudited_tools_for_tests` settings with
  validation that rejects production `DISABLED_TEST_ONLY`.
- Added memory-tool audit mode handling: `FULL` preserves trace/audit/event
  behavior, `TRACE_ONLY` suppresses canonical `MEMORY_READ` events while keeping
  trace/audit, and test-gated `DISABLED_TEST_ONLY` suppresses memory-tool audit
  evidence.
- Added config/contract tests proving daemon-only audit-disable behavior and
  ignored public per-call bypass fields.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py -q -k "audit_disabled or audit_mode or memory_tools_audit"`
    -> RED `2 failed, 1 passed, 53 deselected, 1 warning`; GREEN `3 passed,
    53 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_mcp_contract.py -q -k "audit or memory_read or memory_tools_write_audit"`
    -> `6 passed, 75 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `280 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch O Started

- Added Phase 10 Batch O for S24-38/S24-45 cost-report baseline methodology.
- Target behavior: cost reports clearly mark
  `provider_prompt_tokens_without_mneme_estimate` as counterfactual and include
  one of the allowed methodology labels.

## 2026-06-25 - Phase 10 Batch O Complete

- Added explicit cost-report `period`, `usage`, `provider_breakdown`, and
  `baseline` fields.
- Added contract assertions for period, usage, empty provider breakdown, and
  counterfactual no-savings baseline methodology in
  `tests/test_contract.py::test_turn_complete_cost_export_delete_and_restart_idempotency`.
- Updated `CostReportResponse` OpenAPI schema and the compliance matrix:
  CM-041 is now `COMPLIANT`; Section 24 row `38, 45` is now `COMPLIANT`;
  CM-020 and CM-062 remain `PARTIAL` for broader final-acceptance scope.
- Verification:
  - Focused RED/GREEN:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "cost_report or cost_export_delete or quality_cost_mode"`
    -> initial RED `2 failed, 33 deselected, 1 warning` for missing
    enrichment-token metric; GREEN `2 passed, 33 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_benchmarks.py tests/test_openapi.py -q -k "cost or benchmark or openapi"`
    -> `15 passed, 33 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `280 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch P Started

- Spark final-verification audit found the grouped Section 24 row
  `18, 19, 20, 21, 22, 55, 69, 70, 89, 99` is blocked only by S24-19
  traceability: implementation appears to cascade unused budget, but there is
  no dedicated contract test proving execution-state surplus flows to protected
  tail and then retrieved evidence.
- Batch P target behavior: add the narrow S24-19 regression proof and only
  adjust runtime trace fields if the existing response lacks enough evidence.

## 2026-06-25 - Phase 10 Batch P Complete

- Added `tests/test_context_prepare.py::test_context_prepare_cascades_unused_budget_to_tail_then_evidence`.
- The test proves S24-19 using trace budget fields: execution-state budget is
  underused, protected-tail budget receives the surplus, retrieved-evidence
  budget receives remaining tail surplus, and the evidence event is selected.
- Updated the compliance matrix:
  - Section 24 row `18, 19, 20, 21, 22, 55, 69, 70, 89, 99` is now
    `COMPLIANT`.
  - Spark-audited Section 24 row `2, 3, 48, 49, 91, 92` is now `COMPLIANT`.
  - CM-021, CM-047, CM-061, CM-062, and CM-063 now include Batch P evidence
    while remaining `PARTIAL` where their row-level scope is broader.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cascades_unused_budget or budget_split"`
    -> `3 passed, 13 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_retrieval.py -q -k "context_prepare or budget or freshness or wrapper"`
    -> `22 passed, 7 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `281 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch Q Started

- Spark storage/concurrency audit found the grouped Section 24 row
  `40, 41, 42, 56, 65, 71, 82, 113` still has multiple broad residuals.
- The narrowest executable residual is S24-113: the runtime has a
  `WriterQueueFull` to retryable `429 RATE_LIMITED` path, but no focused
  contract proof currently saturates the writer queue and asserts the public
  envelope.

## 2026-06-25 - Phase 10 Batch Q Complete

- Added `tests/test_contract.py::test_writer_queue_depth_limit_returns_retryable_429`.
- The test saturates the writer lane with `max_writer_queue_depth=1`, attempts
  a foreground `/v1/events` write, and asserts `429 RATE_LIMITED`,
  `retryable=true`, `reason=WRITER_QUEUE_FULL`, and
  `max_writer_queue_depth=1`.
- No runtime changes were needed; the existing `WriterQueueFull` handler already
  emitted the required public error envelope.
- Updated matrix evidence for CM-056, CM-059, CM-062, and grouped Section 24
  row `40, 41, 42, 56, 65, 71, 82, 113`.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "writer_queue_depth_limit"`
    -> `1 passed, 35 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_storage.py -q -k "writer_queue or storage_busy or schema_version"`
    -> `3 passed, 42 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `282 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch R Started

- Spark audits found Section 24 rows `25, 64` and `58` were still partial.
- S24-25 needed a direct scoped-token `GLOBAL` search test without an explicit
  project isolation header.
- S24-58 needed a direct batch-first streaming burst ingestion test proving
  bounded batch windows and oversized-batch rejection.

## 2026-06-25 - Phase 10 Batch R Complete

- Added `tests/test_retrieval.py::test_global_scope_respects_project_isolation_for_scoped_token_without_header`.
- Added `tests/test_contract.py::test_event_ingest_batch_first_handles_streaming_bursts`.
- No runtime changes were required. A transient S24-58 test failure was traced
  to `context_search` creating a memory-read audit event before final export,
  so the assertion now checks exact required event ids and absence of oversized
  ids instead of post-audit total export length.
- Updated the compliance matrix:
  - Section 24 row `25, 64` is now `COMPLIANT`.
  - Section 24 row `58` is now `COMPLIANT`.
  - CM-056 and CM-062 now include Batch R evidence while remaining `PARTIAL`
    where their row-level scope is broader.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_contract.py -q -k "global_scope_respects or streaming_bursts or batch_first"`
    -> `2 passed, 44 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_contract.py tests/test_codex_ingest.py -q -k "scope or batch or ingest or burst"`
    -> `15 passed, 36 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `284 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch S Started

- Section 24 row `43, 85` remained partial: OpenAPI was parseable and covered
  many typed components, but lacked machine-checked success/error examples and
  typed public core schemas for turn completion and context prepare.

## 2026-06-25 - Phase 10 Batch S Complete

- Added `TurnCompleteRequest`, `TurnCompleteResponse`,
  `ContextPrepareRequest`, and `ContextPrepareResponse` OpenAPI component
  schemas.
- Bound `/v1/turns/complete` and `/v1/context/prepare` to those schemas in
  generated OpenAPI without changing runtime payload parsing.
- Added examples for common success/error schemas and asserted route examples
  stay linked to public request components.
- Updated the compliance matrix:
  - Section 24 row `43, 85` is now `COMPLIANT`.
  - CM-027, CM-058, CM-061, CM-062, and CM-063 now include Batch S evidence
    while remaining `PARTIAL` where their row-level scope is broader.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q -k "examples or public_core_schemas or parseable"`
    -> `2 passed, 8 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_mcp_contract.py -q -k "openapi or schema or session_resolution or tool_envelope"`
    -> `13 passed, 22 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `285 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch T Started

- The grouped Section 24 row `46, 50, 67, 74, 86` remained partial.
- Startup automatic retention sweep was selected as the smallest implementation
  slice because explicit cleanup, session-close sweep, audit, metrics, and blob
  GC primitives already existed.

## 2026-06-25 - Phase 10 Batch T Complete

- Added `tests/test_contract.py::test_startup_retention_sweep_is_observable_and_scoped`.
- Added a `retention_sweep_on_startup` hook in `create_app()` that sweeps ended
  sessions only, skips active sessions, reuses existing retention/blob-GC
  primitives, and writes `SYSTEM_DAEMON` audit records with `trigger=STARTUP`.
- Updated the compliance matrix:
  - S24-67 now has startup and session-close sweep evidence.
  - Section 24 row `46, 50, 67, 74, 86` remains `PARTIAL` for periodic sweep
    timer and in-flight-read conflict tracking.
  - CM-035, CM-042, CM-061, and CM-062 now include Batch T evidence while
    remaining `PARTIAL` where their row-level scope is broader.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "startup_retention_sweep"`
    -> `1 passed, 37 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_storage.py tests/test_metrics.py -q -k "retention or sweep or metrics"`
    -> `9 passed, 40 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `286 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch U Started

- The grouped Section 24 row `46, 50, 67, 74, 86` remained partial after Batch
  T for in-flight read conflicts and periodic sweep coverage.
- S24-86 was selected as the next bounded slice because memory reads funnel
  through `audit_memory_tool()` and retention cleanup already has the forced
  active-session guard.

## 2026-06-25 - Phase 10 Batch U Complete

- Added `tests/test_contract.py::test_retention_cleanup_force_active_conflicts_with_in_flight_reads`.
- Added `InFlightReadTracker` to `app.state`/`store` and wrapped
  `audit_memory_tool()` persistence in the tracker.
- Forced active retention cleanup now returns `409 CONFLICT` with
  `details.reason=IN_FLIGHT_READS` and the current in-flight read count.
- Updated the compliance matrix:
  - S24-86 is now covered.
  - Section 24 row `46, 50, 67, 74, 86` remains `PARTIAL` only for periodic
    sweep coverage.
  - CM-035, CM-051, CM-059, CM-061, and CM-062 now include Batch U evidence
    while remaining `PARTIAL` where their row-level scope is broader.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "in_flight_reads or retention_cleanup"`
    -> `5 passed, 34 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_mcp_contract.py -q -k "retention or memory_read or in_flight"`
    -> `9 passed, 55 deselected, 1 warning`.
  - Full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` -> `287 passed,
    1 warning`.
  - Compile and diff hygiene:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    and `git diff --check` -> exit 0, no output.

## 2026-06-25 - Phase 10 Batch V Complete

- Audited Section 24 row `37, 39, 68, 75, 87, 111` and closed it as
  `COMPLIANT` based on existing evidence.
- Focused verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py tests/test_config.py tests/test_contract.py tests/test_reindex.py -q -k "minimal_mode or missing_key or require_evidence_false or provider_failure or provider_wait_timeout or reindex_cancel"`
  -> `9 passed, 69 deselected, 1 warning`.
- Updated the compliance matrix:
  - Section 24 row `37, 39, 68, 75, 87, 111` is now `COMPLIANT`.
  - CM-020, CM-061, and CM-062 now include Batch V evidence while remaining
    `PARTIAL` where their row-level scope is broader.
  - Real provider smoke remains release-gated when release notes claim live
    provider readiness; it is not a required public CI blocker for this grouped
    Section 24 row.

## 2026-06-25 - Phase 10 Batch W Complete

- Audited Section 24 row `46, 50, 67, 74, 86` and closed it as `COMPLIANT`.
- The canonical spec treats startup and session-close retention sweeps as
  mandatory automatic sweeps and the periodic timer as `SHOULD`.
- Batch T/U evidence covers mandatory automatic sweeps, active-session skip,
  owner force rules, and in-flight read conflicts.
- Updated the compliance matrix:
  - Section 24 row `46, 50, 67, 74, 86` is now `COMPLIANT`.
  - CM-035 and CM-042 now note periodic timer/CLI maintenance as broader
    operational hardening rather than a Section 24 blocker.

## 2026-06-25 - Phase 10 Batch X Complete

- Added `tests/test_contract.py::test_storage_busy_returns_retryable_503`.
- Audited the final Section 24 storage/concurrency grouped row
  `40, 41, 42, 56, 65, 71, 82, 113`.
- Updated the compliance matrix:
  - Section 24 row `40, 41, 42, 56, 65, 71, 82, 113` is now `COMPLIANT`.
  - `rg -n "\\| [0-9, ]+ \\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
    now returns no output.
  - CM-056 remains top-level `PARTIAL` for broader Section 18 backup/restore
    and destructive-migration controls, not for Section 24 storage/concurrency
    evidence.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "storage_busy or writer_queue"`
    -> `2 passed, 38 deselected, 1 warning`.
  - Touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_contract.py tests/test_reindex.py -q -k "schema or migration or integrity or busy or writer_queue or streaming_bursts or reindex_drain"`
    -> `10 passed, 52 deselected, 1 warning`.

## 2026-06-25 - Phase 10 Batch Y Complete

- Used Spark read-only audit plus parent review to normalize early top-level
  matrix rows `CM-002` through `CM-017`.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md`:
  - `CM-004`, `CM-007`, and `CM-015` are now `COMPLIANT`.
  - `CM-012` remains `PARTIAL`, but no longer claims Section 24 is partial;
    its remaining gap is final reviewer packet/full-suite acceptance evidence.
  - Matrix summary now reports `COMPLIANT: 18`, `PARTIAL: 46`,
    `OUT_OF_SCOPE/FUTURE: 1`.
- `git diff --check` passed after the matrix/planning update.

## 2026-06-25 - Phase 10 Batch Z Complete

- Used Spark read-only audit plus parent review to normalize top-level matrix
  rows `CM-019` through `CM-030`.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md`:
  - `CM-019`, `CM-020`, `CM-021`, `CM-022`, `CM-024`, `CM-026`, and `CM-027`
    are now `COMPLIANT`.
  - `CM-023`, `CM-025`, `CM-028`, `CM-029`, and `CM-030` remain `PARTIAL`
    as real residual schema/audit/graph/entity lifecycle gaps.
  - Matrix summary now reports `COMPLIANT: 25`, `PARTIAL: 39`,
    `OUT_OF_SCOPE/FUTURE: 1`.
- `git diff --check` passed after the matrix/planning update.

## 2026-06-25 - Phase 10 Batch AA Complete

- Used Spark read-only audit plus parent review to normalize top-level matrix
  rows `CM-033` through `CM-048`.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md`:
  - `CM-034`, `CM-035`, `CM-036`, `CM-038`, `CM-042`, `CM-047`, and `CM-048`
    are now `COMPLIANT`.
  - `CM-033`, `CM-037`, `CM-039`, `CM-040`, `CM-045`, and `CM-046` remain
    `PARTIAL` as real residual backup/restore, turn-derived-update,
    routing/entity lifecycle, segment lifecycle, context-search trace/refill,
    and graph-edge taxonomy gaps.
  - Matrix summary now reports `COMPLIANT: 32`, `PARTIAL: 32`,
    `OUT_OF_SCOPE/FUTURE: 1`.
- `git diff --check` passed after the matrix/planning update.

## 2026-06-25 - Phase 10 Batch AB Complete

- Used Spark read-only audit plus parent review to normalize final top-level
  matrix rows `CM-051` through `CM-065`.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md`:
  - `CM-051`, `CM-052`, `CM-054`, `CM-058`, `CM-059`, and `CM-062` are now
    `COMPLIANT`.
  - `CM-053`, `CM-055`, `CM-056`, `CM-057`, `CM-061`, `CM-063`, and `CM-065`
    remain `PARTIAL` as real residual hardening/final-acceptance gaps.
  - Matrix summary now reports `COMPLIANT: 38`, `PARTIAL: 26`,
    `OUT_OF_SCOPE/FUTURE: 1`.
- `31-top-level-matrix-audit-batch-ab` is complete; active parent task remains
  `04-final-verification-matrix`.

## 2026-06-25 - Phase 10 Batch AC Complete

- Added Batch AC planning node for narrow message/turn schema contract closure.
- RED/GREEN OpenAPI:
  - RED: `tests/test_openapi.py -q -k "core_route_request_and_response_models"`
    failed for missing `Message` schema.
  - GREEN: focused OpenAPI test passed after adding `Message`,
    `MessageContentPart`, and richer `TurnCompleteRequest` schemas.
- RED/GREEN runtime validation:
  - RED: `tests/test_context_prepare.py -q -k "invalid_message_role_and_part_type"`
    accepted invalid `ADMIN` role with `200`.
  - GREEN: invalid message role/content-part type now returns `422`.
- Touched-area verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py tests/test_context_prepare.py -q -k "openapi or turn_complete or context_prepare"`
  -> `30 passed, 37 deselected, 1 warning`.
- Full OpenAPI file verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
  -> `10 passed, 1 warning`.
- Compile and diff hygiene passed:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`;
  `git diff --check`.
- Matrix summary now reports `COMPLIANT: 39`, `PARTIAL: 25`,
  `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AD Complete

- Added Batch AD planning node for turn-completion segment linkage.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_links"`
    failed because `/v1/turns/complete` returned synthetic
    `segment-{session_id}` instead of the actual event-linked segment id.
  - GREEN: focused test passed after resolving segment ids from `event_ids` and
    merging last-turn metadata into the linked segment.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_segments.py tests/test_state.py -q -k "turn_complete or segment or state"`
    -> `27 passed, 35 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 39`, `PARTIAL: 25`,
  `OUT_OF_SCOPE/FUTURE: 1`; Batch AD narrows `CM-025` and `CM-037` but does not
  close either row.

## 2026-06-25 - Phase 10 Batch AE Complete

- Added Batch AE planning node for turn-completion execution-state/history
  updates.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_updates_execution_state"`
    failed because state still reflected the prior user event.
  - GREEN: focused test passed after turn completion wrote a PATCH state
    update with turn provenance.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_state.py -q -k "turn_complete or execution_state or goal_history"`
    -> `13 passed, 40 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 39`, `PARTIAL: 25`,
  `OUT_OF_SCOPE/FUTURE: 1`; Batch AE narrows `CM-025` and `CM-037` but does not
  close either row.

## 2026-06-25 - Phase 10 Batch AF Complete

- Added Batch AF planning node for turn-completion event/graph provenance.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_emits_event"`
    failed because export lacked a `TURN_COMPLETE` event and parent graph edge.
  - GREEN: focused test passed after `/v1/turns/complete` emitted an
    idempotent canonical `TURN_COMPLETE` event and parent-derived graph edges.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_graph.py -q -k "turn_complete or graph or edge"`
    -> `11 passed, 37 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 39`, `PARTIAL: 25`,
  `OUT_OF_SCOPE/FUTURE: 1`; Batch AF narrows `CM-025` and `CM-037` but does not
  close either row.

## 2026-06-25 - Phase 10 Batch AG Complete

- Added Batch AG planning node for the remaining turn-completion
  provider/usage residual.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "turn_complete_cost_export_delete_and_restart_idempotency"`
    failed because `provider_breakdown` stayed empty even when turn usage could
    include provider/model/cost metadata.
  - GREEN: focused test passed after `Store.cost_report()` aggregated provider
    breakdown entries from turn `usage`.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_metrics.py -q -k "turn_complete or cost or metrics or provider"`
    -> `12 passed, 33 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 41`, `PARTIAL: 23`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-025` and `CM-037` are `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AH Complete

- Added Batch AH planning node for `SEGMENT_ANCHOR` graph-edge residuals.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "direct_segment_start_close_list_get_and_events"`
    failed because session export lacked a `SEGMENT_ANCHOR` edge.
  - GREEN: focused test passed after `Store.put_segment()` inserted
    first-anchor-to-remaining-anchor `SEGMENT_ANCHOR` edges for direct segments.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_graph.py -q -k "segment or graph or anchor"`
    -> `15 passed, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 41`, `PARTIAL: 23`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029`, `CM-040`, and `CM-046` are narrowed but
  remain `PARTIAL`.

## 2026-06-25 - Phase 10 Batch AI Complete

- Added Batch AI planning node for direct segment `ABANDONED`/`SUPERSEDED`
  lifecycle semantics.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "event_importance_and_segment_created_by_enums_validate"`
    failed because an `ABANDONED` close returned public status `CLOSED`.
  - GREEN: focused test passed after direct segment close mapped `ABANDONED`
    and `SUPERSEDED` outcomes to matching terminal statuses and terminal
    statuses retained `closed_at`.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_openapi.py -q -k "segment or openapi"`
    -> `20 passed, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-040` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AJ Complete

- Added Batch AJ planning node for expand-context frontier/branching traversal
  residuals.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "branching_factor"`
    failed because graph expansion returned all root neighbors despite
    `graph_max_branching_factor=2`.
  - GREEN: focused test passed after `expand_graph()` enforced configured
    branching/frontier/visited-node limits.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"`
    -> `8 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029` and `CM-046` are narrowed but remain
  `PARTIAL`.

## 2026-06-25 - Phase 10 Batch AK Complete

- Added Batch AK planning node for graph-mode expand-context max-events
  truncation detail.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "traversal_limits_with_warning"`
    failed because `dropped_count` was missing from graph-mode response data.
  - GREEN: focused test passed after max-events truncation returned
    `RESULT_TRUNCATED`, `dropped_count`, and frontier summary details.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal"`
    -> `8 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-046` is narrowed but remains `PARTIAL`.

## 2026-06-25 - Phase 10 Batch AL Complete

- Added Batch AL planning node for a focused mode-specific expand-context
  traversal behavior.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "temporal_mode"`
    failed because non-`SEGMENT` modes still fell back to graph traversal and
    returned graph/segment-anchor neighbors rather than timestamp neighbors.
  - GREEN: focused test passed after `TEMPORAL` mode used explicit timestamp
    neighbor semantics with seed-first ordering.
- Verification:
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or temporal"`
    -> `9 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029` and `CM-046` are narrowed but remain
  `PARTIAL`.

## 2026-06-25 - Phase 10 Batch AM Complete

- Added Batch AM planning node for `TOOL_CHAIN`/`CAUSAL` graph traversal
  behavior after Spark read-only audit `019effb9-da16-7593-b1c0-65090a3ebd63`.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "tool_chain_mode or causal_mode"`
    failed because both modes used generic `(edge_type, event_id)` graph
    ordering.
  - GREEN: focused test passed after graph expansion received the request mode
    and applied mode-specific neighbor ordering/filtering.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py -q -k "tool_chain_mode or causal_mode"`
    -> `2 passed, 7 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal or tool_chain or causal"`
    -> `11 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029` and `CM-046` are narrowed but remain
  `PARTIAL` pending full edge taxonomy/edge-completeness coverage.

## 2026-06-25 - Phase 10 Batch AN Complete

- Added Batch AN planning node for canonical parent-child graph edge taxonomy.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "parent_child or turn_complete_emits_event"`
    failed because ordinary parent links exported `FOLLOWS` with weight `1.0`.
  - GREEN: focused test passed after explicit `parent_event_ids` generated
    `PARENT_CHILD` with weight `0.9`, and traversal allow-lists accepted the
    canonical edge type.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "parent_child or turn_complete_emits_event"`
    -> `2 passed, 51 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py -q -k "expand_context or graph or traversal or turn_complete_emits_event"`
    -> `12 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 42`, `PARTIAL: 22`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029` and `CM-046` are narrowed but remain
  `PARTIAL` pending explicit `TOOL_INPUT`/`SEGMENT_MEMBER` edge coverage.

## 2026-06-25 - Phase 10 Batch AO Complete

- Added Batch AO planning node for `CM-045` context-search candidate trace
  breadth and recency refill behavior after Spark read-only audit
  `019effbf-4c58-7f30-815d-7ecffcd2bc78`.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py -q -k "candidate_breadth or recency_refill"`
    failed because retrieval traces lacked source-count/candidate-id breadth and
    underfilled results were not refilled.
  - GREEN: focused test passed after retrieval traces gained additive breadth
    fields and underfilled searches gained explicit `RECENCY_REFILL` results,
    strategy, and warning.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py -q -k "candidate_breadth or recency_refill"`
    -> `2 passed, 9 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_context_prepare.py -q -k "context_search or freshness or refill"`
    -> `10 passed, 18 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 43`, `PARTIAL: 21`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-045` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AP Complete

- Added Batch AP planning node for remaining graph edge taxonomy coverage after
  Spark read-only audit `019effc6-8303-7543-b845-6a76c3f5c027`.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_segments.py -q -k "tool_input or segment_member"`
    failed because parent→`TOOL_CALL` still exported `PARENT_CHILD` and no
    automatic `SEGMENT_MEMBER` edge existed.
  - GREEN: focused test passed after parent message→`TOOL_CALL` generated
    derived `TOOL_INPUT`, and automatic segmentation wrote `SEGMENT_MEMBER`
    edges for subsequent segment member events.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_segments.py -q -k "tool_input or segment_member"`
    -> `2 passed, 20 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_graph.py tests/test_segments.py tests/test_contract.py -q -k "graph or segment or tool_input or segment_member"`
    -> `27 passed, 38 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 45`, `PARTIAL: 19`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-029` and `CM-046` are `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AQ Complete

- Added Batch AQ planning node for `CM-053` redaction provenance metadata after
  Spark read-only audit `019effcf-1502-7231-acaa-ce7021cb7796`.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "redaction_metadata or secret_profile"`
    failed because event ingest stored redacted values without
    `ingestion.redaction_metadata`.
  - GREEN: focused test passed after event foreground redaction recorded
    `{kind, field, hash}` metadata for changed fields and omitted metadata for
    clean events.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "redaction_metadata or secret_profile"`
    -> `2 passed, 42 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py -q -k "redaction or secret or bytes_ref"`
    -> `10 passed, 55 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 45`, `PARTIAL: 19`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-053` is narrowed but remains `PARTIAL` pending
  explicit extractor-policy behavior for non-text blobs.

## 2026-06-25 - Phase 10 Batch AR Complete

- Added Batch AR planning node for explicit non-text blob extractor policy.
- RED/GREEN:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py -q -k "extractor_policy or binary_metadata_only"`
    failed because non-text BYTES_REF ingest did not record extractor policy and
    invalid extractor policy config was accepted.
  - GREEN: focused test passed after adding `binary_blob_extractor_policy`
    default/validation/loading/capabilities exposure and binary BYTES_REF
    ingestion metadata.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py -q -k "extractor_policy or binary_metadata_only"`
    -> `2 passed, 64 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_config.py tests/test_blobs.py -q -k "redaction or bytes_ref or extractor_policy or binary"`
    -> `9 passed, 76 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 46`, `PARTIAL: 18`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-053` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AS/AT Complete

- Added Batch AS planning node for `CM-009` context-prepare cost-mode parity
  and Batch AT planning node for readiness evidence semantics.
- RED/GREEN:
  - AS RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cost_mode"`
    failed because non-strict `QUALITY` lacked structured downgrade details and
    strict `QUALITY` returned `200` instead of `503 PROVIDER_UNAVAILABLE`.
  - AS GREEN: focused cost-mode test passed after context prepare used
    `cost_mode_warnings_or_error()` and propagated warnings through early
    responses.
  - AT RED: touched readiness gate exposed
    `test_readiness_provider_calls_require_explicit_opt_in` accepting a
    query-unrelated `RECENCY_REFILL` hit as evidence.
  - AT GREEN: readiness disables recency refill for query checks; explicit
    context-search recency refill remains enabled.
- Verification:
  - Focused AS:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py -q -k "cost_mode"`
    -> `3 passed, 16 deselected, 1 warning`.
  - Focused AT:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_readiness_provider_calls_require_explicit_opt_in tests/test_retrieval.py::test_context_search_recency_refills_underfilled_results -q`
    -> `2 passed, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_contract.py -q -k "cost_mode or context_prepare or readiness"`
    -> `24 passed, 39 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 46`, `PARTIAL: 18`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-009` is narrowed but remains `PARTIAL`
  pending provider `last_health` runtime status evidence.
- Spark audit `019effdf-0bb8-7643-92e4-277edd948cc7` completed read-only:
  next recommended narrow residual is `CM-028` audit/forensic retention
  lifecycle enforcement.

## 2026-06-25 - Phase 10 Batch AU Complete

- Added Batch AU planning node for `CM-028` forensic audit-anchor retention.
- RED/GREEN:
  - RED: focused AU test failed because `Store` had no
    `purge_forensic_anchors_older_than()` primitive.
  - RED: startup test failed because restarting Mneme did not purge expired
    forensic anchors.
  - GREEN: storage primitive deletes only forensic-anchor audit rows older than
    the retention cutoff, and `create_app()` runs it on startup using
    `settings.audit_forensic_retention_days`.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_forensic_audit_anchors_expire_after_retention_days tests/test_contract.py::test_startup_purges_expired_forensic_audit_anchors -q`
    -> `2 passed, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py -q -k "audit or forensic or retention"`
    -> `13 passed, 33 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 47`, `PARTIAL: 17`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-028` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AV Complete

- Added Batch AV planning node for `CM-009` provider runtime health snapshots,
  incorporating Spark audit `019effea-57fc-78b1-a917-1b5d2edebbb9`.
- RED/GREEN:
  - RED: provider-summary focused tests failed because `ProviderHealth` did not
    exist.
  - RED: capabilities runtime-failure test failed because `last_health` was a
    static string.
  - GREEN: provider summaries accept structured health snapshots, and
    `create_app()` wraps available embedding/reranker/enrichment providers with
    process-local observed-outcome health tracking.
- Verification:
  - Focused provider summary:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "provider_summary"`
    -> `2 passed, 21 deselected, 1 warning`.
  - Focused capabilities runtime failure:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_capabilities_shows_provider_last_health_after_embedding_failure_degradation -q`
    -> `1 passed, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_context_prepare.py tests/test_contract.py -q -k "provider_summary or capabilities_shows_provider_last_health or readiness_provider_calls_require_explicit_opt_in or cost_mode or capabilities"`
    -> `9 passed, 80 deselected, 1 warning`.
  - OpenAPI:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
    -> `10 passed, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 48`, `PARTIAL: 16`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-009` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch AW Complete

- Added Batch AW planning node for `CM-017` writer-lane config parity,
  incorporating Spark audit `019efff1-5053-7371-9d83-70a34e2a9e9b`.
- RED/GREEN:
  - RED: focused config test failed because `mneme serve` did not recognize
    `--max-writer-queue-depth`.
  - GREEN: added `MNEME_MAX_WRITER_QUEUE_DEPTH` env loading and
    `--max-writer-queue-depth` serve CLI mapping.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "writer_queue_depth or serve_cli_accepts_core_parity_knobs"`
    -> `2 passed, 22 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q`
    -> `24 passed, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 48`, `PARTIAL: 16`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-017` is narrowed but remains `PARTIAL` pending
  other later-phase config parity/runtime enforcement residuals.

## 2026-06-25 - Phase 10 Batch AX Complete

- Added Batch AX implementation for SQLite backup/restore verification,
  incorporating Spark audit `019efff5-c931-7681-a0c2-0ff7a0797050` and
  read-only risk review `019f002a-8299-7a60-8209-34df1632d72a`.
- RED/GREEN:
  - RED: focused storage/config backup tests failed because `Store.backup_to`,
    `Store.restore_from_backup`, and CLI `maintenance` commands were missing.
  - GREEN: `Store.backup_to()` uses SQLite backup API and validates schema,
    migrations, integrity, and blob hashes; `Store.restore_from_backup()`
    verifies the source and restored target and cleans up failed partial
    restores; CLI exposes `mneme maintenance backup|restore`.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q -k "backup or restore"`
    -> RED before implementation `3 failed, 33 deselected, 1 warning`; GREEN
    after implementation `3 passed, 33 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py -q`
    -> `36 passed, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 48`, `PARTIAL: 16`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-033` and `CM-056` are narrowed but remain
  `PARTIAL` pending broader operational/destructive-migration/final-disposition
  evidence.

## 2026-06-25 - Phase 10 Batch AY Complete

- Added Batch AY implementation for `CM-055` owner-only SQLite file/data-dir
  permission policy, incorporating Spark audit
  `019f002f-03fc-7fb2-9953-c5d38c780c62`.
- RED/GREEN:
  - RED: focused storage permission test failed because existing DB files could
    remain group/world-readable after `Store` initialization.
  - GREEN: `Store` now enforces POSIX owner-only modes for the SQLite DB parent
    directory (`0700`) and DB file (`0600`) after initialization.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py -q -k "permission or schema_version"`
    -> RED before implementation `1 failed, 2 passed, 9 deselected`; GREEN
    after implementation `3 passed, 9 deselected`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_storage.py tests/test_config.py tests/test_codex_adapter.py -q -k "permission or runtime_files or schema_version"`
    -> `6 passed, 44 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 48`, `PARTIAL: 16`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-055` is narrowed but remains `PARTIAL` pending
  optional encryption/OS-encrypted-volume documentation and broader
  derivative-retention/final-disposition evidence.

## 2026-06-25 - Phase 10 Batch AZ Complete

- Added Batch AZ regression/documentation coverage for the remaining `CM-055`
  at-rest residuals.
- RED/GREEN:
  - RED: focused AZ gate initially failed because `docs/INSTALLATION.md` did
    not include the required `0600`/`0700` and encryption-boundary guidance.
  - GREEN: installation docs now cover database/default blob path, owner-only
    modes, OS-encrypted volume/SQLCipher strategy, and no
    enterprise-confidentiality claim; retention cleanup test now asserts linked
    derived records are removed.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_retention_cleanup_deletes_eligible_events_and_orphan_blobs tests/test_codex_adapter.py::test_installation_docs_describe_at_rest_storage_guidance -q`
    -> RED before docs update `1 failed, 1 passed, 1 warning`; GREEN after
    docs update `2 passed, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_codex_adapter.py -q -k "retention_cleanup_deletes_eligible_events_and_orphan_blobs or at_rest or runtime_files"`
    -> `3 passed, 58 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 49`, `PARTIAL: 15`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-055` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch BA Complete

- Added Batch BA CLI blob-GC trigger for the `CM-033`/`CM-057` maintenance
  residual, incorporating Spark audit `019f003a-aea8-71d2-9336-673c4f81f535`.
- RED/GREEN:
  - RED: focused config test failed because `mneme maintenance` accepted only
    `backup` and `restore`, not `blob-gc`.
  - GREEN: `mneme maintenance blob-gc` now parses `--db`,
    `--project-isolation-key`, `--session-id`, dry-run default, and `--execute`,
    then calls `Store.garbage_collect_blobs()`.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q -k "blob_gc or backup_restore"`
    -> RED before implementation `1 failed, 1 passed, 24 deselected, 1 warning`;
    GREEN after implementation `2 passed, 24 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_blobs.py -q -k "blob_gc or backup_restore or maintenance_blob_gc"`
    -> `4 passed, 41 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 49`, `PARTIAL: 15`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-033`/`CM-057` are narrowed but remain
  `PARTIAL`.

## 2026-06-25 - Phase 10 Batch BB Complete

- Added Batch BB operations runbook documentation for `CM-057`.
- RED/GREEN:
  - RED: focused docs test failed because installation/testing docs did not
    describe operations runbook stop/restart and in-flight behavior.
  - GREEN: docs now cover config-change restart, in-flight interruption,
    `retryable=true`, `Idempotency-Key`, and structured-log fields.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q -k "operations_runbook or at_rest"`
    -> RED before docs update `1 failed, 1 passed, 13 deselected`; GREEN after
    docs update `2 passed, 13 deselected`.
  - Touched docs:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`
    -> `15 passed`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix counts remain `COMPLIANT: 49`, `PARTIAL: 15`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-057` is narrowed but remains `PARTIAL` pending
  structured logging breadth and final release/reviewer runbook evidence.

## 2026-06-25 - Phase 10 Batch BC Complete

- Added Batch BC structured HTTP access logging for `CM-057`.
- RED/GREEN:
  - RED: focused metrics test failed because no `mneme_service.access`
    structured log records were emitted.
  - GREEN: HTTP middleware now emits safe JSON records with request id,
    optional trace id, endpoint, status/error code, safe scope metadata,
    latency, and background job id without bearer tokens or body content.
- Verification:
  - Focused:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py -q -k "structured_access_log"`
    -> RED before implementation `1 failed, 2 deselected, 1 warning`; GREEN
    after implementation `1 passed, 2 deselected, 1 warning`.
  - Touched-area:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_metrics.py tests/test_contract.py -q -k "structured_access_log or metrics_and_reindex"`
    -> `2 passed, 48 deselected, 1 warning`.
  - Compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 50`, `PARTIAL: 14`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-057` is `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch BD Complete

- Added Batch BD matrix normalization for stale `CM-033` blob lifecycle
  residual.
- Verification:
  - Matrix audit:
    `rg -n "\\| CM-033 .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
    -> no matches.
  - Diff hygiene: `git diff --check` -> exit 0.
- Matrix summary now reports `COMPLIANT: 51`, `PARTIAL: 13`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-033` is `COMPLIANT`.
## 2026-06-25 - Phase 10 Batch BE destructive-migration backup controls

- Added focused `CM-056` coverage for destructive migrations requiring either a verified `--backup-before-migrate` path or explicit `--no-backup-before-migrate` operator bypass.
- Implemented storage startup guard, legacy backup verification support, config/env/serve CLI knobs, and app wiring into `Store`.
- Added installation release-note guidance for migration impacts and tested Python versions.
- Verification: focused RED before implementation `3 failed, 38 deselected, 1 warning`; focused GREEN `3 passed, 38 deselected, 1 warning`; storage/config touched gate `41 passed, 1 warning`; migration docs gate `3 passed, 13 deselected`; compileall exit 0; `git diff --check` exit 0; `CM-056` PARTIAL audit no matches.
- Updated compliance matrix to `COMPLIANT: 52`, `PARTIAL: 12`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-056` is now `COMPLIANT`.
## 2026-06-25 - Phase 10 Batch BF existing-settings config parity

- Delegated narrow `CM-017` implementation to Spark, limited to `mneme_service/config.py`, `mneme_service/cli.py`, and `tests/test_config.py`.
- Added env and `mneme serve` CLI parity for existing later-phase maintenance, reindex, metrics, daemon limit, redaction, and audit settings.
- Verification: focused config parity gate `2 passed, 27 deselected, 1 warning`; full `tests/test_config.py` gate `29 passed, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated compliance matrix without changing counts: `CM-017` remains `PARTIAL`, but the remaining gap is now routing/provider-policy config modeling and additional runtime validation, not existing-field env/CLI parity.
## 2026-06-25 - Phase 10 Batch BG integration-depth capability claims

- Added machine-readable `integration_depth` capability response/OpenAPI schema with the full Section 5 level taxonomy: `TOOLS_ONLY`, `EVENT_INGEST`, `PREPARE_INPUT`, `CONTEXT_ENGINE`, `COMPACTION_OWNER`, `FULL_RUNTIME`.
- Declared core REST lifecycle API as `EVENT_INGEST`, while keeping MCP and Codex hook/preview surfaces from overclaiming deeper host integration.
- Verification: focused depth gate RED before implementation `3 failed, 1 warning`; focused GREEN `3 passed, 1 warning`; touched integration-depth gate `9 passed, 87 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated compliance matrix to `COMPLIANT: 53`, `PARTIAL: 11`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-013` is now `COMPLIANT`, `CM-014` remains `PARTIAL`.
## 2026-06-25 - Phase 10 Batch BH deterministic entity-modifier lifecycle

- Added deterministic `mneme.entity_modifier.v0` state lifecycle: USER_MESSAGE ingest applies ADD/REPLACE/REMOVE modifiers to `execution_state.active_entities` and records provenance in `execution_state.enrichment.entity_modifiers`.
- Kept provider-backed extraction/reconciliation out of scope for this batch.
- Verification: focused RED before implementation `2 failed, 11 deselected, 1 warning`; focused GREEN `2 passed, 11 deselected, 1 warning`; touched state/classifier gate `22 passed, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated matrix row `CM-030` with deterministic lifecycle evidence; global counts remain `COMPLIANT: 53`, `PARTIAL: 11`, `OUT_OF_SCOPE/FUTURE: 1`.
## 2026-06-25 - Phase 10 Batch BI Codex Stop turn lifecycle

- Added Codex hook import turn completion for `Stop` payloads with `turn_id`; imports now call `/v1/sessions/start`, `/v1/events`, and `/v1/turns/complete`.
- Updated integration-depth capabilities so Codex hooks can honestly declare `EVENT_INGEST` while still not claiming `PREPARE_INPUT`/`CONTEXT_ENGINE`.
- Verification: focused RED before implementation `4 failed, 1 warning`; focused GREEN `4 passed, 1 warning`; touched Codex lifecycle gate `32 passed, 48 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated compliance matrix to `COMPLIANT: 54`, `PARTIAL: 10`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-014` is now `COMPLIANT`.
## 2026-06-26 - Phase 10 Batch BJ topic entropy narrowing

- Delegated the narrow `CM-039` topic-entropy slice to Spark and reviewed the resulting two-file change.
- Added deterministic normalized lexical `topic_entropy` for USER_MESSAGE segment drift scoring and trace evidence.
- Verification: focused gate `1 passed, 10 deselected, 1 warning`; touched-area gate `12 passed, 19 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated `CM-039` evidence while keeping global counts unchanged: `COMPLIANT: 54`, `PARTIAL: 10`, `OUT_OF_SCOPE/FUTURE: 1`.
## 2026-06-26 - Phase 10 Batch BK structured-history matrix normalization

- Delegated read-only `CM-005` audit to Spark and reviewed the implementation/test/spec evidence.
- Classified the remaining `CM-005` residual as stale matrix text rather than a code gap.
- Updated `CM-005` to `COMPLIANT` with structured-history evidence across storage schema, audit, retention, migration/versioning, backup/restore, and maintenance metrics.
- Verification: matrix-only update; `git diff --check` exit 0.
- Matrix summary now reports `COMPLIANT: 55`, `PARTIAL: 9`, `OUT_OF_SCOPE/FUTURE: 1`.
## 2026-06-26 - Phase 10 Batch BM core/adapter release boundary

- Delegated the narrow `CM-003` README/test change to Spark and reviewed the resulting docs/test diff.
- Core README no longer presents Codex adapter doc links or command surface as core release docs, while preserving explicit separate core/adapter repository guidance.
- Verification: focused docs gate `3 passed, 14 deselected`; full `tests/test_codex_adapter.py` gate `17 passed`; compileall for the touched test file exit 0; `git diff --check` exit 0.
- Matrix summary now reports `COMPLIANT: 56`, `PARTIAL: 8`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-003` is now `COMPLIANT`.
## 2026-06-26 - Phase 10 Batch BO routing config parity

- Delegated the narrow `CM-017`/`CM-039` routing-config implementation to Spark, then reviewed and tightened the merge semantics in parent.
- Added first-class routing default mode and mode-weight settings, TOML/env/serve CLI coverage, validation, example config, and runtime propagation into context-search trace/score breakdowns.
- Verification: focused gate `3 passed, 42 deselected, 1 warning`; touched routing gate `6 passed, 58 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated compliance matrix to `COMPLIANT: 58`, `PARTIAL: 6`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-017` and `CM-039` are now `COMPLIANT`.
## 2026-06-26 - Phase 10 Batch BP deterministic delta extraction capabilities

- Added `delta_extraction` to `/v1/capabilities` and the typed capabilities schema.
- Capabilities now advertise deterministic `mneme.entity_modifier.v0` support, active-entity-only automatic update scope, conflict order, and provider-guarded extraction disabled policy.
- Verification: focused capability gate `2 passed, 1 warning`; touched capability/entity gate `9 passed, 70 deselected, 1 warning`; compileall exit 0; `git diff --check` exit 0.
- Updated compliance matrix to `COMPLIANT: 59`, `PARTIAL: 5`, `OUT_OF_SCOPE/FUTURE: 1`; `CM-030` is now `COMPLIANT`.

## 2026-06-26 - Phase 10 Batch BQ/BR final acceptance closure

- Created `docs/MNEME_V0_REVIEWER_PACKET.md` as the Mneme v0 reviewer-facing handoff.
- Final verification initially found two stale exact contract assertions after later trace improvements:
  `tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces`
  and `tests/test_parity_recovery.py::test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak`.
- Batch BR root cause: runtime behavior was richer and spec-consistent. `fetch_event(include_neighbors=true)` traces now include the actual returned neighbor evidence, including turn-complete provenance nodes when present; provider retrieval traces now include `GRAPH_DEPENDENCY` before `RERANK` when graph evidence participates.
- Verification:
  - Batch BR focused gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces tests/test_parity_recovery.py::test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak -q`
    -> `2 passed, 1 warning`.
  - Batch BR touched-area gate:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_parity_recovery.py tests/test_graph.py tests/test_retrieval.py -q -k "memory_tools_write_audit_records_and_traces or provider_pipeline_recovers or context_search_includes_graph_dependencies or trace_reports_router_mode or degraded_trace"`
    -> `5 passed, 48 deselected, 1 warning`.
  - Final full suite:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
    -> `332 passed, 1 warning in 21.52s`.
  - Final compile:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    -> exit 0.
  - Final OpenAPI:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`
    -> `10 passed, 1 warning in 1.79s`.
  - Final diff hygiene: `git diff --check` -> exit 0.
- Updated `docs/MNEME_V0_COMPLIANCE_MATRIX.md` to final counts:
  `COMPLIANT: 64`, `PARTIAL: 0`, `MISSING: 0`, `OUT_OF_SCOPE/FUTURE: 1`.
- Marked Phase 10 and the top-level roadmap complete. Commit/push/release publication and external owner sign-off remain separate explicit actions.
