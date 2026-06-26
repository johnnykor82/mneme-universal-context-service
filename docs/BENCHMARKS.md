# Benchmarks

Mneme includes a local adapter-independent benchmark harness for Phase 14B
parity hardening.

Run:

```bash
mneme benchmark --events 30 --db .local/mneme-benchmark.db
```

The benchmark starts an in-process REST app, writes a synthetic session to the
selected SQLite database, ingests mixed events, runs `context_search`, calls
`/v1/context/prepare`, and reads the session cost report.

It uses local fake embedding vectors. It does not call external embedding,
reranking, or LLM providers.

The command prints a JSON report:

```json
{
  "schema_version": "mneme.benchmark_report.v0",
  "mode": "LOCAL_FAKE_PROVIDERS",
  "methodology": {
    "benchmark_type": "LOCAL_SMOKE",
    "providers": "LOCAL_FAKE_PROVIDERS",
    "corpus": "SYNTHETIC_LABELED",
    "comparative_baseline": "NOT_RUN",
    "token_reduction_claim": "NOT_CLAIMED",
    "cost_reduction_claim": "NOT_CLAIMED",
    "token_estimate_methodology": "SERVICE_COST_COUNTERS"
  },
  "event_count": 30,
  "timings_ms": {
    "session_start": 1.0,
    "ingest": 10.0,
    "retrieval": 3.0,
    "context_prepare": 5.0
  },
  "ingest": {
    "accepted": 30,
    "duplicates": 0,
    "rejected": 0
  },
  "retrieval": {
    "result_count": 5
  },
  "quality_report": {
    "schema_version": "mneme.benchmark_quality_report.v0",
    "label_source": "SYNTHETIC_CORPUS",
    "metrics": {
      "precision_at_k": 1.0,
      "recall_at_k": 0.5,
      "mrr": 1.0
    }
  },
  "context_prepare": {
    "changed": true,
    "message_count": 3,
    "selected_event_count": 5
  },
  "costs": {
    "embedding_batches": 2,
    "embedding_items": 31,
    "embedding_input_chars": 1800,
    "reranker_calls": 0,
    "enrichment_calls": 0
  }
}
```

Treat the numbers as local smoke evidence, not as a cross-machine performance
claim. Use the same machine, Python version, database location, and event count
when comparing changes.

The local smoke output has no comparative baseline. It is useful for checking
that ingestion, retrieval, context prepare, cost counters, and synthetic quality
reporting still work, but it is not proof of token or cost reduction.
