# Publication Checklist

This checklist gates public GitHub publication.

## Required Before Public Release

- [x] Select and add a license.
- [x] Decide whether `adapters/codex` remains in this repository or becomes a
  separate package/repository.
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
- [x] After local hook validation, publish Mneme plus the Codex adapter to the
  user's GitHub.
- [ ] Run a second-machine install rehearsal from GitHub as a new-user flow.

## License Gate

The project owner selected Apache License 2.0. `LICENSE` and `NOTICE` identify
Ivan Konstantinov as the 2026 copyright owner.

## Codex Adapter Scope

`adapters/codex` remains in this repository for the first public-prep pass. A
separate adapter package or repository should wait until the adapter has a
stable live ingestion path or a host lifecycle integration beyond MCP tools.

Codex adapter docs and examples should be written as future user-facing install
material: prefer package-relative commands, placeholders for secrets, explicit
trust steps for hooks, and local dogfood paths only in files clearly marked as
dogfood-only.

## Post-Hook Publication Gate

Do not publish the Codex hook adapter path as ready before trusted local hook
payload validation succeeds on this machine.

After local hook validation:

- publish Mneme plus `adapters/codex` to the user's GitHub:
  `https://github.com/johnnykor82/mneme-universal-context-service`;
- install on the second Codex machine from GitHub as if the installer were a
  new user, not by relying on shared symlinked files;
- verify `mneme serve`, `mneme mcp`, auth token/env, database path, provider
  secrets if used, MCP visibility, hook trust, `mneme codex-hook-capture`,
  `mneme codex-hook-validate`, and a REST-ingestion plus MCP-recall smoke path;
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
