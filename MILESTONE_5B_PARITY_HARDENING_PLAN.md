# Milestone 5B: Parity Hardening While Hermes PR Is Pending

Date: 2026-06-14
Status: complete

## Goal

Continue the Phase 14 line of work without starting Hermes adapter
implementation while the upstream Hermes context-engine hook PR is pending.

The target is to harden the universal daemon's recovered Mneme quality pipeline:
documentation accuracy, residual parity gaps, benchmarks, provider robustness,
and adapter-independent conformance evidence.

## Why Hermes Adapter Work Is Deferred

Hermes integration should wait for the upstream Hermes PR that exposes the
native context-engine lifecycle hooks needed for a clean integration:

- post-turn ingestion;
- request-only message preparation before model calls;
- session lifecycle events;
- model and budget updates;
- tool schema/dispatch integration.

Building against the legacy compaction path now would create throwaway work and
increase the chance of implementing the same bridge twice. Until the PR lands,
Hermes adapter implementation remains out of scope.

## Non-Goals

- Do not modify live Hermes.
- Do not modify live `hermes-mneme`.
- Do not implement a Hermes adapter through `compress()` or compaction.
- Do not add host-specific Hermes session discovery to the daemon.
- Do not require real provider API keys for tests.

## Task 1: Refresh Post-Phase-14 Parity Docs

**Status:** complete

The original `HERMES_MNEME_COMPARISON.md` captured the pre-Phase-14 gap. It is
now stale because Phase 14 implemented provider config, embeddings, hybrid
retrieval, execution state, segmentation, lineage, graph scoring, budgeted
prepare, reranker, enrichment, and acceptance tests.

Deliverables:

- Add a post-Phase-14 status section to `HERMES_MNEME_COMPARISON.md`.
- Identify residual gaps that are adapter-dependent versus daemon/core gaps.
- Record that Hermes adapter work is blocked on upstream native hooks, not on
  the daemon parity pipeline.

Result: complete. `HERMES_MNEME_COMPARISON.md` now has a post-Phase-14 status
section that identifies recovered daemon parity and residual gaps. The original
comparison table is preserved as historical pre-Phase-14 audit context.

Verification:

```bash
rg -n "^(<<<<<<<|=======|>>>>>>>)" HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md
rg -n "[[:blank:]]$" HERMES_MNEME_COMPARISON.md task_plan.md findings.md progress.md
```

## Task 2: Add Adapter-Independent Benchmark Harness

**Status:** complete

Create small deterministic benchmarks that exercise the recovered daemon
pipeline without depending on Hermes:

- event ingestion throughput for mixed event batches;
- keyword/recency retrieval baseline;
- fake-provider semantic retrieval path;
- budgeted `/v1/context/prepare` packing;
- cost report counters.

Benchmarks should use local/fake providers by default and produce output that is
easy to paste into docs or release notes.

Result: complete. Added `mneme_service.benchmarks.run_local_benchmark`, the
`mneme benchmark` CLI command, focused benchmark tests, and
`docs/BENCHMARKS.md`. The harness uses an in-process REST app, a synthetic
session, fake local embedding vectors, `context_search`, `/v1/context/prepare`,
and cost reports. It makes no external provider calls.

Verification:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q mneme_service tests
```

## Task 3: Provider Robustness Acceptance

**Status:** complete

Expand provider edge-case coverage without real provider calls:

- malformed embedding responses;
- wrong vector dimensions;
- reranker result indexes outside range;
- non-JSON enrichment responses;
- timeout/circuit-breaker recovery;
- provider input redaction.

Verification:

```bash
.venv/bin/python -m pytest tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py -q
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
```

Result: complete. Added provider robustness coverage for malformed embedding
payloads, mixed embedding dimensions, out-of-range reranker indexes, and
non-JSON LLM enrichment responses. Embedding parsing/indexing now treats
malformed vectors and mixed-dimension batches as provider/index failures.

## Task 4: Residual Optional Vector Acceleration Check

**Status:** complete

`sqlite_vec` is optional and was not installed in the local `.venv` during
Phase 14. Keep Python cosine as the portable default, but document and, if
reasonable, add a skipped/optional test path for `sqlite_vec` so future
environments can exercise vector acceleration without making it mandatory.

Verification:

```bash
.venv/bin/python -c "import importlib.util; print(importlib.util.find_spec('sqlite_vec'))"
.venv/bin/python -m pytest tests/test_embeddings.py -q
```

Result: complete. Local `sqlite_vec` availability check returned `None`.
Added `docs/VECTOR_ACCELERATION.md` documenting that Python cosine fallback is
the verified portable path and that `sqlite_vec` remains optional future
acceleration, not a required dependency or current performance claim.

## Task 5: Phase 14B Final Gate

**Status:** complete

Finish with a focused evidence bundle:

- post-Phase-14 parity status updated;
- benchmarks runnable;
- provider robustness tests pass;
- optional vector acceleration posture documented;
- full pytest and compile checks pass;
- planning files updated.

Verification:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_parity_recovery.py -q
.venv/bin/python -m compileall -q mneme_service tests
```

Result: complete. Full pytest, parity acceptance, provider/benchmark focused
tests, compileall, and conflict/trailing-whitespace scans pass.
