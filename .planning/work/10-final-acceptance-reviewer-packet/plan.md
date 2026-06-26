# Plan: 10-final-acceptance-reviewer-packet

## Level

phase

## Parent

`.planning/roadmap.md`

## Status

complete

## Goal

Prove Mneme fully complies with `docs/MNEME_STANDALONE_SPEC.md` Final v0.7.5
and produce the final reviewer packet.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 23-25 | Testing, required contract tests, traceability |
| Sections 27-30 | Gap register, reviewer checklist, approval gate |
| CM-012, CM-061, CM-062, CM-063, CM-065 | Acceptance and review readiness rows |

## Active Task

Active Task: none

## Tasks

| Task | Status | Purpose |
|---|---|---|
| `01-residual-matrix-section24-audit` | complete | Audit every remaining `PARTIAL` matrix row and Section 24 partial row into already-covered, real residual fix, or explicit deferral candidate. |
| `02-residual-contract-fix-batch-a` | complete | Implement the first bounded batch of real residual contract fixes found by Task 01. |
| `03-residual-contract-fix-batch-b` | complete | Implement the second bounded batch of real residual contract fixes or, if no code fixes remain, matrix/doc traceability cleanup. |
| `06-residual-contract-fix-batch-c` | complete | Implement a narrow idempotency residual fix for reindex cancel `Idempotency-Key` ledger coverage. |
| `07-residual-contract-fix-batch-d` | complete | Implement a narrow Section 24 segment enum validation residual fix. |
| `08-residual-contract-fix-batch-e` | complete | Audit and close the narrow S24-105 memory-read summary/evidence-edge residual. |
| `09-residual-contract-fix-batch-f` | complete | Audit the remaining segmentation drift metadata/scoring/domain-shift residual cluster. |
| `10-residual-contract-fix-batch-g` | complete | Close the narrow S24-8 turn-complete final status residual. |
| `11-residual-contract-fix-batch-h` | complete | Close the narrow S24-109/S24-119 execution-state hash and compression-trace residuals. |
| `12-residual-contract-fix-batch-i` | complete | Close the narrow S24-95/S24-96/S24-104 indexing-compression evidence residuals. |
| `13-residual-contract-fix-batch-j` | complete | Close the S24-26/S24-27/S24-29/S24-78 session-discovery pagination and no-leak residuals. |
| `14-residual-contract-fix-batch-k` | complete | Close the S24-59/S24-84 readiness provider opt-in/status residuals. |
| `15-residual-contract-fix-batch-l` | complete | Close the S24-2/S24-3/S24-48/S24-49/S24-91/S24-92 export `include_audit` residual. |
| `16-residual-contract-fix-batch-m` | complete | Close the S24-44 trace/cost REST typed schema residual. |
| `17-residual-contract-fix-batch-n` | complete | Close the S24-33 test-only audit-disable daemon config residual. |
| `18-residual-contract-fix-batch-o` | complete | Close the S24-38/S24-45 cost-report baseline methodology residual. |
| `19-residual-contract-fix-batch-p` | complete | Close the S24-19 context-prepare budget-cascade contract-proof residual. |
| `20-residual-contract-fix-batch-q` | complete | Close the S24-113 writer-queue retryable 429 contract-proof residual. |
| `21-residual-contract-fix-batch-r` | complete | Close the S24-25 scoped GLOBAL search isolation and S24-58 batch-first burst ingestion contract-proof residuals. |
| `22-residual-contract-fix-batch-s` | complete | Close the S24-43/S24-85 OpenAPI examples and public core schema residual. |
| `23-residual-contract-fix-batch-t` | complete | Close the S24-67 startup automatic retention sweep residual. |
| `24-residual-contract-fix-batch-u` | complete | Close the S24-86 forced active retention cleanup in-flight-read conflict residual. |
| `25-residual-contract-fix-batch-v` | complete | Close the S24-37/S24-39/S24-68/S24-75/S24-87/S24-111 provider/readiness/reindex traceability residual. |
| `26-residual-contract-fix-batch-w` | complete | Close the S24-46/S24-50/S24-67/S24-74/S24-86 retention traceability residual. |
| `27-residual-contract-fix-batch-x` | complete | Close the remaining S24-40/S24-41/S24-42/S24-56/S24-65/S24-71/S24-82/S24-113 storage/concurrency residual. |
| `28-top-level-matrix-audit-batch-y` | complete | Normalize stale CM-002..CM-017 top-level matrix gaps after Section 24 closure. |
| `29-top-level-matrix-audit-batch-z` | complete | Normalize stale CM-019..CM-030 top-level matrix gaps after Section 24 closure. |
| `30-top-level-matrix-audit-batch-aa` | complete | Normalize stale CM-033..CM-048 top-level matrix gaps after Section 24 closure. |
| `31-top-level-matrix-audit-batch-ab` | complete | Normalize stale CM-051..CM-065 top-level matrix gaps after Section 24 closure. |
| `32-residual-contract-fix-batch-ac` | complete | Close narrow typed schema residuals for message and turn OpenAPI contracts. |
| `33-residual-contract-fix-batch-ad` | complete | Close narrow turn-completion derived segment linkage/update residual. |
| `34-residual-contract-fix-batch-ae` | complete | Close narrow turn-completion execution-state/history update residual. |
| `35-residual-contract-fix-batch-af` | complete | Close narrow turn-completion event/graph provenance residual. |
| `36-residual-contract-fix-batch-ag` | complete | Close or retire the remaining turn-completion provider/usage metrics residual. |
| `37-residual-contract-fix-batch-ah` | complete | Add `SEGMENT_ANCHOR` graph edges for segment anchors and narrow graph/segment residuals. |
| `38-residual-contract-fix-batch-ai` | complete | Close or narrow segment `ABANDONED`/`SUPERSEDED` lifecycle residual. |
| `39-residual-contract-fix-batch-aj` | complete | Close or narrow expand-context frontier/branching traversal residual. |
| `40-residual-contract-fix-batch-ak` | complete | Add expand-context result-truncation dropped-count/frontier details. |
| `41-residual-contract-fix-batch-al` | complete | Add a focused mode-specific expand-context traversal behavior. |
| `42-residual-contract-fix-batch-am` | complete | Add explicit `TOOL_CHAIN`/`CAUSAL` graph traversal behavior. |
| `43-residual-contract-fix-batch-an` | complete | Align parent-derived graph edges with canonical `PARENT_CHILD` taxonomy. |
| `44-residual-contract-fix-batch-ao` | complete | Add context-search candidate trace breadth and recency refill behavior. |
| `45-residual-contract-fix-batch-ap` | complete | Add derived `TOOL_INPUT` and automatic `SEGMENT_MEMBER` graph edges. |
| `46-residual-contract-fix-batch-aq` | complete | Add event-ingest redaction provenance metadata. |
| `47-residual-contract-fix-batch-ar` | complete | Add explicit non-text blob extractor policy. |
| `48-residual-contract-fix-batch-as` | complete | Unify context-prepare QUALITY cost-mode downgrade/failure behavior. |
| `49-residual-contract-fix-batch-at` | complete | Prevent readiness evidence checks from accepting query-unrelated recency refill hits. |
| `50-residual-contract-fix-batch-au` | complete | Add age-based forensic audit anchor cleanup primitive for `CM-028`. |
| `51-residual-contract-fix-batch-av` | complete | Replace static provider `last_health` with runtime provider health status for `CM-009`. |
| `52-residual-contract-fix-batch-aw` | complete | Add env/CLI parity for `max_writer_queue_depth` under `CM-017`. |
| `53-residual-contract-fix-batch-ax` | complete | Add SQLite backup/restore verification path for `CM-033`/`CM-056`. |
| `54-residual-contract-fix-batch-ay` | complete | Add owner-only SQLite DB file permission policy for `CM-055`. |
| `55-residual-contract-fix-batch-az` | complete | Add derivative-retention evidence and Section 17.4 at-rest guidance for `CM-055`. |
| `56-residual-contract-fix-batch-ba` | complete | Add CLI `maintenance blob-gc` trigger for `CM-033`/`CM-057`. |
| `57-residual-contract-fix-batch-bb` | complete | Add stop/restart operations runbook guidance for `CM-057`. |
| `58-residual-contract-fix-batch-bc` | complete | Add safe structured HTTP access logs for `CM-057`. |
| `59-residual-contract-fix-batch-bd` | complete | Normalize `CM-033` after blob GC/export/backup evidence closure. |
| `60-residual-contract-fix-batch-be` | complete | Add destructive-migration backup/no-backup startup controls for `CM-056`. |
| `61-residual-contract-fix-batch-bf` | complete | Add env/serve-CLI parity for existing later-phase `Settings` fields under `CM-017`. |
| `62-residual-contract-fix-batch-bg` | complete | Add machine-readable integration-depth capability claims for `CM-013`/`CM-014`. |
| `63-residual-contract-fix-batch-bh` | complete | Add deterministic entity-modifier execution-state lifecycle for `CM-030`. |
| `64-residual-contract-fix-batch-bi` | complete | Complete Codex Stop hook turn lifecycle mapping for `CM-014`. |
| `65-residual-contract-fix-batch-bj` | complete | Add deterministic lexical topic entropy drift component for `CM-039`. |
| `66-top-level-matrix-audit-batch-bk` | complete | Audit whether `CM-005` structured-history residual is stale after later lifecycle work. |
| `67-top-level-matrix-audit-batch-bl` | complete | Audit `CM-002`/`CM-003` top-level service-shape and product-boundary residuals. |
| `68-residual-contract-fix-batch-bm` | complete | Clean up core README release-facing adapter boundary for `CM-003`. |
| `69-config-routing-audit-batch-bn` | complete | Audit remaining `CM-017`/`CM-039` config/routing residuals. |
| `70-residual-contract-fix-batch-bo` | complete | Implement routing config model/validation/runtime propagation for `CM-017`/`CM-039`. |
| `71-residual-contract-fix-batch-bp` | complete | Advertise deterministic delta extraction/entity-modifier support for `CM-030`. |
| `04-final-verification-matrix` | complete | Run full verification and update matrix so every in-scope row is compliant or explicitly user-approved as deferred/future. |
| `73-full-suite-red-fix-batch-br` | complete | Resolve the two stale contract assertions found by the final full-suite gate. |
| `05-reviewer-packet-acceptance` | complete | Assemble reviewer packet and final acceptance evidence. |

## Expected File Touches

`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`, this plan tree, final reviewer packet docs, and any
source/tests identified by Task 01 as real residual implementation gaps.

## Required Verification Commands

- Residual audit evidence:
  `rg -n "\\| CM-[0-9]+ .*\\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- Section 24 residual audit:
  `rg -n "\\| [0-9, ]+ \\| PARTIAL \\|" docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- Full suite:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`
- OpenAPI parse/schema check:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_openapi.py -q`

## Verification Gates

- Every remaining matrix `PARTIAL` row has a concrete disposition.
- Every Section 24 test number 1-119 is implemented, mapped to equivalent
  composite tests, or recorded as an explicit accepted v0 deferral/non-goal.
- No in-scope `BLOCKER` or `HIGH` gap remains open without an implementation
  task or explicit user-approved deferral.
- Full verification passes after final changes.
- Reviewer packet links canonical spec, final matrix, plan evidence, and
  verification results.

## Spec Compliance

| Req ID | Status | Verification Evidence |
|---|---|---|
| Sections 23-25, 27-30 | complete | Final matrix rows closed; reviewer packet created; Section 24 mapping compliant |
| Section 24 tests 1-119 | complete | Required Contract Test Mapping has no `PARTIAL` grouped rows |
| Final matrix all in-scope rows compliant | complete | Matrix summary: `COMPLIANT: 64`, `PARTIAL: 0`, `MISSING: 0`, `OUT_OF_SCOPE/FUTURE: 1` |
| Full verification | complete | Final full suite `332 passed, 1 warning`; compile/OpenAPI/diff gates clean |

**Compliance Status: COMPLETE**
