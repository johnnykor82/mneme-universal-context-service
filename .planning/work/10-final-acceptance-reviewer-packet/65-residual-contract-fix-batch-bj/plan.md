# Plan: 65-residual-contract-fix-batch-bj

## Level

task

## Parent

`.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Status

complete

## Goal

Narrow `CM-039` by replacing the hardcoded segment drift
`topic_entropy: 0.0` placeholder with a deterministic, normalized lexical topic
entropy signal and trace-backed tests.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.5.1 | Drift score includes normalized `topic_entropy`; when topic tags/buckets are unavailable it may be `0`, but implemented signals must be deterministic and traceable. |
| CM-039 | Runtime-neutral routing intelligence, including richer topic-entropy derivation. |
| S24-106 | Combined drift score and component trace evidence. |

## Steps

| Step | Status | Verification |
|---|---|---|
| Add focused failing test for nonzero deterministic topic entropy in segment drift trace | complete | Focused gate after implementation: `1 passed, 10 deselected, 1 warning`. |
| Implement minimal deterministic lexical entropy helper and wire it into drift components | complete | `topic_entropy_from_text()` computes normalized lexical entropy and `/v1/events` drift components use it. |
| Run focused/touched verification and update matrix/planning evidence | complete | Touched-area gate `12 passed, 19 deselected, 1 warning`; compileall and `git diff --check` exit 0. |

## Expected File Touches

- `mneme_service/app.py`
- `tests/test_segments.py`
- `docs/MNEME_V0_COMPLIANCE_MATRIX.md`
- `.planning/findings.md`
- `.planning/progress.md`
- `.planning/work/10-final-acceptance-reviewer-packet/plan.md`

## Verification Commands

- Focused RED/GREEN:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py -q -k "topic_entropy or drift_score_trace"`
- Touched-area gate:
  `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_segments.py tests/test_classifier.py tests/test_retrieval.py -q -k "drift or classifier or score_breakdown"`
- Compile:
  `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- Diff hygiene:
  `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Section 14.5.1 / CM-039 / S24-106 | Deterministic normalized topic entropy contributes to drift score trace | ✓ met | `tests/test_segments.py::test_trusted_tool_domain_shift_contributes_to_segment_drift_score_trace`; focused gate `1 passed, 10 deselected, 1 warning`; touched gate `12 passed, 19 deselected, 1 warning`. |

**Compliance Status: VERIFIED**
