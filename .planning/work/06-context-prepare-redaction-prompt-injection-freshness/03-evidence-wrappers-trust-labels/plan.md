# Plan: 03-evidence-wrappers-trust-labels

## Level

task

## Parent

`.planning/work/06-context-prepare-redaction-prompt-injection-freshness/plan.md`

## Status

complete

## Goal

Render retrieved memory/evidence as escaped data-only wrappers with explicit
source trust labels so memory content cannot be raw prompt instructions.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Sections 14.13, 17.3 | Context evidence rendering and prompt-injection defense |
| CM-047, CM-054 | Trusted evidence wrapper and prompt-injection gaps |
| S24-35, S24-36, S24-69, S24-115 | Wrapper/escaping/redaction safety tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add RED tests with hostile memory content that attempts XML/JSON wrapper
  break-out or instruction injection.
- [x] Add RED tests that selected evidence carries source trust labels.
- [x] Implement escaped data-only rendering for context evidence while keeping
  existing request-only semantics.
- [x] Ensure wrapper metadata is visible in traces without leaking forbidden
  project/session details.
- [x] Run targeted context/MCP tests and record exact results.
- [x] Update this plan's Spec Compliance table and progress.

## Expected File Touches

`mneme_service/app.py`, `mneme_service/security.py`,
`tests/test_context_prepare.py`, `tests/test_context_assembly.py`,
`tests/test_mcp_contract.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_context_prepare.py tests/test_context_assembly.py tests/test_mcp_contract.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`
- `git diff --check`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| Sections 14.13, 17.3 / CM-047, CM-054 | Evidence wrappers escape untrusted data and label source trust | complete | `test_context_prepare_wraps_retrieved_evidence_as_untrusted_xml_data`, `test_context_prepare_trace_records_retrieved_evidence_source_trust`; full suite `219 passed, 1 warning`. |
| S24-35, S24-36, S24-69, S24-115 | Required wrapper/prompt-injection tests are covered | partial | S24-35 and S24-69 covered for retrieved evidence wrappers and XML escaping. S24-36/S24-115 remain Task 04 redaction-profile/timeout work. |

**Compliance Status: COMPLETE FOR TASK 03 WITH REDACTION RESIDUALS RECORDED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
