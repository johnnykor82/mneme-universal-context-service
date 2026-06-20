# Publication Checklist

This checklist gates public GitHub publication.

## Required Before Public Release

- [x] Select and add a license.
- [x] Decide whether `adapters/codex` remains in the public engine repository
  or becomes a separate package/repository.
- [x] Confirm README claims match implemented behavior.
- [x] Confirm Codex docs say MCP is tools-only and does not automatically
  replace Codex prompt context.
- [x] Run the full test suite.
- [x] Run the parity acceptance suite.
- [x] Run Python compile checks.
- [x] Scan docs/examples/config for secrets.
- [x] Confirm `mneme.example.toml` contains no real credentials.
- [x] Confirm provider calls are disabled by default.
- [x] Confirm dogfood/public-readiness mode requires embeddings and refuses a
  silently keyword-only daemon when embeddings are missing.
- [x] Run a real provider smoke with configured local/remote providers:
  capabilities must show `supports_embeddings: true`,
  `requires_embeddings: true`, and expected reranker support; ingest must
  record `embedding_items > 0` and `embedding_failures == 0`; `context_search`
  must record `reranker_calls > 0` and `reranker_failures == 0` when reranker is
  enabled.
- [x] Clarify and verify the LLM surface before publication: current Mneme
  supports structured LLM enrichment of execution state, not a separate
  natural-language answer-synthesis endpoint. Do not claim answer synthesis
  unless it is implemented, documented, and smoke-tested with a real provider.
- [x] Confirm `.gitignore` excludes local DBs, virtualenvs, bytecode, caches,
  build artifacts, and egg-info.
- [x] For each new adapter surface after Phase 15, confirm installation/setup
  docs are understandable to future GitHub users and can be automated where
  feasible.
- [x] For multi-machine Codex use, confirm setup docs distinguish shared
  symlinked files from per-machine runtime installation, daemon, MCP, token,
  database, and hook trust steps.
- [x] Quarantine the first mixed engine/adapter/internal publication as private.
- [x] Publish clean Mneme engine/core repository
  `johnnykor82/mneme-universal-context-service` without host-specific adapters
  or internal planning/dogfood artifacts.
- [x] Publish separate Codex adapter repository/package
  `johnnykor82/mneme-codex-adapter`.
- [x] Add a Codex Desktop global quickstart and token-safe setup/doctor/status
  commands for the next second-machine rehearsal.
- [ ] Run a second-machine install rehearsal from the clean public engine and
  adapter repositories as a new-user flow.

## License Gate

The project owner selected Apache License 2.0. `LICENSE` and `NOTICE` identify
Ivan Konstantinov as the 2026 copyright owner.

## Repository Split Scope

Public release must keep Mneme engine/core separate from host adapters. The
engine/core repository should contain the daemon, storage, REST/MCP service,
provider interfaces, context preparation, and runtime-neutral tests/docs. Codex
hook code, Codex skills, AGENTS snippets, and Codex setup docs belong in a
separate Codex adapter repository/package.

Chosen GitHub repository names:

- Core engine: `johnnykor82/mneme-universal-context-service`.
- Codex adapter: `johnnykor82/mneme-codex-adapter`.

Codex adapter docs and examples should be written as future user-facing install
material: prefer package-relative commands, placeholders for secrets, explicit
trust steps for hooks, and local dogfood paths only in files clearly marked as
dogfood-only.

## Split Publication Gate

Do not publish the Codex hook adapter path as ready before trusted local hook
payload validation succeeds on this machine. Do not publish internal planning,
dogfood prompts, local rehearsal files, or machine-specific notes as public
install artifacts.

Corrected publication sequence:

- keep the first mixed repository private/quarantined;
- publish clean `johnnykor82/mneme-universal-context-service` as the Mneme
  engine/core repository;
- publish separate `johnnykor82/mneme-codex-adapter` as the Codex adapter
  repository/package;
- install both on the second Codex machine from GitHub as if the installer were
  a new user, not by relying on shared symlinked files;
- verify `mneme-codex setup codex-desktop --global`, `mneme-codex doctor`,
  `mneme serve`, `mneme mcp`, auth token/env, database path, provider secrets
  if used, MCP visibility, hook trust, `mneme-codex codex-hook-capture`,
  `mneme-codex codex-hook-validate`, and a REST-ingestion plus MCP-recall smoke
  path;
- record any missing setup step before calling the publication path ready.

## Honest Claims

Allowed claims:

- local-first REST/MCP context memory service;
- audited memory tools for MCP clients;
- request-only context assembly for runtimes with host lifecycle hooks;
- provider-backed semantic memory when embeddings are configured and required;
- optional reranking and structured enrichment quality layers;
- Phase 14C daemon/core parity suite passes locally.

Avoid these claims:

- "Mneme can automatically replace any runtime's prompt from outside the host."
- "Codex MCP integration gives invisible automatic context replacement."
- "Provider-backed features work without configuration or credentials."
- "Dogfood/public-ready semantic memory works without embeddings."
- "Mneme synthesizes final natural-language answers from memory" unless a
  dedicated answer-synthesis path is implemented and verified.
- "This is production-hosted infrastructure."
