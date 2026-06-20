# Task Plan: Mneme Universal Context Service

## Goal

Turn the idea behind `hermes-mneme` into a vendor-neutral context-management service that any agent runtime can integrate through a clear REST/MCP contract.

## Current Phase

Phase 13: Codex memory dogfood and knowledge-base workflow - in progress; next focus is updated global Codex install rehearsal on the second machine.
Phase 13B: Codex/MCP session discovery hotfix - complete; next action is publish updated core package so global Codex MCP sees `resolve_session` and `list_sessions`.
Phase 14C: full Hermes-Mneme parity completion - complete.
Phase 14B: parity hardening while Hermes PR is pending - complete.
Phase 16: Hermes host adapter planning - deferred until upstream Hermes context-engine hook PR is accepted.
Phase 15: GitHub publication preparation - complete.
Phase 14: Hermes-Mneme functional parity recovery - complete.
Phase 13A: Hermes-Mneme parity gap audit - complete.
Phase 12: Codex MCP dogfood restart handoff - complete.
Phase 11 Codex transcript ingestion adapter MVP is complete.
Phase 10 MCP server and adapter substrate is complete.

## Operating Constraints

- Work only inside `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`.
- Do not modify live Hermes at `/Users/openclaw/.hermes/hermes-agent`.
- Do not modify live `hermes-mneme` at `/Users/openclaw/.hermes/plugins/hermes-mneme`.
- Treat existing Hermes/Mneme code as prototype evidence, not final universal-service design.
- Keep claims benchmarkable and record verification commands in `progress.md`.
- Be explicit about overhead: embedding, storage, optional reranking, optional LLM enrichment.
- Treat embeddings as required for dogfood/public-readiness semantic memory.
  Minimal provider-free mode remains available only for CI/dev/fallback tests,
  not as the quality target inherited from `hermes-mneme`.
- Use `planning-with-files`: reread `task_plan.md`, `findings.md`, and `progress.md` before major work; update them after every completed phase or important discovery.
- For Phase 14C, continue through the milestone without stopping after each
  task. Stop only on a real blocker or a user question whose answer is not
  discoverable in original `hermes-mneme`.
- Design docs, examples, CLIs, and adapter setup for future public GitHub users:
  installation should be automatable, understandable, and not depend on this
  developer machine's private paths or live Hermes state.
- Public publication must keep product boundaries clean: the Mneme engine/core
  repository is separate from host adapters, and each adapter belongs in its
  own repository/package such as a future Codex adapter repository. Internal
  dogfood notes, local rehearsal prompts, and project planning files are not
  user-facing GitHub installation artifacts.
- Local real Codex Desktop hook validation, REST/context-preview smoke, real
  preview-hook rehearsal, and MCP recall now pass. Do not claim automatic Codex
  prompt insertion: current documented Codex command hooks can prepare/write
  preview files, but no context-build prompt replacement hook is documented.
  Phase 14C full original-core parity completion is complete. The first mixed
  GitHub publication accidentally combined engine, Codex adapter, and internal
  planning materials; it has been quarantined as a private repository and must
  not be treated as the public install source. The clean engine/core public
  repository `johnnykor82/mneme-universal-context-service` is now published
  from a sanitized root commit. The separate Codex adapter repository/package
  `johnnykor82/mneme-codex-adapter` is also published from a sanitized root
  commit. Next work is second-machine rehearsal.
- Support the user's two-machine Codex workflow: shared symlinked files may
  propagate docs/skills/config examples, but Mneme runtime installation, daemon,
  MCP config, tokens, database paths, and hook trust must be verified per
  machine.
- Second-machine developer-style install rehearsal passed, but showed the
  GitHub docs were still too developer-oriented for ordinary Codex Desktop
  users. The next rehearsal should use the new user-global Codex quickstart and
  `mneme-codex setup/doctor/status` path rather than a workspace-only sandbox
  install.
- Second-machine global install feedback polish is published in the Codex
  adapter repository at commit `47a2127`: the global flow now has
  install-root token resolution, macOS LaunchAgent service commands,
  install-root entrypoint checks in doctor/status, generated `mneme.toml`,
  provider configuration guidance, and clearer MCP-vs-plugin wording.
- Required `mneme-memory` skill install polish is published in the Codex
  adapter repository at commit `2a76286`: the adapter package now includes the
  skill as package data and exposes `mneme-codex skill install`, and public
  install docs make the skill required for expected Codex behavior.

## Phases

### Phase 1: Concept Document

- [x] Define product thesis, target users, architecture, API contract, benchmarks, and cost model.
- [x] Create `MNEME_UNIVERSAL_CONTEXT_SERVICE_CONCEPT.md`.
- **Status:** complete

### Phase 2: Presentation Diagram

- [x] Create a polished architecture diagram showing ingestion, storage, retrieval, context assembly, and agent integration.
- [x] Create `mneme_universal_context_service_architecture.html`.
- **Status:** complete

### Phase 3: Follow-Up Design Session

- [x] Open a separate Codex thread to refine implementation paths, MVP scope, and go-to-market positioning.
- [x] Record follow-up decisions in project docs.
- **Status:** complete

### Phase 4: Implementation Paths and MVP

- [x] Compare implementation paths.
- [x] Recommend the first credible MVP.
- [x] Create `IMPLEMENTATION_PATHS_AND_MVP.md`.
- **Status:** complete

### Phase 5: API/MCP Contract v0

- [x] Create `API_MCP_CONTRACT_V0.md`.
- [x] Cover REST endpoints, MCP tools, shared schemas, context preparation, traces, cost reporting, errors, security/privacy, adapter contract tests, and compatibility strategy.
- **Status:** complete

### Phase 6: Spec Review and Approval Gate

- [x] Review `API_MCP_CONTRACT_V0.md`.
- [x] Resolve first external review findings.
- [x] Prepare revised draft and reviewer response.
- [x] Receive second external review accepting the contract as a basis for implementation.
- **Status:** complete

### Phase 7: Milestone 1 Implementation Planning

- [x] Create a detailed implementation plan for the first milestone.
- [x] Keep live Hermes and live `hermes-mneme` out of scope.
- **Status:** complete

### Phase 8: Milestone 1 Local Daemon MVP

- [x] Implement local Python `mneme-context-service` daemon.
- [x] Implement REST contract v0, SQLite storage, lexical/recency retrieval, request-only context preparation, traces, costs, export/delete, and contract tests.
- [x] Verify with pytest, py_compile, and daemon smoke test.
- [x] Keep MCP server, Hermes adapter, Codex/MCP adapter, benchmarks, embeddings, reranking, and LLM enrichment out of this milestone.
- **Status:** complete

### Phase 9: Milestone 2 Planning

- [x] Create `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`.
- [x] Plan MCP tool server and Codex/MCP adapter substrate on top of the REST daemon.
- [x] Incorporate subagent review findings around MCP/REST parity, memory-read traces, REST tool hardening, error envelopes, audit behavior, redaction, and honest Codex compatibility claims.
- **Status:** complete

### Phase 9A: Host Adapter Contract v0 Alignment

- [x] Resolve the universal thin-layer question for future context-engine integrations.
- [x] Create `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
- [x] Clarify that REST/MCP are service surfaces, while deep context-engine behavior requires host lifecycle hooks.
- [x] Link the new host adapter contract from `API_MCP_CONTRACT_V0.md`.
- [x] Record the decision in planning files before continuing MCP implementation.
- **Status:** complete

### Phase 10: Milestone 2 MCP Server and Adapter Substrate

- [x] Record Host Adapter Contract v0 alignment so MCP substrate does not overpromise prompt control.
- [x] Harden REST memory tool substrate before MCP parity.
- [x] Add official MCP Python SDK dependency and baseline import/discovery test.
- [x] Add async REST proxy client for MCP tools.
- [x] Add local stdio MCP server exposing all v0 memory tools.
- [x] Add MCP/REST parity tests.
- [x] Verify MCP memory reads create audit records, `MEMORY_READ` events, and memory-read traces through REST.
- [x] Add `mneme mcp` CLI subcommand.
- [x] Add Codex/MCP usage guide and example config without claiming automatic prompt replacement.
- [x] Update capabilities once MCP is implemented.
- [x] Run full verification and record results.
- **Status:** complete

### Phase 11: Codex Transcript Ingestion Adapter MVP

- [x] Create a Milestone 3 plan for safe Codex transcript ingestion.
- [x] Add a dependency-free Codex transcript normalizer that produces `mneme.session.v0`, `mneme.event_batch.v0`, and optional `mneme.turn.v0` payloads.
- [x] Add tests proving session start, event replay idempotency, unknown-session prevention by session bootstrapping, turn completion, and redaction-through-service for the reference adapter path.
- [x] Add a CLI import command that sends a provided transcript JSON file to the running REST daemon.
- [x] Document that this is an offline/reference `EVENT_INGEST` path and does not modify live Codex configuration.
- [x] Run focused tests, full pytest, and py_compile.
- **Status:** complete

### Phase 12: Codex MCP Dogfood Restart Handoff

- [x] Create a restart setup guide for running Mneme REST, importing a transcript, configuring Codex MCP, and restarting Codex.
- [x] Create a dogfood MCP config example using absolute `.venv/bin/python` and `PYTHONPATH`.
- [x] Create a ready-to-send prompt for the new Codex session.
- [x] Validate the dogfood MCP config JSON.
- [x] Install and load a local LaunchAgent for the Mneme REST dogfood daemon.
- [x] Import the example Codex transcript into the dogfood daemon.
- [x] Update `/Users/openclaw/.codex/config.toml` with `[mcp_servers.mneme]` and create a backup.
- [x] Verify REST search/fetch and MCP in-process search against the imported transcript.
- [x] Update planning files with the handoff status.
- **Status:** complete

### Phase 13: Codex Memory Dogfood and Knowledge-Base Workflow

- [x] Create `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`.
- [x] Define the Codex memory operating contract for long sessions, compaction recovery, and resume behavior.
- [x] Implement the Codex adapter foundation: MCP server instructions, repo-local `mneme-memory` skill, AGENTS snippet, and hook config contract.
- [x] Keep the Codex adapter foundation publication-friendly: future users should be able to install/configure it from GitHub with clear automated steps.
- [x] Implement the first Codex hook ingestion command MVP so approved hook/session JSON can enter Mneme through REST without manual copy/paste.
- [x] Add capture/validation tooling for real Codex hook payload discovery without enabling writes.
- [x] Add a local hook config renderer and install capture-only
      `.codex/hooks.json` for trusted local Codex hook rehearsal.
- [x] Document the two-machine/symlink Codex setup constraint and per-machine Mneme install/verify requirement.
- [ ] Validate real Codex hook payloads and convert the disabled hook contract example into an enable-ready user setup path.
- [x] After local hook validation and Phase 14C full parity completion, attempt
      first GitHub publication.
- [x] Quarantine the first mixed publication as private because it combined
      engine, Codex adapter, and internal planning/dogfood material.
- [x] Prepare a clean public Mneme engine/core repository without host-specific
      adapters or internal planning files:
      `johnnykor82/mneme-universal-context-service`.
- [x] Prepare a separate Codex adapter repository/package that depends on the
      Mneme engine/core and contains Codex-specific hooks, skills, and setup:
      `johnnykor82/mneme-codex-adapter`.
- [x] Read the second-machine install feedback from shared Codex files and
      identify public-install UX gaps: linear Codex Desktop quickstart, install
      scope, daemon lifecycle, MCP registration, hook ladder, doctor/status,
      and safe uninstall/reinstall expectations.
- [x] Add the first user-global Codex Desktop setup path:
      `mneme-codex setup codex-desktop --global`, `mneme-codex doctor`,
      `mneme-codex status`, generated local runtime files, token-safe MCP
      snippets, sample transcript smoke input, and a quickstart.
- [x] Publish the updated Codex adapter/core docs to GitHub for the next
      second-machine global install rehearsal.
- [x] Apply the first global-install feedback polish to the Codex adapter:
      token-safe sample ingest via `--install-root`, `mneme-codex service`
      LaunchAgent commands, install-root entrypoint checks, generated
      `mneme.toml`, provider setup docs, and MCP/plugin clarification.
- [x] Add an explicit required `mneme-memory` skill installation path to the
      Codex adapter package and public install docs.
- [ ] Rerun a second-machine global install rehearsal from the clean public
      engine/adapter repositories as a new-user flow.
- [x] Before publication/second-machine rehearsal, run a real provider smoke
      proving dogfood embeddings are required and working, embedding rows are
      written on ingest, and enabled reranker calls succeed.
- [ ] Before publication/second-machine rehearsal, clarify and verify the LLM
      surface: current daemon supports structured LLM enrichment, not a
      separate natural-language answer-synthesis endpoint.
- [x] Decide whether MCP should remain read-only for Codex or gain a narrow audited checkpoint/write tool for this slice.
- [ ] Automate dogfood status/import/verify steps where feasible.
- [x] Update Codex prompts/docs so agents use Mneme memory tools as evidence, not as hidden prompt authority.
- [x] Run Phase 13 Task 1 focused Codex/MCP tests, full pytest, parity acceptance, compileall, and text hygiene scans.
- [x] Run Phase 13 Task 2 focused adapter tests, MCP focused tests, full pytest, parity acceptance, compileall, and text hygiene scans.
- [x] Run Phase 13 Task 3 hook-ingestion focused tests, Codex/MCP regression tests, full pytest, parity acceptance, compileall, and text hygiene scans.
- [ ] Run focused tests, full pytest, and compileall after the next ingestion/automation implementation.
- **Status:** in progress after Phase 14/14B parity recovery; Codex adapter foundation, hook-ingestion MVP, hook capture/validation harness, and local capture hook config rendering are complete; next safe focus is starting a trusted Codex session to capture and validate real hook payloads.

### Phase 13A: Hermes-Mneme Parity Gap Audit

- [x] Inspect live `hermes-mneme` read-only for context-engine functionality.
- [x] Compare `hermes-mneme` and universal service by feature, mechanics, and logic.
- [x] Create `HERMES_MNEME_COMPARISON.md`.
- [x] Identify parity gaps: semantic search, provider config, embedding index, reranking, LLM enrichment, execution state, segmentation, intent routing, graph scoring, and budgeted prompt assembly.
- [x] Recommend reordering the next implementation milestone toward parity recovery before further Codex dogfood polish.
- **Status:** complete

### Phase 13B: Codex/MCP Session Discovery Hotfix

- [x] Diagnose why Codex agents guessed Mneme `session_id` values such as `default` or project slugs.
- [x] Confirm existing MCP memory tools required a valid internal `session_id` and did not expose a discovery/resolve path.
- [x] Confirm Codex hook/importer sessions already store enough metadata for discovery: `session_id`, `project_id`, `metadata.cwd`, and optional `metadata.thread_id`.
- [x] Add REST/MCP read-only discovery tools:
      `resolve_session` and `list_sessions`.
- [x] Improve `Session not found` details so `NOT_FOUND` tells agents to use discovery tools and includes bounded candidate sessions.
- [x] Update `mneme-memory` skill, Codex MCP usage docs, AGENTS snippet, and dogfood handoff docs to forbid guessing `session_id`.
- [x] Add `docs/MNEME_DEVELOPMENT_SPEC.md` as the reviewer-facing project specification/index and link it from `README.md`.
- [x] Verify the global local Codex database has sessions and that the real `_rlm-orchestrator` session id is
      `019edb86-1d22-78a3-b9e4-e6121c294056`.
- [x] Run focused REST/MCP tests and syntax checks.
- **Acceptance criteria:** a new Codex/MCP agent can find or resolve a valid Mneme session id using project path, thread id, slug, or query before calling session-bound memory tools.
- **Verification:** focused `pytest` for REST/MCP discovery passed; `py_compile` passed; live MCP read succeeded with the real `_rlm-orchestrator` session id.
- **Status:** complete; publication/install update still required for the already-installed global Codex MCP environment.

### Phase 14: Hermes-Mneme Functional Parity Recovery

- [x] Create `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`.
- [x] Port provider configuration foundation.
- [x] Port embedding provider and index.
- [x] Replace keyword-only retrieval with hybrid semantic/keyword/recency retrieval.
- [x] Port execution state and goal history.
- [x] Port segmentation, intent classification, and runtime-neutral session/topic drift semantics.
  - [x] Slice A: deterministic continuation/switch/clarification classifier and explicit topic-switch segment rollover.
  - [x] Slice B: high embedding-drift `NEW_TASK` classification and segment rollover with event-driven segment embedding ids.
  - [x] Slice C: redacted `SEGMENT_DRIFT` traces for explicit-switch and embedding-drift segment rollover decisions.
  - [x] Slice D: additive fresh/resume session-start classification from adapter lifecycle metadata and existing daemon state.
  - [x] Slice E: lineage/carry-over retrieval across explicit parent/previous session edges without copying canonical events.
  - [x] Slice F: one-shot first-turn resume context fill through `/v1/context/prepare`.
- [x] Port typed event graph and dependency scoring.
  - [x] Slice A: persist typed graph edges from parent event relationships and use them in `expand_context`.
  - [x] Slice B: add graph dependency candidates and bonuses to `context_search` ranking.
- [x] Upgrade `/v1/context/prepare` to budgeted context assembly.
  - [x] Slice A: insert a budgeted, request-only execution-state block when non-empty state fits `execution_state_ratio`.
  - [x] Slice B: protect recent-tail request messages and account for tail tokens.
  - [x] Slice C: pack retrieved context under `retrieved_context_ratio` with selected/dropped trace metadata.
  - [x] Slice D: resolve collisions across state, tail, retrieved context, and headroom.
- [x] Port optional reranker.
- [x] Port optional LLM enrichment.
- [x] Add parity acceptance suite.
- [x] Run focused tests, full pytest, and py_compile after each implementation slice.
- **Status:** complete

### Phase 14B: Parity Hardening While Hermes PR Is Pending

- [x] Create `MILESTONE_5B_PARITY_HARDENING_PLAN.md`.
- [x] Refresh `HERMES_MNEME_COMPARISON.md` with post-Phase-14 parity status.
- [x] Add adapter-independent benchmark harness for ingestion, retrieval, and budgeted context preparation.
- [x] Expand provider robustness acceptance without real provider calls.
- [x] Document or test the optional `sqlite_vec` acceleration posture without making it mandatory.
- [x] Run focused checks, full pytest, parity acceptance, compileall, and planning scans.
- **Status:** complete

### Phase 14C: Full Hermes-Mneme Parity Completion

- [x] Audit remaining runtime-neutral differences between universal Mneme and
      original `hermes-mneme`.
- [x] Create `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`.
- [x] Refresh parity harness and comparison docs with exact remaining gaps.
- [x] Add missing config knobs from original `hermes-mneme`.
- [x] Complete embedding/index parity including optional `sqlite_vec`, global
      search, model reindex, and configurable compression.
- [x] Complete segmentation/intent/router parity.
- [x] Complete execution-state, lineage, and recovery parity.
- [x] Complete LLM enrichment parity: `topic_tags`, decision rationale,
      decision summary, robust JSON recovery, and scheduled/background runs.
- [x] Complete `/v1/context/prepare` prompt-builder parity for future deep
      host adapters, without claiming Codex automatic prompt replacement.
- [x] Complete MCP/REST tool parity for richer search, segments, state, fetch,
      expand, and goal history behavior.
- [x] Run real provider dogfood gate for embeddings/reranker and context
      preparation; verify LLM enrichment by provider tests and keep real LLM
      smoke as a release-claim gate when an LLM provider is configured.
- [x] Refresh publication/install docs after parity is restored.
- **Status:** complete; original-core daemon/core parity no longer blocks
  GitHub publication/second-machine rehearsal. Real LLM provider smoke remains
  a release claim gate only if LLM enrichment is enabled/configured for that
  candidate.

### Phase 15: GitHub Publication Preparation

- [x] Prepare README, installation docs, Codex tools-only guide, provider configuration guide, package metadata, and CI/test documentation after Phase 14.
- [x] Select and add a project license before public open-source publication.
- [x] Decide whether Codex adapter publication is a separate package/repository or remains under `adapters/codex`.
- [x] Scan docs/examples for secret leakage and overclaims before publication.
- **Status:** complete

### Phase 16: Hermes Host Adapter Planning Gate

- [ ] Create a dedicated Hermes adapter milestone plan after Phase 14 parity recovery.
- [ ] Require explicit user approval before inspecting or using live Hermes or live `hermes-mneme` prototype paths.
- [ ] Map the Hermes adapter to `MNEME_HOST_ADAPTER_CONTRACT_V0.md` conformance tests.
- [ ] Do not modify live Hermes or live `hermes-mneme` until a dedicated implementation phase is explicitly approved.
- **Status:** deferred until upstream Hermes context-engine hook PR is accepted; avoid duplicate work against the legacy compaction path

## Key Questions

1. Which MCP SDK APIs are available in the installed Python package version?
   - Answer: `mcp==1.27.2` is installed; `mcp.server.fastmcp.FastMCP` imports successfully and exposes `run`.
2. Should MCP call REST over HTTP or share internal storage/service functions?
   - Answer: MCP should proxy REST for Milestone 2; REST stays canonical and MCP must not read SQLite directly.
3. Which REST tool gaps must be hardened before MCP parity?
   - Answer: resolved in Phase 10 Task 2: memory-read traces, `trace_id`, basic `context_search` filters, `recall_recent` token/tool-output limits, and `list_segments.page_size`.
4. What should Codex/MCP integration honestly promise?
   - Answer: agent-callable memory tools only; no automatic prompt replacement unless a runtime exposes a supported hook.
5. Can Mneme provide a universal thin layer for future context-engine integrations?
   - Answer: yes, as a host adapter contract and optional reference adapter layer. Existing agents still need thin native adapters; new agents can implement the contract directly.
6. Can current Codex MCP integration automatically collect and inject context for every request like a deep context engine?
   - Answer: no. Current Codex/MCP is `TOOLS_ONLY`: agents can call Mneme memory tools, but automatic prompt/request replacement requires a Codex runtime hook equivalent to `prepare_model_request`.
7. How does data enter Mneme storage for Codex?
   - Answer: through REST lifecycle/event ingestion. The current path is the offline/reference `mneme codex-ingest` importer; Phase 13 must choose and automate the next Codex ingestion source path.
8. Where are embedding and LLM provider settings stored today?
   - Answer: Phase 14 added explicit provider settings through config file, environment, and CLI precedence. Minimal mode remains provider-free for CI/dev/fallback tests, but dogfood/public-readiness semantic memory now requires embeddings through `require_embeddings`; provider settings are documented in `docs/PROVIDER_CONFIGURATION.md` and `mneme.example.toml`.
9. Is the current universal service functionally equivalent to `hermes-mneme`?
   - Answer: the runtime-neutral daemon/core parity pipeline is now largely recovered after Phase 14/14B: provider config, embeddings, hybrid retrieval, execution state, segmentation, lineage, graph scoring, budgeted prepare, reranking, enrichment, benchmarks, and acceptance evidence. The remaining major gap is host integration depth, especially Hermes adapter hooks.
10. Are we changing direction before adapter work?
   - Answer: yes. The next milestone is functional parity recovery: port the runtime-neutral core behavior from `hermes-mneme` into the universal daemon before continuing Codex/Hermes/other adapters.
11. Should session drift wiring live only in the Hermes adapter?
   - Answer: no. Host-specific hook wiring stays in adapters, but runtime-neutral drift semantics belong in the daemon: semantic topic drift, segment boundaries, resume/fresh-session classification, lineage/carry-over policy, first-turn resume context fill, and traces.
12. Is the repository ready for public open-source publication?
   - Answer: publication-prep materials exist and Phase 14C is complete, but the first mixed publication exposed the wrong product boundary. Public release now requires a clean split: engine/core repo separately, host adapters separately, and internal planning/dogfood material excluded.
13. Should Hermes adapter planning/implementation start now?
   - Answer: no. It is deferred until the upstream Hermes context-engine hook PR is accepted. Building against the legacy compaction path would create duplicate/throwaway integration work.
14. When should Mneme and the Codex adapter be published to GitHub?
   - Answer: after local trusted Codex hook payload validation, enable-ready
     setup docs, and Phase 14C full parity completion, but not as one mixed
     public repository. Mneme engine/core should publish first as clean
     `johnnykor82/mneme-universal-context-service`; Codex should publish as
     separate `johnnykor82/mneme-codex-adapter`; then the second machine should
     test installing both as if by a new user.

## Decisions Made

| Decision | Rationale |
|---|---|
| REST is lifecycle/control-plane; MCP is agent-facing memory tool surface. | Keeps ingestion/session/context preparation explicit while giving tool-first runtimes a narrow memory interface. |
| Context preparation is request-only. | Prevents Mneme-generated context from mutating the canonical transcript. |
| SQLite is the only Milestone 1 storage backend. | Keeps local daemon MVP small and inspectable. |
| Milestone 1 excludes embeddings/reranking/LLM enrichment. | Establishes a deterministic baseline before optional cost-bearing providers. |
| MCP server will proxy REST in Milestone 2. | Avoids a second behavior path and validates the same daemon boundary external adapters will use. |
| Codex/MCP guidance must not claim prompt-control capabilities. | Codex MCP tools are agent-callable; internal prompt assembly is runtime-owned. |
| Mneme has a separate Host Adapter Contract v0. | REST/MCP define the service; deep context-engine behavior requires host lifecycle hooks and capability negotiation. |
| Codex ingestion will start as an offline/reference transcript importer. | Gives Mneme data for MCP retrieval without touching live Codex config or claiming automatic context-engine integration. |
| Dogfood MCP config uses absolute Python path plus `PYTHONPATH`. | Lets Codex start `mneme_service.cli mcp` from any working directory after restart without depending on shell PATH. |
| Codex dogfood should be practical memory, not a hidden prompt hook. | The agent can search/fetch Mneme memory through MCP, but current Codex cannot be honestly described as automatic context replacement. |
| Provider configuration must precede embeddings/reranking/LLM enrichment. | Different users will have different providers and secrets; minimal mode must remain provider-free and secret-safe by default. |
| Embedding indexing is daemon-safe and provider-optional. | Events are stored first, provider/index failures are costed as degraded embedding failures, and minimal mode still makes no provider calls. |
| Hybrid retrieval is REST-canonical and MCP inherits it through the proxy. | `context_search` combines semantic candidates with keyword/recency fallback on the REST surface; MCP parity remains the existing REST proxy contract. |
| Execution state and goal history are versioned memory tools. | The daemon exposes `mneme.execution_state.v0` and `mneme.state_history_entry.v0` through REST/MCP tools instead of copying Hermes-specific tool internals. |
| Next implementation should recover `hermes-mneme` quality-pipeline parity before more Codex polish. | Codex dogfood should exercise real semantic/execution-state memory, not only keyword/recency retrieval over a database. |
| Adapter work is paused until functional parity recovery. | Adapters should connect to a real Mneme context engine, not to a keyword-only storage substrate. |
| Session/topic drift semantics belong in the daemon, while host hook plumbing belongs in adapters. | Drift is part of memory quality for every runtime; adapters should only translate runtime lifecycle events into Mneme lifecycle metadata. |
| First mixed GitHub publication is quarantined private. | It combined engine, Codex adapter, and internal planning/dogfood material. Public release must use a clean core/adapters split. |
| Public open-source release required an owner-selected license. | License choice was a legal/product decision; Ivan Konstantinov selected Apache-2.0. |
| Defer Hermes adapter work until upstream native hooks land. | The clean integration depends on Hermes context-engine lifecycle hooks; building against compaction now risks duplicate work and later rewrites. |
| Keep the pre-Phase-14 comparison as historical context, but add current status above it. | The old table explains why parity recovery happened, but post-Phase-14 readers need a current residual-gap view. |

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| System Python lacked pytest during Milestone 1 verification. | 1 | Created project `.venv` and installed `.[test]`. |
| FastAPI dependency alias produced auth-related 422s during Milestone 1 tests. | 1 | Replaced the alias with explicit `Depends(require_auth)` parameters. |
| Importing `mneme_service.app` created default `mneme.db` in project root. | 1 | Removed global app creation, started daemon only through CLI with explicit DB path, deleted generated artifact. |
| Sandbox blocked localhost daemon bind. | 1 | Re-ran daemon smoke with approved escalation for local port bind. |
| Shell startup prints `(eval):1: command not found: +` before command output. | 1 | Treat as environment noise; command exit codes and outputs remain usable. |
| `pip install -e '.[test]'` failed in sandbox due DNS/network restriction. | 1 | Re-ran the same command with approved escalation and installed `mcp==1.27.2`. |
| MCP error results could echo a raw secret from a missing event id in REST error details. | 1 | Redacted `MnemeError` envelopes at the REST exception boundary before MCP receives them. |
| Task 9 daemon smoke bind failed in sandbox with `operation not permitted`. | 1 | Re-ran the same local daemon smoke with approved escalation for `127.0.0.1:8766`. |
| Task 9 Python MCP smoke could not connect to the local daemon from sandbox. | 1 | Re-ran the same MCP smoke script with approved escalation; real daemon MCP search passed. |
| `git diff` failed because this workspace path is not a git repository. | 1 | Treated git diff as unavailable and used targeted file inspection plus tests for verification. |
| Port `8765` returned `404` for `/v1/health`, indicating another local service was already bound there. | 1 | Used dogfood port `8767` for Mneme REST and MCP config. |
| Background `nohup` daemon launch did not keep the service reachable. | 1 | Installed a macOS LaunchAgent from `.local/com.openclaw.mneme-dogfood.plist`. |
| `sqlite_vec` is not installed in the project `.venv`. | 1 | Phase 14 Task 2 verified the Python cosine fallback path; optional vector acceleration remains unexercised in this environment. |
| `security-guidance` ASVS reference files were missing from the installed skill bundle. | 1 | Applied the project's concrete security contract directly: redaction before provider/indexing, parameterized SQL, no secret leakage, and no hidden provider calls in tests. |

## Success Criteria

- Planning files answer the 5-question reboot check after context loss.
- Each milestone has a clear status and next action.
- Every implementation phase records tests, smoke checks, warnings, and non-goals in `progress.md`.
- All architectural choices that affect future agents are captured in `findings.md`.
- Live Hermes and live `hermes-mneme` remain untouched unless a later explicit phase changes that constraint.

## Notes

- Primary source-of-truth docs are `task_plan.md`, `progress.md`, `findings.md`, `API_MCP_CONTRACT_V0.md`, `MNEME_HOST_ADAPTER_CONTRACT_V0.md`, and the active milestone plan.
- `HERMES_MNEME_COMPARISON.md` records the current parity gap and should be read before choosing the next implementation phase.
- `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md` is the execution guide for the next implementation phase.
- `NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md` is the restart/handoff prompt for continuing Phase 14 without waiting for a user "continue" after every task.
- `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` is deferred until semantic/execution-state memory is available in the daemon.
- Update `progress.md` immediately after every completed phase, verification run, blocker, or important discovery.
