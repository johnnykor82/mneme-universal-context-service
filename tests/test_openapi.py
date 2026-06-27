from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import Settings
from mneme_service.tool_names import TOOL_NAMES


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def test_contract_version_is_canonical_across_docs_openapi_and_runtime(tmp_path: Path) -> None:
    contract_version_path = Path("docs/MNEME_CONTRACT_VERSION")
    contract_version = contract_version_path.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", contract_version)

    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    openapi = api.get("/openapi.json").json()
    assert openapi["info"]["version"] == contract_version

    health = api.get("/v1/health")
    assert health.status_code == 200, health.text
    assert health.json()["mneme_contract_version"] == contract_version

    capabilities = api.get("/v1/capabilities", headers=auth_headers())
    assert capabilities.status_code == 200, capabilities.text
    assert capabilities.json()["mneme_contract_version"] == contract_version


def test_capabilities_advertise_v0_foundation_without_overclaiming(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    response = api.get("/v1/capabilities", headers=auth_headers())

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["service_version"] == "0.1.0"
    assert body["strict_cost_mode"] is False
    assert body["supports_openapi"] is True
    assert body["supports_metrics"] is True
    assert body["supports_reindex_jobs"] is True
    assert body["supports_reindex_job_polling"] is True
    assert body["metrics_format"] == "prometheus"
    assert body["delta_extraction"] == {
        "enabled": True,
        "schema_version": "mneme.entity_modifier.v0",
        "sources": ["DETERMINISTIC_PATTERN"],
        "automatic_update_scope": ["execution_state.active_entities"],
        "provider_guarded_enabled": False,
        "provider_guarded_policy": "UNSUPPORTED_IN_V0_DETERMINISTIC_FALLBACK_ACTIVE",
        "conflict_order": ["REPLACE", "REMOVE", "CONSTRAINT", "ADD"],
    }
    assert body["supports_blob_store"] is True
    assert body["supports_blob_range_reads"] is True
    assert body["supports_export_bundle"] is True
    assert body["supported_export_formats"] == ["json", "tar_bundle"]
    assert body["supports_project_isolation"] is True
    assert body["supports_retention_cleanup"] is True
    assert body["integration_depth"]["max_supported"] == "EVENT_INGEST"
    assert body["integration_depth"]["supports_prepare_input"] is False
    assert body["integration_depth"]["supports_context_engine"] is False
    assert body["integration_depth"]["unsupported_or_future"] == [
        "PREPARE_INPUT",
        "CONTEXT_ENGINE",
        "COMPACTION_OWNER",
        "FULL_RUNTIME",
    ]
    assert body["integration_depth"]["adapter_claims"]["rest_api"]["level"] == "EVENT_INGEST"
    assert body["integration_depth"]["adapter_claims"]["rest_api"]["host_lifecycle"] == [
        "bootstrap_session",
        "ingest_events",
        "after_model_response",
        "complete_turn",
    ]
    assert body["integration_depth"]["adapter_claims"]["mcp"]["level"] == "TOOLS_ONLY"
    assert set(body["integration_depth"]["adapter_claims"]) == {"rest_api", "mcp"}
    assert body["limits"]["max_blob_bytes"] == 2_097_152
    assert body["limits"]["max_session_id_length"] == 256
    assert body["limits"]["idempotency_key_min_retention_seconds"] == 604_800
    assert body["storage"]["schema_version"] == 1
    assert body["storage"]["migration_status"] == "CURRENT"
    assert body["tokenizer"]["token_estimate_quality"] == "CHAR_APPROXIMATE"
    assert body["supported_schema_versions"]["blob"] == ["mneme.blob.v0"]
    assert body["supported_schema_versions"]["retention_cleanup_request"] == [
        "mneme.retention_cleanup_request.v0"
    ]
    assert body["mcp_tool_versions"] == {name: "v0" for name in TOOL_NAMES}


def test_openapi_schema_is_parseable_and_documents_core_v0_components(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    response = api.get("/openapi.json")

    assert response.status_code == 200, response.text
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    components = schema["components"]
    assert components["securitySchemes"]["BearerAuth"]["scheme"] == "bearer"
    schemas = components["schemas"]
    for name in (
        "BlobDeleteResponse",
        "BlobGcRequest",
        "BlobGcResponse",
        "BlobRecordResponse",
        "BlobBytesRef",
        "CapabilitiesResponse",
        "CapabilitiesIntegrationDepth",
        "AdapterIntegrationClaim",
        "CapabilitiesLimits",
        "CapabilitiesStorage",
        "ErrorEnvelope",
        "ErrorBody",
    ):
        assert name in schemas
    capabilities = schema["paths"]["/v1/capabilities"]["get"]
    assert capabilities["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CapabilitiesResponse"
    }
    assert capabilities["responses"]["401"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }
    integration_depth = schemas["CapabilitiesIntegrationDepth"]["properties"]
    assert integration_depth["max_supported"]["enum"] == [
        "TOOLS_ONLY",
        "EVENT_INGEST",
        "PREPARE_INPUT",
        "CONTEXT_ENGINE",
        "COMPACTION_OWNER",
        "FULL_RUNTIME",
    ]
    assert integration_depth["adapter_claims"]["additionalProperties"] == {
        "$ref": "#/components/schemas/AdapterIntegrationClaim"
    }
    upload_blob = schema["paths"]["/v1/blobs"]["post"]
    assert upload_blob["requestBody"]["content"]["application/octet-stream"]["schema"] == {
        "type": "string",
        "contentMediaType": "application/octet-stream",
        "title": "Body",
    }
    assert upload_blob["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/BlobRecordResponse"
    }
    assert upload_blob["responses"]["415"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }
    blob_content = schema["paths"]["/v1/blobs/{blob_id}/content"]["get"]
    assert blob_content["responses"]["416"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }
    blob_gc = schema["paths"]["/v1/maintenance/blob-gc"]["post"]
    assert blob_gc["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/BlobGcRequest"
    }
    assert blob_gc["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/BlobGcResponse"
    }
    assert blob_gc["responses"]["403"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }


def test_openapi_documents_metrics_and_reindex_contract_routes(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    paths = schema["paths"]
    schemas = schema["components"]["schemas"]

    for name in (
        "MetricsResponse",
        "ReindexRequest",
        "ReindexJobResponse",
        "ReindexCancelRequest",
        "TraceResponse",
        "CostReportResponse",
    ):
        assert name in schemas

    metrics = paths["/v1/metrics"]["get"]
    assert metrics["responses"]["200"]["content"]["text/plain"]["schema"] == {
        "$ref": "#/components/schemas/MetricsResponse"
    }
    assert metrics["responses"]["401"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }

    reindex_create = paths["/v1/maintenance/reindex"]["post"]
    assert reindex_create["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReindexRequest"
    }
    assert reindex_create["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReindexJobResponse"
    }
    for status_code in ("401", "403", "404", "409", "422", "503"):
        assert reindex_create["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    reindex_poll = paths["/v1/maintenance/reindex/{job_id}"]["get"]
    assert reindex_poll["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReindexJobResponse"
    }
    for status_code in ("401", "403", "404"):
        assert reindex_poll["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    reindex_cancel = paths["/v1/maintenance/reindex/{job_id}/cancel"]["post"]
    assert reindex_cancel["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReindexCancelRequest"
    }
    assert reindex_cancel["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReindexJobResponse"
    }
    for status_code in ("401", "403", "404", "409", "422"):
        assert reindex_cancel["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }


def test_openapi_documents_trace_and_cost_response_models(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]
    paths = schema["paths"]

    assert "TraceResponse" in schemas
    assert "CostReportResponse" in schemas
    assert {"schema_version", "trace_id", "session_id", "trace_type", "created_at_ms"} <= set(
        schemas["TraceResponse"]["properties"]
    )
    assert {"schema_version", "session_id", "events_ingested", "prepare_calls", "warnings"} <= set(
        schemas["CostReportResponse"]["properties"]
    )

    trace = paths["/v1/traces/{trace_id}"]["get"]
    assert trace["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/TraceResponse"
    }
    for status_code in ("401", "403", "404"):
        assert trace["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    cost = paths["/v1/costs/session/{session_id}"]["get"]
    assert cost["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/CostReportResponse"
    }
    for status_code in ("401", "403", "404"):
        assert cost["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }


def test_capabilities_match_metrics_and_reindex_route_support(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    capabilities = api.get("/v1/capabilities", headers=auth_headers())

    assert capabilities.status_code == 200, capabilities.text
    body = capabilities.json()
    assert body["supports_metrics"] is ("/v1/metrics" in schema["paths"])
    assert body["supports_reindex_jobs"] is ("/v1/maintenance/reindex" in schema["paths"])
    assert body["supports_reindex_job_polling"] is (
        "/v1/maintenance/reindex/{job_id}" in schema["paths"]
    )


def test_openapi_documents_core_route_request_and_response_models(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]
    for name in (
        "HealthResponse",
        "SessionStartRequest",
        "SessionStartResponse",
        "EventBatchRequest",
        "EventBatchResponse",
        "Message",
        "MessageContentPart",
        "TurnCompleteRequest",
        "TurnCompleteResponse",
        "ContextPrepareRequest",
        "ContextPrepareResponse",
        "SessionReadinessRequest",
        "ToolResponseEnvelope",
    ):
        assert name in schemas

    message = schemas["Message"]
    assert set(message["required"]) >= {"schema_version", "role", "content"}
    assert message["properties"]["schema_version"]["const"] == "mneme.message.v0"
    assert set(message["properties"]["role"]["enum"]) >= {
        "SYSTEM",
        "DEVELOPER",
        "USER",
        "ASSISTANT",
        "TOOL",
    }
    content_schema = message["properties"]["content"]
    assert content_schema["anyOf"][0]["type"] == "string"
    assert content_schema["anyOf"][1]["items"] == {"$ref": "#/components/schemas/MessageContentPart"}
    assert set(schemas["MessageContentPart"]["properties"]["type"]["enum"]) == {
        "text",
        "json",
        "image_ref",
        "bytes_ref",
        "tool_call",
        "tool_result",
    }

    turn_request = schemas["TurnCompleteRequest"]
    status_schema = turn_request["properties"]["status"]
    status_enum = status_schema.get("enum") or next(
        item["enum"] for item in status_schema.get("anyOf", []) if "enum" in item
    )
    assert set(status_enum) == {
        "STARTED",
        "COMPLETED",
        "FAILED",
        "INTERRUPTED",
        "CANCELLED",
    }
    for field in ("started_at", "completed_at", "prepare_ids", "trace_ids", "usage", "outcome", "error"):
        assert field in turn_request["properties"]

    health = schema["paths"]["/v1/health"]["get"]
    assert "security" not in health
    assert health["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }

    start = schema["paths"]["/v1/sessions/start"]["post"]
    assert start["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SessionStartRequest"
    }
    assert start["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SessionStartResponse"
    }
    assert start["responses"]["401"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }
    assert start["responses"]["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }

    ingest = schema["paths"]["/v1/events"]["post"]
    assert ingest["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EventBatchRequest"
    }
    assert ingest["requestBody"]["content"]["multipart/form-data"]["schema"]["properties"] == {
        "payload": {
            "description": "mneme.event_batch.v0 JSON payload",
            "type": "string",
        },
        "blob.<client_part_id>": {
            "description": "Binary blob parts referenced as multipart://<client_part_id>",
            "type": "string",
            "format": "binary",
        },
    }
    assert ingest["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/EventBatchResponse"
    }

    turn_complete = schema["paths"]["/v1/turns/complete"]["post"]
    assert turn_complete["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/TurnCompleteRequest"
    }
    assert turn_complete["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/TurnCompleteResponse"
    }
    for status_code in ("401", "403", "404", "409", "422"):
        assert turn_complete["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    context_prepare = schema["paths"]["/v1/context/prepare"]["post"]
    assert context_prepare["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ContextPrepareRequest"
    }
    assert context_prepare["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ContextPrepareResponse"
    }
    for status_code in ("401", "403", "404", "409", "422"):
        assert context_prepare["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    readiness = schema["paths"]["/v1/readiness/session"]["post"]
    assert readiness["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SessionReadinessRequest"
    }
    assert readiness["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ToolResponseEnvelope"
    }
    for status_code in ("401", "404", "412", "422"):
        assert readiness["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    execution_state = schema["paths"]["/v1/sessions/{session_id}/execution_state"]["post"]
    assert execution_state["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ExecutionStateUpdateRequest"
    }
    assert execution_state["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ExecutionStateUpdateResponse"
    }
    for status_code in ("401", "403", "404", "422"):
        assert execution_state["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }

    segment_start = schema["paths"]["/v1/segments/start"]["post"]
    assert segment_start["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentStartRequest"
    }
    assert segment_start["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentResponse"
    }
    segment_close = schema["paths"]["/v1/segments/{segment_id}/close"]["post"]
    assert segment_close["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentCloseRequest"
    }
    assert segment_close["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentResponse"
    }
    assert schema["paths"]["/v1/segments"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentListResponse"
    }
    assert schema["paths"]["/v1/segments/{segment_id}"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentResponse"
    }
    assert schema["paths"]["/v1/segments/{segment_id}/events"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SegmentEventsResponse"
    }


def test_openapi_documents_session_lifecycle_read_and_close_routes(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/v1/sessions/{session_id}" in paths
    session_get_route = paths["/v1/sessions/{session_id}"]
    assert "get" in session_get_route
    session_get = session_get_route["get"]
    session_get_schema = session_get["responses"]["200"]["content"]["application/json"]["schema"]
    assert session_get_schema.get("type") == "object" or "$ref" in session_get_schema
    assert "session_id" in {parameter["name"] for parameter in session_get["parameters"]}
    assert "422" in session_get["responses"]

    assert "/v1/sessions/{session_id}/close" in paths
    session_close_route = paths["/v1/sessions/{session_id}/close"]
    assert "post" in session_close_route
    session_close = session_close_route["post"]
    session_close_schema = session_close["responses"]["200"]["content"]["application/json"]["schema"]
    assert session_close_schema.get("type") == "object" or "$ref" in session_close_schema
    assert "session_id" in {parameter["name"] for parameter in session_close["parameters"]}
    assert "422" in session_close["responses"]

    assert "/v1/sessions/{session_id}/retention/cleanup" in paths
    retention_route = paths["/v1/sessions/{session_id}/retention/cleanup"]
    assert "post" in retention_route
    retention_cleanup = retention_route["post"]
    assert retention_cleanup["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RetentionCleanupRequest"
    }
    assert retention_cleanup["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RetentionCleanupResponse"
    }
    for status_code in ("401", "403", "404", "409", "422"):
        assert retention_cleanup["responses"][status_code]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ErrorEnvelope"
        }


def test_openapi_documents_memory_tool_routes_with_shared_envelopes(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    assert "ToolRequestPayload" in schema["components"]["schemas"]
    assert "session_resolution" in schema["components"]["schemas"]["ToolResponseEnvelope"]["properties"]
    assert {f"/v1/tools/{name}" for name in TOOL_NAMES} <= set(schema["paths"])

    for path, operations in schema["paths"].items():
        if not path.startswith("/v1/tools/"):
            continue
        operation = operations["post"]
        assert operation["requestBody"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ToolRequestPayload"
        }
        assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/ToolResponseEnvelope"
        }
        for status_code in ("401", "403", "404", "422"):
            assert operation["responses"][status_code]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ErrorEnvelope"
            }


def test_openapi_uses_bearer_security_without_raw_authorization_parameters(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    for path, operations in schema["paths"].items():
        for operation in operations.values():
            if not isinstance(operation, dict):
                continue
            parameter_names = {parameter.get("name") for parameter in operation.get("parameters", [])}
            assert "authorization" not in parameter_names
            if path != "/v1/health":
                assert operation.get("security") == [{"BearerAuth": []}]


def test_openapi_schema_is_parseable_and_matches_examples(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    schema = api.get("/openapi.json").json()
    schemas = schema["components"]["schemas"]
    example_schema_names = (
        "ErrorEnvelope",
        "ToolResponseEnvelope",
        "SessionStartRequest",
        "SessionStartResponse",
        "EventBatchRequest",
        "EventBatchResponse",
        "TurnCompleteRequest",
        "TurnCompleteResponse",
        "ContextPrepareRequest",
        "ContextPrepareResponse",
    )
    for name in example_schema_names:
        examples = schemas[name].get("examples")
        assert isinstance(examples, list), name
        assert examples, name

    error_example = schemas["ErrorEnvelope"]["examples"][0]
    assert error_example["ok"] is False
    assert error_example["error"]["code"] == "VALIDATION_ERROR"
    assert error_example["error"]["retryable"] is False
    assert error_example["warnings"] == []

    tool_example = schemas["ToolResponseEnvelope"]["examples"][0]
    assert tool_example["ok"] is True
    assert tool_example["session_resolution"]["source"] == "EXPLICIT_ARGUMENT"

    public_post_examples = {
        "/v1/sessions/start": "SessionStartRequest",
        "/v1/events": "EventBatchRequest",
        "/v1/turns/complete": "TurnCompleteRequest",
        "/v1/context/prepare": "ContextPrepareRequest",
    }
    for path, schema_name in public_post_examples.items():
        request_schema = schema["paths"][path]["post"]["requestBody"]["content"]["application/json"]["schema"]
        assert request_schema == {"$ref": f"#/components/schemas/{schema_name}"}
        assert schemas[schema_name]["examples"][0]["schema_version"].startswith("mneme.")
