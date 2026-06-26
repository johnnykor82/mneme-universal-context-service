# Plan: 62-residual-contract-fix-batch-bg

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-013`/`CM-014` by adding machine-readable integration-depth and host
adapter lifecycle capability claims without overclaiming unsupported
`CONTEXT_ENGINE` or `COMPACTION_OWNER` behavior.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 5 | Adapters must declare deepest supported integration level and avoid overclaiming. |
| Section 5.1 | Host adapter lifecycle contract must distinguish event ingest, context engine, and future compaction owner levels. |
| CM-013, CM-014 | Integration depth and host lifecycle evidence. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing capabilities/OpenAPI tests for explicit depth claims | complete | RED before implementation: `3 failed, 1 warning`; GREEN after implementation: `3 passed, 1 warning`. |
| Implement minimal capability schema/response fields | complete | Capability response now includes full Section 5 level taxonomy and per-surface claims. |
| Add lifecycle evidence tests/docs assertions if needed | complete | Touched gate with OpenAPI/contract/Codex hook/doc assertions: `9 passed, 87 deselected, 1 warning`. |
| Update matrix/planning and run hygiene checks | complete | `CM-013` set `COMPLIANT`; `CM-014` narrowed; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/schemas.py`
- `mneme_service/app.py`
- `tests/test_openapi.py`
- `tests/test_contract.py`
- `tests/test_codex_hooks.py` or `tests/test_codex_adapter.py` if needed
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 5 depth declaration | ✓ met | `/v1/capabilities` `integration_depth` response and OpenAPI schema include all Section 5 levels and explicit unsupported/future levels. |
| Section 5.1 lifecycle declaration | ✓ met | Core REST lifecycle declares `EVENT_INGEST`; Codex hooks are not overclaimed as full lifecycle integration. |
| CM-013/CM-014 machine-readable depth slice | ✓ met | Matrix `CM-013` set `COMPLIANT`; `CM-014` remains `PARTIAL` only for unverified production host adapter lifecycle. |

**Compliance Status: VERIFIED**
