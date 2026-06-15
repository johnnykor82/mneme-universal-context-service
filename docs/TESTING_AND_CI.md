# Testing and CI

## Local Checks

Run the full suite:

```bash
.venv/bin/python -m pytest -q
```

Run the Phase 14C parity acceptance suite:

```bash
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
```

Compile Python modules:

```bash
.venv/bin/python -m compileall -q mneme_service tests
```

Scan changed files for merge markers and trailing whitespace:

```bash
rg -n "^(<<<<<<<|=======|>>>>>>>)" .
rg -n "[[:blank:]]$" .
```

## CI Quality Gate

The GitHub Actions workflow in `.github/workflows/ci.yml` runs on push and pull
request:

- install package with test extras;
- run `pytest -q`;
- run `pytest tests/test_parity_recovery.py -q`;
- compile `mneme_service` and `tests`.

The suite uses fake providers and `httpx.MockTransport` for provider behavior.
CI should not require real embedding, reranking, or LLM API keys.

## Important Test Groups

- `tests/test_contract.py`: REST contract behavior.
- `tests/test_mcp_contract.py`: MCP discovery/proxy parity.
- `tests/test_embeddings.py`: provider/index/circuit behavior.
- `tests/test_retrieval.py`: hybrid retrieval fallback behavior.
- `tests/test_state.py`: execution state and goal history.
- `tests/test_segments.py`: segmentation and drift traces.
- `tests/test_context_assembly.py`: budgeted context prepare.
- `tests/test_context_prepare.py`: memory hint, goal trail, checkpoint, and
  global-candidate context prepare behavior.
- `tests/test_reranker.py`: optional reranker.
- `tests/test_enrichment.py`: optional LLM enrichment.
- `tests/test_parity_recovery.py`: end-to-end Phase 14C acceptance.
