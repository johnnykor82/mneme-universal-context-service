from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.config import ProviderSettings, Settings
from mneme_service.enrichment import EnrichmentResult, HttpLLMEnrichmentProvider


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def enrichment_settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        enricher_every_n_turns=1,
        llm_enrichment=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-enrichment-test",
            base_url="https://llm.example.test/v1",
        ),
    )


def start_session(api: TestClient) -> None:
    response = api.post(
        "/v1/sessions/start",
        headers=auth_headers(),
        json={
            "schema_version": "mneme.session.v0",
            "session_id": "session-enrich",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "project_id": "project-1",
            "model": "test-model",
            "tokenizer": "approx",
            "context_window_tokens": 100000,
            "cost_mode": "STANDARD",
            "started_at": "2026-06-12T22:00:00Z",
        },
    )
    assert response.status_code == 200, response.text


def event(event_id: str, text: str) -> dict[str, Any]:
    return {
        "schema_version": "mneme.event.v0",
        "event_id": event_id,
        "session_id": "session-enrich",
        "turn_id": "turn-1",
        "agent_id": "agent-1",
        "runtime": "HERMES",
        "role": "USER",
        "type": "USER_MESSAGE",
        "timestamp": "2026-06-12T22:00:01Z",
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": [],
    }


def ingest(api: TestClient, payload: dict[str, Any]) -> None:
    response = api.post(
        "/v1/events",
        headers=auth_headers(),
        json={"schema_version": "mneme.event_batch.v0", "session_id": "session-enrich", "events": [payload]},
    )
    assert response.status_code == 200, response.text


class StaticEnrichmentProvider:
    def __init__(self) -> None:
        self.calls = 0

    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        self.calls += 1
        return EnrichmentResult(
            updates={
                "intent_label": "implementation",
                "decisions": ["Keep REST canonical sk-enrichment-secret"],
                "active_entities": ["context_prepare", "sk-enrichment-secret"],
                "open_loops": ["Add verification"],
            }
        )


class FailingEnrichmentProvider:
    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        return EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")


class CountingEnrichmentProvider:
    def __init__(self) -> None:
        self.calls = 0

    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        self.calls += 1
        return EnrichmentResult(updates={"intent_label": f"call-{self.calls}"})


def test_http_llm_enrichment_provider_requests_strict_json_and_parses_updates() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "intent_label": "implementation",
                                    "decisions": ["Keep REST canonical"],
                                    "active_entities": ["context_prepare"],
                                    "open_loops": ["Add verification"],
                                }
                            )
                        }
                    }
                ]
            },
        )

    provider = HttpLLMEnrichmentProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-enrichment-test",
            base_url="https://llm.example.test/v1",
            api_key="sk-llm-secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    result = provider.enrich(
        event("event-1", "Continue implementation"),
        {"goal": "Ship parity", "current_step": "Continue implementation"},
    )

    assert result.degraded is False
    assert result.updates["intent_label"] == "implementation"
    assert result.updates["active_entities"] == ["context_prepare"]
    body = json.loads(requests[0].read())
    assert requests[0].url == "https://llm.example.test/v1/chat/completions"
    assert body["response_format"] == {"type": "json_object"}
    assert "Return only JSON" in body["messages"][0]["content"]


def test_http_llm_enrichment_parses_fenced_json_topic_tags_and_decision_rationale() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "```json\n"
                                '{"intent_label":"parity work",'
                                '"topic_tags":["router","enrichment"],'
                                '"decisions":[{"decision":"Keep REST canonical","rationale":"MCP proxies REST"}]}'
                                "\n```"
                            )
                        }
                    }
                ]
            },
        )

    provider = HttpLLMEnrichmentProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-enrichment-test",
            base_url="https://llm.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
    )

    result = provider.enrich(event("event-1", "Continue implementation"), {})

    assert result.degraded is False
    assert result.updates["topic_tags"] == ["router", "enrichment"]
    assert result.updates["decisions"] == [
        {"decision": "Keep REST canonical", "rationale": "MCP proxies REST"}
    ]
    assert result.updates["decision_summary"] == "Keep REST canonical"


def test_http_llm_enrichment_degrades_on_non_json_content() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "not json"}}]})

    provider = HttpLLMEnrichmentProvider(
        ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-enrichment-test",
            base_url="https://llm.example.test/v1",
        ),
        transport=httpx.MockTransport(handler),
        failure_threshold=1,
    )

    result = provider.enrich(event("event-1", "Continue implementation"), {})

    assert result.degraded is True
    assert result.fallback_reason == "LLM_ENRICHMENT_UNAVAILABLE"
    assert result.updates == {}
    assert provider.circuit_open is True


def test_event_ingest_applies_redacted_llm_enrichment_and_records_cost(tmp_path: Path) -> None:
    api = TestClient(create_app(enrichment_settings(tmp_path), enrichment_provider=StaticEnrichmentProvider()))
    start_session(api)

    ingest(api, event("event-1", "Continue implementation with sk-user-secret"))

    state = api.post(
        "/v1/tools/get_execution_state",
        headers=auth_headers(),
        json={"session_id": "session-enrich"},
    )
    assert state.status_code == 200
    data = state.json()["data"]
    assert data["enrichment"]["intent_label"] == "implementation"
    assert data["enrichment"]["decisions"] == ["Keep REST canonical [REDACTED]"]
    assert data["active_entities"] == ["context_prepare", "[REDACTED]"]
    assert "sk-user-secret" not in str(data)

    history = api.post(
        "/v1/tools/get_goal_history",
        headers=auth_headers(),
        json={"session_id": "session-enrich", "limit": 5},
    )
    assert history.json()["data"]["history"][-1]["intent_label"] == "implementation"
    assert history.json()["data"]["history"][-1]["decisions"] == ["Keep REST canonical [REDACTED]"]

    cost = api.get("/v1/costs/session/session-enrich", headers=auth_headers())
    assert cost.json()["enrichment_calls"] == 1
    assert cost.json()["failures"]["enrichment_failures"] == 0


def test_event_ingest_runs_enrichment_on_configured_turn_cadence(tmp_path: Path) -> None:
    provider = CountingEnrichmentProvider()
    api = TestClient(
        create_app(
            Settings(
                db_path=tmp_path / "mneme.db",
                auth_token=TOKEN,
                enricher_every_n_turns=2,
                enricher_on_segment_boundary=False,
                llm_enrichment=ProviderSettings(
                    enabled=True,
                    provider="openai_compatible",
                    model="gpt-enrichment-test",
                    base_url="https://llm.example.test/v1",
                ),
            ),
            enrichment_provider=provider,
        )
    )
    start_session(api)

    ingest(api, event("event-1", "First turn"))
    ingest(api, event("event-2", "Second turn"))

    assert provider.calls == 1
    cost = api.get("/v1/costs/session/session-enrich", headers=auth_headers())
    assert cost.json()["enrichment_calls"] == 1
    state = api.post(
        "/v1/tools/get_execution_state",
        headers=auth_headers(),
        json={"session_id": "session-enrich"},
    )
    assert state.json()["data"]["enrichment"]["intent_label"] == "call-1"


def test_event_ingest_keeps_deterministic_state_when_llm_enrichment_fails(tmp_path: Path) -> None:
    api = TestClient(create_app(enrichment_settings(tmp_path), enrichment_provider=FailingEnrichmentProvider()))
    start_session(api)

    ingest(api, event("event-1", "Continue implementation"))

    state = api.post(
        "/v1/tools/get_execution_state",
        headers=auth_headers(),
        json={"session_id": "session-enrich"},
    )
    assert state.json()["data"]["goal"] == "Continue implementation"
    assert state.json()["data"]["enrichment"] == {
        "decision_summary": None,
        "intent_label": None,
        "topic_tags": [],
    }

    cost = api.get("/v1/costs/session/session-enrich", headers=auth_headers())
    assert cost.json()["enrichment_calls"] == 1
    assert cost.json()["failures"]["enrichment_failures"] == 1
