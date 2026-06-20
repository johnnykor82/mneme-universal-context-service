# Progress Log: Mneme Universal Context Service

## 2026-06-18 - RLM Orchestrator Architecture Review Draft

- Created `docs/RLM_ORCHESTRATOR_DEVELOPMENT_SPEC.md` as an architecture
  review draft for a separate `rlm-orchestrator` product.
- Captured the agreed boundary: orchestrator is a read-oriented information
  source for external agents, not an actor that modifies project files,
  databases, git state, or configs.
- Captured the allowed write scope: bounded run-state files inside the
  orchestrator workspace only, required from MVP 1 for resume/progress/audit.
- Captured the phased MVP plan: design/contract, read-only local+Mneme,
  recursion/workers/progress/resume, controlled terminal/read-only DB, web and
  external MCP sources, external agent interface, comparative benchmarks.
- Updated `findings.md` with the RLM Orchestrator proposal findings.
- Incorporated architecture review feedback into spec v0.2:
  explicit OpenAI-compatible/LiteLLM-friendly model provider config,
  deterministic static MVP 1 planner, Mneme hard dependency/fail-closed
  behavior, stricter redaction policy, evidence freshness, shared budget ledger,
  self-reported confidence fields, loop prevention, and stronger MVP 1
  quality/evidence coverage criteria.
- Incorporated follow-up review feedback into spec v0.3: status is now
  approved for MVP 1 planning, model config uses `CONFIGURE_ME`, fast-path
  heuristics avoid vague "narrow lookup" wording, MVP 1 static planner has
  deterministic subtemplates, MVP 1 includes an automated baseline comparison
  runner, and cancellation semantics are defined before MVP 2 parallel workers.

## Current Snapshot

- **Current phase:** Phase 13 - Codex memory dogfood and corrected GitHub publication split.
- **Current status:** Phase 14C full Hermes-Mneme daemon/core parity completion is complete; publication is no longer blocked by original-core parity. The first mixed GitHub publication was quarantined as private because it combined engine, Codex adapter, and internal planning/dogfood material. Hermes adapter work remains deferred until upstream native context-engine hooks are accepted.
- **Next action:** rerun the second-machine install rehearsal as a user-global
  Codex Desktop setup from the updated public Codex adapter commit `2a76286`,
  using `mneme-codex setup`, `mneme-codex service`, `mneme-codex doctor`, and
  provider-capability checks.
- **Active plan:** Phase 13 publication split correction after `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md` completion.
- **Primary source files:** `task_plan.md`, `findings.md`, `progress.md`, `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`, `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`, `adapters/codex/MNEME_CODEX_MCP_USAGE.md`, `API_MCP_CONTRACT_V0.md`, `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
- **Hard constraints:** do not touch live Hermes or live `hermes-mneme`; work only in `_mneme-universal-context-service`.
- **Publication constraint:** future GitHub users must get clear, preferably automated installation/configuration steps; avoid private local-path assumptions in reusable docs/examples; keep the engine/core repository separate from host adapter repositories/packages and keep internal planning/dogfood files out of public install artifacts.
- **Publication rehearsal gate:** local real-hook validation,
  REST/context-preview smoke, real preview-hook rehearsal, MCP recall, and real
  embedding/reranker smoke now pass. Full original-core parity also passes;
  clean core and separate Codex adapter publication are complete; the first
  global-install feedback polish and required skill-install polish are
  published; second-machine new-user install rehearsal is the next gate.
- **Multi-machine constraint:** the user has two Codex machines sharing files
  through symlinks; Mneme runtime setup must be installed and verified
  per-machine, not assumed from shared files.

### Second-Machine Install Feedback Response

- **Status:** first packaging response complete; superseded by the
  `47a2127` global-install feedback polish below
- Actions taken:
  - Read shared feedback files:
    `/Users/openclaw/CodexShared/mneme-install-events.md` and
    `/Users/openclaw/CodexShared/mneme-codex-install-handoff-for-developer.md`.
  - Confirmed the second-machine install worked as developer alpha:
    core tests passed, adapter tests passed, daemon health worked outside
    sandbox, ingest/search/fetch/recall/state checks worked, and no global
    Codex config/hooks were enabled.
  - Added `mneme_service/codex_setup.py` with a first user-global Codex Desktop
    setup/status layer.
  - Added CLI entries for `codex-setup codex-desktop --global`,
    `codex-doctor`, and `codex-status` in the internal checkout. The public
    adapter export maps these to `mneme-codex setup codex-desktop --global`,
    `mneme-codex doctor`, and `mneme-codex status`.
  - Added `adapters/codex/CODEX_DESKTOP_QUICKSTART.md`.
  - Updated adapter-facing docs/examples to use `mneme-codex` commands and to
    include a setup-generated sample transcript for smoke tests without a
    source checkout.
  - Kept setup token-safe: it writes `.local/mneme.env` with mode `0600`,
    writes MCP snippets that do not include the token, does not silently edit
    Codex config, and renders capture-only hook examples.
- Verification:
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`:
    `10 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_codex_hooks.py -q`:
    `33 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`:
    passed.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`:
    `135 passed, 1 warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q`:
    `5 passed, 1 warning`.
  - Adapter public export tests with public core export on `PYTHONPATH`:
    `30 passed`.
  - Adapter public export compileall: passed.
  - Core public export compileall and parity acceptance: passed.
  - Conflict marker and trailing whitespace scans over internal/exported
    touched files: no matches.
  - Old public-facing `mneme codex-*` command scan: no matches outside a
    local dogfood-only restart note.
- Next gate:
  - Build clean public exports, run export tests, push updated core/adapter to
    GitHub, then ask the second agent to rerun installation using the global
    quickstart rather than a workspace-only venv.

### Updated Public Core/Adapter Publication

- **Status:** complete
- Actions taken:
  - Updated the clean public core export with a neutral link to the separate
    Codex adapter repository.
  - Updated the clean public Codex adapter export with:
    `mneme-codex setup codex-desktop --global`, `mneme-codex doctor`,
    `mneme-codex status`, `CODEX_DESKTOP_QUICKSTART.md`, generated token-safe
    install-root files, sample transcript smoke input, and adapter version
    `0.1.1`.
  - Pushed core commit `59bf507a8fc03eb68053d1bf4de2f837224b3872` to
    `johnnykor82/mneme-universal-context-service`.
  - Pushed adapter commit `d3ffaed1419633e5e063857905666cb273fbe7f4` to
    `johnnykor82/mneme-codex-adapter`.
- Verification:
  - GitHub remote head check confirmed core `main` at `59bf507`.
  - GitHub remote head check confirmed adapter `main` at `d3ffaed`.
- Next gate:
  - Ask the second agent to reinstall using
    `adapters/codex/CODEX_DESKTOP_QUICKSTART.md` from
    `johnnykor82/mneme-codex-adapter` and report any remaining blockers.

### Codex-Agent Install Instruction File

- **Status:** complete
- Actions taken:
  - Added a public `CODEX_AGENT_INSTALL.md` to the Codex adapter publication
    path so users can tell their Codex agent to read one file before installing.
  - Linked it from the adapter README and quickstart.
  - Kept the feedback path generic; no internal shared-folder paths are
    published.
- Verification:
  - Adapter export scans for conflict markers, trailing whitespace, internal
    machine paths, shared-folder paths, and token literals: no matches.
  - Adapter export focused setup tests: `2 passed`.

### Codex Global Install Feedback Polish

- **Status:** complete and published
- Feedback addressed:
  - Sample ingest no longer requires manual env sourcing in the global flow;
    REST-writing commands accept `--install-root` and resolve the local token
    from `.local/mneme.env`.
  - Added `mneme-codex service install/start/stop/status/logs/uninstall` for
    macOS user LaunchAgent management; docs now prefer the service route and
    keep foreground daemon launch as troubleshooting fallback.
  - Removed public references to an unpublished `mneme-memory` skill from the
    Codex adapter repo docs/snippet.
  - Clarified that the install is a user-global Mneme daemon plus Codex MCP
    config, not a Codex Desktop marketplace plugin.
  - `doctor/status` now report ambient PATH commands separately from
    install-root `.venv/bin` entrypoints, plus service status and provider
    capability booleans.
  - Setup writes `$MNEME_CODEX_HOME/mneme.toml`; docs now show where to put
    non-secret provider settings, where to put API keys, how to restart the
    service, and how to verify embeddings/reranker/LLM enrichment capability.
- Public adapter:
  - Version bumped to `mneme-codex-adapter==0.1.2`.
  - Published commit:
    `47a212722e8449af9de918f86ccec04ece422759` on
    `johnnykor82/mneme-codex-adapter`.
- Internal sync:
  - Mirrored setup/service/doc behavior into local `mneme_service` Codex setup
    helpers and adapter docs so future exports do not regress.
- Verification:
  - Public adapter export:
    `31 passed`; compileall passed; setup/service CLI dry-runs passed;
    conflict marker, trailing whitespace, private-path/secret scans passed.
  - Internal focused check:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`
    passed with `11 passed`.
  - Internal full pytest:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
    passed with `136 passed, 1 warning`.
  - Internal parity acceptance:
    `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q`
    passed with `5 passed, 1 warning`.
  - Internal compileall:
    `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
    passed.
  - Internal conflict marker and trailing whitespace scans over changed
    Mneme/Codex/planning files: no matches.

### Required Mneme Memory Skill Install Polish

- **Status:** complete and published
- New feedback read from
  `/Users/openclaw/CodexShared/mneme-codex-global-install-feedback-20260615.md`:
  the second agent had installed `mneme-memory` manually into shared Codex
  skills, but public `CODEX_AGENT_INSTALL.md` did not say whether that skill
  was required, global, shared, or optional.
- Actions taken:
  - Added `mneme_codex_adapter/skills/mneme-memory/SKILL.md` as package data so
    pip-installed users do not need a source checkout to install the skill.
  - Added `mneme-codex skill install --target-dir "$HOME/.codex/skills"`.
  - Updated README, `CODEX_AGENT_INSTALL.md`, quickstart, and AGENTS snippet to
    make `mneme-memory` required for the expected Codex operating behavior.
  - Bumped public adapter version to `0.1.3`.
- Public adapter:
  - Published commit:
    `2a7628631198d0938d52e05fb69a916ad604bcf4` on
    `johnnykor82/mneme-codex-adapter`.
- Verification:
  - Public adapter export:
    `33 passed`; compileall passed; `mneme-codex skill install --dry-run`
    passed; conflict marker, trailing whitespace, and private-path/secret
    scans passed.

### Local Global Codex Mneme Enablement

- **Status:** complete on this machine
- Actions taken:
  - Installed public `mneme-codex-adapter==0.1.3` from GitHub into
    `/Users/openclaw/.mneme-codex/.venv` using Python 3.12 after the system
    Python 3.9 venv proved too old.
  - Ran `mneme-codex setup codex-desktop --global` for
    `/Users/openclaw/.mneme-codex`.
  - Confirmed the shared `mneme-memory` skill is installed through
    `/Users/openclaw/.codex/skills -> /Users/openclaw/CodexShared/skills`.
  - Copied existing dogfood embedding/reranker provider settings into the
    global Mneme env and added local LiteLLM `default` for LLM enrichment.
  - Installed and started macOS LaunchAgent `com.mneme.codex`.
  - Replaced the old project-local Mneme MCP block in
    `/Users/openclaw/.codex/config.toml` with global
    `/Users/openclaw/.mneme-codex/bin/mneme-mcp`; backup:
    `/Users/openclaw/.codex/config.toml.bak-mneme-global-20260615-224508`.
  - Created global `/Users/openclaw/.codex/hooks.json` using
    `/Users/openclaw/.mneme-codex/bin/mneme-codex-hook`, with capture, write,
    and context-preview hooks and no token literal in hooks config.
- Verification:
  - `curl http://127.0.0.1:8765/v1/health`: OK.
  - `mneme-codex service status`: `running: true`.
  - `mneme-codex doctor`: `readiness: READY`,
    `supports_embeddings: true`, `supports_reranking: true`,
    `supports_llm_enrichment: true`, `requires_embeddings: true`.
  - Synthetic global hook smoke: capture OK, write accepted 1 event, context
    preview `changed: true`.
  - Sample transcript ingest: accepted 2 events.
  - Hook capture validation: `valid_for_enablement: true`.
- Note:
  - Existing Codex sessions do not reload MCP/hook config. A fresh Codex
    session or Codex restart is needed, and Codex may ask once to trust the new
    global hooks.

## Session: 2026-06-15

### Phase 14C: Full Hermes-Mneme Parity Completion Implementation

- **Status:** complete
- Actions taken:
  - Executed the Phase 14C plan continuously per the recorded rule.
  - Added original-core config knobs for budget, segmentation, retrieval,
    enrichment, embedding-index, and memory/checkpoint behavior.
  - Completed global/multi-session search, configurable embedding compression,
    centroid window behavior, and model-change reindex.
  - Added entity contradiction and question-about-output intent signals,
    router modes/weights, reranker score-list parsing, and reranker top-k cap.
  - Expanded execution state with segment/enrichment fields, decision rationale,
    state-history recovery, topic tags, decision summary, and robust enrichment
    JSON recovery/scheduling.
  - Upgraded `/v1/context/prepare` with memory access hint, goal trail,
    checkpoint hint, execution-state compression, global candidates,
    adapter-ready metadata, and safer helper-block collision handling.
  - Upgraded REST/MCP memory tools with global scope, fetch segment/token
    metadata, `expand_context(mode="segment")`, and richer `list_segments`
    table-of-contents data.
  - Refreshed comparison, provider, install, testing, vector, publication, and
    planning docs for Phase 14C completion and future GitHub users.
  - Confirmed local dogfood daemon capabilities show required embeddings and
    reranker enabled; previous smoke session still reports `embedding_items: 3`,
    `embedding_failures: 0`, `reranker_calls: 4`, `reranker_failures: 0`.
    The local dogfood daemon has no LLM provider enabled, so real LLM smoke is
    a release-claim gate only when configured.
- Files modified include:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `mneme_service/config.py`
  - `mneme_service/embeddings.py`
  - `mneme_service/classifier.py`
  - `mneme_service/enrichment.py`
  - `mneme_service/reranker.py`
  - `mneme_service/state.py`
  - `tests/test_context_prepare.py`
  - `tests/test_context_assembly.py`
  - `tests/test_contract.py`
  - `tests/test_embeddings.py`
  - `tests/test_parity_recovery.py`
  - docs/planning files updated for Phase 14C completion.
- Verification notes:
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q`: passed.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py -q`: `11 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py -q`: `6 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py -q`: `22 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q`: `5 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `133 passed`.

### LLM Provider Smoke Before Publication

- **Status:** passed
- Evidence:
  - `GET http://127.0.0.1:4000/v1/models` succeeded and listed `default`.
  - A later `POST /v1/chat/completions` with model `default` returned
    `MNEME_LLM_OK`; the route can be slow but is reachable.
  - The first Mneme TestClient smoke failed inside sandbox because Python/httpx
    local network access returned `Operation not permitted`.
  - Re-running the same Mneme LLM enrichment smoke with approved unsandboxed
    execution succeeded for session `llm-smoke-1781507835`:
    `accepted: 1`, `enrichment_calls: 1`, `enrichment_failures: 0`,
    `intent_label: DECISION`, topic tags populated, `decision_summary`
    populated, and enrichment decisions include decision plus rationale.
- Decision:
  - LLM structured enrichment gate is now closed. Continue to GitHub
    publication and second-machine install rehearsal.

### GitHub Publication

- **Status:** first mixed publication quarantined private; clean split pending
- Actions taken:
  - Sanitized tracked dogfood docs/progress so local bearer-token literals are
    replaced with placeholders.
  - Initialized a local git repository on branch `main`.
  - Verified ignored local/private paths stay out of git: `.local/`, `.venv/`,
    `.codex/hooks.json`, bytecode caches, pytest cache, and egg-info.
  - Created initial commit `3abe756 Initial Mneme universal context service`.
  - Confirmed GitHub CLI authentication works outside sandbox with account
    `johnnykor82`, SSH git protocol, and `repo` scope.
  - Created public GitHub repository:
    `https://github.com/johnnykor82/mneme-universal-context-service`.
  - Added `origin` as
    `git@github.com:johnnykor82/mneme-universal-context-service.git`.
  - Pushed `main` and set it to track `origin/main`.
  - Verified GitHub initially reported visibility `PUBLIC` and default branch
    `main`.
  - After user review, recognized this was the wrong publication shape because
    it combined the engine, Codex adapter, and internal planning/dogfood
    materials in one public repository.
  - Changed the repository visibility to `PRIVATE`; follow-up verification
    reported `visibility: PRIVATE`.
- Next gate:
  - Prepare clean split publication:
    `johnnykor82/mneme-universal-context-service` for Mneme engine/core,
    `johnnykor82/mneme-codex-adapter` for the Codex adapter, and no internal
    planning/dogfood artifacts in the public install surface.
  - Only then install from GitHub on the user's second Codex machine as a
    new-user flow and record any missing setup steps.

### Publication Split Correction

- **Status:** core published; Codex adapter pending
- Actions taken:
  - Accepted the user's correction that internal planning/rehearsal material
    should not be added to the public GitHub repository.
  - Accepted the product-boundary correction that Mneme engine/core and host
    adapters should be published separately.
  - Verified the existing mixed GitHub repository
    `johnnykor82/mneme-universal-context-service` is now `PRIVATE`.
  - Updated local planning files only; no new internal planning changes were
    pushed to GitHub.
  - Updated the publication-gate test so docs must mention the corrected
    `engine/core` plus separate Codex adapter split and the private quarantine.
  - Recorded the chosen GitHub names: `johnnykor82/mneme-universal-context-service`
    for core and `johnnykor82/mneme-codex-adapter` for Codex.
- Verification:
  - `gh repo view johnnykor82/mneme-universal-context-service --json nameWithOwner,url,visibility,defaultBranchRef` reported `visibility: PRIVATE`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q`: `8 passed`; includes assertions for the chosen core and Codex adapter repository names.
  - Stale combined-publication wording scan over docs/planning/tests: no
    matches.
  - Conflict-marker scan on changed docs/planning/test files: no matches.
  - Trailing-whitespace scan on changed docs/planning/test files: no matches.
- Next gate:
  - Prepare a clean core export for `johnnykor82/mneme-universal-context-service`
    and a separate Codex adapter package/repository at
    `johnnykor82/mneme-codex-adapter`.

### Clean Core GitHub Publication

- **Status:** complete
- Actions taken:
  - Built a sanitized core export at `/private/tmp/mneme-core-public-1781518935`.
  - Excluded host adapter/internal material from the export: `adapters/codex`,
    `.agents`, `.local`, `task_plan.md`, `findings.md`, `progress.md`,
    milestone plans, publication checklist, Codex hook/import modules, and
    Codex-specific tests.
  - Sanitized export-only core files so `mneme_service.cli` contains only
    `serve`, `mcp`, and `benchmark`, MCP server instructions are runtime-neutral,
    and user-facing install/README docs describe adapters as separate packages.
  - Created export root commit `01f969d Initial Mneme core engine`.
  - Attempted to delete the old mixed GitHub repository, but GitHub rejected the
    API call because the token lacks `delete_repo` scope.
  - Renamed the old private mixed repository to
    `johnnykor82/mneme-universal-context-service-internal-quarantine`.
  - Created a new public repository at
    `https://github.com/johnnykor82/mneme-universal-context-service` and pushed
    the clean core root commit to `main`.
  - Updated this local internal checkout's `origin` to the private quarantine
    remote to avoid accidentally pushing mixed internal files to the public core
    repository.
- Verification:
  - Export full pytest:
    `env TMPDIR=/private/tmp /Users/openclaw/.hermes/plugins/_mneme-universal-context-service/.venv/bin/python -m pytest -q`: `97 passed, 1 warning`.
  - Export parity:
    `env TMPDIR=/private/tmp /Users/openclaw/.hermes/plugins/_mneme-universal-context-service/.venv/bin/python -m pytest tests/test_parity_recovery.py -q`: `5 passed, 1 warning`.
  - Export compileall:
    `env TMPDIR=/private/tmp /Users/openclaw/.hermes/plugins/_mneme-universal-context-service/.venv/bin/python -m compileall -q mneme_service tests`: passed.
  - Export scans for Codex hook/import paths, internal planning filenames,
    quarantine adapter repo name, conflict markers, and trailing whitespace:
    no matches.
  - GitHub public core verification:
    `gh repo view johnnykor82/mneme-universal-context-service --json nameWithOwner,url,visibility,defaultBranchRef`
    reported `visibility: PUBLIC`, default branch `main`.
  - GitHub quarantine verification:
    `gh repo view johnnykor82/mneme-universal-context-service-internal-quarantine --json nameWithOwner,url,visibility,defaultBranchRef`
    reported `visibility: PRIVATE`.
  - `git ls-remote --heads origin` in the export reported
    `01f969d1011a715f20d7dbb4f8779b18072945ef refs/heads/main`.
- Next gate:
  - Prepare separate `johnnykor82/mneme-codex-adapter`, then run the
    second-machine new-user install rehearsal using the public core plus adapter.

### Clean Codex Adapter GitHub Publication

- **Status:** complete
- Actions taken:
  - Built sanitized adapter export at `/private/tmp/mneme-codex-adapter-1781520871`.
  - Published public repo:
    `https://github.com/johnnykor82/mneme-codex-adapter`.
  - Adapter root commit:
    `d0415287b9643422cef4063e5bc2b3ba73e72a5b`.
  - Adapter package uses `mneme-codex` CLI and depends on public core
    `mneme-context-service @ git+https://github.com/johnnykor82/mneme-universal-context-service.git`.
- Verification:
  - Adapter tests with public core export on `PYTHONPATH`: `28 passed`.
  - Adapter compileall: passed.
  - Scans for internal paths, old `mneme codex-*` commands, `mneme_service.cli`
    adapter commands, planning filenames, dogfood markers, conflict markers,
    and trailing whitespace: no matches.
  - GitHub reported `visibility: PUBLIC`, default branch `main`.
  - Remote main points to `d0415287b9643422cef4063e5bc2b3ba73e72a5b`.
- Next gate:
  - Second-machine install rehearsal as a new user from the two public GitHub
    repositories.

## Session: 2026-06-14

### Phase 14C: Full Hermes-Mneme Parity Completion Planning

- **Status:** in progress
- Actions taken:
  - Per user request, converted the second parity audit into a compact
    milestone plan.
  - Added `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`.
  - Updated `task_plan.md` so Phase 14C blocks publication/second-machine
    rehearsal until original-core gaps are closed.
  - Updated `findings.md` with the remaining runtime-neutral parity gaps.
  - Verified changed planning files have no conflict markers or trailing
    whitespace.
  - On 2026-06-15, recorded the execution rule: continue through the full
    Phase 14C plan without stopping after each task; stop only for a real
    blocker or a question not answerable from original `hermes-mneme`.
- Files modified:
  - `MILESTONE_6_FULL_HERMES_MNEME_PARITY_COMPLETION_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 13 Task 2: Codex Adapter Foundation Planning

- **Status:** complete
- Actions taken:
  - Re-read `task_plan.md`, `findings.md`, `progress.md`, and `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`.
  - Confirmed Phase 13 is no longer blocked by Phase 14/14B because semantic retrieval, execution state, lineage, provider-safe behavior, and budgeted prepare are now implemented in the daemon/core.
  - Checked current official Codex capability facts: MCP server instructions, repo-local skills, AGENTS.md, and command hooks are available surfaces; automatic prompt replacement through MCP alone is still not a valid claim.
  - Updated the Phase 13 plan: Task 2 is now the Codex adapter foundation; Task 3 is hook-backed ingestion; MCP remains read-only for this slice.
  - Added a publication/installability constraint: future GitHub users should get clear automated setup paths, and reusable adapter docs/examples should not depend on private local paths.
- Files modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`

### Phase 13 Task 2: Codex Adapter Foundation Implementation

- **Status:** complete
- Actions taken:
  - Added `MNEME_MCP_INSTRUCTIONS` to the MCP server and passed it through `FastMCP(..., instructions=...)`.
  - Created repo-local `.agents/skills/mneme-memory/SKILL.md` for long sessions, compaction recovery, resume behavior, and evidence-based Mneme MCP usage.
  - Added `adapters/codex/AGENTS_MNEME_SNIPPET.md` as copyable always-loaded Codex guidance without modifying live user config.
  - Added disabled `adapters/codex/codex_hooks.contract.example.json` to document the planned hook events while requiring real payload validation before writes.
  - Updated publication/install docs so future GitHub users remain a design constraint and setup should be clear and automatable.
  - Added `tests/test_codex_adapter.py` covering MCP instructions, skill, AGENTS snippet, hook contract, read-only MCP posture, and no positive automatic-prompt-replacement claims.
- Files modified:
  - `mneme_service/mcp_server.py`
  - `tests/test_codex_adapter.py`
  - `.agents/skills/mneme-memory/SKILL.md`
  - `adapters/codex/AGENTS_MNEME_SNIPPET.md`
  - `adapters/codex/codex_hooks.contract.example.json`
  - `README.md`
  - `docs/INSTALLATION.md`
  - `docs/PUBLICATION_CHECKLIST.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`

### Phase 13 Task 3: Codex Hook Ingestion MVP

- **Status:** MVP complete; local real-session payload validation complete; enable-ready write smoke pending
- Actions taken:
  - Added `mneme_service/codex_hooks.py` to normalize explicit Codex hook JSON/stdin into `mneme.session.v0` and `mneme.event_batch.v0`.
  - Added stable hook event ids for replay-safe delivery.
  - Added `mneme codex-hook-ingest` with `--dry-run`, `--input`, `--event`, `--base-url`, `--token`, and `--timeout`.
  - Kept writes on the REST ingestion lane and kept MCP read-only.
  - Added `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md` with dry-run-first instructions, trust boundary, and future GitHub user installability notes.
  - Linked hook usage from `README.md`.
  - Added `tests/test_codex_hooks.py` covering normalization, idempotent REST import, service-side redaction, CLI parsing/dry-run, and docs.
  - Changed benchmark import in `mneme_service/cli.py` to lazy import so ordinary `mneme codex-hook-ingest --help` does not emit the benchmark/TestClient warning.
- Files modified:
  - `mneme_service/codex_hooks.py`
  - `mneme_service/cli.py`
  - `tests/test_codex_hooks.py`
  - `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md`
  - `README.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`

### Phase 13 Task 3A: Codex Hook Capture and Validation Harness

- **Status:** complete; local real Codex Desktop capture validated
- Actions taken:
  - Added `validate_codex_hook_payload()` and `validate_codex_hook_capture_file()` to report payload readiness without raw content.
  - Added `capture_codex_hook_payload()` and CLI command `mneme codex-hook-capture` for local JSONL capture.
  - Added CLI command `mneme codex-hook-validate` for validating captured JSONL/list/object payloads.
  - Added capture-only example `adapters/codex/codex_hooks.capture.example.json` that writes to `.local/mneme-codex-hooks.jsonl` and performs no Mneme REST writes.
  - Updated `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md` with capture-first and validate commands for future GitHub users.
  - Did not modify live Codex config, live Hermes, or live `hermes-mneme`.
- Files modified:
  - `mneme_service/codex_hooks.py`
  - `mneme_service/cli.py`
  - `tests/test_codex_hooks.py`
  - `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md`
  - `adapters/codex/codex_hooks.capture.example.json`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`

### Phase 13 Multi-Machine Codex Setup Constraint

- **Status:** documented
- Actions taken:
  - Recorded that the user runs two Codex installs on different machines with
    shared files via symlinks.
  - Documented that shared files can propagate Mneme instructions, skills, and
    examples, but not runtime state.
  - Updated install/Codex docs so `mneme serve`, `mneme mcp`, tokens, provider
    secrets, database paths, hook trust, and hook capture/validation are treated
    as per-machine setup.
- Files modified:
  - `docs/INSTALLATION.md`
  - `docs/PUBLICATION_CHECKLIST.md`
  - `adapters/codex/MNEME_CODEX_MCP_USAGE.md`
  - `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md`
  - `adapters/codex/AGENTS_MNEME_SNIPPET.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 13 GitHub Publication and Second-Machine Rehearsal Gate

- **Status:** documented; pending local hook validation
- Actions taken:
  - Recorded that GitHub publication should happen after local trusted Codex
    hook payload validation, not before.
  - Defined an earlier post-validation flow that would have published Mneme and
    `adapters/codex` together; this is now superseded by the corrected split
    publication model recorded in the current snapshot.
  - Made the rehearsal explicitly check per-machine runtime pieces that shared
    symlinks cannot provide: daemon, MCP config, token/env, database path,
    provider secrets if used, hook trust, hook capture/validation, and a
    REST-ingestion plus MCP-recall smoke path.
  - Checked repository state: `git rev-parse --show-toplevel` fails because the
    current project directory is not a git repository. Future publication will
    need a repo/remote setup step after local hook validation.
- Files modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`
  - `docs/PUBLICATION_CHECKLIST.md`
  - `tests/test_codex_adapter.py`
- Verification notes:
  - First focused run of `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_adapter.py -q` failed because the new test scanned the
    entire historical `progress.md` and matched an old recorded `rg` command
    containing a forbidden phrase as data.
  - Resolution: narrowed the no-overclaim assertion to the current publication
    checklist while keeping the GitHub/second-machine gate assertions across
    the planning files.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_adapter.py -q`: `6 passed`.
  - Conflict-marker scan on changed planning/publication/test files: no
    anchored markers.
  - Trailing-whitespace scan on changed planning/publication/test files: no
    matches.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `96 passed, 1
    warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service
    tests`: passed.
  - Post-planning focused check `env TMPDIR=/private/tmp .venv/bin/python -m
    pytest tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `21
    passed`.
  - Post-planning conflict-marker and trailing-whitespace scans on changed
    files: no matches.
  - Final post-planning `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    -q`: `100 passed, 1 warning`.

### Phase 13 Local Codex Hook Capture Config Renderer

- **Status:** complete; real Codex payload capture still pending
- Actions taken:
  - Added `mneme codex-hook-render-config` to render capture, dry-run, and
    write hook configs with an explicit Python runner.
  - Added `CODEX_HOOK_MATCHERS` as the shared local event list for rendered hook
    configs.
  - Updated hook docs to generate machine-local capture configs without
    relying on shell `PATH`.
  - Added `.codex/hooks.json` to `.gitignore`, because local hook configs can
    contain machine-specific absolute paths.
  - Generated `.local/codex_hooks.capture.local.json` and `.agents/hooks.json`
    capture-only configs for this machine.
  - Ran a synthetic capture/validate smoke path against
    `.local/mneme-codex-hooks.smoke.jsonl`; validation returned
    `valid_for_enablement: true` for the synthetic payload.
  - Read local Codex CLI help and binary strings. Initial evidence suggested
    `.agents/hooks.json`, but a later official Codex manual check corrected the
    active project hook location to `.codex/hooks.json`; no live Codex user
    config was modified.
  - Ran `codex doctor --summary --ascii` with `--cd` set to this project. It did
    not report a hook config parse error, but it did report unrelated Codex
    environment issues: state DB integrity failure, provider reachability and
    WebSocket failures, optional MCP config issues, and `TERM=dumb`.
- Files modified:
  - `.gitignore`
  - `mneme_service/codex_hooks.py`
  - `mneme_service/cli.py`
  - `tests/test_codex_hooks.py`
  - `adapters/codex/MNEME_CODEX_HOOKS_USAGE.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`
- Local generated files:
  - `.local/codex_hooks.capture.local.json`
  - `.agents/hooks.json`
  - `.local/mneme-codex-hooks.smoke.jsonl`
- Verification notes:
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `21 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `100 passed, 1
    warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service
    tests`: passed.

### Phase 13 Real Hook Capture Attempt 1

- **Status:** failed; root cause found
- Evidence:
  - User opened a new Codex Desktop session in
    `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service` and ran
    the requested `pwd` smoke prompt.
  - `mneme codex-hook-validate --input .local/mneme-codex-hooks.jsonl` failed
    with `FileNotFoundError`; no real capture file was created.
  - Fresh rollout metadata confirmed the Codex session `cwd` was the intended
    project path and the `pwd` tool ran there.
  - Searching the project found only the synthetic
    `.local/mneme-codex-hooks.smoke.jsonl`; no real
    `.local/mneme-codex-hooks.jsonl` existed.
  - Official Codex manual confirms active project hooks load from
    `.codex/hooks.json` or inline `.codex/config.toml`, not
    `.agents/hooks.json`.
- Root cause:
  - The local capture config was generated at `.agents/hooks.json`, so Codex did
    not load it as an active project hook config.
- Corrective action:
  - Updated docs/tests/planning to use `.codex/hooks.json`.
  - Regenerate capture-only `.codex/hooks.json` for the next real hook capture
    attempt.
  - Removed the obsolete generated `.agents/hooks.json`.
  - Regenerated `.codex/hooks.json` and `.local/codex_hooks.capture.local.json`
    with only the official top-level `hooks` shape.
  - Changed `mneme codex-hook-validate` so a missing capture file returns a
    structured `CAPTURE_FILE_MISSING` report instead of a traceback.
- Verification notes:
  - `env TMPDIR=/private/tmp .venv/bin/python -m mneme_service.cli
    codex-hook-validate --input .local/mneme-codex-hooks.jsonl` now returns
    `payload_count: 0`, `valid_for_enablement: false`, and
    `warnings: ["CAPTURE_FILE_MISSING"]`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `22 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `101 passed, 1
    warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service
    tests`: passed.
  - `codex doctor --summary --ascii` still reports unrelated Codex environment
    issues, but config loading is OK and no hook config parse error was shown.

### Phase 13 Real Hook Capture Attempt 2

- **Status:** passed; local real Codex Desktop payload validation complete
- Evidence:
  - User restarted Codex Desktop, opened a new session in
    `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`, and
    approved the project hooks through the Codex UI trust prompt.
  - The trusted capture-only `.codex/hooks.json` wrote
    `.local/mneme-codex-hooks.jsonl`.
  - The captured real events were `SessionStart`, `UserPromptSubmit`,
    `PostToolUse`, and `Stop`.
  - Real Codex Desktop payloads use `hook_event_name` for event type. They do
    not include `timestamp`, `summary`, or `message`; content-bearing fields
    observed were `prompt`, `tool_name`, `tool_input`, `tool_response`,
    `tool_use_id`, `last_assistant_message`, `source`, `cwd`, and `model`.
  - The capture JSONL wrapper includes `captured_at`, which is now the
    canonical fallback timestamp for captured hook validation.
- Actions taken:
  - Updated `normalize_codex_hook_payload()` and
    `validate_codex_hook_payload()` to understand real Codex Desktop hook
    fields while keeping validation reports free of raw captured content.
  - Added focused tests for real Codex Desktop payload shapes and stable event
    ids independent of timestamp.
  - Updated direct `codex-hook-ingest` dry-run/write handling to attach a local
    receipt timestamp when Codex stdin does not include one.
- Verification notes:
  - First focused TDD run of `env TMPDIR=/private/tmp .venv/bin/python -m
    pytest
    tests/test_codex_hooks.py::test_codex_hook_capture_validation_accepts_real_codex_desktop_payload_shapes
    -q` failed with `valid_for_enablement` false, confirming the prior
    validator did not understand the real payload shape.
  - After the normalization fix, `env TMPDIR=/private/tmp .venv/bin/python -m
    pytest
    tests/test_codex_hooks.py::test_codex_hook_normalizes_real_codex_desktop_fields
    tests/test_codex_hooks.py::test_codex_hook_capture_validation_accepts_real_codex_desktop_payload_shapes
    -q`: `2 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `24 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `103 passed,
    1 warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_parity_recovery.py -q`: `5 passed, 1 warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service
    tests`: passed.
  - Conflict-marker and trailing-whitespace scans on source, tests, adapter
    docs, and planning files: no matches.

### Phase 13 Active Codex Preview Hook Setup

- **Status:** ready for new-session Codex trust/rehearsal
- Actions taken:
  - Updated local gitignored `.codex/hooks.json` from capture-only to
    capture + REST ingest + context preview.
  - Hook writes target the existing dogfood daemon on `http://127.0.0.1:8767`
    with local token `<mneme-auth-token>`.
  - `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PostCompact`, and
    `Stop` now keep capture JSONL and also write normalized events to Mneme
    REST.
  - `UserPromptSubmit` also calls `mneme codex-hook-prepare-preview` and writes
    `.local/mneme-codex-context-preview.jsonl`.
  - Regenerated `.local/codex_hooks.context_preview.local.json` with
    `http://127.0.0.1:8767` for review/reference.
- Verification notes:
  - `env TMPDIR=/private/tmp .venv/bin/python -m json.tool
    .codex/hooks.json`: valid JSON.
  - `curl -sS http://127.0.0.1:8767/v1/health`: `status: OK`,
    `service: mneme-context-service`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `29 passed`.
  - Conflict-marker and trailing-whitespace scans on `.codex`, source, tests,
    adapter docs, and planning files: no matches.
- Next manual/user check:
  - Restart or open a new Codex Desktop session in this project.
  - Review/trust the changed project hooks when Codex prompts.
  - Send a small test prompt and verify `.local/mneme-codex-context-preview.jsonl`
    gets a new preview record.

### Phase 13 Real Preview Hook Rehearsal and MCP Recall

- **Status:** passed
- Evidence:
  - User opened/restarted Codex Desktop, trusted the changed project hooks, sent
    a small prompt, and observed
    `.local/mneme-codex-context-preview.jsonl` was created.
  - Preview file summary: 1 record,
    `schema_version: mneme.codex_context_preview.v0`, `event_name:
    UserPromptSubmit`, `dry_run: false`, `changed: true`, `warnings: []`, 2
    prepared messages, 1 Mneme-generated message, 1 selected event, and a trace
    id.
  - Preview marker remains `not_supported_by_current_command_hooks`, preserving
    the no automatic prompt-insertion claim.
  - `mneme codex-hook-validate --input .local/mneme-codex-hooks.jsonl` now sees
    12 captured payloads across real sessions; all reports are
    `valid_for_enablement: true` with no warnings.
  - `mcp__mneme.context_search` for session
    `019ec7a1-6fbc-74f3-93fc-367c447fc6f9` and query
    `Тест Mneme preview hook pwd` returned hook-derived `UserPromptSubmit`,
    `PostToolUse`, `Stop`, and `SessionStart` events from Mneme memory.
- Conclusion:
  - The local loop now works end-to-end: Codex hooks capture and ingest events,
    Mneme prepares a context preview file on `UserPromptSubmit`, and Codex can
    retrieve the same hook-derived memory through MCP.
- Verification notes:
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `29 passed`.
  - Conflict-marker and trailing-whitespace scans on planning, Codex tests, and
    adapter docs: no matches.
  - `.venv/bin/python -m mneme_service.cli codex-hook-validate --input
    .local/mneme-codex-hooks.jsonl`: `payload_count: 12`,
    `valid_for_enablement: true`, and no warnings.

### Phase 13 Dogfood Provider Enablement and Required Embeddings

- **Status:** passed for embeddings/reranker; LLM enrichment still not enabled
  in dogfood.
- User clarification:
  - Embeddings should be required for real Mneme memory, not treated as merely
    optional, because semantic search and topic-centroid drift detection depend
    on vectors.
- Actions taken:
  - Added `Settings.require_embeddings`, `MNEME_REQUIRE_EMBEDDINGS`,
    `--require-embeddings`, and `--allow-missing-embeddings`.
  - Added fail-fast daemon startup behavior when required embeddings are not
    enabled/configured.
  - Added `requires_embeddings` to `/v1/capabilities`.
  - Mapped live Hermes provider settings from `/Users/openclaw/.hermes/.env`
    into gitignored `.local/mneme-dogfood.env` without printing secrets.
  - Updated `.local/com.openclaw.mneme-dogfood.plist` to run through
    `.local/run-mneme-dogfood.sh`, which starts Mneme with
    `--require-embeddings`.
  - Reloaded `com.openclaw.mneme-dogfood` through launchd so the wrapper is the
    active program.
  - Updated provider/publication docs so minimal provider-free mode is only
    CI/dev/fallback, while dogfood/public-readiness semantic memory requires
    working embeddings.
- Verification notes:
  - RED: `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_config.py::test_required_embeddings_fail_fast_when_provider_is_unavailable
    tests/test_config.py::test_required_embeddings_setting_comes_from_config_env_and_cli
    -q` failed because `Settings` had no `require_embeddings`.
  - GREEN: same focused tests plus capabilities check: `3 passed, 1 warning`.
  - `plutil -lint .local/com.openclaw.mneme-dogfood.plist`: OK.
  - `launchctl print gui/$(id -u)/com.openclaw.mneme-dogfood` shows active
    program `.local/run-mneme-dogfood.sh`.
  - `GET /v1/capabilities` reports `supports_embeddings: true`,
    `requires_embeddings: true`, `supports_reranking: true`,
    `supports_llm_enrichment: false`.
  - Real provider smoke session `provider-smoke-1781467731`: 3 events accepted,
    3 rows in `embedding_index`, `embedding_batches: 1`,
    `embedding_items: 3`, `embedding_failures: 0`, `reranker_calls: 1`,
    `reranker_failures: 0`.
  - `context_search` for the smoke session returned all three smoke event ids
    through `data.results` with no warnings.
- Errors encountered:
  - Initial `launchctl bootstrap` failed until the job was booted out by full
    service target and reloaded with an absolute plist path.
  - Python localhost smoke needed escalated execution because sandboxed Python
    could not connect to `127.0.0.1`.
  - Initial smoke events missed required REST fields `agent_id`, `runtime`, and
    `role`; fixed the smoke payload, not the service contract.

### Phase 13 Context Preview Smoke

- **Status:** passed; automatic prompt insertion still unsupported by current
  documented Codex command hooks
- Evidence:
  - Official Codex manual lists command hook events including
    `UserPromptSubmit`, `PreCompact`, and `PostCompact`, but no documented
    context-build/pre-model prompt replacement hook.
  - The same manual says only `type: "command"` handlers run today; `prompt`
    and `agent` hook handlers are parsed but skipped.
- Actions taken:
  - Added `mneme codex-hook-import-capture` to replay captured hook JSONL into
    Mneme REST ingestion.
  - Added `mneme codex-hook-prepare-preview` to call `/v1/context/prepare` from
    a Codex hook payload and append the prepared result to a local JSONL file.
  - Added `mneme codex-hook-render-context-preview-config` to render a
    `UserPromptSubmit` hook that writes context previews to
    `.local/mneme-codex-context-preview.jsonl`.
  - Generated `.local/codex_hooks.context_preview.local.json` for review
    without modifying active `.codex/hooks.json`.
  - Started a temporary Mneme daemon on `127.0.0.1:8766` with
    `.local/mneme-preview-smoke.db`, imported the real captured 4 hook events,
    and wrote `.local/mneme-codex-context-preview.smoke.jsonl`.
- Verification notes:
  - `mneme codex-hook-import-capture --input .local/mneme-codex-hooks.jsonl
    --base-url http://127.0.0.1:8766 --token smoke-token`: `accepted: 4`,
    `duplicates: 0`.
  - `mneme codex-hook-prepare-preview --input .local/mneme-codex-hooks.jsonl
    --event UserPromptSubmit --output
    .local/mneme-codex-context-preview.smoke.jsonl --base-url
    http://127.0.0.1:8766 --token smoke-token`: `changed: true`,
    `warnings: []`, generated one Mneme evidence message plus the original user
    message, and included a trace id.
  - The preview record explicitly marks prompt injection as
    `not_supported_by_current_command_hooks`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_codex_hooks.py tests/test_codex_adapter.py -q`: `29 passed`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`: `108 passed,
    1 warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m pytest
    tests/test_parity_recovery.py -q`: `5 passed, 1 warning`.
  - `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service
    tests`: passed.
  - Conflict-marker and trailing-whitespace scans on source, tests, adapter
    docs, and planning files: no matches.

## Session: 2026-06-08

### Phase 1: Concept Document

- **Status:** complete
- Actions taken:
  - Started strategic planning for a universal version of the Mneme context engine.
  - Created isolated folder at `/Users/openclaw/.hermes/plugins/_mneme-universal-context-service`.
  - Created concept brief: `MNEME_UNIVERSAL_CONTEXT_SERVICE_CONCEPT.md`.
- Files created/modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MNEME_UNIVERSAL_CONTEXT_SERVICE_CONCEPT.md`

### Phase 2: Presentation Diagram

- **Status:** complete
- Actions taken:
  - Created polished architecture diagram showing ingestion, storage, retrieval, context assembly, and agent integration.
- Files created/modified:
  - `mneme_universal_context_service_architecture.html`

### Phase 3: Follow-Up Design Session

- **Status:** complete
- Actions taken:
  - Forked a same-directory Codex thread for follow-up strategy discussion: `019ea68c-70ab-7100-ba3d-408ad580e61e`.
  - Continued strategic planning in the delegated session.
  - Re-read the concept brief, plan, findings, and progress files.
- Files created/modified:
  - `progress.md`

### Phase 4: Implementation Paths and MVP

- **Status:** complete
- Actions taken:
  - Created implementation strategy document: `IMPLEMENTATION_PATHS_AND_MVP.md`.
  - Recommended first product path: local daemon with REST API plus MCP server, Hermes as first deep adapter, Codex/MCP as first broad adapter.
- Files created/modified:
  - `IMPLEMENTATION_PATHS_AND_MVP.md`
  - `progress.md`

### Phase 5: API/MCP Contract v0

- **Status:** complete
- Actions taken:
  - Re-read all source-of-truth documents, including concept brief, implementation path, planning files, findings, progress, and architecture HTML.
  - Used two read-only subagents to review API/MCP schema coverage and security/adapter contract risks.
  - Created draft contract: `API_MCP_CONTRACT_V0.md`.
  - Updated the contract with subagent review findings: `snake_case` schemas, auth defaults, idempotency, request-only prepare semantics, trace/cost details, privacy requirements, and adapter conformance tests.
  - Did not start service, adapter, daemon, SDK, or MCP implementation.
- Files created/modified:
  - `API_MCP_CONTRACT_V0.md`
  - `findings.md`
  - `progress.md`

### Phase 6: Contract Review and Approval Gate

- **Status:** complete
- Actions taken:
  - Received an additional external review of `API_MCP_CONTRACT_V0.md`.
  - Independently reviewed the contract and confirmed most external findings were valid.
  - Revised `API_MCP_CONTRACT_V0.md` to resolve protocol ambiguities around oversized payloads, `409 CONFLICT`, `mneme.message.v0`, context prepare validation, REST/MCP parity, memory-read audit, redaction, streaming chunks, graph truncation, schema negotiation, session auto-create behavior, and conformance tests.
  - Created reviewer response: `API_MCP_CONTRACT_V0_REVIEW_RESPONSE.md`.
  - Left implementation blocked until second external review.
- Files created/modified:
  - `API_MCP_CONTRACT_V0.md`
  - `API_MCP_CONTRACT_V0_REVIEW_RESPONSE.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

## Session: 2026-06-09

### Phase 6: Contract Approval Completion

- **Status:** complete
- Actions taken:
  - Received second external review accepting `API_MCP_CONTRACT_V0.md` as a basis for implementation.
  - Confirmed remaining reviewer notes are non-blocking recommendations.
  - Added two small spec clarifications:
    - adapters expecting large outputs should use `BYTES_REF` immediately;
    - `page_token` is server-issued, opaque, and must not be parsed or generated by adapters.
  - Marked the spec review and approval gate complete in `task_plan.md`.
  - Added pending implementation-planning phase.
  - Did not start service, adapter, daemon, SDK, or MCP implementation during the approval step.
- Files created/modified:
  - `API_MCP_CONTRACT_V0.md`
  - `task_plan.md`
  - `progress.md`

### Phase 8: Milestone 1 Local Daemon MVP

- **Status:** complete
- Actions taken:
  - Implemented Milestone 1 local daemon MVP inside `_mneme-universal-context-service`.
  - Added Python service scaffold with FastAPI, Pydantic v2, Uvicorn, pytest, and httpx in `pyproject.toml`.
  - Added `mneme_service` modules for configuration, auth, redaction, standard errors, SQLite storage, retrieval/context assembly, REST app, and CLI.
  - Implemented REST contract v0 endpoints for health, capabilities, session start, event ingest, turn complete, context prepare, REST memory tools, traces, cost report, export, and delete.
  - Implemented SQLite persistence for sessions, events, immutable event hashes, turns/segments, traces, audit records, and derived cleanup paths.
  - Implemented v0 safety behavior: bearer auth by default, loopback CLI default, unsupported schema rejection, unknown session rejection, oversized inline payload rejection, `BYTES_REF` metadata acceptance, duplicate/conflict handling, recursive irreversible redaction before storage/search/traces, and request-only context preparation.
  - Implemented lexical/recency retrieval shared by search, recent recall, context expansion, and context preparation.
  - Added contract/integration tests covering session idempotency, event ingest duplicate/conflict/rejection paths, redaction, memory-read audit, tool envelope errors, context prepare validation/tracing, cost/export/delete, synthetic multi-session retrieval, and SQLite restart idempotency.
  - Removed the app-import side effect that created `mneme.db` in the project root; daemon is started through `mneme_service.cli` with an explicit DB path.
  - Added `.gitignore` entries for local virtualenv, pytest cache, SQLite DBs, bytecode, and egg-info artifacts.
  - Added a regression check for `context_prepare` trace redaction and changed prepare/search paths to redact request-derived query/policy data before search and trace persistence.
  - Did not touch live Hermes or live `hermes-mneme`.
  - Did not implement MCP server, Hermes adapter, Codex/MCP adapter, benchmarks, embeddings, reranking, or LLM enrichment.
- Files created/modified:
  - `.gitignore`
  - `pyproject.toml`
  - `mneme_service/__init__.py`
  - `mneme_service/app.py`
  - `mneme_service/cli.py`
  - `mneme_service/config.py`
  - `mneme_service/errors.py`
  - `mneme_service/security.py`
  - `mneme_service/storage.py`
  - `mneme_service/utils.py`
  - `tests/test_contract.py`
  - `task_plan.md`
  - `progress.md`

### Phase 9: Milestone 2 Planning

- **Status:** complete
- Actions taken:
  - Re-read `task_plan.md`, `progress.md`, `findings.md`, `API_MCP_CONTRACT_V0.md`, current REST daemon code, CLI code, and tests.
  - Checked official MCP/OpenAI MCP-related docs:
    - `https://modelcontextprotocol.io/docs/sdk`
    - `https://py.sdk.modelcontextprotocol.io/`
    - `https://py.sdk.modelcontextprotocol.io/server/`
    - `https://py.sdk.modelcontextprotocol.io/testing/`
    - `https://openai.github.io/openai-agents-python/mcp/`
  - Used a read-only explorer subagent to review MCP contract requirements, reusable REST daemon pieces, implementation risks, and parity/adapter tests.
  - Created Milestone 2 implementation plan: `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`.
  - Chose Milestone 2 architecture: stdio MCP server as a thin proxy to the REST daemon, with REST remaining the canonical control-plane and schema source.
  - Added required REST hardening to the plan before MCP parity:
    - direct memory tools should create durable memory-read traces and return `trace_id`;
    - REST tool parameters should handle basic filters, recall token limits, `include_tool_outputs`, and segment page sizing;
    - MCP must preserve REST error/audit/redaction behavior instead of creating a second storage path.
  - Marked next milestone planning complete in `task_plan.md`.
  - Added pending phase for Milestone 2 MCP server and adapter substrate implementation.
  - Did not implement the MCP server in this planning step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`
  - `task_plan.md`
  - `progress.md`

## Session: 2026-06-12

### Planning-with-Files Standardization

- **Status:** complete
- Actions taken:
  - User requested that future project work use `planning-with-files` so development remains systematic, controlled, traceable, and step-based.
  - Re-read `planning-with-files` skill instructions and templates.
  - Re-read current `task_plan.md`, `findings.md`, and `progress.md`.
  - Ran `session-catchup.py`; it produced no unsynced-context output.
  - Standardized `task_plan.md` with current phase, constraints, phase checklists, key questions, decisions, errors, success criteria, and notes.
  - Standardized `findings.md` with requirements, research findings, technical decisions, issues, resources, visual/browser findings, and open questions.
  - Standardized `progress.md` with current snapshot, session/phase logs, test results, error log, and reboot check.
- Files created/modified:
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 10 Task 1: MCP SDK Dependency and Baseline Import Test

- **Status:** complete
- Actions taken:
  - Added failing test `tests/test_mcp_contract.py::test_mcp_server_module_imports`.
  - Verified RED state: focused pytest failed with `ModuleNotFoundError: No module named 'mneme_service.mcp_server'`.
  - Added `mcp>=1.0` to `pyproject.toml`.
  - First install attempt failed under sandbox DNS/network restrictions while resolving build dependencies.
  - Re-ran `.venv/bin/python -m pip install -e '.[test]'` with approved escalation.
  - Installed official MCP Python SDK package `mcp==1.27.2` and transitive dependencies.
  - Verified local SDK surface: `from mcp.server.fastmcp import FastMCP` works and `FastMCP.run` exists.
  - Created minimal `mneme_service/mcp_server.py` exporting `TOOL_NAMES` and `create_mcp_server`.
  - Re-ran focused test, compile check, and full pytest.
- Files created/modified:
  - `tests/test_mcp_contract.py`
  - `pyproject.toml`
  - `mneme_service/mcp_server.py`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Architecture Check: External Service vs Context Engine

- **Status:** complete
- Actions taken:
  - User raised concern that an external universal Mneme module may not be able to fully rebuild and replace an agent's context the way Hermes/OpenClaw context-engine plugins can.
  - Re-read project architecture assumptions.
  - Checked current public docs for OpenClaw context, context engine, agent loop, system prompt, memory, and OpenAI Agents SDK context/session/MCP integration.
  - Confirmed the key architectural distinction: MCP exposes callable tools and context resources, while automatic prompt/context replacement requires runtime-specific pre-model-call hooks.
  - Recorded the finding in `findings.md`: Mneme should be treated as a service plus adapter pattern, with different integration depths per runtime.
- Files created/modified:
  - `findings.md`
  - `progress.md`

### Host Adapter Contract v0 Alignment

- **Status:** complete
- Actions taken:
  - User agreed to formalize Mneme as a universal service plus a host-side adapter contract for future context-engine integrations.
  - Re-read `planning-with-files`, `documentation-and-adrs`, and `api-and-interface-design` skill guidance.
  - Re-read `task_plan.md`, `findings.md`, `progress.md`, `API_MCP_CONTRACT_V0.md`, and `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`.
  - Re-checked current public docs for OpenClaw context/context-engine behavior and OpenAI Agents SDK context/session/MCP behavior.
  - Created `MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
  - Updated `API_MCP_CONTRACT_V0.md` to link REST/MCP service surfaces with the separate host adapter contract.
  - Recorded that MCP-only integrations are `TOOLS_ONLY` unless the host runtime exposes a supported pre-model-call hook.
  - Received read-only subagent review confirming no inherent conflict, with warnings to avoid "universal automatic prompt replacement" claims and to keep Milestone 2 scoped to MCP substrate.
  - Did not start or modify runtime-specific Hermes, OpenClaw, LangGraph, OpenAI Agents SDK, or Codex adapters.
- Files created/modified:
  - `MNEME_HOST_ADAPTER_CONTRACT_V0.md`
  - `API_MCP_CONTRACT_V0.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 2: Harden REST Memory Tool Substrate

- **Status:** complete
- Actions taken:
  - Added RED tests for REST memory-read trace ids, `context_search.filters.event_types`, `filters.after`, `filters.before`, `recall_recent.max_tokens`, `recall_recent.include_tool_outputs`, and `list_segments.page_size`.
  - Confirmed RED failures before implementation:
    - `trace_id` was `None` for `context_search`;
    - `context_search` ignored `filters.event_types`;
    - `context_search` ignored timestamp window filters.
  - Implemented memory-read trace creation for direct REST memory tools and returned the generated `trace_id` in the shared tool envelope.
  - Kept direct memory reads auditable by preserving audit records and `MEMORY_READ` events.
  - Added parameterized SQLite filtering for `context_search.filters.event_types`, `filters.after`, and `filters.before`.
  - Added bounded integer validation for `top_k`, `depth`, `max_events`, `turns`, `max_tokens`, and `page_size` where touched by memory tools.
  - Implemented `recall_recent.include_tool_outputs=false` and approximate `max_tokens` packing.
  - Implemented `list_segments.page_size` capping with `next_page_token=null`.
  - Added dependency-free `mneme_service/tool_names.py` and re-exported `TOOL_NAMES` through `mneme_service/mcp_server.py`.
  - Ran read-only subagent code review for Task 2.
  - Accepted and fixed two review findings:
    - `fetch_event(include_neighbors=true)` now audits seed and neighbor event ids;
    - `recall_recent.max_tokens` now keeps the newest fitting tail and returns it chronologically.
  - Did not implement MCP server proxying, CLI `mneme mcp`, Codex docs, or deeper runtime adapters in this step.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `mneme_service/tool_names.py`
  - `mneme_service/mcp_server.py`
  - `tests/test_contract.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 3: Add REST Client Wrapper

- **Status:** complete
- Actions taken:
  - Added RED tests in `tests/test_mcp_contract.py` for `MnemeRestClient`.
  - Confirmed RED failure before implementation: `ModuleNotFoundError: No module named 'mneme_service.rest_client'`.
  - Created `mneme_service/rest_client.py` as an async `httpx` wrapper for MCP tools.
  - Implemented base URL normalization, bearer token headers, timeout and transport injection, REST tool posting, cost report fetching, standard REST error conversion, and daemon transport error conversion.
  - Kept MCP server tool registration out of scope for this task.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/rest_client.py`
  - `tests/test_mcp_contract.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 4: Register MCP Tools

- **Status:** complete
- Actions taken:
  - Added RED tests for exact MCP tool names, `FastMCP.list_tools()` discovery, and a real `context_search` MCP call proxying to REST through `httpx.MockTransport`.
  - Confirmed RED failure before implementation: `create_mcp_server()` did not accept `base_url` and no tools were registered.
  - Implemented all seven v0 MCP tools in `mneme_service/mcp_server.py`: `context_search`, `fetch_event`, `expand_context`, `recall_recent`, `list_segments`, `explain_context`, and `mneme_cost_report`.
  - Kept MCP tools as thin REST proxies through `MnemeRestClient`; `mcp_server.py` does not import storage or read SQLite directly.
  - Adjusted tests for installed `mcp==1.27.2` behavior: `FastMCP.call_tool()` returns content blocks plus a structured result dict.
  - Did not implement MCP/REST parity fixtures, audit/privacy regression tests, CLI `mneme mcp`, Codex docs, capabilities updates, or deeper runtime adapters in this step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/mcp_server.py`
  - `tests/test_mcp_contract.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 5: Add MCP/REST Parity Tests

- **Status:** complete
- Actions taken:
  - Added in-process MCP/REST parity fixture helpers in `tests/test_mcp_contract.py` using `httpx.ASGITransport` against the FastAPI app.
  - Added parity coverage for `context_search`, `fetch_event`, `expand_context`, `recall_recent`, `list_segments`, `explain_context`, and `mneme_cost_report`.
  - Confirmed an initial RED/failing parity run caused by an incorrect test expectation for a non-existent `usage` field in the current cost report shape.
  - Corrected the parity assertion to compare current v0 cost report fields: `session_id`, `events_ingested`, `prepare_calls`, and `embedding_batches`.
  - Did not implement MCP audit/privacy regression tests, CLI `mneme mcp`, Codex docs, capabilities updates, final smoke tests, or deeper runtime adapters in this step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `tests/test_mcp_contract.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 6: Verify Audit and Privacy Side Effects Through MCP

- **Status:** complete
- Actions taken:
  - Added RED tests in `tests/test_mcp_contract.py` for MCP memory-tool audit side effects and MCP result redaction.
  - Confirmed RED failure before implementation: MCP `fetch_event` error results could leak `sk-mcp-secret` through REST error `details.event_id`.
  - Verified MCP `context_search`, `fetch_event`, and `expand_context` write durable REST audit records, create `MEMORY_READ` events, and expose fetchable `MEMORY_READ` traces through `/v1/traces/{trace_id}`.
  - Verified MCP success results for redacted stored events do not leak raw `sk-mcp-secret`.
  - Fixed the MCP-visible privacy leak by redacting `MnemeError` envelopes at the REST exception boundary.
  - Did not implement CLI `mneme mcp`, Codex docs, capabilities updates, or deeper runtime adapters in this step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_mcp_contract.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 10 Task 7: Add CLI `mneme mcp`

- **Status:** complete
- Actions taken:
  - Added RED tests in `tests/test_mcp_contract.py` for `mneme mcp` parser arguments, environment defaults, and runner behavior.
  - Confirmed RED failure before implementation: `build_parser` was missing and `mneme_service.cli` did not expose `create_mcp_server`.
  - Extracted `build_parser()` and changed `main()` to accept an optional argv sequence for direct parser/runner tests.
  - Added `mneme mcp --base-url ... --token ... --timeout ...`, with `MNEME_BASE_URL` and `MNEME_AUTH_TOKEN` defaults.
  - Wired the command to create the MCP server and run the installed SDK stdio transport through `server.run("stdio")`.
  - Verified `mneme mcp` does not start the REST daemon; the daemon remains a separate explicit `mneme serve` process.
  - Kept `mneme_service/config.py` unchanged because MCP client settings are currently CLI/env inputs rather than daemon settings.
  - Did not implement Codex docs, capabilities updates, or deeper runtime adapters in this step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/cli.py`
  - `tests/test_mcp_contract.py`
  - `task_plan.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`
  - `findings.md`

### Phase 10 Task 8: Update Capabilities and Codex/MCP Documentation

- **Status:** complete
- Actions taken:
  - Added RED tests for `GET /v1/capabilities` advertising MCP support and exact v0 tool names.
  - Added RED tests for Codex/MCP usage documentation and example config.
  - Confirmed RED failures before implementation:
    - `supports_mcp_tools` was still `False`;
    - `adapters/codex/MNEME_CODEX_MCP_USAGE.md` did not exist.
  - Updated REST capabilities to return `supports_mcp_tools=true` and `mcp_tools=list(TOOL_NAMES)` through the dependency-free `mneme_service.tool_names` module.
  - Created `adapters/codex/MNEME_CODEX_MCP_USAGE.md` with tools-only Codex/MCP guidance, daemon/MCP start commands, audited memory-read note, and an explicit no automatic Codex prompt replacement statement.
  - Created `adapters/codex/mcp_server.example.json`.
  - Did not implement deeper runtime adapters or automatic prompt replacement.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_contract.py`
  - `tests/test_mcp_contract.py`
  - `adapters/codex/MNEME_CODEX_MCP_USAGE.md`
  - `adapters/codex/mcp_server.example.json`
  - `task_plan.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`
  - `findings.md`

### Phase 10 Task 9: Full Verification

- **Status:** complete
- Actions taken:
  - Ran full pytest after Task 8.
  - Ran Python compile check for `mneme_service/*.py`.
  - Started a temporary daemon with `mneme_service.cli serve --db /private/tmp/mneme-mcp-plan-smoke.db --insecure-dev --port 8766`.
  - Verified `GET /v1/health` returned `status=OK`.
  - Seeded a synthetic session against the real daemon and used the MCP server SDK helper to list tools and call `context_search`.
  - Confirmed MCP tools include all seven v0 tool names and `context_search` returned `ok=true`, the expected smoke event id, and a `trace_id`.
  - Stopped the temporary daemon cleanly.
  - Marked Phase 10/Milestone 2 MCP server and adapter substrate complete in planning files.
  - Did not implement Hermes, LangGraph, OpenAI Agents SDK, or deeper host adapters.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `task_plan.md`
  - `progress.md`
  - `MILESTONE_2_MCP_SERVER_AND_ADAPTER_PLAN.md`

### Phase 11: Codex Transcript Ingestion Adapter MVP

- **Status:** complete
- Actions taken:
  - Created `MILESTONE_3_CODEX_INGESTION_PLAN.md`.
  - Added RED tests for Codex transcript normalization, REST ingestion through `httpx.ASGITransport`, idempotent replay, service-side redaction, CLI parsing, and offline/reference docs.
  - Added `mneme_service/codex_ingest.py` with a dependency-free transcript normalizer and async REST import flow.
  - Added `mneme codex-ingest --input ... --base-url ... --token ... --timeout ...`.
  - Added Codex ingestion usage docs and a safe example transcript fixture.
  - Kept live Hermes, live `hermes-mneme`, and live Codex configuration untouched.
- Files created/modified:
  - `MILESTONE_3_CODEX_INGESTION_PLAN.md`
  - `mneme_service/codex_ingest.py`
  - `mneme_service/cli.py`
  - `tests/test_codex_ingest.py`
  - `adapters/codex/MNEME_CODEX_INGEST_USAGE.md`
  - `adapters/codex/transcript.example.json`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 12: Codex MCP Dogfood Restart Handoff

- **Status:** complete
- Actions taken:
  - Created Codex dogfood restart setup guide and new-session prompt.
  - Created `adapters/codex/codex_mcp_dogfood.example.json` using the project `.venv/bin/python`, `PYTHONPATH`, token, and port `8767`.
  - Installed and loaded a macOS LaunchAgent from `.local/com.openclaw.mneme-dogfood.plist`.
  - Verified `GET /v1/health` on `http://127.0.0.1:8767`.
  - Imported `adapters/codex/transcript.example.json` into `.local/mneme-dogfood.db`.
  - Verified REST `context_search` and `fetch_event` for `codex-codex-example-session-turn-1-0003`.
  - Updated `/Users/openclaw/.codex/config.toml` with `[mcp_servers.mneme]`.
  - Created `/Users/openclaw/.codex/config.toml.bak-mneme-dogfood`.
  - Verified TOML syntax with project Python 3.12 `tomllib`.
  - Verified in-process MCP smoke against the running daemon: all seven tools listed and `context_search` returned `ok=true`.
  - Hardened `adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md` after the first new-session agent treated the prompt as read-only context instead of an execution handoff.
  - Added `adapters/codex/MNEME_CODEX_DOGFOOD_FOLLOWUP_PROMPT.md` for already-started sessions that need to be redirected into planning-with-files execution.
  - Kept live Hermes and live `hermes-mneme` untouched.
- Files created/modified:
  - `.local/com.openclaw.mneme-dogfood.plist`
  - `.local/mneme-dogfood.db`
  - `adapters/codex/CODEX_DOGFOOD_RESTART_SETUP.md`
  - `adapters/codex/MNEME_CODEX_DOGFOOD_FOLLOWUP_PROMPT.md`
  - `adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md`
  - `adapters/codex/codex_mcp_dogfood.example.json`
  - `/Users/openclaw/.codex/config.toml`
  - `/Users/openclaw/.codex/config.toml.bak-mneme-dogfood`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 12 Dogfood: Codex MCP Tool Verification

- **Status:** complete
- Actions taken:
  - Re-read the prompt-specified project files before running the dogfood check.
  - Confirmed Mneme MCP tools are visible in the current Codex session as `mcp__mneme.context_search`, `mcp__mneme.fetch_event`, `mcp__mneme.expand_context`, `mcp__mneme.recall_recent`, `mcp__mneme.list_segments`, `mcp__mneme.explain_context`, and `mcp__mneme.mneme_cost_report`.
  - Called `context_search` with `session_id=codex-example-session`, `query=focused pytest passed`, `scope=SESSION`, `top_k=5`, and `include_content=true`.
  - Confirmed search returned `ok=true` and found expected event `codex-codex-example-session-turn-1-0003` with snippet `focused pytest passed`.
  - Called `fetch_event` for `codex-codex-example-session-turn-1-0003` with `full=true` and `include_neighbors=false`.
  - Confirmed fetched event content is `focused pytest passed`, type is `TOOL_OUTPUT`, tool name is `pytest`, and parent event is `codex-codex-example-session-turn-1-0002`.
  - Did not repair live MCP config because the Mneme tools were visible and functional.
  - Did not start Hermes adapter, LangGraph adapter, OpenAI Agents SDK adapter, or deeper Codex runtime hooks.
- Files created/modified:
  - `findings.md`
  - `progress.md`

### Roadmap Reorientation: Codex Memory Dogfood and Provider Config

- **Status:** complete
- Actions taken:
  - User clarified the desired next direction: make Mneme useful as a real Codex knowledge-base memory, clarify whether Codex can get automatic context assembly, define where embedding/LLM provider settings live, then prepare for GitHub publication and later Hermes adapter work.
  - Re-read `planning-with-files` instructions, `task_plan.md`, `progress.md`, and `findings.md`.
  - Ran `session-catchup.py`; it produced no unsynced-context output.
  - Inspected current `mneme_service/config.py` and confirmed the daemon currently has only DB/auth/host/port/limit settings.
  - Checked the API contract and current service capability facts: minimal mode is provider-free; embeddings, reranking, and LLM enrichment are not implemented in the daemon yet.
  - Created `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`.
  - Updated `task_plan.md` with Phase 13 Codex memory dogfood, Phase 14 provider configuration, Phase 15 GitHub publication prep, and Phase 16 Hermes adapter planning gate.
  - Updated `findings.md` to record that Codex/MCP is pull-based memory, storage is populated through REST ingestion, and provider settings must be explicit before optional provider calls.
  - Did not change runtime code in this planning step.
  - Did not touch live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 13A: Hermes-Mneme Parity Gap Audit

- **Status:** complete
- Actions taken:
  - User challenged whether the universal service is drifting away from `hermes-mneme`, especially because embeddings/reranking/LLM enrichment are not implemented in the daemon.
  - Re-read planning files and ran `session-catchup.py`; it produced no unsynced-context output.
  - Inspected `/Users/openclaw/.hermes/plugins/hermes-mneme` read-only. No files there were modified.
  - Compared `hermes-mneme` README, architecture docs, config, engine, index, store, router, segmenter, classifier, prompt builder, tools, graph, enrichment, and parser against the universal service code.
  - Confirmed `hermes-mneme` is a deep Hermes context engine with automatic `compress()` hot-path integration, semantic embeddings, `sqlite-vec`/cosine retrieval, drift segmentation, intent routing, graph/dependency scoring, optional reranker, optional LLM enrichment, execution state, state history, and budgeted prompt assembly.
  - Confirmed the universal service is currently a portable substrate with REST/MCP, SQLite event storage, lexical/recency retrieval, context-prepare skeleton, redaction, audit/traces, MCP parity, and Codex ingest/dogfood support.
  - Created `HERMES_MNEME_COMPARISON.md` with functional/mechanical/logical comparison and recommended roadmap adjustment.
  - Updated `task_plan.md` and `findings.md` so future work does not continue Codex dogfood polish before considering parity recovery.
- Files created/modified:
  - `HERMES_MNEME_COMPARISON.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Direction Change: Functional Parity Before Adapters

- **Status:** complete
- Actions taken:
  - User confirmed the desired interpretation: pause adapter work and first port the `hermes-mneme` functional core into the universal daemon.
  - Clarified the rule: port runtime-neutral behavior, not Hermes-specific lifecycle glue.
  - Created `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`.
  - Updated `task_plan.md` so Phase 14 is Hermes-Mneme functional parity recovery.
  - Deferred Codex dogfood polish, GitHub publication prep, and Hermes/other adapters until parity recovery provides real semantic/execution-state memory.
  - Updated `findings.md` with the direction decision and adapter pause.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Scope Correction: Generic Drift Belongs in the Daemon

- **Status:** complete
- Actions taken:
  - Read the newer local `_hermes-mneme-native` copy read-only.
  - Confirmed the native Hermes path uses `on_turn_complete()` for ingestion and `prepare_request_messages()` for request-only assembly when the host exposes native hooks; `compress()` remains a legacy fallback.
  - Read the local `_hermes-agent-pr` context-engine contract tests/docs read-only.
  - Confirmed Hermes PR shape aligns with the Host Adapter Contract: host hooks provide session, turn, request, model, and tool metadata; the engine owns memory decisions.
  - Corrected Phase 14 scope: host-specific hook/session-id plumbing stays in adapters, but runtime-neutral session/topic drift semantics belong in the daemon.
  - Updated Milestone 5, task plan, findings, and comparison docs to include semantic drift, segment boundaries, resume/fresh-session classification, lineage/carry-over, first-turn resume context fill, and drift traces.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files modified:
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `HERMES_MNEME_COMPARISON.md`
  - `progress.md`

### Phase 14 Task 1: Provider Config Foundation

- **Status:** complete
- Actions taken:
  - Added RED tests in `tests/test_config.py` for config precedence, provider
    summaries, capabilities, and parseable secret-safe example config.
  - Confirmed RED failure before implementation: `ProviderSettings` and
    `load_settings` were missing.
  - Implemented `ProviderSettings`, provider availability/summary helpers,
    and `load_settings()` with precedence `CLI > env > config file > defaults`.
  - Added env support for daemon settings plus embeddings/reranker/LLM provider
    settings.
  - Added provider-aware `/v1/capabilities` output without leaking API keys.
  - Added `mneme serve --config` plus provider enable/disable/model/base-url/API
    key flags.
  - Added `mneme.example.toml` with no real secrets.
  - Did not implement embedding/reranker/LLM clients or any provider calls.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `tests/test_config.py`
  - `mneme_service/config.py`
  - `mneme_service/app.py`
  - `mneme_service/cli.py`
  - `mneme.example.toml`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Autonomous Next-Session Prompt

- **Status:** complete
- Actions taken:
  - Created `NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md`.
  - Encoded the user's autonomy preference: continue through multiple Phase 14
    tasks without waiting for "continue" after each small step.
  - Encoded the blocker rule: stop and ask when a product/architecture choice is
    missing, when contract-impacting options conflict, or when live Hermes/live
    `hermes-mneme`/external config/network provider calls would be required.
  - Included required planning/TDD workflow, current status, next action, and
    verification requirements.
- Files created/modified:
  - `NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 2: Embedding Provider and Index

- **Status:** complete
- Actions taken:
  - Re-read required Phase 14 planning/context files and ran
    `session-catchup.py`; it produced no unsynced-context output.
  - Ran baseline full pytest before implementation: `30 passed, 1 warning`.
  - Read the permitted `_hermes-mneme-native` reference implementation for
    embedding/index/circuit-breaker/compression parity details.
  - Added RED tests in `tests/test_embeddings.py` for OpenAI-compatible batch
    provider shape, provider circuit breaker, SQLite embedding rows, Python
    cosine fallback, redaction-before-embedding, tool-output embedding
    compression, cost metrics, and store-event-even-when-embedding-fails.
  - Confirmed RED failure before implementation:
    `ModuleNotFoundError: No module named 'mneme_service.embeddings'`.
  - Implemented `mneme_service.embeddings` with `EmbeddingProvider`,
    `OpenAICompatibleEmbeddingProvider`, `EmbeddingIndex`, batch stats, Python
    cosine search, packed-float embedding storage, and deterministic head/tail
    tool-output compression for embedding input only.
  - Added SQLite `embedding_index` and `embedding_metrics` tables plus
    embedding export/delete/cost-report accounting.
  - Wired `/v1/events` ingestion so accepted events are stored first, then
    best-effort indexed when embeddings are enabled; provider/index failures do
    not block ingestion.
  - Verified no Phase 14 Task 2 tests make real provider calls; tests use
    `httpx.MockTransport` or fake providers.
  - Checked `.venv` for `sqlite_vec`; it is not installed, so Task 2 verified
    Python cosine fallback rather than optional vector acceleration.
  - The installed `security-guidance` skill bundle lacked referenced ASVS
    files; applied the Mneme contract's concrete security requirements
    directly.
  - Accidentally created `tests/test_embeddings.py` one directory above the
    project with the first patch, then immediately deleted that file and
    recreated it under the project root.
  - Did not modify live Hermes or live `hermes-mneme`.
  - Did not integrate semantic ranking into REST/MCP `context_search`; that
    starts in Phase 14 Task 3.
- Files created/modified:
  - `mneme_service/embeddings.py`
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_embeddings.py`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 3: Hybrid Retrieval Pipeline

- **Status:** complete
- Actions taken:
  - Added RED tests in `tests/test_retrieval.py` for semantic hit retrieval
    when keywords miss, keyword/recency fallback without embeddings, and
    degraded trace/warning behavior when the embedding provider fails.
  - Confirmed RED failures before implementation:
    semantic query returned no results, memory-read traces had no retrieval
    metadata, and provider-outage search returned no degraded warning.
  - Added `EmbeddingIndex.search_with_status()` to distinguish vector results
    from degraded embedding-query failures.
  - Added `hybrid_context_search()` behind REST `context_search`, merging
    vector candidates with keyword/recency fallback while preserving event-type
    and timestamp filters.
  - Extended direct memory-read traces for `context_search` with retrieval
    strategies, candidate count, selected count, degraded flag, fallbacks, and
    warnings.
  - Verified MCP parity remains intact through `tests/test_mcp_contract.py`
    because MCP tools proxy REST rather than ranking independently.
  - Did not add graph/dependency scoring, reranking, execution-state query
    expansion, or budgeted context assembly in this step.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `tests/test_retrieval.py`
  - `mneme_service/app.py`
  - `mneme_service/embeddings.py`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 4: Execution State and Goal History

- **Status:** complete
- Actions taken:
  - Read permitted `_hermes-mneme-native` state/history reference code and
    tools read-only.
  - Used `api-and-interface-design` because Task 4 adds public REST/MCP tools.
  - Added RED tests in `tests/test_state.py` for deterministic state updates,
    goal history, restart persistence, export/delete coverage, and MCP
    discovery/proxy parity.
  - Confirmed RED failures before implementation:
    `/v1/tools/get_execution_state` and `/v1/tools/get_goal_history` returned
    404, and MCP discovery did not list the new tools.
  - Added `mneme_service/state.py` with versioned state/default/update helpers.
  - Added SQLite `execution_state` and append-only `state_history` tables.
  - Wired event ingestion to update execution state from normalized events:
    user messages, tool calls/outputs, assistant messages, and decisions.
  - Added REST tools `get_execution_state` and `get_goal_history`, both using
    the shared tool envelope and memory-read audit trace path.
  - Added MCP proxy tools and updated `TOOL_NAMES`, capabilities, and MCP
    contract tests.
  - Updated `API_MCP_CONTRACT_V0.md` with the new REST/MCP tools and schemas.
  - Did not implement Hermes lineage fallback, LLM enrichment, or state blocks
    in `/v1/context/prepare`.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/state.py`
  - `mneme_service/storage.py`
  - `mneme_service/app.py`
  - `mneme_service/tool_names.py`
  - `mneme_service/mcp_server.py`
  - `tests/test_state.py`
  - `tests/test_mcp_contract.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice A: Intent Classifier and Explicit Switch Segments

- **Status:** complete slice; overall Task 5 remains in progress
- Actions taken:
  - Added RED tests in `tests/test_classifier.py` for English/Russian topic switches, English/Russian clarification questions, and continuation defaults.
  - Added RED tests in `tests/test_segments.py` for explicit topic-switch segment rollover exposed through `list_segments`, plus continuation messages staying in one active segment.
  - Confirmed RED failure before implementation: `mneme_service.classifier` was missing.
  - Added `mneme_service/classifier.py` with a deterministic runtime-neutral classifier for `CONTINUATION`, `SWITCH`, and `CLARIFICATION`, including Russian and English switch/question patterns.
  - Added `mneme_service/segments.py` with user-message segment updates, explicit switch closure, active segment creation, anchor ids, token counts, titles, and drift reasons.
  - Added `Store` segment helpers for active lookup, segment counting, and upsert that preserves the original segment ordering timestamp.
  - Wired event ingestion to classify accepted redacted user messages and update segments after canonical event storage and execution-state update.
  - Kept Task 5 broader drift work out of this slice: embedding drift, new-task/resume/fresh classification, lineage/carry-over, first-turn resume context fill, and drift traces remain next.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/classifier.py`
  - `mneme_service/segments.py`
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_classifier.py`
  - `tests/test_segments.py`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice B: Embedding Drift Segment Rollover

- **Status:** complete slice; overall Task 5 remains in progress
- Actions taken:
  - Added RED coverage in `tests/test_classifier.py` for high `embedding_drift` resolving to `NEW_TASK`.
  - Added RED coverage in `tests/test_segments.py` for semantic drift rollover after an active segment has three indexed embeddings.
  - Confirmed RED failures before implementation:
    - `INTENT_NEW_TASK` was missing from `mneme_service.classifier`;
    - high embedding drift still left all user messages in one active segment.
  - Added `INTENT_NEW_TASK` and the `embedding_drift` classifier signal with the reference threshold `0.35`.
  - Added `EmbeddingIndex.embedding_drift_against_segment()` with centroid comparison, cold-start behavior under three embeddings, provider-failure fallback to `0.0`, and no real provider calls in tests.
  - Wired ingestion so user-message embeddings are tagged with the event-driven segment id via `metadata.mneme_segment_id`.
  - Updated segment rollover so `NEW_TASK` closes the active segment and opens a new one with `drift_reason=EMBEDDING_DRIFT`.
  - Verified embedding/retrieval suites still pass after changing app-ingested embedding segment ids.
  - Kept resume/fresh-session classification, lineage/carry-over, first-turn resume context fill, and drift traces out of this slice.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/classifier.py`
  - `mneme_service/segments.py`
  - `mneme_service/app.py`
  - `mneme_service/embeddings.py`
  - `tests/test_classifier.py`
  - `tests/test_segments.py`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice C: Segment Drift Traces

- **Status:** complete slice; overall Task 5 remains in progress
- Actions taken:
  - Added RED coverage in `tests/test_segments.py` expecting `SEGMENT_DRIFT` traces for explicit-switch and high embedding-drift segment rollovers.
  - Confirmed RED failures before implementation: segment rollover worked, but export contained no `SEGMENT_DRIFT` traces for the triggering events.
  - Added additive trace creation during event ingestion after segment rollover, using the previous active segment, classifier result, and opened segment.
  - Kept trace payloads redacted by recording classifier signals, intent/drift reason, closed/opened segment ids, event counts, fallbacks, and warnings without raw message content.
  - Updated `API_MCP_CONTRACT_V0.md` to document `SEGMENT_DRIFT` traces.
  - Kept resume/fresh-session classification, lineage/carry-over, and first-turn resume context fill out of this slice.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_segments.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice D: Fresh/Resume Session Classification

- **Status:** complete slice; overall Task 5 remains in progress
- Actions taken:
  - Added RED coverage in `tests/test_session_drift.py` for fresh new sessions, existing sessions with prior events, and adapter lifecycle metadata requesting resume.
  - Confirmed RED failures before implementation: `/v1/sessions/start` did not return `session_state`.
  - Added `mneme_service/session_drift.py` with deterministic `FRESH`/`RESUME` classification and resume source detection.
  - Added `Store.session_counts()` so classification can use existing canonical event and turn counts without changing session idempotency.
  - Wired `POST /v1/sessions/start` to return additive `mneme.session_state.v0` metadata with prior counts, adapter resume signal, lineage session id, resume source, and `requires_context_fill`.
  - Updated `API_MCP_CONTRACT_V0.md` to document `mneme.session_state.v0`.
  - Kept lineage/carry-over and first-turn resume context fill out of this slice.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/session_drift.py`
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_session_drift.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice E: Lineage Carry-Over Retrieval

- **Status:** complete slice; overall Task 5 remains in progress
- Actions taken:
  - Added RED coverage in `tests/test_session_lineage.py` for parent/child lineage carry-over search, fetch through child session, export separation, and unrelated-session isolation.
  - Confirmed RED failure before implementation: export lacked `session_lineage`, and child sessions had no carry-over path.
  - Added `session_lineage` storage with cycle-safe edge creation from explicit adapter metadata such as `parent_session_id`.
  - Added lineage-chain resolution to session-scoped keyword search, embedding lookup, `fetch_event`, recent recall, and child/neighbor graph traversal.
  - Kept canonical events in their original sessions; child exports show child events plus lineage edges, not copied parent events.
  - Added `mneme.session_lineage.v0` to capabilities and documented the schema in `API_MCP_CONTRACT_V0.md`.
  - Kept first-turn resume context fill out of this slice.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_session_lineage.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 5 Slice F: First-Turn Resume Context Fill

- **Status:** complete; Task 5 complete
- Actions taken:
  - Added RED coverage in `tests/test_resume_fill.py` for one-shot first prepare fill after session resume and lineage resume.
  - Confirmed RED failures before implementation: unmatched under-budget prepare returned `changed=false`, and lineage child sessions did not require context fill.
  - Added lineage-aware session counts to `mneme.session_state.v0` signals so parent/previous evidence can trigger `requires_context_fill`.
  - Added a persisted one-shot `session_context_fill` latch set by `POST /v1/sessions/start`.
  - Updated `/v1/context/prepare` so a pending fill with empty ordinary retrieval selects recent current/lineage events with reason `RESUME_CONTEXT_FILL`.
  - Marked the latch fulfilled after successful evidence insertion so later under-budget requests can pass through normally.
  - Updated `API_MCP_CONTRACT_V0.md` to document the one-shot fill behavior and `RESUME_CONTEXT_FILL` reason.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `mneme_service/session_drift.py`
  - `tests/test_resume_fill.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 6 Slice A: Typed Graph Edge Persistence

- **Status:** complete slice; overall Task 6 remains in progress
- Actions taken:
  - Added RED coverage in `tests/test_graph.py` for typed graph edge export and typed `expand_context` traversal.
  - Confirmed RED failures before implementation: export lacked `event_graph_edges`, and `expand_context` returned generic `PARENT`/`CHILD` labels.
  - Added `event_graph_edges` storage with versioned `mneme.graph_edge.v0` export objects.
  - Ingest now derives typed edges from `parent_event_ids`: `TOOL_RESULT`, `DECISION_FOLLOWS`, or generic `FOLLOWS`.
  - Updated `expand_context` to traverse typed graph edges when present while preserving legacy parent/child fallback.
  - Verified graph expansion audit still records every exposed event id.
  - Updated `API_MCP_CONTRACT_V0.md` to document `mneme.graph_edge.v0`.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `tests/test_graph.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 6 Slice B: Dependency-Aware Retrieval Scoring

- **Status:** complete; Task 6 complete
- Actions taken:
  - Added RED coverage in `tests/test_graph.py` expecting `context_search` to include graph dependencies for a primary keyword hit.
  - Confirmed RED failure before implementation: keyword retrieval returned only the directly matching event.
  - Updated `hybrid_context_search` to add direct typed graph neighbors of primary semantic/keyword hits before `top_k` packing.
  - Dependency candidates use strategy `GRAPH_DEPENDENCY`, reason `GRAPH_DEPENDENCY:<edge_type>`, and a smaller score than the primary match.
  - Updated `API_MCP_CONTRACT_V0.md` to document graph dependency candidates.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_graph.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 7 Slice A: Execution-State Context Block

- **Status:** complete; Task 7 in progress
- Actions taken:
  - Added RED coverage in `tests/test_context_assembly.py` expecting `/v1/context/prepare` to insert a request-only `[MNEME EXECUTION STATE]` block.
  - Confirmed RED failure before implementation: unmatched under-budget prepare returned `changed=false`.
  - Added `execution_state_context_block()` assembly from stored `mneme.execution_state.v0` fields.
  - Updated `/v1/context/prepare` to include the state block only when `policy.include_execution_state=true`, the state is non-empty, and the token estimate fits `budget_split.execution_state_ratio`.
  - Kept generated context request-only: the block is returned as a `mneme_generated` message and is not exported as a canonical event.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_context_assembly.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 7 Slice B: Protected Recent Tail

- **Status:** complete; Task 7 in progress
- Actions taken:
  - Added RED coverage in `tests/test_context_assembly.py` expecting over-budget prepare to preserve the system prompt and recent message tail while dropping old request history.
  - Confirmed RED failure before implementation: prepare inserted an empty `mneme_generated` assistant message.
  - Added `protected_tail_messages()` to keep a contiguous suffix of recent request messages under `budget_split.recent_tail_ratio`, while preserving the system prompt when requested.
  - Updated `/v1/context/prepare` to report `protected_tail_tokens` and to return trimmed request messages without adding an empty memory block when no state or retrieved evidence exists.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_context_assembly.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 7 Slice C: Retrieved Context Packing

- **Status:** complete; Task 7 in progress
- Actions taken:
  - Added RED coverage in `tests/test_context_assembly.py` expecting retrieved candidates over `retrieved_context_ratio` to be dropped from the generated evidence block.
  - Confirmed RED failure before implementation: prepare included both short and oversized retrieved events.
  - Added `pack_retrieved_events()` and `retrieved_event_line()` to separate retrieval candidates from budget-selected evidence.
  - Updated `/v1/context/prepare` response trace with `dropped_event_refs` and stored context-prepare traces with `dropped_events`.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_context_assembly.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 7 Slice D: Cross-Block Collision Resolution

- **Status:** complete; Task 7 complete
- Actions taken:
  - Added RED coverage in `tests/test_context_assembly.py` for a total-budget collision where retrieved evidence fits its own slice but no longer fits after system prompt, protected tail, and headroom are counted.
  - Confirmed RED failure before implementation: prepare inserted the retrieved evidence block and exceeded the final budget/headroom envelope.
  - Moved context-prepare trace creation after final packing so selected/dropped metadata reflects the actual returned model request.
  - Added final collision handling: retrieved evidence is dropped first with reason `CONTEXT_COLLISION_BUDGET_EXCEEDED`, state can be dropped next, and protected tail is tightened last if required.
  - Verified Task 7 with focused context assembly tests, broader regression, full pytest, compile check, and conflict/trailing-whitespace scans.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `tests/test_context_assembly.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 8: Optional Reranker

- **Status:** complete
- Actions taken:
  - Added RED coverage in `tests/test_reranker.py` for HTTP reranker response parsing, successful `context_search` reranking, and degraded fallback when reranking fails.
  - Confirmed RED failure before implementation: `mneme_service.reranker` did not exist.
  - Added `mneme_service.reranker.HttpRerankerProvider`, `RerankerProvider`, and `RerankResult`.
  - Added an injectable reranker provider to `create_app()` and applied reranking in the REST-canonical `hybrid_context_search` path after semantic/keyword/recency/graph merge.
  - Preserved original ranking on reranker failure and surfaced `RERANKER_UNAVAILABLE` through warnings, retrieval trace `degraded=true`, and `fallbacks`.
  - Added persistent `reranker_metrics` and exposed `reranker_calls` / `reranker_failures` in cost reports.
  - Did not make real provider calls in tests; HTTP provider parsing uses `httpx.MockTransport`.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `mneme_service/reranker.py`
  - `tests/test_reranker.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 9: Optional LLM Enrichment

- **Status:** complete
- Actions taken:
  - Added RED coverage in `tests/test_enrichment.py` for strict JSON provider parsing, redacted state enrichment, history propagation, cost metrics, and degraded non-blocking failure.
  - Confirmed RED failure before implementation: `mneme_service.enrichment` did not exist.
  - Added `mneme_service.enrichment.HttpLLMEnrichmentProvider`, `EnrichmentProvider`, and `EnrichmentResult`.
  - Added injectable enrichment provider support to `create_app()` and applied enrichment after deterministic state update but before state/history commit.
  - Restricted enrichment to structured fields: `intent_label`, `decisions`, `active_entities`, and `open_loops`.
  - Redacted provider updates before storing them and kept ingestion successful when enrichment fails.
  - Added persistent `enrichment_metrics` and exposed `enrichment_calls` / `enrichment_failures` in cost reports.
  - Did not make real provider calls in tests; HTTP provider parsing uses `httpx.MockTransport`.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `mneme_service/app.py`
  - `mneme_service/storage.py`
  - `mneme_service/enrichment.py`
  - `tests/test_enrichment.py`
  - `API_MCP_CONTRACT_V0.md`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14 Task 10: Parity Acceptance Suite

- **Status:** complete; Phase 14 complete
- Actions taken:
  - Added `tests/test_parity_recovery.py` as an end-to-end acceptance suite for the recovered Hermes-Mneme quality pipeline.
  - Covered minimal mode with zero provider calls and redaction across search/export/traces.
  - Covered provider-backed semantic retrieval, reranking, enrichment, provider-input redaction, and cost counters using fake providers.
  - Covered embedding outage fallback to keyword/recency while preserving stored events.
  - Covered restart-safe execution state/history, explicit switch segmentation, fresh/resume classification, lineage carry-over, one-shot resume context fill, and budgeted `/v1/context/prepare`.
  - Covered MCP/REST parity and redaction through the MCP proxy.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `tests/test_parity_recovery.py`
  - `MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 15: GitHub Publication Preparation

- **Status:** complete
- Actions taken:
  - Added top-level `README.md` with honest REST/MCP service positioning, integration-depth distinction, quick start, provider configuration link, Codex tools-only usage, tests, and publication gate.
  - Added `docs/INSTALLATION.md`, `docs/PROVIDER_CONFIGURATION.md`, `docs/TESTING_AND_CI.md`, and `docs/PUBLICATION_CHECKLIST.md`.
  - Updated `pyproject.toml` with setuptools build metadata, README metadata, package discovery, classifiers, and package keywords.
  - Added `.github/workflows/ci.yml` for Python 3.11/3.12 install, full pytest, explicit parity acceptance, and compile checks.
  - Updated `.gitignore` for local caches, SQLite DBs, `.local/`, build artifacts, and egg-info artifacts.
  - Earlier public-prep decision kept `adapters/codex` in this repository; this
    is now superseded by the corrected split-publication model.
  - Confirmed docs keep Codex/MCP claims tools-only and do not claim automatic prompt replacement.
  - Confirmed provider features remain optional and disabled unless configured.
  - Added Apache-2.0 `LICENSE` and `NOTICE` with Ivan Konstantinov as the 2026 copyright owner after owner approval.
- Files created/modified:
  - `README.md`
  - `LICENSE`
  - `NOTICE`
  - `docs/INSTALLATION.md`
  - `docs/PROVIDER_CONFIGURATION.md`
  - `docs/TESTING_AND_CI.md`
  - `docs/PUBLICATION_CHECKLIST.md`
  - `.github/workflows/ci.yml`
  - `.gitignore`
  - `pyproject.toml`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 14B: Parity Hardening While Hermes PR Is Pending

- **Status:** complete
- Actions taken:
  - Accepted the user's direction to defer Phase 16 Hermes adapter work until
    the upstream Hermes context-engine hook PR is accepted.
  - Recorded that building a Hermes bridge against the legacy compaction path
    would create duplicate/throwaway integration work.
  - Created `MILESTONE_5B_PARITY_HARDENING_PLAN.md` to continue safe
    adapter-independent Phase 14 work while the PR is pending.
  - Updated `HERMES_MNEME_COMPARISON.md` with a post-Phase-14 status section
    and marked the old comparison table as historical pre-Phase-14 context.
  - Added `mneme_service.benchmarks.run_local_benchmark`, the `mneme benchmark`
    CLI command, focused benchmark tests, and benchmark documentation.
  - Verified the benchmark harness with local fake embeddings and no external
    provider calls.
  - Added provider robustness tests for malformed embedding payloads, mixed
    embedding dimensions, out-of-range reranker indexes, and non-JSON LLM
    enrichment responses.
  - Hardened embedding parsing/indexing so malformed vectors and mixed-dimension
    batches degrade instead of entering the index as successful embeddings.
  - Checked local `sqlite_vec` availability and added vector acceleration docs
    documenting Python cosine fallback as the verified path.
  - Ran and recorded the final Phase 14B verification gate.
- Files created/modified:
  - `MILESTONE_5B_PARITY_HARDENING_PLAN.md`
  - `HERMES_MNEME_COMPARISON.md`
  - `docs/BENCHMARKS.md`
  - `docs/VECTOR_ACCELERATION.md`
  - `README.md`
  - `mneme_service/benchmarks.py`
  - `mneme_service/cli.py`
  - `tests/test_benchmarks.py`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

### Phase 13 Task 1: Codex Memory Operating Contract

- **Status:** complete
- Actions taken:
  - Re-read `task_plan.md`, `findings.md`, `progress.md`,
    `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`, and
    `MILESTONE_5B_PARITY_HARDENING_PLAN.md`.
  - Confirmed Phase 13 is no longer blocked because Phase 14 parity recovery
    and Phase 14B parity hardening are complete.
  - Refreshed `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`
    so it reflects the post-Phase-14 daemon: semantic retrieval, execution
    state, lineage, provider-safe behavior, and budgeted prepare are available.
  - Added a RED doc-contract test for the Codex long-session operating guide.
  - Updated `adapters/codex/MNEME_CODEX_MCP_USAGE.md` with the operating
    contract for session start/resume, compaction recovery, long interruption
    recovery, evidence-based MCP usage, tool selection, lineage/state usage,
    provider-safe behavior, and the tools-only boundary.
  - Updated Codex dogfood restart/follow-up prompts so they treat Mneme memory
    as evidence rather than hidden prompt authority and include current memory
    tool expectations.
  - Verified the focused doc-contract test is GREEN.
  - Did not start Hermes adapter work and did not build a compaction bridge.
  - Did not modify live Hermes or live `hermes-mneme`.
- Files created/modified:
  - `adapters/codex/MNEME_CODEX_MCP_USAGE.md`
  - `adapters/codex/CODEX_DOGFOOD_RESTART_SETUP.md`
  - `adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md`
  - `adapters/codex/MNEME_CODEX_DOGFOOD_FOLLOWUP_PROMPT.md`
  - `tests/test_mcp_contract.py`
  - `MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md`
  - `task_plan.md`
  - `findings.md`
  - `progress.md`

## Test Results

| Test | Input | Expected | Actual | Status |
|---|---|---|---|---|
| Milestone 1 contract tests | `.venv/bin/python -m pytest -q` | All tests pass | `6 passed, 1 warning` | pass |
| Milestone 1 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Milestone 1 daemon smoke | `mneme_service.cli serve --db /private/tmp/mneme-smoke-final-3.db --insecure-dev --port 8766` plus `/v1/health` | Health returns `status: OK` | Returned `status: OK` | pass |
| Planning standardization | `python3 .../session-catchup.py /Users/openclaw/.hermes/plugins/_mneme-universal-context-service` | No required catchup changes | No output | pass |
| Milestone 2 Task 1 RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_server_module_imports -q` before implementation | Fails because `mneme_service.mcp_server` is missing | Failed with `ModuleNotFoundError` | pass |
| Milestone 2 Task 1 focused GREEN | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_server_module_imports -q` | Test passes | `1 passed` | pass |
| Milestone 2 Task 1 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Milestone 2 Task 1 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `7 passed, 1 warning` | pass |
| Host Adapter Contract doc alignment | Documentation-only review | Service API remains separate from host lifecycle contract | `MNEME_HOST_ADAPTER_CONTRACT_V0.md` created and cross-linked | pass |
| Host Adapter Contract wording scan | `rg` scan for conflict markers and trailing whitespace on changed docs | No conflict markers or trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 10 Task 2 focused RED | `.venv/bin/python -m pytest tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion tests/test_contract.py::test_memory_tool_filters_limits_and_segment_page_size -q` before implementation | Fails on missing memory-read trace id and ignored filters | Failed with `assert None` for `trace_id`, then failed on ignored `event_types`, then failed on ignored timestamp filters | pass |
| Phase 10 Task 2 review RED | Same focused command after adding review regression assertions | Fails on under-audited fetch neighbors and older-first recent packing | Failed with trace ids missing `event-call`/`event-decision` and recent ids missing `event-note` | pass |
| Phase 10 Task 2 focused GREEN | `.venv/bin/python -m pytest tests/test_contract.py::test_memory_tools_audit_memory_read_and_graph_expansion tests/test_contract.py::test_memory_tool_filters_limits_and_segment_page_size -q` | Focused tests pass | `2 passed, 1 warning` | pass |
| Phase 10 Task 2 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 2 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `8 passed, 1 warning` | pass |
| Phase 10 Task 3 focused RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_rest_client_posts_tool_with_normalized_base_url_and_bearer_token tests/test_mcp_contract.py::test_rest_client_normalizes_rest_error_to_tool_envelope tests/test_mcp_contract.py::test_rest_client_normalizes_transport_error_to_tool_envelope -q` before implementation | Fails because `mneme_service.rest_client` is missing | `3 failed` with `ModuleNotFoundError` | pass |
| Phase 10 Task 3 focused GREEN | Same focused command after implementation | Focused REST client tests pass | `3 passed` | pass |
| Phase 10 Task 3 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `4 passed` | pass |
| Phase 10 Task 3 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `11 passed, 1 warning` | pass |
| Phase 10 Task 3 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 4 focused RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_tool_names_match_contract tests/test_mcp_contract.py::test_mcp_tools_are_discoverable tests/test_mcp_contract.py::test_mcp_context_search_tool_proxies_rest_envelope -q` before implementation | Fails because `create_mcp_server` does not accept REST proxy settings and tools are not registered | `2 failed, 1 passed` with unexpected `base_url` argument | pass |
| Phase 10 Task 4 focused GREEN | Same focused command after implementation | MCP discovery and proxy test pass | `3 passed` | pass |
| Phase 10 Task 4 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `7 passed` | pass |
| Phase 10 Task 4 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `14 passed, 1 warning` | pass |
| Phase 10 Task 4 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 5 parity RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity -q` before correction | Reveals parity/test mismatch | Failed with `KeyError: 'usage'` because the current cost report has no `usage` object | pass |
| Phase 10 Task 5 focused GREEN | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity -q` | MCP/REST parity test passes | `1 passed` | pass |
| Phase 10 Task 5 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `8 passed` | pass |
| Phase 10 Task 5 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `15 passed, 1 warning` | pass |
| Phase 10 Task 5 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 6 focused RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces tests/test_mcp_contract.py::test_mcp_results_do_not_leak_redacted_secret -q` before implementation | Audit test passes; privacy test fails on raw secret in MCP error result | `1 failed, 1 passed` with `missing-sk-mcp-secret` in error details | pass |
| Phase 10 Task 6 focused GREEN | Same focused command after redacting REST error envelopes | Focused audit/privacy tests pass | `2 passed` | pass |
| Phase 10 Task 6 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `10 passed` | pass |
| Phase 10 Task 6 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `17 passed, 1 warning` | pass |
| Phase 10 Task 6 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 7 focused RED | `.venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_cli_accepts_base_url_token_and_timeout tests/test_mcp_contract.py::test_mcp_cli_uses_environment_defaults tests/test_mcp_contract.py::test_mcp_cli_runs_stdio_server_without_starting_daemon -q` before implementation | Fails because CLI MCP parser/runner do not exist | `3 failed` with missing `build_parser` and missing `create_mcp_server` attribute | pass |
| Phase 10 Task 7 focused GREEN | Same focused command after implementation | CLI parser and runner tests pass | `3 passed` | pass |
| Phase 10 Task 7 MCP help smoke | `.venv/bin/python -m mneme_service.cli mcp --help` | Prints `usage: mneme mcp ...` and exits 0 | Help output displayed `--base-url`, `--token`, and `--timeout` | pass |
| Phase 10 Task 7 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `13 passed` | pass |
| Phase 10 Task 7 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `20 passed, 1 warning` | pass |
| Phase 10 Task 7 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 8 focused RED | `.venv/bin/python -m pytest tests/test_contract.py::test_auth_health_capabilities_and_session_idempotency tests/test_mcp_contract.py::test_codex_mcp_usage_docs_are_tools_only_and_config_is_valid -q` before implementation | Fails on missing MCP capability advertisement and missing Codex doc | `2 failed, 1 warning` | pass |
| Phase 10 Task 8 focused GREEN | Same focused command after implementation | Capabilities and Codex docs tests pass | `2 passed, 1 warning` | pass |
| Phase 10 Task 8 MCP contract tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass | `14 passed` | pass |
| Phase 10 Task 8 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `21 passed, 1 warning` | pass |
| Phase 10 Task 8 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 8 config JSON check | `.venv/bin/python -m json.tool adapters/codex/mcp_server.example.json` | JSON is valid | Pretty-printed valid JSON | pass |
| Phase 10 Task 8 doc overclaim scan | `rg -n "will automatically replace|automatically replaces|automatic prompt replacement" adapters/codex/MNEME_CODEX_MCP_USAGE.md` | No overclaim matches | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 10 Task 9 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `21 passed, 1 warning` | pass |
| Phase 10 Task 9 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 10 Task 9 daemon smoke first attempt | `.venv/bin/python -m mneme_service.cli serve --db /private/tmp/mneme-mcp-plan-smoke.db --insecure-dev --port 8766` | Start local test daemon | Failed with sandbox `operation not permitted` on bind | expected sandbox block |
| Phase 10 Task 9 daemon smoke escalated | Same serve command with approved escalation | Daemon runs on `127.0.0.1:8766` | Uvicorn running; stopped cleanly after smoke | pass |
| Phase 10 Task 9 health smoke | `curl -sS http://127.0.0.1:8766/v1/health` | Health returns `status=OK` | Returned `{"status":"OK","service":"mneme-context-service",...}` | pass |
| Phase 10 Task 9 MCP smoke first attempt | Python SDK helper smoke against `http://127.0.0.1:8766` | Seed session, list tools, call `context_search` | Failed with sandbox `httpx.ConnectError` to localhost | expected sandbox block |
| Phase 10 Task 9 MCP smoke escalated | Same Python SDK helper smoke with approved escalation | Seven tools visible; `context_search` returns expected event id | `ok=true`, tools list included all seven v0 tools, trace id returned | pass |
| Phase 11 Codex ingest focused RED | `.venv/bin/python -m pytest tests/test_codex_ingest.py -q` before implementation | Fails because Codex ingest module and CLI command are missing | `4 failed` with `ModuleNotFoundError` and invalid `codex-ingest` command | pass |
| Phase 11 Codex ingest docs RED | `.venv/bin/python -m pytest tests/test_codex_ingest.py::test_codex_ingest_usage_docs_are_offline_reference_only -q` before docs | Fails because usage doc is missing | `1 failed` with `FileNotFoundError` | pass |
| Phase 11 Codex ingest focused GREEN | `.venv/bin/python -m pytest tests/test_codex_ingest.py -q` | Codex ingest tests pass | `5 passed` | pass |
| Phase 11 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `26 passed, 1 warning` | pass |
| Phase 11 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 11 CLI help smoke | `.venv/bin/python -m mneme_service.cli codex-ingest --help` | Help prints import options and exits 0 | Displayed `--input`, `--base-url`, `--token`, and `--timeout` | pass |
| Phase 11 example transcript JSON check | `.venv/bin/python -m json.tool adapters/codex/transcript.example.json` | JSON is valid | Pretty-printed valid JSON | pass |
| Phase 11 unchecked checkbox scan | `rg -n "\\[ \\]" task_plan.md MILESTONE_3_CODEX_INGESTION_PLAN.md` | No unchecked Phase 11/Milestone 3 boxes | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 11 conflict marker scan | `rg -n "<<<<<<<\|>>>>>>>\|=======" ...changed files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 11 final post-planning pytest | `.venv/bin/python -m pytest -q` | All tests pass after planning updates | `26 passed, 1 warning` | pass |
| Phase 11 final post-planning compile | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 after planning updates | Passed | pass |
| Phase 12 health check | `curl -sS http://127.0.0.1:8767/v1/health` | Health returns `status=OK` | Returned `{"status":"OK","service":"mneme-context-service",...}` | pass |
| Phase 12 transcript import | `.venv/bin/python -m mneme_service.cli codex-ingest --input adapters/codex/transcript.example.json --base-url http://127.0.0.1:8767 --token <mneme-auth-token>` with escalation | Imports example transcript | `accepted=3`, `duplicates=0`, stored expected event ids | pass |
| Phase 12 REST search | `curl -sS ... /v1/tools/context_search` | Finds imported pytest event | Found `codex-codex-example-session-turn-1-0003` | pass |
| Phase 12 REST fetch | `curl -sS ... /v1/tools/fetch_event` | Fetches imported pytest event | Returned content `focused pytest passed` and parent neighbor | pass |
| Phase 12 Codex config TOML parse | `.venv/bin/python -c 'import tomllib, pathlib; ...'` | Config parses as TOML | Printed `toml ok` | pass |
| Phase 12 MCP smoke | `.venv/bin/python -c '... create_mcp_server ... context_search ...'` with escalation | Seven tools visible; search returns expected event | Listed all seven tools and returned `ok=true` with `codex-codex-example-session-turn-1-0003` | pass |
| Phase 12 dogfood port scan | `rg -n "8765" adapters/codex/CODEX_DOGFOOD_RESTART_SETUP.md adapters/codex/MNEME_CODEX_NEW_SESSION_PROMPT.md adapters/codex/codex_mcp_dogfood.example.json` | No stale dogfood port references | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 12 dogfood JSON check | `.venv/bin/python -m json.tool adapters/codex/codex_mcp_dogfood.example.json` | JSON is valid | Pretty-printed valid JSON | pass |
| Phase 12 final pytest | `.venv/bin/python -m pytest -q` | All tests pass | `26 passed, 1 warning` | pass |
| Phase 12 final compile | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 12 Codex-session MCP search | `mcp__mneme.context_search(session_id="codex-example-session", query="focused pytest passed", scope="SESSION", top_k=5, include_content=true)` | Find imported event `codex-codex-example-session-turn-1-0003` | `ok=true`, returned expected event with `trace_id=trace-a5c3dba9990842579275c4eed2b696dc` | pass |
| Phase 12 Codex-session MCP fetch | `mcp__mneme.fetch_event(session_id="codex-example-session", event_id="codex-codex-example-session-turn-1-0003", full=true, include_neighbors=false)` | Fetch imported pytest event content | `ok=true`, content text `focused pytest passed`, `trace_id=trace-5aef6e1710c84ffe8044deae45e08272` | pass |
| Phase 13 roadmap conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 roadmap trailing whitespace scan | `rg -n "[[:blank:]]$" task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13A parity audit conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" task_plan.md findings.md progress.md HERMES_MNEME_COMPARISON.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13A parity audit trailing whitespace scan | `rg -n "[[:blank:]]$" task_plan.md findings.md progress.md HERMES_MNEME_COMPARISON.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 direction-plan conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" task_plan.md findings.md progress.md MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md HERMES_MNEME_COMPARISON.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 direction-plan trailing whitespace scan | `rg -n "[[:blank:]]$" task_plan.md findings.md progress.md MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md HERMES_MNEME_COMPARISON.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 drift-scope conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" task_plan.md findings.md progress.md MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md HERMES_MNEME_COMPARISON.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 drift-scope trailing whitespace scan | `rg -n "[[:blank:]]$" task_plan.md findings.md progress.md MILESTONE_5_HERMES_MNEME_PARITY_RECOVERY_PLAN.md HERMES_MNEME_COMPARISON.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 1 config RED | `.venv/bin/python -m pytest tests/test_config.py -q` before implementation | Fails because provider config API is missing | Failed with `ImportError: cannot import name 'ProviderSettings'` | pass |
| Phase 14 Task 1 config GREEN | `.venv/bin/python -m pytest tests/test_config.py -q` | Focused provider config tests pass | `4 passed, 1 warning` | pass |
| Phase 14 Task 1 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `30 passed, 1 warning` | pass |
| Phase 14 Task 1 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 1 serve help smoke | `.venv/bin/python -m mneme_service.cli serve --help` | Serve help lists config/provider flags and exits 0 | Help output included `--config`, embedding, reranker, and LLM flags | pass |
| Phase 14 Task 1 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 1 trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 1 example secret scan | `rg -n "sk-\|real-token" mneme.example.toml` | No real-looking secrets in example config | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 autonomous prompt conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 autonomous prompt trailing whitespace scan | `rg -n "[[:blank:]]$" NEXT_SESSION_PROMPT_PHASE_14_AUTONOMOUS.md task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 2 baseline full pytest | `.venv/bin/python -m pytest -q` before Task 2 implementation | Existing suite passes before RED tests | `30 passed, 1 warning` | pass |
| Phase 14 Task 2 RED | `.venv/bin/python -m pytest tests/test_embeddings.py -q` before implementation | Fails because embedding module/provider/index are missing | Failed with `ModuleNotFoundError: No module named 'mneme_service.embeddings'` | pass |
| Phase 14 Task 2 focused GREEN | `.venv/bin/python -m pytest tests/test_embeddings.py -q` | Embedding tests pass | `5 passed, 1 warning` | pass |
| Phase 14 Task 2 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `35 passed, 1 warning` | pass |
| Phase 14 Task 2 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 2 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/embeddings.py tests/test_embeddings.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 2 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/embeddings.py tests/test_embeddings.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 2 sqlite-vec check | `.venv/bin/python -c "import importlib.util; print(importlib.util.find_spec('sqlite_vec'))"` | Determine whether optional sqlite-vec path can be exercised locally | Printed `None`; Python cosine fallback is the verified path | pass |
| Phase 14 Task 2 post-planning full pytest | `.venv/bin/python -m pytest -q` | All tests pass after planning updates | `35 passed, 1 warning` | pass |
| Phase 14 Task 2 post-planning compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 after planning updates | Passed | pass |
| Phase 14 Task 2 post-planning conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 2 post-planning trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 3 RED | `.venv/bin/python -m pytest tests/test_retrieval.py -q` before implementation | Fails on keyword-only retrieval and missing degraded trace metadata | `3 failed, 1 warning`: no semantic result, missing `retrieval` trace key, missing `EMBEDDINGS_UNAVAILABLE` warning | pass |
| Phase 14 Task 3 focused GREEN | `.venv/bin/python -m pytest tests/test_retrieval.py -q` | Hybrid retrieval tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 3 MCP parity tests | `.venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP/REST parity remains intact | `14 passed` | pass |
| Phase 14 Task 3 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `38 passed, 1 warning` | pass |
| Phase 14 Task 3 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 3 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/app.py mneme_service/embeddings.py tests/test_retrieval.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 3 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/embeddings.py tests/test_retrieval.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 3 post-planning full pytest | `.venv/bin/python -m pytest -q` | All tests pass after planning updates | `38 passed, 1 warning` | pass |
| Phase 14 Task 3 post-planning compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 after planning updates | Passed | pass |
| Phase 14 Task 3 post-planning conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 3 post-planning trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 4 RED | `.venv/bin/python -m pytest tests/test_state.py -q` before implementation | Fails because state/history REST/MCP tools do not exist | `3 failed, 1 warning`: REST tools returned 404 and MCP discovery lacked new tool names | pass |
| Phase 14 Task 4 focused GREEN | `.venv/bin/python -m pytest tests/test_state.py -q` | State/history tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 4 state plus MCP tests | `.venv/bin/python -m pytest tests/test_state.py tests/test_mcp_contract.py -q` | State tools and MCP contract pass together | `17 passed, 1 warning` | pass |
| Phase 14 Task 4 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `41 passed, 1 warning` | pass |
| Phase 14 Task 4 compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 4 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/state.py mneme_service/tool_names.py mneme_service/mcp_server.py tests/test_state.py tests/test_mcp_contract.py API_MCP_CONTRACT_V0.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 4 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/state.py mneme_service/tool_names.py mneme_service/mcp_server.py tests/test_state.py tests/test_mcp_contract.py API_MCP_CONTRACT_V0.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice A RED | `.venv/bin/python -m pytest tests/test_classifier.py tests/test_segments.py -q` before implementation | Fails because classifier/segmenter wiring is missing | First failed with `ModuleNotFoundError: No module named 'mneme_service.classifier'`; after partial file creation failed with empty segment lists | pass |
| Phase 14 Task 5 Slice A focused GREEN | `.venv/bin/python -m pytest tests/test_classifier.py tests/test_segments.py -q` | Classifier and explicit-switch segment tests pass | `5 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice A contract spot-check | `.venv/bin/python -m pytest tests/test_contract.py::test_memory_tool_filters_limits_and_segment_page_size tests/test_mcp_contract.py::test_mcp_rest_memory_tool_parity -q` | Existing segment page-size and MCP/REST parity behavior still pass | `2 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice A compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice A full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `46 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice A conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/classifier.py mneme_service/segments.py tests/test_classifier.py tests/test_segments.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice A trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/classifier.py mneme_service/segments.py tests/test_classifier.py tests/test_segments.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice A post-planning full pytest | `.venv/bin/python -m pytest -q` | All tests pass after planning updates | `46 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice A post-planning compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 after planning updates | Passed | pass |
| Phase 14 Task 5 Slice A post-planning conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice A post-planning trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice B classifier RED | `.venv/bin/python -m pytest tests/test_classifier.py::test_classifier_uses_high_embedding_drift_for_new_task -q` before implementation | Fails because `NEW_TASK` classifier support is missing | Failed with `ImportError: cannot import name 'INTENT_NEW_TASK'` | pass |
| Phase 14 Task 5 Slice B segment RED | `.venv/bin/python -m pytest tests/test_segments.py::test_high_embedding_drift_rolls_over_active_segment -q` before implementation | Fails because high embedding drift does not cut the active segment | Failed with one `ACTIVE` segment instead of `CLOSED`, `ACTIVE` | pass |
| Phase 14 Task 5 Slice B classifier GREEN | `.venv/bin/python -m pytest tests/test_classifier.py -q` | Classifier tests pass | `4 passed` | pass |
| Phase 14 Task 5 Slice B focused GREEN | `.venv/bin/python -m pytest tests/test_segments.py -q` | Explicit switch, continuation, and embedding drift segment tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice B embedding/retrieval spot-check | `.venv/bin/python -m pytest tests/test_embeddings.py tests/test_retrieval.py -q` | Embedding and hybrid retrieval tests still pass | `8 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice B compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice B full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `48 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice B conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/classifier.py mneme_service/segments.py mneme_service/embeddings.py tests/test_classifier.py tests/test_segments.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice B trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/classifier.py mneme_service/segments.py mneme_service/embeddings.py tests/test_classifier.py tests/test_segments.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice B post-planning full pytest | `.venv/bin/python -m pytest -q` | All tests pass after planning updates | `48 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice B post-planning compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 after planning updates | Passed | pass |
| Phase 14 Task 5 Slice B post-planning conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice B post-planning trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice C RED | `.venv/bin/python -m pytest tests/test_segments.py -q` before implementation | Fails because segment rollover traces are missing | `2 failed, 1 passed, 1 warning`: export contained no `SEGMENT_DRIFT` traces for rollover events | pass |
| Phase 14 Task 5 Slice C focused GREEN | `.venv/bin/python -m pytest tests/test_segments.py -q` | Segment rollover trace tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice C focused regression | `.venv/bin/python -m pytest tests/test_segments.py tests/test_contract.py tests/test_mcp_contract.py -q` | Segment, REST contract, and MCP contract tests pass together | `24 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice C full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `48 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice C compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice C conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice C trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice D RED | `.venv/bin/python -m pytest tests/test_session_drift.py -q` before implementation | Fails because `/v1/sessions/start` lacks `session_state` | `3 failed, 1 warning` with `KeyError: 'session_state'` | pass |
| Phase 14 Task 5 Slice D focused GREEN | `.venv/bin/python -m pytest tests/test_session_drift.py -q` | Fresh/resume session-start classification tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice D lifecycle spot-check | `.venv/bin/python -m pytest tests/test_session_drift.py tests/test_contract.py::test_auth_health_capabilities_and_session_idempotency -q` | New session-state response remains compatible with start/capabilities idempotency | `4 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice D focused regression | `.venv/bin/python -m pytest tests/test_session_drift.py tests/test_segments.py tests/test_contract.py tests/test_mcp_contract.py -q` | Session drift, segment, REST contract, and MCP contract tests pass together | `27 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice D full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `51 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice D compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice D conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice D trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice E RED | `.venv/bin/python -m pytest tests/test_session_lineage.py -q` before implementation | Fails because lineage export/carry-over retrieval are missing | `1 failed, 1 passed, 1 warning`: export lacked `session_lineage` | pass |
| Phase 14 Task 5 Slice E focused GREEN | `.venv/bin/python -m pytest tests/test_session_lineage.py -q` | Lineage carry-over tests pass | `2 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice E focused regression | `.venv/bin/python -m pytest tests/test_session_lineage.py tests/test_session_drift.py tests/test_retrieval.py tests/test_embeddings.py tests/test_contract.py tests/test_mcp_contract.py -q` | Lineage, session drift, retrieval, embeddings, REST contract, and MCP contract tests pass together | `34 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice E full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `53 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice E compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice E conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice E trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice F RED | `.venv/bin/python -m pytest tests/test_resume_fill.py -q` before implementation | Fails because first-turn resume context fill is missing | `2 failed, 1 warning`: unmatched under-budget prepare returned `changed=false`, and lineage child did not require fill | pass |
| Phase 14 Task 5 Slice F focused GREEN | `.venv/bin/python -m pytest tests/test_resume_fill.py -q` | Resume fill one-shot tests pass | `2 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice F focused regression | `.venv/bin/python -m pytest tests/test_resume_fill.py tests/test_session_lineage.py tests/test_session_drift.py tests/test_segments.py tests/test_classifier.py tests/test_contract.py tests/test_mcp_contract.py -q` | Task 5, context prepare, REST contract, and MCP contract tests pass together | `35 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice F full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `55 passed, 1 warning` | pass |
| Phase 14 Task 5 Slice F compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 5 Slice F conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 5 Slice F trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 6 Slice A RED | `.venv/bin/python -m pytest tests/test_graph.py -q` before implementation | Fails because typed graph edges are missing | `2 failed, 1 warning`: export lacked `event_graph_edges`, and expansion used generic edge labels | pass |
| Phase 14 Task 6 Slice A focused GREEN | `.venv/bin/python -m pytest tests/test_graph.py -q` | Typed graph export and expansion tests pass | `2 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice A focused regression | `.venv/bin/python -m pytest tests/test_graph.py tests/test_contract.py tests/test_mcp_contract.py tests/test_retrieval.py -q` | Graph, REST contract, MCP contract, and retrieval tests pass together | `26 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice A full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `57 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice A compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 6 Slice A conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 6 Slice A trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 6 Slice B RED | `.venv/bin/python -m pytest tests/test_graph.py::test_context_search_includes_graph_dependencies_for_keyword_hit -q` before implementation | Fails because graph dependencies are not included in retrieval | Failed with only `event-output` returned | pass |
| Phase 14 Task 6 Slice B focused GREEN | `.venv/bin/python -m pytest tests/test_graph.py::test_context_search_includes_graph_dependencies_for_keyword_hit -q` | Dependency-aware retrieval scoring test passes | `1 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice B focused regression | `.venv/bin/python -m pytest tests/test_graph.py tests/test_retrieval.py tests/test_contract.py tests/test_mcp_contract.py -q` | Graph, retrieval, REST contract, and MCP contract tests pass together | `27 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice B full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `58 passed, 1 warning` | pass |
| Phase 14 Task 6 Slice B compile check | `.venv/bin/python -m py_compile mneme_service/*.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 6 Slice B conflict marker scan | `rg -n "^[<=>]{7}" ...changed files plus planning files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 6 Slice B trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files plus planning files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice A RED | `.venv/bin/python -m pytest tests/test_context_assembly.py -q` before implementation | Fails because execution-state prepare assembly is missing | Failed with `changed=false` for an execution-state-only prepare | pass |
| Phase 14 Task 7 Slice A focused GREEN | `.venv/bin/python -m pytest tests/test_context_assembly.py -q` | Execution-state context assembly test passes | `1 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice A focused regression | `.venv/bin/python -m pytest tests/test_context_assembly.py tests/test_contract.py tests/test_resume_fill.py tests/test_state.py -q` | Context assembly, contract, resume fill, and state tests pass together | `13 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice A full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `59 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice A compile check | `python3 -m py_compile mneme_service/app.py tests/test_context_assembly.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 7 Slice A conflict marker scan | `rg -n "<<<<<<<|=======|>>>>>>>" mneme_service/app.py tests/test_context_assembly.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice A trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py tests/test_context_assembly.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice B RED | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_protects_recent_tail_when_request_exceeds_budget -q` before implementation | Fails because protected-tail packing is missing | Failed by inserting an empty `mneme_generated` assistant message | pass |
| Phase 14 Task 7 Slice B focused GREEN | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_protects_recent_tail_when_request_exceeds_budget -q` | Protected-tail test passes | `1 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice B focused regression | `.venv/bin/python -m pytest tests/test_context_assembly.py tests/test_contract.py tests/test_resume_fill.py tests/test_state.py -q` | Context assembly, contract, resume fill, and state tests pass together | `14 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice B full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `60 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice B compile check | `python3 -m py_compile mneme_service/app.py tests/test_context_assembly.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 7 Slice B conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" mneme_service/app.py tests/test_context_assembly.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice B trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py tests/test_context_assembly.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice C RED | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_packs_retrieved_context_and_traces_dropped_events -q` before implementation | Fails because retrieved-context budget packing is missing | Failed by including `event-long` in generated evidence | pass |
| Phase 14 Task 7 Slice C focused GREEN | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_packs_retrieved_context_and_traces_dropped_events -q` | Retrieved-context packing test passes | `1 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice C focused regression | `.venv/bin/python -m pytest tests/test_context_assembly.py tests/test_contract.py tests/test_resume_fill.py tests/test_state.py tests/test_retrieval.py tests/test_graph.py -q` | Context assembly, contract, resume fill, state, retrieval, and graph tests pass together | `21 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice C full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `61 passed, 1 warning` | pass |
| Phase 14 Task 7 Slice C compile check | `python3 -m py_compile mneme_service/app.py tests/test_context_assembly.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 7 Slice C conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" mneme_service/app.py tests/test_context_assembly.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice C trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py tests/test_context_assembly.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 Slice D RED | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_resolves_collision_by_dropping_retrieved_context -q` before implementation | Fails because cross-block collision handling is missing | Failed by inserting the retrieved evidence block | pass |
| Phase 14 Task 7 Slice D focused GREEN | `.venv/bin/python -m pytest tests/test_context_assembly.py::test_context_prepare_resolves_collision_by_dropping_retrieved_context -q` | Collision-resolution test passes | `1 passed, 1 warning` | pass |
| Phase 14 Task 7 focused assembly suite | `.venv/bin/python -m pytest tests/test_context_assembly.py -q` | Task 7 context assembly tests pass | `4 passed, 1 warning` | pass |
| Phase 14 Task 7 focused regression | `.venv/bin/python -m pytest tests/test_context_assembly.py tests/test_contract.py tests/test_resume_fill.py tests/test_state.py tests/test_retrieval.py tests/test_graph.py tests/test_mcp_contract.py -q` | Context assembly, contract, resume fill, state, retrieval, graph, and MCP tests pass together | `36 passed, 1 warning` | pass |
| Phase 14 Task 7 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `62 passed, 1 warning` | pass |
| Phase 14 Task 7 compile check | `python3 -m py_compile mneme_service/app.py tests/test_context_assembly.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 7 conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" mneme_service/app.py tests/test_context_assembly.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 7 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py tests/test_context_assembly.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 8 RED | `.venv/bin/python -m pytest tests/test_reranker.py -q` before implementation | Fails because reranker module/integration is missing | Failed during collection with `ModuleNotFoundError: No module named 'mneme_service.reranker'` | pass |
| Phase 14 Task 8 focused GREEN | `.venv/bin/python -m pytest tests/test_reranker.py -q` | Reranker parsing, integration, fallback, and metrics tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 8 focused regression | `.venv/bin/python -m pytest tests/test_reranker.py tests/test_retrieval.py tests/test_config.py tests/test_contract.py tests/test_mcp_contract.py -q` | Reranker, retrieval, provider config, REST contract, and MCP tests pass together | `31 passed, 1 warning` | pass |
| Phase 14 Task 8 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `65 passed, 1 warning` | pass |
| Phase 14 Task 8 compile check | `python3 -m py_compile mneme_service/app.py mneme_service/storage.py mneme_service/reranker.py tests/test_reranker.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 8 conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/reranker.py tests/test_reranker.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 8 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/reranker.py tests/test_reranker.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 9 RED | `.venv/bin/python -m pytest tests/test_enrichment.py -q` before implementation | Fails because enrichment module/integration is missing | Failed during collection with `ModuleNotFoundError: No module named 'mneme_service.enrichment'` | pass |
| Phase 14 Task 9 focused GREEN | `.venv/bin/python -m pytest tests/test_enrichment.py -q` | Enrichment provider, state application, fallback, and metrics tests pass | `3 passed, 1 warning` | pass |
| Phase 14 Task 9 focused regression | `.venv/bin/python -m pytest tests/test_enrichment.py tests/test_state.py tests/test_config.py tests/test_contract.py tests/test_mcp_contract.py tests/test_reranker.py -q` | Enrichment, state, provider config, REST contract, MCP, and reranker tests pass together | `34 passed, 1 warning` | pass |
| Phase 14 Task 9 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `68 passed, 1 warning` | pass |
| Phase 14 Task 9 compile check | `python3 -m py_compile mneme_service/app.py mneme_service/storage.py mneme_service/enrichment.py tests/test_enrichment.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 9 conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" mneme_service/app.py mneme_service/storage.py mneme_service/enrichment.py tests/test_enrichment.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 9 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/app.py mneme_service/storage.py mneme_service/enrichment.py tests/test_enrichment.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 10 acceptance initial | `.venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Acceptance suite passes | Initially `1 failed, 4 passed`: outage test included reranker fallback and export included expected `MEMORY_READ` audit event | pass |
| Phase 14 Task 10 focused GREEN | `.venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance suite passes | `5 passed, 1 warning` | pass |
| Phase 14 Task 10 focused regression | `.venv/bin/python -m pytest tests/test_parity_recovery.py tests/test_embeddings.py tests/test_retrieval.py tests/test_state.py tests/test_segments.py tests/test_session_drift.py tests/test_session_lineage.py tests/test_resume_fill.py tests/test_graph.py tests/test_context_assembly.py tests/test_reranker.py tests/test_enrichment.py tests/test_mcp_contract.py -q` | Phase 14 and MCP-adjacent tests pass together | `53 passed, 1 warning` | pass |
| Phase 14 Task 10 full pytest | `.venv/bin/python -m pytest -q` | All tests pass | `73 passed, 1 warning` | pass |
| Phase 14 Task 10 compile check | `python3 -m py_compile tests/test_parity_recovery.py` | Exit code 0 | Passed | pass |
| Phase 14 Task 10 conflict marker scan | `rg -n "^(<<<<<<<|=======|>>>>>>>)" tests/test_parity_recovery.py` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14 Task 10 trailing whitespace scan | `rg -n "[[:blank:]]$" tests/test_parity_recovery.py` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 15 editable install | `.venv/bin/python -m pip install -e '.[test]'` | Package metadata supports editable install | First sandbox attempt failed on DNS/build dependency fetch; approved escalated rerun succeeded | pass |
| Phase 15 full pytest | `.venv/bin/python -m pytest -q` | All tests pass after publication docs/package/license prep | `73 passed, 1 warning` | pass |
| Phase 15 parity acceptance | `.venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Acceptance suite passes after publication prep | `5 passed, 1 warning` | pass |
| Phase 15 compileall | `.venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 15 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" README.md docs .github/workflows/ci.yml pyproject.toml .gitignore task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 15 trailing whitespace scan | `rg -n "[[:blank:]]$" README.md docs .github/workflows/ci.yml pyproject.toml .gitignore task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 15 secret scan | `rg -n "sk-\|real-token\|AKIA\|AIza\|ghp_\|MNEME_.*API_KEY=.*[A-Za-z0-9]\|api_key\\s*=\\s*['\\\"][^<'\\\"]" README.md docs adapters/codex mneme.example.toml .github/workflows/ci.yml pyproject.toml` | No real secrets | Matched only `<secret>` placeholders in `docs/PROVIDER_CONFIGURATION.md` | pass |
| Phase 15 overclaim scan | `rg -n "automatic prompt replacement\|automatically replace\|magic universal\|invisible context" README.md docs adapters/codex` | No overclaims | Matches are negative/honesty statements saying MCP does not automatically replace host prompt context | pass |
| Phase 15 default provider config check | `rg -n "available\\s*=\\s*true\|enabled\\s*=\\s*true\|api_key" mneme.example.toml docs/PROVIDER_CONFIGURATION.md` plus inspection of `mneme.example.toml` | Defaults disabled; docs examples may show opt-in enablement | `mneme.example.toml` has all providers `enabled = false`; only provider guide opt-in examples use `enabled = true` | pass |
| Phase 15 license metadata check | `.venv/bin/python -m pip show mneme-context-service` | Package metadata includes Apache-2.0 license and Ivan Konstantinov author | Printed `Author: Ivan Konstantinov` and `License: Apache-2.0` | pass |
| Phase 14B Task 1 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 1 trailing whitespace scan | `rg -n "[[:blank:]]$" MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 2 RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py -q` before implementation | Fails because benchmark module/CLI do not exist | Failed with `ModuleNotFoundError: No module named 'mneme_service.benchmarks'` and invalid CLI choice `benchmark` | pass |
| Phase 14B Task 2 focused GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py -q` | Benchmark tests pass | `2 passed, 1 warning` | pass |
| Phase 14B Task 2 CLI smoke | `env TMPDIR=/private/tmp .venv/bin/python -m mneme_service.cli benchmark --events 6 --db /private/tmp/mneme-benchmark-smoke.db` | Prints JSON benchmark report | Returned `schema_version=mneme.benchmark_report.v0`, `accepted=6`, `message_count=3`, and embedding cost counters | pass |
| Phase 14B Task 2 full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `75 passed, 1 warning` | pass |
| Phase 14B Task 2 focused parity regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py tests/test_benchmarks.py -q` | Parity and benchmark tests pass together | `7 passed, 1 warning` | pass |
| Phase 14B Task 2 compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 14B Task 2 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/benchmarks.py mneme_service/cli.py tests/test_benchmarks.py MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 2 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/benchmarks.py mneme_service/cli.py tests/test_benchmarks.py MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 3 RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py -q` before implementation | Fails on provider robustness gaps | `2 failed, 13 passed`: malformed embedding payload did not open circuit and mixed-dimension embeddings were indexed | pass |
| Phase 14B Task 3 focused GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py -q` | Provider robustness tests pass | `15 passed, 1 warning` | pass |
| Phase 14B Task 3 parity/provider regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py -q` | Parity and provider tests pass together | `20 passed, 1 warning` | pass |
| Phase 14B Task 3 full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | First run hit external `sqlite3.OperationalError: disk I/O error` from low disk; after temp cleanup rerun passed `79 passed, 1 warning` | pass |
| Phase 14B Task 3 compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 14B Task 3 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service/embeddings.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py MILESTONE_5B_PARITY_HARDENING_PLAN.md task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 3 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service/embeddings.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py MILESTONE_5B_PARITY_HARDENING_PLAN.md task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B Task 4 sqlite_vec availability | `env TMPDIR=/private/tmp .venv/bin/python -c "import importlib.util; print(importlib.util.find_spec('sqlite_vec'))"` | Determine optional acceleration availability | Printed `None`; Python cosine fallback remains the verified path | pass |
| Phase 14B final full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `79 passed, 1 warning` | pass |
| Phase 14B final parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes | `5 passed, 1 warning` | pass |
| Phase 14B final provider/benchmark focus | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_benchmarks.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py -q` | Benchmark and provider robustness tests pass | `17 passed, 1 warning` | pass |
| Phase 14B final compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 14B final conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" README.md docs/BENCHMARKS.md docs/VECTOR_ACCELERATION.md mneme_service/benchmarks.py mneme_service/cli.py mneme_service/embeddings.py tests/test_benchmarks.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 14B final trailing whitespace scan | `rg -n "[[:blank:]]$" README.md docs/BENCHMARKS.md docs/VECTOR_ACCELERATION.md mneme_service/benchmarks.py mneme_service/cli.py mneme_service/embeddings.py tests/test_benchmarks.py tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py MILESTONE_5B_PARITY_HARDENING_PLAN.md HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 1 doc-contract RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_codex_mcp_usage_docs_are_tools_only_and_config_is_valid -q` before guide update | Fails because the Codex MCP usage guide lacks the long-session operating contract | Failed on missing `long-session operating contract` | pass |
| Phase 13 Task 1 doc-contract GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_codex_mcp_usage_docs_are_tools_only_and_config_is_valid -q` | Focused doc-contract test passes | `1 passed` | pass |
| Phase 13 Task 1 MCP focused suite | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests pass after guide/test updates | `14 passed, 1 warning` | pass |
| Phase 13 Task 1 full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `79 passed, 1 warning` | pass |
| Phase 13 Task 1 parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes | `5 passed, 1 warning` | pass |
| Phase 13 Task 1 compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 13 Task 1 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 1 trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 1 positive overclaim scan | `rg -n "will automatically replace\|automatically replaces\|rewrites every Codex request" adapters/codex README.md docs API_MCP_CONTRACT_V0.md MNEME_HOST_ADAPTER_CONTRACT_V0.md` | No positive automatic-prompt-replacement claims in user-facing docs | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 1 stale tool-count scan | `rg -n "seven v0\|all seven\|seven tools" adapters/codex MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md task_plan.md findings.md` | No stale active Codex tool-count wording | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 2 adapter RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q` before implementation | Fails because MCP instructions and adapter foundation files are missing | Failed during collection with missing `MNEME_MCP_INSTRUCTIONS` | pass |
| Phase 13 Task 2 adapter GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py -q` | Codex adapter foundation tests pass | `4 passed` | pass |
| Phase 13 Task 2 MCP focused suite | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q` | MCP contract tests still pass after adding instructions | `14 passed, 1 warning` | pass |
| Phase 13 Task 2 full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `83 passed, 1 warning` | pass |
| Phase 13 Task 2 parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes | `5 passed, 1 warning` | pass |
| Phase 13 Task 2 compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 13 Task 2 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service tests adapters/codex .agents README.md docs task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 2 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service tests adapters/codex .agents README.md docs task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 2 overclaim/secret scan | `rg` scans over adapter/docs/planning/code/test files | No new positive overclaim or real secret | Matches were historical scan strings, test fake secrets, and `<secret>` placeholders only | pass |
| Phase 13 Task 3 hook RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py -q` before implementation | Fails because hook module, CLI command, and hook usage doc are missing | `6 failed`: missing `mneme_service.codex_hooks`, invalid CLI command, missing docs | pass |
| Phase 13 Task 3 hook GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py -q` | Hook ingestion tests pass | `6 passed, 1 warning` | pass |
| Phase 13 Task 3 Codex/MCP regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py tests/test_codex_ingest.py tests/test_codex_adapter.py tests/test_mcp_contract.py -q` | Codex hook, transcript ingest, adapter foundation, and MCP tests pass together | `29 passed, 1 warning` | pass |
| Phase 13 Task 3 full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `89 passed, 1 warning` | pass |
| Phase 13 Task 3 parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes | `5 passed, 1 warning` | pass |
| Phase 13 Task 3 compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 13 Task 3 conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" mneme_service tests adapters/codex .agents README.md docs task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3 trailing whitespace scan | `rg -n "[[:blank:]]$" mneme_service tests adapters/codex .agents README.md docs task_plan.md findings.md progress.md MILESTONE_4_CODEX_MEMORY_DOGFOOD_AND_PROVIDER_CONFIG_PLAN.md` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3 overclaim/secret scan | `rg` scans over adapter/docs/planning/code/test files | No new positive overclaim or real secret | Matches were historical scan strings, test fake secrets, and `<secret>` placeholders only | pass |
| Phase 13 Task 3 CLI help smoke | `env TMPDIR=/private/tmp .venv/bin/python -m mneme_service.cli codex-hook-ingest --help` | Help prints hook options without benchmark/TestClient warning | Printed `--input`, `--event`, `--base-url`, `--token`, `--timeout`, and `--dry-run`; no TestClient warning | pass |
| Phase 13 Task 3 CLI/benchmark regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py tests/test_codex_ingest.py tests/test_mcp_contract.py tests/test_benchmarks.py -q` | CLI-adjacent tests pass after lazy benchmark import | `27 passed, 1 warning` | pass |
| Phase 13 Task 3 final full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass after CLI cleanup | `89 passed, 1 warning` | pass |
| Phase 13 Task 3 final parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes after CLI cleanup | `5 passed, 1 warning` | pass |
| Phase 13 Task 3 final compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 after CLI cleanup | Passed | pass |
| Phase 13 Task 3 final conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files...` | No conflict markers after CLI cleanup | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3 final trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files...` | No trailing whitespace after CLI cleanup | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3A hook capture/validate RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py -q` before implementation | Fails because capture/validate functions and CLI commands are missing | `5 failed, 5 passed` | pass |
| Phase 13 Task 3A hook capture/validate GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py -q` | Hook capture/validate tests pass | `11 passed` | pass |
| Phase 13 Task 3A Codex/MCP/benchmark regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_hooks.py tests/test_codex_ingest.py tests/test_codex_adapter.py tests/test_mcp_contract.py tests/test_benchmarks.py -q` | Codex hook, ingest, adapter, MCP, and benchmark tests pass together | `35 passed, 1 warning` | pass |
| Phase 13 Task 3A CLI help smoke | `env TMPDIR=/private/tmp .venv/bin/python -m mneme_service.cli codex-hook-capture --help` and `... codex-hook-validate --help` | Help prints capture/validate options | Both commands printed expected usage/options | pass |
| Phase 13 Task 3A full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass | `94 passed, 1 warning` | pass |
| Phase 13 Task 3A parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes | `5 passed, 1 warning` | pass |
| Phase 13 Task 3A compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 | Passed | pass |
| Phase 13 Task 3A JSON check | `env TMPDIR=/private/tmp .venv/bin/python -m json.tool adapters/codex/codex_hooks.capture.example.json` | Capture example JSON is valid | Pretty-printed valid JSON | pass |
| Phase 13 Task 3A conflict marker scan | `rg -n "^(<<<<<<<\|=======\|>>>>>>>)" ...changed files...` | No conflict markers | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3A trailing whitespace scan | `rg -n "[[:blank:]]$" ...changed files...` | No trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 Task 3A overclaim/secret scan | `rg` scans over adapter/docs/planning/code/test files | No new positive overclaim or real secret | Matches were historical scan strings, test fake secrets, and `<secret>` placeholders only | pass |
| Phase 13 multi-machine doc RED | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py::test_codex_docs_capture_multi_machine_install_constraints -q` before docs | Fails because multi-machine install constraints are missing | Failed on missing `multi-machine codex setup` | pass |
| Phase 13 multi-machine doc GREEN | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py::test_codex_docs_capture_multi_machine_install_constraints -q` | Multi-machine doc contract passes | `1 passed` | pass |
| Phase 13 multi-machine Codex doc regression | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_codex_adapter.py tests/test_codex_hooks.py tests/test_mcp_contract.py -q` | Codex adapter/hook/MCP docs remain consistent | `30 passed` | pass |
| Phase 13 multi-machine doc hygiene scan | `rg` conflict marker and trailing whitespace scans over changed docs/planning/test files | No conflict markers or trailing whitespace | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13 multi-machine final full pytest | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | All tests pass after multi-machine docs | `95 passed, 1 warning` | pass |
| Phase 13 multi-machine final parity acceptance | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q` | Parity acceptance passes after multi-machine docs | `5 passed, 1 warning` | pass |
| Phase 13 multi-machine final compileall | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit code 0 after multi-machine docs | Passed | pass |
| Phase 13 multi-machine final hygiene scan | `rg` conflict marker and trailing whitespace scans over changed docs/planning/test files | No conflict markers or trailing whitespace after final progress update | No matches; exit code 1 from `rg` means no matches | pass |
| Phase 13B session discovery RED | `.venv/bin/python -m pytest tests/test_contract.py::test_session_discovery_resolves_codex_session_without_guessing tests/test_mcp_contract.py::test_tool_names_match_contract tests/test_mcp_contract.py::test_mcp_tools_are_discoverable tests/test_mcp_contract.py::test_mcp_resolve_session_tool_proxies_rest_envelope -q` before implementation | Discovery endpoints/tools are missing and existing MCP tool list lacks `resolve_session`/`list_sessions` | `4 failed`: REST 404 for `/v1/tools/list_sessions`, unknown MCP tool `resolve_session`, and tool-name mismatch | pass |
| Phase 13B session discovery GREEN | Same focused pytest command after implementation | REST/MCP discovery tools and NOT_FOUND guidance pass | `4 passed, 1 warning` | pass |
| Phase 13B discovery regression | `.venv/bin/python -m pytest tests/test_contract.py::test_auth_health_capabilities_and_session_idempotency tests/test_contract.py::test_session_discovery_resolves_codex_session_without_guessing tests/test_mcp_contract.py tests/test_codex_hooks.py::test_codex_hook_normalizes_real_codex_desktop_fields -q` | Capabilities, MCP contract, docs checks, and real Codex hook normalization remain compatible | `18 passed, 1 warning` | pass |
| Phase 13B syntax check | `python3 -m py_compile mneme_service/app.py mneme_service/storage.py mneme_service/mcp_server.py mneme_service/tool_names.py` | Modified Python modules compile | Exit code 0 | pass |
| Phase 13B global DB inspection | `sqlite3 /Users/openclaw/.mneme-codex/.local/mneme.db ...` | Verify whether Codex events are written and find real project session ids | Found 7 sessions and 947 non-memory-read events; `_rlm-orchestrator` session id is `019edb86-1d22-78a3-b9e4-e6121c294056` | pass |
| Phase 13B live MCP read | `mcp__mneme.get_execution_state` and `mcp__mneme.context_search` with session `019edb86-1d22-78a3-b9e4-e6121c294056` | Verify current MCP can read memory when given the real internal session id | Both returned `ok=true`; search found RLM Orchestrator task/README evidence | pass |
| Phase 13B reviewer spec doc | Created `docs/MNEME_DEVELOPMENT_SPEC.md` and linked it from `README.md` | Provide one reviewer-facing specification/index tying requirements, architecture, contracts, security, tests, and traceability together | New doc added; README links to it under Specification | pass |
| Phase 13B API/MCP contract update | Updated `API_MCP_CONTRACT_V0.md` | Keep public contract aligned with new `resolve_session`/`list_sessions` tools and improved missing-session guidance | Contract now lists discovery endpoints/tools, schemas, Codex/MCP strategy, and `NOT_FOUND` discovery details | pass |
| Phase 13B status test determinism fix | Updated `codex_desktop_status(service_label=...)` and `tests/test_codex_adapter.py` | Avoid false failures when the developer machine already has a real `com.mneme.codex.plist` LaunchAgent installed | Status tests can use an isolated service label | pass |
| Phase 13B isolated status test | `.venv/bin/python -m pytest tests/test_codex_adapter.py::test_codex_status_reports_missing_daemon_without_token_leak -q` | Previously failing status test is deterministic with isolated service label | `1 passed` | pass |
| Phase 13B full pytest | `.venv/bin/python -m pytest -q` | Entire repository test suite passes after discovery/spec/status updates | `138 passed, 1 warning` | pass |
| Phase 13B final syntax check | `python3 -m py_compile mneme_service/app.py mneme_service/storage.py mneme_service/mcp_server.py mneme_service/tool_names.py mneme_service/codex_setup.py` | Modified Python modules compile | Exit code 0 | pass |
| Phase 13B git commit | `git commit -m "feat: harden Codex Mneme integration"` | Commit verified integrated state after tests | Created commit `088bbb5` on `main` | pass |
| Phase 13B git push attempt | `git push origin main` | Push commit to current GitHub remote | Normal sandbox push failed DNS; escalated push was blocked by approval reviewer because `origin` is `johnnykor82/mneme-universal-context-service-internal-quarantine.git` on default branch and needs explicit user approval | blocked |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|---|---|---:|---|
| 2026-06-09 | System Python lacked pytest. | 1 | Created `.venv` and installed `.[test]`. |
| 2026-06-09 | FastAPI dependency alias produced auth-related 422s. | 1 | Replaced alias with explicit `Depends(require_auth)` route parameters. |
| 2026-06-09 | Importing `mneme_service.app` created `mneme.db` in project root. | 1 | Removed global app side effect and deleted generated DB artifact. |
| 2026-06-09 | Sandbox blocked localhost daemon bind. | 1 | Re-ran daemon smoke with approved escalation for local bind. |
| 2026-06-09 onward | Shell startup prints `(eval):1: command not found: +`. | 1 | Treat as environment noise; command exit codes and useful output remain valid. |
| 2026-06-12 | `pip install -e '.[test]'` failed under sandbox DNS/network restrictions while adding MCP SDK. | 1 | Re-ran the same command with approved escalation; install succeeded with `mcp==1.27.2`. |
| 2026-06-12 | `git diff`, `git diff --check`, and `git status` failed because the workspace path is not a git repository in this environment. | 1 | Used targeted file inspection and focused/full tests instead. |
| 2026-06-12 | MCP error result leaked `sk-mcp-secret` from missing `event_id` details. | 1 | Redacted `MnemeError` response content before returning it from the REST exception handler. |
| 2026-06-12 | Task 9 daemon smoke bind failed under sandbox with `operation not permitted`. | 1 | Re-ran the same local daemon smoke with approved escalation. |
| 2026-06-12 | Task 9 Python MCP smoke failed to connect to the local daemon under sandbox. | 1 | Re-ran the same SDK helper smoke with approved escalation; MCP search passed against the real daemon. |
| 2026-06-12 | Port `8765` returned `404` for `/v1/health`. | 1 | Treated port as occupied by another local service and used `8767`. |
| 2026-06-12 | Background `nohup` daemon launch did not keep Mneme reachable. | 1 | Installed and loaded a LaunchAgent from `.local/com.openclaw.mneme-dogfood.plist`. |
| 2026-06-12 | Python/httpx import could not connect to local daemon from sandbox. | 1 | Re-ran the same import with approved escalation; import succeeded. |
| 2026-06-12 | System `python3` lacked `tomllib` while checking Codex config. | 1 | Used project `.venv/bin/python` 3.12 for TOML parsing. |
| 2026-06-12 | Initial `tests/test_embeddings.py` patch landed one directory above the project root. | 1 | Deleted the accidental parent-level file and recreated the test under `_mneme-universal-context-service/tests/`. |
| 2026-06-12 | `security-guidance` referenced ASVS files that were absent from the installed skill bundle. | 1 | Recorded the local skill issue and applied Mneme's concrete contract requirements directly. |
| 2026-06-12 | `sqlite_vec` is not installed in the project `.venv`. | 1 | Verified Python cosine fallback for Task 2; left vector acceleration unexercised in this environment. |
| 2026-06-12 | Phase 15 editable install failed under sandbox DNS while resolving build dependencies for `setuptools>=68`. | 1 | Re-ran `.venv/bin/python -m pip install -e '.[test]'` with approved escalation; editable install succeeded. |
| 2026-06-14 | Pytest could not create temp files because the data volume had only about 116 MiB available and Python found no usable temp directory. | 1 | Inspected disk usage, removed old temporary pytest/electron/log artifacts with approved escalation, then reran tests with `TMPDIR=/private/tmp`. |
| 2026-06-20 | Global `mneme-codex doctor/status` wrapper returned exit code 127 in the sandbox. | 1 | Inspected global config, wrapper scripts, logs, and SQLite database directly; confirmed daemon config and stored sessions without printing secrets. |
| 2026-06-20 | `git push origin main` was rejected by approvals reviewer. | 1 | Stop and ask for explicit user approval for pushing commit `088bbb5` to `git@github.com:johnnykor82/mneme-universal-context-service-internal-quarantine.git`; do not work around the policy. |

## 5-Question Reboot Check

| Question | Answer |
|---|---|
| Where am I? | Phase 13B Codex/MCP session discovery hotfix is complete in the working tree: REST/MCP now expose `resolve_session` and `list_sessions`, and docs/skill tell agents not to guess `session_id`. |
| Where am I going? | Next: finish full verification, review the diff, commit, and push the update to GitHub; then reinstall/restart the global Codex MCP environment so the running tools include discovery. |
| What is the goal? | Create a vendor-neutral Mneme context service any agent runtime can integrate through a clear REST/MCP contract. |
| What have I learned? | See `findings.md` for requirements, technical decisions, issues, resources, and open questions. |
| What have I done? | Completed concept, architecture diagram, implementation path, API/MCP contract, Host Adapter Contract v0, Milestone 1 daemon MVP, Milestone 2 MCP substrate, Milestone 3 offline/reference Codex transcript ingestion MVP, Codex MCP dogfood setup, Phase 14 parity recovery, Phase 14B/14C hardening/parity, Phase 15 publication prep, Phase 13 Codex hook dogfood, and Phase 13B session discovery hotfix. |
