# Mneme v0 Reviewer Packet

Date: 2026-06-26
Spec under review: `docs/MNEME_STANDALONE_SPEC.md`
Spec status: Final v0.7.5 - Approved for v0 implementation
Implementation evidence status: ready for reviewer acceptance

## Scope

This packet is the reviewer-facing handoff for Mneme Universal Context Service
v0 compliance. The canonical target is `docs/MNEME_STANDALONE_SPEC.md`; this
packet does not modify or supersede that specification.

The reviewed implementation scope is the local service in this repository:

- FastAPI REST daemon and OpenAPI contract.
- SQLite-backed local storage, migrations, idempotency, audit, traces, graph,
  segments, retention, blobs, metrics, maintenance, and provider-safe optional
  quality layers.
- MCP read-tool parity and host-adapter boundary documentation.
- Packaging, benchmark, installation, and operations documentation needed for
  v0 review.

Out-of-scope/future items remain those listed by Section 26 of the spec and
`CM-064`, including hosted/cloud Mneme, enterprise RBAC, collaborative
multi-user workspaces, model-callable MCP write tools, first-class SQLCipher or
keychain integration, and `COMPACTION_OWNER` host authority.

## Compliance Status

The final compliance matrix is `docs/MNEME_V0_COMPLIANCE_MATRIX.md`.

Final matrix state after Phase 10 Batch BQ/BR:

| Status | Count |
|---|---:|
| `COMPLIANT` | 64 |
| `PARTIAL` | 0 |
| `MISSING` | 0 |
| `UNCLEAR` | 0 |
| `OUT_OF_SCOPE/FUTURE` | 1 |

The single `OUT_OF_SCOPE/FUTURE` row is `CM-064`, which records explicit
non-goals and future scope from the approved spec. It is not an implementation
gap.

## Acceptance Evidence

Final verification was run on 2026-06-26:

| Gate | Command | Result |
|---|---|---|
| Full test suite | `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q` | `332 passed, 1 warning in 21.52s` |
| Compile check | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` | Exit 0 |
| OpenAPI focused gate | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q` | `10 passed, 1 warning in 1.79s` |
| Diff hygiene | `git diff --check` | Exit 0 |

One final full-suite run initially exposed two stale contract assertions after
later graph and retrieval trace improvements:

- `tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces`
- `tests/test_parity_recovery.py::test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak`

Phase 10 Batch BR updated those assertions to match the current richer,
spec-compliant trace behavior:

- `fetch_event(include_neighbors=true)` memory-read traces now follow the
  actual neighbor evidence returned by the response, including turn-complete
  provenance nodes when present.
- Provider-backed retrieval traces now include the explicit
  `GRAPH_DEPENDENCY` strategy before `RERANK` when graph evidence participates.

Focused verification after the BR fix:

| Gate | Command | Result |
|---|---|---|
| Two red tests | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py::test_mcp_memory_tools_write_audit_records_and_traces tests/test_parity_recovery.py::test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak -q` | `2 passed, 1 warning` |
| Touched area | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py tests/test_parity_recovery.py tests/test_graph.py tests/test_retrieval.py -q -k "memory_tools_write_audit_records_and_traces or provider_pipeline_recovers or context_search_includes_graph_dependencies or trace_reports_router_mode or degraded_trace"` | `5 passed, 48 deselected, 1 warning` |

## Traceability

Traceability is maintained through these artifacts:

- Canonical spec: `docs/MNEME_STANDALONE_SPEC.md`.
- Final compliance matrix: `docs/MNEME_V0_COMPLIANCE_MATRIX.md`.
- Implementation plan input: `docs/MNEME_V0_COMPLIANCE_IMPLEMENTATION_PLAN.md`.
- Spec-driven planning manifest: `.planning/spec.md`.
- Roadmap and active phase evidence: `.planning/roadmap.md`.
- Phase 10 final acceptance plan:
  `.planning/work/10-final-acceptance-reviewer-packet/plan.md`.
- Final verification task:
  `.planning/work/10-final-acceptance-reviewer-packet/72-final-verification-batch-bq/plan.md`.
- Full-suite red-fix task:
  `.planning/work/10-final-acceptance-reviewer-packet/73-full-suite-red-fix-batch-br/plan.md`.
- Progress log: `.planning/progress.md`.

The accepted mapping approach is:

`spec section -> compliance matrix row -> Section 24 test number -> task plan -> verification evidence`.

Section 24 required contract tests 1-119 are either implemented directly or
mapped to equivalent composite tests in the matrix. No grouped Section 24 row
remains `PARTIAL`.

## Reviewer Checklist

| Check | Status | Evidence |
|---|---|---|
| One canonical v0 target spec | complete | `docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5 |
| Compliance matrix closed | complete | `COMPLIANT: 64`, `PARTIAL: 0`, `OUT_OF_SCOPE/FUTURE: 1` |
| Section 24 tests mapped | complete | `CM-062` and Required Contract Test Mapping table |
| Full verification green | complete | `332 passed`, compile/OpenAPI/diff gates clean |
| Reviewer packet produced | complete | This document |
| Explicit future/non-goal scope preserved | complete | `CM-064` and Section 26 |

## Residual Risks

- The repository worktree is intentionally dirty with the accumulated
  implementation and planning changes for this compliance effort; no commit or
  push has been made.
- Real-provider smoke remains release-gated only when release notes claim live
  provider readiness. Public CI remains provider-free/local by design.
- Previous-version migration fixtures must be added for each future published
  schema migration before a later stable release; current v0 has no earlier
  published migration series to fixture.
- First-class SQLCipher/keychain integration remains future scope; v0 relies on
  owner-only file permissions and OS-encrypted storage guidance.

## Disposition

Implementation evidence is ready for reviewer acceptance against
`docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5.

Recommended reviewer decision: `ACCEPT_V0_IMPLEMENTATION_EVIDENCE`.

Release publication, git commit, push, and any live Hermes integration remain
separate owner-approved actions.
