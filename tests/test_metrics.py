from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                insecure_dev=False,
                reindex_enqueue_when_provider_unavailable=True,
            )
        )
    )


def start_session(api: TestClient, session_id: str = "metrics-session") -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": "CODEX",
            "project_id": "metrics-project",
            "privacy": {
                "project_isolation_key": "metrics-project",
                "retention_days": 30,
                "redaction_profile": "DEFAULT",
                "redaction_policy": "IRREVERSIBLE",
            },
        },
    )
    assert response.status_code == 200, response.text


def ingest_secret_event(api: TestClient, session_id: str = "metrics-session") -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": session_id,
            "events": [
                {
                    "schema_version": "mneme.event.v0",
                    "event_id": "metrics-event-1",
                    "session_id": session_id,
                    "turn_id": "turn-1",
                    "agent_id": "agent-1",
                    "runtime": "CODEX",
                    "role": "USER",
                    "type": "USER_MESSAGE",
                    "timestamp": "2026-06-24T12:00:00Z",
                    "content": {
                        "format": "TEXT",
                        "text": "metrics secret should stay out sk-metrics-secret",
                    },
                    "metadata": {"authorization": f"Bearer {TOKEN}"},
                }
            ],
        },
    )
    assert response.status_code == 200, response.text


def test_metrics_endpoint_exposes_required_prometheus_families(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest_secret_event(api)
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "metrics-project"},
    )
    assert created.status_code == 200, created.text

    response = api.get("/v1/metrics", headers=auth_headers())

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    for family in (
        "mneme_http_requests_total",
        "mneme_http_request_latency_ms",
        "mneme_provider_calls_total",
        "mneme_provider_failures_total",
        "mneme_provider_latency_ms",
        "mneme_writer_queue_depth",
        "mneme_background_job_backlog",
        "mneme_embedding_events_total",
        "mneme_reindex_jobs_total",
        "mneme_retention_sweeps_total",
        "mneme_blob_storage_bytes",
        "mneme_blob_storage_count",
        "mneme_startup_integrity_status",
        "mneme_intent_classifications_total",
        "mneme_segment_rollovers_total",
        "mneme_routing_modes_total",
        "mneme_indexing_compressions_total",
        "mneme_retrieval_quality_precision_at_k",
    ):
        assert family in text
    assert 'endpoint="/v1/metrics"' in text
    assert 'status="200"' in text
    assert 'status="WAITING_FOR_PROVIDER"' in text


def test_metrics_endpoint_does_not_export_tokens_or_evidence_content(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest_secret_event(api)

    response = api.get("/v1/metrics", headers=auth_headers())

    assert response.status_code == 200, response.text
    text = response.text
    assert TOKEN not in text
    assert "sk-metrics-secret" not in text
    assert "metrics secret should stay out" not in text


def test_structured_access_log_includes_safe_operational_fields(tmp_path: Path, caplog) -> None:
    api = client(tmp_path)

    with caplog.at_level(logging.INFO, logger="mneme_service.access"):
        response = api.get(
            "/v1/health",
            headers={
                "Authorization": "Bearer super-secret-token",
                "X-Request-Id": "request-log-1",
                "X-Mneme-Trace-Id": "trace-log-1",
                "X-Mneme-Project-Isolation-Key": "project-log",
            },
        )

    assert response.status_code == 200
    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "mneme_service.access"
    ]
    assert records
    access = records[-1]
    assert access["request_id"] == "request-log-1"
    assert access["trace_id"] == "trace-log-1"
    assert access["endpoint"] == "/v1/health"
    assert access["status"] == 200
    assert access["error_code"] is None
    assert access["project_scope"] == "project-log"
    assert access["background_job_id"] is None
    assert access["latency_ms"] >= 0
    assert "super-secret-token" not in str(access)
