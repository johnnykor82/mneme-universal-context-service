# Plan: 02-readiness-capabilities-contract

## Level

task

## Parent

`.planning/work/04-session-lifecycle-readiness-retention/plan.md`

## Status

complete

## Goal

Align readiness behavior, capabilities, and OpenAPI schemas with the session
lifecycle support implemented in this phase.

## Spec Coverage

| Req ID | Requirement Summary |
|---|---|
| Section 14.1 | `/v1/readiness/session` distinguishes auth, missing session, no evidence, provider-free session-only checks |
| Sections 12.6, 20 | Typed request/response schemas in OpenAPI |
| CM-034, CM-058, CM-062 | Capabilities/OpenAPI/test mapping |
| S24-59, 84, 111 | Readiness required tests |

## Active Subtask

Active Subtask: none

## Planned Steps

- [x] Add/adjust focused readiness tests for missing auth, unknown session,
  `NO_EVIDENCE`, visible session-only success, and provider-free behavior.
- [x] Ensure `require_evidence=false` does not call embedding/reranker/LLM
  providers and returns `200 ok=true` for an existing visible session.
- [x] Ensure `require_evidence=true` returns `412 FAILED_PRECONDITION` with
  `details.reason=NO_EVIDENCE` when required evidence is absent.
- [x] Update typed readiness/capabilities/OpenAPI schemas where needed.
- [x] Run focused readiness/OpenAPI tests and compile check.

## Evidence

| Gate | Result |
|---|---|
| Spark inspection | Spark worker `019ef547-ff05-7143-809b-05c210e40924` identified missing readiness test assertions for readiness 404, `require_evidence=false`, and provider-free behavior. |
| Targeted readiness/OpenAPI | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py::test_session_readiness_requires_auth_session_and_evidence tests/test_contract.py::test_readiness_require_evidence_false_checks_session_only_without_provider_calls tests/test_openapi.py::test_openapi_documents_core_route_request_and_response_models -q` -> `3 passed, 1 warning`. |
| Focused contract/OpenAPI | `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q` -> `22 passed, 1 warning`. |
| Compile | `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests` -> passed. |

## Expected File Touches

`mneme_service/app.py`, `mneme_service/schemas.py`, `tests/test_contract.py`,
`tests/test_openapi.py`.

## Verification Commands

- `env TMPDIR=/private/tmp .venv/bin/python -m pytest tests/test_contract.py tests/test_openapi.py -q`
- `env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests`

## Spec Compliance

| Req ID | Requirement Summary | Status | Verification |
|---|---|---|---|
| S24-59 | Readiness distinguishes auth, missing session, and no evidence | verified | `tests/test_contract.py::test_session_readiness_requires_auth_session_and_evidence`; targeted readiness/OpenAPI `3 passed`. |
| S24-84 | `require_evidence=false` checks session only | verified | `tests/test_contract.py::test_readiness_require_evidence_false_checks_session_only_without_provider_calls`; targeted readiness/OpenAPI `3 passed`. |
| S24-111 | Provider-free readiness makes no provider calls | verified | Same provider-call guard monkeypatch test; focused contract/OpenAPI `22 passed`. |

**Compliance Status: VERIFIED**

## Errors

| Attempt | Command/Action | Error | Next Approach |
|---|---|---|---|
