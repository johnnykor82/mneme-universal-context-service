# Findings: Mneme v0 Compliance Planning

## 2026-06-22 Planning Restore

- `.planning/` was absent at session start. A new `.planning/` hierarchy is
  required before any further implementation.
- Current user instruction supersedes the old root-file workflow. Root
  `task_plan.md`, `findings.md`, and `progress.md` are input context only.
- Canonical source is `docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5, approved
  for v0 implementation on 2026-06-21.
- Baseline audit source is `docs/MNEME_V0_COMPLIANCE_MATRIX.md`.
- Implementation plan source is `docs/MNEME_V0_COMPLIANCE_IMPLEMENTATION_PLAN.md`.
- The worktree was already dirty before `.planning/` content was written.
  Existing modified code, tests, and docs must be treated as prior/user work.

## Compliance Baseline

- User-provided baseline counts: COMPLIANT 3, PARTIAL 51, MISSING 10,
  UNCLEAR 0, OUT_OF_SCOPE/FUTURE 1.
- Current matrix file also contains later Phase 1A evidence with counts:
  COMPLIANT 3, PARTIAL 52, MISSING 9, UNCLEAR 0, OUT_OF_SCOPE/FUTURE 1.
- Root history says Phase 1A added config defaults/validation,
  capabilities/error schema components, expanded capabilities, bearer OpenAPI
  scheme, and session-start schema compatibility. Treat this as existing
  dirty-worktree evidence to review, not as a cleared `.planning/` task.

## Blocker Gap Clusters

- Project isolation, principal derivation, effective project scope, and scoped
  filtering are missing or incomplete: CM-018, CM-019, CM-052.
- Safe bearer-token handling is incomplete; docs/scripts still include unsafe
  token-in-argv paths.
- Auth-failure audit with `UNAUTHENTICATED` principal is incomplete.
- Owned blob/BYTES_REF lifecycle is missing: CM-031, CM-032, CM-033.
- `Idempotency-Key` ledger semantics are missing: CM-060.
- SQLite migrations, startup integrity, and writer lane are missing: CM-056.

## First-Phase Evidence Notes

- First phase should combine contract/OpenAPI/config/capabilities with security
  foundation because the audit explicitly moved auth/project isolation/token
  handling earlier.
- Relevant spec anchors: Sections 8, 9, 12.6-12.7, 14.1, 16, 17.1, 20, 21,
  22, 23-25, 27-30.
- Relevant Section 24 tests for first phase: 25, 26, 27, 29, 32, 33, 34, 37,
  38, 39, 43, 59, 77, 84, 85, 111, 117, 118.
- Redaction timeout and prompt-injection implementation are tracked mainly in
  Phase 06, but OpenAPI/schema/audit placeholders may be touched earlier.

## Mneme MCP Evidence

- `resolve_session` for this project path was AMBIGUOUS.
- Newest visible session observed: `019eef36-2751-7672-8eeb-c8e7d1eb5628`.
- Session search corroborated the current user prompt and root progress reads.
- Mneme memory is evidence only; current files and user instructions override it.
- A post-compaction `resolve_session` retry on 2026-06-22 was rejected by the
  external auto-review/model-capacity path before returning project evidence.
  This is not a repository blocker; local `.planning` files remain the workflow
  source of truth.

## 2026-06-22 Phase 2 Implementation Findings

- `security-guidance` ASVS detail files were not present in the local skill
  install; Phase 2 security decisions were anchored to the skill index and the
  canonical Mneme spec Sections 18, 21, and 22.
- SQLite startup now has `CURRENT_SCHEMA_VERSION`, `PRAGMA user_version`,
  `schema_migrations`, default integrity checks, and fail-closed
  mismatch/newer-schema behavior.
- `Idempotency-Key` replay/conflict is implemented for the currently present
  mutating endpoints: session start, event batch, turn complete, context
  prepare, and session delete. Future blob/segment/session-close/maintenance
  idempotency remains with the phases that add those endpoints.
- Current-process Store writes now pass through a bounded single-writer lane;
  deterministic tests cover queue-full `429 RATE_LIMITED`, mapped
  `503 STORAGE_BUSY`, and SQLite busy timeout. Future background priority and
  reindex/retention micro-transaction behavior remains in later operations
  phases.
- Event batch conflict preflight prevents expected `409 CONFLICT` cases from
  leaving earlier events partially stored. A stronger successful-batch
  transaction visibility guarantee remains tracked as part of the broader
  storage/ingest hardening still marked `PARTIAL` in the matrix.

## 2026-06-22 Phase 3 Planning Findings

- Phase 3 is active in `.planning/roadmap.md`, but its phase plan is still a
  stub and must be expanded before production or test implementation continues.
- Canonical Phase 3 anchors are Sections 13, 14.2, 14.3, 14.8, 21, 22, and
  Required Contract Tests 14-17, 47, 49, 51, 53-54, 62, 66, 76, 81, and 114.
- Matrix rows CM-031, CM-032, and CM-033 are still `MISSING`; Section 24 blob
  tests 15, 16, 17, 47, 51, 53, 54, 62, 66, 76, 81, and 114 are also marked
  missing in the matrix.
- Phase 3 scope must cover blob endpoint contract, SQLite-owned blob storage,
  BYTES_REF validation/normalization, multipart atomic rollback, session export
  JSON/tar behavior, scoped delete interactions, scoped blob GC, and blob-route
  idempotency/error envelopes.
- Read-only explorer `019eefb5-7afc-76b0-8125-952fb459bdf9` corroborated that
  existing integration points are `app.py` idempotency/scope helpers,
  JSON-only `/v1/events`, simple JSON export/delete, and storage `_init`; it
  also flagged multipart atomicity and export audit defaults as later coupling
  risks.
- The `security-guidance` skill again lacked local `data/asvs/*` reference
  files. Phase 3 security implementation is therefore anchored to the skill
  index plus canonical spec requirements for input validation, HTTP message
  validation, upload/download handling, authorization, and safe error envelopes.
- Task 01 implemented only direct server-owned blob endpoint lifecycle and
  range reads. Multipart, owned BYTES_REF event validation, export/delete blob
  lifecycle, and blob GC remain in active/future Phase 3 tasks.
- Task 02 closed the previous permissive BYTES_REF hole: JSON event ingest now
  requires server-owned `mneme-blob://` refs visible in the target
  session/project scope and rejects default `file://` adapter-owned refs.
- Blob `ref_count` now changes through duplicate-safe reference attach/detach
  methods, but session delete/export/GC lifecycle use of those references
  remains in later Phase 3 tasks.
- Task 03 added multipart event ingestion with digest-based request hashes,
  placeholder rewrite, transaction-level blob/event/ref commits, and rollback
  tests. The route now manually dispatches JSON versus multipart bodies, so
  custom OpenAPI restoration is required for `/v1/events` requestBody docs.
- Task 04 moved export/delete closer to the final contract: JSON export is now
  metadata-only for blobs, `tar_bundle` includes manifest plus blob parts,
  unknown formats return `422`, capabilities advertise bundle support, and
  session delete removes session-owned blob rows.
- Task 05 added explicit blob GC with dry-run/deletion counts, scope checks,
  idempotency replay/conflict, and OpenAPI schemas. Retention-triggered and
  startup/session-close GC remain in later retention/operations phases.

## 2026-06-22 Phase 3 Completion Findings

- Phase 3 verification passed: focused blob/contract/OpenAPI/storage tests
  `61 passed, 1 warning`; MCP regression `16 passed`; full suite
  `202 passed, 1 warning`; compileall and `git diff --check` passed.
- Current matrix counts after Phase 3 are `COMPLIANT=6`, `PARTIAL=55`,
  `MISSING=3`, `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1`.
- CM-031 and CM-032 are now `COMPLIANT`; CM-033 is `PARTIAL` only for
  later CLI/startup/retention-triggered GC and backup/restore procedure.
- CM-042 is now `PARTIAL` because `/v1/maintenance/blob-gc` exists, while
  retention sweeps, reindex jobs, cancellation, background job status, and
  operations observability remain future phase work.
- Phase 4 must not treat retention as isolated session cleanup: it must connect
  session delete/close/retention semantics with visible project scope,
  derivative cleanup, blob lifecycle, audit anchors, and idempotency evidence.

## 2026-06-23 Phase 4 Completion Findings

- Phase 4 verification passed: focused lifecycle/retention suite
  `55 passed, 1 warning`; MCP regression `16 passed`; full suite
  `196 passed, 1 warning`; compileall and `git diff --check` passed.
- Current matrix counts remain `COMPLIANT=6`, `PARTIAL=55`, `MISSING=3`,
  `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1` because Phase 4 improved evidence in
  several rows but did not fully close rows that still include later
  state/segment/reindex/metrics/MCP/freshness requirements.
- CM-035 now has direct session read/close/generated-id/retention evidence but
  remains `PARTIAL` for forced active cleanup in-flight-read conflict tracking,
  startup/periodic sweeps, and export `include_audit` policy.
- CM-051/CM-055 now include anonymized forensic anchor evidence and retention
  delete behavior; broader audit feedback state, evidence edges, and at-rest
  policy remain later work.
- Capabilities now advertise `supports_retention_cleanup=true` only after
  actual cleanup/delete behavior was implemented and tested.
- Phase 5 must be expanded from its stub before production/test implementation:
  execution-state update, direct segment REST, graph traversal limits,
  classifier/entity modifiers, lineage/routing, and Section 24 tests 10-13,
  23-24, 61, 78-80, 88, 93-94, 97-103, 105-110, 112, and 116.

## 2026-06-23 Phase 5 Planning Findings

- Spark read-only review recommended five implementation chunks: execution
  state, graph traversal, segment lifecycle, routing/entity modifiers, and
  session discovery/lineage. Parent adopted the order and added a sixth
  verification/evidence task.
- Phase 5 begins with execution-state update because later routing, query
  construction, memory feedback, and segment decisions depend on trustworthy
  state and state-history semantics.
- Graph traversal is scheduled before segment REST so anchor/evidence edge
  behavior and traversal warnings exist before segment lifecycle starts
  creating more graph relationships.
- Routing/entity modifiers are deliberately later than state/graph/segments:
  deterministic classifier behavior needs stable state inputs and segment
  boundary semantics to avoid brittle tests.
- Session discovery/lineage stabilization is last in implementation because it
  can be affected by all previous changes to scope, graph, routing, and segment
  metadata.

## 2026-06-23 Phase 5 Completion Findings

- Phase 5 verification passed: focused state/segments/graph/routing suite
  `70 passed, 1 warning`; MCP regression `16 passed`; full suite
  `210 passed, 1 warning`; compileall and `git diff --check` passed.
- Matrix counts after Phase 5 are `COMPLIANT=6`, `PARTIAL=57`, `MISSING=1`,
  `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1`.
- CM-030 and CM-038 moved from `MISSING` to `PARTIAL` because deterministic
  entity modifiers and explicit execution-state update now exist, but each row
  still has broader lifecycle/provider/idempotency residuals.
- Section 24 rows now mark S24-23, S24-24, S24-88, S24-93, S24-97, S24-101,
  S24-102, S24-103, S24-110, and S24-112 as covered for Phase 5 purposes.
- Residual Phase 5 gaps remain recorded for S24-80, S24-100, S24-105,
  S24-106, S24-107, and S24-109, plus `SEGMENT_ANCHOR`, final enum edge
  cases, richer drift/freshness metadata, and full canonical state-hash
  fixtures.

## 2026-06-23 Phase 6 Planning Findings

- Spark worker `019ef590-cf31-7bd2-9c40-d12a5ca085ab` performed a read-only
  Phase 6 stub audit and proposed budget -> latest-user -> wrappers ->
  redaction -> freshness ordering. Parent review adopted the ordering and added
  a sixth verification/evidence task.
- Phase 6 must start with budget/token-accounting semantics because latest-user
  protection, impossible-budget errors, and evidence packing all depend on the
  same canonical `budget_split` and trace fields.
- Freshness is deliberately late in Phase 6 because prompt wrappers and
  redaction must be stable before freshness/conflict metadata is surfaced in
  selected evidence and traces.
- Spark-suitable Phase 6 implementation slices are Tasks 01, 02, and 05 if
  scoped narrowly; Tasks 03 and 04 touch shared rendering/redaction surfaces and
  should either be parent-led or delegated as a single bounded bundle.
- Task 01 parent review found and fixed a Spark regression in canonical default
  handling: Final v0.7.5 defaults apply only when `budget_split` is omitted;
  supplied partial splits default omitted `hints_ratio` to `0.0` before the sum
  check.
- Task 01 also showed that S24-20 is not fully closed by warning-only behavior:
  changed STANDARD/QUALITY prepare currently emits `COST_MODE_DOWNGRADED` under
  char approximation, but final reject or downgrade-to-MINIMAL behavior remains
  a Phase 6 residual.
- Task 02 added latest-user protection with exact 422 reasons. Parent review
  noted a future hardening opportunity: if an oversized non-minimal execution
  state fits its bucket but causes final collision, a later packing refinement
  should prefer recompressing to minimal state before declaring
  `MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET`.
- Task 03 kept wrapper work separate from redaction profile work. Retrieved
  evidence is now XML-escaped and wrapped as data-only content with
  `source_trust`, while the execution-state block can still include raw
  redacted state summaries until Task 04 redaction hardening.
- Task 04 expanded the default redaction profile without changing the existing
  outward replacement token (`[REDACTED]`) to avoid broad compatibility churn.
  Covered secret fixtures now include Bearer, JWT-like, AWS, GitHub, Google API
  key, PEM, `.env`, database URL credentials, and nested sensitive JSON fields.
- Task 04 chose the explicit `422 REDACTION_TIMEOUT` posture for foreground
  event ingestion rather than degraded metadata-only storage on timeout. This
  avoids silently persisting unredacted plaintext when `max_redaction_time_ms`
  is exceeded.
- Spark worker `019ef9e9-6841-7121-a8c4-cfb5ed27392e` reviewed the Task 04
  diff and flagged a false-positive risk in JSON key redaction. Parent review
  accepted the concern, added benign-key regression coverage for
  `credential_type` and `token_budget`, and narrowed key matching while leaving
  the spec-required `.env` assignment matcher broad.
- Task 04 marks non-text `BYTES_REF` event ingestion with
  `redaction_scope=BINARY_METADATA_ONLY`. Existing metadata-only text extraction
  for `BYTES_REF` means raw blob bytes are not indexed/embedded through
  `text_from_content`; full extractor-policy support remains out of this task.
- `security-guidance` ASVS reference files were unavailable at the paths named
  by the installed skill index, so Task 04 used canonical Mneme Sections 17.2
  and 17.3 plus local tests as the controlling security source.
- Task 05 confirmed that freshness is now adapter/source supplied only:
  `event.freshness`, `metadata.freshness`, or `privacy.freshness`; Mneme core
  does not claim independent current filesystem/git verification.
- Task 05 implements explicit conflict handling only when `CURRENT` evidence
  carries `conflicting_event_ids` (or equivalent freshness metadata). Conflicting
  memory evidence is dropped before context packing and trace warnings include
  `FRESHNESS_CONFLICT`.
- Spark worker `019ef9f4-55af-7822-aba8-efbf1e938d9b` reviewed Task 05 and
  found no high-severity regressions. Residuals recorded: warning shape remains
  endpoint-specific, conflict drops do not refill from a larger candidate set,
  and missing/invalid freshness defaults to `RECENT` rather than deriving
  `HISTORICAL` from timestamps.
- Phase 6 verification passed: focused context/security/freshness suite
  `75 passed, 1 warning`; MCP regression `16 passed`; full suite
  `226 passed, 1 warning`; compileall and `git diff --check` passed.
- Phase 6 matrix update moved CM-048 from `MISSING` to `PARTIAL`; matrix row
  counts are now `COMPLIANT=6`, `PARTIAL=58`, `MISSING=0`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
- Phase 7 is now active, but its phase plan is still a stub. Per
  `spec-driven-planning`, Phase 7 must be expanded into detailed task plans
  before production/test implementation begins.
- Spark worker `019ef9fa-9f61-7cd0-8271-000a8760729a` performed a read-only
  Phase 7 audit and recommended contract foundation before reindex API,
  cancellation, resiliency, and metrics/observability completion. Parent review
  split metrics into its own early task so observability can support later
  reindex behavior.
- Phase 7 Task 01 confirmed the canonical capabilities example in Section 14.1
  requires `supports_metrics=true`, `supports_reindex_jobs=true`, and
  `supports_reindex_job_polling=true` for v0 once the route surface exists; the
  previous OpenAPI test expectation of `supports_metrics=false` was Phase 6-era
  truthful-but-incomplete behavior.
- Spark worker `019efa06-1860-7670-8ef0-e460b4254498` reviewed the Task 01
  contract slice and confirmed required paths:
  `/v1/metrics`, `/v1/maintenance/reindex`,
  `/v1/maintenance/reindex/{job_id}`, and
  `/v1/maintenance/reindex/{job_id}/cancel`. Parent adopted the schema/status
  recommendations and kept trace/cost response typing as a later Phase 7
  residual rather than expanding Task 01 scope.
- Task 01 intentionally uses minimal in-process reindex job records only as a
  typed contract anchor. Durable persistence, idempotent create semantics,
  provider-unavailable behavior, polling progress, cancellation safety, and
  background engine behavior remain assigned to Phase 7 Tasks 03-05.
- Spark worker `019efa0b-2da5-7d81-9c3f-59f5db5d4d32` inventoried metrics data
  sources for Task 02. Parent implemented immediate safe aggregation from
  existing numeric data and lightweight HTTP instrumentation, while leaving
  precise provider latency and labelled retrieval-quality values as zero-valued
  family placeholders until the corresponding runtime data is produced.
- Task 02 metrics exporter deliberately emits Prometheus labels/counts only,
  never event content, metadata values, bearer tokens, provider secrets, or
  evidence text. Required retrieval/segmentation intelligence metric families
  are present with `UNKNOWN`/zero defaults when no source data exists.
- Spark worker `019efa10-e761-7460-a5db-c46bc2517cd3` reviewed Task 03 and
  recommended a minimal `reindex_jobs` table, normalized idempotency inputs,
  404 for out-of-scope poll, default `503 PROVIDER_UNAVAILABLE`, and
  `WAITING_FOR_PROVIDER` when enqueue-while-unavailable is enabled. Parent
  adopted those recommendations.
- Task 03 changed reindex create semantics from the Task 01 in-memory contract
  stub: default daemon instances without an embedding provider now return
  `503 PROVIDER_UNAVAILABLE`; tests that need a shape-only reindex job use
  `reindex_enqueue_when_provider_unavailable=True` and expect
  `WAITING_FOR_PROVIDER`.
- Reindex candidate counts are persisted at job creation. `force=true` counts
  all scoped non-memory-read events up to `max_job_events`; status-based
  selection uses `event.ingestion.embedding_status` and, when an active
  embedding model exists, also treats missing embedding-index rows as
  `PENDING`.
- Spark worker `019efd97-2eb4-7e92-8ca0-bca1fbe6e47d` reviewed Task 04 and
  found that full S24-75 provider-call/write stop proof requires the Task 05
  reindex execution engine. Task 04 therefore closes persisted cancel,
  final-state idempotency, metrics, and audit evidence, while Task 05 now
  explicitly inherits the S24-75 worker checkpoint proof.
- Task 04 adds `REINDEX_CANCEL` audit only for session-scoped jobs, where the
  existing session audit lane is well-defined. Project/all maintenance audit
  expansion can be handled later if the reviewer wants daemon-wide maintenance
  audit records outside session history.
- Spark worker `019efd9c-e8ff-76a2-b352-4dfd1dc28970` reviewed the first Task
  05 drain slice and found missing per-event failure status, provider wait
  timeout, and reindex-level circuit behavior. Parent fixed all three before
  marking Task 05 complete.
- Task 05 deliberately exposes the reindex drain as an internal
  `app.state.run_reindex_job_once(job_id)` hook rather than a public REST
  endpoint. This preserves the v0 REST surface while giving tests and a future
  scheduler a deterministic bounded execution path.
- Reindex provider circuit behavior is implemented at the drain layer as a
  compact recent-outcome guard using the configured minimum call count, failure
  ratio, and open seconds. It avoids new provider calls while open and lets
  future successful calls clear the recent window after cooldown.
- Phase 7 verification passed on 2026-06-25: focused operations/reindex suite
  `88 passed, 1 warning`; MCP regression `16 passed`; full suite
  `243 passed, 1 warning`; compileall and `git diff --check` passed.
- Phase 7 matrix synchronization moved the audit baseline to Phase 7 and added
  evidence for `/v1/metrics`, reindex create/poll/cancel, persistent
  `reindex_jobs`, provider wait/failure/circuit behavior, bounded drain slices,
  and safe metrics output.
- Row-level compliance remains intentionally conservative: CM-020, CM-041,
  CM-042, CM-057, CM-058, CM-060, CM-061, CM-062, and CM-063 stay `PARTIAL`
  because each includes later/final-acceptance scope beyond the Phase 7 slice.
  S24-52/63 now has direct compliant endpoint evidence; S24-72/77 are covered
  for metrics route/capabilities, while S24-108 remains partial until final
  quality-evaluation labeling semantics are proven beyond exported family
  names.
- Phase 8 planning review confirmed the current MCP/REST parity gaps: REST
  lacked `/v1/tools/mneme_cost_report`, tool envelopes lacked
  `session_resolution`, MCP default-session/stale-default behavior was absent,
  REST-client error mapping was incomplete for some v0 status codes, and
  schema/version rejection behavior still needs explicit evidence.
- Phase 8 Task 01 closed the narrow `mneme_cost_report` parity gap by making
  MCP call `POST /v1/tools/mneme_cost_report`; `GET /v1/costs/session/{id}`
  remains as the existing direct REST endpoint, while the tool endpoint is now
  the canonical MCP parity path.
- Phase 8 Task 02 confirmed the session-bound REST/MCP tool set:
  context_search, fetch_event, expand_context, recall_recent, list_segments,
  get_execution_state, get_goal_history, explain_context, and
  mneme_cost_report. These now emit `session_resolution` for explicit
  arguments; `resolve_session` emits `RESOLVED_BY_TOOL` only when it resolves a
  concrete session; `list_sessions` intentionally omits metadata as a
  non-session-bound discovery tool.
- Phase 8 Task 03 implements only immutable/default or explicit session
  resolution at the MCP server boundary. It deliberately does not add a mutable
  current-session setter, preserving Section 15's cross-project leakage guard.
  Host per-call injection can be represented by a trusted host proxy/adaptor
  using `default_session_source="HOST_INJECTED"`; the model-visible tool
  arguments still do not include a source override.
- Phase 8 Task 04 intentionally keeps versioning narrow: v0 MCP tool names
  remain unversioned, capabilities still expose `mcp_tool_versions`, and REST
  tool payloads now reject unsupported shared `mneme.tool_request.*`
  schema_versions. No broad schema-negotiation layer was introduced.
- REST-client fallback mapping now covers 415/416 explicitly; semantic 503
  distinctions such as `STORAGE_BUSY` versus `PROVIDER_UNAVAILABLE` remain
  dependent on server-sent error envelopes, which the client preserves.
- Phase 8 verification passed on 2026-06-25: focused MCP parity suite
  `61 passed, 1 warning`; full suite `252 passed, 1 warning`; compileall and
  `git diff --check` clean. Matrix counts after Phase 8 are
  `COMPLIANT=9`, `PARTIAL=55`, `MISSING=0`, `UNCLEAR=0`,
  `OUT_OF_SCOPE/FUTURE=1`.
## 2026-06-25 - Phase 9 Task 01 Benchmark Methodology Evidence

- Existing `mneme benchmark` already used local fake providers and returned a
  smoke summary, but lacked machine-readable methodology and labeled quality
  report fields required for reviewer evidence.
- Added `mneme.benchmark_quality_report.v0` to local benchmark output using the
  synthetic corpus labels: retrieved event ids, relevant event ids,
  precision@k, recall@k, MRR, and confusion counts.
- Added benchmark methodology evidence that explicitly identifies
  `LOCAL_SMOKE`, `LOCAL_FAKE_PROVIDERS`, `SYNTHETIC_LABELED`,
  `comparative_baseline=NOT_RUN`, and no token/cost reduction claim.
- Spark worker `019efdc8-d002-7fe0-bb03-81097ff21806` scanned the scoped docs
  and found no explicit unsupported token/cost-savings claim or automatic
  integration overclaim in the Task 01 read set. It recommended mirroring the
  benchmark caveat in installation/testing docs as optional Phase 9 Task 03
  cleanup.

## 2026-06-25 - Phase 9 Task 02 Core Package Boundary Evidence

- Spark worker `019efdcc-536d-7333-8927-9fd737fdc61b` confirmed the core
  package discovery config already limits setuptools discovery to
  `include = ["mneme_service*"]`, and `adapters/codex` currently contains
  docs/examples without Python package markers.
- Added executable regression coverage in `tests/test_codex_adapter.py` to
  assert core package discovery remains restricted to `mneme_service*`, does
  not include `adapters`, and publication docs require a separate Codex adapter
  repository/package.
- No adapter directory move was needed; release exclusion is achieved through
  packaging metadata and publication docs, which keeps Phase 9 risk low.

## 2026-06-25 - Phase 9 Task 03 Release Docs Honesty

- Existing docs already constrained MCP/Codex to tools-only, explicit recall,
  and no automatic prompt replacement.
- Installation and testing docs did not mirror the README/local benchmark
  caveat, so added release-facing text that `mneme benchmark` is a local smoke
  benchmark with fake providers, no external provider calls, no comparative
  baseline, and no proof of token/cost reduction.
- Updated `docs/BENCHMARKS.md` example so it reflects the new methodology and
  synthetic quality-report fields emitted by `mneme_service/benchmarks.py`.

## 2026-06-25 - Phase 10 Residual Acceptance Accounting

- After Phase 9, matrix row counts are `COMPLIANT=12`, `PARTIAL=52`,
  `MISSING=0`, `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1`.
- Required Contract Test Mapping mechanically includes all Section 24 numbers
  1-119; no test number is missing from the mapping table.
- 39 Section 24 numbers are in `COMPLIANT` rows and 80 are still in `PARTIAL`
  rows. Phase 10 must classify those partials before final acceptance can be
  claimed.
- Active Spark residual audits:
  `019efdd8-0131-7483-9b71-3d9521f53903` covers CM-002..020,
  `019efdd8-57a5-77b3-a4ed-396df371f148` covers CM-021..042,
  `019efdd8-a461-7770-9b7a-ceaaf7a76e39` covers CM-044..060,
  and `019efdd8-edfc-7103-b651-9cde204fbdea` covers acceptance rows and
  Section 24 numbering.

### Spark Audit: CM-021 Through CM-042

Spark worker `019efdd8-57a5-77b3-a4ed-396df371f148` performed read-only
inspection of lifecycle/storage/state rows. It classified CM-031 and CM-032 as
already compliant, and all remaining rows CM-021..030 and CM-033..042 as real
residual implementation/test gaps. No explicit deferral/non-goal candidate was
identified in this cluster.

High-value residual batches suggested by that audit:

1. Context lifecycle correctness:
   CM-021, CM-022, CM-023, CM-024, CM-025, CM-039, CM-047 plus Section 24
   tokenizer/message/event/turn/freshness/trace partials.
2. Execution/segment/edge/type completeness:
   CM-027, CM-029, CM-030, CM-038, CM-039, CM-040 plus segment/entity/graph
   Section 24 partials.
3. Storage/concurrency/maintenance lifecycle:
   CM-033, CM-034, CM-035, CM-040, CM-041, CM-042 plus storage/retention/
   maintenance Section 24 partials.

### Spark Audit: CM-044 Through CM-060

Spark worker `019efdd8-a461-7770-9b7a-ceaaf7a76e39` performed read-only
inspection of context/MCP/security/ops rows. It classified CM-049 and CM-050
as already compliant, and all remaining rows CM-044..048 and CM-051..060 as
real residual implementation/test gaps. It identified no explicit deferral or
non-goal candidate in this cluster.

Smallest residual batches suggested by that audit:

1. Discovery, scope, and pagination hardening:
   CM-044 plus Section 24 discovery/search metadata partials.
2. Context prepare/freshness warning/schema completion:
   CM-047, CM-048, CM-051, CM-054 plus S24-20/70/89/99/111-style partials.
3. Storage/migrations and idempotency completion:
   CM-056, CM-060 plus S24-40/41/42/56/59/74/75.
4. OpenAPI/operations/errors polish:
   CM-057, CM-058, CM-059 plus trace/cost/provider lifecycle edge partials.

### Spark Audit: CM-002 Through CM-020

Spark worker `019efdd8-0131-7483-9b71-3d9521f53903` performed read-only
inspection of product-boundary/provider/foundation rows. It classified CM-015
as likely matrix-stale/already covered by current metrics/reindex/retention
architecture evidence, CM-013 and CM-014 as explicit deferral/non-goal
candidates requiring user approval, and the remaining rows in its cluster as
real residual implementation/test gaps.

Notable implications:

- CM-013 and CM-014 cannot be silently moved to compliant unless we either
  implement/test final `CONTEXT_ENGINE` host lifecycle proof and host hook
  integration, or record an explicit user-approved v0 deferral/non-goal
  decision for the missing host-depth/Hermes hook scope.
- CM-015 should be rechecked by the parent agent during Task 01 because it may
  be a matrix wording drift after metrics/reindex/retention work.
- CM-019 still calls out token-file owner-readable permission checks and
  complete maintenance route scope parity as real security residuals.

## 2026-06-25 - Phase 10 Batch A Security/Idempotency Result

- Added owner-only token-file permission checks for owner auth token files and
  static scoped token files. Group/world-readable token files now fail startup
  with a clear `owner-readable` validation error.
- Added durable `Idempotency-Key` replay/conflict support to
  `POST /v1/sessions/{session_id}/execution_state` and
  `POST /v1/segments/{segment_id}/close`.
- Existing `POST /v1/segments/start` idempotency was already present; Batch A
  adds missing close-route coverage.
- Matrix rows CM-019, CM-052, and CM-060 were updated with Batch A evidence,
  but remain `PARTIAL` because other residuals remain open.

## 2026-06-25 - Phase 10 Batch B Tokenizer Quality Result

- Added explicit S24-20 behavior for model-bound `/v1/context/prepare`:
  when `policy.model_bound=true` and `cost_mode` is `STANDARD` or `QUALITY`,
  local `CHAR_APPROXIMATE` token estimates now fail with `422 VALIDATION_ERROR`
  and downgrade metadata (`effective_cost_mode=MINIMAL`).
- Existing non-model-bound local diagnostics still work with
  `COST_MODE_DOWNGRADED` warnings, preserving local smoke/dev behavior.
- Matrix rows CM-021, CM-047, CM-062, and the Section 24 grouped row
  `18, 19, 20, 21, 22, 55, 69, 70, 89, 99` were updated with Batch B evidence,
  but remain `PARTIAL` where other grouped residuals remain open.

## 2026-06-25 - Phase 10 Batch C Selection

- Full verification after Batch A/B passed (`263 passed, 1 warning`), but
  final acceptance cannot proceed while real residual `PARTIAL` rows remain.
- Selected CM-060 reindex cancel ledger support as the next bounded residual:
  the route already has safe final-state idempotency, but matrix evidence says
  it is not yet backed by the durable `Idempotency-Key` ledger.
- This batch should not alter provider-drain/cancel semantics; it should only
  add compatible replay and incompatible conflict behavior for explicit
  `Idempotency-Key` calls.

## 2026-06-25 - Phase 10 Batch C Result

- Spark inspection confirmed the existing route helper pattern:
  normalize payload, hash path parameters plus body, replay before mutation,
  and record the response after successful route logic.
- Reindex cancel now uses durable ledger semantics with path template
  `/v1/maintenance/reindex/{job_id}/cancel` and request hash containing
  `job_id` plus normalized cancel body.
- Existing final-state idempotency remains unchanged: calls without
  `Idempotency-Key` still return the current final job state without rewriting
  history.
- CM-060 no longer has an identified v0 implementation gap after Batch C.

## 2026-06-25 - Phase 10 Batch D Selection

- Selected S24-80 segment invalid enum rejection as the next bounded residual.
- Matrix row CM-040 remains `PARTIAL` partly because invalid enum rejection for
  final segment enum fields is not fully proven.
- Batch D must stay narrow: validate segment enum fields and tests only, while
  leaving broader `ABANDONED`/`SUPERSEDED` lifecycle semantics and
  `SEGMENT_ANCHOR` graph work for separate residual tasks.

## 2026-06-25 - Phase 10 Batch D Result

- Spark clarified that S24-80 is named
  `event_importance_and_segment_created_by_enums_validate`; Batch D therefore
  covered both event `importance` and segment `created_by`.
- The implementation also aligned adjacent segment enum checks by rejecting
  invalid segment list `status` filters and replacing the old close outcome set
  with the spec values: `COMPLETED`, `ABANDONED`, `SUPERSEDED`,
  `INTERRUPTED`, `CANCELLED`, and `UNKNOWN`.
- Automatic segments now carry `created_by="AUTOMATIC"` instead of relying on
  response fallback defaults.
- CM-040 remains `PARTIAL` because `SEGMENT_ANCHOR` edges and broader
  `ABANDONED`/`SUPERSEDED` lifecycle semantics remain separate residuals, but
  S24-80 is now covered.

## 2026-06-25 - Phase 10 Batch E Selection

- Selected S24-105 as the next bounded residual because it is independent of
  the larger automatic segmentation/drift scoring cluster.
- Matrix rows CM-028, CM-029, and CM-051 already claim partial memory-read
  audit, state feedback, and `MEMORY_READ_EVIDENCE` graph-edge behavior; Batch
  E must determine whether the residual is a real runtime gap or missing
  dedicated contract tests.

## 2026-06-25 - Phase 10 Batch E Result

- Spark found that the central `audit_memory_tool` path already creates
  memory-read traces, audits, canonical `MEMORY_READ` events, bounded redacted
  state summaries, and `MEMORY_READ_EVIDENCE` edges for most tools.
- The concrete runtime gap was `/v1/tools/mneme_cost_report`, which Section 16
  includes in trace/audit defaults but which did not call `audit_memory_tool`.
- Batch E added the missing `mneme_cost_report` memory-read trace/audit/state
  feedback and strengthened S24-105 summary/edge assertions.
- CM-051 remains `PARTIAL` only for test-only audit-disable config and broader
  audit lifecycle controls; S24-105 is now directly covered.

## 2026-06-25 - Phase 10 Batch F Selection

- Remaining Section 24 residuals now include S24-100, S24-106, and S24-107 in
  the segmentation drift cluster.
- This cluster is higher risk than the previous residual batches because it may
  touch automatic segmentation scoring, trace metadata, and trusted adapter
  domain-shift signals. Batch F is therefore audit-first: implement only a
  bounded slice if Spark and parent inspection show one exists.

## 2026-06-25 - Phase 10 Batch F Result

- Spark confirmed S24-100/106/107 were real implementation/test gaps:
  `SEGMENT_DRIFT` traces lacked drift-score component metadata, classifier
  drift decisions used a fixed threshold rather than configured threshold, and
  tool-domain shift metadata was not trusted-adapter scoped.
- Batch F implemented the bounded slice: weighted drift score, configured
  threshold, ADAPTER-scoped `metadata.tool_domain_shift`, trace
  `drift_components`, `drift_weights`, `drift_score`, `drift_threshold`, and
  `TOOL_DOMAIN_SHIFT` rollover reason.
- Topic entropy remains `0.0` when no tags/buckets exist, matching the v0
  fallback path; richer topic-entropy derivation remains a quality extension,
  not an open Section 24 residual after Batch F.

## 2026-06-25 - Phase 10 Batch G Selection

- Selected S24-8 because it is an isolated turn-completion residual: explicit
  failed/interrupted/cancelled final statuses are not covered by current tests.
- Batch G should not alter turn storage architecture; it should validate and
  echo final status semantics on the existing `/v1/turns/complete` route.

## 2026-06-25 - Phase 10 Batch G Result

- `/v1/turns/complete` now accepts `COMPLETED`, `FAILED`, `INTERRUPTED`, and
  `CANCELLED`, rejects invalid statuses, replays compatible repeated calls,
  and returns `409 CONFLICT` for incompatible repeated turn completion.
- The route now returns `mneme.turn_complete_result.v0` with the final status
  rather than the older generic `RECORDED` acknowledgement.
- S24-8 is directly covered; CM-025/CM-037 remain `PARTIAL` only for broader
  typed turn schema/OpenAPI and derived-state/usage update semantics.
## 2026-06-25 - Phase 10 Batch H Selection

- Residual row `10, 11, 109, 119` still has two concrete open items:
  S24-109 canonical state-history hash fixture coverage and S24-119 explicit
  context-prepare compression-level/truncation warning coverage.
- Spark read-only audit found `execution_state_hash()` already uses
  `canonical_json(state).encode("utf-8")`, while context-prepare already emits
  `execution_state_compression_level` but does not add a dedicated warning when
  the level is `TRUNCATED`.
- Batch H is therefore scoped to tests plus minimal warning propagation, not a
  state-storage redesign.

## 2026-06-25 - Phase 10 Batch H Result

- S24-109 is covered by
  `tests/test_state.py::test_state_history_hash_uses_canonical_json_bytes`,
  which checks the returned history hash against SHA-256 over
  `canonical_json(state).encode("utf-8")` and verifies the previous-state hash
  chain is present.
- S24-119 is covered by
  `tests/test_context_assembly.py::test_context_prepare_trace_reports_truncated_execution_state_compression_level`,
  which forces `TRUNCATED` execution-state compression and verifies
  `EXECUTION_STATE_TRUNCATED` in both response trace summary and stored trace.
- The first full run exposed an over-broad warning propagation regression in
  resume-fill `REQUEST_UNDER_BUDGET`; Batch H narrowed top-level early-response
  warnings back to the previous behavior while keeping trace warnings complete.

## 2026-06-25 - Phase 10 Batch I Selection

- Residual row `95, 96, 104` is likely a test/evidence gap, not a production
  behavior gap.
- Spark read-only audit found S24-95 raw fetch preservation already covered by
  long tool-output ingest/fetch tests, and S24-96 model-id filtering already
  implemented through `EmbeddingIndex`/`Store.list_embeddings*` model filters.
- Batch I will add explicit focused evidence for active model-id isolation and
  deterministic provider-free excerpt stability, then update the matrix.

## 2026-06-25 - Phase 10 Batch I Result

- S24-95 is covered by the existing long tool-output ingest/fetch test proving
  compressed embedding input does not replace fetchable redacted raw content.
- S24-96 is covered by a new active-model-id isolation test: rows indexed under
  `embedding-old` are invisible to an `EmbeddingIndex` configured with
  `embedding-new`.
- S24-104 is covered by a new direct deterministic fallback test for
  `summarize_for_embedding`, asserting stable output, head/tail boundaries, and
  truncation marker without any external summary provider.

## 2026-06-25 - Phase 10 Batch J Selection

- Residual row `26, 27, 29, 78` has a real code gap for session discovery
  pagination: current REST/MCP tools accept `limit`, but spec Section 14.10
  requires `page_size`, `page_token`, `next_page_token`, and no silent
  truncation.
- `S24-78` best-guess semantics already have behavioral tests, but Batch J must
  keep them green while adding pagination.
- `S24-29` appears mostly implemented through discovery metadata allowlisting,
  but lacks an explicit no-leak contract test for not-found guidance.

## 2026-06-25 - Phase 10 Batch J Result

- `resolve_session` and `list_sessions` now support canonical `page_size` and
  `page_token`, return `next_page_token` and `matches_truncated`, and retain
  legacy `limit` as a compatibility alias.
- Session discovery pagination is stable over the existing visible filtered
  result set and avoids silent truncation.
- Not-found guidance now has explicit test evidence that candidate sessions are
  scoped by token visibility and discovery metadata remains allowlisted/redacted.

## 2026-06-25 - Phase 10 Batch K Selection

- Residual row `59, 84` needs provider-call boundary enforcement for
  readiness: `require_evidence=false` is already provider-free, but
  `require_evidence=true` with a query currently uses `hybrid_context_search`
  with `embedding_index` whenever embeddings are configured.
- Batch K will make provider calls opt-in for readiness and expose
  `provider_calls_allowed` / `provider_calls_used` in readiness checks.

## 2026-06-25 - Phase 10 Batch K Result

- Readiness provider calls are now explicitly gated: `allow_provider_calls=false`
  uses local keyword/recency retrieval, while `allow_provider_calls=true` keeps
  the provider-backed vector/rerank path available.
- Tests prove both sides of the boundary: lexical evidence succeeds without a
  new provider call, semantic-only evidence fails without opt-in, then succeeds
  with opt-in and records provider-call usage.

## 2026-06-25 - Phase 10 Batch L Selection

- During the final verification matrix pass, JSON session export was found to
  include `audit_records` by default even though Section 14.2 requires
  `include_audit=false` as the default.
- Existing memory-read tests rely on exported audit evidence and should switch
  to explicit `include_audit=true`, preserving the evidence path while proving
  the default is safe.

## 2026-06-25 - Phase 10 Batch L Result

- JSON session export now defaults to `audit_records: []`.
- Explicit `include_audit=true` preserves authorized audit evidence for REST and
  MCP memory-read tests.
- The grouped Section 24 row `2, 3, 48, 49, 91, 92` remains partial only for
  broader lifecycle edge semantics, not for audit inclusion policy.

## 2026-06-25 - Phase 10 Batch M Selection

- Spark Section 24 and top-level CM audits both identified S24-44/CM-041 as a
  small localized residual: trace and cost endpoints exist but are not typed in
  OpenAPI.
- Initial local inspection confirms `/v1/traces/{trace_id}` and
  `/v1/costs/session/{session_id}` currently return raw `dict[str, Any]`
  without `response_model` bindings.

## 2026-06-25 - Phase 10 Batch M Result

- `/v1/traces/{trace_id}` now advertises `TraceResponse` and
  `/v1/costs/session/{session_id}` advertises `CostReportResponse` in OpenAPI.
- Response models are compatibility-flexible to preserve existing trace/cost
  runtime payloads while providing concrete schema refs and shared error
  envelope docs.
- S24-44 is now compliant; cost baseline methodology remains tracked under
  S24-38/45.

## 2026-06-25 - Phase 10 Batch N Selection

- The grouped audit row `32, 33, 34, 73, 98, 105, 118` is still partial
  because S24-33 requires audit disabling to be daemon-config-only and
  test-only.
- Current implementation has no visible public per-call audit bypass, but also
  no explicit `DISABLED_TEST_ONLY` daemon config/validation path.

## 2026-06-25 - Phase 10 Batch N Result

- Added daemon-level audit modes `FULL`, `TRACE_ONLY`, and
  `DISABLED_TEST_ONLY`.
- Production/default settings reject `DISABLED_TEST_ONLY` unless
  `MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS=true` or equivalent explicit test
  daemon config is present.
- Public REST/MCP payload fields such as `disable_audit` or `audit_mode` do not
  disable memory-read audit in normal mode.

## 2026-06-25 - Phase 10 Batch O Selection

- S24-38 is already backed by cost-mode downgrade/strict-failure tests.
- S24-45 remains narrow: `Store.cost_report()` exposes
  `provider_prompt_tokens_without_mneme_estimate` but does not wrap it in an
  explicit `baseline.methodology`/counterfactual contract field.

## 2026-06-25 - Phase 10 Batch O Result

- Cost reports now include explicit `period`, `usage`, `provider_breakdown`,
  and `baseline` fields.
- The baseline object marks
  `provider_prompt_tokens_without_mneme_estimate` as `COUNTERFACTUAL`, uses
  methodology `UNKNOWN`, and carries `savings_claim=false`.
- Poincare's read-only Spark audit was correct: S24-38 was already behaviorally
  covered, while S24-45 needed the explicit baseline-methodology contract.
- `llm_enrichment_tokens` is intentionally reported as `0` because current
  enrichment metrics track calls/failures only, not token counts.

## 2026-06-25 - Phase 10 Batch P Selection

- Spark context-prepare audit found S24-18, S24-20, S24-21, S24-22, S24-55,
  S24-69, S24-70, S24-89, and S24-99 already have code/test evidence.
- S24-19 remains a test-proof residual only: `mneme_service/app.py` appears to
  cascade unused execution-state budget to protected tail and retrieved
  evidence, but there is no focused regression asserting that cascade.

## 2026-06-25 - Phase 10 Batch P Result

- Added the focused S24-19 regression without runtime changes.
- The existing trace fields were sufficient: `execution_state_budget_tokens`,
  `execution_state_tokens`, `protected_tail_budget_tokens`,
  `retrieved_evidence_budget_tokens`, and trace-selected events.
- The context-prepare grouped Section 24 row is now compliant. The session
  lifecycle/export grouped Section 24 row was also moved to compliant based on
  Spark read-only audit and existing tests.

## 2026-06-25 - Phase 10 Batch Q Selection

- Storage/concurrency audit found a mix of broad residuals and already-covered
  behavior. S24-113 is the smallest safe next slice: existing code maps
  `WriterQueueFull` to retryable `429 RATE_LIMITED`, but the public contract
  lacks a dedicated saturation test.

## 2026-06-25 - Phase 10 Batch Q Result

- S24-113 now has a dedicated public contract test.
- The storage/concurrency grouped Section 24 row remains partial for broader
  residuals: previous-version migration fixture, successful-batch visibility,
  startup read-only/fail-closed nuance, and background scheduler priority beyond
  the current reindex-focused evidence.

## 2026-06-25 - Phase 10 Batch R Selection

- Spark read-only audits found two small Section 24 residuals suitable for a
  test-proof batch:
  - S24-25 lacked a direct scoped-token `GLOBAL` search proof without an
    explicit `X-Mneme-Project-Isolation-Key` header.
  - S24-58 lacked a direct batch-first streaming burst ingestion proof.
- Both residuals were narrow enough to close without production changes if the
  existing behavior already matched the contract.

## 2026-06-25 - Phase 10 Batch R Result

- Added `tests/test_retrieval.py::test_global_scope_respects_project_isolation_for_scoped_token_without_header`.
- Added `tests/test_contract.py::test_event_ingest_batch_first_handles_streaming_bursts`.
- The initial S24-58 test failure was a test-ordering issue, not a partial
  write bug: `context_search` creates a memory-read audit event before the
  final export. The final assertion now checks expected burst ids and absence
  of oversized ids rather than total export count after audit creation.
- Section 24 rows `25, 64` and `58` are now marked `COMPLIANT` in the matrix.

## 2026-06-25 - Phase 10 Batch S Selection

- Section 24 row `43, 85` remained partial because OpenAPI was parseable and
  broadly typed, but core success/error examples and public schemas for
  `/v1/turns/complete` and `/v1/context/prepare` were not machine-checked.

## 2026-06-25 - Phase 10 Batch S Result

- Added OpenAPI component schemas/examples for turn completion and context
  prepare without changing runtime payload parsing.
- Added success/error examples for core public schemas including
  `ErrorEnvelope`, `ToolResponseEnvelope`, session start, event batch, turn
  completion, and context prepare.
- Section 24 row `43, 85` is now marked `COMPLIANT` in the matrix.

## 2026-06-25 - Phase 10 Batch T Selection

- The retention grouped Section 24 row still had multiple residuals. Startup
  automatic retention sweep was the smallest implementation slice because
  explicit cleanup, session-close sweep, audit, metrics, and blob GC primitives
  already existed.

## 2026-06-25 - Phase 10 Batch T Result

- Added a startup retention sweep hook gated by `retention_sweep_on_startup`.
- Startup sweeps run only ended sessions, skip active sessions, reuse scoped
  cleanup/blob-GC primitives, and write `SYSTEM_DAEMON` audit records with
  `trigger=STARTUP`.
- S24-67 is improved but the grouped retention row remains `PARTIAL` because
  periodic sweep timer and forced active cleanup in-flight-read conflict
  tracking remain separate residuals.

## 2026-06-25 - Phase 10 Batch U Selection

- The retention grouped Section 24 row still needed S24-86 forced active
  cleanup conflict behavior for in-flight memory reads.
- This was a bounded slice because memory reads already funnel through
  `audit_memory_tool()` and retention cleanup already has the active-session
  force guard.

## 2026-06-25 - Phase 10 Batch U Result

- Added `InFlightReadTracker` and attached it to `app.state`/`store`.
- `audit_memory_tool()` now enters the tracker while persisting memory-read
  traces/audits/events/state summaries.
- Forced active retention cleanup now returns `409 CONFLICT` with
  `details.reason=IN_FLIGHT_READS` when the same session has in-flight reads.
- S24-86 is now covered; the grouped retention row remains `PARTIAL` only for
  periodic sweep coverage.

## 2026-06-25 - Phase 10 Batch V Result

- Audited provider/readiness/reindex grouped Section 24 row
  `37, 39, 68, 75, 87, 111`.
- Existing tests cover minimal provider-free mode, enabled provider missing-key
  startup failure, readiness `require_evidence=false` no-provider-call behavior,
  provider failure marking derived embedding status `FAILED`, and reindex cancel
  stop/final-state/idempotency behavior.
- Real provider smoke remains release-gated when release notes claim live
  provider readiness; it is not a required public CI blocker for the grouped
  Section 24 row.

## 2026-06-25 - Phase 10 Batch W Result

- Audited retention grouped Section 24 row `46, 50, 67, 74, 86`.
- The canonical spec makes startup and session-close retention sweeps mandatory
  (`MUST`) while the periodic timer is `SHOULD`.
- Existing Batch T/U evidence covers mandatory automatic sweeps, active-session
  skip, owner force rules, and in-flight read conflicts, so the grouped Section
  24 row is now `COMPLIANT`.

## 2026-06-25 - Phase 10 Batch X Result

- The final Section 24 `PARTIAL` row was storage/concurrency row
  `40, 41, 42, 56, 65, 71, 82, 113`.
- The matrix referenced `tests/test_contract.py::test_storage_busy_returns_retryable_503`,
  but the test did not exist yet; runtime already had `StorageBusy` mapped to
  retryable `503 STORAGE_BUSY`.
- Added the missing public REST contract test and confirmed focused
  storage/concurrency verification passes.
- The previous-version migration fixture is not a v0 Section 24 blocker because
  Section 23 requires it once there is a first published schema migration and
  before stable release.
- Successful batch visibility is covered by export/search assertions in the
  streaming-burst ingestion test, and foreground priority/yield is covered by
  the reindex micro-transaction test.

## 2026-06-25 - Phase 10 Batch Y Result

- Audited early top-level matrix rows `CM-002` through `CM-017`.
- Reclassified stale rows `CM-004`, `CM-007`, and `CM-015` to `COMPLIANT`
  because retention/metrics/direct segments, MCP default-session/session
  resolution, and architecture-level maintenance/reindex/metrics evidence are
  now implemented and tested.
- Left `CM-002`, `CM-003`, `CM-005`, `CM-009`, `CM-012`, `CM-013`,
  `CM-014`, and `CM-017` as `PARTIAL` because their remaining gaps are broader
  acceptance, release-material, adapter-depth, lifecycle, provider-quality, or
  config-parity issues.
- Updated the matrix summary counts to `COMPLIANT: 18`, `PARTIAL: 46`,
  `OUT_OF_SCOPE/FUTURE: 1`; all Section 24 grouped rows remain compliant.

## 2026-06-25 - Phase 10 Batch Z Result

- Audited middle top-level matrix rows `CM-019` through `CM-030`.
- Reclassified stale rows `CM-019`, `CM-020`, `CM-021`, `CM-022`, `CM-024`,
  `CM-026`, and `CM-027` to `COMPLIANT` because project isolation, provider
  modes/cost modes, budget semantics, session/event schemas, execution-state
  history, and control request/result schemas are now covered by current tests.
- Left `CM-023`, `CM-025`, `CM-028`, `CM-029`, and `CM-030` as `PARTIAL`
  because their remaining message-schema, turn-derived-state, audit-lifecycle,
  graph-edge taxonomy, and entity-modifier lifecycle gaps are real.
- Updated matrix summary counts to `COMPLIANT: 25`, `PARTIAL: 39`,
  `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AA Result

- Audited REST/runtime top-level matrix rows `CM-033` through `CM-048`.
- Reclassified stale rows `CM-034`, `CM-035`, `CM-036`, `CM-038`, `CM-042`,
  `CM-047`, and `CM-048` to `COMPLIANT`.
- Left `CM-033`, `CM-037`, `CM-039`, `CM-040`, `CM-045`, and `CM-046` as
  `PARTIAL` because backup/restore, turn-derived updates, routing/entity
  lifecycle, segment lifecycle, context-search trace/refill, and graph edge
  taxonomy gaps remain real.
- Spark flagged CM-036 as conservative `PARTIAL`, but the canonical Section
  14.3 adapter batching language is `SHOULD`; daemon-side batch acceptance,
  export/search visibility, oversize rejection, and no partial oversized writes
  are covered by `test_event_ingest_batch_first_handles_streaming_bursts`.
- Updated matrix summary counts to `COMPLIANT: 32`, `PARTIAL: 32`,
  `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AB Result

- Audited final top-level matrix rows `CM-051` through `CM-065`.
- Reclassified stale rows `CM-051`, `CM-052`, `CM-054`, `CM-058`, `CM-059`,
  and `CM-062` to `COMPLIANT` because current audit/MEMORY_READ,
  threat-boundary, prompt-injection wrapper, OpenAPI, error-envelope, and
  Section 24 evidence satisfies the row-specific v0 requirements.
- Left `CM-053`, `CM-055`, `CM-056`, `CM-057`, `CM-061`, `CM-063`, and
  `CM-065` as `PARTIAL` because redaction metadata/policy, at-rest protection,
  backup/restore, operations runbook/logging/cancellation, final acceptance,
  traceability packet, and approval-gate work remain real.
- Spark returned a more conservative recommendation for several rows. Parent
  review accepted the conservative residuals where they map to real hardening
  or final acceptance rows, but did not keep runtime/contract rows partial only
  for reviewer-packet or future SDK polish covered elsewhere.
- Updated matrix summary counts to `COMPLIANT: 38`, `PARTIAL: 26`,
  `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AC Result

- Closed the narrow `CM-023` message-schema residual.
- Added typed OpenAPI schemas for `mneme.message.v0` and typed content parts,
  plus runtime validation for allowed message roles and content-part types.
- Added richer `mneme.turn.v0` completion request schema fields. This narrows
  `CM-025`, but does not close it because derived state, segment, graph-edge,
  provider metric, and usage-counter updates remain real turn-completion work.
- Matrix summary now moves to `COMPLIANT: 39`, `PARTIAL: 25`,
  `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AD Result

- Closed the narrow turn-completion segment-linkage subgap in `CM-025` and
  `CM-037`.
- `POST /v1/turns/complete` now resolves segment ids from completed turn
  `event_ids`, falls back to the active segment only when necessary, and no
  longer reports only synthetic `segment-{session_id}` ids.
- `Store.put_turn()` now merges last-turn metadata into the linked segment
  without replacing existing segment lifecycle fields.
- Remaining `CM-025`/`CM-037` gaps are execution-state transition,
  graph/provenance edges, provider metrics, and broader usage-counter semantics.

## 2026-06-25 - Phase 10 Batch AE Result

- Closed the narrow turn-completion execution-state/history subgap in
  `CM-025` and `CM-037`.
- `POST /v1/turns/complete` now writes a state/history update with
  `current_step="Turn {turn_id} {status}"`, `TURN_{status}` intent label, and
  provenance `{"turn_id": ..., "source": "turn_complete"}`.
- Remaining `CM-025`/`CM-037` gaps are graph/provenance edges, provider
  metrics, and broader usage-counter semantics.

## 2026-06-25 - Phase 10 Batch AF Result

- Closed the narrow turn-completion graph/provenance subgap in `CM-025` and
  `CM-037`.
- `POST /v1/turns/complete` now emits an idempotent canonical
  `TURN_COMPLETE` event whose `parent_event_ids` point at completed turn event
  ids; existing graph-edge insertion then exports parent-derived `FOLLOWS`
  edges.
- Touched-area verification passed:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_graph.py -q -k "turn_complete or graph or edge"`
  -> `11 passed, 37 deselected, 1 warning`.

## 2026-06-25 - Phase 10 Batch AG Result

- Closed the remaining turn-completion provider/usage residual in `CM-025` and
  `CM-037`.
- Usage counters were already derived from persisted turns in cost reports;
  Batch AG added provider/model/cost aggregation into `provider_breakdown` when
  adapters provide provider metadata in turn `usage`.
- `CM-025` and `CM-037` are now `COMPLIANT`; matrix summary moved to
  `COMPLIANT: 41`, `PARTIAL: 23`, `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AH Result

- Closed the `SEGMENT_ANCHOR` subgap in `CM-029`, `CM-040`, and `CM-046`.
- Direct segment anchor ids were already validated and persisted, and graph
  scoring already recognized `SEGMENT_ANCHOR`; Batch AH added the missing edge
  producer in segment persistence.
- Because the current graph schema is event-to-event rather than segment-node
  based, direct multi-anchor segments now use the first anchor event as the
  segment-anchor root and link remaining anchor events with `SEGMENT_ANCHOR`
  edges.
- `CM-029`, `CM-040`, and `CM-046` remain `PARTIAL` pending broader edge
  taxonomy/frontier/lifecycle coverage.

## 2026-06-25 - Phase 10 Batch AI Result

- Closed the remaining `CM-040` direct segment lifecycle residual.
- `POST /v1/segments/{segment_id}/close` now maps `ABANDONED` and
  `SUPERSEDED` outcomes to matching terminal public segment statuses while
  preserving `CLOSED` for other close outcomes.
- `rest_segment()` exposes `closed_at` for all terminal non-`OPEN` statuses.
- `CM-040` is now `COMPLIANT`; matrix summary moved to `COMPLIANT: 42`,
  `PARTIAL: 22`, `OUT_OF_SCOPE/FUTURE: 1`.

## 2026-06-25 - Phase 10 Batch AJ Result

- Narrowed the `CM-029` and `CM-046` graph traversal residuals.
- `expand_graph()` now receives and enforces configured
  `graph_max_traversal_steps`, `graph_max_frontier_size`, and
  `graph_max_branching_factor` limits.
- Hard traversal cap hits produce `TRAVERSAL_LIMIT_REACHED` warning details
  while existing `MAX_EVENTS`/depth behavior remains compatible with current
  tests.
- Remaining graph residuals are mode-specific traversal semantics,
  `RESULT_TRUNCATED`/`dropped_count` detail, and complete edge taxonomy.

## 2026-06-25 - Phase 10 Batch AK Result

- Narrowed the `CM-046` max-events truncation residual.
- Graph-mode `expand_context` now returns `RESULT_TRUNCATED` warning details,
  `dropped_count`, and a minimal frontier summary when `max_events` truncates
  traversal.
- The implementation keeps the legacy `GRAPH_TRAVERSAL_LIMIT_REACHED` warning
  first for compatibility and appends the spec-required `RESULT_TRUNCATED`
  warning.
- Remaining `CM-046` residuals are mode-specific traversal semantics and full
  edge-completeness coverage.

## 2026-06-25 - Phase 10 Batch AL Result

- Narrowed the `CM-029`/`CM-046` mode-specific traversal residuals.
- `POST /v1/tools/expand_context` now has explicit `TEMPORAL` mode semantics:
  the seed event is returned first, followed by nearest previous events in
  reverse timestamp order and next events in timestamp order, without requiring
  graph edges.
- The temporal mode returns the same response-shape fields used by graph mode,
  including truncation metadata when `max_events` cuts off timestamp neighbors.
- Remaining graph residuals are `TOOL_CHAIN`/`CAUSAL` mode-specific semantics
  and full edge-completeness coverage.

## 2026-06-25 - Phase 10 Batch AM Result

- Narrowed the `CM-029`/`CM-046` graph-mode residuals.
- `expand_context` now threads request mode into graph expansion and applies
  mode-aware neighbor planning for `TOOL_CHAIN` and `CAUSAL`.
- `TOOL_CHAIN` prioritizes tool-result/tool-input style edges before ordinary
  parent/child flow and downstream decisions. `CAUSAL` orders relevant graph
  neighbors by edge weight, then event time, then event id.
- Remaining graph residual is edge-completeness: explicit `TOOL_INPUT` coverage
  and richer parent/child edge taxonomy/weights are not fully materialized yet.

## 2026-06-25 - Phase 10 Batch AN Result

- Narrowed the `CM-029`/`CM-046` graph edge taxonomy residuals.
- Explicit `parent_event_ids` now generate canonical `PARENT_CHILD` graph edges
  with the Section 12.8 default weight `0.9` instead of generic temporal
  `FOLLOWS` edges with weight `1.0`.
- `TOOL_CHAIN` and `CAUSAL` graph expansion allow-lists now include
  `PARENT_CHILD`.
- Remaining graph edge-completeness residuals are explicit `TOOL_INPUT` and
  `SEGMENT_MEMBER` coverage.

## 2026-06-25 - Phase 10 Batch AO Result

- Closed the `CM-045` context-search residual.
- `context_search` retrieval traces now include additive candidate breadth
  metadata: raw candidate count, unique candidate count, per-source counts, and
  bounded candidate ids by source.
- When selected results underfill `top_k`, context search now adds explicit
  scoped `RECENCY_REFILL` results with a matching strategy and warning instead
  of silently returning a short result set.
- Existing freshness behavior remains explicit: source-supplied `CURRENT`
  conflicts still drop conflicting stale evidence, and unrelated old evidence is
  not auto-marked stale.

## 2026-06-25 - Phase 10 Batch AP Result

- Closed the `CM-029`/`CM-046` graph edge taxonomy and edge-completeness
  residuals.
- Parent message → `TOOL_CALL` relations now produce derived `TOOL_INPUT` graph
  edges with weight `1.0`. This is the v0 representation because the approved
  event schema does not define a distinct persisted tool-input event type.
- Automatic segmentation updates now write `SEGMENT_MEMBER` edges from the
  segment representative root event to subsequent automatic segment member
  events with weight `0.5`.
- The segment-member write is intentionally limited to events returned by the
  automatic segmentation update path; broader active-segment fallback was tested
  and rejected because it introduced graph traversal shortcuts for unrelated
  depth/max-events tests.

## 2026-06-25 - Phase 10 Batch AQ Result

- Narrowed the `CM-053` redaction residual.
- Event-ingest foreground redaction now records internal
  `ingestion.redaction_metadata` only when redaction occurs.
- Metadata entries include `kind`, stable `field` path, and a `sha256` hash of
  the original value; they do not store plaintext secrets.
- The helper preserves existing timeout behavior by reusing `redact_text()`.
- Remaining `CM-053` residual is explicit extractor policy for text extraction
  from non-text blobs.

## 2026-06-25 - Phase 10 Batch AR Result

- Closed the remaining `CM-053` extractor-policy residual.
- Added explicit `binary_blob_extractor_policy` config, defaulting to
  `DISABLED`, with TOML/env loading and validation.
- Capabilities expose the active policy, and non-text BYTES_REF event ingestion
  records `ingestion.extractor_policy` together with
  `redaction_scope=BINARY_METADATA_ONLY`.
- This makes the default v0 behavior explicit: non-text blob bytes are not
  text-extracted or sent to providers unless a future explicit policy enables a
  safe extractor path.

## 2026-06-25 - Phase 10 Batch AS/AT Findings

- Batch AS closed the `CM-009` context-prepare cost-mode sub-residual:
  `/v1/context/prepare` now uses the same `QUALITY` downgrade/strict-failure
  resolver as `/v1/sessions/start`.
- `COST_MODE_DOWNGRADED` is now a provider `QUALITY` warning, not a generic
  `STANDARD` char-approx warning. Model-bound char-approx rejection remains
  covered separately.
- Batch AT found and fixed a neighboring readiness regression introduced by
  explicit `RECENCY_REFILL`: readiness with a query must not accept
  query-unrelated refill events as evidence. The fix disables refill only for
  readiness query checks while preserving explicit context-search refill.
- Spark audit `019effdf-0bb8-7643-92e4-277edd948cc7` found `CM-028` remains a
  real residual: audit/forensic retention config exists, but runtime cleanup of
  aged forensic audit anchors is not enforced yet.

## 2026-06-25 - Phase 10 Batch AU Findings

- Closed the `CM-028` forensic retention residual.
- `Store.purge_forensic_anchors_older_than()` deletes only anonymized forensic
  anchors whose `created_at_ms` is older than the configured retention window;
  ordinary live-session audit records are not touched by this primitive.
- `create_app()` now runs forensic-anchor retention cleanup on startup using
  `settings.audit_forensic_retention_days`, giving the policy a deterministic
  runtime enforcement point without adding a new public API surface.

## 2026-06-25 - Phase 10 Batch AV Findings

- Closed the remaining `CM-009` provider-status residual.
- Provider `last_health` is now a structured process-local snapshot derived
  from observed provider outcomes, not a static `"UNKNOWN"` string.
- Health tracking wraps embedding, reranker, and LLM enrichment providers,
  including injected test providers, without adding live health probes or
  network calls.
- The v0 scope is intentionally process-lifetime health reporting; persistence
  across restarts is not required by the current spec and would be a future
  operations hardening item.

## 2026-06-25 - Phase 10 Batch AW Findings

- Narrowed `CM-017` by adding env/serve-CLI parity for
  `max_writer_queue_depth`.
- `MNEME_MAX_WRITER_QUEUE_DEPTH` now participates in the same precedence chain
  as TOML and CLI overrides, and `mneme serve --max-writer-queue-depth` maps to
  `Settings.max_writer_queue_depth`.
- Remaining `CM-017` residuals are broader later-phase config parity and
  runtime enforcement items, especially periodic/background maintenance
  behavior.

## 2026-06-25 - Phase 10 Batch AX Findings

- Narrowed `CM-033` and `CM-056` by adding a verified SQLite backup/restore
  path.
- `Store.backup_to()` uses SQLite's backup API and validates the produced
  backup with `PRAGMA integrity_check`, schema/user-version checks, migration
  version checks, and per-blob `sha256:` hash recomputation against
  `blobs.content`.
- `Store.restore_from_backup()` validates the source backup before writing the
  target, verifies the restored DB after copy, and removes partial target files
  if copy/post-verify fails.
- `mneme maintenance backup --db ... --output ...` and
  `mneme maintenance restore --backup ... --target ...` expose the primitive
  through a CLI surface without changing public REST contracts.
- This closes the backup/restore sub-residual but does not by itself close
  broader destructive-migration controls, periodic/background GC, or final
  release runbook evidence.

## 2026-06-25 - Phase 10 Batch AY Findings

- Narrowed `CM-055` at-rest protection by implementing the local POSIX
  filesystem permission guidance for SQLite storage.
- `Store` now enforces owner-only mode on its SQLite database parent directory
  (`0700`) and database file (`0600`) after initialization.
- The behavior is intentionally POSIX-only best effort; non-POSIX platforms
  keep startup compatibility rather than failing on unsupported mode semantics.
- This complements existing env/token-file protections but does not close
  optional SQLCipher/OS-encrypted volume documentation or broader
  derivative-retention evidence.

## 2026-06-25 - Phase 10 Batch AZ Findings

- Closed `CM-055`.
- Retention cleanup evidence now explicitly covers linked derived rows:
  `embedding_index`, `event_graph_edges`, `traces`, and `state_history` for
  eligible old events.
- `docs/INSTALLATION.md` now includes the required Section 17.4 guidance:
  configured SQLite database path, no default external blob path, recommended
  `0600` file and `0700` data-directory modes, optional OS-encrypted
  volume/SQLCipher strategy, and no enterprise-confidentiality claim for the
  default local SQLite runtime.
- First-class SQLCipher/keychain integration remains future per Section 17.4,
  not an open v0 implementation gap.

## 2026-06-25 - Phase 10 Batch BA Findings

- Narrowed `CM-033` and `CM-057` by adding the missing Section 13.6 CLI
  explicit blob-GC trigger.
- `mneme maintenance blob-gc --db ...` now dispatches to the same
  `Store.garbage_collect_blobs()` primitive covered by REST blob-GC tests.
- The command supports dry-run by default, `--execute`, optional
  `--project-isolation-key`, and optional `--session-id`.
- This closes the CLI trigger sub-residual; structured logging breadth,
  stop/restart semantics, periodic/background maintenance evidence, and final
  runbook evidence remain tracked separately.

## 2026-06-25 - Phase 10 Batch BB Findings

- Narrowed `CM-057` by adding test-guarded operations runbook guidance.
- `docs/INSTALLATION.md` now states that config changes require daemon restart,
  in-flight requests may be interrupted during stop/restart, retryable failures
  should be retried, and mutating calls should use `Idempotency-Key`.
- `docs/TESTING_AND_CI.md` now includes an operations runbook smoke checklist
  covering restart, in-flight interruption, retry/idempotency, and structured
  log fields.
- Remaining `CM-057` work is code-level structured logging breadth and final
  release/reviewer runbook evidence.

## 2026-06-25 - Phase 10 Batch BC Findings

- Closed `CM-057`.
- Mneme now emits safe structured HTTP access logs through
  `mneme_service.access`.
- Each log record includes request id, optional trace id, method, endpoint,
  status, error code, safe project/session scope metadata, latency, and
  background job id; it does not log bearer tokens or request/response bodies.
- Final reviewer packet and fresh full-suite evidence remain tracked by
  `CM-061`, `CM-063`, and `CM-065`, not as a row-specific Section 19 gap.

## 2026-06-25 - Phase 10 Batch BD Findings

- Closed `CM-033`.
- After Batch AX backup/restore and Batch BA CLI blob-GC, the remaining
  `CM-033` matrix gap was stale: Section 13.6 required explicit REST/CLI,
  startup/session-close/retention cleanup triggers and no unimplemented
  background-GC overclaim.
- Periodic/background maintenance evidence remains relevant to broader
  operations/final acceptance only, not as an open blob-lifecycle row gap.
## 2026-06-25 - CM-056 destructive migration closure

- Section 18 requires startup to create a backup or require explicit `--no-backup-before-migrate` before destructive migrations.
- The implemented v0 schema has no built-in destructive migration today, so tests inject a destructive migration marker for a supported previous version and verify both paths: fail-closed without backup/bypass, verified backup before migration, and explicit operator bypass.
- Release/runbook evidence now lives in `docs/INSTALLATION.md` under "Migration And Release Notes"; it names tested Python versions, migration impacts, `--backup-before-migrate`, and `--no-backup-before-migrate`.
## 2026-06-25 - CM-017 config parity narrowing

- Spark audit found a broad but separable `CM-017` gap: many existing `Settings` fields were TOML-only or not exposed through `mneme serve` CLI.
- Batch BF intentionally covered only fields that already existed in `Settings`; it did not add new routing/provider-policy config models.
- Remaining `CM-017` risk: Section 8 routing/provider policy keys and additional periodic/background validation may require explicit modeling decisions rather than mechanical env/CLI mapping.
## 2026-06-25 - CM-013/CM-014 integration depth

- Section 5 includes six levels, not four: `TOOLS_ONLY`, `EVENT_INGEST`, `PREPARE_INPUT`, `CONTEXT_ENGINE`, `COMPACTION_OWNER`, and `FULL_RUNTIME`.
- Codex hooks currently write sessions/events but do not call `/v1/turns/complete`; they must not be advertised as full `EVENT_INGEST`.
- Batch BG resolved this by declaring core REST lifecycle support as `EVENT_INGEST` and Codex hook surfaces as tools/session-events-only unless a future production adapter proves the full lifecycle.
## 2026-06-25 - CM-030 deterministic entity lifecycle

- Existing classifier extraction was deterministic, but execution-state lifecycle was missing.
- Batch BH adds deterministic ADD/REPLACE/REMOVE application to `active_entities` and provenance in `enrichment.entity_modifiers`.
- While testing, the phrase `Use OAuthBridge instead of TokenBroker` exposed ambiguous existing classifier matches; the batch used the canonical `Replace TokenBroker with OAuthBridge` pattern and did not alter classifier semantics.
- Remaining `CM-030` scope is provider-backed extraction/reconciliation and provider-source audit policy.
## 2026-06-25 - CM-014 Codex hook lifecycle

- Codex hooks previously ingested sessions/events but did not complete turns; advertising them as `EVENT_INGEST` would have overclaimed Section 5.1.
- Batch BI adds `/v1/turns/complete` for trusted `Stop` hook imports with `turn_id`, making the hook lane a complete EVENT_INGEST lifecycle for the implemented Codex surface.
- Context-engine behavior remains unclaimed; preview-only context prepare is still not host pre-model-request prompt authority.
## 2026-06-25 - CM-039 topic entropy residual

- Section 14.5.1 defines `topic_entropy` as a normalized deterministic drift-score component based on topic tags or retrieved evidence buckets; it may be `0` when no tags/buckets exist.
- Current ingest already traces drift weights/components and trusted tool-domain shift, but `topic_entropy` is hardcoded to `0.0`.
- Batch BJ will add only a deterministic lexical fallback signal for current user-message text; provider-backed topic extraction and broader routing policy remain tracked separately by `CM-039`/`CM-030`.
## 2026-06-26 - CM-039 topic entropy narrowing

- Batch BJ replaced the hardcoded `topic_entropy: 0.0` placeholder with deterministic normalized lexical entropy for user-message text.
- The existing trusted tool-domain drift trace now verifies nonzero `topic_entropy` and the resulting combined `drift_score` contribution.
- This narrows `CM-039`; it does not close broader routing/provider-policy config modeling or provider-backed extraction lifecycle gaps.
## 2026-06-26 - CM-005 structured history audit

- Spark read-only audit plus parent review found `CM-005` to be stale after later storage, audit, retention, migration, backup, and maintenance work.
- Structured history now includes sessions, events, turns, execution state/history, segments, graph edges, blobs, traces, rich audit records, schema migration history, retention cleanup metadata, startup sweeps, and operational metrics.
- The spec's migration-from-previous-version fixture is required before stable only after a first published schema migration exists, so it is not a current `BR-1` implementation blocker.
## 2026-06-26 - CM-002/CM-003 top-level audit

- `CM-002` remains a final-acceptance umbrella dependency because unresolved `CM-017`, `CM-030`, `CM-039`, `CM-061`, `CM-063`, and `CM-065` still prevent claiming full v0 contract breadth.
- `CM-003` has a concrete docs/release-boundary gap: package discovery excludes adapters, but the core README still presents Codex adapter docs in the release-facing flow.
- Batch BM will keep the development-checkout adapter guidance while making the core README boundary explicit and test-backed.
## 2026-06-26 - CM-003 release boundary closure

- Batch BM removed the core README's adapter-doc link list and added a test that prevents Codex adapter docs/commands from reappearing in the core release-facing README.
- The development checkout may still mention that adapter work exists locally, but public engine/core and Codex adapter repos/packages are documented as separate.
- `CM-003` is now closed; final reviewer/release packet evidence remains tracked by `CM-063`/`CM-065`.
## 2026-06-26 - CM-017/CM-039 routing config audit

- Spark read-only audit found a real shared residual: `retrieval.routing` policy is hardcoded in runtime constants rather than modeled end-to-end in `Settings`.
- Provider-backed/reindex lifecycle evidence appears mostly present and should not block `CM-039` once routing config parity is fixed.
- Batch BO will implement only default-mode/weights config propagation and validation, avoiding broader provider extraction redesign.
## 2026-06-26 - CM-017/CM-039 routing config closure

- Batch BO added first-class `routing_default_mode` and `routing_mode_weights` settings with TOML/env/serve CLI coverage and validation for mode names, required weight keys, non-negative values, and `1.0 +/- 0.01` sums.
- `context_search` now uses configured default mode and configured score weights in retrieval traces/score breakdowns; explicit request mode remains supported.
- Parent review fixed partial TOML weight handling so user-specified `[retrieval.routing.weights.<mode>]` tables overlay defaults instead of deleting other supported modes.
- `CM-030` still tracks provider-backed entity extraction/reconciliation; it should not double-block `CM-039` after deterministic/config-driven routing is complete.
## 2026-06-26 - CM-030 deterministic delta extraction closure

- Section 14.5.1 makes delta extraction optional in v0; if enabled, it must produce deterministic `mneme.entity_modifier.v0` objects and update only `execution_state.active_entities`.
- Batch BH already implemented deterministic extraction/application/provenance; Batch BP adds explicit capabilities reporting for deterministic support and provider-guarded extraction disabled policy.
- Provider-assisted extraction remains allowed only when explicitly configured in a future slice; it is no longer an open v0 blocker for `CM-030`.

## 2026-06-26 - Final acceptance closure

- Final verification passed after Batch BR fixed two stale trace assertions:
  full pytest `332 passed, 1 warning`; compileall exit 0; OpenAPI gate
  `10 passed, 1 warning`; `git diff --check` exit 0.
- `docs/MNEME_V0_REVIEWER_PACKET.md` now consolidates canonical spec,
  compliance matrix, verification log, planning evidence, explicit non-goals,
  and reviewer disposition.
- Final matrix counts are `COMPLIANT: 64`, `PARTIAL: 0`, `MISSING: 0`,
  `OUT_OF_SCOPE/FUTURE: 1`; `CM-064` is the explicit non-goal/future row.
- `docs/MNEME_STANDALONE_SPEC.md` is modified relative to the repository's git
  baseline because the working tree contains the user-provided Final v0.7.5
  canonical spec rather than the older draft baseline. Treat the current file as
  the immutable source for this workflow unless the user explicitly authorizes a
  spec change; do not revert it as cleanup.

## 2026-06-27 - Phase 11 Core/Adapter Boundary Planning Findings

- `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` reached v0.5 and was
  accepted by the user as the ready specification for the Core/Adapter boundary
  refactor.
- Final v0.5 external approval evidence: Kimi, DeepSeek, and Owl returned
  `APPROVE`; GLM v0.5 was unavailable due repeated provider 429 after having
  approved v0.4.
- Existing v0 compliance `.planning/` remains the project planning root. Phase
  11 is added as an extension scope rather than replacing `.planning/spec.md`
  or erasing completed Phase 1-10 evidence.
- Mneme MCP session resolution for this workspace returned `NOT_FOUND`, so
  local `.planning/` files remain the recovery source for this transition.
- Phase 11 execution must not start until the new Extension Planning Gate is
  explicitly cleared by the user.

## 2026-06-27 - Phase 11 Task 01 Contract-Version Surface Findings

- Current Core version surfaces are duplicated: `mneme_service/__init__.py`
  defines `__version__ = "0.1.0"`, `create_app()` passes FastAPI
  `version="0.1.0"`, and `/v1/capabilities` returns
  `service_version: "0.1.0"`.
- `/v1/health` and `/v1/capabilities` response models do not yet include
  `mneme_contract_version`.
- `docs/MNEME_CONTRACT_VERSION` and `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md`
  are absent before Task 01 implementation.
- Runtime code should not depend solely on a repository-root `docs/` path when
  installed from a wheel; Task 01 will keep a package fallback constant and use
  tests plus later Phase 5 CI checks to enforce equality with the canonical docs
  file.

## 2026-06-27 - Phase 11 Task 02 Adapter Sync Findings

- No local standalone `mneme-codex-adapter` checkout existed under the searched
  local project scopes; the task cloned the public repository into
  `/private/tmp/mneme-codex-adapter-phase11`.
- Adapter tests had real drift against current Core:
  - `tests/test_codex_ingest.py` expected turn status `RECORDED`, but Core
    final turn-complete behavior returns `COMPLETED`.
  - `mneme_codex_adapter/hooks.py` used stale context-prepare budget keys
    `retrieved_context_ratio` and `recent_tail_ratio`; Core requires
    `retrieved_evidence_ratio` and `protected_tail_ratio`.
  - `tests/test_setup.py` assumed `com.mneme.codex.plist` is absent, which can
    be false on a developer machine with a real LaunchAgent installed.
- Adapter source had no private `mneme_service.*` imports, but tests still use
  Core public package imports to construct in-process ASGI test fixtures. The
  new import-boundary script scans adapter package source by default and ignores
  tests unless explicitly requested.
- The adapter package now declares `CORE_CONTRACT_RANGE = ">=0.7,<0.8"` and
  mirrors it in `[tool.mneme].supported_core_contract`; the drift-check script
  fails if Core OpenAPI `info.version` falls outside that range.
- Task 02 verification was initially local and durable through a saved
  patch/evidence file. Adapter publication was treated as a separate gate before
  any final release claim.
- Superseded 2026-06-27: the adapter patch was later committed and pushed to
  GitHub `main` as `bd69b15e5716bb7731256aeba85ae45963be399a`.

## 2026-06-27 - Phase 11 Task 03 Dependency Extraction Findings

- Core-side Codex logic is adapter-owned end to end: transcript parsing, hook
  normalization, context-preview request construction, setup/status/service
  helpers, command rendering, Codex docs/examples, and the `mneme-memory` skill.
- The audit found no `promote to Core` units. Generic behavior needed by the
  adapter is already represented by public REST/MCP contracts and OpenAPI.
- Task 04 must preserve generic Core coverage for sessions, events,
  turn-complete, context-prepare, OpenAPI schemas, Core CLI non-Codex commands,
  distribution boundaries, and Core docs pointer behavior before deleting
  Codex-specific tests/files.
- Historical compliance/reviewer docs may keep Codex references as evidence,
  but active Core package/docs/tests must not depend on Codex implementation.
## 2026-06-27 - Phase 11 Task 04 Build Cache And Local Build Tooling

- A stale generated `build/` cache can cause setuptools wheel builds to include
  deleted Core files such as `mneme_service/codex_*.py` even after those files
  are removed from the working tree. Task 04 verification must clean generated
  build cache before distribution-boundary checks.
- The project venv did not have the PyPA `build` CLI available, and network
  installation was unavailable. Local verification used the bundled Python's
  `setuptools.build_meta` backend to produce wheel/sdist artifacts in a
  temporary external artifact directory. CI still installs `build` explicitly.
- Boundary source-text checks should avoid false positives on neutral technical
  identifiers such as SQLite `cursor`; package/path checks remain strict for
  host-specific module and test names.

## 2026-06-27 - Phase 11 Task 05 Spark Limit And CI Guard Details

- A delegated Spark audit for Task 05 could not complete because the separate
  Spark usage limit was exhausted until 2026-06-29. Task 05 review and fixes
  were completed in the parent session.
- `scripts/host_boundary_policy.json` should stay on the approved four-key
  schema (`version`, `denylist`, `allowlist`, `exemptions`). False positives
  such as SQLite `cursor` are handled in the checker logic rather than by
  adding non-spec policy keys.
- The adapter patch evidence originally had AST import-boundary CI but not a
  required contract-drift CI step. Task 05 updated the adapter patch evidence
  so adapter CI generates a Core OpenAPI fixture from the installed Core
  dependency and runs `scripts/check_core_contract_drift.py`.
