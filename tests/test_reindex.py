from __future__ import annotations

from pathlib import Path
from typing import Sequence

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings, StaticTokenSettings


OWNER_TOKEN = "owner-token"


class StaticEmbeddingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        self.calls += 1
        return [[1.0, 0.0, 0.0] if text.strip() else None for text in texts]


class FailingEmbeddingProvider:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        self.calls += 1
        raise RuntimeError("provider down")


def auth_headers(token: str = OWNER_TOKEN, *, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def settings(
    tmp_path: Path,
    *,
    enqueue_when_provider_unavailable: bool = False,
    with_static_tokens: bool = False,
    provider_configured: bool = False,
    reindex_max_events_per_transaction: int = 10,
    reindex_provider_wait_timeout_seconds: int = 86400,
    reindex_provider_circuit_breaker_min_calls: int = 10,
    reindex_provider_circuit_breaker_failure_ratio: float = 0.5,
    reindex_provider_circuit_breaker_open_seconds: int = 60,
) -> Settings:
    static_tokens = ()
    if with_static_tokens:
        static_tokens = (
            StaticTokenSettings(
                name="project-a-adapter",
                token="project-a-token",
                project_scopes=("project-a",),
                role="ADAPTER",
            ),
            StaticTokenSettings(
                name="project-b-adapter",
                token="project-b-token",
                project_scopes=("project-b",),
                role="ADAPTER",
            ),
        )
    embeddings = ProviderSettings(
        enabled=provider_configured,
        provider="openai_compatible" if provider_configured else None,
        model="embedding-test" if provider_configured else None,
    )
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=OWNER_TOKEN,
        insecure_dev=False,
        static_tokens=static_tokens,
        reindex_enqueue_when_provider_unavailable=enqueue_when_provider_unavailable,
        reindex_max_events_per_transaction=reindex_max_events_per_transaction,
        reindex_provider_wait_timeout_seconds=reindex_provider_wait_timeout_seconds,
        reindex_provider_circuit_breaker_min_calls=reindex_provider_circuit_breaker_min_calls,
        reindex_provider_circuit_breaker_failure_ratio=reindex_provider_circuit_breaker_failure_ratio,
        reindex_provider_circuit_breaker_open_seconds=reindex_provider_circuit_breaker_open_seconds,
        embeddings=embeddings,
    )


def client(
    tmp_path: Path,
    *,
    enqueue_when_provider_unavailable: bool = False,
    with_static_tokens: bool = False,
    provider_configured: bool = False,
) -> TestClient:
    embedding_provider = StaticEmbeddingProvider() if provider_configured else None
    return TestClient(
        create_app(
            settings(
                tmp_path,
                enqueue_when_provider_unavailable=enqueue_when_provider_unavailable,
                with_static_tokens=with_static_tokens,
                provider_configured=provider_configured,
            ),
            embedding_provider=embedding_provider,
        )
    )


def start_session(api: TestClient, session_id: str, project_id: str, token: str = OWNER_TOKEN) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(token),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": "CODEX",
            "project_id": project_id,
            "privacy": {
                "project_isolation_key": project_id,
                "retention_days": 30,
                "redaction_profile": "DEFAULT",
                "redaction_policy": "IRREVERSIBLE",
            },
        },
    )
    assert response.status_code == 200, response.text


def ingest_event(api: TestClient, session_id: str, text: str, token: str = OWNER_TOKEN) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(token),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": session_id,
            "events": [
                {
                    "schema_version": "mneme.event.v0",
                    "event_id": f"event-{session_id}",
                    "session_id": session_id,
                    "turn_id": "turn-1",
                    "agent_id": "agent-1",
                    "runtime": "CODEX",
                    "role": "USER",
                    "type": "USER_MESSAGE",
                    "timestamp": "2026-06-24T12:00:00Z",
                    "content": {"format": "TEXT", "text": text},
                    "parent_event_ids": [],
                }
            ],
        },
    )
    assert response.status_code == 200, response.text


def test_reindex_create_enforces_scope_and_poll_hides_out_of_scope_jobs(tmp_path: Path) -> None:
    api = client(
        tmp_path,
        enqueue_when_provider_unavailable=True,
        with_static_tokens=True,
    )
    start_session(api, "session-a", "project-a", token="project-a-token")

    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers("project-a-token"),
        json={"scope": "PROJECT", "project_isolation_key": "project-a"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "WAITING_FOR_PROVIDER"

    cross_project_create = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers("project-a-token"),
        json={"scope": "PROJECT", "project_isolation_key": "project-b"},
    )
    assert cross_project_create.status_code == 403

    all_projects = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers("project-a-token"),
        json={"scope": "ALL"},
    )
    assert all_projects.status_code == 403

    out_of_scope_poll = api.get(
        f"/v1/maintenance/reindex/{created.json()['job_id']}",
        headers=auth_headers("project-b-token"),
    )
    assert out_of_scope_poll.status_code == 404


def test_reindex_create_idempotency_replays_and_conflicts(tmp_path: Path) -> None:
    api = client(tmp_path, enqueue_when_provider_unavailable=True)

    payload = {"scope": "PROJECT", "project_isolation_key": "project-idem", "force": True}
    first = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(idempotency_key="reindex-idem-1"),
        json=payload,
    )
    assert first.status_code == 200, first.text
    replay = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(idempotency_key="reindex-idem-1"),
        json=payload,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == first.json()

    conflict = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(idempotency_key="reindex-idem-1"),
        json={**payload, "force": False},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


def test_reindex_provider_unavailable_default_and_waiting_mode(tmp_path: Path) -> None:
    unavailable = client(tmp_path)
    rejected = unavailable.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-provider"},
    )
    assert rejected.status_code == 503
    assert rejected.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"

    waiting = client(tmp_path, enqueue_when_provider_unavailable=True)
    created = waiting.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-provider"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "WAITING_FOR_PROVIDER"


def test_reindex_create_persists_progress_and_queues_with_provider(tmp_path: Path) -> None:
    api = client(tmp_path, provider_configured=True)
    start_session(api, "session-queued", "project-queued")
    ingest_event(api, "session-queued", "queued reindex evidence")

    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(idempotency_key="reindex-persist-1"),
        json={
            "scope": "SESSION",
            "session_id": "session-queued",
            "force": True,
            "max_job_events": 10,
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["status"] == "QUEUED"
    assert body["progress"] == {
        "candidate_count": 1,
        "processed_count": 0,
        "failed_count": 0,
    }

    restarted = TestClient(
        create_app(
            settings(tmp_path, provider_configured=True),
            embedding_provider=StaticEmbeddingProvider(),
        )
    )
    polled = restarted.get(
        f"/v1/maintenance/reindex/{body['job_id']}",
        headers=auth_headers(),
    )
    assert polled.status_code == 200, polled.text
    assert polled.json() == body


def test_reindex_cancel_persists_waiting_job_and_is_idempotent(tmp_path: Path) -> None:
    api = client(tmp_path, enqueue_when_provider_unavailable=True)
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-cancel"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "WAITING_FOR_PROVIDER"

    cancelled = api.post(
        f"/v1/maintenance/reindex/{created.json()['job_id']}/cancel",
        headers=auth_headers(),
        json={"reason": "test cancel"},
    )
    assert cancelled.status_code == 200, cancelled.text
    body = cancelled.json()
    assert body["status"] == "CANCELLED"
    assert body["completed_at"] is not None

    replay = api.post(
        f"/v1/maintenance/reindex/{body['job_id']}/cancel",
        headers=auth_headers(),
        json={"reason": "repeat cancel"},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == body

    polled = api.get(f"/v1/maintenance/reindex/{body['job_id']}", headers=auth_headers())
    assert polled.status_code == 200, polled.text
    assert polled.json() == body

    metrics = api.get("/v1/metrics", headers=auth_headers())
    assert metrics.status_code == 200, metrics.text
    assert 'mneme_reindex_jobs_total{status="CANCELLED"} 1' in metrics.text


def test_reindex_cancel_idempotency_key_replays_and_conflicts(tmp_path: Path) -> None:
    api = client(tmp_path, enqueue_when_provider_unavailable=True)
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-cancel-idem"},
    )
    assert created.status_code == 200, created.text
    job_id = created.json()["job_id"]

    first = api.post(
        f"/v1/maintenance/reindex/{job_id}/cancel",
        headers=auth_headers(idempotency_key="reindex-cancel-1"),
        json={"reason": "operator requested"},
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "CANCELLED"

    replay = api.post(
        f"/v1/maintenance/reindex/{job_id}/cancel",
        headers=auth_headers(idempotency_key="reindex-cancel-1"),
        json={"reason": "operator requested"},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == first.json()

    conflict = api.post(
        f"/v1/maintenance/reindex/{job_id}/cancel",
        headers=auth_headers(idempotency_key="reindex-cancel-1"),
        json={"reason": "different reason"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


def test_reindex_cancel_final_states_do_not_rewrite_history(tmp_path: Path) -> None:
    api = client(tmp_path, provider_configured=True)
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-final"},
    )
    assert created.status_code == 200, created.text
    job = created.json()
    job["status"] = "COMPLETED"
    job["completed_at"] = "2026-06-25T00:00:00Z"
    api.app.state.store.update_reindex_job(job)

    cancelled = api.post(
        f"/v1/maintenance/reindex/{job['job_id']}/cancel",
        headers=auth_headers(),
        json={},
    )

    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "COMPLETED"
    assert cancelled.json()["completed_at"] == "2026-06-25T00:00:00Z"


def test_reindex_cancel_running_job_sets_cancelled(tmp_path: Path) -> None:
    api = client(tmp_path, provider_configured=True)
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-running"},
    )
    assert created.status_code == 200, created.text
    job = created.json()
    job["status"] = "RUNNING"
    job["started_at"] = "2026-06-25T00:00:00Z"
    api.app.state.store.update_reindex_job(job)

    cancelled = api.post(
        f"/v1/maintenance/reindex/{job['job_id']}/cancel",
        headers=auth_headers(),
        json={},
    )

    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "CANCELLED"
    assert cancelled.json()["completed_at"] is not None


def test_reindex_cancel_queued_job_stops_future_provider_calls_and_writes(tmp_path: Path) -> None:
    provider = StaticEmbeddingProvider()
    api = TestClient(
        create_app(
            settings(tmp_path, provider_configured=True),
            embedding_provider=provider,
        )
    )
    start_session(api, "session-cancel-provider", "project-cancel-provider")
    ingest_event(api, "session-cancel-provider", "cancel provider safety")
    calls_after_ingest = provider.calls

    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={
            "scope": "SESSION",
            "session_id": "session-cancel-provider",
            "force": True,
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["status"] == "QUEUED"

    cancelled = api.post(
        f"/v1/maintenance/reindex/{created.json()['job_id']}/cancel",
        headers=auth_headers(),
        json={},
    )

    assert cancelled.status_code == 200, cancelled.text
    body = cancelled.json()
    assert body["status"] == "CANCELLED"
    assert body["progress"] == {
        "candidate_count": 1,
        "processed_count": 0,
        "failed_count": 0,
    }
    assert provider.calls == calls_after_ingest
    cancel_audits = [
        audit
        for audit in api.app.state.store.list_audit("session-cancel-provider")
        if audit["action"] == "REINDEX_CANCEL"
    ]
    assert len(cancel_audits) == 1
    assert cancel_audits[0]["result"]["job_id"] == body["job_id"]
    assert cancel_audits[0]["result"]["status"] == "CANCELLED"

    drained = api.app.state.run_reindex_job_once(body["job_id"])
    assert drained["status"] == "CANCELLED"
    assert provider.calls == calls_after_ingest


def test_reindex_drain_marks_provider_failure_failed(tmp_path: Path) -> None:
    provider = FailingEmbeddingProvider()
    api = TestClient(
        create_app(
            settings(tmp_path, provider_configured=True),
            embedding_provider=provider,
        )
    )
    start_session(api, "session-failing-provider", "project-failing-provider")
    ingest_event(api, "session-failing-provider", "provider failure should mark failed")
    calls_after_ingest = provider.calls
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "SESSION", "session_id": "session-failing-provider", "force": True},
    )
    assert created.status_code == 200, created.text

    drained = api.app.state.run_reindex_job_once(created.json()["job_id"])

    assert provider.calls == calls_after_ingest + 1
    assert drained["status"] == "FAILED"
    assert drained["progress"]["failed_count"] == 1
    fetched = api.post(
        "/v1/tools/fetch_event",
        headers=auth_headers(),
        json={"session_id": "session-failing-provider", "event_id": "event-session-failing-provider"},
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["data"]["event"]["ingestion"]["embedding_status"] == "FAILED"


def test_waiting_reindex_job_fails_after_provider_wait_timeout(tmp_path: Path) -> None:
    api = TestClient(
        create_app(
            settings(
                tmp_path,
                enqueue_when_provider_unavailable=True,
                reindex_provider_wait_timeout_seconds=1,
            )
        )
    )
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "PROJECT", "project_isolation_key": "project-timeout"},
    )
    assert created.status_code == 200, created.text
    job = created.json()
    job["created_at"] = "2000-01-01T00:00:00Z"
    api.app.state.store.update_reindex_job(job)

    drained = api.app.state.run_reindex_job_once(job["job_id"])

    assert drained["status"] == "FAILED"
    assert drained["error"]["reason"] == "PROVIDER_WAIT_TIMEOUT"


def test_reindex_drain_uses_bounded_micro_transactions_and_yields_to_foreground(tmp_path: Path) -> None:
    provider = StaticEmbeddingProvider()
    api = TestClient(
        create_app(
            settings(
                tmp_path,
                provider_configured=True,
                reindex_max_events_per_transaction=1,
            ),
            embedding_provider=provider,
        )
    )
    start_session(api, "session-yield", "project-yield")
    ingest_event(api, "session-yield", "first yield event")
    second = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-yield",
        "events": [
            {
                "schema_version": "mneme.event.v0",
                "event_id": "event-session-yield-2",
                "session_id": "session-yield",
                "turn_id": "turn-2",
                "agent_id": "agent-1",
                "runtime": "CODEX",
                "role": "USER",
                "type": "USER_MESSAGE",
                "timestamp": "2026-06-24T12:00:01Z",
                "content": {"format": "TEXT", "text": "second yield event"},
                "parent_event_ids": [],
            }
        ],
    }
    accepted = api.post("/v1/events", headers=auth_headers(), json=second)
    assert accepted.status_code == 200, accepted.text
    created = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={"scope": "SESSION", "session_id": "session-yield", "force": True},
    )
    assert created.status_code == 200, created.text
    assert created.json()["progress"]["candidate_count"] == 2

    first_slice = api.app.state.run_reindex_job_once(created.json()["job_id"])
    assert first_slice["status"] == "RUNNING"
    assert first_slice["progress"]["processed_count"] == 1

    foreground = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-yield",
            "events": [
                {
                    "schema_version": "mneme.event.v0",
                    "event_id": "event-session-yield-foreground",
                    "session_id": "session-yield",
                    "turn_id": "turn-foreground",
                    "agent_id": "agent-1",
                    "runtime": "CODEX",
                    "role": "USER",
                    "type": "USER_MESSAGE",
                    "timestamp": "2026-06-24T12:00:02Z",
                    "content": {"format": "TEXT", "text": "foreground write wins"},
                    "parent_event_ids": [],
                }
            ],
        },
    )
    assert foreground.status_code == 200, foreground.text

    second_slice = api.app.state.run_reindex_job_once(created.json()["job_id"])
    assert second_slice["status"] == "COMPLETED"
    assert second_slice["progress"]["processed_count"] == 2


def test_reindex_provider_circuit_blocks_new_calls_after_failure_budget(tmp_path: Path) -> None:
    provider = FailingEmbeddingProvider()
    api = TestClient(
        create_app(
            settings(
                tmp_path,
                provider_configured=True,
                reindex_provider_circuit_breaker_min_calls=2,
                reindex_provider_circuit_breaker_failure_ratio=0.5,
                reindex_provider_circuit_breaker_open_seconds=60,
            ),
            embedding_provider=provider,
        )
    )
    start_session(api, "session-circuit", "project-circuit")
    ingest_event(api, "session-circuit", "first circuit event")
    baseline_calls = provider.calls

    for index in range(2):
        created = api.post(
            "/v1/maintenance/reindex",
            headers=auth_headers(),
            json={
                "scope": "SESSION",
                "session_id": "session-circuit",
                "force": True,
                "max_job_events": 1,
            },
        )
        assert created.status_code == 200, created.text
        drained = api.app.state.run_reindex_job_once(created.json()["job_id"])
        assert drained["status"] == "FAILED"
        assert provider.calls == baseline_calls + index + 1

    blocked = api.post(
        "/v1/maintenance/reindex",
        headers=auth_headers(),
        json={
            "scope": "SESSION",
            "session_id": "session-circuit",
            "force": True,
            "max_job_events": 1,
        },
    )
    assert blocked.status_code == 200, blocked.text
    before_blocked_drain = provider.calls
    drained_blocked = api.app.state.run_reindex_job_once(blocked.json()["job_id"])
    assert drained_blocked["status"] == "WAITING_FOR_PROVIDER"
    assert drained_blocked["error"]["reason"] == "PROVIDER_CIRCUIT_OPEN"
    assert provider.calls == before_blocked_drain
