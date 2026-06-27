from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Sequence

from fastapi.testclient import TestClient

from .app import create_app
from .config import ProviderSettings, Settings

BENCHMARK_AUTH_VALUE = "mneme-benchmark-token"


class BenchmarkEmbeddingProvider:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        batch = list(texts)
        self.calls.append(batch)
        return [benchmark_vector(text) if text.strip() else None for text in batch]


def run_local_benchmark(*, event_count: int = 30, db_path: Path | None = None) -> dict[str, Any]:
    if event_count < 1:
        raise ValueError("event_count must be positive")
    resolved_db = db_path or Path(".local/mneme-benchmark.db")
    resolved_db.parent.mkdir(parents=True, exist_ok=True)
    token = BENCHMARK_AUTH_VALUE
    provider = BenchmarkEmbeddingProvider()
    settings = Settings(
        db_path=resolved_db,
        auth_token=token,
        max_batch_events=max(200, event_count),
        embeddings=ProviderSettings(
            enabled=True,
            provider="benchmark_fake",
            model="benchmark-fake-embedding",
            base_url="memory://benchmark",
        ),
    )
    api = TestClient(create_app(settings, embedding_provider=provider))
    headers = {"Authorization": f"Bearer {token}"}
    session_id = f"benchmark-session-{time.time_ns()}"

    timings: dict[str, float] = {}
    started = time.perf_counter()
    response = api.post("/v1/sessions/start", headers=headers, json=benchmark_session(session_id))
    response.raise_for_status()
    timings["session_start"] = elapsed_ms(started)

    events = [benchmark_event(session_id, index) for index in range(event_count)]
    started = time.perf_counter()
    ingest = api.post(
        "/v1/events",
        headers=headers,
        json={"schema_version": "mneme.event_batch.v0", "session_id": session_id, "events": events},
    )
    ingest.raise_for_status()
    timings["ingest"] = elapsed_ms(started)

    started = time.perf_counter()
    retrieval = api.post(
        "/v1/tools/context_search",
        headers=headers,
        json={"session_id": session_id, "scope": "SESSION", "query": "oauth refresh verifier", "top_k": 5},
    )
    retrieval.raise_for_status()
    timings["retrieval"] = elapsed_ms(started)

    started = time.perf_counter()
    prepared = api.post("/v1/context/prepare", headers=headers, json=benchmark_prepare_request(session_id))
    prepared.raise_for_status()
    timings["context_prepare"] = elapsed_ms(started)

    costs = api.get(f"/v1/costs/session/{session_id}", headers=headers)
    costs.raise_for_status()

    ingest_body = ingest.json()
    retrieval_body = retrieval.json()
    prepared_body = prepared.json()
    costs_body = costs.json()
    retrieval_results = retrieval_body["data"]["results"]
    relevant_event_ids = benchmark_relevant_event_ids(event_count)
    quality_report = benchmark_quality_report(
        query="oauth refresh verifier",
        top_k=5,
        retrieved_event_ids=[str(result["event_id"]) for result in retrieval_results],
        relevant_event_ids=relevant_event_ids,
        event_count=event_count,
    )
    return {
        "schema_version": "mneme.benchmark_report.v0",
        "mode": "LOCAL_FAKE_PROVIDERS",
        "methodology": benchmark_methodology(),
        "db_path": str(resolved_db),
        "session_id": session_id,
        "event_count": event_count,
        "timings_ms": timings,
        "ingest": {
            "accepted": ingest_body["accepted"],
            "duplicates": ingest_body["duplicates"],
            "rejected": len(ingest_body.get("rejected", [])),
        },
        "retrieval": {
            "result_count": len(retrieval_results),
            "strategies": retrieval_body.get("data", {}).get("retrieval", {}).get("strategies", []),
            "trace_id": retrieval_body.get("trace_id"),
        },
        "quality_report": quality_report,
        "context_prepare": {
            "changed": prepared_body["changed"],
            "message_count": len(prepared_body["messages"]),
            "selected_event_count": len(prepared_body.get("trace", {}).get("selected_event_ids", [])),
            "trace_id": prepared_body.get("trace_id"),
        },
        "costs": {
            "embedding_batches": costs_body["embedding_batches"],
            "embedding_items": costs_body["embedding_items"],
            "embedding_input_chars": costs_body["embedding_input_chars"],
            "reranker_calls": costs_body["reranker_calls"],
            "enrichment_calls": costs_body["enrichment_calls"],
        },
        "provider_calls": {
            "embedding_batches": len(provider.calls),
            "embedding_items": sum(len(batch) for batch in provider.calls),
        },
    }


def benchmark_methodology() -> dict[str, str]:
    return {
        "benchmark_type": "LOCAL_SMOKE",
        "providers": "LOCAL_FAKE_PROVIDERS",
        "corpus": "SYNTHETIC_LABELED",
        "comparative_baseline": "NOT_RUN",
        "token_reduction_claim": "NOT_CLAIMED",
        "cost_reduction_claim": "NOT_CLAIMED",
        "token_estimate_methodology": "SERVICE_COST_COUNTERS",
    }


def benchmark_relevant_event_ids(event_count: int) -> set[str]:
    return {f"benchmark-event-{index:04d}" for index in range(event_count) if benchmark_is_relevant(index)}


def benchmark_is_relevant(index: int) -> bool:
    event_type, _, text = benchmark_event_shape(index)
    return event_type in {"USER_MESSAGE", "TOOL_CALL", "TOOL_OUTPUT"} and all(
        term in text.lower() for term in ("oauth", "verifier")
    )


def benchmark_quality_report(
    *,
    query: str,
    top_k: int,
    retrieved_event_ids: list[str],
    relevant_event_ids: set[str],
    event_count: int,
) -> dict[str, Any]:
    retrieved_set = set(retrieved_event_ids)
    true_positive = len(retrieved_set & relevant_event_ids)
    false_positive = len(retrieved_set - relevant_event_ids)
    false_negative = len(relevant_event_ids - retrieved_set)
    true_negative = max(0, event_count - true_positive - false_positive - false_negative)
    reciprocal_rank = 0.0
    for rank, event_id in enumerate(retrieved_event_ids, start=1):
        if event_id in relevant_event_ids:
            reciprocal_rank = round(1 / rank, 6)
            break

    precision_at_k = true_positive / len(retrieved_event_ids) if retrieved_event_ids else 0.0
    recall_at_k = true_positive / len(relevant_event_ids) if relevant_event_ids else 0.0
    return {
        "schema_version": "mneme.benchmark_quality_report.v0",
        "label_source": "SYNTHETIC_CORPUS",
        "query": query,
        "k": top_k,
        "retrieved_event_ids": retrieved_event_ids,
        "relevant_event_ids": sorted(relevant_event_ids),
        "metrics": {
            "precision_at_k": round(precision_at_k, 6),
            "recall_at_k": round(recall_at_k, 6),
            "mrr": reciprocal_rank,
        },
        "confusion_counts": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "true_negative": true_negative,
        },
    }


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)



def benchmark_session(session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "mneme.session.v0",
        "session_id": session_id,
        "agent_id": "benchmark-agent",
        "runtime": "MNEME_BENCHMARK",
        "project_id": "mneme-benchmark",
        "model": "benchmark-model",
        "tokenizer": "approx",
        "context_window_tokens": 100000,
        "cost_mode": "STANDARD",
        "started_at": "2026-06-14T00:00:00Z",
        "metadata": {"source": "mneme benchmark"},
    }


def benchmark_event(session_id: str, index: int) -> dict[str, Any]:
    event_type, role, text = benchmark_event_shape(index)
    parent_event_ids = [f"benchmark-event-{index - 1:04d}"] if index > 0 and event_type != "USER_MESSAGE" else []
    payload: dict[str, Any] = {
        "schema_version": "mneme.event.v0",
        "event_id": f"benchmark-event-{index:04d}",
        "session_id": session_id,
        "turn_id": f"benchmark-turn-{index // 4:04d}",
        "agent_id": "benchmark-agent",
        "runtime": "MNEME_BENCHMARK",
        "role": role,
        "type": event_type,
        "timestamp": f"2026-06-14T00:00:{index % 60:02d}Z",
        "content": {"format": "TEXT", "text": text},
        "parent_event_ids": parent_event_ids,
    }
    if event_type in {"TOOL_CALL", "TOOL_OUTPUT"}:
        payload["tool"] = {"name": "benchmark_tool", "call_id": f"benchmark-call-{index // 2:04d}"}
    return payload


def benchmark_event_shape(index: int) -> tuple[str, str, str]:
    match index % 4:
        case 0:
            return ("USER_MESSAGE", "USER", f"Need oauth refresh verifier evidence for benchmark slice {index}.")
        case 1:
            return ("TOOL_CALL", "TOOL", f"Run benchmark retrieval check for oauth verifier slice {index}.")
        case 2:
            return ("TOOL_OUTPUT", "TOOL", f"Benchmark pytest passed for oauth refresh verifier slice {index}.")
        case _:
            return ("DECISION", "ASSISTANT", f"Decided to keep budgeted context prepare evidence for slice {index}.")


def benchmark_prepare_request(session_id: str) -> dict[str, Any]:
    return {
        "schema_version": "mneme.context_prepare_request.v0",
        "request_id": "benchmark-prepare",
        "prepare_id": "benchmark-prepare",
        "session_id": session_id,
        "turn_id": "benchmark-turn-final",
        "agent_id": "benchmark-agent",
        "runtime": "MNEME_BENCHMARK",
        "model": "benchmark-model",
        "context_window_tokens": 100000,
        "budget_tokens": 1200,
        "request_messages": [
            {"schema_version": "mneme.message.v0", "role": "SYSTEM", "content": "system"},
            {"schema_version": "mneme.message.v0", "role": "USER", "content": "Continue oauth verifier work."},
        ],
        "policy": {
            "mode": "AUTO",
            "cost_mode": "STANDARD",
            "preserve_system_prompt": True,
            "include_execution_state": True,
            "include_recent_tail": True,
            "include_retrieved_events": True,
            "retrieval": {"query": "oauth refresh verifier", "top_k": 8},
            "budget_split": {
                "execution_state_ratio": 0.10,
                "retrieved_evidence_ratio": 0.35,
                "protected_tail_ratio": 0.45,
                "headroom_ratio": 0.10,
            },
        },
    }


def benchmark_vector(text: str) -> list[float]:
    lowered = text.lower()
    if any(term in lowered for term in ("oauth", "refresh", "verifier")):
        return [1.0, 0.0, 0.0]
    if any(term in lowered for term in ("budget", "context", "prepare")):
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]
