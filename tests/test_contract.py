from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import mneme_service.app as mneme_app
import mneme_service.security as mneme_security
from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings, StaticTokenSettings
from mneme_service.storage import StorageBusy
from mneme_service.tool_names import TOOL_NAMES


TOKEN = "test-token"


def client(
    tmp_path: Path,
    *,
    max_event_content_bytes: int = 1_048_576,
    max_redaction_time_ms: int = 250,
    retention_sweep_on_session_close: bool = True,
) -> TestClient:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        insecure_dev=False,
        max_event_content_bytes=max_event_content_bytes,
        max_redaction_time_ms=max_redaction_time_ms,
        retention_sweep_on_session_close=retention_sweep_on_session_close,
    )
    return TestClient(create_app(settings))


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def approx_tokens(value: str) -> int:
    return max(1, (len(value) + 3) // 4) if value else 0


class ReadinessEmbeddingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        self.calls += 1
        return [_readiness_vector(text) if text.strip() else None for text in texts]


class RuntimeFailingEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        return [None for _ in texts]


def _readiness_vector(text: str) -> list[float]:
    lowered = text.lower()
    if "oauth" in lowered or "auth" in lowered or "authentication" in lowered or "refresh" in lowered:
        return [1.0, 0.0, 0.0]
    return [0.0, 1.0, 0.0]


def start_session(
    api: TestClient,
    session_id: str = "session-1",
    runtime: str = "HERMES",
    *,
    project_id: str = "project-1",
    metadata: dict | None = None,
) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": runtime,
            "project_id": project_id,
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-09T12:00:00Z",
            "metadata": metadata if metadata is not None else {"cwd": "/repo"},
            "privacy": {
                "project_isolation_key": project_id,
                "retention_days": 30,
                "redaction_profile": "DEFAULT",
                "redaction_policy": "IRREVERSIBLE",
            },
        },
    )
    assert response.status_code == 200, response.text


def event(
    event_id: str,
    text: str,
    *,
    session_id: str = "session-1",
    turn_id: str = "turn-1",
    event_type: str = "TOOL_OUTPUT",
    role: str = "TOOL",
    parent_event_ids: list[str] | None = None,
    timestamp: str = "2026-06-09T12:00:01Z",
) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": session_id,
        "turn_id": turn_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": role,
        "type": event_type,
        "timestamp": timestamp,
        "content": {"format": "TEXT", "text": text},
        "tool": {"name": "exec_command", "call_id": "tool-call-1"},
        "parent_event_ids": parent_event_ids or [],
        "metadata": {"authorization": "Bearer sk-test-secret"},
    }


def ingest(api: TestClient, events: list[dict], session_id: str = "session-1"):
    return api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )


def test_auth_health_capabilities_and_session_idempotency(tmp_path: Path) -> None:
    api = client(tmp_path)

    assert api.get("/v1/health").status_code == 200
    assert api.get("/v1/capabilities").status_code == 401

    capabilities = api.get("/v1/capabilities", headers=auth_headers())
    assert capabilities.status_code == 200
    body = capabilities.json()
    assert body["default_cost_mode"] == "STANDARD"
    assert body["supports_embeddings"] is False
    assert body["supports_mcp_tools"] is True
    assert body["mcp_tools"] == list(TOOL_NAMES)
    assert body["delta_extraction"]["enabled"] is True
    assert body["delta_extraction"]["schema_version"] == "mneme.entity_modifier.v0"
    assert body["delta_extraction"]["sources"] == ["DETERMINISTIC_PATTERN"]
    assert body["delta_extraction"]["provider_guarded_enabled"] is False
    assert body["delta_extraction"]["automatic_update_scope"] == ["execution_state.active_entities"]
    assert body["integration_depth"] == {
        "max_supported": "EVENT_INGEST",
        "supported_levels": ["TOOLS_ONLY", "EVENT_INGEST"],
        "unsupported_or_future": ["PREPARE_INPUT", "CONTEXT_ENGINE", "COMPACTION_OWNER", "FULL_RUNTIME"],
        "supports_prepare_input": False,
        "supports_context_engine": False,
        "supports_compaction_owner": False,
        "supports_full_runtime": False,
        "adapter_claims": {
            "rest_api": {
                "level": "EVENT_INGEST",
                "host_lifecycle": [
                    "bootstrap_session",
                    "ingest_events",
                    "after_model_response",
                    "complete_turn",
                ],
                "context_prepare": "REQUEST_ONLY_ENDPOINT",
                "writes_enabled_by_default": True,
            },
            "mcp": {
                "level": "TOOLS_ONLY",
                "host_lifecycle": [],
                "context_prepare": "MANUAL_TOOL",
                "writes_enabled_by_default": False,
            },
            "codex_hooks": {
                "level": "EVENT_INGEST",
                "host_lifecycle": ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop"],
                "context_prepare": "NOT_HOST_PRE_MODEL_REQUEST",
                "writes_enabled_by_default": False,
            },
            "codex_context_preview": {
                "level": "TOOLS_ONLY",
                "host_lifecycle": [],
                "context_prepare": "PREVIEW_ONLY",
                "writes_enabled_by_default": False,
            },
        },
    }
    assert "mneme.event.v0" in body["supported_schema_versions"]["event"]

    start_session(api)
    again = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "started_at": "2026-06-09T12:00:00Z",
        },
    )
    assert again.status_code == 200
    assert again.json()["created"] is False


def test_metrics_and_reindex_routes_require_auth_and_return_contract_shapes(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                insecure_dev=False,
                reindex_enqueue_when_provider_unavailable=True,
            )
        )
    )

    assert api.get("/v1/metrics").status_code == 401
    metrics = api.get("/v1/metrics", headers=auth_headers())
    assert metrics.status_code == 200, metrics.text
    assert metrics.headers["content-type"].startswith("text/plain")
    assert "mneme_startup_integrity_status 1" in metrics.text
    assert TOKEN not in metrics.text

    assert api.post("/v1/maintenance/reindex", json={"scope": "PROJECT"}).status_code == 401
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={
            "scope": "PROJECT",
            "project_isolation_key": "project-1",
            "statuses": ["PENDING", "FAILED"],
        },
    )
    assert created.status_code == 200, created.text
    job = created.json()
    assert job["schema_version"] == "mneme.reindex_job.v0"
    assert job["scope"] == "PROJECT"
    assert job["project_isolation_key"] == "project-1"
    assert job["statuses"] == ["PENDING", "FAILED"]
    assert job["status"] == "WAITING_FOR_PROVIDER"
    assert job["progress"] == {
        "candidate_count": 0,
        "processed_count": 0,
        "failed_count": 0,
    }

    polled = api.get(f"/v1/maintenance/reindex/{job['job_id']}", headers=auth_headers())
    assert polled.status_code == 200, polled.text
    assert polled.json()["job_id"] == job["job_id"]

    missing = api.get("/v1/maintenance/reindex/missing-job", headers=auth_headers())
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    cancelled = api.post(
        f"/v1/maintenance/reindex/{job['job_id']}/cancel",
        headers=auth_headers(),
        json={"reason": "contract test"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "CANCELLED"


def test_get_session_returns_redacted_summary(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-redacted")

    accepted = ingest(
        api,
        [event("event-redacted", "secret marker sk-redacted-token", session_id="session-redacted")],
        session_id="session-redacted",
    )
    assert accepted.status_code == 200, accepted.text

    response = api.get("/v1/sessions/session-redacted", headers=auth_headers())
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["session_id"] == "session-redacted"
    assert "sk-redacted-token" not in str(body)
    assert "[REDACTED]" in str(body)


def test_event_ingest_redacts_default_secret_profile_before_persistence_and_search(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-secret-profile")
    secrets = {
        "bearer": "Bearer bearer-secret-token-123",
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtbmVtZSJ9.signaturesignature",
        "aws": "AKIAIOSFODNN7EXAMPLE",
        "github": "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "google": "AIzaSyD-example-google-api-key-token",
        "pem": "-----BEGIN PRIVATE KEY-----\nsecret-private-key-body\n-----END PRIVATE KEY-----",
        "env": "CLIENT_SECRET=client-secret-value",
        "db": "postgres://mneme:db-secret@example.test/mneme",
    }
    secret_event = event(
        "event-secret-profile",
        "redaction fixture\n" + "\n".join(secrets.values()),
        session_id="session-secret-profile",
    )
    secret_event["metadata"] = {
        "nested": {
            "api_key": "nested-api-key-secret",
            "client_secret": "nested-client-secret",
            "credential_type": "oauth",
            "token_budget": 512,
        }
    }

    accepted = ingest(api, [secret_event], session_id="session-secret-profile")
    assert accepted.status_code == 200, accepted.text

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-secret-profile", "event_id": "event-secret-profile"},
    )
    searched = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-secret-profile", "query": "redaction fixture", "top_k": 3},
    )

    assert fetched.status_code == 200, fetched.text
    assert searched.status_code == 200, searched.text
    exposed = f"{fetched.json()} {searched.json()}"
    for secret in secrets.values():
        assert secret not in exposed
    assert "nested-api-key-secret" not in exposed
    assert "nested-client-secret" not in exposed
    assert fetched.json()["data"]["event"]["metadata"]["nested"]["credential_type"] == "oauth"
    assert fetched.json()["data"]["event"]["metadata"]["nested"]["token_budget"] == 512
    assert "[REDACTED]" in exposed
    redaction_metadata = fetched.json()["data"]["event"]["ingestion"]["redaction_metadata"]
    assert any(
        item["kind"] == "SECRET_PATTERN"
        and item["field"] == "content.text"
        and item["hash"].startswith("sha256:")
        for item in redaction_metadata
    )
    assert any(
        item["kind"] == "SENSITIVE_KEY"
        and item["field"] == "metadata.nested.api_key"
        and item["hash"].startswith("sha256:")
        for item in redaction_metadata
    )


def test_event_ingest_omits_redaction_metadata_when_no_redaction_needed(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-no-redaction")
    clean_event = event("event-no-redaction", "plain implementation note", session_id="session-no-redaction")
    clean_event.pop("metadata", None)
    accepted = ingest(
        api,
        [clean_event],
        session_id="session-no-redaction",
    )
    assert accepted.status_code == 200, accepted.text

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-no-redaction", "event_id": "event-no-redaction"},
    )

    assert fetched.status_code == 200, fetched.text
    assert "redaction_metadata" not in fetched.json()["data"]["event"]["ingestion"]


def test_event_ingest_redaction_timeout_rejects_without_echoing_plaintext(tmp_path: Path, monkeypatch) -> None:
    api = client(tmp_path, max_redaction_time_ms=1)
    start_session(api, session_id="session-redaction-timeout")
    original_redact_text = mneme_security.redact_text

    def delayed_redact_text(value: str) -> str:
        time.sleep(0.01)
        return original_redact_text(value)

    monkeypatch.setattr(mneme_security, "redact_text", delayed_redact_text)

    timed_out = ingest(
        api,
        [
            event(
                "event-redaction-timeout",
                "timeout secret sk-timeout-secret",
                session_id="session-redaction-timeout",
            )
        ],
        session_id="session-redaction-timeout",
    )

    assert timed_out.status_code == 422, timed_out.text
    body = timed_out.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]["reason"] == "REDACTION_TIMEOUT"
    assert "sk-timeout-secret" not in str(body)


def test_session_close_is_nondestructive_and_idempotent(tmp_path: Path) -> None:
    api = client(tmp_path)
    session_id = "session-close"
    start_session(api, session_id=session_id)
    headers = {**auth_headers(), "Idempotency-Key": "close-key-1"}
    event_id = "event-before-close"

    accepted = ingest(
        api,
        [event(event_id, "this event should remain after close", session_id=session_id)],
        session_id=session_id,
    )
    assert accepted.status_code == 200, accepted.text

    first = api.post(f"/v1/sessions/{session_id}/close", headers=headers, json={})
    replay = api.post(f"/v1/sessions/{session_id}/close", headers=headers, json={})

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert replay.json() == first.json()

    fetch = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": session_id, "event_id": event_id},
    )
    assert fetch.status_code == 200


def test_session_start_generates_id_only_with_idempotency_key(tmp_path: Path) -> None:
    api = client(tmp_path)
    payload = {
        "schema_version": "mneme.session_start.v0",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "project_id": "project-1",
        "privacy": {"project_isolation_key": "project-1"},
    }

    missing_key = api.post("/v1/sessions/start", headers=auth_headers(), json=payload)
    assert missing_key.status_code != 200, missing_key.text

    headers = {**auth_headers(), "Idempotency-Key": "generate-session-id"}
    first = api.post("/v1/sessions/start", headers=headers, json=payload)
    replay = api.post("/v1/sessions/start", headers=headers, json=payload)

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert first.json()["created"] is True
    assert replay.json() == first.json()
    assert replay.json()["session_id"] == first.json()["session_id"]


def test_session_id_validation_rejects_oversized_or_pathlike_ids(tmp_path: Path) -> None:
    api = client(tmp_path)
    invalid_path_ids = (
        "session%2fwith%2fslash",
        "session%3fwith%3fquestion",
        "session%23with%23hash",
    )

    for bad_id in invalid_path_ids:
        response = api.get(f"/v1/sessions/{bad_id}", headers=auth_headers())
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    long_id = "x" * 300
    oversized = api.get(f"/v1/sessions/{long_id}", headers=auth_headers())
    assert oversized.status_code == 422, oversized.text
    assert oversized.json()["error"]["code"] == "VALIDATION_ERROR"


def test_rest_tool_errors_use_uniform_envelope_for_auth_and_missing_session(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    missing_token = api.post(
        "/v1/tools/context_search",
        json={"query": "pytest", "session_id": "session-1", "top_k": 1},
    )
    assert missing_token.status_code == 401
    missing_body = missing_token.json()
    assert missing_body["ok"] is False
    assert missing_body["warnings"] == []
    assert missing_body["error"]["code"] == "UNAUTHENTICATED"

    invalid_token = api.post(
        "/v1/tools/context_search",
        headers={"Authorization": "Bearer wrong-token"},
        json={"query": "pytest", "session_id": "session-1", "top_k": 1},
    )
    assert invalid_token.status_code == 401
    invalid_body = invalid_token.json()
    assert invalid_body["ok"] is False
    assert invalid_body["warnings"] == []
    assert invalid_body["error"]["code"] == "UNAUTHENTICATED"

    missing_session = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "pytest", "session_id": "missing-session", "top_k": 1},
    )
    assert missing_session.status_code == 404
    missing_session_body = missing_session.json()
    assert missing_session_body["ok"] is False
    assert missing_session_body["warnings"] == []
    assert missing_session_body["error"]["code"] == "NOT_FOUND"
    assert missing_session_body["error"]["details"]["reason"] == "SESSION_ID_NOT_FOUND"


def test_session_readiness_requires_auth_session_and_evidence(tmp_path: Path) -> None:
    api = client(tmp_path)
    rlm_session_id = "019edb86-1d22-78a3-b9e4-e6121c294056"
    start_session(api, session_id=rlm_session_id, runtime="CODEX", project_id="/repo/rlm-orchestrator")

    no_auth = api.post(
        "/v1/readiness/session",
        json={
            "session_id": rlm_session_id,
            "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
        },
    )
    assert no_auth.status_code == 401
    assert no_auth.json()["error"]["code"] == "UNAUTHENTICATED"

    missing_session = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "missing-readiness-session",
            "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
        },
    )
    assert missing_session.status_code == 404
    assert missing_session.json()["error"]["details"]["reason"] == "SESSION_ID_NOT_FOUND"

    no_evidence = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": rlm_session_id,
            "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
            "require_evidence": True,
        },
    )
    assert no_evidence.status_code == 412
    no_evidence_body = no_evidence.json()
    assert no_evidence_body["ok"] is False
    assert no_evidence_body["error"]["code"] == "FAILED_PRECONDITION"
    assert no_evidence_body["error"]["details"]["reason"] == "NO_EVIDENCE"

    accepted = ingest(
        api,
        [
            event(
                "rlm-evidence-1",
                "RLM Orchestrator MVP 1 benchmark evidence project status is ready.",
                session_id=rlm_session_id,
                event_type="CODEX_HOOK",
                role="RUNTIME",
            )
        ],
        session_id=rlm_session_id,
    )
    assert accepted.status_code == 200, accepted.text

    ready = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": rlm_session_id,
            "query": "RLM Orchestrator MVP 1 benchmark evidence project status",
            "require_evidence": True,
            "top_k": 1,
        },
    )
    assert ready.status_code == 200, ready.text
    body = ready.json()
    assert body["ok"] is True
    assert body["data"]["ready"] is True
    assert body["data"]["session_id"] == rlm_session_id
    assert body["data"]["evidence_count"] == 1
    assert body["data"]["checks"] == {
        "authenticated": True,
        "session_found": True,
        "evidence_found": True,
        "provider_calls_allowed": False,
        "provider_calls_used": False,
    }


def test_readiness_require_evidence_false_checks_session_only_without_provider_calls(
    tmp_path: Path,
    monkeypatch,
) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-readiness-session-only")

    def fail_hybrid_context_search(*_args, **_kwargs):
        raise AssertionError("require_evidence=false must not run provider-backed retrieval")

    monkeypatch.setattr(mneme_app, "hybrid_context_search", fail_hybrid_context_search)

    response = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "session-readiness-session-only",
            "query": "no persisted evidence should be required",
            "require_evidence": False,
            "allow_provider_calls": False,
            "top_k": 1,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["ready"] is True
    assert body["data"]["required_check"] == "session_exists"
    assert body["data"]["evidence_count"] == 0
    assert body["data"]["evidence_event_ids"] == []
    assert body["data"]["checks"] == {
        "authenticated": True,
        "session_found": True,
        "evidence_found": False,
        "provider_calls_allowed": False,
        "provider_calls_used": False,
    }


def test_readiness_evidence_false_uses_local_search_without_provider_calls(tmp_path: Path) -> None:
    provider = ReadinessEmbeddingProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="readiness-embedding-test",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=provider,
        )
    )
    start_session(api, session_id="session-readiness-local")
    accepted = ingest(
        api,
        [
            event(
                "event-readiness-local",
                "local readiness evidence is available",
                session_id="session-readiness-local",
                event_type="CODEX_HOOK",
                role="RUNTIME",
            )
        ],
        session_id="session-readiness-local",
    )
    assert accepted.status_code == 200, accepted.text
    calls_after_ingest = provider.calls

    ready = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "session-readiness-local",
            "query": "local readiness evidence",
            "require_evidence": True,
            "allow_provider_calls": False,
            "top_k": 1,
        },
    )

    assert ready.status_code == 200, ready.text
    body = ready.json()
    assert body["data"]["evidence_event_ids"] == ["event-readiness-local"]
    assert body["data"]["checks"]["provider_calls_allowed"] is False
    assert body["data"]["checks"]["provider_calls_used"] is False
    assert provider.calls == calls_after_ingest


def test_readiness_provider_calls_require_explicit_opt_in(tmp_path: Path) -> None:
    provider = ReadinessEmbeddingProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="readiness-embedding-test",
                    base_url="https://embed.example.test/v1",
                ),
            ),
            embedding_provider=provider,
        )
    )
    start_session(api, session_id="session-readiness-provider")
    accepted = ingest(
        api,
        [
            event(
                "event-readiness-provider",
                "oauth callback verifier rotated",
                session_id="session-readiness-provider",
                event_type="CODEX_HOOK",
                role="RUNTIME",
            )
        ],
        session_id="session-readiness-provider",
    )
    assert accepted.status_code == 200, accepted.text
    calls_after_ingest = provider.calls

    no_provider = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "session-readiness-provider",
            "query": "authentication refresh flow",
            "require_evidence": True,
            "allow_provider_calls": False,
            "top_k": 1,
        },
    )
    assert no_provider.status_code == 412
    assert no_provider.json()["error"]["details"]["reason"] == "NO_EVIDENCE"
    assert provider.calls == calls_after_ingest

    with_provider = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "session-readiness-provider",
            "query": "authentication refresh flow",
            "require_evidence": True,
            "allow_provider_calls": True,
            "top_k": 1,
        },
    )

    assert with_provider.status_code == 200, with_provider.text
    body = with_provider.json()
    assert body["data"]["evidence_event_ids"] == ["event-readiness-provider"]
    assert body["data"]["checks"]["provider_calls_allowed"] is True
    assert body["data"]["checks"]["provider_calls_used"] is True
    assert provider.calls == calls_after_ingest + 1


def test_capabilities_shows_provider_last_health_after_embedding_failure_degradation(
    tmp_path: Path,
) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                embeddings=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="readiness-embedding-test",
                    base_url="https://embed.example.test/v1",
                    api_key="sk-embedding-secret",
                ),
            ),
            embedding_provider=RuntimeFailingEmbeddingProvider(),
        )
    )
    start_session(api, session_id="session-provider-health")
    accepted = ingest(
        api,
        [
            event(
                "event-provider-health",
                "oauth callback verifier rotated",
                session_id="session-provider-health",
            )
        ],
        session_id="session-provider-health",
    )
    assert accepted.status_code == 200, accepted.text

    readiness = api.post(
        "/v1/readiness/session",
        headers=auth_headers(),
        json={
            "session_id": "session-provider-health",
            "query": "authentication refresh flow",
            "require_evidence": True,
            "allow_provider_calls": True,
            "top_k": 1,
        },
    )
    assert readiness.status_code == 412, readiness.text

    capabilities = api.get("/v1/capabilities", headers=auth_headers())
    assert capabilities.status_code == 200
    provider = capabilities.json()["providers"]["embeddings"]
    assert provider["available"] is True
    assert provider["last_health"]["status"] == "DEGRADED"
    assert provider["last_health"]["last_error_code"] == "EMBEDDINGS_UNAVAILABLE"
    assert provider["last_health"]["failure_count"] >= 1
    assert "sk-embedding-secret" not in str(provider)


def test_retention_cleanup_skips_active_by_default_and_replays(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-retention-active")

    first = api.post(
        "/v1/sessions/session-retention-active/retention/cleanup",
        headers={**auth_headers(), "Idempotency-Key": "cleanup-active-default"},
        json={},
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["schema_version"] == "mneme.retention_cleanup_result.v0"
    assert body["session_id"] == "session-retention-active"
    assert body["dry_run"] is False
    assert body["force_active_cleanup"] is False
    assert body["active_session_skipped"] is True
    assert body["deleted_counts"]["events"] == 0
    assert "ACTIVE_SESSION_SKIPPED" in body["warnings"]

    replay = api.post(
        "/v1/sessions/session-retention-active/retention/cleanup",
        headers={**auth_headers(), "Idempotency-Key": "cleanup-active-default"},
        json={},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == body


def test_retention_cleanup_uses_ended_session_timestamp_cutoff(tmp_path: Path) -> None:
    api = client(tmp_path, retention_sweep_on_session_close=False)
    start_session(api, session_id="session-retention-ended")
    accepted = ingest(
        api,
        [
            event(
                "retention-old-event",
                "old retained event",
                session_id="session-retention-ended",
                timestamp="2020-01-01T00:00:00Z",
            ),
            event(
                "retention-recent-event",
                "recent retained event",
                session_id="session-retention-ended",
                timestamp="2026-06-09T12:00:01Z",
            ),
        ],
        session_id="session-retention-ended",
    )
    assert accepted.status_code == 200, accepted.text
    closed = api.post("/v1/sessions/session-retention-ended/close", headers=auth_headers())
    assert closed.status_code == 200, closed.text

    cleanup = api.post(
        "/v1/sessions/session-retention-ended/retention/cleanup",
        headers=auth_headers(),
        json={"dry_run": True},
    )
    assert cleanup.status_code == 200, cleanup.text
    body = cleanup.json()
    assert body["dry_run"] is True
    assert body["active_session_skipped"] is False
    assert body["cutoff_timestamp"] < closed.json()["ended_at"]
    assert body["candidate_counts"]["events"] == 1
    assert body["deleted_counts"]["events"] == 0
    assert body["orphan_counts"]["blobs"] == 0


def test_retention_cleanup_requires_visible_scope_and_owner_for_active_force(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        insecure_dev=False,
        static_tokens=(
            StaticTokenSettings(
                name="project-a-adapter",
                token="project-a-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
        ),
    )
    api = TestClient(create_app(settings))
    start_session(api, session_id="session-retention-project-a", project_id="project-a")
    start_session(api, session_id="session-retention-project-b", project_id="project-b")

    scoped_headers = {"Authorization": "Bearer project-a-token"}
    forced_active = api.post(
        "/v1/sessions/session-retention-project-a/retention/cleanup",
        headers=scoped_headers,
        json={"force_active_cleanup": True},
    )
    assert forced_active.status_code == 403
    assert forced_active.json()["error"]["details"]["reason"] == "ACTIVE_SESSION_FORCE_REQUIRES_OWNER"

    cross_project = api.post(
        "/v1/sessions/session-retention-project-b/retention/cleanup",
        headers=scoped_headers,
        json={"dry_run": True},
    )
    assert cross_project.status_code == 403


def test_retention_cleanup_force_active_conflicts_with_in_flight_reads(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-retention-in-flight")

    with api.app.state.in_flight_reads.enter("session-retention-in-flight"):
        blocked = api.post(
            "/v1/sessions/session-retention-in-flight/retention/cleanup",
            headers=auth_headers(),
            json={"force_active_cleanup": True},
        )

    assert blocked.status_code == 409, blocked.text
    body = blocked.json()
    assert body["error"]["code"] == "CONFLICT"
    assert body["error"]["details"]["reason"] == "IN_FLIGHT_READS"
    assert body["error"]["details"]["session_id"] == "session-retention-in-flight"
    assert body["error"]["details"]["in_flight_reads"] == 1


def test_retention_cleanup_deletes_eligible_events_and_orphan_blobs(tmp_path: Path) -> None:
    api = client(tmp_path, retention_sweep_on_session_close=False)
    session_id = "session-retention-delete"
    project_id = "project-retention-delete"
    start_session(api, session_id=session_id, project_id=project_id)
    blob_bytes = b"old blob should be deleted by retention"
    upload = api.post(
        "/v1/blobs",
        headers={
            **auth_headers(),
            "Content-Type": "application/octet-stream",
            "X-Mneme-Session-Id": session_id,
            "X-Mneme-Project-Isolation-Key": project_id,
            "Digest": f"sha-256={hashlib.sha256(blob_bytes).hexdigest()}",
        },
        content=blob_bytes,
    )
    assert upload.status_code == 200, upload.text

    old_event = event(
        "retention-delete-old",
        "",
        session_id=session_id,
        timestamp="2020-01-01T00:00:00Z",
    )
    old_event["content"] = upload.json()["bytes_ref"]
    recent_event = event(
        "retention-delete-recent",
        "recent content must remain",
        session_id=session_id,
        timestamp="2026-06-09T12:00:01Z",
    )
    accepted = ingest(api, [old_event, recent_event], session_id=session_id)
    assert accepted.status_code == 200, accepted.text
    store = api.app.state.store
    with store.write_connect() as conn:
        conn.execute(
            """
            INSERT INTO embedding_index(
              event_id, session_id, segment_id, embedding, embedding_model_id,
              token_count, type, created_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "retention-delete-old",
                session_id,
                "segment-retention-derived",
                b"embedding-bytes",
                "test-model",
                2,
                "event",
                1,
            ),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO event_graph_edges(
              source_event_id, target_event_id, session_id, edge_type, weight, created_at_ms
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "retention-delete-old",
                "retention-delete-recent",
                session_id,
                "PARENT_CHILD",
                0.9,
                1,
            ),
        )
        conn.execute(
            "INSERT INTO traces(trace_id, session_id, turn_id, data, created_at_ms) VALUES (?, ?, ?, ?, ?)",
            (
                "trace-retention-derived",
                session_id,
                None,
                json.dumps({"event_ids": ["retention-delete-old"]}),
                1,
            ),
        )
        conn.execute(
            """
            INSERT INTO state_history(
              session_id, timestamp, goal, current_step, intent_label, decisions_added_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                "2020-01-01T00:00:00Z",
                "old goal",
                "old step",
                "old_intent",
                "[]",
            ),
        )
    closed = api.post(f"/v1/sessions/{session_id}/close", headers=auth_headers())
    assert closed.status_code == 200, closed.text

    cleanup = api.post(
        f"/v1/sessions/{session_id}/retention/cleanup",
        headers=auth_headers(),
        json={"dry_run": False},
    )
    assert cleanup.status_code == 200, cleanup.text
    body = cleanup.json()
    assert body["status"] == "COMPLETED"
    assert body["candidate_counts"]["events"] == 1
    assert body["deleted_counts"]["events"] == 1
    assert body["deleted_counts"]["derived_records"] >= 4
    assert body["deleted_counts"]["graph_edges"] == 1
    assert body["deleted_counts"]["traces"] == 1
    assert body["deleted_counts"]["state_history"] >= 1
    assert body["deleted_counts"]["blobs"] == 1
    assert body["events_deleted"] == 1
    assert body["blobs_deleted"] == 1
    with store.connect() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM embedding_index WHERE event_id = ?",
            ("retention-delete-old",),
        ).fetchone()["n"] == 0
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM event_graph_edges WHERE source_event_id = ? OR target_event_id = ?",
            ("retention-delete-old", "retention-delete-old"),
        ).fetchone()["n"] == 0
        assert conn.execute(
            "SELECT COUNT(*) AS n FROM traces WHERE trace_id = ?",
            ("trace-retention-derived",),
        ).fetchone()["n"] == 0

    old_fetch = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": session_id, "event_id": "retention-delete-old"},
    )
    assert old_fetch.status_code == 404

    recent_fetch = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": session_id, "event_id": "retention-delete-recent"},
    )
    assert recent_fetch.status_code == 200, recent_fetch.text

    missing_blob = api.get(f"/v1/blobs/{upload.json()['blob_id']}", headers=auth_headers())
    assert missing_blob.status_code == 404


def test_delete_preserves_anonymized_forensic_audit_anchors(tmp_path: Path) -> None:
    api = client(tmp_path)
    session_id = "session-delete-anchor"
    event_id = "event-delete-anchor"
    start_session(api, session_id=session_id)
    accepted = ingest(
        api,
        [event(event_id, "secret content must not survive delete", session_id=session_id)],
        session_id=session_id,
    )
    assert accepted.status_code == 200, accepted.text
    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": session_id, "event_id": event_id},
    )
    assert fetched.status_code == 200, fetched.text

    deleted = api.delete(f"/v1/sessions/{session_id}", headers=auth_headers())
    assert deleted.status_code == 200, deleted.text

    anchors = api.app.state.store.list_forensic_anchors()
    assert {anchor["action"] for anchor in anchors} >= {"MEMORY_READ", "SESSION_DELETE"}
    serialized = str(anchors)
    assert session_id not in serialized
    assert event_id not in serialized
    assert "secret content" not in serialized
    assert all(anchor["session_id"].startswith("deleted-session:") for anchor in anchors)
    assert all(anchor["request"] == {} for anchor in anchors)
    assert all(anchor["result"].get("forensic_anchor") is True for anchor in anchors)


def test_forensic_audit_anchors_expire_after_retention_days(tmp_path: Path) -> None:
    api = client(tmp_path)
    old_session_id = "session-delete-anchor-old"
    fresh_session_id = "session-delete-anchor-fresh"
    for session_id in [old_session_id, fresh_session_id]:
        start_session(api, session_id=session_id)
        accepted = ingest(
            api,
            [event(f"event-{session_id}", f"delete anchor evidence {session_id}", session_id=session_id)],
            session_id=session_id,
        )
        assert accepted.status_code == 200, accepted.text
        fetched = api.post(
            "/v1/tools/fetch_event",
            headers=auth_headers(),
            json={"session_id": session_id, "event_id": f"event-{session_id}"},
        )
        assert fetched.status_code == 200, fetched.text
        deleted = api.delete(f"/v1/sessions/{session_id}", headers=auth_headers())
        assert deleted.status_code == 200, deleted.text

    store = api.app.state.store
    anchors = store.list_forensic_anchors()
    old_anchor_ids = [anchor["audit_id"] for anchor in anchors if anchor["session_id"].startswith("deleted-session:")]
    assert len(old_anchor_ids) >= 4
    stale_ids = old_anchor_ids[:2]
    stale_ms = int((time.time() - 3 * 86400) * 1000)
    with store.write_connect() as conn:
        conn.executemany(
            "UPDATE audit_records SET created_at_ms = ? WHERE audit_id = ?",
            [(stale_ms, audit_id) for audit_id in stale_ids],
        )

    result = store.purge_forensic_anchors_older_than(retention_days=1)

    assert result == {"candidate_count": 2, "deleted_count": 2}
    remaining_ids = {anchor["audit_id"] for anchor in store.list_forensic_anchors()}
    assert not set(stale_ids) & remaining_ids
    assert remaining_ids


def test_startup_purges_expired_forensic_audit_anchors(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                audit_forensic_retention_days=1,
            )
        )
    )
    session_id = "session-delete-anchor-startup"
    start_session(api, session_id=session_id)
    accepted = ingest(
        api,
        [event("event-delete-anchor-startup", "startup forensic retention evidence", session_id=session_id)],
        session_id=session_id,
    )
    assert accepted.status_code == 200, accepted.text
    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": session_id, "event_id": "event-delete-anchor-startup"},
    )
    assert fetched.status_code == 200, fetched.text
    deleted = api.delete(f"/v1/sessions/{session_id}", headers=auth_headers())
    assert deleted.status_code == 200, deleted.text

    stale_ms = int((time.time() - 3 * 86400) * 1000)
    with api.app.state.store.write_connect() as conn:
        conn.execute("UPDATE audit_records SET created_at_ms = ?", (stale_ms,))
    assert api.app.state.store.list_forensic_anchors()

    restarted = TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                audit_forensic_retention_days=1,
            )
        )
    )

    assert restarted.app.state.store.list_forensic_anchors() == []


def test_session_close_retention_sweep_is_observable_and_scoped(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-sweep-a", project_id="project-a")
    start_session(api, session_id="session-sweep-b", project_id="project-b")
    assert ingest(
        api,
        [
            event(
                "event-sweep-a-old",
                "old project a content",
                session_id="session-sweep-a",
                timestamp="2020-01-01T00:00:00Z",
            )
        ],
        session_id="session-sweep-a",
    ).status_code == 200
    assert ingest(
        api,
        [
            event(
                "event-sweep-b-old",
                "old project b content",
                session_id="session-sweep-b",
                timestamp="2020-01-01T00:00:00Z",
            )
        ],
        session_id="session-sweep-b",
    ).status_code == 200

    closed = api.post("/v1/sessions/session-sweep-a/close", headers=auth_headers())
    assert closed.status_code == 200, closed.text

    removed = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-sweep-a", "event_id": "event-sweep-a-old"},
    )
    assert removed.status_code == 404

    other_project_retained = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-sweep-b", "event_id": "event-sweep-b-old"},
    )
    assert other_project_retained.status_code == 200, other_project_retained.text

    audits = api.app.state.store.list_audit("session-sweep-a")
    cleanup_audits = [audit for audit in audits if audit["action"] == "RETENTION_CLEANUP"]
    assert len(cleanup_audits) == 1
    audit = cleanup_audits[0]
    assert audit["tool"] == "SYSTEM_DAEMON"
    assert audit["result"]["trigger"] == "SESSION_CLOSE"
    assert audit["result"]["deleted_counts"]["events"] == 1
    assert "old project a content" not in str(audit)


def test_startup_retention_sweep_is_observable_and_scoped(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    first = TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                retention_sweep_on_startup=False,
                retention_sweep_on_session_close=False,
            )
        )
    )
    start_session(first, session_id="session-startup-ended", project_id="project-startup-a")
    start_session(first, session_id="session-startup-active", project_id="project-startup-b")
    assert ingest(
        first,
        [
            event(
                "event-startup-ended-old",
                "startup sweep should remove this old ended event",
                session_id="session-startup-ended",
                timestamp="2020-01-01T00:00:00Z",
            )
        ],
        session_id="session-startup-ended",
    ).status_code == 200
    assert ingest(
        first,
        [
            event(
                "event-startup-active-old",
                "startup sweep should keep active session content",
                session_id="session-startup-active",
                timestamp="2020-01-01T00:00:00Z",
            )
        ],
        session_id="session-startup-active",
    ).status_code == 200
    closed = first.post("/v1/sessions/session-startup-ended/close", headers=auth_headers())
    assert closed.status_code == 200, closed.text

    restarted = TestClient(
        create_app(
            Settings(
                db_path=db_path,
                auth_token=TOKEN,
                retention_sweep_on_startup=True,
                retention_sweep_on_session_close=False,
            )
        )
    )

    removed = restarted.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-startup-ended", "event_id": "event-startup-ended-old"},
    )
    assert removed.status_code == 404
    active_retained = restarted.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-startup-active", "event_id": "event-startup-active-old"},
    )
    assert active_retained.status_code == 200, active_retained.text

    audits = restarted.app.state.store.list_audit("session-startup-ended")
    startup_audits = [
        audit
        for audit in audits
        if audit["action"] == "RETENTION_CLEANUP" and audit["result"].get("trigger") == "STARTUP"
    ]
    assert len(startup_audits) == 1
    assert startup_audits[0]["tool"] == "SYSTEM_DAEMON"
    assert startup_audits[0]["result"]["deleted_counts"]["events"] == 1
    assert "startup sweep should remove" not in str(startup_audits[0])

    metrics = restarted.get("/v1/metrics", headers=auth_headers())
    assert metrics.status_code == 200, metrics.text
    assert "mneme_retention_sweeps_total 1" in metrics.text


def test_event_ingestion_redaction_duplicate_conflict_and_unknown_session(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    first = ingest(api, [event("event-1", "pytest failed with sk-test-secret in output")])
    assert first.status_code == 200, first.text
    assert first.json()["accepted"] == 1
    assert first.json()["duplicates"] == 0

    duplicate = ingest(api, [event("event-1", "pytest failed with sk-test-secret in output")])
    assert duplicate.status_code == 200
    assert duplicate.json()["accepted"] == 0
    assert duplicate.json()["duplicates"] == 1

    conflict = ingest(api, [event("event-1", "different immutable content")])
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"

    unsupported = ingest(api, [{**event("event-2", "bad schema"), "schema_version": "mneme.event.v9"}])
    assert unsupported.status_code == 400
    assert unsupported.json()["error"]["code"] == "BAD_REQUEST"

    unknown = ingest(api, [event("event-x", "unknown", session_id="missing-session")], session_id="missing-session")
    assert unknown.status_code == 404

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "pytest secret", "session_id": "session-1", "scope": "SESSION", "top_k": 10},
    )
    assert search.status_code == 200
    payload = search.json()
    assert payload["ok"] is True
    assert "sk-test-secret" not in str(payload)
    assert "[REDACTED]" in str(payload)


def test_session_discovery_resolves_codex_session_without_guessing(tmp_path: Path) -> None:
    api = client(tmp_path)
    project_path = "/repo/rlm-orchestrator"
    start_session(
        api,
        session_id="019ec6c0-65a9-7bf3-9faa-830730a560c5",
        runtime="CODEX",
        project_id=project_path,
        metadata={"cwd": project_path, "thread_id": "thread-rlm-1", "source": "codex_hook"},
    )

    listed = api.post(
        "/v1/tools/list_sessions",
        headers=auth_headers(),
        json={"query": "rlm-orchestrator", "limit": 5},
    )
    assert listed.status_code == 200, listed.text
    sessions = listed.json()["data"]["sessions"]
    assert [item["session_id"] for item in sessions] == ["019ec6c0-65a9-7bf3-9faa-830730a560c5"]
    assert sessions[0]["metadata"]["cwd"] == project_path

    by_project = api.post(
        "/v1/tools/resolve_session",
        headers=auth_headers(),
        json={"project_path": project_path},
    )
    assert by_project.status_code == 200, by_project.text
    assert by_project.json()["data"]["resolved_session_id"] == "019ec6c0-65a9-7bf3-9faa-830730a560c5"

    by_thread = api.post(
        "/v1/tools/resolve_session",
        headers=auth_headers(),
        json={"thread_id": "thread-rlm-1"},
    )
    assert by_thread.status_code == 200, by_thread.text
    assert by_thread.json()["data"]["resolved_session_id"] == "019ec6c0-65a9-7bf3-9faa-830730a560c5"

    guessed = api.post(
        "/v1/tools/get_execution_state",
        headers=auth_headers(),
        json={"session_id": "rlm-orchestrator"},
    )
    assert guessed.status_code == 404
    details = guessed.json()["error"]["details"]
    assert details["session_id"] == "rlm-orchestrator"
    assert details["reason"] == "SESSION_ID_NOT_FOUND"
    assert details["discovery_tools"] == ["resolve_session", "list_sessions"]
    assert details["candidate_sessions"][0]["session_id"] == "019ec6c0-65a9-7bf3-9faa-830730a560c5"


def test_resolve_session_best_guess_prefers_exact_project_path_before_recency(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(
        api,
        session_id="session-app-older-exact",
        runtime="CODEX",
        project_id="project-1",
        metadata={"cwd": "/repo/app", "thread_id": "thread-old"},
    )
    start_session(
        api,
        session_id="session-app-newer-prefix",
        runtime="CODEX",
        project_id="project-1",
        metadata={"cwd": "/repo/app-old", "thread_id": "thread-new"},
    )

    resolved = api.post(
        "/v1/tools/resolve_session",
        headers=auth_headers(),
        json={"project_path": "/repo/app", "limit": 5},
    )

    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body["ok"] is True
    assert body["data"]["resolution"] == "AMBIGUOUS"
    assert body["data"]["resolved_session_id"] is None
    assert body["data"]["best_guess_session_id"] == "session-app-older-exact"
    assert [item["session_id"] for item in body["data"]["matches"]][:2] == [
        "session-app-older-exact",
        "session-app-newer-prefix",
    ]
    assert body["warnings"][0]["code"] == "SESSION_RESOLUTION_AMBIGUOUS"
    assert "list_sessions" in body["warnings"][0]["message"]


def test_resolve_session_best_guess_is_null_for_recency_only_ambiguity(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(
        api,
        session_id="session-app-a",
        runtime="CODEX",
        project_id="project-1",
        metadata={"cwd": "/repo/app", "thread_id": "thread-a"},
    )
    start_session(
        api,
        session_id="session-app-b",
        runtime="CODEX",
        project_id="project-1",
        metadata={"cwd": "/repo/app", "thread_id": "thread-b"},
    )

    resolved = api.post(
        "/v1/tools/resolve_session",
        headers=auth_headers(),
        json={"project_path": "/repo/app", "limit": 5},
    )

    assert resolved.status_code == 200, resolved.text
    body = resolved.json()
    assert body["data"]["resolution"] == "AMBIGUOUS"
    assert body["data"]["best_guess_session_id"] is None
    assert body["warnings"][0]["code"] == "SESSION_RESOLUTION_AMBIGUOUS"


def test_session_discovery_filters_and_paginates_without_silent_truncation(tmp_path: Path) -> None:
    api = client(tmp_path)
    for index in range(3):
        start_session(
            api,
            session_id=f"session-page-{index}",
            runtime="CODEX",
            project_id="project-1",
            metadata={"cwd": "/repo/page-proj", "thread_id": f"thread-page-{index}"},
        )
        time.sleep(0.002)

    listed = api.post(
        "/v1/tools/list_sessions",
        headers=auth_headers(),
        json={"project_path": "/repo/page-proj", "page_size": 2},
    )
    assert listed.status_code == 200, listed.text
    first_body = listed.json()
    first_page = first_body["data"]["sessions"]
    assert len(first_page) == 2
    assert first_body["data"]["count"] == 2
    assert first_body["data"]["matches_truncated"] is True
    assert first_body["data"]["next_page_token"]

    second = api.post(
        "/v1/tools/list_sessions",
        headers=auth_headers(),
        json={
            "project_path": "/repo/page-proj",
            "page_size": 2,
            "page_token": first_body["data"]["next_page_token"],
        },
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    second_page = second_body["data"]["sessions"]
    assert len(second_page) == 1
    assert second_body["data"]["matches_truncated"] is False
    assert second_body["data"]["next_page_token"] is None
    all_ids = [item["session_id"] for item in first_page + second_page]
    assert sorted(all_ids) == ["session-page-0", "session-page-1", "session-page-2"]
    assert len(set(all_ids)) == 3

    resolved = api.post(
        "/v1/tools/resolve_session",
        headers=auth_headers(),
        json={"project_path": "/repo/page-proj", "page_size": 2},
    )
    assert resolved.status_code == 200, resolved.text
    resolved_body = resolved.json()
    assert resolved_body["data"]["resolution"] == "AMBIGUOUS"
    assert len(resolved_body["data"]["matches"]) == 2
    assert resolved_body["data"]["matches_truncated"] is True
    assert resolved_body["data"]["next_page_token"]
    assert resolved_body["warnings"][0]["code"] == "SESSION_RESOLUTION_AMBIGUOUS"


def test_not_found_discovery_guidance_is_scoped_and_redacted(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        insecure_dev=False,
        static_tokens=(
            StaticTokenSettings(
                name="project-a-adapter",
                token="project-a-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
        ),
    )
    api = TestClient(create_app(settings))
    start_session(
        api,
        session_id="session-visible-leak",
        project_id="project-a",
        metadata={
            "cwd": "/repo/visible-leak",
            "thread_id": "thread-visible",
            "api_key": "sk-visible-secret",
            "token": "ghp-visible-secret",
            "notes": "hidden diagnostic metadata",
        },
    )
    start_session(
        api,
        session_id="session-hidden-leak",
        project_id="project-b",
        metadata={"cwd": "/repo/hidden-leak", "api_key": "sk-hidden-secret"},
    )

    missing = api.post(
        "/v1/tools/get_execution_state",
        headers={"Authorization": "Bearer project-a-token"},
        json={"session_id": "leak"},
    )

    assert missing.status_code == 404
    details = missing.json()["error"]["details"]
    candidate_ids = [item["session_id"] for item in details["candidate_sessions"]]
    assert candidate_ids == ["session-visible-leak"]
    assert details["candidate_sessions"][0]["metadata"] == {
        "cwd": "/repo/visible-leak",
        "thread_id": "thread-visible",
    }
    serialized = str(details)
    assert "session-hidden-leak" not in serialized
    assert "sk-visible-secret" not in serialized
    assert "ghp-visible-secret" not in serialized
    assert "hidden diagnostic metadata" not in serialized


def test_oversized_inline_requires_owned_bytes_ref(tmp_path: Path) -> None:
    api = client(tmp_path, max_event_content_bytes=12)
    start_session(api)

    too_large = ingest(api, [event("event-large", "this text is too large")])
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    arbitrary_ref_event = event("event-arbitrary-ref", "")
    arbitrary_ref_event["content"] = {
        "format": "BYTES_REF",
        "uri": "file:///tmp/mneme/blob-1",
        "hash": "sha256:abc",
        "size_bytes": 10_000_000,
        "media_type": "text/plain",
    }
    arbitrary = ingest(api, [arbitrary_ref_event])
    assert arbitrary.status_code == 422
    assert arbitrary.json()["error"]["code"] == "VALIDATION_ERROR"

    blob_bytes = b"owned bytes"
    uploaded = api.post(
        "/v1/blobs",
        headers={
            **auth_headers(),
            "Content-Type": "application/octet-stream",
            "X-Mneme-Session-Id": "session-1",
            "X-Mneme-Project-Isolation-Key": "project-1",
            "Digest": f"sha-256={hashlib.sha256(blob_bytes).hexdigest()}",
        },
        content=blob_bytes,
    )
    assert uploaded.status_code == 200, uploaded.text

    bytes_ref_event = event("event-ref", "")
    bytes_ref_event["content"] = uploaded.json()["bytes_ref"]
    accepted = ingest(api, [bytes_ref_event])
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted"] == 1


def test_non_text_bytes_ref_is_stored_as_binary_metadata_only(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api, session_id="session-binary-redaction")
    blob_bytes = b"%PDF-1.7\nbinary-secret-that-must-not-be-inline\n%%EOF"
    uploaded = api.post(
        "/v1/blobs",
        headers={
            **auth_headers(),
            "Content-Type": "application/octet-stream",
            "X-Mneme-Session-Id": "session-binary-redaction",
            "X-Mneme-Project-Isolation-Key": "project-1",
            "Digest": f"sha-256={hashlib.sha256(blob_bytes).hexdigest()}",
        },
        content=blob_bytes,
    )
    assert uploaded.status_code == 200, uploaded.text

    bytes_ref_event = event("event-binary-ref", "", session_id="session-binary-redaction")
    bytes_ref_event["content"] = uploaded.json()["bytes_ref"]
    accepted = ingest(api, [bytes_ref_event], session_id="session-binary-redaction")
    assert accepted.status_code == 200, accepted.text

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-binary-redaction", "event_id": "event-binary-ref"},
    )

    assert fetched.status_code == 200, fetched.text
    body = fetched.json()
    assert body["data"]["event"]["ingestion"]["redaction_scope"] == "BINARY_METADATA_ONLY"
    assert body["data"]["event"]["ingestion"]["extractor_policy"] == "DISABLED"
    assert body["data"]["event"]["content"]["media_type"] == "application/octet-stream"
    assert "binary-secret-that-must-not-be-inline" not in str(body)


def test_memory_tools_audit_memory_read_and_graph_expansion(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    call = event("event-call", "run pytest", event_type="TOOL_CALL")
    output = event(
        "event-output",
        "pytest failure in context assembler with sk-test-secret. second sentence should not be in summary",
        parent_event_ids=["event-call"],
    )
    decision = event("event-decision", "decided to inspect assembler", event_type="DECISION", role="ASSISTANT", parent_event_ids=["event-output"])
    assert ingest(api, [call, output, decision]).status_code == 200

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "assembler failure", "session_id": "session-1", "scope": "SESSION", "top_k": 5},
    )
    assert search.status_code == 200
    search_body = search.json()
    assert search_body["data"]["results"][0]["event_id"] == "event-output"
    trace_id = search_body["trace_id"]
    assert trace_id

    trace = api.get(f"/v1/traces/{trace_id}", headers=auth_headers())
    assert trace.status_code == 200
    trace_body = trace.json()
    assert trace_body["trace_type"] == "MEMORY_READ"
    assert trace_body["tool"] == "context_search"
    assert trace_body["selected_event_ids"] == [item["event_id"] for item in search_body["data"]["results"]]

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-1", "event_id": "event-output", "full": True, "include_neighbors": True},
    )
    assert fetched.status_code == 200
    fetched_body = fetched.json()
    assert fetched_body["data"]["neighbors"]

    fetch_trace = api.get(f"/v1/traces/{fetched_body['trace_id']}", headers=auth_headers())
    assert fetch_trace.status_code == 200
    assert set(fetch_trace.json()["selected_event_ids"]) == {"event-output", "event-call", "event-decision"}

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-1", "seed_event_id": "event-output", "mode": "TOOL_CHAIN", "depth": 2, "max_events": 10},
    )
    assert expanded.status_code == 200
    expanded_ids = {item["event_id"] for item in expanded.json()["data"]["events"]}
    assert {"event-call", "event-output", "event-decision"}.issubset(expanded_ids)

    exported = api.get("/v1/sessions/session-1/export?include_audit=true", headers=auth_headers())
    assert exported.status_code == 200
    exported_body = exported.json()
    assert len(exported_body["audit_records"]) >= 3
    assert any(item["type"] == "MEMORY_READ" for item in exported_body["events"])
    memory_read_events = [item for item in exported_body["events"] if item["type"] == "MEMORY_READ"]
    memory_read_ids = {item["event_id"] for item in memory_read_events}
    evidence_edges = [
        edge
        for edge in exported_body["event_graph_edges"]
        if edge["edge_type"] == "MEMORY_READ_EVIDENCE"
        and edge["source_event_id"] in memory_read_ids
    ]
    assert any(edge["target_event_id"] == "event-output" for edge in evidence_edges)
    assert all(edge["weight"] == 0.8 for edge in evidence_edges)
    state = exported_body["execution_state"]
    assert state["last_tool"] == "expand_context"
    summary = state["last_tool_output_summary"]
    assert summary.startswith("memory_read:expand_context results=")
    assert "top_event=event-output" in summary
    assert "top_type=TOOL_OUTPUT" in summary
    assert "top_excerpt=pytest failure in context assembler with [REDACTED]." in summary
    assert "second sentence" not in summary
    assert "sk-test-secret" not in summary
    assert len(summary.split()) <= 120


def test_audit_disabled_only_by_test_daemon_config_and_not_public_payload(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    assert ingest(api, [event("event-audit-default", "audit default evidence")]).status_code == 200

    public_attempt = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={
            "session_id": "session-1",
            "query": "audit default evidence",
            "disable_audit": True,
            "audit_mode": "DISABLED_TEST_ONLY",
        },
    )

    assert public_attempt.status_code == 200, public_attempt.text
    assert public_attempt.json()["trace_id"]
    exported = api.get("/v1/sessions/session-1/export?include_audit=true", headers=auth_headers())
    body = exported.json()
    assert any(audit["action"] == "MEMORY_READ" for audit in body["audit_records"])
    assert any(item["type"] == "MEMORY_READ" for item in body["events"])

    with pytest.raises(ValueError, match="DISABLED_TEST_ONLY"):
        create_app(
            Settings(
                db_path=tmp_path / "blocked.db",
                auth_token=TOKEN,
                audit_mode="DISABLED_TEST_ONLY",
            )
        )

    disabled = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "disabled.db",
                auth_token=TOKEN,
                audit_mode="DISABLED_TEST_ONLY",
                allow_unaudited_tools_for_tests=True,
            )
        )
    )
    start_session(disabled, session_id="session-disabled")
    assert ingest(
        disabled,
        [event("event-audit-disabled", "audit disabled evidence", session_id="session-disabled")],
        session_id="session-disabled",
    ).status_code == 200

    disabled_search = disabled.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-disabled", "query": "audit disabled evidence"},
    )

    assert disabled_search.status_code == 200, disabled_search.text
    assert disabled_search.json()["trace_id"] is None
    assert disabled.app.state.store.list_audit("session-disabled") == []
    disabled_export = disabled.get(
        "/v1/sessions/session-disabled/export?include_audit=true",
        headers=auth_headers(),
    )
    assert disabled_export.status_code == 200, disabled_export.text
    assert disabled_export.json()["audit_records"] == []
    assert all(item["type"] != "MEMORY_READ" for item in disabled_export.json()["events"])


def test_mneme_cost_report_tool_creates_memory_read_audit_trace_and_updates_state(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    report = api.post(
        "/v1/tools/mneme_cost_report",
        headers=auth_headers(),
        json={"session_id": "session-1"},
    )

    assert report.status_code == 200, report.text
    trace_id = report.json()["trace_id"]
    assert trace_id
    trace = api.get(f"/v1/traces/{trace_id}", headers=auth_headers())
    assert trace.status_code == 200, trace.text
    assert trace.json()["trace_type"] == "MEMORY_READ"
    assert trace.json()["tool"] == "mneme_cost_report"

    exported = api.get("/v1/sessions/session-1/export?include_audit=true", headers=auth_headers())
    assert exported.status_code == 200, exported.text
    body = exported.json()
    assert any(
        audit["action"] == "MEMORY_READ" and audit["tool"] == "mneme_cost_report"
        for audit in body["audit_records"]
    )
    state = body["execution_state"]
    assert state["last_tool"] == "mneme_cost_report"
    assert state["last_tool_output_summary"] == (
        "memory_read:mneme_cost_report results=0 top_event=null "
        "top_type=null top_excerpt="
    )


def test_memory_tool_filters_limits_and_segment_page_size(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    events = [
        event("event-error", "pytest crashed in parser", event_type="ERROR", role="RUNTIME", turn_id="turn-1"),
        event("event-old-error", "pytest older parser error", event_type="ERROR", role="RUNTIME", turn_id="turn-0", timestamp="2026-06-09T11:59:59Z"),
        event("event-output", "pytest output should be hidden from recent recall", event_type="TOOL_OUTPUT", role="TOOL", turn_id="turn-2"),
        event("event-decision", "pytest parser fix chosen", event_type="DECISION", role="ASSISTANT", turn_id="turn-3"),
        event("event-note", "small note", event_type="NOTE", role="ASSISTANT", turn_id="turn-4"),
    ]
    assert ingest(api, events).status_code == 200

    filtered = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={
            "query": "pytest",
            "session_id": "session-1",
            "scope": "SESSION",
            "top_k": 10,
            "filters": {
                "event_types": ["ERROR"],
                "after": "2026-06-09T12:00:00Z",
                "before": "2026-06-09T12:00:02Z",
            },
        },
    )
    assert filtered.status_code == 200
    filtered_results = filtered.json()["data"]["results"]
    assert [item["event_id"] for item in filtered_results] == ["event-error"]
    assert all(item["type"] == "ERROR" for item in filtered_results)

    recent = api.post(
        "/v1/tools/recall_recent",
        headers=auth_headers(),
        json={"session_id": "session-1", "turns": 4, "max_tokens": 12, "include_tool_outputs": False},
    )
    assert recent.status_code == 200
    recent_events = recent.json()["data"]["events"]
    recent_ids = [item["event_id"] for item in recent_events]
    assert all(item["type"] != "TOOL_OUTPUT" for item in recent_events)
    assert sum(approx_tokens(item["snippet"]) for item in recent_events) <= 12
    assert "event-note" in recent_ids
    assert "event-old-error" not in recent_ids

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": "turn-4",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-note"],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "tool_call_count": 1},
        },
    )
    assert completed.status_code == 200

    bad_page_size = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 0, "page_token": None},
    )
    assert bad_page_size.status_code == 422

    segments = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 1, "page_token": None},
    )
    assert segments.status_code == 200
    assert len(segments.json()["data"]["segments"]) <= 1


def test_turn_complete_accepts_failed_interrupted_cancelled_and_rejects_conflicts(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    for status in ("FAILED", "INTERRUPTED", "CANCELLED"):
        payload = {
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": f"turn-{status.lower()}",
            "status": status,
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": [],
            "error": {"code": f"{status}_TEST", "message": f"{status} turn"},
        }
        completed = api.post("/v1/turns/complete", headers=auth_headers(), json=payload)
        replay = api.post("/v1/turns/complete", headers=auth_headers(), json=payload)
        assert completed.status_code == 200, completed.text
        assert replay.status_code == 200, replay.text
        assert replay.json() == completed.json()
        body = completed.json()
        assert body["schema_version"] == "mneme.turn_complete_result.v0"
        assert body["session_id"] == "session-1"
        assert body["turn_id"] == payload["turn_id"]
        assert body["status"] == status

    conflict = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": "turn-failed",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": [],
        },
    )
    assert conflict.status_code == 409

    invalid = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-1",
            "turn_id": "turn-bogus",
            "status": "BOGUS",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["details"]["field"] == "status"


def test_turn_complete_links_event_segment_without_clobbering_lifecycle(tmp_path: Path) -> None:
    api = client(tmp_path)
    session_id = "session-turn-links"
    start_session(api, session_id=session_id)
    stored = ingest(
        api,
        [
            event(
                "event-turn-link-user",
                "Start the linked segment work",
                session_id=session_id,
                turn_id="turn-linked",
                event_type="USER_MESSAGE",
                role="USER",
            )
        ],
        session_id=session_id,
    )
    assert stored.status_code == 200, stored.text

    segments_before = api.get(f"/v1/segments?session_id={session_id}", headers=auth_headers())
    assert segments_before.status_code == 200, segments_before.text
    active_segment = segments_before.json()["segments"][0]
    assert active_segment["status"] == "OPEN"

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": session_id,
            "turn_id": "turn-linked",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-turn-link-user"],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "tool_call_count": 1},
            "outcome": {"summary": "Linked segment completed."},
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["segment_ids"] == [active_segment["segment_id"]]

    fetched = api.get(f"/v1/segments/{active_segment['segment_id']}", headers=auth_headers())
    assert fetched.status_code == 200, fetched.text
    segment = fetched.json()["segment"]
    assert segment["status"] == "OPEN"
    assert segment["title"] == active_segment["title"]
    assert segment["event_count"] == 2
    assert segment["metadata"]["last_turn_id"] == "turn-linked"
    assert segment["metadata"]["last_turn_status"] == "COMPLETED"
    assert segment["metadata"]["last_turn_usage"]["prompt_tokens"] == 10


def test_turn_complete_updates_execution_state_history(tmp_path: Path) -> None:
    api = client(tmp_path)
    session_id = "session-turn-state"
    start_session(api, session_id=session_id)
    stored = ingest(
        api,
        [
            event(
                "event-turn-state-user",
                "Start state update work",
                session_id=session_id,
                turn_id="turn-state",
                event_type="USER_MESSAGE",
                role="USER",
            )
        ],
        session_id=session_id,
    )
    assert stored.status_code == 200, stored.text

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": session_id,
            "turn_id": "turn-state",
            "status": "FAILED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-turn-state-user"],
            "outcome": {"summary": "State update failed safely."},
            "error": {"code": "FAILED_TEST", "message": "failure was recorded"},
        },
    )
    assert completed.status_code == 200, completed.text

    state = api.post(
        "/v1/tools/get_execution_state",
        headers=auth_headers(),
        json={"session_id": session_id},
    )
    assert state.status_code == 200, state.text
    data = state.json()["data"]
    assert data["current_step"] == "Turn turn-state FAILED"
    assert data["enrichment"]["intent_label"] == "TURN_FAILED"

    history = api.post(
        "/v1/tools/get_goal_history",
        headers=auth_headers(),
        json={"session_id": session_id, "limit": 5},
    )
    assert history.status_code == 200, history.text
    latest = history.json()["data"]["history"][-1]
    assert latest["current_step"] == "Turn turn-state FAILED"
    assert latest["provenance"] == {"turn_id": "turn-state", "source": "turn_complete"}


def test_turn_complete_emits_event_and_graph_provenance(tmp_path: Path) -> None:
    api = client(tmp_path)
    session_id = "session-turn-graph"
    start_session(api, session_id=session_id)
    stored = ingest(
        api,
        [
            event(
                "event-turn-graph-user",
                "Start graph update work",
                session_id=session_id,
                turn_id="turn-graph",
                event_type="USER_MESSAGE",
                role="USER",
            )
        ],
        session_id=session_id,
    )
    assert stored.status_code == 200, stored.text

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": session_id,
            "turn_id": "turn-graph",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-turn-graph-user"],
            "outcome": {"summary": "Graph provenance complete."},
        },
    )
    assert completed.status_code == 200, completed.text

    exported = api.get(f"/v1/sessions/{session_id}/export", headers=auth_headers())
    assert exported.status_code == 200, exported.text
    body = exported.json()
    turn_events = [item for item in body["events"] if item["type"] == "TURN_COMPLETE"]
    assert len(turn_events) == 1
    turn_event = turn_events[0]
    assert turn_event["turn_id"] == "turn-graph"
    assert turn_event["parent_event_ids"] == ["event-turn-graph-user"]
    assert turn_event["metadata"]["turn_status"] == "COMPLETED"

    assert any(
        edge["source_event_id"] == "event-turn-graph-user"
        and edge["target_event_id"] == turn_event["event_id"]
        and edge["edge_type"] == "PARENT_CHILD"
        for edge in body["event_graph_edges"]
    )


def test_segment_tools_return_manifest_skeleton_and_fetch_metadata(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    events = [
        event(
            "event-user-1",
            "Start parser parity work",
            event_type="USER_MESSAGE",
            role="USER",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:01Z",
        ),
        event(
            "event-tool-1",
            "run pytest for parser",
            event_type="TOOL_CALL",
            role="ASSISTANT",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:02Z",
        ),
        event(
            "event-assistant-1",
            "parser parity looks stable",
            event_type="ASSISTANT_MESSAGE",
            role="ASSISTANT",
            turn_id="turn-1",
            timestamp="2026-06-09T12:00:03Z",
        ),
        event(
            "event-user-2",
            "Switch to billing migration",
            event_type="USER_MESSAGE",
            role="USER",
            turn_id="turn-2",
            timestamp="2026-06-09T12:00:04Z",
        ),
    ]
    assert ingest(api, events).status_code == 200

    segments = api.post(
        "/v1/tools/list_segments",
        headers=auth_headers(),
        json={"session_id": "session-1", "status": "ANY", "page_size": 20, "page_token": None},
    )
    assert segments.status_code == 200
    segment_rows = segments.json()["data"]["segments"]
    first_segment = segment_rows[0]
    assert first_segment["events_by_type"]["USER_MESSAGE"] == 1
    assert first_segment["events_by_type"]["TOOL_CALL"] == 1
    assert first_segment["events_by_type"]["ASSISTANT_MESSAGE"] == 1
    assert first_segment["first_user_snippet"] == "Start parser parity work"
    assert first_segment["last_user_snippet"] == "Start parser parity work"
    assert first_segment["goal_at_end"]
    assert "topic_tags" in first_segment

    expanded = api.post(
        "/v1/tools/expand_context",
        headers=auth_headers(),
        json={"session_id": "session-1", "seed_event_id": "event-user-1", "mode": "segment", "max_events": 10},
    )
    assert expanded.status_code == 200
    skeleton = expanded.json()["data"]
    assert skeleton["mode"] == "SEGMENT"
    assert skeleton["segment_id"] == first_segment["segment_id"]
    assert [item["event_id"] for item in skeleton["events"]] == [
        "event-user-1",
        "event-tool-1",
        "event-assistant-1",
    ]

    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-1", "event_id": "event-user-1"},
    )
    assert fetched.status_code == 200
    metadata = fetched.json()["data"]["metadata"]
    assert metadata["segment_id"] == first_segment["segment_id"]
    assert metadata["token_estimate"] > 0
    assert metadata["truncated"] is False


def test_context_prepare_validation_trace_and_off_mode(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    assert ingest(api, [event("event-prepare", "important old pytest evidence")]).status_code == 200

    request = {
        "schema_version": "mneme.context_prepare_request.v0",
        "request_id": "prepare-1",
        "prepare_id": "prepare-1",
        "session_id": "session-1",
        "turn_id": "turn-2",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "model": "test-model",
        "context_window_tokens": 100000,
        "budget_tokens": 2000,
        "request_messages": [
            {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
            {"schema_version": "mneme.message.v0", "role": "USER", "content": "continue pytest work"},
        ],
        "policy": {
            "mode": "AUTO",
            "cost_mode": "STANDARD",
            "preserve_system_prompt": True,
            "include_recent_tail": True,
            "include_retrieved_events": True,
            "retrieval": {"query": "continue pytest work sk-trace-secret", "top_k": 24},
                "budget_split": {
                    "execution_state_ratio": 0.05,
                    "retrieved_evidence_ratio": 0.30,
                    "protected_tail_ratio": 0.55,
                    "headroom_ratio": 0.10,
                },
        },
    }

    prepared = api.post("/v1/context/prepare", headers=auth_headers(), json=request)
    assert prepared.status_code == 200, prepared.text
    body = prepared.json()
    assert body["changed"] is True
    assert body["messages"][0]["role"] == "SYSTEM"
    assert body["trace_id"]
    assert body["trace"]["selected_event_ids"] == ["event-prepare"]

    trace = api.get(f"/v1/traces/{body['trace_id']}", headers=auth_headers())
    assert trace.status_code == 200
    assert trace.json()["selected_events"][0]["event_id"] == "event-prepare"
    assert "sk-trace-secret" not in str(trace.json())
    assert "[REDACTED]" in str(trace.json())

    off_request = {**request, "request_id": "prepare-off", "prepare_id": "prepare-off", "policy": {**request["policy"], "mode": "OFF"}}
    off = api.post("/v1/context/prepare", headers=auth_headers(), json=off_request)
    assert off.status_code == 200
    assert off.json()["changed"] is False

    bad_split = {**request, "request_id": "bad-split", "prepare_id": "bad-split"}
    bad_split["policy"] = {**request["policy"], "budget_split": {"execution_state_ratio": 2.0}}
    assert api.post("/v1/context/prepare", headers=auth_headers(), json=bad_split).status_code == 422

    bad_messages = {**request, "request_id": "bad-message", "prepare_id": "bad-message", "request_messages": [{"role": "USER"}]}
    assert api.post("/v1/context/prepare", headers=auth_headers(), json=bad_messages).status_code == 422


def test_turn_complete_cost_export_delete_and_restart_idempotency(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    runtimes = ["HERMES", "CODEX_MCP", "LANGGRAPH"]
    for session_idx in range(5):
        session_id = f"session-{session_idx}"
        start_session(api, session_id=session_id, runtime=runtimes[session_idx % len(runtimes)])
        events = [
            event(
                f"event-{session_idx}-{idx}",
                f"synthetic event {idx} runtime {runtimes[session_idx % len(runtimes)]}",
                session_id=session_id,
                turn_id=f"turn-{idx % 5}",
            )
            for idx in range(20)
        ]
        assert ingest(api, events, session_id=session_id).status_code == 200

    completed = api.post(
        "/v1/turns/complete",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.turn.v0",
            "session_id": "session-0",
            "turn_id": "turn-1",
            "status": "COMPLETED",
            "started_at": "2026-06-09T12:00:00Z",
            "completed_at": "2026-06-09T12:00:45Z",
            "event_ids": ["event-0-1"],
            "usage": {
                "provider": "openai",
                "model": "gpt-test",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "tool_call_count": 1,
                "cost_usd": 0.0123,
            },
        },
    )
    assert completed.status_code == 200

    restarted = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    replay = ingest(restarted, [event("event-0-0", "synthetic event 0 runtime HERMES", session_id="session-0", turn_id="turn-0")], session_id="session-0")
    assert replay.status_code == 200
    assert replay.json()["duplicates"] == 1

    cost = restarted.get("/v1/costs/session/session-0", headers=auth_headers())
    assert cost.status_code == 200
    cost_body = cost.json()
    assert cost_body["events_ingested"] == 21
    assert cost_body["embedding_batches"] == 0
    assert cost_body["period"] == {
        "from": "2026-06-09T12:00:00Z",
        "to": "2026-06-09T12:00:45Z",
    }
    assert cost_body["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "embedding_tokens": 0,
        "reranker_calls": 0,
        "llm_enrichment_tokens": 0,
        "tool_calls": 1,
    }
    assert cost_body["provider_breakdown"] == [
        {
            "provider": "openai",
            "model": "gpt-test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "tool_calls": 1,
            "estimated_cost_usd": 0.0123,
        }
    ]
    assert cost_body["baseline"] == {
        "provider_prompt_tokens_without_mneme_estimate": 0,
        "methodology": "UNKNOWN",
        "estimate_kind": "COUNTERFACTUAL",
        "savings_claim": False,
    }

    exported = restarted.get("/v1/sessions/session-0/export", headers=auth_headers())
    assert exported.status_code == 200
    assert len(exported.json()["events"]) >= 20

    deleted = restarted.delete("/v1/sessions/session-0", headers={**auth_headers(), "Idempotency-Key": "delete-1"})
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert restarted.get("/v1/sessions/session-0/export", headers=auth_headers()).status_code == 404


def test_writer_queue_depth_limit_returns_retryable_429(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                max_writer_queue_depth=1,
            )
        )
    )

    start_session(api)

    with api.app.state.store._writer_lane.enter():
        saturated = ingest(
            api,
            [
                event(
                    "event-saturated",
                    "queue-depth test",
                    event_type="ASSISTANT_MESSAGE",
                    role="ASSISTANT",
                )
            ],
            session_id="session-1",
        )

    assert saturated.status_code == 429, saturated.text
    body = saturated.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert body["error"]["details"]["reason"] == "WRITER_QUEUE_FULL"
    assert body["error"]["retryable"] is True
    details = body["error"]["details"]
    assert details["max_writer_queue_depth"] == 1


def test_storage_busy_returns_retryable_503(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    start_session(api)

    def raise_storage_busy(*_: object, **__: object) -> None:
        raise StorageBusy("SQLITE_STORAGE_BUSY")

    monkeypatch.setattr(api.app.state.store, "put_event", raise_storage_busy)

    busy = ingest(api, [event("event-storage-busy", "storage busy retry")])

    assert busy.status_code == 503, busy.text
    body = busy.json()
    assert body["error"]["code"] == "STORAGE_BUSY"
    assert body["error"]["details"]["reason"] == "SQLITE_STORAGE_BUSY"
    assert body["error"]["retryable"] is True


def test_event_ingest_batch_first_handles_streaming_bursts(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                max_batch_events=3,
            )
        )
    )
    start_session(api, session_id="stream-session")

    burst_events = [
        event(
            f"streaming-event-{idx}",
            f"Streaming burst event {idx}",
            session_id="stream-session",
            turn_id=f"turn-{idx // 2}",
            timestamp=f"2026-06-09T12:00:0{idx}Z",
        )
        for idx in range(7)
    ]

    for start in range(0, len(burst_events), 3):
        chunk = burst_events[start : start + 3]
        accepted = ingest(api, chunk, session_id="stream-session")
        assert accepted.status_code == 200, accepted.text

    exported = api.get("/v1/sessions/stream-session/export", headers=auth_headers())
    assert exported.status_code == 200, exported.text
    events_after_stream = exported.json()["events"]
    assert len(events_after_stream) == 7
    expected_ids = {event_payload["event_id"] for event_payload in burst_events}
    assert expected_ids.issubset({item["event_id"] for item in events_after_stream})

    searched = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"query": "Streaming", "session_id": "stream-session", "scope": "SESSION", "top_k": 10},
    )
    assert searched.status_code == 200, searched.text
    assert len(searched.json()["data"]["results"]) == 7

    oversized_batch = [
        event(
            "oversized-event-0",
            "Streaming oversized",
            session_id="stream-session",
            turn_id="turn-overflow",
            timestamp="2026-06-09T12:01:00Z",
        ),
        event(
            "oversized-event-1",
            "Streaming oversized",
            session_id="stream-session",
            turn_id="turn-overflow",
            timestamp="2026-06-09T12:01:01Z",
        ),
        event(
            "oversized-event-2",
            "Streaming oversized",
            session_id="stream-session",
            turn_id="turn-overflow",
            timestamp="2026-06-09T12:01:02Z",
        ),
        event(
            "oversized-event-3",
            "Streaming oversized",
            session_id="stream-session",
            turn_id="turn-overflow",
            timestamp="2026-06-09T12:01:03Z",
        ),
    ]
    oversized = ingest(api, oversized_batch, session_id="stream-session")
    assert oversized.status_code == 413, oversized.text
    oversized_error = oversized.json()["error"]
    assert oversized_error["code"] == "PAYLOAD_TOO_LARGE"
    assert "max_batch_events" in oversized_error["details"]
    assert oversized_error["details"]["max_batch_events"] == 3

    export_after_rejected = api.get("/v1/sessions/stream-session/export", headers=auth_headers())
    assert export_after_rejected.status_code == 200, export_after_rejected.text
    post_reject_ids = {item["event_id"] for item in export_after_rejected.json()["events"]}
    assert expected_ids.issubset(post_reject_ids)
    assert post_reject_ids.isdisjoint({"oversized-event-0", "oversized-event-1", "oversized-event-2", "oversized-event-3"})
