# Vector Acceleration

Mneme currently verifies semantic retrieval through the portable Python cosine
fallback over SQLite-stored embedding rows.

## Current Status

- `sqlite_vec` is optional and is not required to run Mneme.
- The local Phase 14C environment does not have `sqlite_vec` installed.
- The verified path is provider-backed embedding generation plus Python cosine
  search fallback.
- Public docs should not claim accelerated `sqlite_vec` search until an
  installed environment exercises that path.

Check local availability:

```bash
.venv/bin/python -c "import importlib.util; print(importlib.util.find_spec('sqlite_vec'))"
```

Expected output in the current local environment:

```text
None
```

## Optional Acceleration Path

`sqlite_vec` can be added behind dependency detection:

- if `sqlite_vec` imports successfully, initialize the extension and use vector
  KNN for eligible searches;
- if it is unavailable or fails to initialize, keep Python cosine fallback;
- tests for the accelerated path should skip when `sqlite_vec` is unavailable;
- fallback behavior must remain covered in normal CI.

The acceptance requirement is portability first: missing vector acceleration
must not prevent ingestion, retrieval, context preparation, or MCP tools from
working.
