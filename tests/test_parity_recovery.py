from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Sequence

import httpx
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings
from mneme_service.enrichment import EnrichmentResult
from mneme_service.reranker import RerankResult
from mneme_service.utils import token_estimate


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def provider_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        enricher_every_n_turns=1,
        embeddings=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
        ),
        reranker=ProviderSettings(
            enabled=True,
            provider="jina",
            model="jina-reranker-test",
            base_url="https://rerank.example.test/v1",
        ),
        llm_enrichment=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-enrichment-test",
            base_url="https://llm.example.test/v1",
        ),
    )


def embedding_only_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        embeddings=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-test",
            base_url="https://embed.example.test/v1",
        ),
    )


def session_payload(session_id: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "mneme.session.v0",
        "session_id": session_id,
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "project_id": "project-1",
        "model": "test-model",
        "tokenizer": "approx",
        "context_window_tokens": 100000,
        "cost_mode": "STANDARD",
        "started_at": "2026-06-12T23:00:00Z",
        "metadata": metadata or {"cwd": "/repo"},
    }


def event(
    session_id: str,
    event_id: str,
    text: str,
    *,
    event_type: str = "USER_MESSAGE",
    role: str = "USER",
    turn_id: str = "turn-1",
    timestamp: str = "2026-06-12T23:00:01Z",
    parent_event_ids: list[str] | None = None,
    tool_name: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
        "parent_event_ids": parent_event_ids or [],
    }
    if tool_name:
        payload["tool"] = {"name": tool_name, "call_id": f"{event_id}-call"}
    return payload


def start(api: TestClient, session_id: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    response = api.post("/v1/sessions/start", headers=auth_headers(), json=session_payload(session_id, metadata=metadata))
    assert response.status_code == 200, response.text
    return response.json()


def ingest(api: TestClient, session_id: str, events: list[dict[str, Any]]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )
    assert response.status_code == 200, response.text


class RecordingEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        batch = list(texts)
        self.calls.append(batch)
        return [vector_for(text) if text.strip() else None for text in batch]


class FailingEmbeddingProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        raise RuntimeError("embedding outage")


class PreferenceReranker:
    def rerank(self, query: str, documents: Sequence[str]) -> RerankResult:
        scores = [
            {"index": index, "score": 1.0 if "oauth" in document.lower() else 0.1}
            for index, document in enumerate(documents)
        ]
        return RerankResult(scores=sorted(scores, key=lambda item: item["score"], reverse=True))


class RecordingEnrichmentProvider:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        self.events.append(event_payload)
        return EnrichmentResult(
            updates={
                "intent_label": "implementation",
                "active_entities": ["context_prepare"],
                "open_loops": ["verify parity suite"],
            }
        )


def vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if any(term in lowered for term in ("oauth", "auth", "authentication", "refresh", "verifier")):
        return [1.0, 0.0, 0.0]
    if "database" in lowered:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


def tool(api: TestClient, name: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = api.post(f"/v1/tools/{name}", headers=auth_headers(), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_minimal_mode_redacts_and_makes_zero_provider_calls(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))
    capabilities = api.get("/v1/capabilities", headers=auth_headers()).json()
    assert capabilities["supports_embeddings"] is False
    assert capabilities["supports_reranking"] is False
    assert capabilities["supports_llm_enrichment"] is False

    start(api, "session-minimal")
    ingest(
        api,
        "session-minimal",
        [event("session-minimal", "event-minimal", "minimal parser evidence sk-minimal-secret")],
    )

    search = tool(api, "context_search", {"session_id": "session-minimal", "query": "minimal parser", "top_k": 5})
    assert search["data"]["results"][0]["event_id"] == "event-minimal"
    assert "sk-minimal-secret" not in str(search)

    trace = api.get(f"/v1/traces/{search['trace_id']}", headers=auth_headers()).json()
    export = api.get("/v1/sessions/session-minimal/export", headers=auth_headers()).json()
    cost = api.get("/v1/costs/session/session-minimal", headers=auth_headers()).json()

    assert "sk-minimal-secret" not in str(trace)
    assert "sk-minimal-secret" not in str(export)
    assert cost["embedding_batches"] == 0
    assert cost["reranker_calls"] == 0
    assert cost["enrichment_calls"] == 0


def test_provider_pipeline_recovers_semantic_reranked_enriched_context_without_secret_leak(tmp_path: Path) -> None:
    embedding_provider = RecordingEmbeddingProvider()
    enrichment_provider = RecordingEnrichmentProvider()
    api = TestClient(
        create_app(
            provider_settings(tmp_path),
            embedding_provider=embedding_provider,
            reranker_provider=PreferenceReranker(),
            enrichment_provider=enrichment_provider,
        )
    )
    start(api, "session-provider")
    ingest(
        api,
        "session-provider",
        [
            event("session-provider", "event-oauth", "oauth callback verifier rotated sk-provider-secret"),
            event("session-provider", "event-db", "database migration completed"),
        ],
    )

    search = tool(
        api,
        "context_search",
        {"session_id": "session-provider", "query": "authentication refresh flow", "top_k": 2},
    )

    assert search["data"]["results"][0]["event_id"] == "event-oauth"
    assert search["data"]["results"][0]["reason"] == "RERANKED"
    trace = api.get(f"/v1/traces/{search['trace_id']}", headers=auth_headers()).json()
    assert trace["retrieval"]["strategies"] == ["VECTOR", "KEYWORD", "RECENCY", "RERANK"]
    assert trace["retrieval"]["degraded"] is False

    state = tool(api, "get_execution_state", {"session_id": "session-provider"})["data"]
    cost = api.get("/v1/costs/session/session-provider", headers=auth_headers()).json()

    assert state["enrichment"]["intent_label"] == "implementation"
    assert state["active_entities"] == ["context_prepare"]
    assert cost["embedding_items"] == 2
    assert cost["reranker_calls"] == 1
    assert cost["enrichment_calls"] == 2
    assert "sk-provider-secret" not in str(embedding_provider.calls)
    assert "sk-provider-secret" not in str(enrichment_provider.events)
    assert "sk-provider-secret" not in str(search)


def test_embedding_outage_degrades_to_keyword_recency_without_losing_events(tmp_path: Path) -> None:
    api = TestClient(
        create_app(embedding_only_settings(tmp_path), embedding_provider=FailingEmbeddingProvider())
    )
    start(api, "session-outage")
    ingest(api, "session-outage", [event("session-outage", "event-outage", "outage keyword evidence survives")])

    search = tool(api, "context_search", {"session_id": "session-outage", "query": "outage keyword", "top_k": 5})
    trace = api.get(f"/v1/traces/{search['trace_id']}", headers=auth_headers()).json()
    export = api.get("/v1/sessions/session-outage/export", headers=auth_headers()).json()
    cost = api.get("/v1/costs/session/session-outage", headers=auth_headers()).json()

    assert search["data"]["results"][0]["event_id"] == "event-outage"
    assert search["warnings"][0]["code"] == "EMBEDDINGS_UNAVAILABLE"
    assert trace["retrieval"]["degraded"] is True
    assert trace["retrieval"]["fallbacks"] == ["EMBEDDINGS_UNAVAILABLE"]
    assert "event-outage" in [item["event_id"] for item in export["events"]]
    assert cost["failures"]["embedding_failures"] >= 1


def test_state_segments_resume_lineage_and_budgeted_prepare_survive_restart(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    api = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    start(api, "session-parent")
    ingest(
        api,
        "session-parent",
        [
            event("session-parent", "event-goal", "Ship semantic retrieval parity", timestamp="2026-06-12T23:00:01Z"),
            event(
                "session-parent",
                "event-call",
                "run pytest",
                event_type="TOOL_CALL",
                role="ASSISTANT",
                tool_name="pytest",
                timestamp="2026-06-12T23:00:02Z",
            ),
            event(
                "session-parent",
                "event-output",
                "pytest passed for budgeted context assembly",
                event_type="TOOL_OUTPUT",
                role="TOOL",
                parent_event_ids=["event-call"],
                tool_name="pytest",
                timestamp="2026-06-12T23:00:03Z",
            ),
            event(
                "session-parent",
                "event-decision",
                "Decision: keep REST retrieval canonical",
                event_type="DECISION",
                role="ASSISTANT",
                parent_event_ids=["event-output"],
                timestamp="2026-06-12T23:00:04Z",
            ),
            event(
                "session-parent",
                "event-switch",
                "Switch to billing migration cleanup",
                timestamp="2026-06-12T23:00:05Z",
            ),
        ],
    )

    restarted = TestClient(create_app(Settings(db_path=db_path, auth_token=TOKEN)))
    state = tool(restarted, "get_execution_state", {"session_id": "session-parent"})["data"]
    history = tool(restarted, "get_goal_history", {"session_id": "session-parent", "limit": 10})["data"]["history"]
    segments = tool(restarted, "list_segments", {"session_id": "session-parent"})["data"]["segments"]

    assert state["goal"] == "Ship semantic retrieval parity"
    assert history[-1]["current_step"] == "Switch to billing migration cleanup"
    assert {segment["status"] for segment in segments} == {"CLOSED", "ACTIVE"}

    prepare = restarted.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-parent",
            "prepare_id": "prepare-parent",
            "session_id": "session-parent",
            "turn_id": "turn-prepare",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 420,
            "request_messages": [
                {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "old context " + ("drop " * 360)},
                {"schema_version": "mneme.message.v0", "role": "ASSISTANT", "content": "recent assistant tail"},
                {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue pytest work"},
            ],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "preserve_system_prompt": True,
                "include_execution_state": True,
                "include_retrieved_events": True,
                "include_recent_tail": True,
                "budget_split": {
                    "execution_state_ratio": 0.20,
                    "retrieved_context_ratio": 0.25,
                    "recent_tail_ratio": 0.45,
                    "headroom_ratio": 0.10,
                },
                "retrieval": {"query": "pytest passed budgeted", "top_k": 5},
            },
        },
    ).json()

    generated = [message for message in prepare["messages"] if message.get("metadata", {}).get("mneme_generated")]
    rendered = "\n".join(message["content"] for message in prepare["messages"])
    assert "[MNEME EXECUTION STATE]" in generated[0]["content"]
    assert "event-output" in generated[0]["content"]
    assert "Continue pytest work" in rendered
    assert "old context" not in rendered
    assert prepare["trace"]["protected_tail_tokens"] > 0
    assert sum(token_estimate(message["content"]) for message in prepare["messages"]) + prepare["trace"]["headroom_tokens"] <= prepare["trace"]["budget_tokens"]

    fresh = start(restarted, "session-fresh")
    assert fresh["session_state"]["classification"] == "FRESH"
    child = start(restarted, "session-child", metadata={"lifecycle": "RESUME", "parent_session_id": "session-parent"})
    assert child["session_state"]["classification"] == "RESUME"
    assert child["session_state"]["requires_context_fill"] is True

    resume_prepare = restarted.post(
        "/v1/context/prepare",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.context_prepare_request.v0",
            "request_id": "prepare-child",
            "prepare_id": "prepare-child",
            "session_id": "session-child",
            "turn_id": "turn-child",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "model": "test-model",
            "context_window_tokens": 100000,
            "budget_tokens": 1000,
            "request_messages": [{"schema_version": "mneme.message.v0", "role": "USER", "content": "Resume."}],
            "policy": {
                "mode": "AUTO",
                "cost_mode": "STANDARD",
                "include_retrieved_events": True,
                "retrieval": {"query": "zzzz unmatched", "top_k": 5},
            },
        },
    ).json()
    child_export = restarted.get("/v1/sessions/session-child/export", headers=auth_headers()).json()

    assert resume_prepare["trace"]["selected_event_refs"][0]["reason"] == "RESUME_CONTEXT_FILL"
    assert child_export["events"] == []
    assert child_export["session_lineage"][0]["old_session_id"] == "session-parent"


def test_mcp_tools_expose_same_data_as_rest_and_preserve_redaction(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN))
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(base_url="http://mneme.test", transport=transport, headers=auth_headers()) as http:
            from mneme_service.mcp_server import create_mcp_server

            server = create_mcp_server(base_url="http://mneme.test", token=TOKEN, transport=transport)
            session = await http.post("/v1/sessions/start", json=session_payload("session-mcp"))
            assert session.status_code == 200, session.text
            ingested = await http.post(
                "/v1/events",
                json={
                    "schema_version": "mneme.event_batch.v0",
                    "session_id": "session-mcp",
                    "events": [event("session-mcp", "event-mcp", "mcp parity evidence sk-mcp-secret")],
                },
            )
            assert ingested.status_code == 200, ingested.text

            payload = {"session_id": "session-mcp", "query": "mcp parity", "top_k": 5}
            rest = (await http.post("/v1/tools/context_search", json=payload)).json()
            mcp_result = await server.call_tool("context_search", {**payload, "scope": "SESSION"})
            mcp = mcp_result[1] if isinstance(mcp_result, tuple) else mcp_result

            assert [item["event_id"] for item in rest["data"]["results"]] == [
                item["event_id"] for item in mcp["data"]["results"]
            ]
            assert "sk-mcp-secret" not in str(rest)
            assert "sk-mcp-secret" not in str(mcp)

    asyncio.run(scenario())
