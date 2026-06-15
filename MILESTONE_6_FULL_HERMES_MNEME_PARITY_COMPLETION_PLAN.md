# Milestone 6: Full Hermes-Mneme Parity Completion

Date: 2026-06-14
Status: complete as of 2026-06-15

## Goal

Make Mneme Universal no worse than original `hermes-mneme` for runtime-neutral
memory/context-engine behavior, while keeping the newer REST/MCP/audit/Codex
additions.

This milestone ports the remaining original behavior into the universal core,
including features Codex cannot yet use automatically. Future host adapters
should find a complete context-engine backend out of the box.

## Completion Notes

- Runtime-neutral daemon/core parity is restored without Hermes adapter work.
- Codex remains tools-only; `/v1/context/prepare` now returns adapter-ready
  metadata, but automatic prompt insertion still requires a host lifecycle hook.
- Real local dogfood confirms required embeddings and reranker calls. LLM
  enrichment is covered by provider tests; real LLM smoke remains a release
  claim gate when an LLM provider is configured.
- Optional `sqlite_vec` acceleration remains documented as optional because it
  is not installed in this local environment; Python cosine fallback is the
  verified portable path.

## Rules

- Work only inside `_mneme-universal-context-service`.
- Do not modify live Hermes or live `hermes-mneme`.
- Do not start Hermes adapter work or a compaction bridge.
- Execute this milestone continuously: after finishing one task, immediately
  continue to the next task. Stop only for a real blocker or for a user question
  whose answer cannot be found in original `hermes-mneme`.
- Keep Codex claims tools-only until a real prompt/context hook exists.
- Keep prompts, docs, traces, and test fixtures as short as possible.
- Prefer small slices: one behavior, one focused test file, one verification.
- Provider calls stay opt-in; real-provider smoke runs only when explicitly
  configured.
- Embeddings are required for dogfood/public quality; minimal mode is CI/dev
  fallback only.

## Acceptance Target

Universal Mneme must support these original-core behaviors:

- required semantic embeddings for quality mode;
- optional `sqlite_vec` acceleration plus portable Python fallback;
- topic-centroid drift with cache/window behavior;
- intent-aware routing with semantic, keyword, recency, type, dependency, and
  reranker scoring;
- cross-session/global search and segment fallback;
- full execution state, goal trail, state recovery, and lineage behavior;
- LLM enrichment with `intent_label`, `topic_tags`, decisions with rationale,
  and decision summary;
- budgeted context preparation equivalent to original prompt builder;
- MCP/REST tools that expose the richer state, segment, search, fetch, expand,
  recent, explain, and cost behavior.

## Task 0: Parity Harness Refresh

Create a compact test matrix from original `hermes-mneme` behavior and update
the comparison doc so current gaps are explicit.

Deliverables:

- Expand parity tests as failing/xfail-free specs before each slice.
- Refresh `HERMES_MNEME_COMPARISON.md` from "mostly recovered" to exact
  remaining gaps.
- Add compact fixture sessions covering topic drift, dependencies, enrichment,
  global search, and context packing.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q
```

## Task 1: Config Surface Parity

Add missing original knobs without exposing secrets.

Scope:

- budget ratios, prompt overhead, protected tail;
- segmentation drift weights, centroid cache/window;
- retrieval router limits, dependency depth/decay, reranker top_k;
- enrichment schedule/history/timeout/max_tokens;
- tool-output embedding compression thresholds;
- reindex-on-model-change flag;
- memory access hint, goal trail, checkpoint settings.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py -q
```

## Task 2: Embedding and Index Parity

Make semantic storage/search match original quality behavior.

Scope:

- optional `sqlite_vec` path when installed;
- Python fallback remains default portable path;
- global and multi-session semantic search;
- model-change reindex behavior;
- configurable tool-output embedding compression;
- embedding metrics and degraded traces stay secret-safe.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_retrieval.py -q
```

## Task 3: Segmentation and Intent Parity

Port original topic and intent signals.

Scope:

- centroid cache and centroid window;
- weighted drift score;
- entity contradiction signal;
- question-about-last-output signal;
- explicit switch signal weights;
- segment large-warning trace;
- richer `list_segments` data: event types, first/last user snippets,
  `goal_at_end`, `topic_tags`.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_classifier.py tests/test_segments.py -q
```

## Task 4: Router and Ranking Parity

Port original retrieval routing and scoring.

Scope:

- routing modes: general, reasoning, factual, debugging, clarification;
- query builder from execution state, current prompt, last tool output;
- strip retrieved-context echoes from query input;
- current-segment search plus `router_min_candidates` fallback;
- score mix: similarity, recency, dependency, type;
- dependency BFS depth/decay from recent tool/assistant anchors;
- reranker parser parity, including score-list responses.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_retrieval.py tests/test_reranker.py -q
```

## Task 5: Execution State and Lineage Parity

Make state and session recovery no weaker than original.

Scope:

- default state includes `segment_id` and enrichment fields;
- enrichment fields include `decision_summary`, `intent_label`, `topic_tags`;
- decision stack supports rationale;
- recover current state from state history;
- ancestor-state fallback for compressed/resumed sessions;
- runtime-neutral session rebase/reassign operation if needed by adapters.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_state.py tests/test_session_drift.py -q
```

## Task 6: LLM Enrichment Parity

Port original enrichment quality while keeping provider behavior safe.

Scope:

- concise enrichment prompt returning JSON only;
- fields: `intent_label`, `topic_tags`, decisions with `decision` and
  `rationale`, `decision_summary`;
- robust JSON recovery from markdown/prose/truncation;
- configurable history window, max tokens, timeout, temperature 0;
- run by schedule and segment boundary without blocking ingestion;
- host-supplied provider hook point for future adapters, not Hermes-specific
  coupling.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_enrichment.py tests/test_state.py -q
```

## Task 7: Context Prepare / Prompt Builder Parity

Make `/v1/context/prepare` a complete request-only context-engine backend.

Scope:

- memory access hint;
- goal trail;
- checkpoint hint;
- execution state compression ladder;
- retrieved context with event ids;
- cross-session candidates;
- protected tail plus tail extension;
- calibrated prompt overhead;
- collision handling equivalent to original;
- adapter-ready output metadata for future automatic host insertion.

Codex remains preview/tools-only unless Codex exposes a real host hook.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_parity_recovery.py -q
```

## Task 8: MCP/REST Tool Parity

Expose the richer behavior through public tools without breaking current
additions.

Scope:

- `context_search` supports current, lineage, global, and segment scopes;
- `fetch_event` includes segment and token metadata;
- `expand_context(mode="segment")` returns segment skeleton;
- `list_segments` returns richer table-of-contents data;
- `recall_recent` remains newest-tail safe;
- `get_execution_state` and `get_goal_history` include recovered fields;
- tool instructions stay short and evidence-focused.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_contract.py -q
```

## Task 9: Real Provider Dogfood Gate

Verify the full quality stack with local configured providers.

Scope:

- embeddings required and rows written on ingest;
- reranker called and affects ranking;
- LLM enrichment writes topic tags and decision rationale;
- context prepare includes enriched state and semantic evidence;
- costs/traces show calls, failures, and degraded states.

Verification:

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest -q
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q
env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests
```

## Task 10: Publication/Install Readiness Refresh

After parity is restored, refresh public docs and install flow.

Scope:

- README and provider docs match final behavior;
- Codex adapter docs remain tools-only/no overclaim;
- installer examples are package-relative and second-machine friendly;
- GitHub publication checklist includes daemon, MCP, hooks, providers, DB path,
  and trust approval per machine.

Verification:

```bash
rg -n "automatic prompt replacement|automatically replace|magic universal" README.md docs adapters/codex
rg -n "^(<<<<<<<|=======|>>>>>>>)" README.md docs adapters/codex mneme_service tests *.md
rg -n "[[:blank:]]$" README.md docs adapters/codex mneme_service tests *.md
```

## Final Gate

```bash
env TMPDIR=/private/tmp .venv/bin/python -m pytest -q
env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_parity_recovery.py -q
env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests
```

Only after this gate should Codex hook publication and second-machine GitHub
install rehearsal resume.
