# Provider Configuration

Mneme works in minimal mode without provider credentials. Optional providers add
semantic embeddings, reranking, and LLM-derived structured state enrichment.

## Precedence

Settings are loaded in this order:

1. CLI overrides
2. Environment variables
3. TOML config file
4. Defaults

## Minimal Mode

Minimal mode disables all provider surfaces and exists for local development,
CI, and fallback testing:

```toml
[daemon]
require_embeddings = false

[providers.embeddings]
enabled = false

[providers.reranker]
enabled = false

[providers.llm_enrichment]
enabled = false
```

No provider network calls should be made in this mode.

Minimal mode is not the recommended mode for production-like semantic memory.
Real semantic memory
requires embeddings because semantic search, topic centroids, and drift
detection depend on stored vectors. In short: semantic memory requires embeddings.

## Required Embeddings Mode

For production-like usage, require embeddings so the daemon fails
fast instead of silently running keyword-only memory:

```toml
[daemon]
require_embeddings = true

[providers.embeddings]
enabled = true
provider = "openai_compatible"
model = "jina-embeddings-v5-text-small-retrieval-mlx"
base_url = "http://localhost:8000/v1"
```

Equivalent environment/CLI controls:

```bash
export MNEME_REQUIRE_EMBEDDINGS=true
mneme serve --require-embeddings --embeddings-enabled ...
```

`GET /v1/capabilities` should report both `supports_embeddings: true` and
`requires_embeddings: true` for this mode. For release validation, ingest a real
event and verify `embedding_items > 0` and
`embedding_failures == 0` in the session cost report.

## Embeddings

Embeddings use an OpenAI-compatible `/embeddings` endpoint.

```toml
[providers.embeddings]
enabled = true
provider = "openai_compatible"
model = "text-embedding-3-small"
base_url = "https://api.openai.com/v1"
timeout_seconds = 30.0
batch_size = 16
```

Secret:

```bash
export MNEME_EMBEDDING_API_KEY="<secret>"
```

Embedding failures do not block event ingestion. Stored events remain available
through keyword/recency fallback.

## Reranker

Reranking uses a Jina/Cohere-style `/rerank` endpoint and parses result items
with `index` plus `relevance_score` or `score`.

```toml
[providers.reranker]
enabled = true
provider = "jina"
model = "jina-reranker-v2-base-multilingual"
base_url = "https://api.jina.ai/v1"
timeout_seconds = 30.0
```

Secret:

```bash
export MNEME_RERANKER_API_KEY="<secret>"
```

Reranker failures preserve the original retrieval order and are reflected in
trace fallback metadata and cost-report failure counters.

For production-like verification, run a real `context_search` and
confirm `reranker_calls > 0` with `reranker_failures == 0` when the configured
reranker is expected to be available.

## LLM Enrichment

LLM enrichment uses an OpenAI-compatible `/chat/completions` endpoint with JSON
mode. Provider output can update only structured execution-state fields:

- `enrichment.intent_label`
- `enrichment.topic_tags`
- `enrichment.decisions` with optional `decision` and `rationale`
- `enrichment.decision_summary`
- `active_entities`
- `open_loops`

```toml
[providers.llm_enrichment]
enabled = true
provider = "openai_compatible"
model = "gpt-4.1-mini"
base_url = "https://api.openai.com/v1"
timeout_seconds = 30.0
```

Secret:

```bash
export MNEME_LLM_API_KEY="<secret>"
```

LLM enrichment failures do not block ingestion. Provider output is parsed as
JSON, recovered from common fenced/prose/truncated response shapes when safe,
constrained to allowed fields, and redacted before state commit.

LLM enrichment is not the same as natural-language answer synthesis. The current
daemon can enrich structured execution state; it is not a separate natural-language answer-synthesis endpoint. Do not
publish an answer-synthesis claim unless that path is implemented and verified
with a real provider.

Run a real-provider smoke before claiming live LLM enrichment readiness in a
release.

## Privacy

Mneme redacts configured secret patterns before storage, indexing, embedding,
reranking, enrichment, traces, and MCP results. Do not put real API keys in
tracked TOML files or examples.
