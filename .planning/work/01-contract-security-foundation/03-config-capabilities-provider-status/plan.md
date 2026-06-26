# Plan: 03-config-capabilities-provider-status

## Level

task

## Parent

`.planning/work/01-contract-security-foundation/plan.md`

## Status

complete

## Goal

Complete v0 foundation config validation and capabilities/provider status
reporting while preserving truthful unsupported flags.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 8 | Config defaults and validation invariants |
| Section 10 | Provider and cost-mode behavior |
| Section 14.1 | Capabilities shape, limits, tokenizer, storage, metrics format |
| CM-017, CM-020, CM-034 | Config/capabilities/provider gaps |
| S24-37, S24-38, S24-39, S24-77, S24-111 | Provider-free readiness and capability tests |

## Active Step

Active Task: none (leaf)

## Steps

- [x] Review prior Phase 1A config/capabilities diffs for completeness.
  - Verification: config tests enumerate Section 8 required defaults and invalid invariants.
- [x] Close missing provider status and strict cost-mode reporting gaps for this phase.
  - Verification: provider/cost tests cover downgrade or strict failure behavior.
- [x] Ensure `/v1/capabilities` exposes only implemented support as true.
  - Verification: capabilities tests assert unsupported blob/metrics/reindex/retention flags stay false until implemented.
- [x] Verify readiness provider-free behavior remains cheap for `require_evidence=false`.
  - Verification: targeted readiness test proves no provider calls.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Section 8 / CM-017 | ~ partial | Prior Phase 1A config defaults/validation retained; targeted config suite passes |
| Section 10 / CM-020 | ~ partial | `QUALITY` strict mode returns `503 PROVIDER_UNAVAILABLE`; non-strict emits `COST_MODE_DOWNGRADED`; enabled HTTP provider without key fails startup |
| Section 14.1 / CM-034 | ~ partial | Capabilities expose provider `enabled/configured/available`, strict mode, metrics format, tokenizer/storage limits, and truthful false unsupported flags |
| S24-37 / 38 / 39 / 77 / 111 | ~ partial | Added/verified no-provider minimal readiness, cost-mode downgrade/fail, provider missing key fail, metrics capability, and provider-free readiness evidence |

**Compliance Status: COMPLETE FOR PHASE 1 FOUNDATION SCOPE; OVERALL ROWS REMAIN PARTIAL**

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|

## Notes

- Existing root history reports partial Phase 1A coverage; verify against current files after approval.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_config.py tests/test_contract.py tests/test_openapi.py -q`
  -> `35 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_embeddings.py tests/test_reranker.py tests/test_enrichment.py tests/test_parity_recovery.py tests/test_retrieval.py -q`
  -> `33 passed, 1 warning`.
- Verification:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_mcp_contract.py -q`
  -> `16 passed`.
