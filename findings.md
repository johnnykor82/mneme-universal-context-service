# Findings & Decisions: Mneme Universal Context Service

## Requirements

- Build a vendor-neutral Mneme context service from the idea behind `hermes-mneme`.
- Keep the project isolated in `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`.
- Do not touch live Hermes at `/Users/openclaw/.hermes/hermes-agent`.
- Do not touch live `hermes-mneme` at `/Users/openclaw/.hermes/plugins/hermes-mneme`.
- Preserve REST and MCP contract clarity before adapter work.
- Preserve the distinction between the service contract and the host-side context-engine adapter contract.
- Use file-based planning (`task_plan.md`, `findings.md`, `progress.md`) to keep development systematic, controlled, traceable, and resumable.
- Future public GitHub publication remains a product constraint: installation
  and adapter setup should be clear, automatable where possible, and free of
  hidden dependencies on this workstation's private paths.
- GitHub publication must split the product into separate install surfaces:
  the Mneme engine/core repository first, then host-specific adapter
  repositories/packages such as a Codex adapter. Internal planning, dogfood
  prompts, local rehearsal files, and machine-specific notes should not be
  published as user-facing install artifacts.
- The user runs two Codex installs on different machines with shared files via
  symlinks. Mneme docs/installers must treat runtime setup as per-machine:
  daemon, MCP config, tokens, database, provider secrets, and hook trust do not
  automatically follow symlinked project files.
- Current next implementation target is Phase 14: Hermes-Mneme functional parity recovery.
- Provider configuration must be explicit before embeddings, reranking, or LLM enrichment are implemented.
- Embeddings are required for dogfood/public-readiness semantic memory because
  semantic search, topic centroids, and drift detection depend on stored
  vectors. Provider-free minimal mode is still useful for CI/dev/fallback
  tests, but it is not the quality target inherited from `hermes-mneme`.
- `hermes-mneme` parity must be considered before further Codex dogfood polish; the current universal service is not yet a functional replacement for the prototype context engine.
- Adapter work is paused until the universal daemon has semantic retrieval, execution state, segmentation/routing, and budgeted context assembly.
- Runtime-neutral session/topic drift semantics are daemon scope, not Hermes-adapter-only scope. Host adapters supply lifecycle metadata; the daemon decides segment drift, resume/fresh-session behavior, lineage/carry-over, and first-turn resume context fill.

## Research Findings

### Standalone Spec Review Consolidation Findings

- External reviewers repeatedly identified the same pre-implementation/spec
  gaps: `BYTES_REF` lacks a blob API/lifecycle, project isolation is not
  enforceable with one global bearer token, token passing through CLI args is
  unsafe, discovery tools may leak cross-project metadata, and SQLite schema
  migrations/concurrency are underspecified.
- The standalone spec must be honest about integration depth: Codex is
  currently `TOOLS_ONLY` unless trusted hooks/importers write events, while
  automatic prompt/context replacement requires host lifecycle hooks such as
  `prepare_model_request` or `assemble-before-prompt`.
- Provider behavior must be explicit: `cost_mode` is an intent, not a
  guarantee; capabilities and provider health decide whether the server fails
  closed, degrades with warnings, or refuses a request requiring missing
  providers.
- Reviewer feedback treats prompt injection through stored memory as a real
  design risk. The spec must define evidence isolation, rendering boundaries,
  source trust labels, and sanitization/non-execution rules without pretending
  that text warnings alone perfectly solve LLM prompt injection.
- The new reviewer-facing artifact should be a standalone specification rather
  than the current index-style `docs/MNEME_DEVELOPMENT_SPEC.md`, so reviewers
  can evaluate business requirements, architecture, API, security, operations,
  testing, known limitations, and traceability from a single file.
- Created `docs/MNEME_STANDALONE_SPEC.md` as draft v0.3. It explicitly covers
  blob/BYTES_REF API, project-scoped auth/isolation, safe token handling,
  insecure development mode, provider/cost-mode mapping, execution-state update
  API, manual segment boundaries, deterministic context expansion, fluid
  context budget packing, MCP/REST error mapping, migration/concurrency,
  OpenAPI, benchmark baselines, prompt-injection limitations, default redaction
  classes, and a reviewer concern coverage matrix.
- The standalone spec intentionally records several items as compliance gaps
  instead of pretending the alpha implementation already satisfies them. After
  approval, those gaps should become the implementation plan for bringing the
  plugin/core into spec compliance.
- The v0.4 review response tightens the spec without adding enterprise scope:
  local v0 auth is an owner token plus logical project isolation, with static
  scoped tokens only when multi-project sharing is enabled.
- Freshness is no longer presented as something Mneme can infer magically from
  memory age. `CURRENT` evidence must come from a host adapter/source connector
  that just verified the source of truth; Mneme core may only derive
  `RECENT`/`HISTORICAL` from timestamps without external verification.
- v0.4 makes SQLite BLOB storage the default ACID blob store and demotes
  filesystem/file URI blob storage to an experimental, trusted-path-gated
  adapter mode.
- v0.4 closes concrete API/schema review gaps: `mneme.audit_record.v0`,
  `/v1/traces/{trace_id}`, `/v1/costs/session/{session_id}`, explicit
  execution-state update request/response bodies, direct segment list/get
  endpoints, `source_trust`, `mcp_tool_versions`, and graph edge weights.
- v0.4 replaces vague or risky mechanics with testable ones: serialized SQLite
  writer lane instead of independent writer retries, fixed-slot context packing
  for v0, rejection/downgrade of `CHAR_APPROXIMATE` for STANDARD/QUALITY
  model-bound prepare, data-only prompt-injection wrappers, OpenAPI as REST
  source of truth, and MCP default-session injection when the host knows the
  current session.

### RLM Orchestrator Proposal Findings

- RLM Orchestrator should be treated as a separate product/repository, not as
  part of Mneme core. Mneme remains independently useful and becomes the
  required memory/evidence backend for the orchestrator.
- The orchestrator's core boundary is read-oriented: it can read Mneme, local
  files, git, controlled terminal output, read-only database query results,
  web/SearX MCP output, and external MCP knowledge sources. It must not modify
  project files, git state, user databases, configs, or external systems.
- The orchestrator may write only its own bounded run state under its own
  workspace directory. This is required from MVP 1 for progress visibility,
  crash recovery, deterministic resume, and auditability.
- All source adapters should be capability-gated and read-only by default.
  Source content is evidence, not instruction authority.
- Proposed MVP sequence: design/contract; read-only local+Mneme core;
  recursive workers/verifier/progress/resume; controlled terminal plus
  read-only DB access through command templates; web and external MCP knowledge
  sources; external agent interfaces; comparative benchmarks.
- A development spec for architecture review is recorded in
  `docs/RLM_ORCHESTRATOR_DEVELOPMENT_SPEC.md`.
- Architecture review feedback identified three MVP 1 blockers that are now
  resolved in the v0.2 draft: model/provider configuration is explicit through
  an OpenAI-compatible/LiteLLM-friendly provider contract, MVP 1 uses a
  deterministic static planner instead of model-driven decomposition, and
  Mneme is a hard dependency that fails closed at run start.
- The v0.2 draft also tightens secret redaction, first-class evidence
  freshness, shared budget reservations for future parallel workers,
  self-reported confidence naming, loop prevention through task hashes, and
  baseline quality criteria for MVP 1.
- Follow-up review approved v0.2 for MVP 1. The v0.3 draft adds non-blocking
  refinements before implementation planning: `CONFIGURE_ME` model placeholder,
  deterministic static subtemplates, automated MVP 1 baseline comparison,
  cancellation semantics before MVP 2 parallel workers, and removal of the
  vague fast-path phrase "narrow lookup".

### RLM Orchestrator REST/MCP Consistency Findings

- Phase 13B already verified the real `_rlm-orchestrator` Mneme session id as
  `019edb86-1d22-78a3-b9e4-e6121c294056`.
- The current user-provided failure is an unauthenticated REST call to
  `/v1/tools/context_search`, not evidence that REST rejects the session id.
  The local REST daemon is expected to require a bearer token unless explicitly
  started in insecure development mode.
- MCP can read the same session because the installed local MCP entrypoint is
  configured with the Mneme token through the Codex/Mneme runtime environment.
  That is an auth boundary, not proof that unauthenticated REST should work.
- RLM Orchestrator MVP 1 needs a cheap authenticated readiness check that
  proves tool access and session visibility before benchmark execution, because
  `/v1/health` only proves the process is alive.
- REST tool callers need distinct machine-readable failures for
  missing/invalid token and missing session so the orchestrator can fail closed
  differently for auth/config errors versus empty evidence.
- Implemented repo-level fixes now make REST failures uniform:
  `{ok:false,error:{...},warnings:[]}` for auth and session/tool failures while
  preserving the existing top-level `error` key for compatibility.
- Added authenticated `POST /v1/readiness/session`. With
  `require_evidence=true`, it returns `412 FAILED_PRECONDITION` and
  `details.reason=NO_EVIDENCE` when the session exists but the run-start
  evidence gate has no hits.
- Live authenticated REST smoke against the running daemon proved that
  `context_search` accepts session id
  `019edb86-1d22-78a3-b9e4-e6121c294056` and returns 5 RLM evidence results
  when a valid bearer token is supplied. The original failing curl lacked this
  token.
- The running global daemon was not reinstalled or restarted during this slice.
  It can serve authenticated `context_search` now, but the new
  `/v1/readiness/session` endpoint requires deploying this checkout before live
  use on `127.0.0.1:8765`.
- Phase 17B aligned the specs with the Phase 18 fix: MCP success is evidence
  that the MCP process has a valid REST token, not evidence that unauthenticated
  REST should work. RLM Orchestrator must use Mneme REST with
  `MNEME_AUTH_TOKEN`/configured `token_env`, call authenticated
  `/v1/readiness/session` at run start, and temporarily fall back to
  authenticated `context_search top_k=1` only when the live daemon has not yet
  deployed the readiness endpoint.
- The spec-level fail-closed taxonomy is now explicit: `401` means auth/config
  failure, `404` means missing/unknown session, `412` with
  `details.reason=NO_EVIDENCE` means the session exists but required evidence
  is absent, and `200 ok=true` with evidence means Mneme is usable for the
  run-start gate. These cases must not be collapsed into "empty memory".

### Current Mneme Prototype Facts

- `llm_enrichment_enabled` exists and can disable LLM-based state enrichment.
- Reranking is configurable through `reranker_enabled`.
- Embedding calls are currently Jina-compatible HTTP calls, batched, with a circuit breaker.
- If embedding endpoint fails, events still land in SQLite and retrieval can fall back to keyword/recency paths.
- Current Hermes integration has native prototype hooks for request-only assembly and post-turn ingestion.

### Market Signals

- Letta, Mem0, LangGraph, LlamaIndex, Anthropic, and Codex all treat memory/context engineering as a major agent-runtime problem.
- Mneme's differentiator should be raw event history plus request-only context assembly for long-running tool-using agents, not generic user memory storage.

### Resolved Earlier Questions

- REST and MCP are both in scope.
- REST is lifecycle/control-plane: sessions, events, turns, context preparation, traces, costs, export, and delete.
- MCP is agent-facing memory tooling: search, fetch, expand, list segments, recall recent, explain context, and cost report.
- Event ingestion can be synchronous at the protocol level, but adapters should buffer until acknowledgement and replay idempotently after restart.
- Retrieval is both service-driven through `/context/prepare` for deep adapters and agent-driven through memory tools for tool-first adapters.
- Benchmark/conformance data should be synthetic or scrubbed.
- The revised contract sets a minimum synthetic conformance corpus of 5 sessions, 100 events, and 3 runtime labels.

### Agent Context Integration Findings

- A universal external service can store, search, audit, and prepare context, but it cannot unilaterally replace an agent's model-bound prompt unless the host runtime exposes a pre-model-call hook.
- OpenClaw distinguishes memory plugins from context engines. Memory plugins provide search/retrieval; context engines control what the model sees. A context engine participates in ingest, assemble, compact, and after-turn lifecycle points.
- OpenClaw context engines can declare host capability requirements such as `assemble-before-prompt`; generic CLI backends that cannot satisfy this are rejected before the run starts.
- OpenClaw's plugin hooks include `before_prompt_build`, which can inject context before prompt submission, but this is still a host-owned integration point rather than generic MCP behavior.
- OpenAI Agents SDK separates local run context from LLM-visible context. Data becomes visible to the LLM only through instructions, run input, tools/retrieval, or session/input filtering.
- OpenAI Agents SDK supports `RunConfig.session_input_callback`, which can customize how session history and new input merge before a model call. That is the kind of deep hook Mneme needs for automatic request-only context assembly in that runtime.
- MCP is valuable as a tool surface: it lets agents discover and call Mneme memory tools through stdio/HTTP transports. It is not, by itself, a universal prompt replacement mechanism.
- A universal thin layer is possible as a host adapter contract: future agent runtimes can implement Mneme lifecycle hooks and capability negotiation directly instead of requiring bespoke conceptual integration work.
- Existing agents still need native thin adapters because their hook names, prompt assembly boundaries, tool registries, trace systems, and compaction behavior differ.
- The correct universal claim is: "new runtimes can become Mneme-compatible by implementing the Host Adapter Contract"; not "Mneme can externally override any runtime's prompt without host cooperation."
- Current Codex/MCP integration is useful as pull-based memory. It can help after context compaction if the agent is instructed to search/fetch Mneme evidence, but it is not an invisible context collector for every Codex request.
- `planning-with-files` remains a file-backed project memory workflow for the agent, while Mneme MCP is an external searchable memory tool surface. The former can instruct behavior; the latter stores/searches evidence; neither gives Codex automatic prompt replacement without host cooperation.

### Codex Memory Dogfood Findings

- Current Codex/MCP tools are read-oriented memory/state tools. They do not, by themselves, populate Mneme storage.
- Codex data currently enters Mneme through REST lifecycle/event ingestion, with `mneme codex-ingest` as the offline/reference transcript importer.
- A practical Codex knowledge-base workflow needs an ingestion lane and a recall lane:
  - ingestion lane: transcript/checkpoint/session events are sent to REST;
  - recall lane: Codex calls MCP memory tools when it needs project memory.
- Adding a model-callable MCP write/checkpoint tool is possible but should be a separate contract decision because it changes the security and prompt-injection surface.
- Phase 13 Task 1 defined the Codex memory operating contract in `adapters/codex/MNEME_CODEX_MCP_USAGE.md`.
- Codex agents should use Mneme MCP evidence at session start or resume, after compaction/context loss, before milestone decisions, before modifying files after a long interruption, and when asked what was done or why.
- Retrieved Mneme memory is evidence, not instruction authority. Current system, developer, and user instructions override retrieved memory; stored transcripts/tool output remain untrusted data until corroborated.
- Codex tools-only recovery should combine local planning files with `get_execution_state`, `get_goal_history`, semantic `context_search`, `fetch_event`, `expand_context`, `recall_recent`, `list_segments`, `explain_context`, and `mneme_cost_report`.
- The daemon now has semantic retrieval, execution state, lineage-aware retrieval, provider-safe degradation, and budgeted `/v1/context/prepare`; Codex/MCP uses those capabilities through explicit tool calls, not automatic prompt replacement.
- Official Codex docs confirm that MCP server-wide `instructions` are read at
  MCP initialization, so Mneme should provide concise guidance directly from the
  MCP server in addition to external docs.
- Official Codex docs confirm command hooks for lifecycle/tool/compaction/stop
  events. These are a viable path for approved local event ingestion into Mneme,
  but they are not treated as proven automatic prompt replacement for every
  model call.
- Official Codex docs confirm repo-local skills under `.agents/skills` and
  `AGENTS.md` as persistent instruction surfaces. Mneme should use a repo-local
  `mneme-memory` skill plus an AGENTS snippet so Codex remembers when and how to
  call memory tools.
- For the next Phase 13 slice, MCP remains read-only for Codex. Writes should
  come from trusted hook/importer commands that call REST ingestion, not from a
  model-callable MCP write tool.
- Phase 13 Task 2 implemented the Codex adapter foundation: MCP server
  instructions, repo-local `mneme-memory` skill, AGENTS snippet, disabled hook
  contract example, and tests that enforce read-only/evidence/no-overclaim
  behavior.
- Phase 13 Task 3 implemented a hook-ingestion MVP: `mneme codex-hook-ingest`
  normalizes explicit Codex hook JSON/stdin into Mneme session/event payloads,
  supports dry-run inspection, writes through REST ingestion when enabled, and
  preserves replay idempotency through stable event ids.
- The hook-ingestion MVP is not yet an enable-ready automatic Codex hook setup.
  Real Codex hook payloads still need to be captured and validated before
  removing dry-run from user-facing hook examples.
- Added a capture/validation harness for the real-payload step:
  `mneme codex-hook-capture` writes raw hook payloads to an untracked JSONL
  file, `mneme codex-hook-validate` reports field readiness without raw content,
  and `adapters/codex/codex_hooks.capture.example.json` is capture-only with no
  REST writes.
- Added `mneme codex-hook-render-config` so each machine can generate a local
  capture/dry-run/write hook config with an explicit Python runner. The local
  capture rehearsal file is `.codex/hooks.json`, gitignored, and currently
  capture-only with no REST writes.
- The official Codex manual confirms project hooks are discovered next to active
  config layers as `.codex/hooks.json` or inline `[hooks]` in
  `.codex/config.toml`. The earlier local `.agents/hooks.json` assumption was
  wrong for active hook loading.
- Local real Codex Desktop hook capture now works after Codex UI trust
  approval. The real capture file contained `SessionStart`,
  `UserPromptSubmit`, `PostToolUse`, and `Stop` events, and
  `mneme codex-hook-validate --input .local/mneme-codex-hooks.jsonl` now
  reports `payload_count: 4`, `valid_for_enablement: true`, and no warnings.
- Real Codex Desktop hook payloads use `hook_event_name` and omit
  `timestamp`, `summary`, and `message`. The capture wrapper's `captured_at`
  timestamp is therefore the right fallback for captured JSONL validation, and
  content must be derived from actual Codex fields such as `prompt`,
  `tool_name`, `tool_input`, `tool_response`, `tool_use_id`,
  `last_assistant_message`, `source`, `cwd`, and `model`.
- Direct `codex-hook-ingest` dry-run/write mode now supplies a local receipt
  timestamp when Codex stdin has no timestamp, while hook event ids stay stable
  without depending on that timestamp. This keeps replay behavior idempotent.
- Current documented Codex command hooks do not include a context-build or
  pre-model prompt replacement hook. `UserPromptSubmit` can run a command when
  the user submits a prompt, and `PreCompact`/`PostCompact` can run around
  compaction, but current command hook output is not documented as a way to
  replace the model input.
- The official Codex manual says only `type: "command"` hook handlers run
  today; `prompt` and `agent` handlers are parsed but skipped. Therefore Mneme
  can automatically prepare and write context preview files from hooks, but
  Codex prompt insertion remains unsupported until Codex exposes a suitable
  host lifecycle hook or runnable prompt handler.
- Local context-preview smoke passed: captured real hook events were imported
  into a temporary Mneme daemon, `codex-hook-prepare-preview` called
  `/v1/context/prepare` for `UserPromptSubmit`, and wrote a JSONL preview with
  `changed: true`, generated Mneme evidence, no warnings, and a trace id.
- Real preview-hook rehearsal passed after enabling the local gitignored
  `.codex/hooks.json` capture + REST ingest + context-preview setup. A new
  trusted Codex Desktop session wrote `.local/mneme-codex-context-preview.jsonl`,
  capture validation still passed for 12 payloads, and MCP `context_search`
  returned hook-derived `UserPromptSubmit`, `PostToolUse`, `Stop`, and
  `SessionStart` events for the preview session.
- Multi-machine Codex dogfood requires per-machine Mneme verification. A shared
  symlinked AGENTS/skill/doc tree can remind both Codex installs to use Mneme,
  but each machine still needs its own working `mneme serve`, `mneme mcp`, local
  env vars/tokens, database path, and trusted hook setup.
- The first GitHub publication step accidentally mixed engine, Codex adapter,
  and internal planning/dogfood material in one repository. That repository was
  made private and should be treated as quarantine/internal, not as the public
  install source.
- The corrected publication path is: create a clean public Mneme engine/core
  repository, create a separate Codex adapter repository/package that depends
  on the core, then rehearse installation on the second Codex machine from
  those public surfaces as if by a new user.
- The chosen GitHub names are `johnnykor82/mneme-universal-context-service` for
  the Mneme engine/core and `johnnykor82/mneme-codex-adapter` for the Codex
  adapter.
- Clean core publication is complete. The public core repository
  `johnnykor82/mneme-universal-context-service` was recreated from sanitized
  root commit `01f969d`, while the earlier mixed repository was preserved as
  private `johnnykor82/mneme-universal-context-service-internal-quarantine`
  because the GitHub token did not have `delete_repo` scope.
- Clean Codex adapter publication is complete. The public adapter repository
  `johnnykor82/mneme-codex-adapter` was created from sanitized root commit
  `d041528` and uses the `mneme-codex` CLI while depending on the public core.
- The second-machine install rehearsal succeeded technically, but it was a
  developer alpha path: local clone, workspace `.venv`, manual daemon process,
  manual MCP distinction, and no always-clear global Codex operating model.
  The feedback recommends a linear Codex Desktop quickstart, explicit install
  scope, daemon/service story, MCP registration guidance, hook state ladder,
  doctor/status commands, safe uninstall/reinstall guidance, and copyable smoke
  tests.
- The first packaging response is intentionally narrow: add a user-global
  install root (`~/.mneme-codex`), token-safe generated runtime files,
  `mneme-codex setup codex-desktop --global`, `mneme-codex doctor/status`,
  sample transcript smoke input that does not require a source checkout, and a
  Codex Desktop quickstart. It does not silently edit Codex config, install a
  background service, enable write hooks, or claim automatic prompt
  replacement.
- The second global-install feedback showed that the public adapter needed one
  more usability pass before another rehearsal: sample ingest needed
  install-root token resolution, daemon startup needed a launchd service path,
  doctor/status needed install-root entrypoint checks, public docs needed to
  avoid references to unpublished skills, and provider setup needed explicit
  non-secret config/API-key/restart/verify instructions.
- The Codex adapter public commit `47a2127` closes that pass: it adds
  `mneme-codex service install/start/stop/status/logs/uninstall`, writes
  `$MNEME_CODEX_HOME/mneme.toml`, resolves REST command tokens from
  `$MNEME_CODEX_HOME/.local/mneme.env` when `--install-root` is supplied, and
  reports `provider_capabilities` in doctor/status without printing secrets.
- The follow-up public commit `2a76286` closes the remaining skill-install
  gap: `mneme-memory` is packaged with the adapter, `mneme-codex skill install`
  writes it to `~/.codex/skills` or a symlinked shared skills target, and
  install docs now mark the skill as required for expected Codex recall
  behavior in fresh/resumed/compacted sessions.
- `codex doctor --summary --ascii` for this project did not surface a hook
  config parse error, but it reported unrelated environment issues: Codex state
  database integrity failure, provider reachability/WebSocket failures, optional
  MCP config issues, and `TERM=dumb`. These were not repaired during this
  Mneme slice.

### Codex Dogfood Verification Findings

- Current Codex session can see the Mneme MCP memory tools through the `mcp__mneme` namespace.
- `context_search` against `session_id=codex-example-session` with query `focused pytest passed` returned expected event `codex-codex-example-session-turn-1-0003`.
- `fetch_event` for `codex-codex-example-session-turn-1-0003` returned content text `focused pytest passed`, confirming the offline/reference Codex transcript import is readable through MCP.
- The dogfood result preserves the existing integration-depth claim: Codex/MCP is working as `TOOLS_ONLY` memory access, not automatic prompt replacement.

### Provider Configuration Findings

- The daemon settings in `mneme_service/config.py` cover DB path, auth token, insecure-dev flag, host, port, request/content limits, and optional provider settings.
- The CLI accepts `MNEME_AUTH_TOKEN` and `MNEME_BASE_URL` for daemon/MCP/Codex-ingest connectivity, plus provider config and provider override flags for `mneme serve`.
- Provider configuration separates non-secret config from secrets: tracked examples show provider names/models/base URLs, while real API keys come from environment variables, CLI inputs, or an intentionally local config path.
- Phase 14 Task 1 implemented the provider configuration foundation:
  `mneme_service.config.ProviderSettings`, `load_settings()`,
  `mneme.example.toml`, env/CLI/TOML/default precedence, secret-safe provider
  summaries, provider-aware REST capabilities, and `mneme serve` config/provider
  flags.
- Phase 14 later implemented provider clients for embeddings, reranking, and
  LLM enrichment behind explicit opt-in settings. `supports_*` capabilities
  reflect whether a provider surface is both enabled and minimally configured.
- Phase 13 dogfood now has an explicit `require_embeddings` setting. When true,
  daemon startup fails fast unless an enabled, configured embedding provider is
  available; `/v1/capabilities` reports `requires_embeddings`.
- Local dogfood provider settings were mapped from the live Hermes environment
  into a gitignored `.local/mneme-dogfood.env` without printing secrets. The
  dogfood LaunchAgent now runs through `.local/run-mneme-dogfood.sh` with
  `--require-embeddings`.
- Current dogfood capabilities report configured local embeddings and reranker:
  embeddings via `http://localhost:8000/v1`, model
  `jina-embeddings-v5-text-small-retrieval-mlx`; reranker via
  `http://localhost:4000`, model `rerank`; API keys are configured but not
  printed.
- Real provider smoke passed for session `provider-smoke-1781467731`: 3 events
  accepted, 3 `embedding_index` rows written, `embedding_items: 3`,
  `embedding_failures: 0`, `reranker_calls: 1`, `reranker_failures: 0`, and
  `context_search` returned the three smoke events.
- Current LLM provider surface is structured enrichment of execution state, not
  natural-language answer synthesis from memory. Publication docs must not
  claim answer synthesis unless a dedicated path is implemented and
  smoke-tested with a real provider.
- A second read-only parity audit found that Phase 14/14B recovered the broad
  pipeline but not every original `hermes-mneme` behavior. Remaining
  runtime-neutral gaps include richer config knobs, optional `sqlite_vec`,
  global/multi-session semantic search, centroid cache/window segmentation,
  weighted intent routing, router fallback, richer execution state recovery,
  `topic_tags`, decision rationale/summary, scheduled/background enrichment,
  original prompt-builder details, richer segment skeletons, and fuller MCP/REST
  tool parity.
- These gaps should be closed before GitHub publication and second-machine
  install rehearsal. Codex still must not be described as automatic prompt
  replacement, but `/v1/context/prepare` should become a complete context-engine
  backend for future adapters that do have host lifecycle hooks.
- Phase 14C closed the runtime-neutral original-core gaps in the universal
  daemon/core: config surface, global search, model reindex, intent/router
  parity, state recovery, enrichment fields, prompt-builder helper blocks, and
  richer MCP/REST tools. Publication can proceed to GitHub/second-machine
  rehearsal after final hygiene checks.
- Local dogfood confirms required embeddings and reranker support. The local
  dogfood daemon does not configure an LLM provider, so real LLM enrichment
  smoke remains a release-claim gate only if the publication candidate claims
  live LLM enrichment readiness.
- Pre-publication LiteLLM check on `127.0.0.1:4000` now passes for model
  `default`. The real Mneme LLM enrichment smoke initially failed under
  sandboxed Python/httpx local-network restrictions, then passed with approved
  unsandboxed execution: one event accepted, one enrichment call, zero
  enrichment failures, and state enrichment populated `intent_label`,
  `topic_tags`, `decision_summary`, and decision rationale.

### Embedding Provider and Index Findings

- Phase 14 Task 2 implemented `mneme_service.embeddings` with an
  OpenAI/Jina-compatible embedding provider shape, sync batch embedding calls,
  injectable `httpx` transports for tests, same-length batch outputs, blank
  input skipping, and a provider circuit breaker.
- Event ingestion now stores canonical redacted events before embedding work.
  Provider/index failures do not block ingestion; they are recorded in
  per-session embedding metrics and surfaced through the existing cost report.
- SQLite now has `embedding_index` and `embedding_metrics` tables. Embeddings
  are stored as packed float BLOBs keyed by `(event_id, embedding_model_id)`.
- Python cosine fallback is the verified search path for embeddings. The
  project `.venv` does not have `sqlite_vec` installed, so optional vector
  acceleration remains unexercised in this environment.
- Tool-output compression is used only for embedding input; stored/fetched raw
  events remain intact after normal service redaction.
- No Phase 14 Task 2 tests make real provider calls. HTTP provider behavior is
  tested with `httpx.MockTransport` and app ingestion uses fake providers.
- The installed `security-guidance` skill bundle did not include the referenced
  ASVS files. The implementation followed the project contract directly:
  redaction before indexing/provider calls, parameterized SQL, no raw provider
  secrets in outputs, and local fake/mock provider tests.

### Hybrid Retrieval Findings

- Phase 14 Task 3 replaced REST `context_search` keyword-only behavior with a
  hybrid retrieval path when embeddings are enabled. Vector candidates are
  fetched from `EmbeddingIndex`, then merged with keyword/recency fallback.
- Minimal mode still uses keyword/recency only and makes no provider calls.
- When embedding query generation or vector retrieval is unavailable, the tool
  returns keyword/recency results with an `EMBEDDINGS_UNAVAILABLE` warning and a
  degraded memory-read trace.
- Direct `context_search` memory-read traces now include retrieval metadata:
  strategies, candidate count, selected count, degraded flag, and fallbacks.
- MCP parity remains REST-canonical because MCP tools proxy the same
  `/v1/tools/context_search` endpoint through `MnemeRestClient`.
- Hybrid retrieval does not yet include graph/dependency scoring, reranking, or
  execution-state query expansion; those belong to later Phase 14 tasks.

### Execution State and Goal History Findings

- Phase 14 Task 4 added runtime-neutral deterministic execution state derived
  from normalized events: first user message sets `goal`, latest user message
  updates `current_step`, tool events update `last_tool` and output summary,
  and `DECISION` events append to `decision_stack`.
- SQLite now stores `execution_state` and append-only `state_history`; export
  includes both and delete removes both.
- REST/MCP now expose `get_execution_state` and `get_goal_history` using
  versioned schemas `mneme.execution_state.v0` and
  `mneme.state_history_entry.v0`.
- MCP remains a thin REST proxy for state/history tools, preserving the
  REST-canonical behavior boundary.
- `API_MCP_CONTRACT_V0.md` was updated additively to document the new tools and
  schemas.
- This slice does not implement Hermes-specific lineage/ancestor fallback,
  LLM-derived enrichment, or budgeted context assembly with state blocks; those
  remain later Phase 14/future adapter work.

### Segmentation and Intent Classification Findings

- Phase 14 Task 5 Slice A added `mneme_service.classifier`, a deterministic
  runtime-neutral classifier for `CONTINUATION`, `SWITCH`, `NEW_TASK`, and
  `CLARIFICATION` with English and Russian switch/question patterns.
- Accepted redacted `USER_MESSAGE` events now update segments during ingestion
  after canonical event storage and execution-state update.
- Explicit topic switches close the active segment and open a new active segment
  with `drift_reason=EXPLICIT_SWITCH`; continuation messages extend the active
  segment.
- Phase 14 Task 5 Slice B added high embedding-drift `NEW_TASK` resolution and
  segment rollover. Drift compares the new user-message embedding to the active
  segment centroid after at least three indexed segment embeddings; cold start
  and provider failures yield drift `0.0`.
- Embedding rows for user-message segmentation now use event-driven segment ids
  through `metadata.mneme_segment_id` while preserving the fallback
  `segment-{session_id}` behavior for records without segment metadata.
- `list_segments` now exposes event-driven segment metadata including status,
  anchor event ids, event count, token estimate, title, summary, and drift
  reason.
- Phase 14 Task 5 Slice C added redacted `SEGMENT_DRIFT` traces when
  explicit-switch or embedding-drift classification causes segment rollover.
  These traces expose classifier signals, intent/drift reason, closed/opened
  segment ids, event counts, fallbacks, and warnings without raw message
  content.
- Phase 14 Task 5 Slice D added `mneme.session_state.v0` classification to
  `POST /v1/sessions/start`: new empty sessions are `FRESH`, existing sessions
  with canonical events or turns are `RESUME`, and adapter lifecycle metadata
  can classify a newly created session as `RESUME`.
- Session-state decisions expose prior event/turn counts, adapter resume
  signals, optional lineage session id, resume source, and
  `requires_context_fill` for resumed sessions with prior daemon state.
- Phase 14 Task 5 Slice E added `mneme.session_lineage.v0` edges from explicit
  adapter lineage metadata. Session-scoped retrieval can search the lineage
  chain so child/resumed sessions recall parent evidence without copying parent
  canonical events into the child export.
- Lineage-aware lookup now applies to keyword search, semantic embedding search,
  `fetch_event`, recent recall, and graph expansion through the shared storage
  helpers.
- Phase 14 Task 5 Slice F added a one-shot resume context-fill latch. Session
  start sets it when `requires_context_fill=true`; the next successful
  `/v1/context/prepare` fills from recent current/lineage events with reason
  `RESUME_CONTEXT_FILL` if ordinary retrieval selects no evidence, then marks
  the latch fulfilled.
- Phase 14 Task 5 is complete. Remaining Phase 14 parity work starts with typed
  event graph and dependency scoring.

### Typed Event Graph Findings

- Phase 14 Task 6 Slice A added `mneme.graph_edge.v0` persistence for typed
  event dependencies derived from `parent_event_ids`.
- Initial graph edge types are `TOOL_RESULT` for tool call to tool output,
  `DECISION_FOLLOWS` for decision events, and generic `FOLLOWS` for other
  parent-linked events.
- `expand_context` now uses typed graph edges when present and falls back to
  legacy parent/child traversal for older databases without graph edges.
- Export includes `event_graph_edges`, and memory-read audit continues to
  account for every event id returned by graph expansion.
- Phase 14 Task 6 Slice B added dependency-aware retrieval scoring:
  `context_search` expands direct graph neighbors of primary semantic/keyword
  hits before `top_k` packing, using strategy `GRAPH_DEPENDENCY`, reason
  `GRAPH_DEPENDENCY:<edge_type>`, and a smaller bonus score than primary
  matches.
- Phase 14 Task 6 is complete. Remaining Phase 14 parity work starts with
  budgeted context assembly.

### Budgeted Context Assembly Findings

- Phase 14 Task 7 Slice A added a request-only execution-state block to
  `/v1/context/prepare`.
- When `policy.include_execution_state=true`, Mneme derives the block from the
  stored `mneme.execution_state.v0` fields: goal, current step, last tool, last
  tool output summary, and recent decisions.
- The block is inserted only when the state is non-empty and its token estimate
  fits `budget_split.execution_state_ratio`; otherwise prepare preserves the
  existing pass-through behavior when no retrieved events are selected.
- The generated context message carries `metadata.mneme_generated=true` and is
  not persisted as a canonical transcript event. Export remains free of the
  `[MNEME EXECUTION STATE]` marker.
- Phase 14 Task 7 Slice B added protected recent-tail packing for oversized
  request messages. When `policy.include_recent_tail=true`, Mneme preserves the
  system prompt and a contiguous suffix of recent messages that fits
  `budget_split.recent_tail_ratio`.
- Slice B also fixed the over-budget/no-context edge so prepare no longer
  inserts an empty `mneme_generated` assistant message.
- Phase 14 Task 7 Slice C added retrieved-context packing under
  `budget_split.retrieved_context_ratio`. Search can return candidates, but
  prepare now includes only events whose evidence lines fit the retrieved
  budget.
- Retrieved candidates dropped by the budget are omitted from the generated
  evidence block and recorded with reason
  `RETRIEVED_CONTEXT_BUDGET_EXCEEDED` in response `dropped_event_refs` and
  stored trace `dropped_events`.
- Phase 14 Task 7 Slice D added final collision resolution across execution
  state, protected tail, retrieved context, and headroom. The final assembled
  request is checked against `budget_tokens` after reserving headroom.
- Collision priority is conservative: preserve system prompt and protected
  tail first, drop retrieved evidence first with reason
  `CONTEXT_COLLISION_BUDGET_EXCEEDED`, drop the execution-state block next if
  still necessary, and tighten the tail only if the protected blocks still do
  not fit.
- Phase 14 Task 7 is complete. Remaining Phase 14 parity work starts with the
  optional reranker.

### Optional Reranker Findings

- Phase 14 Task 8 added `mneme_service.reranker` with
  `HttpRerankerProvider`, `RerankerProvider`, and `RerankResult`.
- The HTTP provider posts to `{base_url}/rerank` with model, query, documents,
  and `top_n`, and parses Jina/Cohere-style result payloads using `index` plus
  `relevance_score` or `score`.
- `context_search` now applies reranking after semantic/keyword/recency/graph
  candidate merge when `settings.reranker.available` is true. MCP inherits the
  behavior through the existing REST proxy.
- Reranker failures preserve the original retrieval order, return warning
  `RERANKER_UNAVAILABLE`, mark retrieval traces degraded, and record the
  fallback reason.
- SQLite now tracks per-session `reranker_calls` and `reranker_failures`;
  `/v1/costs/session/{session_id}` reports those counters.
- Phase 14 Task 8 is complete. Remaining Phase 14 parity work starts with
  optional LLM enrichment.

### Optional LLM Enrichment Findings

- Phase 14 Task 9 added `mneme_service.enrichment` with
  `HttpLLMEnrichmentProvider`, `EnrichmentProvider`, and `EnrichmentResult`.
- The HTTP provider uses OpenAI-compatible `/chat/completions` with
  `response_format={"type":"json_object"}` and a strict JSON-only system
  prompt.
- Enrichment is ingestion-time and optional. Deterministic execution state is
  computed first; provider updates can only affect structured fields:
  `enrichment.intent_label`, `enrichment.decisions`, `active_entities`, and
  `open_loops`.
- Provider outputs are redacted before state commit. Raw LLM output is not
  stored as an event, and enrichment failure does not block ingestion.
- SQLite now tracks per-session `enrichment_calls` and
  `enrichment_failures`; `/v1/costs/session/{session_id}` reports those
  counters.
- Phase 14 Task 9 is complete. Remaining Phase 14 parity work starts with the
  parity acceptance suite.

### Parity Acceptance Findings

- Phase 14 Task 10 added `tests/test_parity_recovery.py` as an end-to-end
  acceptance layer for the whole parity recovery milestone.
- Acceptance coverage proves minimal mode makes zero provider calls and still
  redacts storage/search/traces.
- Provider-backed acceptance proves semantic retrieval can recover paraphrased
  evidence keyword search misses, reranking can reorder candidates, enrichment
  can add structured state, and secrets are not passed to provider inputs.
- Degraded-provider acceptance proves embedding outage falls back to
  keyword/recency without losing stored events.
- Runtime-neutral context-engine acceptance proves state/history survive
  restart, explicit topic switches create separate segments, fresh/resume
  session classification works, lineage carries parent context without copying
  parent events, first-turn resume fill works, and `/v1/context/prepare` packs
  execution state, retrieved evidence, protected tail, and headroom under
  budget.
- MCP acceptance proves MCP memory tools expose the same redacted data as REST
  through the existing proxy.
- Phase 14 is complete.

### Publication Preparation Findings

- Phase 15 added a top-level README that describes the implemented REST/MCP
  service, integration depth, quick start, provider configuration, Codex
  tools-only usage, tests, and the publication gate.
- Installation, provider configuration, testing/CI, and publication checklist
  docs now live under `docs/`.
- `pyproject.toml` now has setuptools build metadata, package discovery,
  README metadata, classifiers, and package keywords suitable for a first
  editable/package install.
- CI now installs `.[test]`, runs the full pytest suite, runs the parity
  acceptance suite explicitly, and compiles `mneme_service` plus tests on
  Python 3.11 and 3.12.
- `.gitignore` excludes local virtualenvs, caches, SQLite DBs, `.local/`, build
  artifacts, and egg-info artifacts.
- Secret and overclaim scans found no real tokens. Matches were either
  placeholder-only examples such as `<secret>` or negative/honesty statements
  warning that MCP does not automatically replace a host prompt.
- The earlier decision to keep `adapters/codex` in the same first public
  repository was wrong for the desired product shape. The durable public model
  is engine/core separately and host adapters separately.
- Ivan Konstantinov selected Apache License 2.0. `LICENSE` and `NOTICE` now
  identify Ivan Konstantinov as the 2026 copyright owner.

### Phase 14B Direction Findings

- Hermes adapter implementation should wait for the upstream Hermes
  context-engine hook PR. The clean integration path needs native lifecycle
  hooks instead of the legacy compaction path.
- Work can safely continue in the Phase 14 daemon/core layer while the PR is
  pending: post-Phase-14 parity docs, benchmarks, provider robustness, optional
  vector acceleration posture, and adapter-independent acceptance evidence.
- `HERMES_MNEME_COMPARISON.md` is intentionally useful as historical audit
  evidence, but its comparison table is stale after Phase 14 and needs a
  post-Phase-14 status section.
- Added the post-Phase-14 comparison update: the daemon parity pipeline is now
  largely recovered, while the remaining major gap is host integration depth
  pending upstream Hermes native context-engine hooks.
- Added an adapter-independent benchmark harness exposed as `mneme benchmark`.
  It uses an in-process app, synthetic events, fake local embedding vectors,
  `context_search`, `/v1/context/prepare`, and cost reports, with no external
  provider calls.
- Expanded provider robustness coverage without real provider calls:
  malformed embedding payloads now trip provider failure handling, mixed
  embedding dimensions are rejected before indexing, out-of-range reranker
  indexes degrade cleanly, and non-JSON enrichment responses degrade cleanly.
- Local `sqlite_vec` availability remains `None`. Added vector acceleration docs
  that treat Python cosine as the verified portable path and `sqlite_vec` as an
  optional future acceleration path, not a current requirement or performance
  claim.
- Phase 14B final gate passed: full pytest, parity acceptance,
  provider/benchmark focused tests, compileall, and documentation/code scans are
  clean.

### Hermes-Mneme Parity Audit Findings

- `hermes-mneme` is a Hermes-native context engine, not only a memory database. Hermes calls its `compress()` method on every turn, letting it ingest events, update state, retrieve context, and return the model-bound message list.
- `hermes-mneme` implements a semantic retrieval stack: Jina/OpenAI-compatible embeddings, `sqlite-vec` KNN when available, Python cosine fallback, embedding batching, and an embedding endpoint circuit breaker.
- `hermes-mneme` has a richer provider configuration surface through `HERMES_CTX_*` environment variables and plugin-local `config.yaml`.
- `hermes-mneme` has optional reranking and optional LLM enrichment. The enricher can use explicit config, Hermes auxiliary LLM, or captured Hermes model parameters.
- `hermes-mneme` tracks execution state: goal, current step, open loops, last tool, decision stack, active entities, and enrichment signals. It also appends state history for goal trail/recovery.
- `hermes-mneme` includes deterministic intent classification and embedding-drift segmentation. These affect retrieval query building and segment boundaries.
- `hermes-mneme` uses a retrieval router with similarity, recency, dependency, and event-type scoring, plus optional rerank. The universal service currently uses keyword term count and recency ordering.
- `hermes-mneme` prompt assembly includes memory access hints, goal trail, execution state, retrieved context, protected tail, cross-session candidates, checkpoint blocks, and token-budget collision resolution.
- The universal service is ahead on portable REST/MCP contract, schema versioning, redaction, audit records, `MEMORY_READ` events, memory-read traces, MCP/REST parity tests, Codex MCP visibility, and explicit adapter-depth honesty.
- The universal service is behind on semantic retrieval quality, provider config, execution state, goal history, segmentation, intent routing, typed execution graph scoring, reranker/enricher, and full budgeted prompt assembly.
- Conclusion: the direction is still valid as a universal substrate, but the next implementation milestone should recover `hermes-mneme`'s quality pipeline before deeper Codex dogfood polish.
- Direction decision: yes, the project changes order now. Port the runtime-neutral `hermes-mneme` core into the universal daemon first; then continue Codex/Hermes/other adapters.
- The newer local `_hermes-mneme-native` copy no longer depends on `compress()` as the primary path when native hooks exist. It uses `on_turn_complete()` for ingestion and `prepare_request_messages()` for request-only context assembly, while `compress()` remains a legacy fallback.
- Hermes PR local copy `_hermes-agent-pr` exposes generic context-engine hooks: `on_turn_complete`, `prepare_request_messages`, `on_session_start/end/reset`, tool schemas, tool dispatch, and model/budget updates. These match the universal Host Adapter Contract direction.
- Do not port Hermes-specific `compress()` lifecycle glue or Hermes thread-local session-id discovery into the daemon. Those belong in a future Hermes host adapter.
- Do port runtime-neutral session/topic drift semantics into the daemon: semantic drift scoring, explicit switches, segment boundaries, resume vs fresh-session classification, lineage/carry-over policy, first-turn resume context fill, and drift traces.

## Technical Decisions

| Decision | Rationale |
|---|---|
| Use `/v1` REST routes with `mneme.*.v0` schema versions. | Allows a stable API namespace while keeping schema versions explicit during pre-1.0 contract evolution. |
| Use `snake_case` JSON fields. | Aligns with existing Mneme concept documents and Python implementation style. |
| Context preparation remains request-only. | Prevents prepared context from replacing or corrupting canonical transcripts. |
| Direct REST/MCP memory tool calls create durable audit records and `MEMORY_READ` events by default. | Makes memory reads inspectable and accountable. |
| `/context/prepare` may rely on trace audit entries instead of extra `MEMORY_READ` events. | Avoids polluting retrieval with internally generated prepare activity. |
| Oversized inline content returns `413 PAYLOAD_TOO_LARGE`; adapters retry with `BYTES_REF`. | Keeps storage policy explicit and prevents hidden server-side conversion. |
| Adapters expecting large outputs should use `BYTES_REF` immediately. | Avoids probing inline limits and reduces wasted transfer. |
| Pagination tokens are server-issued and opaque. | Prevents adapters from depending on token internals. |
| Unknown sessions during event ingestion return `404`; sessions are not auto-created. | Forces explicit lifecycle control and avoids accidental cross-project leakage. |
| Streaming can use `ASSISTANT_MESSAGE_CHUNK`, but retrieval prefers final `ASSISTANT_MESSAGE`. | Supports streaming without making partial chunks canonical retrieval evidence by default. |
| Milestone 1 excludes embeddings, reranking, and LLM enrichment. | Creates deterministic baseline behavior and zero optional provider cost. |
| Milestone 2 MCP server proxies REST rather than reading SQLite directly. | REST remains the canonical behavior boundary and MCP/REST parity is easier to enforce. |
| `MnemeRestClient` is the MCP substrate's only REST proxy wrapper. | It normalizes base URLs, bearer auth, request timeouts, REST error envelopes, and daemon transport failures before MCP tool registration begins. |
| Codex/MCP integration must not claim automatic prompt replacement. | Codex can discover and call memory tools, but prompt assembly remains runtime-owned unless a supported hook exists. |
| Use `mcp.server.fastmcp.FastMCP` for the Python MCP server baseline. | Installed `mcp==1.27.2`; this import path and `FastMCP.run` are available in the local environment. |
| Register MCP tools with installed `FastMCP.tool()` and verify via `list_tools()` / `call_tool()`. | In `mcp==1.27.2`, `FastMCP.call_tool()` returns content blocks plus a structured result dict; tests should assert the structured dict for envelope parity. |
| MCP/REST parity tests can use `httpx.ASGITransport` against the FastAPI app. | This keeps parity tests in-process, avoids localhost bind/sandbox escalation, and verifies MCP tools cross the same REST boundary. |
| Treat Mneme as a service plus adapter pattern, not as a magic universal context-engine replacement. | Full automatic context assembly requires runtime-specific adapter hooks; MCP-only integrations provide agent-callable memory tools and explicit recall. |
| Add `MNEME_HOST_ADAPTER_CONTRACT_V0.md` as a separate contract. | REST/MCP specify daemon and tool surfaces; host adapter v0 specifies integration depth, lifecycle hooks, and capability negotiation for context-engine use. |
| Redact standard REST error envelopes before returning them. | MCP tools proxy REST errors into model-visible results, so error details must not leak raw secrets from tool arguments. |
| `mneme mcp` runs only the local MCP stdio server. | The REST daemon remains an explicit separate `mneme serve` process, keeping lifecycle/control-plane startup separate from agent-facing tool transport. |
| REST capabilities advertise MCP tools through `mneme_service.tool_names`. | Keeps the public capabilities response aligned with MCP registration without making REST app import depend on the MCP SDK. |
| Codex/MCP documentation is explicitly tools-only. | Codex can call Mneme memory tools, but automatic prompt replacement requires host lifecycle hooks from `MNEME_HOST_ADAPTER_CONTRACT_V0.md`. |
| Codex adapter foundation uses MCP instructions, a repo-local skill, an AGENTS snippet, and hook config docs before automatic writes. | These are the official Codex surfaces that can make memory usage repeatable without claiming hidden prompt replacement. |
| Keep Codex MCP read-only for Phase 13 Task 2. | Hook/importer commands can write through REST under user-approved local execution, while model-callable MCP writes require a separate contract and security review. |
| Codex hook ingestion writes through REST, not MCP. | Command hooks are trusted local automation; MCP remains a read-only evidence surface until a separate write/checkpoint contract exists. |
| Real Codex hook payload discovery should use capture-only hooks first. | Capturing to `.local/` lets us inspect field shape and validate readiness without enabling automatic Mneme writes or touching global Codex config. |
| Codex ingestion starts as an offline/reference transcript importer. | It gives Mneme data for MCP retrieval while avoiding live Codex config changes and avoiding MCP write tools. |
| The first Codex ingestion input contract is explicit JSON. | It keeps the adapter reproducible and avoids parsing private Codex internals until the user approves a source path or live integration. |
| Dogfood MCP config uses absolute Python path plus `PYTHONPATH`. | It avoids relying on the user's shell PATH when Codex starts the MCP server after restart. |
| Dogfood daemon uses port `8767`. | Port `8765` was already occupied by a different local service returning `404` for `/v1/health`. |
| Dogfood daemon is managed by LaunchAgent. | Plain background launch did not keep the service reachable; launchctl keeps it alive across Codex restart. |
| Phase 13 should make Codex memory practical through ingestion plus explicit recall. | MCP tools alone retrieve memory; REST ingestion or a future approved write path must populate memory. |
| Provider config will be explicit and local-first. | Minimal mode remains default; optional external provider calls require configured providers and secret-safe handling. |
| Provider secrets are configuration inputs, never capability outputs. | Capabilities expose only `api_key_configured`; raw keys stay out of REST responses. |
| Embedding indexing is best-effort after canonical event storage. | Provider/index outages should degrade retrieval quality, not lose agent history or make ingestion fail. |
| `context_search` hybrid retrieval is REST-canonical. | REST owns retrieval behavior and MCP inherits it through the existing proxy, preventing a second ranking path. |
| Execution state updates are deterministic before enrichment exists. | The daemon can expose useful goal/current-step/tool/decision state without depending on optional LLM enrichment or Hermes internals. |
| Parity recovery should precede further Codex dogfood polish. | A useful Codex memory should dogfood semantic/execution-state retrieval, not only keyword/recency reads over persisted events. |
| Port `hermes-mneme` behavior before adapter work. | Adapters should validate and expose a mature context engine, not compensate for missing daemon features. |
| Generic session/topic drift is daemon behavior; hook plumbing is adapter behavior. | Every runtime needs topic-switch detection and resume/carry-over memory semantics, but each runtime exposes session ids and request hooks differently. |
| First mixed GitHub publication is quarantined private. | It combined engine, Codex adapter, and internal planning/dogfood material. Public release must use a clean core/adapters split. |
| Publish under Apache License 2.0. | Ivan Konstantinov selected Apache-2.0 for permissive commercial adoption with explicit patent terms. |
| Defer Hermes adapter implementation until upstream native context-engine hooks land. | A compaction-based bridge would be throwaway work and could force duplicated integration effort after the PR is accepted. |
| Treat public installability as a continuing design constraint after Phase 15. | Future users should be able to install Mneme and its adapters from GitHub with understandable automated steps, so docs/examples must avoid local-only assumptions. |
| Prefer `mneme-codex service` over `nohup` for macOS global Codex installs. | The second-machine rehearsal showed `nohup` could exit from the agent/tool environment, while a user LaunchAgent gives a durable per-account daemon lifecycle. |
| Global Codex adapter REST commands should support install-root token discovery. | A new user should not have to source `.local/mneme.env` manually for sample ingest, hook replay, or context-preview smoke after running setup. |
| Treat `mneme-memory` as a required Codex operating skill, not a hidden context hook. | The skill teaches Codex when to call Mneme MCP tools, while MCP remains tools-only and does not automatically replace prompt context. |
| Treat pre-Phase-14 comparison entries as historical audit data. | The old comparison remains valuable for rationale, but current status must be read from the new post-Phase-14 section. |
| Add MCP session discovery before session-bound memory tools. | Codex agents were guessing `session_id` values such as `default` or repo slugs because MCP exposed only tools that required an already-known internal id. `resolve_session` and `list_sessions` make discovery explicit and keep session-bound tools strict. |

## Phase 13B Session Discovery Findings

- Root cause: Mneme MCP exposed `context_search`, `fetch_event`,
  `expand_context`, `recall_recent`, `list_segments`,
  `get_execution_state`, `get_goal_history`, `explain_context`, and
  `mneme_cost_report`, all of which either required a valid internal
  `session_id` directly or depended on a trace/session that already existed.
  It did not expose a way for the agent to discover valid sessions.
- `session_id="default"` and `session_id="rlm-orchestrator"` correctly
  returned `NOT_FOUND`; those are aliases/slugs, not internal Mneme session ids.
- Existing storage already has enough data for discovery without schema
  migration: the `sessions.data` JSON includes `session_id`, `project_id`,
  runtime/agent metadata, and Codex hook/importer metadata such as `cwd` and
  optional `thread_id`.
- The global local Codex installation uses
  `/Users/openclaw/.mneme-codex/.local/mneme.db` and `127.0.0.1:8765`; it is
  separate from the repo-local dogfood database `.local/mneme-dogfood.db` on
  port `8767`.
- Events are being written in the global local Codex database: inspection found
  7 sessions and 947 non-memory-read events.
- The real `_rlm-orchestrator` session in the global local database is
  `019edb86-1d22-78a3-b9e4-e6121c294056`, with project/cwd
  `/Users/openclaw/Documents/_rlm-orchestrator`.
- Live MCP reads succeed with that real session id; `get_execution_state`
  returned `ok=true`, and `context_search` found RLM Orchestrator task/README
  evidence.
- Operational caveat: the running Codex MCP uses the installed
  `mneme-context-service` wheel in `/Users/openclaw/.mneme-codex/.venv`.
  The package is now reinstalled from the current GitHub `main`; the REST
  daemon was restarted after the functional code update, but an already-open
  Codex session may still need a new thread or MCP/Codex restart before the
  UI/tool registry lists newly added MCP tools.

## Issues Encountered

| Issue | Resolution |
|---|---|
| Initial contract had ambiguities around oversized payloads, conflicts, message schema, REST/MCP parity, and memory-read audit. | Revised `API_MCP_CONTRACT_V0.md` and created `API_MCP_CONTRACT_V0_REVIEW_RESPONSE.md`. |
| System Python lacked pytest during Milestone 1 verification. | Created local `.venv` and installed project test dependencies. |
| FastAPI dependency alias produced unexpected 422s. | Switched to explicit route dependencies. |
| App import created `mneme.db` in project root. | Removed global app side effect and made CLI responsible for daemon startup with explicit DB path. |
| Sandbox blocked local daemon bind. | Used approved escalation for localhost smoke test. |
| Direct REST memory tools currently need more complete v0 behavior before MCP parity. | Captured hardening tasks in `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`. |
| REST memory tools lacked complete MCP-parity substrate behavior. | Phase 10 Task 2 added memory-read traces/trace ids, `context_search` filters, `recall_recent` limits, `list_segments.page_size`, and shared tool names. |
| Phase 10 Task 2 review found incomplete memory exposure accounting. | Fixed `fetch_event(include_neighbors=true)` so memory-read traces/audit include seed and neighbor event ids. |
| Phase 10 Task 2 review found recent recall could prefer older events under tight token budget. | Fixed `recall_recent.max_tokens` packing to keep the newest fitting tail and return it chronologically. |
| Shell startup emits `(eval):1: command not found: +`. | Treat as local shell noise; rely on command exit code and meaningful output. |
| `pip install -e '.[test]'` failed under sandbox DNS/network restrictions when adding MCP SDK. | Re-ran the same install with approved escalation; `mcp==1.27.2` and transitive dependencies installed successfully. |
| Phase 10 Task 6 RED found MCP error results could leak a raw secret from REST error details. | Redacted `MnemeError` envelopes at the REST exception boundary; focused MCP privacy tests now pass. |
| `security-guidance` referenced ASVS files that were absent from the installed skill bundle. | Recorded the local skill issue and applied the concrete security requirements already present in the Mneme contracts. |

## Resources

- Project root: `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`.
- Concept: `MNEME_UNIVERSAL_CONTEXT_SERVICE_CONCEPT.md`.
- Implementation strategy: `IMPLEMENTATION_PATHS_AND_MVP.md`.
- API/MCP contract: `API_MCP_CONTRACT_V0.md`.
- Host adapter contract: `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
- Contract review response: `API_MCP_CONTRACT_V0_REVIEW_RESPONSE.md`.
- Architecture diagram: `mneme_universal_context_service_architecture.html`.
- Milestone 2 plan: `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`.
- Milestone 3 plan: `MILESTONE_3_CODEX_INGESTION_PLAN.md`.
- Milestone 4 plan: `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`.
- Milestone 5 plan: `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`.
- Milestone 6 plan: `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`.
- Hermes-Mneme parity comparison: `HERMES_MNEME_COMPARISON.md`.
- Read-only newer native plugin reference: `/Users/openclaw/.hermes/plugins/_hermes-mneme-native`.
- Read-only Hermes context-engine PR reference: `/Users/openclaw/.hermes/plugins/_hermes-agent-pr`.
- Codex dogfood restart setup: `adapters/codex/CODEX_DOGFOOD_RESTART_SETUP.md`.
- New-session dogfood prompt: `adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md`.
- Phase 14 autonomous next-session prompt: `NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md`.
- Planning files:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
- Official MCP SDK overview: `https://modelcontextprotocol.io/docs/sdk`.
- Official Python MCP SDK docs: `https://py.sdk.modelcontextprotocol.io/`.
- Official Python MCP SDK server docs: `https://py.sdk.modelcontextprotocol.io/server/`.
- Official Python MCP SDK testing docs: `https://py.sdk.modelcontextprotocol.io/testing/`.
- OpenAI Agents SDK MCP docs: `https://openai.github.io/openai-agents-python/mcp/`.
- OpenAI Agents SDK context docs: `https://openai.github.io/openai-agents-python/context/`.
- OpenAI Agents SDK sessions docs: `https://openai.github.io/openai-agents-python/sessions/`.
- OpenClaw architecture docs: `https://docs.openclaw.ai/concepts/architecture`.
- OpenClaw context docs: `https://docs.openclaw.ai/concepts/context`.
- OpenClaw context engine docs: `https://docs.openclaw.ai/concepts/context-engine`.
- OpenClaw agent loop docs: `https://docs.openclaw.ai/concepts/agent-loop`.
- OpenClaw system prompt docs: `https://docs.openclaw.ai/concepts/system-prompt`.
- OpenClaw memory overview: `https://docs.openclaw.ai/concepts/memory`.

## Visual/Browser Findings

- The architecture HTML diagram represents the intended high-level flow: runtime adapters ingest events, Mneme stores/retrieves context, request-only context assembly augments a single model call, and agent integrations consume REST/MCP surfaces.
- Official MCP docs confirm Python SDK is an appropriate local server implementation path for a stdio-first MCP server.

## Open Questions

1. Which exact MCP Python SDK helper names are available after installing the dependency?
   - Resolved for Task 1: `mcp.server.fastmcp.FastMCP` imports successfully and exposes `run`.
2. Should `/v1/metrics` remain optional or become required for demos and benchmarks?
   - Currently optional in v0.
3. Should `max_event_content_bytes=1048576` remain the reference daemon default?
   - Non-blocking review item from contract approval.
4. Should `mneme.message.v0` be extended before the first Hermes/LangGraph/OpenAI adapter implementations?
   - Non-blocking for Milestone 2 MCP substrate.
5. Should Codex get a narrow MCP checkpoint/write tool, or should all Codex writes remain REST-ingestion-only?
   - Open for Phase 13. Default should remain REST ingestion until the contract and security tests are updated.
6. Which provider config file format should become the default?
   - Open for Phase 14. Current planning preference is `mneme.toml` for non-secrets plus environment variables or an explicitly supported untracked `.env` path for secrets.
7. Should the next implementation milestone be renamed from Codex dogfood polish to parity recovery?
   - Resolved: yes. Phase 14 is Hermes-Mneme functional parity recovery. Codex dogfood, publication, and adapters are deferred until the daemon has the core quality pipeline.
8. Should session drift wiring wait for the Hermes adapter?
   - Resolved: split it. Host-specific hook/session-id plumbing waits for adapters; runtime-neutral session/topic drift semantics move into Phase 14 daemon parity recovery.
9. Which license should the public repository use?
   - Resolved: Apache License 2.0, with Ivan Konstantinov as the 2026 copyright owner.
10. Should work move into Hermes adapter planning now?
   - Resolved for now: no. Return to Phase 14 hardening and defer Hermes adapter work until the upstream Hermes context-engine hook PR is accepted.
