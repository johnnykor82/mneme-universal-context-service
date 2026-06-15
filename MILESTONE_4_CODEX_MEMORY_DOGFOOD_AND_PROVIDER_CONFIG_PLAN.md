# Milestone 4: Codex Memory Dogfood and Knowledge-Base Workflow

Date: 2026-06-12
Last updated: 2026-06-14
Status: active

## Goal

Make the current Codex/MCP dogfood useful as a practical knowledge-base memory
for long Codex sessions, while keeping the integration-depth claim honest:
Codex can call Mneme memory tools and can run approved local hooks, but Mneme
does not automatically replace Codex prompt context or become a hidden
pre-model-call context engine through MCP alone.

Phase 14/14B has since restored the daemon/core memory pipeline: provider
configuration, semantic retrieval, execution state, lineage, budgeted prepare,
reranking, enrichment, parity acceptance, and hardening. Phase 15 publication
prep is also complete. The remaining safe focus for this milestone is the Codex
dogfood workflow over those capabilities.

## Current Truth

- The Mneme REST daemon and MCP server are implemented and verified.
- Codex can see Mneme MCP memory tools through `mcp__mneme.*`.
- The current MCP tools are memory-read/state-read tools:
  - `context_search`
  - `fetch_event`
  - `expand_context`
  - `recall_recent`
  - `list_segments`
  - `get_execution_state`
  - `get_goal_history`
  - `explain_context`
  - `mneme_cost_report`
- Storage is populated through REST lifecycle/event ingestion, currently via
  the offline/reference `mneme codex-ingest` transcript importer.
- The daemon now supports explicit provider config, semantic retrieval,
  execution state, goal history, lineage-aware retrieval, and budgeted
  `/v1/context/prepare`.
- Provider-backed reranking and LLM enrichment remain quality-layer opt-ins.
  Minimal mode remains valid for CI/dev/fallback tests and makes no provider
  calls. Dogfood/public-readiness semantic memory requires embeddings because
  semantic retrieval, topic centroids, and drift detection depend on vectors.
- Future public GitHub users must be able to understand and install the Mneme
  service/adapters without relying on this workstation's private paths. Codex
  adapter artifacts should therefore favor package-relative examples, explicit
  commands, and automatable setup steps.
- Actual GitHub publication of the Codex hook path is gated behind local
  real-hook validation and Phase 14C full original-core parity completion. Once
  both pass, publish Mneme plus `adapters/codex` to the user's GitHub and
  immediately rehearse installation on the second Codex machine from GitHub as
  a new-user setup.
- Official Codex docs now confirm useful adapter surfaces:
  - MCP server-wide `instructions` are read during server initialization;
  - Codex skills can live in repo-local `.agents/skills`;
  - `AGENTS.md` remains the right place for always-loaded project rules;
  - hook events exist for session start/resume, user prompt submit, tool use,
    compaction, subagent stop, and turn stop, with command hooks available
    today.
- Those hooks are enough to build an approved Codex event-ingestion adapter and
  Mneme reminders, but they are not yet treated as a proven automatic prompt
  replacement path for every Codex model request.

## Non-Goals

- Do not claim automatic Codex prompt/context replacement through MCP alone.
- Do not modify live Hermes.
- Do not modify live `hermes-mneme`.
- Do not start Hermes adapter work until the upstream Hermes native
  context-engine hook PR is accepted.
- Do not build a compaction-based Hermes bridge.
- Do not add model-callable MCP writes until the contract and security tests
  explicitly cover that surface.

## Architecture Position

Codex/MCP remains `TOOLS_ONLY` for model-visible recall unless Codex provides
and we validate a runtime hook equivalent to `prepare_model_request` from
`MNEME_HOST_ADAPTER_CONTRACT_V0.md`.

Codex adapter work for this milestone is split into four explicit surfaces:

1. **MCP server instructions:** short server-wide guidance that tells Codex when
   and how to use Mneme memory tools.
2. **Repo-local skill:** `mneme-memory` instructions for long sessions,
   compaction recovery, resume behavior, and evidence-based MCP usage.
3. **AGENTS snippet:** always-loaded project guidance that reminds Codex to use
   the skill/MCP tools in Mneme projects.
4. **Hook adapter:** approved Codex command hooks that can send session, prompt,
   compaction, tool, and stop events to Mneme REST ingestion after real-session
   payloads are verified.

For practical dogfood, Mneme should support two lanes:

1. **Ingestion lane:** a Codex adapter/importer sends transcript, checkpoint, or
   session events to REST so Mneme has data to retrieve.
2. **Recall lane:** the Codex agent calls MCP memory tools when instructed by
   its operating prompt, especially after context compaction, before major
   decisions, and when resuming a long project.

For this slice, MCP remains read-only. Automatic writes should come from
trusted local hook commands or explicit importer/adapter commands, not from a
model-callable write tool. A narrow MCP checkpoint/write tool may still be useful
later, but it needs a separate contract and security-test update because
model-callable writes are a different trust surface from memory reads.

## Task 1: Codex Memory Operating Contract

**Status:** complete

Define the supported Codex behavior in docs and tests.

Deliverables:

- Update or create a Codex memory operating guide.
- State that Codex agents should call Mneme memory tools:
  - at session start or resume;
  - after compaction or context loss;
  - before choosing the next milestone;
  - before modifying files after a long interruption;
  - when a user asks what was done or why.
- State that retrieved memory is evidence, not instructions overriding current
  system/developer/user policy.
- Add checks that docs do not claim automatic prompt replacement.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_codex_mcp_usage_docs_are_tools_only_and_config_is_valid -q
rg -n "automatically replace|automatic prompt replacement|rewrites every Codex request" adapters/codex *.md
```

Result: complete. `adapters/codex/MNEME_CODEX_MCP_USAGE.md` now defines the
long-session operating contract: when to call Mneme tools, how to recover after
compaction/resume, how to use execution state, goal history, semantic search,
lineage, recent recall, and explainability, and how to treat retrieved memory
as evidence rather than instruction authority.

## Task 2: Codex Adapter Foundation

**Status:** complete

Create the repo-visible operating layer that makes Codex remember Mneme exists
and use it correctly before adding automatic hook ingestion.

Deliverables:

- Add concise MCP server instructions so Codex sees Mneme usage guidance during
  MCP initialization.
- Add repo-local `.agents/skills/mneme-memory/SKILL.md` so Codex can load a
  focused Mneme workflow for long sessions, compaction recovery, resume behavior,
  and evidence-based MCP usage.
- Add an `AGENTS.md` snippet that can be copied into project or global Codex
  rules without modifying live user configuration during this milestone.
- Add a Codex hook config/example contract that names the intended command-hook
  events and marks real-session payload validation as required before enabling
  automatic writes.
- Keep examples publication-friendly: use placeholders or package-relative
  commands, explain what must be installed, and avoid local private paths except
  where explicitly marked as local dogfood-only.
- Add tests that protect the no-overclaim boundary: MCP instructions, skill,
  AGENTS snippet, and hook example must not claim automatic prompt replacement.

Decision:

- Keep REST event ingestion canonical.
- Keep MCP read-only for Codex in this slice.
- Use Codex hooks for approved local event ingestion/reminders after validating
  real hook payloads.
- Avoid parsing private or unstable Codex internals unless the user explicitly
  approves a source path.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q
```

Result: complete. The MCP server now exports Mneme instructions through
`FastMCP(..., instructions=...)`; the repo has `.agents/skills/mneme-memory`,
`adapters/codex/AGENTS_MNEME_SNIPPET.md`, and a disabled
`adapters/codex/codex_hooks.contract.example.json`; tests enforce the
read-only/evidence contract and no automatic prompt replacement claim.

## Task 3: Codex Hook Ingestion Source

**Status:** MVP complete; local real-session payload validation, context-preview smoke, preview-hook rehearsal, and MCP recall complete

Implement the first automatic Codex data path after Task 2 establishes the
operating layer.

Completed MVP deliverables:

- `mneme codex-hook-ingest` accepts explicit hook JSON from a file or stdin.
- `mneme codex-hook-capture` captures raw hook payloads into an untracked local
  JSONL file for trusted payload discovery.
- `mneme codex-hook-validate` summarizes captured payload readiness without
  printing raw content.
- `mneme codex-hook-render-config` renders capture, dry-run, or write hook
  configs with an explicit Python runner, so local Codex hook rehearsal does
  not depend on shell `PATH`.
- `adapters/codex/codex_hooks.capture.example.json` provides a capture-only
  hook example that performs no REST writes.
- Dry-run mode prints normalized `mneme.session.v0` and
  `mneme.event_batch.v0` payloads before enabling writes.
- Write mode sends the normalized session/event batch through Mneme REST
  ingestion and attaches a local receipt timestamp when Codex stdin does not
  include one.
- `mneme codex-hook-import-capture` replays a captured hook JSONL file into
  Mneme REST ingestion for local smoke tests.
- `mneme codex-hook-prepare-preview` calls `/v1/context/prepare` from a
  `UserPromptSubmit` hook payload and writes the prepared result to a local
  JSONL preview file.
- `mneme codex-hook-render-context-preview-config` renders a per-machine
  `UserPromptSubmit` preview hook config.
- Idempotent event ids for replay-safe hook delivery.
- Redaction-through-service verification for hook-derived events.
- Documentation that hooks are disabled by default, dry-run first, and intended
  for future GitHub users through copyable commands.

Completed local real-payload validation:

- The generated local `.codex/hooks.json` capture config worked after Codex
  Desktop showed the hook trust prompt and the user approved it.
- `.local/mneme-codex-hooks.jsonl` captured `SessionStart`,
  `UserPromptSubmit`, `PostToolUse`, and `Stop`.
- Real Codex Desktop hook payloads use `hook_event_name` and omit
  `timestamp`, `summary`, and `message`; captured JSONL validation now uses
  the wrapper `captured_at` timestamp and content-bearing fields such as
  `prompt`, `tool_name`, `tool_input`, `tool_response`,
  `last_assistant_message`, `source`, `cwd`, and `model`.
- `mneme codex-hook-validate --input .local/mneme-codex-hooks.jsonl` reports
  `payload_count: 4`, `valid_for_enablement: true`, and no warnings on the
  user's local real capture.

Completed local active preview setup:

- `.codex/hooks.json` is now a local gitignored capture + REST ingest + context
  preview setup targeting the dogfood daemon on `127.0.0.1:8767`.
- `.local/codex_hooks.context_preview.local.json` was regenerated for the same
  dogfood port.
- JSON syntax and dogfood daemon health were verified.

Completed real preview-hook rehearsal:

- A new Codex session trusted the changed hooks and confirmed
  `.local/mneme-codex-context-preview.jsonl` receives an automatic preview
  record.
- MCP recall returned hook-derived Mneme data for the preview session.
- The capture file still validates with no warnings after the preview hook run.

Pending before user-facing/public hook setup:

- Convert `adapters/codex/codex_hooks.contract.example.json` from disabled
  dry-run contract into an optional install/setup artifact.
- After Phase 14C full parity completion, publish the repository plus Codex
  adapter to the user's GitHub and validate the public install path on the
  second Codex machine without relying on symlinked shared files.
- Keep MCP read-only unless a separate model-callable write contract is created.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_ingest.py tests/test_codex_adapter.py -q
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q
```

Result: MVP complete. `mneme_service/codex_hooks.py`, `mneme codex-hook-ingest`,
`mneme codex-hook-capture`, `mneme codex-hook-validate`, and
`adapters/codex/MNEME_CODEX_HOOKS_USAGE.md` provide explicit JSON/stdin
hook capture, validation, dry-run, and REST write modes. The write-oriented
example hook config remains disabled until real Codex hook payloads are
validated.

## Task 3B: GitHub Publication and Second-Machine Install Rehearsal Gate

**Status:** pending; blocked on Phase 14C full parity completion

Treat the first public GitHub publication as an installation rehearsal, not only
as a source-code backup.

Gate sequence:

1. Capture and validate real Codex hook payloads on this machine with the
   capture-only hook example.
2. Convert the hook example into an enable-ready user setup path while keeping
   dry-run and trust steps explicit.
3. Complete Phase 14C full original-core parity gate.
4. Publish Mneme plus the Codex adapter to the user's GitHub.
5. On the second Codex machine, install from GitHub as if it were a new user
   setup rather than relying on the shared symlinked files.
6. Verify per-machine runtime pieces: `mneme serve`, `mneme mcp`, auth token,
   database path, provider secrets if used, MCP visibility, hook
   capture/validation, and a simple REST-ingestion plus MCP-recall smoke path.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q
rg -n "second-machine install rehearsal|after local hook validation|GitHub" task_plan.md findings.md progress.md docs/PUBLICATION_CHECKLIST.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md
```

## Task 4: Codex Dogfood Automation

**Status:** pending

Reduce manual work around the local dogfood setup.

Candidate deliverables:

- `mneme codex-dogfood status`
- `mneme codex-dogfood import-example`
- `mneme codex-dogfood verify`
- documented LaunchAgent status checks for the REST daemon;
- a single smoke path that proves REST ingestion and MCP recall still work.

Verification:

```bash
.venv/bin/python -m pytest tests/test_codex_ingest.py tests/test_mcp_contract.py -q
.venv/bin/python -m py_compile mneme_service/*.py
```

## Task 5: Provider Configuration Surface

**Status:** complete in Phase 14 Task 1

Create an explicit configuration layer before implementing embeddings, reranking,
or LLM enrichment.

Configuration principles:

- Minimal mode remains available for CI/dev/fallback tests and makes zero
  provider calls.
- Dogfood/public-readiness mode must set `require_embeddings=true` or
  `--require-embeddings` and verify real embedding rows/cost counters.
- Non-secret provider options should live in a local config file, such as
  `mneme.toml`.
- Secrets should come from environment variables or a local untracked `.env`
  file if `.env` support is intentionally added.
- Example files must never contain real secrets.
- Config precedence should be explicit, for example:
  CLI arguments > environment variables > config file > defaults.
- Capabilities and cost reports must reflect provider enablement.
- Provider payloads and errors must be redacted before storage, traces, logs,
  and MCP-visible results.

Candidate settings:

- `MNEME_AUTH_TOKEN`
- `MNEME_BASE_URL`
- `MNEME_CONFIG`
- `MNEME_REQUIRE_EMBEDDINGS`
- `MNEME_EMBEDDINGS_ENABLED`
- `MNEME_EMBEDDING_PROVIDER`
- `MNEME_EMBEDDING_MODEL`
- `MNEME_EMBEDDING_BASE_URL`
- `MNEME_EMBEDDING_API_KEY`
- `MNEME_RERANKER_ENABLED`
- `MNEME_RERANKER_PROVIDER`
- `MNEME_LLM_ENRICHMENT_ENABLED`
- `MNEME_LLM_PROVIDER`
- `MNEME_LLM_MODEL`
- `MNEME_LLM_BASE_URL`
- `MNEME_LLM_API_KEY`

Verification:

```bash
.venv/bin/python -m pytest tests/test_config.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile mneme_service/*.py
```

Result: complete. Phase 14 Task 1 added explicit provider configuration with
CLI, environment, config-file, and default precedence; secret-safe provider
summaries; provider-aware capabilities; and `mneme.example.toml`. Later Phase
14 tasks implemented embeddings, reranking, and enrichment behind explicit
provider settings. Phase 13 dogfood later added `require_embeddings` so real
semantic-memory runs can fail fast instead of silently degrading to
keyword-only mode.

## Task 6: GitHub Publication Preparation

**Status:** complete in Phase 15

Prepare publication only after Codex dogfood and provider configuration claims
are clear.

Deliverables:

- README with honest integration-depth matrix.
- installation and local daemon guide;
- Codex MCP tools-only guide;
- provider configuration guide with secret-handling rules;
- package metadata review;
- license decision;
- CI/test command documentation;
- repository split decision:
  - core service repository;
  - optional Codex adapter package or `adapters/codex` subpackage.

Verification:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile mneme_service/*.py
rg -n "sk-[A-Za-z0-9]|api[_-]?key.*=" .
```

Result: complete. Phase 15 added README, installation/provider/testing/publication
docs, package metadata, CI workflow, Apache-2.0 `LICENSE`, `NOTICE`, and
publication scans while preserving tools-only Codex claims.

## Task 7: Hermes Adapter Planning Gate

**Status:** deferred

Start Hermes adapter planning only after the upstream Hermes native
context-engine hook PR is accepted.

Required before implementation:

- explicit user approval to inspect any live Hermes or `hermes-mneme` prototype
  files, if needed;
- a separate Hermes adapter milestone plan;
- conformance target against `MNEME_HOST_ADAPTER_CONTRACT_V0.md`;
- no changes to live Hermes until a dedicated implementation phase is approved.

Verification:

```bash
rg -n "Hermes adapter" task_plan.md progress.md findings.md
```

## Success Criteria

- A new Codex session can use Mneme as a practical searchable project memory
  through MCP tools.
- The plan clearly explains how data enters Mneme storage.
- The docs do not imply that MCP alone can rewrite every Codex request.
- Provider settings are explicit, opt-in, redacted, and covered by tests.
- GitHub publication prep is complete.
- Hermes adapter work remains deferred behind upstream native hooks.
