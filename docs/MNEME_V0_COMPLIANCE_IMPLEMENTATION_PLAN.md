# Mneme v0 Compliance Implementation Plan

Status: approved implementation plan
Date: 2026-06-21
Target spec: `docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5
Approval gate: passed on 2026-06-21; begin Phase 0 with the compliance matrix
and baseline test run.

## 1. Objective

Bring the current alpha Mneme core implementation into compliance with the
approved Mneme v0 standalone specification.

The target is not "add a few missing endpoints"; the target is a verifiable
contract match: REST, MCP, storage, context preparation, security behavior,
observability, OpenAPI, and required tests should all agree with the standalone
spec before the code is sent for external review.

## 2. Success Criteria

- All MUST requirements in `docs/MNEME_STANDALONE_SPEC.md` are either
  implemented or explicitly tracked as a remaining compliance gap with owner,
  severity, and release decision.
- `/openapi.json` documents every public REST endpoint, schema, auth behavior,
  and error envelope required by the spec.
- Required contract tests from Section 24 of the spec are implemented or mapped
  to equivalent composite tests.
- Hermes-parity retrieval intelligence is covered: deterministic intent
  classification, automatic segmentation, selective indexing compression,
  routing modes, explicit scoring formula, optional deterministic delta
  extraction, and memory-tool feedback continuity.
- Algorithmic hardening is covered: canonical state hashes, bounded graph
  traversal, bounded writer queues, provider-free fast readiness, bounded
  redaction latency, and multipart rollback tests.
- Final integration polish is covered: `REDACTION_TIMEOUT` adapter recovery
  guidance, provider-enabled readiness rate-limit behavior, and ordered state
  arrays for canonical hashing.
- Full local verification passes:
  `.venv/bin/python -m pytest -q`
  `.venv/bin/python -m compileall -q mneme_service tests`
  `git diff --check`
- Code review packet contains the standalone spec, this plan, test evidence,
  and a compliance matrix.

## 3. Non-Goals

- No MCP model-callable write tools in v0.
- No hosted/cloud Mneme.
- No enterprise RBAC or collaborative multi-user workspaces.
- No `COMPACTION_OWNER` implementation until a compaction API is specified.
- No RLM Orchestrator implementation in this repository.
- No hidden direct SQLite access by external clients; REST remains canonical.

## 4. Implementation Principles

- Use tests first for each behavioral slice.
- Keep changes vertical and reviewable: schema + storage + endpoint + tests
  should land together for one capability.
- Preserve current working behavior unless the v0 spec explicitly changes it.
- Prefer small, deterministic local algorithms over provider-dependent behavior
  in contract tests.
- Treat OpenAPI as implementation truth for REST clients, not as afterthought
  documentation.
- Keep Codex adapter code development-only unless release packaging explicitly
  excludes or moves it.

## 5. Phase Plan

### Phase 0: Compliance Baseline

**Description:** Freeze the target contract and map the current alpha code
against it before changing behavior.

**Tasks:**

- [x] Create `docs/MNEME_V0_COMPLIANCE_MATRIX.md` with every required endpoint,
  schema, test, and known gap.
- [x] Run the current full test suite and record results in `progress.md`.
- [x] Record current public endpoints and MCP tools from `mneme_service/app.py`
  and `mneme_service/mcp_server.py`.

**Verification:**

- [x] Compliance matrix links every Section 24 test number to an existing,
  planned, or intentionally deferred test file.
- [x] Baseline command output is recorded.

**Likely files:**

- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `progress.md`
- `findings.md`

### Phase 1: Contract, Config, And OpenAPI Foundation

**Description:** Make the implementation speak the same contract language as
the spec before deeper features are built on top.

**Tasks:**

- [ ] Add explicit schema/model definitions for all v0 public request/response
  shapes, including retention cleanup, trace, cost report, state history,
  session lineage, blob, segment, and reindex job.
- [ ] Expand config parsing and validation for v0.7.5 limits, retention,
  metrics, provider retry/backoff, circuit breaker, graph scoring/traversal
  limits, writer queue depth, redaction timeout, multipart transaction time,
  and idempotency-key retention.
- [ ] Update `/v1/capabilities` to advertise supported schema versions,
  metrics format, limits, export formats, provider status, and MCP tool
  versions.
- [ ] Ensure all REST errors use the uniform `{ok:false,error:{...},warnings:[]}`
  envelope, including auth failures.
- [ ] Generate or validate `/openapi.json` against the public schemas.

**Verification:**

- [ ] `tests/test_config.py` covers invalid config invariants.
- [ ] `tests/test_contract.py` covers capabilities and uniform errors.
- [ ] `tests/test_openapi.py` or equivalent validates `/openapi.json`.

**Likely files:**

- `mneme_service/config.py`
- `mneme_service/app.py`
- `mneme_service/errors.py`
- `tests/test_config.py`
- `tests/test_contract.py`

### Phase 2: Storage, Migrations, And Writer Lane

**Description:** Build the durable substrate required by all later phases.

**Tasks:**

- [ ] Add a migration framework with startup schema version checks,
  `PRAGMA user_version`, and migration history.
- [ ] Add tables/indexes for blobs, idempotency records, richer audit records,
  traces, costs, reindex jobs, retention state, and forensic anchors.
- [ ] Implement startup integrity check with fail-closed or read-only recovery.
- [ ] Introduce serialized SQLite writer-lane behavior with foreground priority
  over background jobs.
- [ ] Enforce `max_writer_queue_depth` with retryable `429 RATE_LIMITED` and
  keep background writes from filling foreground capacity.
- [ ] Add bounded busy/retry behavior and concurrency tests.

**Verification:**

- [ ] Migration tests cover fresh database, known older schema, and unknown
  newer schema.
- [ ] Writer concurrency tests prove foreground ingestion/state updates are not
  starved by background jobs and bounded queue overflow returns retryable 429.

**Likely files:**

- `mneme_service/storage.py`
- `mneme_service/app.py`
- `tests/test_storage.py`
- `tests/test_contract.py`

### Phase 3: Blob And Export Compliance

**Description:** Complete the `BYTES_REF` protocol and make export/delete safe.

**Tasks:**

- [ ] Implement `POST /v1/blobs`, blob metadata, content reads, single-range
  reads, scoped delete, and blob GC.
- [ ] Implement multipart event ingest with `multipart://...` placeholder
  rewrite, request-level limits, digest/idempotency behavior, and atomic
  metadata semantics.
- [ ] Ensure multipart blob persistence failures roll back all events, blob
  metadata, and searchable derivatives from the request.
- [ ] Implement JSON metadata-only session export and streaming
  `application/x-tar` `tar_bundle` export with `manifest.json`.
- [ ] Reject unsupported export formats with `422 VALIDATION_ERROR`.
- [ ] Ensure privacy delete removes blobs/search derivatives while preserving
  anonymized forensic audit anchors.

**Verification:**

- [ ] Blob tests cover upload, metadata, content range, delete, GC, and 413
  error envelopes.
- [ ] Multipart tests prove any blob failure rolls back all events/blob metadata
  from the request.
- [ ] Export tests cover JSON metadata-only, tar bundle manifest/blob entries,
  unknown format, and scope enforcement.

**Likely files:**

- `mneme_service/storage.py`
- `mneme_service/app.py`
- `mneme_service/security.py`
- `tests/test_blobs.py`
- `tests/test_contract.py`

### Phase 4: Session Lifecycle, Readiness, Retention, And Audit

**Description:** Make lifecycle endpoints deterministic and safe under auth,
scope, and active-session conditions.

**Tasks:**

- [ ] Enforce `session_id` validation and stable generated-id behavior with
  `Idempotency-Key`.
- [ ] Finalize authenticated `/v1/readiness/session` with distinct 401, 404,
  412 `NO_EVIDENCE`/`INDEX_UNAVAILABLE`, and 200 outcomes; ensure
  `require_evidence=false` makes no provider calls and evidence readiness uses
  local persisted indexes unless explicitly allowed.
- [ ] Implement `POST /v1/sessions/{session_id}/retention/cleanup` request and
  response schema, active-session skip, force cleanup owner-only behavior, and
  in-flight read conflict.
- [ ] Implement forensic audit anchors with per-record salt and optional
  external pepper support.
- [ ] Add `AUTH_FAILURE`, `RETENTION_CLEANUP`, and system maintenance audit
  records with stable `tool` semantics and `UNAUTHENTICATED` principal for
  pre-token failures.

**Verification:**

- [ ] Readiness tests distinguish auth, session, no-evidence/index-unavailable,
  success, and provider-free `require_evidence=false`.
- [ ] Retention tests cover cutoff, visible scope, active skip, force conflict,
  and response counts.
- [ ] Audit tests cover auth failures and anonymized anchors after delete.

**Likely files:**

- `mneme_service/app.py`
- `mneme_service/storage.py`
- `mneme_service/security.py`
- `tests/test_contract.py`
- `tests/test_security.py`

### Phase 5: State, Segments, Lineage, Graph, And Routing Intelligence

**Description:** Align higher-level memory structure with the v0 data model.

**Tasks:**

- [ ] Complete execution-state update/result/history schemas, RFC 8785/JCS
  canonical state hashing, and provenance requirements.
- [ ] Implement deterministic intent classification with the v0.7.5 priority
  chain, default switch patterns, entity contradiction terms, and trace
  classifier signals.
- [ ] Implement optional `mneme.entity_modifier.v0` delta extraction with
  deterministic modifier rules, conflict ordering, and active-entity-only
  automatic state updates.
- [ ] Complete direct segment start/close/list/get endpoints, segment event
  summaries, generated segment ids with idempotency, and stable enums.
- [ ] Implement automatic segmentation rollover for explicit switches,
  embedding distance, combined drift score, topic-entropy fallback behavior,
  trusted tool-domain shift signals, centroid rules, and redacted
  `SEGMENT_DRIFT` traces.
- [ ] Complete session lineage schema, cycle prevention, scope enforcement, and
  lineage-aware retrieval/fetch behavior.
- [ ] Make graph traversal scoring normative with bounded importance boost,
  deterministic tie-breaking, max traversal steps, max frontier size, branching
  factor, and tests for depth decay/limit warnings.
- [ ] Ensure direct memory-read feedback updates bounded state summaries and
  `MEMORY_READ_EVIDENCE` graph links without making MCP a model-callable write
  surface.

**Verification:**

- [ ] Existing `tests/test_state.py`, `tests/test_segments.py`,
  `tests/test_session_lineage.py`, and `tests/test_graph.py` pass with new v0
  schema assertions.
- [ ] New tests cover enum validation, bounded importance boost, intent
  priority, entity modifiers, automatic rollover, drift scoring, segment drift
  traces, trusted tool-domain shift, canonical state hashes, traversal hard
  limits, and memory feedback.

**Likely files:**

- `mneme_service/state.py`
- `mneme_service/segments.py`
- `mneme_service/storage.py`
- `mneme_service/app.py`
- `tests/test_state.py`
- `tests/test_segments.py`
- `tests/test_session_lineage.py`
- `tests/test_graph.py`

### Phase 6: Retrieval, Context Prepare, Redaction, And Freshness

**Description:** Make the core user-facing value path match the spec.

**Tasks:**

- [ ] Implement canonical `budget_split` keys, defaults, unknown-key rejection,
  hard `minimum_headroom_tokens`, state-to-tail-to-evidence cascade, and unused
  slack reporting.
- [ ] Implement Hermes-parity query construction for `CONTINUATION`, `SWITCH`,
  `NEW_TASK`, and `CLARIFICATION`, using execution state when appropriate.
- [ ] Implement routing modes (`general`, `reasoning`, `factual`, `debugging`)
  with the v0.7.5 scoring formula, default weights, traceable score breakdowns,
  normalized components, and no scope leakage.
- [ ] Implement selective indexing compression for long tool/command outputs,
  including deterministic excerpt fallback, preserving raw `fetch_event`
  content, and filtering vector retrieval by `embedding_model_id`.
- [ ] Preserve the latest user message unmodified; return
  `LATEST_USER_MESSAGE_EXCEEDS_BUDGET` when it cannot fit.
- [ ] Define behavior for prepare requests without a user message.
- [ ] Ensure execution-state compression thresholds and warnings are
  deterministic and reported through `trace.execution_state_compression_level`.
- [ ] Render untrusted evidence inside escaped XML/JSON wrappers and never in
  system/developer roles.
- [ ] Strengthen redaction ordering, multiline secret handling, neutral
  redaction classes, bounded-time redaction behavior, and metadata-only binary
  blob handling.
- [ ] Enforce freshness semantics only when adapters/source connectors supply
  current/conflicting evidence.

**Verification:**

- [ ] Context prepare tests cover budget split validation, cascade, latest user
  protection, no-user-message behavior, impossible budget 422s, query
  construction, routing modes/scoring, indexing compression/excerpts, and trace
  fields including execution-state compression level.
- [ ] Security tests cover prompt-injection fixture wrapping, redaction
  fixtures, and redaction-timeout fallback/rejection behavior.

**Likely files:**

- `mneme_service/app.py`
- `mneme_service/security.py`
- `mneme_service/state.py`
- `mneme_service/storage.py`
- `tests/test_context_prepare.py`
- `tests/test_context_assembly.py`
- `tests/test_security.py`

### Phase 7: Providers, Maintenance, Metrics, And Operations

**Description:** Complete operational behavior so the daemon is reliable during
long-running local use.

**Tasks:**

- [ ] Implement reindex job creation, polling, status enum, cooperative cancel,
  idempotent cancel on final states, and provider-call stop after cancellation.
- [ ] Add provider retry/backoff, circuit breaker, half-open behavior, slow
  recovery ramp, and `WAITING_FOR_PROVIDER` expiry.
- [ ] Add `/v1/metrics` with required request, provider, writer, background,
  retention, blob, and integrity metrics.
- [ ] Add retrieval-intelligence counters for intent labels, segment rollover
  reasons, routing modes, and indexing-compression events.
- [ ] Add labeled benchmark quality report output for precision@k, recall@k,
  MRR, segment boundary accuracy/coherence, and intent confusion counts when
  ground-truth labels are available.
- [ ] Add structured logs with safe request id, trace id, endpoint, status,
  latency, and background job id.
- [ ] Document or implement service stop/restart in-flight cancellation
  semantics.

**Verification:**

- [ ] Maintenance tests cover reindex lifecycle, cancel, provider failure, and
  background micro-transactions/yield.
- [ ] Metrics tests cover advertised format, required operational counters,
  retrieval-intelligence counters, and labeled quality-report output.

**Likely files:**

- `mneme_service/app.py`
- `mneme_service/storage.py`
- `mneme_service/embeddings.py`
- `mneme_service/config.py`
- `tests/test_embeddings.py`
- `tests/test_contract.py`

### Phase 8: MCP Parity And Session Discovery UX

**Description:** Keep MCP read-only while making it usable without guessed
session ids.

**Tasks:**

- [ ] Add optional trusted immutable default session/project config for MCP.
- [ ] Support host per-call session injection and
  `session_resolution.source` in session-bound tool results.
- [ ] Add MCP-only `DEFAULT_SESSION_STALE` for stale trusted defaults.
- [ ] Ensure `resolve_session` best-guess semantics are deterministic and
  scoped.
- [ ] Keep MCP tools read-oriented; do not add `append_insight` in v0.

**Verification:**

- [ ] MCP/REST parity tests cover all tools, session resolution source,
  default-session injection, stale-default error, and no session-id guessing.

**Likely files:**

- `mneme_service/mcp_server.py`
- `mneme_service/rest_client.py`
- `mneme_service/app.py`
- `tests/test_mcp_contract.py`

### Phase 9: Benchmarks, Packaging, And Review Packet

**Description:** Prepare the final code review and public alpha dogfood gate.

**Tasks:**

- [x] Add or update benchmark fixtures for direct prompt, Mneme-only, and
  Mneme context-prepare comparisons once the context path is compliant.
- [x] Reconcile core package boundary: move or exclude development-only Codex
  adapter artifacts from core release artifacts.
- [x] Update installation, provider configuration, testing, and CI docs.
- [x] Produce final compliance matrix with implemented/deferred status.
- [x] Run full verification and prepare reviewer packet.

**Verification:**

- [x] Full test suite and compile checks pass.
- [x] Benchmark docs state methodology and do not claim savings without
  baseline evidence.
- [x] Reviewer packet contains one target spec, compliance matrix, this plan,
  and verification log.

**Likely files:**

- `docs/BENCHMARKS.md`
- `docs/INSTALLATION.md`
- `docs/TESTING_AND_CI.md`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `pyproject.toml`

## 6. Checkpoints

| Checkpoint | After phases | Required evidence |
|---|---:|---|
| Contract foundation | 0-1 | OpenAPI/capabilities/config tests pass. |
| Storage foundation | 2 | Migration, integrity, writer-lane tests pass. |
| Data lifecycle | 3-4 | Blob/export/delete/retention/readiness tests pass. |
| Memory behavior | 5-6 | State/segment/graph/context/security tests pass. |
| Operational parity | 7-8 | Reindex/metrics/MCP parity tests pass. |
| Review ready | 9 | Full test suite, compile, diff checks, compliance matrix. |

## 7. Parallelization Opportunities

Safe to parallelize after Phase 1 schemas are stable:

- Blob/export implementation and tests.
- Context prepare budget/redaction tests.
- MCP parity/default-session tests.
- Metrics/logging tests.
- Documentation and compliance matrix updates.

Must remain mostly sequential:

- Migrations and storage schema changes before endpoint work.
- Idempotency ledger before mutation retry semantics.
- OpenAPI schema changes before SDK/client-facing docs.
- Retention/delete behavior before final export/privacy review.

## 8. Key Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Spec is broader than current alpha architecture | High | Work in vertical slices and keep a compliance matrix, not a giant refactor branch. |
| SQLite writer/background behavior becomes flaky | High | Add deterministic fake workload tests and keep foreground write priority simple. |
| Blob/export code creates memory or WAL spikes | High | Enforce request/transaction limits and stream tar/blob content. |
| MCP default session leaks across projects | High | No mutable global session; only immutable config or host per-call injection. |
| Universal daemon becomes safer but less smart than Hermes | High | Keep routing intelligence, segmentation, selective compression, and feedback loop as core v0 compliance, not adapter folklore. |
| Redaction overclaims safety | Medium | Keep binary caveats, neutral classes, and explicit provider privacy docs. |
| Benchmarks become marketing claims | Medium | Require direct baseline runs and document methodology. |

## 9. Initial Implementation Order

1. Phase 0 compliance matrix.
2. Phase 1 schema/config/capabilities/OpenAPI foundation.
3. Phase 2 storage/migrations/writer lane.
4. Phase 3 blob/export/delete lifecycle.
5. Phase 4 readiness/auth/session lifecycle before broad MCP work.
6. Phase 5 structural memory behavior.
7. Phase 6 context prepare and security path.
8. Phase 7 operational maintenance.
9. Phase 8 MCP parity.
10. Phase 9 review packet and benchmarks.

## 10. Audit Baseline Update - 2026-06-22

Phase 0 read-only audit created
`docs/MNEME_V0_COMPLIANCE_MATRIX.md` and confirmed that the current alpha test
suite passes while the implementation remains materially short of Final v0.7.5.

The initial phase order remains valid, but the audit moves several safety
items earlier in execution priority:

1. Treat project isolation, safe bearer-token handling, and auth-failure audit
   as foundation work alongside Phase 1 contract/OpenAPI work, not late polish.
2. Land storage migrations, startup integrity, writer-lane behavior, and the
   idempotency ledger before broad endpoint expansion relies on mutation
   replay semantics.
3. Implement blob/BYTES_REF lifecycle and multipart rollback before claiming
   event ingestion or export/delete compliance.
4. Keep existing alpha behavior covered, but replace tests that assert
   non-final behavior, especially arbitrary BYTES_REF acceptance, legacy
   `budget_split` keys, `ACTIVE` segment status, and cross-session global
   retrieval without project isolation.

Audit-found blockers:

- Project isolation and principal/scope enforcement are not implemented.
- Some docs/scripts still pass bearer tokens through command-line arguments.
- Owned blob/BYTES_REF endpoints, storage, export, delete, GC, and multipart
  rollback are missing.
- Final `Idempotency-Key` request ledger semantics are missing.
- SQLite migration/integrity/writer-lane behavior is missing.
- Public OpenAPI schemas are not defined beyond FastAPI validation defaults.
