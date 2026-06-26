# Plan: 09-residual-contract-fix-batch-f

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Audit the remaining segmentation drift residual cluster and implement only a
bounded, low-risk slice if one exists. If full compliance requires broad
segmentation architecture work, record that as a real blocker/scope decision.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.5.1, 14.6, 14.11 | Intent/routing intelligence, automatic segmentation, drift scoring, and trusted adapter domain-shift metadata |
| CM-039, CM-040, CM-047, CM-062 | Routing/segment/context residuals and Section 24 mapping |
| S24-100, S24-106, S24-107 | Segment drift trace metadata, drift score components, and trusted adapter tool-domain-shift metadata |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Use Spark read-only inspection to classify S24-100/106/107 as bounded
  fix(es), stale matrix/test evidence, or broad blocker.
- [x] If bounded, add focused failing tests for the missing drift metadata or
  score component.
- [x] Implement minimal code only for the bounded slice.
- [x] Run focused and touched-area verification.
- [x] Update matrix evidence and this plan's Spec Compliance table, or record a
  real blocker if the remaining work is architectural.

## Expected File Touches

Likely `tests/test_segments.py`, possibly `mneme_service/app.py`,
`mneme_service/segments.py`, `mneme_service/classifier.py`,
`docs/MNEME_V0_COMPLIANCE_MATRIX.md`, `.planning/findings.md`,
`.planning/progress.md`.

## Verification Commands

- Focused:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_session_drift.py tests/test_retrieval.py -q -k "drift or domain"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_session_drift.py tests/test_retrieval.py tests/test_contract.py -q`
- Full confidence gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| CM-039, CM-040, CM-062 / S24-100, S24-106, S24-107 | Segment drift metadata/scoring/domain shift residual | ✓ met | `tests/test_segments.py::test_trusted_tool_domain_shift_contributes_to_segment_drift_score_trace`; focused RED -> `1 failed, 9 deselected, 1 warning`; focused GREEN -> `1 passed, 9 deselected, 1 warning`; touched-area gate -> `59 passed, 1 warning`; full suite -> `267 passed, 1 warning`; compileall and diff hygiene passed. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
