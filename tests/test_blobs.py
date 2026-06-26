from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from mneme_service.app import create_app
from mneme_service.config import Settings, StaticTokenSettings


TOKEN = "test-token"


def auth_headers(token: str = TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def client(
    tmp_path: Path,
    *,
    max_blob_bytes: int = 2_097_152,
    max_batch_total_blob_bytes: int = 20_971_520,
) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                max_blob_bytes=max_blob_bytes,
                max_batch_total_blob_bytes=max_batch_total_blob_bytes,
                max_multipart_transaction_bytes=max_batch_total_blob_bytes + 2_097_152,
            )
        )
    )


def scoped_client(tmp_path: Path) -> TestClient:
    return TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                static_tokens=(
                    StaticTokenSettings(
                        name="project-a-token",
                        token="project-a-token",
                        project_scopes=("project-a",),
                        role="ADAPTER",
                    ),
                    StaticTokenSettings(
                        name="project-b-token",
                        token="project-b-token",
                        project_scopes=("project-b",),
                        role="ADAPTER",
                    ),
                ),
            )
        )
    )


def start_session(
    api: TestClient,
    *,
    session_id: str = "session-1",
    project_id: str = "project-1",
    token: str = TOKEN,
) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(token),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": session_id,
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": project_id,
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-09T12:00:00Z",
            "metadata": {"cwd": "/repo"},
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
    *,
    session_id: str = "session-1",
    content: dict | None = None,
) -> dict:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": session_id,
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "TOOL",
        "type": "TOOL_OUTPUT",
        "timestamp": "2026-06-09T12:00:01Z",
        "content": content or {"format": "TEXT", "text": "hello"},
        "tool": {"name": "exec_command", "call_id": "tool-call-1"},
        "parent_event_ids": [],
        "metadata": {},
    }


def blob_upload_headers(
    *,
    session_id: str = "session-1",
    project_id: str = "project-1",
    token: str = TOKEN,
    idempotency_key: str | None = None,
    content_type: str = "application/octet-stream",
) -> dict[str, str]:
    headers = {
        **auth_headers(token),
        "Content-Type": content_type,
        "X-Mneme-Session-Id": session_id,
        "X-Mneme-Project-Isolation-Key": project_id,
    }
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def multipart_files(payload: dict, parts: dict[str, bytes]) -> list[tuple[str, tuple[str, str | bytes, str]]]:
    files: list[tuple[str, tuple[str, str | bytes, str]]] = [
        ("payload", ("payload.json", json.dumps(payload), "application/json"))
    ]
    for part_id, content in parts.items():
        files.append((f"blob.{part_id}", (f"{part_id}.bin", content, "application/octet-stream")))
    return files


def test_blob_upload_fetch_metadata_content_range_delete_and_gc(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    created = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(idempotency_key="blob-upload-1"),
        content=b"hello blob",
    )

    assert created.status_code == 200, created.text
    created_body = created.json()
    assert created_body["schema_version"] == "mneme.blob.v0"
    blob_id = created_body["blob_id"]
    assert created_body["uri"] == f"mneme-blob://{blob_id}"
    assert created_body["bytes_ref"] == {
        "format": "BYTES_REF",
        "uri": f"mneme-blob://{blob_id}",
        "hash": created_body["hash"],
        "size_bytes": 10,
        "media_type": "application/octet-stream",
        "storage_owner": "SERVER",
    }

    replay = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(idempotency_key="blob-upload-1"),
        content=b"hello blob",
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["blob_id"] == blob_id

    conflict = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(idempotency_key="blob-upload-1"),
        content=b"different",
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"

    metadata = api.get(f"/v1/blobs/{blob_id}", headers=auth_headers())
    assert metadata.status_code == 200, metadata.text
    metadata_body = metadata.json()
    assert metadata_body["blob_id"] == blob_id
    assert metadata_body["owner"] == "SERVER"
    assert metadata_body["session_id"] == "session-1"
    assert metadata_body["project_isolation_key"] == "project-1"
    assert metadata_body["size_bytes"] == 10
    assert metadata_body["media_type"] == "application/octet-stream"
    assert metadata_body["ref_count"] == 0
    assert metadata_body["retention"]["delete_with_session"] is True
    assert "content" not in metadata_body

    content = api.get(f"/v1/blobs/{blob_id}/content", headers=auth_headers())
    assert content.status_code == 200, content.text
    assert content.content == b"hello blob"
    assert content.headers["content-type"] == "application/octet-stream"

    ranged = api.get(
        f"/v1/blobs/{blob_id}/content",
        headers={**auth_headers(), "Range": "bytes=1-3"},
    )
    assert ranged.status_code == 206, ranged.text
    assert ranged.content == b"ell"
    assert ranged.headers["content-range"] == "bytes 1-3/10"
    assert ranged.headers["content-type"] == "application/octet-stream"

    malformed = api.get(
        f"/v1/blobs/{blob_id}/content",
        headers={**auth_headers(), "Range": "potatoes"},
    )
    assert malformed.status_code == 400
    assert malformed.json()["error"]["code"] == "BAD_REQUEST"

    unsatisfiable = api.get(
        f"/v1/blobs/{blob_id}/content",
        headers={**auth_headers(), "Range": "bytes=99-120"},
    )
    assert unsatisfiable.status_code == 416
    assert unsatisfiable.json()["error"]["code"] == "RANGE_NOT_SATISFIABLE"

    deleted = api.delete(
        f"/v1/blobs/{blob_id}",
        headers={**auth_headers(), "Idempotency-Key": "blob-delete-1"},
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"blob_id": blob_id, "deleted": True}

    delete_replay = api.delete(
        f"/v1/blobs/{blob_id}",
        headers={**auth_headers(), "Idempotency-Key": "blob-delete-1"},
    )
    assert delete_replay.status_code == 200, delete_replay.text
    assert delete_replay.json() == {"blob_id": blob_id, "deleted": True}

    gone = api.get(f"/v1/blobs/{blob_id}", headers=auth_headers())
    assert gone.status_code == 404
    assert gone.json()["error"]["code"] == "NOT_FOUND"


def test_blob_upload_errors_use_contract_envelopes(tmp_path: Path) -> None:
    api = client(tmp_path, max_blob_bytes=4)
    start_session(api)

    too_large = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"12345",
    )
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert too_large.json()["error"]["details"]["max_blob_bytes"] == 4
    assert too_large.json()["error"]["details"]["actual_bytes"] == 5

    unsupported = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(content_type="text/plain"),
        content=b"text",
    )
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_blob_routes_enforce_project_scope(tmp_path: Path) -> None:
    api = scoped_client(tmp_path)
    start_session(api, session_id="session-a", project_id="project-a", token="project-a-token")

    created = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(
            session_id="session-a",
            project_id="project-a",
            token="project-a-token",
        ),
        content=b"project a bytes",
    )
    assert created.status_code == 200, created.text
    blob_id = created.json()["blob_id"]

    denied_metadata = api.get(
        f"/v1/blobs/{blob_id}",
        headers=auth_headers("project-b-token"),
    )
    assert denied_metadata.status_code == 403
    assert denied_metadata.json()["error"]["code"] == "FORBIDDEN"

    denied_content = api.get(
        f"/v1/blobs/{blob_id}/content",
        headers=auth_headers("project-b-token"),
    )
    assert denied_content.status_code == 403
    assert denied_content.json()["error"]["code"] == "FORBIDDEN"


def test_event_ingest_rejects_cross_project_bytes_ref(tmp_path: Path) -> None:
    api = scoped_client(tmp_path)
    start_session(api, session_id="session-a", project_id="project-a", token="project-a-token")
    start_session(api, session_id="session-b", project_id="project-b", token="project-b-token")

    created = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(
            session_id="session-a",
            project_id="project-a",
            token="project-a-token",
        ),
        content=b"project a bytes",
    )
    assert created.status_code == 200, created.text

    cross_project_event = event(
        "event-cross-project-ref",
        session_id="session-b",
        content=created.json()["bytes_ref"],
    )
    rejected = api.post(
        "/v1/events",
        headers=auth_headers("project-b-token"),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-b",
            "events": [cross_project_event],
        },
    )

    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "FORBIDDEN"


def test_multipart_event_ingest_creates_bytes_ref_for_binary_parts(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    blob_bytes = b"binary multipart payload"
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-multipart-ref",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }

    response = api.post(
        "/v1/events",
        headers={**auth_headers(), "Idempotency-Key": "multipart-create-1"},
        files=[
            ("payload", ("payload.json", json.dumps(payload), "application/json")),
            ("blob.artifact", ("artifact.bin", blob_bytes, "application/octet-stream")),
        ],
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["accepted"] == 1
    assert body["blob_refs"] == [
        {
            "client_part_id": "artifact",
            "event_id": "event-multipart-ref",
            "bytes_ref": {
                "format": "BYTES_REF",
                "uri": body["blob_refs"][0]["bytes_ref"]["uri"],
                "hash": f"sha256:{hashlib.sha256(blob_bytes).hexdigest()}",
                "size_bytes": len(blob_bytes),
                "media_type": "application/octet-stream",
                "storage_owner": "SERVER",
            },
        }
    ]

    exported = api.get("/v1/sessions/session-1/export", headers=auth_headers())
    assert exported.status_code == 200
    [stored_event] = [
        item
        for item in exported.json()["events"]
        if item["event_id"] == "event-multipart-ref"
    ]
    stored_ref = stored_event["content"]
    assert stored_ref == body["blob_refs"][0]["bytes_ref"]
    assert stored_event["ingestion"]["original_content_hash"].startswith("sha256:")
    assert stored_event["ingestion"]["normalized_content_hash"].startswith("sha256:")
    assert (
        stored_event["ingestion"]["original_content_hash"]
        != stored_event["ingestion"]["normalized_content_hash"]
    )
    blob_id = stored_ref["uri"].removeprefix("mneme-blob://")
    metadata = api.get(f"/v1/blobs/{blob_id}", headers=auth_headers())
    assert metadata.status_code == 200
    assert metadata.json()["ref_count"] == 1


def test_multipart_event_ingest_replays_by_payload_and_blob_digest(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-multipart-idem",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }

    first = api.post(
        "/v1/events",
        headers={**auth_headers(), "Idempotency-Key": "multipart-idem-1"},
        files=multipart_files(payload, {"artifact": b"same bytes"}),
    )
    replay = api.post(
        "/v1/events",
        headers={**auth_headers(), "Idempotency-Key": "multipart-idem-1"},
        files=multipart_files(payload, {"artifact": b"same bytes"}),
    )
    conflict = api.post(
        "/v1/events",
        headers={**auth_headers(), "Idempotency-Key": "multipart-idem-1"},
        files=multipart_files(payload, {"artifact": b"different bytes"}),
    )

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert replay.json() == first.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


def test_multipart_event_ingest_validates_payload_and_blob_parts(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-missing-part",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://missing",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }

    missing_payload = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=[("blob.artifact", ("artifact.bin", b"bytes", "application/octet-stream"))],
    )
    missing_part = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(payload, {}),
    )
    unreferenced_part = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(
            {
                "schema_version": "mneme.event_batch.v0",
                "session_id": "session-1",
                "events": [event("event-no-ref")],
            },
            {"artifact": b"bytes"},
        ),
    )
    unsupported = api.post(
        "/v1/events",
        headers={**auth_headers(), "Content-Type": "text/plain"},
        content=b"not-json",
    )

    assert missing_payload.status_code == 400
    assert missing_payload.json()["error"]["code"] == "BAD_REQUEST"
    assert missing_part.status_code == 422
    assert missing_part.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unreferenced_part.status_code == 422
    assert unreferenced_part.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_multipart_event_ingest_rejects_blob_byte_limits(tmp_path: Path) -> None:
    part_dir = tmp_path / "part"
    total_dir = tmp_path / "total"
    part_dir.mkdir()
    total_dir.mkdir()
    part_limit_api = client(part_dir, max_blob_bytes=4)
    start_session(part_limit_api)
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-part-limit",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }
    part_too_large = part_limit_api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(payload, {"artifact": b"12345"}),
    )

    total_limit_api = client(total_dir, max_batch_total_blob_bytes=4)
    start_session(total_limit_api)
    total_payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-total-limit-1",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://one",
                    "media_type": "application/octet-stream",
                },
            ),
            event(
                "event-total-limit-2",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://two",
                    "media_type": "application/octet-stream",
                },
            ),
        ],
    }
    total_too_large = total_limit_api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(total_payload, {"one": b"123", "two": b"456"}),
    )

    assert part_too_large.status_code == 413
    assert part_too_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert total_too_large.status_code == 413
    assert total_too_large.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_multipart_ingest_blob_failure_rolls_back_all_events(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-rollback-good",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            ),
            {
                **event("event-rollback-bad"),
                "schema_version": "mneme.event.v9",
            },
        ],
    }

    failed = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(payload, {"artifact": b"rollback bytes"}),
    )

    assert failed.status_code == 400
    assert failed.json()["error"]["code"] == "BAD_REQUEST"
    assert api.app.state.store.count_blobs_for_session("session-1") == 0
    exported = api.get("/v1/sessions/session-1/export", headers=auth_headers())
    assert exported.status_code == 200
    assert all(item["event_id"] != "event-rollback-good" for item in exported.json()["events"])


def test_multipart_event_conflict_does_not_leave_blob_rows(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    existing = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [event("event-conflict-existing")],
        },
    )
    assert existing.status_code == 200, existing.text
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-conflict-existing",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }

    conflict = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(payload, {"artifact": b"conflicting bytes"}),
    )

    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"
    assert api.app.state.store.count_blobs_for_session("session-1") == 0


def test_multipart_event_storage_failure_removes_staged_blobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)
    app = create_app(settings)
    api = TestClient(app, raise_server_exceptions=False)
    start_session(api)

    def fail_put_blob_records_and_events(*_args, **_kwargs) -> None:
        raise RuntimeError("forced multipart transaction failure")

    monkeypatch.setattr(
        app.state.store,
        "put_blob_records_and_events",
        fail_put_blob_records_and_events,
    )
    payload = {
        "schema_version": "mneme.event_batch.v0",
        "session_id": "session-1",
        "events": [
            event(
                "event-storage-failure",
                content={
                    "format": "BYTES_REF",
                    "uri": "multipart://artifact",
                    "media_type": "application/octet-stream",
                },
            )
        ],
    }

    failed = api.post(
        "/v1/events",
        headers=auth_headers(),
        files=multipart_files(payload, {"artifact": b"staged bytes"}),
    )

    assert failed.status_code == 500
    assert app.state.store.count_blobs_for_session("session-1") == 0


def test_session_export_json_is_metadata_only_and_respects_scope(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    upload = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"export bytes",
    )
    assert upload.status_code == 200, upload.text
    ingest_response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [
                event(
                    "event-export-blob",
                    content=upload.json()["bytes_ref"],
                )
            ],
        },
    )
    assert ingest_response.status_code == 200, ingest_response.text

    exported = api.get(
        "/v1/sessions/session-1/export?format=json",
        headers=auth_headers(),
    )

    assert exported.status_code == 200, exported.text
    body = exported.json()
    assert body["schema_version"] == "mneme.session_export.v0"
    assert body["format"] == "json"
    assert body["blob_contents"] == []
    assert body["blobs_metadata"] == [
        {
            "blob_id": upload.json()["blob_id"],
            "uri": upload.json()["uri"],
            "size_bytes": len(b"export bytes"),
            "hash": upload.json()["hash"],
            "media_type": "application/octet-stream",
            "omitted_reason": "FORMAT_JSON_METADATA_ONLY",
        }
    ]
    assert "export bytes" not in exported.text


def test_session_export_json_excludes_audit_by_default_and_includes_on_request(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    ingest_response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [event("event-export-audit", content={"format": "TEXT", "text": "audit searchable"})],
        },
    )
    assert ingest_response.status_code == 200, ingest_response.text

    search = api.post(
        "/v1/tools/context_search",
        headers=auth_headers(),
        json={"session_id": "session-1", "query": "audit searchable"},
    )
    assert search.status_code == 200, search.text

    default_export = api.get(
        "/v1/sessions/session-1/export?format=json",
        headers=auth_headers(),
    )
    assert default_export.status_code == 200, default_export.text
    assert default_export.json()["audit_records"] == []

    audit_export = api.get(
        "/v1/sessions/session-1/export?format=json&include_audit=true",
        headers=auth_headers(),
    )
    assert audit_export.status_code == 200, audit_export.text
    assert any(
        audit["action"] == "MEMORY_READ" and audit["tool"] == "context_search"
        for audit in audit_export.json()["audit_records"]
    )


def test_cross_project_export_does_not_leak_blob_metadata(tmp_path: Path) -> None:
    api = scoped_client(tmp_path)
    start_session(api, session_id="session-a", project_id="project-a", token="project-a-token")
    upload = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(
            session_id="session-a",
            project_id="project-a",
            token="project-a-token",
        ),
        content=b"project a export bytes",
    )
    assert upload.status_code == 200, upload.text
    ingested = api.post(
        "/v1/events",
        headers=auth_headers("project-a-token"),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-a",
            "events": [
                event(
                    "event-project-a-export",
                    session_id="session-a",
                    content=upload.json()["bytes_ref"],
                )
            ],
        },
    )
    assert ingested.status_code == 200, ingested.text

    denied = api.get(
        "/v1/sessions/session-a/export?format=json",
        headers=auth_headers("project-b-token"),
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"
    assert upload.json()["blob_id"] not in denied.text


def test_unknown_export_format_returns_422_validation_error(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)

    response = api.get(
        "/v1/sessions/session-1/export?format=zip",
        headers=auth_headers(),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["field"] == "format"


def test_session_export_tar_bundle_streams_blob_parts(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    upload = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"tar bundle bytes",
    )
    assert upload.status_code == 200, upload.text
    ingested = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [
                event(
                    "event-tar-blob",
                    content=upload.json()["bytes_ref"],
                )
            ],
        },
    )
    assert ingested.status_code == 200, ingested.text

    response = api.get(
        "/v1/sessions/session-1/export?format=tar_bundle&include_blobs=true",
        headers=auth_headers(),
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/x-tar"
    with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:") as bundle:
        names = set(bundle.getnames())
        assert "manifest.json" in names
        blob_path = f"blobs/{upload.json()['blob_id']}.bin"
        assert blob_path in names
        manifest = json.loads(bundle.extractfile("manifest.json").read().decode("utf-8"))
        assert manifest["schema_version"] == "mneme.session_export_manifest.v0"
        assert manifest["format"] == "tar_bundle"
        assert manifest["session_id"] == "session-1"
        assert manifest["blob_parts"][0]["path"] == blob_path
        assert bundle.extractfile(blob_path).read() == b"tar bundle bytes"


def test_delete_session_removes_session_scoped_blobs(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    upload = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"delete me",
    )
    assert upload.status_code == 200, upload.text
    ingested = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [
                event(
                    "event-delete-blob",
                    content=upload.json()["bytes_ref"],
                )
            ],
        },
    )
    assert ingested.status_code == 200, ingested.text
    assert api.app.state.store.count_blobs_for_session("session-1") == 1

    deleted = api.delete("/v1/sessions/session-1", headers=auth_headers())

    assert deleted.status_code == 200, deleted.text
    assert api.app.state.store.count_blobs_for_session("session-1") == 0
    missing_blob = api.get(f"/v1/blobs/{upload.json()['blob_id']}", headers=auth_headers())
    assert missing_blob.status_code == 404


def test_maintenance_blob_gc_requires_scope_and_is_idempotent(tmp_path: Path) -> None:
    api = client(tmp_path)
    start_session(api)
    orphan = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"orphan",
    )
    referenced = api.post(
        "/v1/blobs",
        headers=blob_upload_headers(),
        content=b"referenced",
    )
    assert orphan.status_code == 200, orphan.text
    assert referenced.status_code == 200, referenced.text
    ingested = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.event_batch.v0",
            "session_id": "session-1",
            "events": [
                event(
                    "event-gc-ref",
                    content=referenced.json()["bytes_ref"],
                )
            ],
        },
    )
    assert ingested.status_code == 200, ingested.text

    dry_run = api.post(
        "/v1/maintenance/blob-gc",
        headers=auth_headers(),
        json={
            "scope": "PROJECT",
            "project_isolation_key": "project-1",
            "session_id": None,
            "dry_run": True,
        },
    )
    assert dry_run.status_code == 200, dry_run.text
    assert dry_run.json()["candidate_count"] == 1
    assert dry_run.json()["deleted_count"] == 0
    assert api.app.state.store.count_blobs_for_session("session-1") == 2

    delete = api.post(
        "/v1/maintenance/blob-gc",
        headers={**auth_headers(), "Idempotency-Key": "gc-project-1"},
        json={
            "scope": "PROJECT",
            "project_isolation_key": "project-1",
            "session_id": None,
            "dry_run": False,
        },
    )
    replay = api.post(
        "/v1/maintenance/blob-gc",
        headers={**auth_headers(), "Idempotency-Key": "gc-project-1"},
        json={
            "scope": "PROJECT",
            "project_isolation_key": "project-1",
            "session_id": None,
            "dry_run": False,
        },
    )
    conflict = api.post(
        "/v1/maintenance/blob-gc",
        headers={**auth_headers(), "Idempotency-Key": "gc-project-1"},
        json={
            "scope": "PROJECT",
            "project_isolation_key": "project-1",
            "session_id": None,
            "dry_run": True,
        },
    )

    assert delete.status_code == 200, delete.text
    assert delete.json()["candidate_count"] == 1
    assert delete.json()["deleted_count"] == 1
    assert replay.status_code == 200, replay.text
    assert replay.json() == delete.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"
    assert api.get(f"/v1/blobs/{orphan.json()['blob_id']}", headers=auth_headers()).status_code == 404
    assert api.get(f"/v1/blobs/{referenced.json()['blob_id']}", headers=auth_headers()).status_code == 200


def test_scoped_token_cannot_run_unscoped_blob_gc(tmp_path: Path) -> None:
    api = scoped_client(tmp_path)
    start_session(api, session_id="session-a", project_id="project-a", token="project-a-token")

    denied = api.post(
        "/v1/maintenance/blob-gc",
        headers=auth_headers("project-a-token"),
        json={"scope": "ALL", "project_isolation_key": None, "session_id": None, "dry_run": True},
    )

    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"
