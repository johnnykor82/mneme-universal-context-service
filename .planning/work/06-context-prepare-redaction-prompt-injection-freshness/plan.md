# Plan: 06-context-prepare-redaction-prompt-injection-freshness

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Make context prepare, token accounting, redaction, prompt-injection defense,
and evidence freshness match the approved Final v0.7.5 contract.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 11, 14.13, 14.14, 17.2, 17.3 | Tokenization, context packing, freshness, redaction, evidence wrappers |
| CM-021, CM-047, CM-048, CM-053, CM-054 | Context/security gaps |
| S24-18-22, 35-36, 55, 69-70, 89, 95-96, 99, 104, 115, 119 | Required/equivalent tests |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-budget-contract-token-accounting` | complete | Enforce canonical `budget_split` keys, tokenizer-quality guardrails, trace budget fields, budget cascade, and unknown/deprecated-key behavior. |
| `02-latest-user-headroom-impossible-budget` | complete | Protect the latest user message, enforce hard minimum headroom, and return the exact v0 422 reasons for impossible budgets. |
| `03-evidence-wrappers-trust-labels` | complete | Render retrieved evidence as escaped data-only XML/JSON wrappers with source trust labels and no raw prompt interpolation. |
| `04-redaction-profile-timeout-binary-safety` | complete | Expand default redaction fixtures, bounded-time behavior, timeout safety, and binary metadata-only handling. |
| `05-freshness-conflict-semantics` | complete | Add adapter/source-supplied freshness fields, conflict warnings, and honest no-independent-current-source behavior. |
| `06-phase-verification-evidence` | complete | Run focused/full verification and update compliance matrix, Section 24 mapping, findings, progress, and roadmap evidence. |

## Expected File Touches

| Area | Expected files |
|---|---|
| Context prepare contract | `mneme_service/app.py`, `mneme_service/schemas.py` |
| Redaction/security | `mneme_service/security.py`, possibly `mneme_service/config.py` for timeout/config exposure |
| Retrieval/freshness | `mneme_service/app.py`, retrieval trace helpers |
| Tests | `tests/test_context_prepare.py`, `tests/test_context_assembly.py`, `tests/test_retrieval.py`, `tests/test_mcp_contract.py`, `tests/test_openapi.py`, `tests/test_contract.py` |
| Evidence | `docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`, `.planning/progress.md`, this plan tree |

## Required Verification Commands

- Focused context/security:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_retrieval.py tests/test_mcp_contract.py -q`
- OpenAPI/contract if schemas change:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py tests/test_contract.py -q`
- Phase 6 focused gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_retrieval.py tests/test_mcp_contract.py tests/test_openapi.py tests/test_contract.py -q`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Verification Gates

- `budget_split` accepts only canonical keys and rejects unknown keys.
- Deprecated `policy.headroom_ratio` is normalized with
  `DEPRECATED_FIELD_NORMALIZED`, or strict clients receive the specified 422.
- STANDARD/QUALITY model-bound prepare must not claim safety with only
  `CHAR_APPROXIMATE` tokenization.
- Latest user-authored message is never silently truncated or dropped.
- Impossible budgets return `LATEST_USER_MESSAGE_EXCEEDS_BUDGET` or
  `MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET` as applicable.
- Evidence wrappers escape user/memory content and label source trust.
- Redaction handles default secret classes, multiline inputs, timeout failure
  posture, and binary metadata-only cases without persisting unredacted
  plaintext after timeout.
- Freshness is adapter/source supplied; Mneme core must not claim independent
  current filesystem/git verification.
- Every Phase 6 Section 24 mapping must either pass directly or be recorded as
  an explicit residual gap.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 11, 14.13 | verified for Phase 6 scope | Task 01 added canonical budget keys/defaults, unknown-key rejection, deprecated headroom normalization, budget trace fields, and char-approximate warning behavior for changed STANDARD/QUALITY prepare. Task 02 added latest-user hard protection and exact impossible-budget 422 reasons. S24-20 remains a tokenizer-quality residual recorded in the matrix. |
| Sections 14.14, 17.2, 17.3 | verified for Phase 6 scope | Task 03 added XML data-only wrappers for retrieved evidence and additive trace `source_trust`; Task 04 added expanded default redaction coverage, foreground `REDACTION_TIMEOUT`, positive `max_redaction_time_ms` validation, and binary `BYTES_REF` metadata-only marking; Task 05 added source-supplied freshness propagation and explicit conflict drops/warnings. |
| CM-021, CM-047, CM-048, CM-053, CM-054 | verified for Phase 6 scope | Matrix updated in Task 06 with Phase 6 evidence. CM-048 moved from `MISSING` to `PARTIAL`; Phase 6 summary counts are `COMPLIANT=6`, `PARTIAL=58`, `MISSING=0`, `UNCLEAR=0`, `OUT_OF_SCOPE/FUTURE=1`. |
| S24-18-22, 35-36, 55, 69-70, 89, 95-96, 99, 104, 115, 119 | verified for Phase 6 scope | Section 24 mapping updated: S24-35/36/115 are now marked compliant for their bucket; context budget/wrapper/freshness/redaction/binary metadata tests are recorded; S24-20 remains a residual partial. |

**Compliance Status: VERIFIED FOR PHASE 6 SCOPE**

## Planning Evidence

- Spark worker `019ef590-cf31-7bd2-9c40-d12a5ca085ab` performed a read-only
  Phase 6 stub audit and recommended the budget -> latest-user -> wrappers ->
  redaction -> freshness order.
- Parent review adopted the ordering and added `06-phase-verification-evidence`
  to keep matrix/Section 24 updates explicit before Phase 6 closes.
