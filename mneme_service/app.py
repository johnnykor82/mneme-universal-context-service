from __future__ import annotations

import hashlib
import html
import io
import json
import logging
import math
import tarfile
import tempfile
import threading
import time
import re
from collections import Counter
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Mapping

from fastapi import Body, Depends, FastAPI, Header, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .classifier import INTENT_NEW_TASK, INTENT_SWITCH, classify_intent, extract_entities
from .config import ProviderHealth, Settings, validate_settings
from .embeddings import EmbeddingIndex, EmbeddingProvider, OpenAICompatibleEmbeddingProvider, embedding_record_from_event
from .enrichment import (
    EnrichmentProvider,
    EnrichmentResult,
    HttpLLMEnrichmentProvider,
    apply_enrichment_updates,
)
from .errors import (
    MnemeError,
    bad_request,
    conflict,
    failed_precondition,
    forbidden,
    not_found,
    payload_too_large,
    provider_unavailable,
    range_not_satisfiable,
    rate_limited,
    storage_busy,
    unauthenticated,
    unsupported_media_type,
    validation_error,
)
from .reranker import HttpRerankerProvider, RerankerProvider, RerankResult
from .security import Principal, RedactionTimeoutError, authenticate_bearer, redact, redact_with_metadata
from .segments import update_segment_for_event
from pydantic import BaseModel

from .schemas import (
    BlobDeleteResponse,
    BlobGcRequest,
    BlobGcResponse,
    BlobRecordResponse,
    CapabilitiesResponse,
    ContextPrepareRequest,
    ContextPrepareResponse,
    CostReportResponse,
    ErrorEnvelope,
    EventBatchRequest,
    EventBatchResponse,
    ExecutionStateUpdateRequest,
    ExecutionStateUpdateResponse,
    HealthResponse,
    MetricsResponse,
    ReindexCancelRequest,
    ReindexJobResponse,
    ReindexRequest,
    RetentionCleanupRequest,
    RetentionCleanupResponse,
    Message,
    MessageContentPart,
    SegmentCloseRequest,
    SegmentEventsResponse,
    SegmentListResponse,
    SegmentResponse,
    SegmentStartRequest,
    SessionReadinessRequest,
    SessionCloseResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionSummaryResponse,
    TraceResponse,
    ToolRequestPayload,
    ToolResponseEnvelope,
    TurnCompleteRequest,
    TurnCompleteResponse,
)
from .session_drift import LINEAGE_KEYS, classify_session_start, first_metadata_string
from .state import apply_event_to_state
from .storage import (
    AUTH_FAILURE_SESSION_ID,
    CURRENT_SCHEMA_VERSION,
    StorageBusy,
    Store,
    WriterQueueFull,
    normalize_match_value,
    session_project_key as session_payload_project_key,
    strip_rich_segment_fields,
)
from .tool_names import TOOL_NAMES
from .utils import canonical_json, new_id, now_ms, sha256_text, text_from_content, token_estimate

ACCESS_LOGGER = logging.getLogger("mneme_service.access")

SUPPORTED_SCHEMAS = {
    "session": ["mneme.session.v0"],
    "session_start": ["mneme.session_start.v0"],
    "session_export": ["mneme.session_export.v0"],
    "session_export_manifest": ["mneme.session_export_manifest.v0"],
    "event_batch": ["mneme.event_batch.v0"],
    "event": ["mneme.event.v0"],
    "event_summary": ["mneme.event_summary.v0"],
    "turn": ["mneme.turn.v0"],
    "tool_request": ["mneme.tool_request.v0"],
    "message": ["mneme.message.v0"],
    "context_prepare_request": ["mneme.context_prepare_request.v0"],
    "context_prepare_response": ["mneme.context_prepare_response.v0"],
    "retention_cleanup_request": ["mneme.retention_cleanup_request.v0"],
    "retention_cleanup_result": ["mneme.retention_cleanup_result.v0"],
    "trace": ["mneme.trace.v0"],
    "audit_record": ["mneme.audit_record.v0"],
    "cost_report": ["mneme.cost_report.v0"],
    "session_state": ["mneme.session_state.v0"],
    "session_lineage": ["mneme.session_lineage.v0"],
    "segment": ["mneme.segment.v0"],
    "segment_start": ["mneme.segment_start.v0"],
    "segment_close": ["mneme.segment_close.v0"],
    "graph_edge": ["mneme.graph_edge.v0"],
    "blob": ["mneme.blob.v0"],
    "reindex_job": ["mneme.reindex_job.v0"],
    "execution_state": ["mneme.execution_state.v0"],
    "execution_state_update": ["mneme.execution_state_update.v0"],
    "execution_state_update_result": ["mneme.execution_state_update_result.v0"],
    "state_history_entry": ["mneme.state_history_entry.v0"],
}

TEXT_LIKE_MEDIA_TYPES = {
    "application/json",
    "application/ld+json",
    "application/toml",
    "application/xml",
    "application/yaml",
    "application/x-yaml",
    "application/x-www-form-urlencoded",
}

FRESHNESS_VALUES = {"CURRENT", "RECENT", "HISTORICAL", "STALE_OR_CONFLICTING", "UNKNOWN"}


def topic_entropy_from_text(text: str) -> float:
    if not isinstance(text, str):
        return 0.0
    tokens = [token for token in re.findall(r"[A-Za-z0-9']+", text.lower()) if token]
    if len(tokens) < 2:
        return 0.0
    counts = Counter(tokens)
    if len(counts) <= 1:
        return 0.0
    total = float(sum(counts.values()))
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    max_entropy = math.log2(len(counts))
    if max_entropy <= 0:
        return 0.0
    return max(0.0, min(1.0, entropy / max_entropy))


def is_text_like_media_type(media_type: Any) -> bool:
    if not isinstance(media_type, str):
        return False
    normalized = media_type.split(";", 1)[0].strip().lower()
    return normalized.startswith("text/") or normalized in TEXT_LIKE_MEDIA_TYPES or normalized.endswith("+json") or normalized.endswith("+xml")


def is_binary_metadata_only_content(content: Any) -> bool:
    return isinstance(content, dict) and content.get("format") == "BYTES_REF" and not is_text_like_media_type(content.get("media_type"))


EVENT_TYPE_WEIGHTS = {
    "ERROR": 1.0,
    "TOOL_CALL": 1.0,
    "COMMAND_OUTPUT": 0.9,
    "TOOL_OUTPUT": 0.85,
    "DECISION": 0.75,
    "ASSISTANT_MESSAGE": 0.75,
    "USER_MESSAGE": 0.7,
    "NOTE": 0.6,
}

EXECUTION_STATE_ALLOWED_FIELDS = {
    "goal",
    "current_step",
    "open_loops",
    "last_tool",
    "last_tool_output_summary",
    "decision_stack",
    "active_entities",
    "turn_count",
    "segment_id",
    "enrichment",
}

EXECUTION_STATE_PROVENANCE_FIELDS = {"event_id", "turn_id", "adapter_trace_id"}
EVENT_IMPORTANCE_VALUES = {"CRITICAL", "HIGH", "NORMAL", "LOW"}
SEGMENT_CREATED_BY_VALUES = {"ADAPTER", "AUTOMATIC", "ENRICHMENT", "IMPORTER"}
SEGMENT_OUTCOMES = {"COMPLETED", "ABANDONED", "SUPERSEDED", "INTERRUPTED", "CANCELLED", "UNKNOWN"}
SEGMENT_PUBLIC_STATUSES = {"OPEN", "CLOSED", "ABANDONED", "SUPERSEDED"}
TURN_COMPLETE_STATUSES = {"COMPLETED", "FAILED", "INTERRUPTED", "CANCELLED"}


class InFlightReadTracker:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._lock = threading.Lock()

    @contextmanager
    def enter(self, session_id: str):
        with self._lock:
            self._counts[session_id] = self._counts.get(session_id, 0) + 1
        try:
            yield
        finally:
            with self._lock:
                remaining = self._counts.get(session_id, 0) - 1
                if remaining > 0:
                    self._counts[session_id] = remaining
                else:
                    self._counts.pop(session_id, None)

    def count(self, session_id: str) -> int:
        with self._lock:
            return self._counts.get(session_id, 0)


class ProviderHealthState:
    def __init__(self) -> None:
        self._status = "UNKNOWN"
        self._checked_at_ms: int | None = None
        self._failure_count = 0
        self._last_error_code: str | None = None
        self._lock = threading.Lock()

    def record_success(self) -> None:
        with self._lock:
            self._status = "AVAILABLE"
            self._checked_at_ms = now_ms()
            self._failure_count = 0
            self._last_error_code = None

    def record_failure(self, error_code: str) -> None:
        with self._lock:
            self._status = "DEGRADED"
            self._checked_at_ms = now_ms()
            self._failure_count += 1
            self._last_error_code = error_code

    def snapshot(self) -> ProviderHealth:
        with self._lock:
            return ProviderHealth(
                status=self._status,
                checked_at_ms=self._checked_at_ms,
                failure_count=self._failure_count,
                last_error_code=self._last_error_code,
            )


class HealthTrackingEmbeddingProvider:
    def __init__(self, provider: EmbeddingProvider, health: ProviderHealthState) -> None:
        self.provider = provider
        self.health = health

    def embed_texts(self, texts: Any) -> list[list[float] | None]:
        text_items = list(texts)
        try:
            embeddings = self.provider.embed_texts(text_items)
        except Exception:
            self.health.record_failure("EMBEDDINGS_UNAVAILABLE")
            raise
        if any(isinstance(text, str) and text.strip() for text in text_items) and not any(embeddings):
            self.health.record_failure("EMBEDDINGS_UNAVAILABLE")
        else:
            self.health.record_success()
        return embeddings


class HealthTrackingRerankerProvider:
    def __init__(self, provider: RerankerProvider, health: ProviderHealthState) -> None:
        self.provider = provider
        self.health = health

    def rerank(self, query: str, documents: Any) -> RerankResult:
        try:
            result = self.provider.rerank(query, documents)
        except Exception:
            self.health.record_failure("RERANKER_UNAVAILABLE")
            raise
        if result.degraded:
            self.health.record_failure(result.fallback_reason or "RERANKER_UNAVAILABLE")
        elif query.strip() and documents:
            self.health.record_success()
        return result


class HealthTrackingEnrichmentProvider:
    def __init__(self, provider: EnrichmentProvider, health: ProviderHealthState) -> None:
        self.provider = provider
        self.health = health

    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        try:
            result = self.provider.enrich(event_payload, state)
        except Exception:
            self.health.record_failure("LLM_ENRICHMENT_UNAVAILABLE")
            raise
        if result.degraded:
            self.health.record_failure(result.fallback_reason or "LLM_ENRICHMENT_UNAVAILABLE")
        else:
            self.health.record_success()
        return result


def create_app(
    settings: Settings | None = None,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    reranker_provider: RerankerProvider | None = None,
    enrichment_provider: EnrichmentProvider | None = None,
) -> FastAPI:
    settings = validate_settings(settings or Settings())
    validate_provider_startup(
        settings,
        embedding_provider=embedding_provider,
        reranker_provider=reranker_provider,
        enrichment_provider=enrichment_provider,
    )
    embeddings_available = settings.embeddings.runtime_available(
        injected_provider=embedding_provider is not None
    )
    reranker_available = settings.reranker.runtime_available(
        injected_provider=reranker_provider is not None
    )
    enrichment_available = settings.llm_enrichment.runtime_available(
        injected_provider=enrichment_provider is not None
    )
    if settings.require_embeddings and not embeddings_available:
        raise RuntimeError(
            "Embeddings are required but no enabled, configured embedding provider is available."
        )
    provider_health = {
        "embeddings": ProviderHealthState(),
        "reranker": ProviderHealthState(),
        "llm_enrichment": ProviderHealthState(),
    }
    store = Store(
        settings.db_path,
        max_writer_queue_depth=settings.max_writer_queue_depth,
        startup_integrity_check=settings.startup_integrity_check,
        backup_before_migrate=settings.backup_before_migrate,
        no_backup_before_migrate=settings.no_backup_before_migrate,
    )
    embedding_index: EmbeddingIndex | None = None
    if embeddings_available:
        provider = HealthTrackingEmbeddingProvider(
            embedding_provider or OpenAICompatibleEmbeddingProvider(settings.embeddings),
            provider_health["embeddings"],
        )
        embedding_index = EmbeddingIndex(
            store,
            provider,
            model_id=settings.embeddings.model or "",
            batch_size=settings.embeddings.batch_size,
            centroid_window=settings.centroid_window,
        )
    if settings.reindex_on_model_change:
            reindex_missing_embeddings(store, embedding_index, settings)
    reranker: RerankerProvider | None = None
    if reranker_available:
        reranker = HealthTrackingRerankerProvider(
            reranker_provider or HttpRerankerProvider(settings.reranker),
            provider_health["reranker"],
        )
    enricher: EnrichmentProvider | None = None
    if enrichment_available:
        enricher = HealthTrackingEnrichmentProvider(
            enrichment_provider or HttpLLMEnrichmentProvider(settings.llm_enrichment),
            provider_health["llm_enrichment"],
        )
    app = FastAPI(title="Mneme Context Service", version="0.1.0")
    app.state.settings = settings
    app.state.store = store
    app.state.embedding_index = embedding_index
    app.state.reranker = reranker
    app.state.enrichment_provider = enricher
    app.state.provider_health = provider_health
    app.state.in_flight_reads = InFlightReadTracker()
    store.in_flight_reads = app.state.in_flight_reads
    reindex_jobs: dict[str, dict[str, Any]] = {}
    http_metrics: dict[tuple[str, str, int], dict[str, float]] = {}
    reindex_provider_recent_outcomes: list[bool] = []
    reindex_provider_circuit_open_until = 0.0

    def route_template(request: Request) -> str:
        route = request.scope.get("route")
        path = getattr(route, "path", None)
        return str(path or request.url.path)

    def record_http_metric(method: str, path: str, status_code: int, latency_ms: float) -> None:
        key = (method.upper(), path, int(status_code))
        bucket = http_metrics.setdefault(key, {"count": 0.0, "latency_ms": 0.0})
        bucket["count"] += 1.0
        bucket["latency_ms"] += max(0.0, float(latency_ms))

    def request_header(request: Request, name: str) -> str | None:
        value = request.headers.get(name)
        return value if value else None

    def emit_access_log(request: Request, *, status_code: int, latency_ms: float, error_code: str | None = None) -> None:
        record = {
            "event": "http_request",
            "request_id": request_header(request, "X-Request-Id") or new_id("request"),
            "trace_id": request_header(request, "X-Mneme-Trace-Id"),
            "method": request.method.upper(),
            "endpoint": route_template(request),
            "status": int(status_code),
            "error_code": error_code,
            "project_scope": request_header(request, "X-Mneme-Project-Isolation-Key"),
            "session_id": request_header(request, "X-Mneme-Session-Id"),
            "latency_ms": round(max(0.0, float(latency_ms)), 3),
            "background_job_id": request_header(request, "X-Mneme-Background-Job-Id"),
        }
        ACCESS_LOGGER.info(canonical_json(record))

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = (time.perf_counter() - start) * 1000
            record_http_metric(
                request.method,
                route_template(request),
                500,
                latency_ms,
            )
            emit_access_log(request, status_code=500, latency_ms=latency_ms, error_code="INTERNAL_SERVER_ERROR")
            raise
        latency_ms = (time.perf_counter() - start) * 1000
        record_http_metric(
            request.method,
            route_template(request),
            response.status_code,
            latency_ms,
        )
        emit_access_log(request, status_code=response.status_code, latency_ms=latency_ms)
        response.headers.setdefault("X-Mneme-Request-Id", request_header(request, "X-Request-Id") or "")
        return response

    def prometheus_label_value(value: Any) -> str:
        return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

    def prometheus_line(name: str, labels: dict[str, Any] | None, value: int | float) -> str:
        if labels:
            rendered_labels = ",".join(
                f'{key}="{prometheus_label_value(label_value)}"'
                for key, label_value in sorted(labels.items())
            )
            return f"{name}{{{rendered_labels}}} {value}"
        return f"{name} {value}"

    def prometheus_family(lines: list[str], name: str, metric_type: str, help_text: str) -> None:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} {metric_type}")

    def prometheus_metrics_text(include_current_metrics_request: bool = False) -> str:
        snapshot = store.operations_metrics_snapshot(
            settings.embeddings.model if embedding_index else None
        )
        lines: list[str] = []
        http_snapshot = dict(http_metrics)
        if include_current_metrics_request:
            current_key = ("GET", "/v1/metrics", 200)
            current_bucket = dict(http_snapshot.get(current_key, {"count": 0.0, "latency_ms": 0.0}))
            current_bucket["count"] += 1.0
            http_snapshot[current_key] = current_bucket

        prometheus_family(lines, "mneme_http_requests_total", "counter", "HTTP requests by method, endpoint, and status.")
        for (method, path, status), bucket in sorted(http_snapshot.items()):
            lines.append(
                prometheus_line(
                    "mneme_http_requests_total",
                    {"method": method, "endpoint": path, "status": status},
                    int(bucket["count"]),
                )
            )
        prometheus_family(lines, "mneme_http_request_latency_ms", "counter", "Total HTTP request latency in milliseconds.")
        for (method, path, status), bucket in sorted(http_snapshot.items()):
            lines.append(
                prometheus_line(
                    "mneme_http_request_latency_ms",
                    {"method": method, "endpoint": path, "status": status},
                    round(float(bucket["latency_ms"]), 3),
                )
            )

        prometheus_family(lines, "mneme_provider_calls_total", "counter", "Provider calls by provider family.")
        prometheus_family(lines, "mneme_provider_failures_total", "counter", "Provider failures by provider family.")
        prometheus_family(lines, "mneme_provider_latency_ms", "counter", "Provider latency in milliseconds by provider family.")
        for provider, values in sorted(snapshot["provider_metrics"].items()):
            labels = {"provider": provider}
            lines.append(prometheus_line("mneme_provider_calls_total", labels, values["calls"]))
            lines.append(prometheus_line("mneme_provider_failures_total", labels, values["failures"]))
            lines.append(prometheus_line("mneme_provider_latency_ms", labels, values["latency_ms"]))

        persisted_reindex_jobs = store.list_reindex_jobs()
        queued_reindex_jobs = sum(
            1
            for job in persisted_reindex_jobs
            if job.get("status") in {"QUEUED", "RUNNING", "WAITING_FOR_PROVIDER"}
        )
        prometheus_family(lines, "mneme_writer_queue_depth", "gauge", "Current foreground writer queue depth.")
        lines.append(prometheus_line("mneme_writer_queue_depth", None, store.writer_queue_depth))
        prometheus_family(lines, "mneme_background_job_backlog", "gauge", "Current background job backlog.")
        lines.append(
            prometheus_line(
                "mneme_background_job_backlog",
                None,
                queued_reindex_jobs + store.writer_queue_backlog,
            )
        )

        prometheus_family(lines, "mneme_embedding_events_total", "gauge", "Events by embedding status.")
        for status, count in sorted(snapshot["embedding_statuses"].items()):
            lines.append(prometheus_line("mneme_embedding_events_total", {"status": status}, count))

        reindex_counts = {status: 0 for status in ["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "WAITING_FOR_PROVIDER"]}
        for job in persisted_reindex_jobs:
            status = str(job.get("status") or "UNKNOWN")
            reindex_counts[status] = reindex_counts.get(status, 0) + 1
        prometheus_family(lines, "mneme_reindex_jobs_total", "gauge", "Reindex jobs by status.")
        for status, count in sorted(reindex_counts.items()):
            lines.append(prometheus_line("mneme_reindex_jobs_total", {"status": status}, count))

        prometheus_family(lines, "mneme_retention_sweeps_total", "counter", "Retention cleanup and maintenance sweeps.")
        lines.append(prometheus_line("mneme_retention_sweeps_total", None, snapshot["retention_sweeps"]))
        prometheus_family(lines, "mneme_blob_storage_bytes", "gauge", "Stored blob bytes.")
        lines.append(prometheus_line("mneme_blob_storage_bytes", None, snapshot["blob_storage"]["bytes"]))
        prometheus_family(lines, "mneme_blob_storage_count", "gauge", "Stored blob count.")
        lines.append(prometheus_line("mneme_blob_storage_count", None, snapshot["blob_storage"]["count"]))
        prometheus_family(lines, "mneme_startup_integrity_status", "gauge", "Startup integrity status, 1 means current.")
        lines.append(prometheus_line("mneme_startup_integrity_status", None, 1))

        prometheus_family(lines, "mneme_intent_classifications_total", "counter", "Intent classification counters by label.")
        intent_labels = snapshot["intent_labels"] or {"UNKNOWN": 0}
        for label, count in sorted(intent_labels.items()):
            lines.append(prometheus_line("mneme_intent_classifications_total", {"label": label}, count))
        prometheus_family(lines, "mneme_segment_rollovers_total", "counter", "Segment rollover counters by reason.")
        rollovers = snapshot["segment_rollovers"] or {"UNKNOWN": 0}
        for reason, count in sorted(rollovers.items()):
            lines.append(prometheus_line("mneme_segment_rollovers_total", {"reason": reason}, count))
        prometheus_family(lines, "mneme_routing_modes_total", "counter", "Routing mode counters.")
        routing_modes = snapshot["routing_modes"] or {"UNKNOWN": 0}
        for mode, count in sorted(routing_modes.items()):
            lines.append(prometheus_line("mneme_routing_modes_total", {"mode": mode}, count))
        prometheus_family(lines, "mneme_indexing_compressions_total", "counter", "Indexing compression counters by event type.")
        compressions = snapshot["compression_by_type"] or {"UNKNOWN": 0}
        for event_type, count in sorted(compressions.items()):
            lines.append(prometheus_line("mneme_indexing_compressions_total", {"event_type": event_type}, count))
        prometheus_family(lines, "mneme_retrieval_quality_precision_at_k", "gauge", "Labeled retrieval precision@k when evaluation labels are supplied.")
        lines.append(prometheus_line("mneme_retrieval_quality_precision_at_k", {"k": 0}, 0))
        lines.append("")
        return "\n".join(lines)

    def reindex_provider_circuit_allows_call() -> bool:
        nonlocal reindex_provider_circuit_open_until
        if reindex_provider_circuit_open_until <= 0:
            return True
        if time.monotonic() >= reindex_provider_circuit_open_until:
            reindex_provider_circuit_open_until = 0.0
            reindex_provider_recent_outcomes.clear()
            return True
        return False

    def record_reindex_provider_outcome(success: bool) -> None:
        nonlocal reindex_provider_circuit_open_until
        reindex_provider_recent_outcomes.append(bool(success))
        max_window = max(1, settings.reindex_provider_circuit_breaker_min_calls)
        del reindex_provider_recent_outcomes[:-max_window]
        if len(reindex_provider_recent_outcomes) < max_window:
            return
        failures = sum(1 for outcome in reindex_provider_recent_outcomes if not outcome)
        failure_ratio = failures / len(reindex_provider_recent_outcomes)
        if failure_ratio >= settings.reindex_provider_circuit_breaker_failure_ratio:
            reindex_provider_circuit_open_until = (
                time.monotonic() + settings.reindex_provider_circuit_breaker_open_seconds
            )

    @app.exception_handler(MnemeError)
    async def mneme_error_handler(_: Request, exc: MnemeError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=redact(exc.detail))

    @app.exception_handler(WriterQueueFull)
    async def writer_queue_full_handler(_: Request, __: WriterQueueFull) -> JSONResponse:
        exc = rate_limited(
            "Writer queue is full.",
            reason="WRITER_QUEUE_FULL",
            max_writer_queue_depth=settings.max_writer_queue_depth,
        )
        return JSONResponse(status_code=exc.status_code, content=redact(exc.detail))

    @app.exception_handler(StorageBusy)
    async def storage_busy_handler(_: Request, __: StorageBusy) -> JSONResponse:
        exc = storage_busy(
            "SQLite storage remained busy after bounded internal retries.",
            reason="SQLITE_STORAGE_BUSY",
        )
        return JSONResponse(status_code=exc.status_code, content=redact(exc.detail))

    def require_auth(
        request: Request,
        authorization: Annotated[str | None, Header(include_in_schema=False)] = None,
    ) -> Principal:
        principal = authenticate_bearer(authorization, settings)
        if principal is None:
            store.add_audit(
                AUTH_FAILURE_SESSION_ID,
                "AUTH_FAILURE",
                "AUTH",
                [],
                principal={
                    "name": "UNAUTHENTICATED",
                    "role": "UNAUTHENTICATED",
                    "project_scopes": [],
                },
                request={
                    "method": request.method,
                    "path": request.url.path,
                },
                result={"status_code": 401, "error_code": "UNAUTHENTICATED"},
            )
            raise unauthenticated()
        return principal

    def idempotency_request_hash(payload: dict[str, Any]) -> str:
        return sha256_text(canonical_json(payload))

    def normalized_idempotency_key(value: str | None) -> str | None:
        if value is None:
            return None
        key = value.strip()
        if not key:
            raise validation_error("Idempotency-Key must be non-empty.", header="Idempotency-Key")
        return key

    def replay_idempotent_response(
        *,
        principal: Principal,
        method: str,
        path: str,
        idempotency_key: str | None,
        request_hash: str,
    ) -> dict[str, Any] | None:
        key = normalized_idempotency_key(idempotency_key)
        if key is None:
            return None
        record = store.get_idempotency_record(
            principal_name=principal.name,
            method=method,
            path=path,
            idempotency_key=key,
        )
        if record is None:
            return None
        if record["request_hash"] != request_hash:
            raise conflict(
                "Idempotency-Key reused with a different request.",
                method=method,
                path=path,
            )
        return record["response"]

    def record_idempotent_response(
        *,
        principal: Principal,
        method: str,
        path: str,
        idempotency_key: str | None,
        request_hash: str,
        response: dict[str, Any],
    ) -> None:
        key = normalized_idempotency_key(idempotency_key)
        if key is None:
            return
        store.put_idempotency_record(
            principal_name=principal.name,
            method=method,
            path=path,
            idempotency_key=key,
            request_hash=request_hash,
            response=response,
        )

    def require_session(session_id: str) -> None:
        if not store.has_session(session_id):
            raise not_found("Session not found.", **session_not_found_details(store, session_id))

    def validate_session_id(session_id: str) -> str:
        if not session_id:
            raise validation_error("session_id must be non-empty.", field="session_id")
        if len(session_id) > settings.max_session_id_length:
            raise validation_error(
                "session_id exceeds max_session_id_length.",
                field="session_id",
                max_length=settings.max_session_id_length,
            )
        if any(part in session_id for part in ("/", "\\", "?", "#", "..")):
            raise validation_error("session_id must not contain path or URL delimiters.", field="session_id")
        return session_id

    def visible_project_keys(principal: Principal, requested_project_key: str | None = None) -> list[str] | None:
        if requested_project_key:
            if not principal.can_access_project(requested_project_key):
                raise forbidden(
                    "Requested project is outside the caller project scope.",
                    project_isolation_key=requested_project_key,
                )
            return [requested_project_key]
        if principal.all_projects:
            return None
        return list(principal.project_scopes)

    def require_project_access(
        principal: Principal,
        project_key: str | None,
        *,
        session_id: str | None = None,
    ) -> None:
        if principal.can_access_project(project_key):
            return
        raise forbidden(
            "Requested session is outside the caller project scope.",
            session_id=session_id,
            scope="PROJECT",
        )

    def require_session_access(
        principal: Principal,
        session_id: str,
        *,
        requested_project_key: str | None = None,
    ) -> None:
        validate_session_id(session_id)
        if not store.has_session(session_id):
            raise not_found(
                "Session not found.",
                **session_not_found_details(
                    store,
                    session_id,
                    project_isolation_keys=visible_project_keys(principal),
                ),
            )
        project_key = store.session_project_key(session_id)
        if requested_project_key and project_key != requested_project_key:
            raise forbidden(
                "Requested session is outside the caller project scope.",
                session_id=session_id,
                scope="PROJECT",
            )
        require_project_access(principal, project_key, session_id=session_id)

    def require_blob_access(principal: Principal, blob_id: str) -> dict[str, Any]:
        blob = store.get_blob_metadata(blob_id)
        if blob is None:
            raise not_found("Blob not found.", blob_id=blob_id)
        require_project_access(
            principal,
            blob.get("project_isolation_key"),
            session_id=blob.get("session_id"),
        )
        return blob

    def normalize_reindex_scope(payload: dict[str, Any], principal: Principal) -> tuple[str, str | None, str | None]:
        scope = str(payload.get("scope") or "PROJECT").strip().upper()
        if scope not in {"ALL", "PROJECT", "SESSION"}:
            raise validation_error("scope must be ALL, PROJECT, or SESSION.", field="scope")
        project_key = payload.get("project_isolation_key")
        session_id = payload.get("session_id")
        if project_key is not None and not isinstance(project_key, str):
            raise validation_error("project_isolation_key must be a string or null.", field="project_isolation_key")
        if session_id is not None and not isinstance(session_id, str):
            raise validation_error("session_id must be a string or null.", field="session_id")
        if scope == "ALL":
            if not principal.all_projects:
                raise forbidden("Unscoped reindex requires owner all-projects scope.", scope=scope)
            return scope, None, None
        if scope == "PROJECT":
            if not project_key:
                raise validation_error("PROJECT reindex requires project_isolation_key.", field="project_isolation_key")
            visible_project_keys(principal, project_key)
            return scope, project_key, None
        if not session_id:
            raise validation_error("SESSION reindex requires session_id.", field="session_id")
        require_session_access(principal, session_id, requested_project_key=project_key)
        return scope, store.session_project_key(session_id), session_id

    def normalize_reindex_statuses(payload: dict[str, Any]) -> list[str]:
        raw_statuses = payload.get("statuses") or ["PENDING", "FAILED"]
        if not isinstance(raw_statuses, list):
            raise validation_error("statuses must be a list.", field="statuses")
        statuses = [str(status).strip().upper() for status in raw_statuses if str(status).strip()]
        if not statuses:
            raise validation_error("statuses must not be empty.", field="statuses")
        allowed = {"PENDING", "FAILED"}
        invalid = sorted(set(statuses) - allowed)
        if invalid:
            raise validation_error("statuses may only contain PENDING or FAILED.", field="statuses", invalid=invalid)
        return statuses

    def normalize_reindex_max_job_events(payload: dict[str, Any]) -> int:
        raw_value = payload.get("max_job_events", settings.reindex_max_job_events)
        try:
            max_job_events = int(raw_value)
        except (TypeError, ValueError):
            raise validation_error("max_job_events must be an integer.", field="max_job_events")
        if max_job_events <= 0:
            raise validation_error("max_job_events must be positive.", field="max_job_events")
        return min(max_job_events, settings.reindex_max_job_events)

    def require_reindex_job_access(principal: Principal, job_id: str) -> dict[str, Any]:
        job = store.get_reindex_job(job_id)
        if job is None:
            raise not_found("Reindex job not found.", job_id=job_id)
        if job["scope"] == "ALL":
            if not principal.all_projects:
                raise not_found("Reindex job not found.", job_id=job_id)
            return job
        try:
            if job.get("session_id"):
                require_session_access(principal, job["session_id"], requested_project_key=job.get("project_isolation_key"))
            else:
                require_project_access(principal, job.get("project_isolation_key"))
        except MnemeError as exc:
            if exc.status_code in {403, 404}:
                raise not_found("Reindex job not found.", job_id=job_id) from exc
            raise
        return job

    def run_reindex_job_once(job_id: str) -> dict[str, Any]:
        job = store.get_reindex_job(job_id)
        if job is None:
            raise not_found("Reindex job not found.", job_id=job_id)
        if job["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            return job
        if embedding_index is None:
            created_at = str(job.get("created_at") or "")
            try:
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_dt = datetime.now(timezone.utc)
            waited_seconds = (datetime.now(timezone.utc) - created_dt).total_seconds()
            if waited_seconds >= settings.reindex_provider_wait_timeout_seconds:
                job["status"] = "FAILED"
                job["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                job["error"] = {
                    "reason": "PROVIDER_WAIT_TIMEOUT",
                    "provider_wait_timeout_seconds": settings.reindex_provider_wait_timeout_seconds,
                }
                store.update_reindex_job(job)
                return job
            if job["status"] != "WAITING_FOR_PROVIDER":
                job["status"] = "WAITING_FOR_PROVIDER"
                store.update_reindex_job(job)
            return job

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if not job.get("started_at"):
            job["started_at"] = now
        job["status"] = "RUNNING"
        store.update_reindex_job(job)

        progress = job.get("progress") if isinstance(job.get("progress"), dict) else {}
        candidate_count = int(progress.get("candidate_count") or 0)
        processed_count = int(progress.get("processed_count") or 0)
        failed_count = int(progress.get("failed_count") or 0)
        if processed_count + failed_count >= candidate_count:
            job["status"] = "COMPLETED" if failed_count == 0 else "FAILED"
            job["completed_at"] = now
            store.update_reindex_job(job)
            return job

        latest = store.get_reindex_job(job_id)
        if latest and latest.get("status") == "CANCELLED":
            return latest

        candidates = store.list_reindex_candidates(
            scope=str(job["scope"]),
            project_isolation_key=job.get("project_isolation_key"),
            session_id=job.get("session_id"),
            statuses=[str(status) for status in job.get("statuses", ["PENDING", "FAILED"])],
            force=bool(job.get("force", False)),
            embedding_model_id=embedding_index.model_id,
            offset=processed_count + failed_count,
            limit=settings.reindex_max_events_per_transaction,
        )
        records = [
            record
            for record in (
                embedding_record_from_event(
                    event,
                    tool_output_compress_threshold_tokens=settings.tool_output_compress_threshold_tokens,
                    tool_output_summary_tokens=settings.tool_output_summary_tokens,
                )
                for event in candidates
            )
            if record is not None
        ]
        if not records:
            job["status"] = "COMPLETED" if failed_count == 0 else "FAILED"
            job["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            store.update_reindex_job(job)
            return job

        if not reindex_provider_circuit_allows_call():
            job["status"] = "WAITING_FOR_PROVIDER"
            job["error"] = {"reason": "PROVIDER_CIRCUIT_OPEN"}
            store.update_reindex_job(job)
            return job

        stats = embedding_index.index_events(records)
        record_reindex_provider_outcome(stats.embedding_failures == 0)
        latest = store.get_reindex_job(job_id)
        if latest and latest.get("status") == "CANCELLED":
            return latest
        processed_count += int(stats.embedding_items)
        failed_count += max(int(stats.embedding_failures), len(records) - int(stats.embedding_items))
        if stats.embedding_failures and stats.embedding_items == 0:
            for record in records:
                store.update_event_embedding_status(
                    session_id=str(record["session_id"]),
                    event_id=str(record["event_id"]),
                    status="FAILED",
                    reason="PROVIDER_FAILURE",
                )
        job["progress"] = {
            "candidate_count": candidate_count,
            "processed_count": processed_count,
            "failed_count": failed_count,
        }
        if processed_count + failed_count >= candidate_count:
            job["status"] = "COMPLETED" if failed_count == 0 else "FAILED"
            job["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        else:
            job["status"] = "RUNNING"
        store.update_reindex_job(job)
        if job.get("session_id"):
            store.record_embedding_metrics(
                str(job["session_id"]),
                embedding_batches=stats.embedding_batches,
                embedding_items=stats.embedding_items,
                embedding_input_chars=stats.embedding_input_chars,
                embedding_failures=stats.embedding_failures,
            )
        if settings.reindex_yield_between_transactions_ms > 0:
            time.sleep(settings.reindex_yield_between_transactions_ms / 1000)
        return job

    app.state.run_reindex_job_once = run_reindex_job_once

    def redact_foreground(value: Any) -> Any:
        try:
            return redact(value, max_time_ms=settings.max_redaction_time_ms)
        except RedactionTimeoutError as exc:
            raise validation_error(
                "Redaction exceeded max_redaction_time_ms.",
                reason="REDACTION_TIMEOUT",
                max_redaction_time_ms=settings.max_redaction_time_ms,
            ) from exc

    def redact_event_foreground(value: dict[str, Any]) -> dict[str, Any]:
        try:
            redacted, redaction_metadata = redact_with_metadata(
                value,
                max_time_ms=settings.max_redaction_time_ms,
            )
        except RedactionTimeoutError as exc:
            raise validation_error(
                "Redaction exceeded max_redaction_time_ms.",
                reason="REDACTION_TIMEOUT",
                max_redaction_time_ms=settings.max_redaction_time_ms,
            ) from exc
        if isinstance(redacted, dict) and redaction_metadata:
            ingestion = redacted.get("ingestion") if isinstance(redacted.get("ingestion"), dict) else {}
            redacted["ingestion"] = {
                **ingestion,
                "redaction_metadata": redaction_metadata,
            }
        return redacted if isinstance(redacted, dict) else value

    def parse_blob_range(range_header: str | None, size_bytes: int) -> tuple[int, int] | None:
        if range_header is None:
            return None
        value = range_header.strip()
        if not value.startswith("bytes="):
            raise bad_request("Malformed Range header.", range=range_header)
        spec = value.removeprefix("bytes=")
        if "," in spec:
            raise range_not_satisfiable(
                "Multiple byte ranges are not supported.",
                range=range_header,
            )
        start_text, separator, end_text = spec.partition("-")
        if separator != "-" or not start_text.isdigit() or (end_text and not end_text.isdigit()):
            raise bad_request("Malformed Range header.", range=range_header)
        start = int(start_text)
        end = int(end_text) if end_text else size_bytes - 1
        if start >= size_bytes or end < start:
            raise range_not_satisfiable(
                "Blob byte range is unsatisfiable.",
                range=range_header,
                size_bytes=size_bytes,
            )
        return start, min(end, size_bytes - 1)

    def validate_bytes_ref_content(
        principal: Principal,
        *,
        session_id: str,
        content: dict[str, Any],
    ) -> str:
        if content.get("format") != "BYTES_REF":
            return ""
        uri = content.get("uri")
        if not isinstance(uri, str) or not uri.startswith("mneme-blob://"):
            raise validation_error(
                "BYTES_REF must use a server-owned mneme-blob URI.",
                field="content.uri",
            )
        if content.get("storage_owner") != "SERVER":
            raise validation_error(
                "BYTES_REF storage_owner must be SERVER.",
                field="content.storage_owner",
            )
        blob_id = uri.removeprefix("mneme-blob://")
        if not blob_id or "/" in blob_id:
            raise validation_error("BYTES_REF blob URI is invalid.", field="content.uri")
        blob = store.get_blob_metadata(blob_id)
        if blob is None:
            raise not_found("Blob not found.", blob_id=blob_id)
        require_project_access(
            principal,
            blob.get("project_isolation_key"),
            session_id=blob.get("session_id"),
        )
        if blob.get("session_id") != session_id:
            raise forbidden(
                "BYTES_REF blob is outside the target session scope.",
                blob_id=blob_id,
                session_id=session_id,
            )
        checks = {
            "hash": blob["hash"],
            "size_bytes": blob["size_bytes"],
            "media_type": blob["media_type"],
        }
        for field, expected in checks.items():
            if content.get(field) != expected:
                raise validation_error(
                    "BYTES_REF metadata does not match stored blob.",
                    field=f"content.{field}",
                    blob_id=blob_id,
                )
        return blob_id

    async def read_form_part_bytes(value: Any, *, part_name: str) -> tuple[bytes, str]:
        if isinstance(value, str):
            return value.encode("utf-8"), "text/plain"
        read = getattr(value, "read", None)
        if read is None:
            raise validation_error("Multipart form part is invalid.", part=part_name)
        content = await read()
        media_type = getattr(value, "content_type", None) or "application/octet-stream"
        return bytes(content), str(media_type)

    async def parse_multipart_event_request(request: Request, principal: Principal) -> tuple[dict[str, Any], str, dict[str, dict[str, Any]]]:
        try:
            form = await request.form()
        except Exception as exc:
            raise bad_request("Malformed multipart form-data.", reason=type(exc).__name__) from exc
        payload_part = form.get("payload")
        if payload_part is None:
            raise bad_request("Multipart event ingest requires payload part.", part="payload")
        payload_bytes, _ = await read_form_part_bytes(payload_part, part_name="payload")
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise bad_request("Multipart payload part must contain JSON.", part="payload") from exc
        if not isinstance(payload, dict):
            raise bad_request("Multipart payload part must contain an object.", part="payload")
        require_schema(payload, "event_batch")
        session_id = payload.get("session_id")
        if not isinstance(session_id, str):
            raise validation_error("Event batch requires session_id.")
        require_session_access(principal, session_id)

        blob_parts: dict[str, dict[str, Any]] = {}
        total_bytes = 0
        for name, value in form.multi_items():
            if not isinstance(name, str) or not name.startswith("blob."):
                continue
            client_part_id = name.removeprefix("blob.")
            if not client_part_id:
                raise validation_error("Multipart blob part id is empty.", part=name)
            content, media_type = await read_form_part_bytes(value, part_name=name)
            if len(content) > settings.max_blob_bytes:
                raise payload_too_large(
                    f"Multipart blob part exceeds max_blob_bytes={settings.max_blob_bytes}.",
                    max_blob_bytes=settings.max_blob_bytes,
                    actual_bytes=len(content),
                    part=name,
                )
            total_bytes += len(content)
            blob_parts[client_part_id] = {
                "content": content,
                "media_type": media_type,
                "hash": f"sha256:{hashlib.sha256(content).hexdigest()}",
                "size_bytes": len(content),
            }
        if len(blob_parts) > settings.max_batch_events:
            raise payload_too_large(
                "Multipart blob part count exceeds max_batch_events.",
                max_batch_events=settings.max_batch_events,
            )
        effective_max_bytes = min(
            settings.max_batch_total_blob_bytes,
            settings.max_multipart_transaction_bytes - settings.max_multipart_metadata_overhead_bytes,
        )
        if total_bytes > effective_max_bytes:
            raise payload_too_large(
                "Multipart blob bytes exceed request limit.",
                max_batch_total_blob_bytes=effective_max_bytes,
                actual_bytes=total_bytes,
            )
        used_parts: set[str] = set()
        events = payload.get("events")
        if not isinstance(events, list):
            raise validation_error("Event batch requires events list.")
        for raw_event in events:
            content = raw_event.get("content") if isinstance(raw_event, dict) else None
            if not isinstance(content, dict):
                continue
            uri = content.get("uri")
            if content.get("format") == "BYTES_REF" and isinstance(uri, str) and uri.startswith("multipart://"):
                client_part_id = uri.removeprefix("multipart://")
                if client_part_id not in blob_parts:
                    raise validation_error(
                        "Multipart BYTES_REF references a missing blob part.",
                        field="content.uri",
                        client_part_id=client_part_id,
                    )
                used_parts.add(client_part_id)
        unused_parts = sorted(set(blob_parts) - used_parts)
        if unused_parts:
            raise validation_error(
                "Multipart blob part is not referenced by payload.",
                parts=unused_parts,
            )
        request_hash = idempotency_request_hash(
            {
                "payload": payload,
                "blob_parts": {
                    part_id: {
                        "hash": part["hash"],
                        "size_bytes": part["size_bytes"],
                        "media_type": part["media_type"],
                    }
                    for part_id, part in sorted(blob_parts.items())
                },
            }
        )
        return payload, request_hash, blob_parts

    def persist_multipart_blob_parts(
        payload: dict[str, Any],
        blob_parts: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        session_id = str(payload["session_id"])
        project_key = store.session_project_key(session_id)
        if not project_key:
            raise validation_error("Session has no project isolation key.", session_id=session_id)
        stored_parts: dict[str, dict[str, Any]] = {}
        blob_refs: list[dict[str, Any]] = []
        blob_records: list[dict[str, Any]] = []
        for raw_event in payload.get("events", []):
            if not isinstance(raw_event, dict):
                continue
            content = raw_event.get("content")
            if not isinstance(content, dict):
                continue
            uri = content.get("uri")
            if content.get("format") != "BYTES_REF" or not isinstance(uri, str) or not uri.startswith("multipart://"):
                continue
            client_part_id = uri.removeprefix("multipart://")
            blob = stored_parts.get(client_part_id)
            part = blob_parts[client_part_id]
            if blob is None:
                blob_id = new_id("blob")
                created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                blob = {
                    "schema_version": "mneme.blob.v0",
                    "blob_id": blob_id,
                    "uri": f"mneme-blob://{blob_id}",
                    "owner": "SERVER",
                    "session_id": session_id,
                    "project_isolation_key": project_key,
                    "hash": part["hash"],
                    "size_bytes": part["size_bytes"],
                    "media_type": part["media_type"],
                    "created_at": created_at,
                    "ref_count": 0,
                    "retention": {"delete_with_session": True, "expires_at": None},
                    "metadata": {"multipart_part_id": client_part_id},
                }
                blob["bytes_ref"] = {
                    "format": "BYTES_REF",
                    "uri": blob["uri"],
                    "hash": blob["hash"],
                    "size_bytes": blob["size_bytes"],
                    "media_type": blob["media_type"],
                    "storage_owner": "SERVER",
                }
                blob_records.append(
                    {
                        **blob,
                        "delete_with_session": True,
                        "expires_at": None,
                        "content": part["content"],
                    }
                )
                stored_parts[client_part_id] = blob
            original_hash = "sha256:" + sha256_text(
                canonical_json(
                    {
                        "content": content,
                        "blob_part": {
                            "hash": part["hash"],
                            "size_bytes": part["size_bytes"],
                            "media_type": part["media_type"],
                        },
                    }
                )
            )
            normalized_hash = "sha256:" + sha256_text(canonical_json(blob["bytes_ref"]))
            raw_event["ingestion"] = {
                **raw_event.get("ingestion", {}),
                "original_content_hash": original_hash,
                "normalized_content_hash": normalized_hash,
            }
            raw_event["content"] = dict(blob["bytes_ref"])
            blob_refs.append(
                {
                    "client_part_id": client_part_id,
                    "event_id": raw_event.get("event_id"),
                    "bytes_ref": dict(blob["bytes_ref"]),
                }
            )
        return blob_refs, blob_records

    def preflight_multipart_event_identity(payload: dict[str, Any], blob_parts: dict[str, dict[str, Any]]) -> None:
        batch_hashes: dict[str, str] = {}
        for raw_event in payload.get("events", []):
            event_for_hash = dict(raw_event)
            content = event_for_hash.get("content")
            if isinstance(content, dict):
                uri = content.get("uri")
                if content.get("format") == "BYTES_REF" and isinstance(uri, str) and uri.startswith("multipart://"):
                    client_part_id = uri.removeprefix("multipart://")
                    part = blob_parts[client_part_id]
                    event_for_hash["content"] = {
                        "format": "BYTES_REF",
                        "uri": f"mneme-blob://pending-{client_part_id}",
                        "hash": part["hash"],
                        "size_bytes": part["size_bytes"],
                        "media_type": part["media_type"],
                        "storage_owner": "SERVER",
                    }
            clean = redact_event_foreground(normalize_event(event_for_hash))
            immutable_hash = event_immutable_hash(clean)
            event_id = clean["event_id"]
            batch_hash = batch_hashes.get(event_id)
            if batch_hash is not None:
                if batch_hash != immutable_hash:
                    raise conflict("Event id reused with incompatible immutable fields.", event_id=event_id)
                continue
            existing_hash = store.get_event_hash(event_id)
            if existing_hash is not None and existing_hash != immutable_hash:
                raise conflict("Event id reused with incompatible immutable fields.", event_id=event_id)
            batch_hashes[event_id] = immutable_hash

    def visible_session_ids(
        principal: Principal,
        requested_project_key: str | None = None,
    ) -> list[str] | None:
        project_keys = visible_project_keys(principal, requested_project_key)
        if project_keys is None:
            return None
        return store.session_ids_for_projects(project_keys)

    def project_session_ids_for_scope(principal: Principal, session_id: str) -> list[str]:
        project_key = store.session_project_key(session_id)
        require_project_access(principal, project_key, session_id=session_id)
        if project_key:
            return store.session_ids_for_project(project_key)
        return [session_id]

    tool_responses = {
        401: {"model": ErrorEnvelope},
        403: {"model": ErrorEnvelope},
        404: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
    }

    @app.get("/v1/health", response_model=HealthResponse)
    async def health() -> dict[str, Any]:
        return {
            "status": "OK",
            "service": "mneme-context-service",
            "api_version": "v1",
            "schema_versions": ["mneme.session.v0", "mneme.event.v0", "mneme.trace.v0"],
        }

    @app.get(
        "/v1/capabilities",
        response_model=CapabilitiesResponse,
        responses={401: {"model": ErrorEnvelope}},
    )
    async def capabilities(_principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        return {
            "api_version": "v1",
            "service_version": "0.1.0",
            "supported_cost_modes": ["MINIMAL", "STANDARD", "QUALITY"],
            "default_cost_mode": "STANDARD",
            "strict_cost_mode": settings.strict_cost_mode,
            "supports_embeddings": embeddings_available,
            "requires_embeddings": settings.require_embeddings,
            "supports_reranking": reranker_available,
            "supports_llm_enrichment": enrichment_available,
            "supports_context_prepare": True,
            "supports_mcp_tools": True,
            "supports_blob_store": True,
            "supports_blob_range_reads": True,
            "supports_export_bundle": True,
            "supported_export_formats": ["json", "tar_bundle"],
            "supports_project_isolation": True,
            "supports_session_readiness": True,
            "supports_retention_cleanup": True,
            "supports_reindex_jobs": True,
            "supports_reindex_job_polling": True,
            "supports_openapi": True,
            "supports_metrics": True,
            "metrics_format": settings.metrics_format,
            "delta_extraction": {
                "enabled": True,
                "schema_version": "mneme.entity_modifier.v0",
                "sources": ["DETERMINISTIC_PATTERN"],
                "automatic_update_scope": ["execution_state.active_entities"],
                "provider_guarded_enabled": False,
                "provider_guarded_policy": "UNSUPPORTED_IN_V0_DETERMINISTIC_FALLBACK_ACTIVE",
                "conflict_order": ["REPLACE", "REMOVE", "CONSTRAINT", "ADD"],
            },
            "binary_blob_extractor_policy": settings.binary_blob_extractor_policy,
            "integration_depth": {
                "max_supported": "EVENT_INGEST",
                "supported_levels": ["TOOLS_ONLY", "EVENT_INGEST"],
                "unsupported_or_future": [
                    "PREPARE_INPUT",
                    "CONTEXT_ENGINE",
                    "COMPACTION_OWNER",
                    "FULL_RUNTIME",
                ],
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
            },
            "mcp_tools": list(TOOL_NAMES),
            "mcp_tool_versions": {name: "v0" for name in TOOL_NAMES},
            "providers": {
                "embeddings": settings.embeddings.summary(
                    available=embeddings_available,
                    health=provider_health["embeddings"].snapshot(),
                ),
                "reranker": settings.reranker.summary(
                    available=reranker_available,
                    health=provider_health["reranker"].snapshot(),
                ),
                "llm_enrichment": settings.llm_enrichment.summary(
                    available=enrichment_available,
                    health=provider_health["llm_enrichment"].snapshot(),
                ),
            },
            "auth_schemes": ["INSECURE_DEV"] if settings.insecure_dev else ["BEARER_TOKEN"],
            "max_batch_events": settings.max_batch_events,
            "max_event_content_bytes": settings.max_event_content_bytes,
            "max_tool_result_events": settings.max_tool_result_events,
            "supported_schema_versions": SUPPORTED_SCHEMAS,
            "limits": {
                "max_batch_events": settings.max_batch_events,
                "max_event_content_bytes": settings.max_event_content_bytes,
                "max_blob_bytes": settings.max_blob_bytes,
                "max_session_id_length": settings.max_session_id_length,
                "max_batch_total_blob_bytes": settings.max_batch_total_blob_bytes,
                "max_multipart_metadata_overhead_bytes": settings.max_multipart_metadata_overhead_bytes,
                "max_multipart_transaction_bytes": settings.max_multipart_transaction_bytes,
                "max_export_blob_inline_bytes": settings.max_export_blob_inline_bytes,
                "max_export_session_memory_bytes": settings.max_export_session_memory_bytes,
                "top_k": 10,
                "top_k_max": 100,
                "page_size_default": 20,
                "page_size_max": 1000,
                "expand_context_depth_default": 2,
                "expand_context_depth_max": 5,
                "expand_context_max_events_default": 12,
                "expand_context_max_events_max": 200,
                "max_latency_ms_default": 250,
                "max_parent_event_ids": 64,
                "idempotency_key_min_retention_seconds": settings.idempotency_key_min_retention_seconds,
                "graph_importance_depth_decay": settings.graph_importance_depth_decay,
            },
            "tokenizer": {
                "tokenizer_id": "char_4_fallback",
                "token_estimate_quality": "CHAR_APPROXIMATE",
            },
            "storage": {
                "sqlite_wal": True,
                "blob_driver": "sqlite",
                "schema_version": CURRENT_SCHEMA_VERSION,
                "migration_status": "CURRENT",
                "vector_acceleration": "PYTHON_FALLBACK",
            },
        }

    @app.get(
        "/v1/metrics",
        response_class=Response,
        responses={
            200: {
                "content": {
                    "text/plain": {
                        "schema": {"$ref": "#/components/schemas/MetricsResponse"}
                    }
                }
            },
            401: {"model": ErrorEnvelope},
        },
    )
    async def metrics(_principal: Principal = Depends(require_auth)) -> Response:
        content = prometheus_metrics_text(include_current_metrics_request=True)
        return Response(content=content, media_type="text/plain")

    @app.post(
        "/v1/blobs",
        response_model=BlobRecordResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            413: {"model": ErrorEnvelope},
            415: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def upload_blob(
        body: Annotated[bytes, Body(media_type="application/octet-stream")],
        principal: Principal = Depends(require_auth),
        content_type: Annotated[str | None, Header(alias="Content-Type")] = None,
        session_id: Annotated[str | None, Header(alias="X-Mneme-Session-Id")] = None,
        project_isolation_key: Annotated[str | None, Header(alias="X-Mneme-Project-Isolation-Key")] = None,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized_content_type != "application/octet-stream":
            raise unsupported_media_type(
                "Blob upload requires application/octet-stream.",
                content_type=content_type,
            )
        if not session_id:
            raise validation_error(
                "Blob upload requires X-Mneme-Session-Id.",
                header="X-Mneme-Session-Id",
            )
        if not project_isolation_key:
            raise validation_error(
                "Blob upload requires X-Mneme-Project-Isolation-Key.",
                header="X-Mneme-Project-Isolation-Key",
            )
        if len(body) > settings.max_blob_bytes:
            raise payload_too_large(
                f"Blob upload exceeds max_blob_bytes={settings.max_blob_bytes}.",
                max_blob_bytes=settings.max_blob_bytes,
                actual_bytes=len(body),
            )
        require_session_access(
            principal,
            session_id,
            requested_project_key=project_isolation_key,
        )
        content_hash = f"sha256:{hashlib.sha256(body).hexdigest()}"
        request_hash = idempotency_request_hash(
            {
                "session_id": session_id,
                "project_isolation_key": project_isolation_key,
                "hash": content_hash,
                "size_bytes": len(body),
                "media_type": normalized_content_type,
            }
        )
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/blobs",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        response = store.put_blob(
            session_id=session_id,
            project_isolation_key=project_isolation_key,
            content=body,
            media_type=normalized_content_type,
        )
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/blobs",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.get(
        "/v1/blobs/{blob_id}",
        response_model=BlobRecordResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
        },
    )
    async def get_blob_metadata(
        blob_id: str,
        principal: Principal = Depends(require_auth),
    ) -> dict[str, Any]:
        return require_blob_access(principal, blob_id)

    @app.get(
        "/v1/blobs/{blob_id}/content",
        responses={
            400: {"model": ErrorEnvelope},
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            416: {"model": ErrorEnvelope},
        },
    )
    async def get_blob_content(
        blob_id: str,
        principal: Principal = Depends(require_auth),
        range_header: Annotated[str | None, Header(alias="Range")] = None,
    ) -> Response:
        blob = require_blob_access(principal, blob_id)
        content = store.get_blob_content(blob_id)
        if content is None:
            raise not_found("Blob not found.", blob_id=blob_id)
        byte_range = parse_blob_range(range_header, int(blob["size_bytes"]))
        if byte_range is None:
            return Response(content=content, media_type=blob["media_type"])
        start, end = byte_range
        return Response(
            content=content[start : end + 1],
            media_type=blob["media_type"],
            status_code=206,
            headers={"Content-Range": f"bytes {start}-{end}/{blob['size_bytes']}"},
        )

    @app.delete(
        "/v1/blobs/{blob_id}",
        response_model=BlobDeleteResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
        },
    )
    async def delete_blob(
        blob_id: str,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        request_hash = idempotency_request_hash({"blob_id": blob_id})
        replay = replay_idempotent_response(
            principal=principal,
            method="DELETE",
            path="/v1/blobs/{blob_id}",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_blob_access(principal, blob_id)
        response = {"blob_id": blob_id, "deleted": store.delete_blob(blob_id)}
        record_idempotent_response(
            principal=principal,
            method="DELETE",
            path="/v1/blobs/{blob_id}",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post(
        "/v1/maintenance/blob-gc",
        response_model=BlobGcResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def blob_gc(
        payload: BlobGcRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        payload = model_payload(payload)
        scope = str(payload.get("scope") or "PROJECT").strip().upper()
        if scope not in {"ALL", "PROJECT", "SESSION"}:
            raise validation_error("scope must be ALL, PROJECT, or SESSION.", field="scope")
        project_key = payload.get("project_isolation_key")
        session_id = payload.get("session_id")
        dry_run = bool(payload.get("dry_run", True))
        if project_key is not None and not isinstance(project_key, str):
            raise validation_error("project_isolation_key must be a string or null.", field="project_isolation_key")
        if session_id is not None and not isinstance(session_id, str):
            raise validation_error("session_id must be a string or null.", field="session_id")
        if scope == "ALL":
            if not principal.all_projects:
                raise forbidden("Unscoped blob GC requires owner all-projects scope.", scope=scope)
            project_key = None
            session_id = None
        elif scope == "PROJECT":
            if not project_key:
                raise validation_error("PROJECT blob GC requires project_isolation_key.", field="project_isolation_key")
            visible_project_keys(principal, project_key)
            session_id = None
        else:
            if not session_id:
                raise validation_error("SESSION blob GC requires session_id.", field="session_id")
            require_session_access(principal, session_id, requested_project_key=project_key)
            project_key = store.session_project_key(session_id)
        request_hash = idempotency_request_hash(
            {
                "scope": scope,
                "project_isolation_key": project_key,
                "session_id": session_id,
                "dry_run": dry_run,
            }
        )
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/maintenance/blob-gc",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        response = store.garbage_collect_blobs(
            project_isolation_key=project_key,
            session_id=session_id,
            dry_run=dry_run,
        )
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/maintenance/blob-gc",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post(
        "/v1/maintenance/reindex",
        response_model=ReindexJobResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
        },
    )
    async def create_reindex_job(
        payload: ReindexRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        scope, project_key, session_id = normalize_reindex_scope(body, principal)
        statuses = normalize_reindex_statuses(body)
        max_job_events = normalize_reindex_max_job_events(body)
        force = bool(body.get("force", False))
        request_hash = idempotency_request_hash(
            {
                "scope": scope,
                "project_isolation_key": project_key,
                "session_id": session_id,
                "statuses": statuses,
                "force": force,
                "max_job_events": max_job_events,
            }
        )
        key = normalized_idempotency_key(idempotency_key)
        if key is not None:
            record = store.get_idempotency_record(
                principal_name=principal.name,
                method="POST",
                path="/v1/maintenance/reindex",
                idempotency_key=key,
            )
            if record is not None:
                if record["request_hash"] != request_hash:
                    raise conflict(
                        "Idempotency-Key reused with a different request.",
                        method="POST",
                        path="/v1/maintenance/reindex",
                    )
                replay_job_id = record["response"].get("job_id")
                if isinstance(replay_job_id, str):
                    replay_job = store.get_reindex_job(replay_job_id)
                    if replay_job is not None:
                        return replay_job
                return record["response"]
        if embedding_index is None and not settings.reindex_enqueue_when_provider_unavailable:
            raise provider_unavailable(
                "Embedding provider is unavailable for reindex.",
                reason="EMBEDDINGS_PROVIDER_UNAVAILABLE",
            )
        status = "QUEUED" if embedding_index is not None else "WAITING_FOR_PROVIDER"
        candidate_count = store.count_reindex_candidates(
            scope=scope,
            project_isolation_key=project_key,
            session_id=session_id,
            statuses=statuses,
            force=force,
            max_job_events=max_job_events,
            embedding_model_id=embedding_index.model_id if embedding_index else None,
        )
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        job = {
            "schema_version": "mneme.reindex_job.v0",
            "job_id": new_id("reindex"),
            "scope": scope,
            "project_isolation_key": project_key,
            "session_id": session_id,
            "statuses": statuses,
            "status": status,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "progress": {
                "candidate_count": candidate_count,
                "processed_count": 0,
                "failed_count": 0,
            },
            "error": None,
        }
        store.put_reindex_job(job)
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/maintenance/reindex",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=job,
        )
        return job

    @app.get(
        "/v1/maintenance/reindex/{job_id}",
        response_model=ReindexJobResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
        },
    )
    async def get_reindex_job(
        job_id: str,
        principal: Principal = Depends(require_auth),
    ) -> dict[str, Any]:
        return require_reindex_job_access(principal, job_id)

    @app.post(
        "/v1/maintenance/reindex/{job_id}/cancel",
        response_model=ReindexJobResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def cancel_reindex_job(
        job_id: str,
        payload: ReindexCancelRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        request_hash = idempotency_request_hash({"job_id": job_id, "body": body})
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/maintenance/reindex/{job_id}/cancel",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        job = require_reindex_job_access(principal, job_id)
        if job["status"] not in {"COMPLETED", "FAILED", "CANCELLED"}:
            job["status"] = "CANCELLED"
            job["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            store.update_reindex_job(job)
            if job.get("session_id"):
                store.add_audit(
                    str(job["session_id"]),
                    "REINDEX_CANCEL",
                    "maintenance.reindex.cancel",
                    [],
                    project_isolation_key=job.get("project_isolation_key"),
                    principal=principal.as_audit_principal(),
                    request={"job_id": job_id},
                    result={
                        "job_id": job["job_id"],
                        "status": job["status"],
                        "completed_at": job["completed_at"],
                    },
                )
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/maintenance/reindex/{job_id}/cancel",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=job,
        )
        return job

    @app.post(
        "/v1/readiness/session",
        response_model=ToolResponseEnvelope,
        responses={
            401: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            412: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def session_readiness(
        payload: SessionReadinessRequest,
        principal: Principal = Depends(require_auth),
    ) -> dict[str, Any]:
        payload = model_payload(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        require_evidence = bool(payload.get("require_evidence", True))
        allow_provider_calls = bool(payload.get("allow_provider_calls", False))
        top_k = parse_int(payload, "top_k", default=1, minimum=1, maximum=10)
        query = optional_payload_str(payload, "query") or ""
        safe_query = redact(query)
        filters = search_filters(payload)
        scope_payload = dict(payload)
        scope_payload["scope"] = payload.get("scope") or "SESSION"
        scope = parse_search_scope(scope_payload)
        provider_calls_used = False

        if not require_evidence:
            results = []
            retrieval = {
                "candidate_count": 0,
                "selected_count": 0,
                "strategies": ["SESSION_EXISTS"],
                "degraded": False,
                "fallbacks": [],
            }
            warnings = []
            evidence_ids = []
            check = "session_exists"
        elif query:
            readiness_embedding_index = embedding_index if allow_provider_calls else None
            readiness_reranker = reranker if allow_provider_calls else None
            provider_calls_used = bool(readiness_embedding_index or readiness_reranker)
            results, retrieval, warnings = hybrid_context_search(
                store,
                readiness_embedding_index,
                session_id=session_id,
                query=safe_query,
                top_k=top_k,
                filters=filters,
                scope=scope,
                mode=search_mode(payload, settings=settings),
                routing_mode_weights=settings.routing_mode_weights,
                project_session_ids=project_session_ids_for_scope(principal, session_id),
                reranker=readiness_reranker,
                reranker_top_k=settings.reranker_top_k,
                allow_recency_refill=False,
            )
            evidence_ids = [item["event_id"] for item in results]
            check = "context_search"
        else:
            events = store.recent_events(session_id, top_k)
            results = summarize_events(events)
            retrieval = {
                "candidate_count": len(results),
                "selected_count": len(results),
                "strategies": ["RECENT"],
                "degraded": False,
                "fallbacks": [],
            }
            warnings = []
            evidence_ids = [item["event_id"] for item in results]
            check = "recall_recent"

        if require_evidence and not evidence_ids:
            raise failed_precondition(
                "Session readiness check found no evidence.",
                session_id=session_id,
                reason="NO_EVIDENCE",
                query=safe_query,
                required_check=check,
                evidence_count=0,
            )

        trace_id = audit_memory_tool(
            store,
            session_id,
            "session_readiness",
            evidence_ids,
            retrieval=retrieval,
            warnings=warnings,
            audit_mode=settings.audit_mode,
        )
        return tool_response(
            {
                "ready": True,
                "session_id": session_id,
                "required_check": check,
                "evidence_count": len(evidence_ids),
                "evidence_event_ids": evidence_ids,
                "checks": {
                    "authenticated": True,
                    "session_found": True,
                    "evidence_found": bool(evidence_ids),
                    "provider_calls_allowed": allow_provider_calls,
                    "provider_calls_used": provider_calls_used,
                },
            },
            trace_id=trace_id,
            warnings=warnings,
        )

    @app.post(
        "/v1/sessions/start",
        response_model=SessionStartResponse,
        responses={
            401: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def start_session(
        payload: SessionStartRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        payload = model_payload(payload)
        request_hash = idempotency_request_hash(payload)
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/start",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_schema(payload, "session", "session_start")
        if "agent_id" not in payload or "runtime" not in payload:
            raise validation_error("Session requires agent_id and runtime.")
        if "session_id" not in payload or not payload.get("session_id"):
            if normalized_idempotency_key(idempotency_key) is None:
                raise validation_error("Session requires session_id unless Idempotency-Key is supplied.")
            payload["session_id"] = new_id("session")
        validate_session_id(str(payload["session_id"]))
        clean = redact(payload)
        require_project_access(
            principal,
            session_payload_project_key(clean),
            session_id=str(clean.get("session_id") or ""),
        )
        warnings = cost_mode_warnings_or_error(
            clean,
            settings,
            embeddings_available=embeddings_available,
            reranker_available=reranker_available,
            enrichment_available=enrichment_available,
        )
        created = store.put_session(clean)
        metadata = clean.get("metadata") if isinstance(clean.get("metadata"), dict) else {}
        lineage_session_id = first_metadata_string(metadata, LINEAGE_KEYS)
        if lineage_session_id:
            store.put_session_lineage(lineage_session_id, clean["session_id"])
        counts = store.session_counts(clean["session_id"])
        lineage_counts = store.lineage_counts(clean["session_id"])
        session_state = classify_session_start(
            clean,
            created=created,
            prior_event_count=counts["event_count"],
            prior_turn_count=counts["turn_count"],
            lineage_event_count=lineage_counts["event_count"],
            lineage_turn_count=lineage_counts["turn_count"],
        )
        store.set_context_fill_required(clean["session_id"], bool(session_state["requires_context_fill"]))
        response = {
            "session_id": clean["session_id"],
            "created": created,
            "status": "ACTIVE",
            "accepted_schema_version": clean["schema_version"],
            "session_state": session_state,
            "warnings": warnings,
        }
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/start",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post(
        "/v1/events",
        response_model=EventBatchResponse,
        responses={
            400: {"model": ErrorEnvelope},
            401: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            413: {"model": ErrorEnvelope},
            415: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def ingest_events(
        request: Request,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
        multipart_blob_parts: dict[str, dict[str, Any]] | None = None
        multipart_blob_refs: list[dict[str, Any]] = []
        multipart_blob_records: list[dict[str, Any]] | None = None
        planned_multipart_blob_ids: set[str] = set()
        if content_type == "multipart/form-data":
            payload, request_hash, multipart_blob_parts = await parse_multipart_event_request(
                request,
                principal,
            )
        elif content_type in {"application/json", ""}:
            try:
                payload = await request.json()
            except json.JSONDecodeError as exc:
                raise bad_request("Malformed JSON request body.") from exc
            if not isinstance(payload, dict):
                raise bad_request("Event batch request body must be an object.")
            request_hash = idempotency_request_hash(payload)
        else:
            raise unsupported_media_type(
                "Event ingest requires application/json or multipart/form-data.",
                content_type=content_type,
            )
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/events",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        if multipart_blob_parts is not None:
            multipart_session_id = payload.get("session_id")
            multipart_events = payload.get("events")
            if not isinstance(multipart_session_id, str):
                raise validation_error("Event batch requires session_id.")
            if not isinstance(multipart_events, list):
                raise validation_error("Event batch requires events list.")
            for raw_event in multipart_events:
                require_schema(raw_event, "event")
                if raw_event.get("session_id") != multipart_session_id:
                    raise validation_error("Event session_id does not match batch.")
            preflight_multipart_event_identity(payload, multipart_blob_parts)
            multipart_blob_refs, multipart_blob_records = persist_multipart_blob_parts(payload, multipart_blob_parts)
            planned_multipart_blob_ids = {str(blob["blob_id"]) for blob in multipart_blob_records}
        require_schema(payload, "event_batch")
        session_id = payload.get("session_id")
        if not isinstance(session_id, str):
            raise validation_error("Event batch requires session_id.")
        require_session_access(principal, session_id)
        events = payload.get("events")
        if not isinstance(events, list):
            raise validation_error("Event batch requires events list.")
        if len(events) > settings.max_batch_events:
            raise payload_too_large("Event batch exceeds max_batch_events.", max_batch_events=settings.max_batch_events)

        accepted = 0
        duplicates = 0
        rejected: list[dict[str, Any]] = []
        stored_ids: list[str] = []
        embedding_events: list[dict[str, Any]] = []
        prepared_events: list[dict[str, Any]] = []
        batch_hashes: dict[str, str] = {}
        for raw_event in events:
            require_schema(raw_event, "event")
            if raw_event.get("session_id") != session_id:
                rejected.append({"event_id": raw_event.get("event_id"), "code": "VALIDATION_ERROR", "message": "Event session_id does not match batch."})
                continue
            normalized = normalize_event(raw_event)
            content = normalized.get("content", {})
            blob_ref_ids: list[str] = []
            if content.get("format") != "BYTES_REF":
                size = len(text_from_content(content).encode("utf-8"))
                if size > settings.max_event_content_bytes:
                    raise payload_too_large("Inline event content exceeds max_event_content_bytes.", max_event_content_bytes=settings.max_event_content_bytes)
            else:
                uri = content.get("uri")
                if (
                    multipart_blob_records is not None
                    and isinstance(uri, str)
                    and uri.startswith("mneme-blob://")
                    and uri.removeprefix("mneme-blob://") in planned_multipart_blob_ids
                ):
                    blob_ref_id = uri.removeprefix("mneme-blob://")
                else:
                    blob_ref_id = validate_bytes_ref_content(
                        principal,
                        session_id=session_id,
                        content=content,
                    )
                if blob_ref_id:
                    blob_ref_ids.append(blob_ref_id)
            clean = redact_event_foreground(normalized)
            clean["ingestion"] = {
                **clean.get("ingestion", {}),
                "status": "STORED",
                "embedding_status": "PENDING" if embedding_index else "NOT_CONFIGURED",
            }
            if is_binary_metadata_only_content(content):
                clean["ingestion"]["redaction_scope"] = "BINARY_METADATA_ONLY"
                clean["ingestion"]["extractor_policy"] = settings.binary_blob_extractor_policy
            text = text_from_content(clean.get("content", {}))
            immutable_hash = event_immutable_hash(clean)
            batch_hash = batch_hashes.get(clean["event_id"])
            if batch_hash is not None:
                if batch_hash != immutable_hash:
                    raise conflict("Event id reused with incompatible immutable fields.", event_id=clean["event_id"])
                duplicates += 1
                continue
            existing_hash = store.get_event_hash(clean["event_id"])
            if existing_hash is not None:
                if existing_hash != immutable_hash:
                    raise conflict("Event id reused with incompatible immutable fields.", event_id=clean["event_id"])
                duplicates += 1
                continue
            batch_hashes[clean["event_id"]] = immutable_hash
            prepared_events.append({"event": clean, "immutable_hash": immutable_hash, "text": text, "blob_ref_ids": blob_ref_ids})

        if multipart_blob_records is not None:
            store.put_blob_records_and_events(
                blob_records=multipart_blob_records,
                event_records=[
                    {
                        "event": prepared["event"],
                        "immutable_hash": str(prepared["immutable_hash"]),
                        "content_text": str(prepared["text"]),
                        "is_memory_read": prepared["event"]["type"] == "MEMORY_READ",
                        "blob_ref_ids": list(prepared.get("blob_ref_ids", [])),
                    }
                    for prepared in prepared_events
                ],
            )

        for prepared in prepared_events:
            clean = prepared["event"]
            immutable_hash = str(prepared["immutable_hash"])
            text = str(prepared["text"])
            previous_state = store.execution_state_or_default(session_id)
            if multipart_blob_records is None:
                store.put_event(clean, immutable_hash, text, is_memory_read=clean["type"] == "MEMORY_READ")
                for blob_ref_id in prepared.get("blob_ref_ids", []):
                    store.attach_blob_reference(
                        blob_id=str(blob_ref_id),
                        session_id=session_id,
                        event_id=clean["event_id"],
                    )
            store.put_event_graph_edges(clean)
            state = apply_event_to_state(previous_state, clean)
            previous_segment = store.latest_active_segment(session_id) if clean["type"] == "USER_MESSAGE" else None
            embedding_drift = 0.0
            if embedding_index and previous_segment:
                embedding_drift = embedding_index.embedding_drift_against_segment(
                    text,
                    session_id=session_id,
                    segment_id=previous_segment["segment_id"],
                )
            metadata = clean.get("metadata") if isinstance(clean.get("metadata"), dict) else {}
            tool_domain_shift_trusted = (
                principal.role == "ADAPTER"
                and metadata.get("tool_domain_shift") is True
                and isinstance(metadata.get("tool_domain"), str)
            )
            drift_weights = tuple(float(item) for item in settings.drift_weights)
            topic_entropy = topic_entropy_from_text(text)
            drift_components = {
                "embedding_distance": max(0.0, min(1.0, float(embedding_drift))),
                "topic_entropy": topic_entropy,
                "tool_domain_shift_score": 1.0 if tool_domain_shift_trusted else 0.0,
            }
            drift_score = round(
                drift_weights[0] * drift_components["embedding_distance"]
                + drift_weights[1] * drift_components["topic_entropy"]
                + drift_weights[2] * drift_components["tool_domain_shift_score"],
                6,
            )
            classification = classify_intent(
                text,
                embedding_drift=embedding_drift,
                drift_score=drift_score,
                drift_threshold=settings.drift_threshold,
                active_entities=previous_state.get("active_entities") or [],
                last_assistant_entities=last_assistant_entities(store, session_id),
            )
            classification["signals"]["drift_components"] = drift_components
            classification["signals"]["drift_weights"] = {
                "embedding": drift_weights[0],
                "topic_entropy": drift_weights[1],
                "tool_domain": drift_weights[2],
            }
            classification["signals"]["tool_domain_shift"] = metadata.get("tool_domain_shift") is True
            classification["signals"]["tool_domain_shift_trusted"] = tool_domain_shift_trusted
            if isinstance(metadata.get("tool_domain"), str):
                classification["signals"]["tool_domain"] = str(metadata["tool_domain"])
            segment = update_segment_for_event(store, clean, classification)
            if segment:
                store.put_segment_member_edge(session_id, segment, clean["event_id"])
            if segment:
                state["segment_id"] = segment["segment_id"]
            if should_run_enrichment(settings, clean, state, previous_segment, segment):
                state = apply_optional_enrichment(store, enricher, clean, state)
            store.commit_execution_state(session_id, state)
            maybe_trace_segment_drift(store, clean, classification, previous_segment, segment)
            accepted += 1
            stored_ids.append(clean["event_id"])
            if embedding_index:
                event_for_embedding = dict(clean)
                if segment:
                    metadata = dict(event_for_embedding.get("metadata", {}))
                    metadata["mneme_segment_id"] = segment["segment_id"]
                    event_for_embedding["metadata"] = metadata
                embedding_events.append(event_for_embedding)

        if embedding_index and embedding_events:
            records = [
                record
                for record in (
                    embedding_record_from_event(
                        event,
                        tool_output_compress_threshold_tokens=settings.tool_output_compress_threshold_tokens,
                        tool_output_summary_tokens=settings.tool_output_summary_tokens,
                    )
                    for event in embedding_events
                )
                if record is not None
            ]
            if records:
                stats = embedding_index.index_events(records)
                store.record_embedding_metrics(
                    session_id,
                    embedding_batches=stats.embedding_batches,
                    embedding_items=stats.embedding_items,
                    embedding_input_chars=stats.embedding_input_chars,
                    embedding_failures=stats.embedding_failures,
                )

        response = {"session_id": session_id, "accepted": accepted, "duplicates": duplicates, "rejected": rejected, "stored_event_ids": stored_ids, "blob_refs": multipart_blob_refs}
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/events",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post("/v1/turns/complete")
    async def complete_turn(
        payload: dict[str, Any],
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        request_hash = idempotency_request_hash(payload)
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/turns/complete",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_schema(payload, "turn")
        session_id = require_payload_str(payload, "session_id")
        turn_id = require_payload_str(payload, "turn_id")
        require_session_access(principal, session_id)
        status = str(payload.get("status") or "COMPLETED").upper()
        if status not in TURN_COMPLETE_STATUSES:
            raise validation_error("Unknown turn completion status.", field="status")
        turn = redact({**payload, "status": status})
        existing = store.get_turn(session_id, turn_id)
        if existing is not None:
            if canonical_json(existing) != canonical_json(turn):
                raise conflict("Turn id reused with incompatible completion fields.", turn_id=turn_id)
            response = turn_complete_response(
                existing,
                session_id=session_id,
                turn_id=turn_id,
                segment_ids=turn_segment_ids(session_id, existing),
            )
            record_idempotent_response(
                principal=principal,
                method="POST",
                path="/v1/turns/complete",
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response=response,
            )
            return response
        segment_ids = turn_segment_ids(session_id, turn)
        store.put_turn(session_id, turn_id, turn, segment_ids=segment_ids)
        state_patch = {
            "current_step": f"Turn {turn_id} {status}",
            "enrichment": {
                "intent_label": f"TURN_{status}",
                "topic_tags": [],
            },
        }
        store.update_execution_state(
            session_id,
            mode="PATCH",
            state_patch=state_patch,
            provenance={"turn_id": turn_id, "source": "turn_complete"},
        )
        store_turn_complete_event(session_id, turn_id, turn)
        response = turn_complete_response(turn, session_id=session_id, turn_id=turn_id, segment_ids=segment_ids)
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/turns/complete",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    def turn_segment_ids(session_id: str, turn: dict[str, Any]) -> list[str]:
        segment_ids = []
        for event_id in turn.get("event_ids") or []:
            if isinstance(event_id, str):
                segment_id = store.segment_id_for_event(session_id, event_id)
                if segment_id:
                    segment_ids.append(segment_id)
        if not segment_ids:
            active_segment = store.latest_active_segment(session_id)
            if active_segment and active_segment.get("segment_id"):
                segment_ids.append(str(active_segment["segment_id"]))
        if not segment_ids:
            segment_ids.append(f"segment-{session_id}")
        return list(dict.fromkeys(segment_ids))

    def store_turn_complete_event(session_id: str, turn_id: str, turn: dict[str, Any]) -> None:
        event_ids = [item for item in turn.get("event_ids") or [] if isinstance(item, str) and item]
        status_value = str(turn.get("status") or "COMPLETED").upper()
        event_id = f"turn-complete-{turn_id}"
        summary = ""
        outcome = turn.get("outcome") if isinstance(turn.get("outcome"), dict) else {}
        if outcome.get("summary"):
            summary = str(outcome["summary"])
        elif turn.get("error"):
            error = turn.get("error") if isinstance(turn.get("error"), dict) else {}
            summary = str(error.get("message") or error.get("code") or status_value)
        else:
            summary = f"Turn {turn_id} {status_value}"
        raw_event = {
            "schema_version": "mneme.event.v0",
            "event_id": event_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "agent_id": str(turn.get("agent_id") or "mneme"),
            "runtime": str(turn.get("runtime") or "MNEME"),
            "role": "RUNTIME",
            "type": "TURN_COMPLETE",
            "timestamp": str(turn.get("completed_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            "content": {"format": "TEXT", "text": summary},
            "parent_event_ids": event_ids,
            "importance": "HIGH",
            "metadata": {
                "turn_status": status_value,
                "usage": turn.get("usage") if isinstance(turn.get("usage"), dict) else {},
            },
        }
        clean = redact_event_foreground(normalize_event(raw_event))
        immutable_hash = event_immutable_hash(clean)
        existing_hash = store.get_event_hash(clean["event_id"])
        if existing_hash is not None:
            if existing_hash != immutable_hash:
                raise conflict("TURN_COMPLETE event id reused with incompatible immutable fields.", event_id=clean["event_id"])
            return
        store.put_event(clean, immutable_hash, text_from_content(clean["content"]), is_memory_read=False)
        store.put_event_graph_edges(clean)

    def turn_complete_response(
        turn: dict[str, Any],
        *,
        session_id: str,
        turn_id: str,
        segment_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "schema_version": "mneme.turn_complete_result.v0",
            "session_id": session_id,
            "turn_id": turn_id,
            "status": str(turn.get("status") or "COMPLETED").upper(),
            "recorded": True,
            "segment_ids": segment_ids,
        }

    def rest_segment(segment: dict[str, Any]) -> dict[str, Any]:
        session_id = str(segment.get("session_id") or "")
        status = str(segment.get("status") or "ACTIVE")
        public_status = "OPEN" if status == "ACTIVE" else status
        return {
            "schema_version": "mneme.segment.v0",
            "segment_id": segment.get("segment_id"),
            "session_id": session_id,
            "project_isolation_key": store.session_project_key(session_id),
            "title": segment.get("title"),
            "summary": segment.get("summary"),
            "status": public_status,
            "outcome": segment.get("outcome"),
            "started_at": segment.get("started_at") or segment.get("created_at") or segment.get("first_ts"),
            "closed_at": segment.get("closed_at") if public_status != "OPEN" else None,
            "anchor_event_ids": list(segment.get("anchor_event_ids") or []),
            "event_count": int(segment.get("event_count") or 0),
            "last_event_id": segment.get("last_event_id"),
            "created_by": segment.get("created_by") or "AUTOMATIC",
            "metadata": segment.get("metadata") if isinstance(segment.get("metadata"), dict) else {},
        }

    def event_summary(event: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "mneme.event_summary.v0",
            "event_id": event.get("event_id"),
            "session_id": event.get("session_id"),
            "turn_id": event.get("turn_id"),
            "type": event.get("type"),
            "role": event.get("role"),
            "timestamp": event.get("timestamp"),
            "importance": event.get("importance") or "NORMAL",
            "freshness": event_freshness(event),
            "snippet": text_from_content(event.get("content", {}))[:200],
            "redaction_applied": True,
        }

    def require_segment_anchor_events(session_id: str, anchor_event_ids: list[str]) -> None:
        for event_id in anchor_event_ids:
            if not store.get_event(session_id, event_id):
                raise validation_error(
                    "Segment anchor_event_ids must reference events in the same session.",
                    field="anchor_event_ids",
                    event_id=event_id,
                )

    @app.post(
        "/v1/segments/start",
        response_model=SegmentResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def start_segment(
        payload: SegmentStartRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        request_hash = idempotency_request_hash(body)
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/segments/start",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_schema(body, "segment_start")
        session_id = require_payload_str(body, "session_id")
        require_session_access(principal, session_id)
        segment_id = body.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id:
            if normalized_idempotency_key(idempotency_key) is None:
                raise validation_error("segment_id is required unless Idempotency-Key is supplied.", field="segment_id")
            segment_id = new_id("segment")
        anchor_event_ids = body.get("anchor_event_ids") if isinstance(body.get("anchor_event_ids"), list) else []
        anchor_event_ids = [str(item) for item in anchor_event_ids if isinstance(item, str) and item]
        require_segment_anchor_events(session_id, anchor_event_ids)
        created_by = str(body.get("created_by") or "ADAPTER").upper()
        if created_by not in SEGMENT_CREATED_BY_VALUES:
            raise validation_error("Unknown segment created_by.", field="created_by")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        segment = {
            "schema_version": "mneme.segment.v0",
            "segment_id": segment_id,
            "session_id": session_id,
            "title": str(body.get("title") or f"Segment {segment_id}")[:160],
            "summary": str(body.get("summary") or ""),
            "status": "ACTIVE",
            "outcome": None,
            "created_at": now,
            "updated_at": now,
            "anchor_event_ids": anchor_event_ids,
            "event_count": 0,
            "token_estimate": 0,
            "created_by": created_by,
            "metadata": {"provenance": redact(body.get("provenance") or {})},
        }
        store.put_segment(segment)
        response = {"segment": rest_segment(segment)}
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/segments/start",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.get("/v1/segments", response_model=SegmentListResponse, responses={401: {"model": ErrorEnvelope}, 403: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}})
    async def list_segments_rest(
        principal: Principal = Depends(require_auth),
        session_id: Annotated[str | None, Query()] = None,
        status: Annotated[str | None, Query()] = None,
        page_size: Annotated[int, Query(ge=1, le=1000)] = 20,
    ) -> dict[str, Any]:
        if not session_id:
            raise validation_error("session_id is required for v0 segment listing in this implementation.", field="session_id")
        require_session_access(principal, session_id)
        segments = [rest_segment(segment) for segment in store.list_segments(session_id, limit=page_size)]
        if status and status.upper() != "ANY":
            requested_status = status.upper()
            if requested_status not in SEGMENT_PUBLIC_STATUSES:
                raise validation_error("Unknown segment status.", field="status")
            segments = [segment for segment in segments if segment["status"] == requested_status]
        return {"segments": segments, "next_page_token": None}

    @app.get("/v1/segments/{segment_id}/events", response_model=SegmentEventsResponse, responses={401: {"model": ErrorEnvelope}, 403: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}})
    async def segment_events_rest(
        segment_id: str,
        principal: Principal = Depends(require_auth),
        page_size: Annotated[int, Query(ge=1, le=1000)] = 20,
    ) -> dict[str, Any]:
        segment = store.get_segment(segment_id)
        if segment is None:
            raise not_found("Segment not found.", segment_id=segment_id)
        session_id = str(segment.get("session_id") or "")
        require_session_access(principal, session_id)
        events = [event_summary(event) for event in store.segment_events(session_id, segment_id, limit=page_size)]
        return {"events": events, "next_page_token": None}

    @app.get("/v1/segments/{segment_id}", response_model=SegmentResponse, responses={401: {"model": ErrorEnvelope}, 403: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}, 422: {"model": ErrorEnvelope}})
    async def get_segment_rest(segment_id: str, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        segment = store.get_segment(segment_id)
        if segment is None:
            raise not_found("Segment not found.", segment_id=segment_id)
        require_session_access(principal, str(segment.get("session_id") or ""))
        return {"segment": rest_segment(segment)}

    @app.post(
        "/v1/segments/{segment_id}/close",
        response_model=SegmentResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def close_segment(
        segment_id: str,
        payload: SegmentCloseRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        request_hash = idempotency_request_hash({"segment_id": segment_id, "body": body})
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/segments/{segment_id}/close",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_schema(body, "segment_close")
        segment = store.get_segment(segment_id)
        if segment is None:
            raise not_found("Segment not found.", segment_id=segment_id)
        session_id = require_payload_str(body, "session_id")
        if session_id != segment.get("session_id"):
            raise validation_error("Segment close session_id does not match segment.", field="session_id")
        require_session_access(principal, session_id)
        outcome = body.get("outcome")
        outcome_upper = str(outcome).upper() if outcome is not None else None
        if outcome_upper is not None and outcome_upper not in SEGMENT_OUTCOMES:
            raise validation_error("Unknown segment close outcome.", field="outcome")
        anchor_event_ids = body.get("anchor_event_ids") if isinstance(body.get("anchor_event_ids"), list) else []
        anchor_event_ids = [str(item) for item in anchor_event_ids if isinstance(item, str) and item]
        require_segment_anchor_events(session_id, anchor_event_ids)
        closed = strip_rich_segment_fields(segment)
        closed["status"] = outcome_upper if outcome_upper in {"ABANDONED", "SUPERSEDED"} else "CLOSED"
        closed["closed_at"] = str(body.get("closed_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        closed["updated_at"] = closed["closed_at"]
        if body.get("summary") is not None:
            closed["summary"] = str(body.get("summary"))[:1000]
        if outcome_upper is not None:
            closed["outcome"] = outcome_upper
        if anchor_event_ids:
            closed["anchor_event_ids"] = anchor_event_ids
        metadata = closed.get("metadata") if isinstance(closed.get("metadata"), dict) else {}
        metadata["close_provenance"] = redact(body.get("provenance") or {})
        closed["metadata"] = metadata
        store.put_segment(closed)
        response = {"segment": rest_segment(store.get_segment(segment_id) or closed)}
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/segments/{segment_id}/close",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post("/v1/context/prepare")
    async def prepare_context(
        payload: dict[str, Any],
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        request_hash = idempotency_request_hash(payload)
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/context/prepare",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay

        def record_prepare_response(response: dict[str, Any]) -> dict[str, Any]:
            record_idempotent_response(
                principal=principal,
                method="POST",
                path="/v1/context/prepare",
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response=response,
            )
            return response

        require_schema(payload, "context_prepare_request")
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        validate_prepare(payload)
        clean_payload = redact(payload)
        policy = clean_payload.get("policy", {})
        budget_split, budget_warnings = _normalize_budget_split(clean_payload, settings=settings)
        warnings = list(budget_warnings)
        requested_cost_mode = str(policy.get("cost_mode") or "STANDARD").upper()
        cost_mode_warnings = cost_mode_warnings_or_error(
            {"cost_mode": requested_cost_mode},
            settings,
            embeddings_available=embeddings_available,
            reranker_available=reranker_available,
            enrichment_available=enrichment_available,
        )

        request_id = clean_payload.get("request_id") or new_id("request")
        prepare_id = clean_payload.get("prepare_id") or request_id
        trace_id = new_id("trace")
        budget_tokens = int(clean_payload["budget_tokens"])
        request_messages = clean_payload["request_messages"]
        request_tokens = approximate_messages_tokens(request_messages)
        latest_user_message_idx = latest_user_message_index(request_messages)
        latest_user_message = request_messages[latest_user_message_idx] if latest_user_message_idx is not None else None
        preserve_system_prompt = bool(policy.get("preserve_system_prompt", True))
        if policy.get("mode") == "OFF":
            trace = prepare_trace(
                trace_id,
                clean_payload,
                [],
                start,
                budget_split=budget_split,
                minimum_headroom_tokens=int(budget_tokens * budget_split["headroom_ratio"]),
            )
            store.put_trace(trace)
            response = {
                "schema_version": "mneme.context_prepare_response.v0",
                "request_id": request_id,
                "prepare_id": prepare_id,
                "session_id": session_id,
                "turn_id": clean_payload.get("turn_id"),
                "changed": False,
                "messages": [],
                "trace_id": trace_id,
                "warnings": cost_mode_warnings + ["POLICY_OFF"],
            }
            return record_prepare_response(response)

        resume_fill_required = store.context_fill_required(session_id)
        retrieval_policy = policy.get("retrieval", {})
        state_for_query = store.execution_state_or_default(session_id)
        query, query_built_from = prepare_retrieval_query(
            clean_payload["request_messages"],
            state_for_query,
            explicit_query=retrieval_policy.get("query"),
        )
        retrieval_top_k = int(retrieval_policy.get("top_k", 24))
        retrieval_scope = parse_search_scope({"scope": retrieval_policy.get("scope") or policy.get("scope") or "LINEAGE"})
        search_session_ids = search_session_ids_for_scope(store, session_id, retrieval_scope)
        results = store.search_events_for_sessions(search_session_ids, query, retrieval_top_k)
        candidate_ids = [item["event_id"] for item in results[:8]]
        candidate_events = [store.get_event_for_sessions(search_session_ids, event_id) for event_id in candidate_ids]
        candidate_events = [event for event in candidate_events if event]
        if not policy.get("include_retrieved_events", True):
            candidate_events = []
        selection_reason = "KEYWORD_RECENCY"
        if resume_fill_required and not candidate_events:
            candidate_events = store.recent_events(session_id, 8)
            selection_reason = "RESUME_CONTEXT_FILL"
        dropped_event_refs: list[dict[str, str]] = []
        candidate_events, freshness_dropped_refs, freshness_warnings = apply_freshness_conflicts_to_events(candidate_events)
        dropped_event_refs.extend(freshness_dropped_refs)
        warnings.extend(freshness_warnings)

        minimum_headroom_ratio = budget_split["headroom_ratio"]
        minimum_headroom_tokens = int(budget_tokens * minimum_headroom_ratio)
        prompt_budget_tokens = max(0, budget_tokens - minimum_headroom_tokens)
        authority_tokens = 0
        if preserve_system_prompt and request_messages and request_messages[0].get("role") == "SYSTEM":
            authority_tokens = token_estimate(str(request_messages[0].get("content", "")))
        latest_user_tokens = token_estimate(str(latest_user_message.get("content", ""))) if latest_user_message else 0
        if latest_user_message is not None and authority_tokens + latest_user_tokens > prompt_budget_tokens:
            raise validation_error(
                "Latest user-authored message exceeds budget with minimum_headroom_tokens reserved.",
                reason="LATEST_USER_MESSAGE_EXCEEDS_BUDGET",
            )
        execution_state_budget_tokens = int(prompt_budget_tokens * budget_split["execution_state_ratio"])
        protected_tail_budget_tokens = int(prompt_budget_tokens * budget_split["protected_tail_ratio"])
        retrieved_evidence_budget_tokens = int(prompt_budget_tokens * budget_split["retrieved_evidence_ratio"])
        hints_budget_tokens = int(prompt_budget_tokens * budget_split["hints_ratio"])

        state_block = ""
        execution_state_tokens = 0
        state_compression = "NONE"
        selected_ids: list[str] = []
        if policy.get("include_execution_state"):
            candidate_state_block, candidate_tokens, compression = execution_state_context_block(
                store.execution_state_or_default(session_id),
                budget_tokens=execution_state_budget_tokens,
            )
            if candidate_state_block:
                if candidate_tokens <= execution_state_budget_tokens:
                    state_block = candidate_state_block
                    execution_state_tokens = candidate_tokens
                    state_compression = compression
                else:
                    state_compression = "DROPPED_FOR_BUDGET"

        execution_state_unused = max(0, execution_state_budget_tokens - execution_state_tokens)
        available_tail_budget_tokens = protected_tail_budget_tokens + execution_state_unused

        messages = list(request_messages)
        protected_tail_tokens = 0
        tail_changed = False
        if policy.get("include_recent_tail"):
            messages, protected_tail_tokens = protected_tail_messages(
                request_messages,
                available_tail_budget_tokens,
                preserve_system_prompt=preserve_system_prompt,
                latest_user_message_index=latest_user_message_idx,
            )
            tail_changed = messages != clean_payload["request_messages"]

        retrieved_unused = max(0, available_tail_budget_tokens - protected_tail_tokens)
        selected_events, budget_dropped_event_refs, retrieved_tokens = pack_retrieved_events(
            candidate_events,
            retrieved_evidence_budget_tokens + retrieved_unused,
        )
        dropped_event_refs.extend(budget_dropped_event_refs)
        selected_ids = [event["event_id"] for event in selected_events]
        retrieved_evidence_budget_tokens = retrieved_evidence_budget_tokens + retrieved_unused

        memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
            store,
            settings,
            session_id,
            include_helpers=bool(state_block or selected_events),
        )
        context_blocks = prepare_context_blocks(
            memory_hint_block,
            goal_trail_block,
            state_block,
            checkpoint_block,
            selected_events,
        )
        if projected_prepare_tokens(messages, context_blocks) > budget_tokens - minimum_headroom_tokens and (
            memory_hint_block or goal_trail_block or checkpoint_block
        ):
            memory_hint_block = ""
            goal_trail_block = ""
            checkpoint_block = ""
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
        if projected_prepare_tokens(messages, context_blocks) > budget_tokens - minimum_headroom_tokens and selected_events:
            dropped_event_refs.extend(
                {"event_id": event["event_id"], "reason": "CONTEXT_COLLISION_BUDGET_EXCEEDED"}
                for event in selected_events
            )
            selected_events = []
            selected_ids = []
            retrieved_tokens = 0
            memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
                store,
                settings,
                session_id,
                include_helpers=bool(state_block),
            )
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
        if policy.get("include_recent_tail") and projected_prepare_tokens(messages, context_blocks) > budget_tokens - minimum_headroom_tokens:
            preserve_system = bool(policy.get("preserve_system_prompt", True))
            available_for_messages = max(0, budget_tokens - minimum_headroom_tokens - context_blocks_tokens(context_blocks))
            system_tokens = (
                token_estimate(str(clean_payload["request_messages"][0].get("content", "")))
                if preserve_system and clean_payload["request_messages"] and clean_payload["request_messages"][0].get("role") == "SYSTEM"
                else 0
            )
            messages, protected_tail_tokens = protected_tail_messages(
                request_messages,
                max(0, available_for_messages - system_tokens),
                preserve_system_prompt=preserve_system,
                latest_user_message_index=latest_user_message_idx,
            )
            tail_changed = messages != clean_payload["request_messages"]
        if projected_prepare_tokens(messages, context_blocks) > budget_tokens - minimum_headroom_tokens:
            if latest_user_message is not None:
                raise validation_error(
                    "Minimum required content cannot fit after safe truncation.",
                    reason="MINIMUM_REQUIRED_CONTENT_EXCEEDS_BUDGET",
                )
            state_block = ""
            execution_state_tokens = 0
            state_compression = "DROPPED_FOR_BUDGET"
            memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
                store,
                settings,
                session_id,
                include_helpers=bool(selected_events),
            )
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
            if selected_events:
                retrieved_evidence_budget_tokens = 0
                retrieved_tokens = 0
                dropped_event_refs = [{"event_id": event["event_id"], "reason": "CONTEXT_COLLISION_BUDGET_EXCEEDED"} for event in selected_ids]
        degraded = projected_prepare_tokens(messages, context_blocks) > budget_tokens - minimum_headroom_tokens
        unused_context_slack_tokens = max(
            0,
            (budget_tokens - minimum_headroom_tokens) - projected_prepare_tokens(messages, context_blocks),
        )
        trace_warnings = warnings + cost_mode_warnings
        if state_compression == "TRUNCATED" and "EXECUTION_STATE_TRUNCATED" not in trace_warnings:
            trace_warnings.append("EXECUTION_STATE_TRUNCATED")

        trace = prepare_trace(
            trace_id,
            clean_payload,
            selected_events,
            start,
            selection_reason=selection_reason,
            execution_state_tokens=execution_state_tokens,
            protected_tail_tokens=protected_tail_tokens,
            dropped_event_refs=dropped_event_refs,
            retrieved_tokens=retrieved_tokens,
            degraded=degraded,
            context_blocks=context_blocks,
            minimum_headroom_tokens=minimum_headroom_tokens,
            execution_state_budget_tokens=execution_state_budget_tokens,
            protected_tail_budget_tokens=available_tail_budget_tokens,
            retrieved_evidence_budget_tokens=retrieved_evidence_budget_tokens,
            hints_budget_tokens=hints_budget_tokens,
            budget_split=budget_split,
            unused_context_slack_tokens=unused_context_slack_tokens,
            memory_hint_tokens=token_estimate(memory_hint_block),
            goal_trail_tokens=token_estimate(goal_trail_block),
            checkpoint_tokens=token_estimate(checkpoint_block),
            cross_session_event_ids=cross_session_event_ids(session_id, selected_events),
            state_compression=state_compression,
            query_built_from=query_built_from,
            trace_warnings=trace_warnings,
        )
        store.put_trace(trace)
        store.add_audit(session_id, "MEMORY_READ", "context_prepare", selected_ids, trace_id=trace_id)

        if not selected_events and not state_block and not tail_changed and request_tokens < budget_tokens:
            response = {
                "schema_version": "mneme.context_prepare_response.v0",
                "request_id": request_id,
                "prepare_id": prepare_id,
                "session_id": session_id,
                "turn_id": clean_payload.get("turn_id"),
                "changed": False,
                "messages": [],
                "trace_id": trace_id,
                "warnings": trace_warnings + ["REQUEST_UNDER_BUDGET"],
            }
            return record_prepare_response(response)
        if resume_fill_required and selected_events:
            store.mark_context_fill_fulfilled(session_id)
        if not context_blocks and not tail_changed:
            response = {
                "schema_version": "mneme.context_prepare_response.v0",
                "request_id": request_id,
                "prepare_id": prepare_id,
                "session_id": session_id,
                "turn_id": clean_payload.get("turn_id"),
                "changed": False,
                "messages": [],
                "trace_id": trace_id,
                "warnings": trace_warnings + ["NO_CONTEXT_AVAILABLE"],
            }
            return record_prepare_response(response)
        context_message_role = None
        if context_blocks:
            memory_message = {
                "schema_version": "mneme.message.v0",
                "role": "ASSISTANT",
                "content": "\n\n".join(context_blocks).strip(),
                "metadata": {"mneme_generated": True, "trace_id": trace_id},
            }
            context_message_role = memory_message["role"]
            insert_at = 1 if messages and messages[0].get("role") == "SYSTEM" else 0
            messages.insert(insert_at, memory_message)
        response = {
            "schema_version": "mneme.context_prepare_response.v0",
            "request_id": request_id,
            "prepare_id": prepare_id,
            "session_id": session_id,
            "turn_id": clean_payload.get("turn_id"),
            "changed": True,
            "messages": messages,
            "trace_id": trace_id,
            "trace": {
                "budget_tokens": clean_payload["budget_tokens"],
                "input_request_tokens": request_tokens,
                "system_prompt_tokens": token_estimate(messages[0].get("content", "")) if messages else 0,
                "execution_state_tokens": execution_state_tokens,
                "execution_state_compression_level": state_compression,
                "protected_tail_tokens": protected_tail_tokens,
                "retrieved_tokens": retrieved_tokens,
                "minimum_headroom_tokens": minimum_headroom_tokens,
                "headroom_tokens": minimum_headroom_tokens,
                "unused_context_slack_tokens": unused_context_slack_tokens,
                "budget_split": budget_split,
                "execution_state_budget_tokens": execution_state_budget_tokens,
                "protected_tail_budget_tokens": available_tail_budget_tokens,
                "retrieved_evidence_budget_tokens": retrieved_evidence_budget_tokens,
                "hints_budget_tokens": hints_budget_tokens,
                "candidate_count": len(results),
                "context_blocks": len(context_blocks),
                "memory_hint_tokens": token_estimate(memory_hint_block),
                "goal_trail_tokens": token_estimate(goal_trail_block),
                "checkpoint_tokens": token_estimate(checkpoint_block),
                "state_compression": state_compression,
                "selected_event_ids": selected_ids,
                "selected_event_refs": [{"event_id": event_id, "reason": selection_reason} for event_id in selected_ids],
                "cross_session_event_ids": cross_session_event_ids(session_id, selected_events),
                "dropped_event_refs": dropped_event_refs,
                "degraded": degraded,
                "warnings": trace_warnings,
            },
            "adapter_metadata": {
                "can_insert_automatically": False,
                "insertion_mode": "request-only context block; host hook required for automatic insertion",
                "context_message_role": context_message_role,
                "trace_id": trace_id,
            },
            "warnings": trace_warnings,
            "cost_estimate": {"embedding_calls": 0, "reranker_calls": 0, "enrichment_calls": 0},
        }
        return record_prepare_response(response)

    @app.post(
        "/v1/tools/resolve_session",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def resolve_session(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        page_size = discovery_page_size(payload, default=10, maximum=50)
        page_token = parse_page_token(payload)
        session_id = optional_payload_str(payload, "session_id")
        project_path = optional_payload_str(payload, "project_path")
        thread_id = optional_payload_str(payload, "thread_id")
        slug = optional_payload_str(payload, "slug")
        query = optional_payload_str(payload, "query")
        if not any([session_id, project_path, thread_id, slug, query]):
            raise validation_error(
                "resolve_session requires session_id, project_path, thread_id, slug, or query.",
                field="session_id",
            )

        project_keys = visible_project_keys(principal)
        exact = None
        if session_id and store.has_session(session_id):
            session_project = store.session_project_key(session_id)
            if principal.can_access_project(session_project):
                exact = store.get_session_summary(session_id)
        if exact:
            return tool_response(
                {
                    "resolved_session_id": exact["session_id"],
                    "resolution": "EXACT_SESSION_ID",
                    "matches": [exact],
                    "next_page_token": None,
                    "matches_truncated": False,
                },
                session_resolution=session_resolution(exact["session_id"], "RESOLVED_BY_TOOL"),
            )

        search_query = query or session_id
        page = store.list_sessions_page(
            query=search_query,
            project_path=project_path,
            thread_id=thread_id,
            slug=slug,
            project_isolation_keys=project_keys,
            page_size=page_size,
            page_token=page_token,
        )
        matches = sorted_resolution_matches(
            page["sessions"],
            project_path=project_path,
            thread_id=thread_id,
            project_isolation_keys=project_keys,
        )
        resolved_session_id = matches[0]["session_id"] if len(matches) == 1 else None
        if resolved_session_id:
            resolution = "SINGLE_MATCH"
            best_guess_session_id = resolved_session_id
            warnings: list[dict[str, Any]] = []
        elif matches:
            resolution = "AMBIGUOUS"
            best_guess_session_id = best_guess_session_id_for_matches(
                matches,
                project_path=project_path,
                thread_id=thread_id,
                project_isolation_keys=project_keys,
            )
            warnings = [
                {
                    "code": "SESSION_RESOLUTION_AMBIGUOUS",
                    "message": "Multiple sessions matched; call list_sessions with the same project filters or refine project_path, thread_id, or slug.",
                }
            ]
        else:
            resolution = "NOT_FOUND"
            best_guess_session_id = None
            warnings = [{"code": "SESSION_NOT_FOUND", "message": "No session matched; check that REST/importer/hooks write to the same Mneme database as this MCP server."}]
        return tool_response(
            {
                "resolved_session_id": resolved_session_id,
                "best_guess_session_id": best_guess_session_id,
                "resolution": resolution,
                "matches": matches,
                "next_page_token": page["next_page_token"],
                "matches_truncated": page["matches_truncated"],
            },
            warnings=warnings,
            session_resolution=session_resolution(resolved_session_id, "RESOLVED_BY_TOOL") if resolved_session_id else None,
        )

    @app.post(
        "/v1/tools/list_sessions",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def list_sessions(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        page_size = discovery_page_size(payload, default=20, maximum=100)
        page_token = parse_page_token(payload)
        page = store.list_sessions_page(
            query=optional_payload_str(payload, "query"),
            project_path=optional_payload_str(payload, "project_path"),
            thread_id=optional_payload_str(payload, "thread_id"),
            slug=optional_payload_str(payload, "slug"),
            project_isolation_keys=visible_project_keys(principal),
            page_size=page_size,
            page_token=page_token,
        )
        return tool_response(
            {
                "sessions": page["sessions"],
                "count": page["count"],
                "next_page_token": page["next_page_token"],
                "matches_truncated": page["matches_truncated"],
            }
        )

    @app.post(
        "/v1/tools/context_search",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def context_search(
        payload: ToolRequestPayload,
        project_isolation_key: Annotated[
            str | None,
            Header(alias="X-Mneme-Project-Isolation-Key"),
        ] = None,
        principal: Principal = Depends(require_auth),
    ) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id, requested_project_key=project_isolation_key)
        query = redact(str(payload.get("query", "")))
        top_k = parse_int(payload, "top_k", default=10, minimum=1, maximum=100)
        filters = search_filters(payload)
        scope = parse_search_scope(payload)
        results, retrieval, warnings = hybrid_context_search(
            store,
            embedding_index,
            session_id=session_id,
            query=query,
            top_k=top_k,
            filters=filters,
            scope=scope,
            mode=search_mode(payload, settings=settings),
            project_isolation_key=project_isolation_key,
            global_session_ids=visible_session_ids(principal, project_isolation_key),
            project_session_ids=project_session_ids_for_scope(principal, session_id),
            reranker=reranker,
            reranker_top_k=settings.reranker_top_k,
            routing_mode_weights=settings.routing_mode_weights,
        )
        trace_id = audit_memory_tool(
            store,
            session_id,
            "context_search",
            [item["event_id"] for item in results],
            retrieval=retrieval,
            warnings=warnings,
            audit_mode=settings.audit_mode,
        )
        return tool_response(
            {"results": results},
            trace_id=trace_id,
            warnings=warnings,
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/fetch_event",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def fetch_event(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        event_id = require_payload_str(payload, "event_id")
        require_session_access(principal, session_id)
        event = store.get_event(session_id, event_id)
        if not event:
            raise not_found("Event not found.", event_id=event_id)
        response_event, metadata = event_for_fetch(store, session_id, event, full=bool(payload.get("full")))
        neighbors = store.neighbor_events(session_id, event_id) if payload.get("include_neighbors") else []
        exposed_event_ids = [event_id, *[neighbor["event_id"] for neighbor in neighbors]]
        trace_id = audit_memory_tool(store, session_id, "fetch_event", exposed_event_ids, audit_mode=settings.audit_mode)
        return tool_response(
            {"event": response_event, "metadata": metadata, "neighbors": neighbors},
            trace_id=trace_id,
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/expand_context",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def expand_context(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        seed_id = require_payload_str(payload, "seed_event_id")
        require_session_access(principal, session_id)
        max_events = min(parse_int(payload, "max_events", default=12, minimum=1, maximum=200), settings.max_tool_result_events)
        depth = parse_int(payload, "depth", default=2, minimum=0, maximum=5)
        mode = str(payload.get("mode") or "GRAPH").strip().upper()
        if mode == "SEGMENT":
            segment_id = store.segment_id_for_event(session_id, seed_id)
            if not segment_id:
                raise not_found("Segment not found for seed event.", event_id=seed_id)
            events = store.get_segment_skeleton(session_id, segment_id, max_events=max_events)
            trace_id = audit_memory_tool(store, session_id, "expand_context", [item["event_id"] for item in events], audit_mode=settings.audit_mode)
            truncated = len(events) >= max_events
            warnings = [{"code": "RESULT_TRUNCATED", "message": "Segment skeleton hit max_events."}] if truncated else []
            return tool_response(
                {"seed_event_id": seed_id, "mode": "SEGMENT", "segment_id": segment_id, "truncated": truncated, "events": events},
                trace_id=trace_id,
                warnings=warnings,
                session_resolution=session_resolution(session_id),
            )
        if mode == "TEMPORAL":
            temporal_result = expand_temporal(store, session_id, seed_id, max_events)
            events = temporal_result["events"]
            trace_id = audit_memory_tool(store, session_id, "expand_context", [item["event_id"] for item in events], audit_mode=settings.audit_mode)
            return tool_response(
                {
                    "seed_event_id": seed_id,
                    "mode": "TEMPORAL",
                    "truncated": temporal_result["truncated"],
                    "truncation_reason": temporal_result["truncation_reason"],
                    "dropped_count": temporal_result["dropped_count"],
                    "frontier_summary": temporal_result["frontier_summary"],
                    "events": events,
                },
                trace_id=trace_id,
                warnings=temporal_result["warnings"],
                session_resolution=session_resolution(session_id),
            )
        graph_result = expand_graph(
            store,
            session_id,
            seed_id,
            mode,
            depth,
            max_events,
            importance_depth_decay=settings.graph_importance_depth_decay,
            max_traversal_steps=settings.graph_max_traversal_steps,
            max_frontier_size=settings.graph_max_frontier_size,
            max_branching_factor=settings.graph_max_branching_factor,
        )
        events = graph_result["events"]
        trace_id = audit_memory_tool(store, session_id, "expand_context", [item["event_id"] for item in events], audit_mode=settings.audit_mode)
        return tool_response(
            {
                "seed_event_id": seed_id,
                "mode": mode,
                "truncated": graph_result["truncated"],
                "truncation_reason": graph_result["truncation_reason"],
                "dropped_count": graph_result["dropped_count"],
                "frontier_summary": graph_result["frontier_summary"],
                "events": events,
            },
            trace_id=trace_id,
            warnings=graph_result["warnings"],
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/recall_recent",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def recall_recent(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        turns = parse_int(payload, "turns", default=3, minimum=1, maximum=100)
        events = store.recent_events(session_id, turns * 10)
        if payload.get("include_tool_outputs") is False:
            events = [event for event in events if event.get("type") != "TOOL_OUTPUT"]
        max_tokens = parse_optional_int(payload, "max_tokens", minimum=1, maximum=200000)
        events, truncated = pack_events_under_token_limit(events, max_tokens)
        trace_id = audit_memory_tool(store, session_id, "recall_recent", [event["event_id"] for event in events], audit_mode=settings.audit_mode)
        warnings = [{"code": "RESULT_TRUNCATED", "message": "Recent recall hit max_tokens before all candidate events fit."}] if truncated else []
        return tool_response(
            {"events": summarize_events(events)},
            trace_id=trace_id,
            warnings=warnings,
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/list_segments",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def list_segments(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        page_size = parse_int(payload, "page_size", default=20, minimum=1, maximum=1000)
        segments = store.list_segments(session_id, limit=page_size)
        trace_id = audit_memory_tool(store, session_id, "list_segments", [], audit_mode=settings.audit_mode)
        return tool_response(
            {"segments": segments, "next_page_token": None},
            trace_id=trace_id,
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/get_execution_state",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def get_execution_state(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        state = store.execution_state_or_default(session_id)
        trace_id = audit_memory_tool(store, session_id, "get_execution_state", [], audit_mode=settings.audit_mode)
        return tool_response(state, trace_id=trace_id, session_resolution=session_resolution(session_id))

    @app.post(
        "/v1/tools/get_goal_history",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def get_goal_history(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        limit = parse_int(payload, "limit", default=20, minimum=1, maximum=200)
        history = store.get_state_history(session_id, limit=limit)
        trace_id = audit_memory_tool(store, session_id, "get_goal_history", [], audit_mode=settings.audit_mode)
        return tool_response(
            {"history": history},
            trace_id=trace_id,
            session_resolution=session_resolution(session_id),
        )

    @app.post(
        "/v1/tools/explain_context",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def explain_context(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        trace = store.get_trace(require_payload_str(payload, "trace_id"))
        if not trace:
            raise not_found("Trace not found.", trace_id=payload.get("trace_id"))
        require_session_access(principal, trace["session_id"])
        event_id = payload.get("event_id")
        selected = next((event for event in trace.get("selected_events", []) if event.get("event_id") == event_id), None)
        read_trace_id = audit_memory_tool(store, trace["session_id"], "explain_context", [event_id] if selected and isinstance(event_id, str) else [], audit_mode=settings.audit_mode)
        return tool_response(
            {"trace_id": trace["trace_id"], "event_id": event_id, "included": selected is not None, "reason": selected.get("reason") if selected else None, "score": selected.get("score") if selected else None, "layer": selected.get("included_as") if selected else None},
            trace_id=read_trace_id,
            session_resolution=session_resolution(trace["session_id"]),
        )

    @app.post(
        "/v1/tools/mneme_cost_report",
        response_model=ToolResponseEnvelope,
        responses=tool_responses,
    )
    async def mneme_cost_report_tool(payload: ToolRequestPayload, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        payload = model_payload(payload)
        validate_tool_request_schema(payload)
        session_id = require_payload_str(payload, "session_id")
        require_session_access(principal, session_id)
        trace_id = audit_memory_tool(store, session_id, "mneme_cost_report", [], audit_mode=settings.audit_mode)
        return tool_response(
            store.cost_report(session_id),
            trace_id=trace_id,
            session_resolution=session_resolution(session_id),
        )

    @app.get(
        "/v1/traces/{trace_id}",
        response_model=TraceResponse,
        responses={401: {"model": ErrorEnvelope}, 403: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}},
    )
    async def get_trace(trace_id: str, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        trace = store.get_trace(trace_id)
        if not trace:
            raise not_found("Trace not found.", trace_id=trace_id)
        require_session_access(principal, trace["session_id"])
        return trace

    @app.get(
        "/v1/costs/session/{session_id}",
        response_model=CostReportResponse,
        responses={401: {"model": ErrorEnvelope}, 403: {"model": ErrorEnvelope}, 404: {"model": ErrorEnvelope}},
    )
    async def cost_report(session_id: str, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        require_session_access(principal, session_id)
        return store.cost_report(session_id)

    def session_summary_response(session_id: str) -> dict[str, Any]:
        summary = store.get_session_summary(session_id)
        session = store.get_session(session_id)
        if summary is None or session is None:
            raise not_found("Session not found.", **session_not_found_details(store, session_id))
        latest_events = store.recent_events(session_id, 1)
        latest_event_preview = None
        if latest_events:
            event = latest_events[0]
            latest_event_preview = {
                "event_id": event.get("event_id"),
                "type": event.get("type"),
                "timestamp": event.get("timestamp"),
                "content": event.get("content"),
            }
        return {
            **summary,
            "segment_count": store.segment_count(session_id),
            "blob_count": store.count_blobs_for_session(session_id),
            "latest_event_preview": latest_event_preview,
            "session": redact(session),
        }

    def parse_retention_base_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def retention_days_for_session(session: dict[str, Any]) -> int:
        privacy = session.get("privacy") if isinstance(session.get("privacy"), dict) else {}
        raw_days = privacy.get("retention_days", 30)
        try:
            days = int(raw_days)
        except (TypeError, ValueError):
            return 30
        return max(days, 0)

    def retention_cutoff(session: dict[str, Any], *, request_time: datetime) -> tuple[str, list[str]]:
        warnings: list[str] = []
        base = request_time
        if session.get("status") == "ENDED":
            ended_at = parse_retention_base_timestamp(session.get("ended_at"))
            if ended_at is None:
                warnings.append("ENDED_SESSION_MISSING_ENDED_AT")
            else:
                base = ended_at
        cutoff = base - timedelta(days=retention_days_for_session(session))
        return cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), warnings

    def run_startup_retention_sweeps() -> None:
        if not settings.retention_sweep_on_startup:
            return
        request_time = datetime.now(timezone.utc)
        for summary in store.list_sessions(limit=1000):
            session_id = str(summary.get("session_id") or "")
            if not session_id:
                continue
            session = store.get_session(session_id)
            if not session or str(session.get("status") or "ACTIVE").upper() != "ENDED":
                continue
            cutoff_timestamp, warnings = retention_cutoff(session, request_time=request_time)
            cleanup_result = store.cleanup_retention(session_id, cutoff_timestamp, dry_run=False)
            blob_gc = store.garbage_collect_blobs(
                project_isolation_key=store.session_project_key(session_id),
                session_id=session_id,
                dry_run=False,
            )
            candidate_counts = {
                **cleanup_result["candidate_counts"],
                "blobs": int(blob_gc["candidate_count"]),
            }
            deleted_counts = {
                **cleanup_result["deleted_counts"],
                "blobs": int(blob_gc["deleted_count"]),
            }
            if not any(int(value) for value in candidate_counts.values()) and not any(
                int(value) for value in deleted_counts.values()
            ):
                continue
            store.add_audit(
                session_id,
                "RETENTION_CLEANUP",
                "SYSTEM_DAEMON",
                [],
                project_isolation_key=store.session_project_key(session_id),
                principal={
                    "name": "SYSTEM_DAEMON",
                    "role": "SYSTEM_DAEMON",
                    "project_scopes": [store.session_project_key(session_id)] if store.session_project_key(session_id) else [],
                },
                request={
                    "trigger": "STARTUP",
                    "dry_run": False,
                    "force_active_cleanup": False,
                },
                result={
                    "trigger": "STARTUP",
                    "cutoff_timestamp": cutoff_timestamp,
                    "candidate_counts": candidate_counts,
                    "deleted_counts": {
                        "events": int(deleted_counts.get("events", 0)),
                        "derived_records": int(deleted_counts.get("derived_records", 0)),
                        "traces": int(deleted_counts.get("traces", 0)),
                        "state_history": int(deleted_counts.get("state_history", 0)),
                        "graph_edges": int(deleted_counts.get("graph_edges", 0)),
                        "blobs": int(deleted_counts.get("blobs", 0)),
                    },
                    "orphan_counts": {"blobs": int(blob_gc["candidate_count"])},
                    "warnings": warnings + [str(warning) for warning in blob_gc.get("warnings", [])],
                },
            )

    def run_startup_forensic_anchor_retention() -> None:
        store.purge_forensic_anchors_older_than(
            retention_days=settings.audit_forensic_retention_days,
        )

    run_startup_forensic_anchor_retention()
    run_startup_retention_sweeps()

    @app.get(
        "/v1/sessions/{session_id}",
        response_model=SessionSummaryResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def get_session(session_id: str, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        require_session_access(principal, session_id)
        return session_summary_response(session_id)

    @app.post(
        "/v1/sessions/{session_id}/close",
        response_model=SessionCloseResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def close_session(
        session_id: str,
        payload: dict[str, Any] | None = Body(default=None),
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = payload or {}
        request_hash = idempotency_request_hash({"session_id": session_id, "body": body})
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/close",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_session_access(principal, session_id)
        ended_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        closed = store.close_session(session_id, ended_at)
        if closed is None:
            raise not_found("Session not found.", **session_not_found_details(store, session_id))
        session, changed = closed
        if changed and settings.retention_sweep_on_session_close:
            cutoff_timestamp, sweep_warnings = retention_cutoff(session, request_time=datetime.now(timezone.utc))
            cleanup_result = store.cleanup_retention(session_id, cutoff_timestamp, dry_run=False)
            blob_gc = store.garbage_collect_blobs(
                project_isolation_key=store.session_project_key(session_id),
                session_id=session_id,
                dry_run=False,
            )
            deleted_counts = {
                **cleanup_result["deleted_counts"],
                "blobs": int(blob_gc["deleted_count"]),
            }
            store.add_audit(
                session_id,
                "RETENTION_CLEANUP",
                "SYSTEM_DAEMON",
                [],
                project_isolation_key=store.session_project_key(session_id),
                principal={
                    "name": "SYSTEM_DAEMON",
                    "role": "SYSTEM_DAEMON",
                    "project_scopes": [store.session_project_key(session_id)] if store.session_project_key(session_id) else [],
                },
                request={"trigger": "SESSION_CLOSE", "dry_run": False},
                result={
                    "trigger": "SESSION_CLOSE",
                    "cutoff_timestamp": cutoff_timestamp,
                    "candidate_counts": cleanup_result["candidate_counts"],
                    "deleted_counts": deleted_counts,
                    "orphan_counts": {"blobs": int(blob_gc["candidate_count"])},
                    "warnings": sweep_warnings + [str(warning) for warning in blob_gc.get("warnings", [])],
                },
            )
        response = {
            "session_id": session_id,
            "status": "ENDED",
            "closed": changed,
            "ended_at": str(session.get("ended_at") or ended_at),
            "warnings": [],
        }
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/close",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post(
        "/v1/sessions/{session_id}/execution_state",
        response_model=ExecutionStateUpdateResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def update_execution_state(
        session_id: str,
        payload: ExecutionStateUpdateRequest,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        request_hash = idempotency_request_hash({"session_id": session_id, "body": body})
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/execution_state",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_schema(body, "execution_state_update")
        require_session_access(principal, session_id)
        mode = str(body.get("mode") or "").upper()
        if mode not in {"PATCH", "REPLACE"}:
            raise validation_error("execution_state update mode must be PATCH or REPLACE.", field="mode")
        state_patch = body.get("state")
        if not isinstance(state_patch, dict) or not state_patch:
            raise validation_error("execution_state update requires a non-empty state object.", field="state")
        for key in sorted(state_patch):
            if key not in EXECUTION_STATE_ALLOWED_FIELDS:
                raise validation_error(
                    "Unknown execution_state field.",
                    field=f"state.{key}",
                )
        provenance = body.get("provenance")
        if not isinstance(provenance, dict) or not any(
            isinstance(provenance.get(field), str) and provenance.get(field)
            for field in EXECUTION_STATE_PROVENANCE_FIELDS
        ):
            raise validation_error(
                "execution_state update requires provenance.event_id, provenance.turn_id, or provenance.adapter_trace_id.",
                field="provenance",
            )
        clean_patch = redact(state_patch)
        clean_provenance = redact(
            {
                key: provenance[key]
                for key in sorted(EXECUTION_STATE_PROVENANCE_FIELDS)
                if isinstance(provenance.get(key), str) and provenance.get(key)
            }
        )
        updated = store.update_execution_state(
            session_id,
            mode=mode,
            state_patch=clean_patch,
            provenance=clean_provenance,
        )
        response = {
            "schema_version": "mneme.execution_state_update_result.v0",
            "session_id": session_id,
            "updated": True,
            "state": updated["state"],
            "history_entry": updated["history_entry"],
        }
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/execution_state",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.post(
        "/v1/sessions/{session_id}/retention/cleanup",
        response_model=RetentionCleanupResponse,
        responses={
            401: {"model": ErrorEnvelope},
            403: {"model": ErrorEnvelope},
            404: {"model": ErrorEnvelope},
            409: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
        },
    )
    async def retention_cleanup(
        session_id: str,
        payload: RetentionCleanupRequest = Body(default_factory=RetentionCleanupRequest),
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        body = model_payload(payload)
        if body.get("schema_version") is not None:
            require_schema(body, "retention_cleanup_request")
        dry_run = bool(body.get("dry_run", False))
        force_active_cleanup = bool(body.get("force_active_cleanup", False))
        normalized_body = {
            "dry_run": dry_run,
            "force_active_cleanup": force_active_cleanup,
        }
        request_hash = idempotency_request_hash({"session_id": session_id, "body": normalized_body})
        replay = replay_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/retention/cleanup",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_session_access(principal, session_id)
        session = store.get_session(session_id)
        if session is None:
            raise not_found("Session not found.", **session_not_found_details(store, session_id))
        status = str(session.get("status") or "ACTIVE").upper()
        if status == "ACTIVE" and force_active_cleanup and not (principal.role == "OWNER" and principal.all_projects):
            raise forbidden(
                "Active-session retention cleanup requires OWNER authorization.",
                reason="ACTIVE_SESSION_FORCE_REQUIRES_OWNER",
                session_id=session_id,
            )
        if status == "ACTIVE" and force_active_cleanup:
            in_flight_reads = app.state.in_flight_reads.count(session_id)
            if in_flight_reads:
                raise conflict(
                    "Active-session retention cleanup blocked by in-flight memory reads.",
                    reason="IN_FLIGHT_READS",
                    session_id=session_id,
                    in_flight_reads=in_flight_reads,
                )
        request_time = datetime.now(timezone.utc)
        cutoff_timestamp, warnings = retention_cutoff(session, request_time=request_time)
        active_session_skipped = status == "ACTIVE" and not force_active_cleanup
        if active_session_skipped:
            candidate_counts = {"events": 0, "derived_records": 0, "blobs": 0}
            deleted_counts = {"events": 0, "derived_records": 0, "traces": 0, "state_history": 0, "graph_edges": 0, "blobs": 0}
            orphan_counts = {"blobs": 0}
            warnings.append("ACTIVE_SESSION_SKIPPED")
        else:
            cleanup_result = store.cleanup_retention(session_id, cutoff_timestamp, dry_run=dry_run)
            candidate_counts = cleanup_result["candidate_counts"]
            deleted_counts = cleanup_result["deleted_counts"]
            blob_gc = store.garbage_collect_blobs(
                project_isolation_key=store.session_project_key(session_id),
                session_id=session_id,
                dry_run=dry_run,
            )
            candidate_counts = {**candidate_counts, "blobs": int(blob_gc["candidate_count"])}
            deleted_counts = {**deleted_counts, "blobs": int(blob_gc["deleted_count"])}
            orphan_counts = {"blobs": int(blob_gc["candidate_count"])}
            warnings.extend(str(warning) for warning in blob_gc.get("warnings", []))
        response_status = "SKIPPED_ACTIVE_SESSION" if active_session_skipped else "DRY_RUN" if dry_run else "COMPLETED"
        response = {
            "schema_version": "mneme.retention_cleanup_result.v0",
            "session_id": session_id,
            "status": response_status,
            "cutoff_timestamp": cutoff_timestamp,
            "candidate_counts": candidate_counts,
            "deleted_counts": {"events": 0, "derived_records": 0, "blobs": 0},
            "orphan_counts": orphan_counts,
            "dry_run": dry_run,
            "force_active_cleanup": force_active_cleanup,
            "active_session_skipped": active_session_skipped,
            "skipped_active_session": active_session_skipped,
            "events_deleted": int(deleted_counts.get("events", 0)),
            "state_history_deleted": int(deleted_counts.get("state_history", 0)),
            "graph_edges_deleted": int(deleted_counts.get("graph_edges", 0)),
            "blobs_deleted": int(deleted_counts.get("blobs", 0)),
            "blobs_orphaned": int(orphan_counts.get("blobs", 0)),
            "in_flight_reads_blocked": 0,
            "warnings": warnings,
        }
        response["deleted_counts"] = {
            "events": int(deleted_counts.get("events", 0)),
            "derived_records": int(deleted_counts.get("derived_records", 0)),
            "traces": int(deleted_counts.get("traces", 0)),
            "state_history": int(deleted_counts.get("state_history", 0)),
            "graph_edges": int(deleted_counts.get("graph_edges", 0)),
            "blobs": int(deleted_counts.get("blobs", 0)),
        }
        store.add_audit(
            session_id,
            "RETENTION_CLEANUP",
            "REST",
            [],
            project_isolation_key=store.session_project_key(session_id),
            principal={
                "name": principal.name,
                "role": principal.role,
                "project_scopes": list(principal.project_scopes),
            },
            request={
                "dry_run": dry_run,
                "force_active_cleanup": force_active_cleanup,
            },
            result={
                "status": response_status,
                "cutoff_timestamp": cutoff_timestamp,
                "candidate_counts": candidate_counts,
                "deleted_counts": response["deleted_counts"],
                "orphan_counts": orphan_counts,
                "active_session_skipped": active_session_skipped,
            },
        )
        record_idempotent_response(
            principal=principal,
            method="POST",
            path="/v1/sessions/{session_id}/retention/cleanup",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.get("/v1/sessions/{session_id}/export")
    async def export_session(
        session_id: str,
        principal: Principal = Depends(require_auth),
        export_format: Annotated[str, Query(alias="format")] = "json",
        include_blobs: Annotated[bool, Query()] = False,
        include_audit: Annotated[bool, Query()] = False,
    ) -> Any:
        require_session_access(principal, session_id)
        if export_format not in {"json", "tar_bundle"}:
            raise validation_error(
                "Unknown export format.",
                field="format",
                value=export_format,
            )
        if export_format == "tar_bundle":
            bundle_file = tempfile.SpooledTemporaryFile(max_size=1_048_576)
            exported_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            blobs = store.list_blob_metadata_for_session(session_id) if include_blobs else []
            manifest = {
                "schema_version": "mneme.session_export_manifest.v0",
                "format": "tar_bundle",
                "session_id": session_id,
                "manifest_part": "manifest.json",
                "blob_parts": [
                    {
                        "blob_id": blob["blob_id"],
                        "path": f"blobs/{blob['blob_id']}.bin",
                        "size_bytes": blob["size_bytes"],
                        "hash": blob["hash"],
                        "media_type": blob["media_type"],
                        "redaction_scope": "BINARY_METADATA_ONLY",
                    }
                    for blob in blobs
                ],
                "exported_at": exported_at,
                "redaction_applied": True,
            }
            with tarfile.open(fileobj=bundle_file, mode="w") as bundle:
                manifest_bytes = canonical_json(manifest).encode("utf-8")
                manifest_info = tarfile.TarInfo("manifest.json")
                manifest_info.size = len(manifest_bytes)
                bundle.addfile(manifest_info, io.BytesIO(manifest_bytes))
                for blob in blobs:
                    content = store.get_blob_content(blob["blob_id"]) or b""
                    info = tarfile.TarInfo(f"blobs/{blob['blob_id']}.bin")
                    info.size = len(content)
                    bundle.addfile(info, io.BytesIO(content))
            bundle_file.seek(0)

            def iter_bundle() -> Any:
                try:
                    while True:
                        chunk = bundle_file.read(65_536)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    bundle_file.close()

            return StreamingResponse(
                iter_bundle(),
                media_type="application/x-tar",
            )
        return store.export_session(session_id, include_audit=include_audit)

    @app.delete("/v1/sessions/{session_id}")
    async def delete_session(
        session_id: str,
        principal: Principal = Depends(require_auth),
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> dict[str, Any]:
        request_hash = idempotency_request_hash({"session_id": session_id})
        replay = replay_idempotent_response(
            principal=principal,
            method="DELETE",
            path="/v1/sessions/{session_id}",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replay is not None:
            return replay
        require_session_access(principal, session_id)
        project_key = store.session_project_key(session_id)
        store.add_audit(
            session_id,
            "SESSION_DELETE",
            "REST",
            [],
            project_isolation_key=project_key,
            principal={
                "name": principal.name,
                "role": principal.role,
                "project_scopes": list(principal.project_scopes),
            },
            request={"method": "DELETE", "path": "/v1/sessions/{session_id}"},
            result={"requested": True},
        )
        deleted = store.delete_session(session_id)
        response = {"session_id": session_id, "deleted": deleted}
        record_idempotent_response(
            principal=principal,
            method="DELETE",
            path="/v1/sessions/{session_id}",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response=response,
        )
        return response

    @app.get(
        "/v1/sessions/{session_id:path}",
        include_in_schema=False,
        responses={422: {"model": ErrorEnvelope}},
    )
    async def invalid_session_path(session_id: str, principal: Principal = Depends(require_auth)) -> dict[str, Any]:
        validate_session_id(session_id)
        raise not_found("Session not found.", **session_not_found_details(store, session_id))

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=app.description,
        )
        components = schema.setdefault("components", {})
        components.setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
        }
        schemas = components.setdefault("schemas", {})
        schemas.setdefault(
            "EventBatchRequest",
            EventBatchRequest.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "MessageContentPart",
            MessageContentPart.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "Message",
            Message.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "TurnCompleteRequest",
            TurnCompleteRequest.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "TurnCompleteResponse",
            TurnCompleteResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "ContextPrepareRequest",
            ContextPrepareRequest.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "ContextPrepareResponse",
            ContextPrepareResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        schemas.setdefault(
            "MetricsResponse",
            MetricsResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        event_ingest = schema.get("paths", {}).get("/v1/events", {}).get("post")
        if isinstance(event_ingest, dict):
            event_ingest["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/EventBatchRequest"}
                    },
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "payload": {
                                    "description": "mneme.event_batch.v0 JSON payload",
                                    "type": "string",
                                },
                                "blob.<client_part_id>": {
                                    "description": "Binary blob parts referenced as multipart://<client_part_id>",
                                    "type": "string",
                                    "format": "binary",
                                },
                            },
                            "required": ["payload"],
                        }
                    },
                },
            }
        turn_complete = schema.get("paths", {}).get("/v1/turns/complete", {}).get("post")
        if isinstance(turn_complete, dict):
            turn_complete["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TurnCompleteRequest"}
                    }
                },
            }
            turn_complete.setdefault("responses", {})["200"] = {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TurnCompleteResponse"}
                    }
                },
            }
            for status_code in ("401", "403", "404", "409", "422"):
                turn_complete["responses"][status_code] = {
                    "description": "Error Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorEnvelope"}
                        }
                    },
                }
        context_prepare = schema.get("paths", {}).get("/v1/context/prepare", {}).get("post")
        if isinstance(context_prepare, dict):
            context_prepare["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ContextPrepareRequest"}
                    }
                },
            }
            context_prepare.setdefault("responses", {})["200"] = {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ContextPrepareResponse"}
                    }
                },
            }
            for status_code in ("401", "403", "404", "409", "422"):
                context_prepare["responses"][status_code] = {
                    "description": "Error Response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorEnvelope"}
                        }
                    },
                }
        for path, operations in schema.get("paths", {}).items():
            if path in {"/v1/health", "/openapi.json"}:
                continue
            for operation in operations.values():
                if isinstance(operation, dict):
                    operation.setdefault("security", [{"BearerAuth": []}])
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


def require_schema(payload: dict[str, Any], schema_key: str, *extra_schema_keys: str) -> None:
    accepted = list(SUPPORTED_SCHEMAS[schema_key])
    for extra_schema_key in extra_schema_keys:
        accepted.extend(SUPPORTED_SCHEMAS[extra_schema_key])
    if payload.get("schema_version") not in accepted:
        raise bad_request("Unsupported schema_version.", schema_version=payload.get("schema_version"))


def validate_provider_startup(
    settings: Settings,
    *,
    embedding_provider: EmbeddingProvider | None,
    reranker_provider: RerankerProvider | None,
    enrichment_provider: EnrichmentProvider | None,
) -> None:
    configured_providers = (
        ("embeddings", settings.embeddings, embedding_provider),
        ("reranker", settings.reranker, reranker_provider),
        ("llm_enrichment", settings.llm_enrichment, enrichment_provider),
    )
    for name, provider, injected in configured_providers:
        if (
            provider.enabled
            and provider.configured
            and provider.requires_api_key
            and not provider.api_key
            and injected is None
        ):
            raise RuntimeError(f"{name} provider requires an API key when enabled.")


def quality_missing_features(
    *,
    embeddings_available: bool,
    reranker_available: bool,
    enrichment_available: bool,
) -> list[str]:
    missing: list[str] = []
    if not embeddings_available:
        missing.append("embeddings")
    if not reranker_available:
        missing.append("reranker")
    if not enrichment_available:
        missing.append("llm_enrichment")
    return missing


def cost_mode_warnings_or_error(
    payload: dict[str, Any],
    settings: Settings,
    *,
    embeddings_available: bool,
    reranker_available: bool,
    enrichment_available: bool,
) -> list[dict[str, Any]]:
    requested = str(payload.get("cost_mode") or "STANDARD").strip().upper()
    if requested != "QUALITY":
        return []
    missing = quality_missing_features(
        embeddings_available=embeddings_available,
        reranker_available=reranker_available,
        enrichment_available=enrichment_available,
    )
    if not missing:
        return []
    details = {
        "requested_cost_mode": "QUALITY",
        "effective_cost_mode": "STANDARD" if embeddings_available else "MINIMAL",
        "missing_features": missing,
    }
    if settings.strict_cost_mode:
        raise provider_unavailable(
            "QUALITY cost mode requires unavailable providers.",
            **details,
        )
    return [
        {
            "code": "COST_MODE_DOWNGRADED",
            "message": "QUALITY cost mode downgraded because providers are unavailable.",
            "details": details,
        }
    ]


def model_payload(payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json", exclude_none=True)
    return payload


def validate_tool_request_schema(payload: dict[str, Any]) -> None:
    schema_version = payload.get("schema_version")
    if schema_version is None:
        return
    if schema_version not in SUPPORTED_SCHEMAS["tool_request"]:
        raise validation_error(
            "Unsupported tool request schema_version.",
            field="schema_version",
            supported_schema_versions=SUPPORTED_SCHEMAS["tool_request"],
            received=schema_version,
        )


def require_payload_str(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise validation_error(f"Missing required field {field}.", field=field)
    return value


def optional_payload_str(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise validation_error(f"{field} must be a non-empty string.", field=field)
    return value


def session_not_found_details(
    store: Store,
    session_id: str,
    project_isolation_keys: list[str] | None = None,
) -> dict[str, Any]:
    candidates = store.list_sessions(
        query=session_id,
        project_isolation_keys=project_isolation_keys,
        limit=5,
    )
    return {
        "session_id": session_id,
        "reason": "SESSION_ID_NOT_FOUND",
        "hint": "Do not guess Mneme session_id. Call resolve_session with project_path/thread_id/slug or list_sessions to find a valid session.",
        "discovery_tools": ["resolve_session", "list_sessions"],
        "candidate_sessions": candidates,
    }


def normalize_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    required = ["event_id", "session_id", "agent_id", "runtime", "role", "type", "timestamp", "content"]
    for field in required:
        if field not in raw_event:
            raise validation_error("Event missing required field.", field=field)
    event = dict(raw_event)
    event.setdefault("parent_event_ids", [])
    importance = str(event.get("importance") or "NORMAL").upper()
    if importance not in EVENT_IMPORTANCE_VALUES:
        raise validation_error("Unknown event importance.", field="importance")
    event["importance"] = importance
    event.setdefault("token_estimate", token_estimate(text_from_content(event["content"])))
    return event


def event_immutable_hash(event: dict[str, Any]) -> str:
    content = event.get("content", {})
    immutable = {
        "session_id": event.get("session_id"),
        "turn_id": event.get("turn_id"),
        "agent_id": event.get("agent_id"),
        "runtime": event.get("runtime"),
        "role": event.get("role"),
        "type": event.get("type"),
        "timestamp": event.get("timestamp"),
        "content_hash": content.get("hash") or sha256_text(text_from_content(content)),
        "tool_name": event.get("tool", {}).get("name"),
        "tool_call_id": event.get("tool", {}).get("call_id"),
        "parent_event_ids": event.get("parent_event_ids", []),
    }
    return sha256_text(canonical_json(immutable))


def apply_optional_enrichment(
    store: Store,
    enricher: EnrichmentProvider | None,
    event: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    if enricher is None:
        return state
    try:
        result = enricher.enrich(event, state)
    except Exception:
        result = EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")
    store.record_enrichment_metrics(
        event["session_id"],
        enrichment_calls=1,
        enrichment_failures=1 if result.degraded else 0,
    )
    if result.degraded or not result.updates:
        return state
    return apply_enrichment_updates(state, redact(result.updates))


def reindex_missing_embeddings(store: Store, embedding_index: EmbeddingIndex, settings: Settings) -> None:
    events = store.list_events_missing_embedding(embedding_index.model_id)
    if not events:
        return
    records_by_session: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        record = embedding_record_from_event(
            event,
            tool_output_compress_threshold_tokens=settings.tool_output_compress_threshold_tokens,
            tool_output_summary_tokens=settings.tool_output_summary_tokens,
        )
        if record is None:
            continue
        records_by_session.setdefault(str(record["session_id"]), []).append(record)
    for session_id, records in records_by_session.items():
        stats = embedding_index.index_events(records)
        store.record_embedding_metrics(
            session_id,
            embedding_batches=stats.embedding_batches,
            embedding_items=stats.embedding_items,
            embedding_input_chars=stats.embedding_input_chars,
            embedding_failures=stats.embedding_failures,
        )


def should_run_enrichment(
    settings: Settings,
    event: dict[str, Any],
    state: dict[str, Any],
    previous_segment: dict[str, Any] | None,
    segment: dict[str, Any] | None,
) -> bool:
    if event.get("type") != "USER_MESSAGE":
        return False
    every_n = int(settings.enricher_every_n_turns or 0)
    if every_n > 0 and int(state.get("turn_count") or 0) % every_n == 0:
        return True
    if not settings.enricher_on_segment_boundary or not previous_segment or not segment:
        return False
    return previous_segment.get("segment_id") != segment.get("segment_id")


CANONICAL_BUDGET_KEYS = {
    "headroom_ratio",
    "execution_state_ratio",
    "protected_tail_ratio",
    "retrieved_evidence_ratio",
    "hints_ratio",
}
_CANONICAL_BUDGET_DEFAULTS = {
    "headroom_ratio": 0.10,
    "execution_state_ratio": 0.12,
    "protected_tail_ratio": 0.28,
    "retrieved_evidence_ratio": 0.45,
    "hints_ratio": 0.05,
}


def _normalize_budget_split(
    payload: dict[str, Any],
    settings: Settings,
) -> tuple[dict[str, float], list[str]]:
    policy = payload.get("policy", {}) if isinstance(payload.get("policy", {}), dict) else {}
    split = policy.get("budget_split")
    warnings: list[str] = []

    if split is None:
        return dict(_CANONICAL_BUDGET_DEFAULTS), warnings
    if not isinstance(split, dict):
        raise validation_error("policy.budget_split must be an object.", field="policy.budget_split")
    supplied_defaults = {
        "headroom_ratio": 0.0,
        "execution_state_ratio": 0.0,
        "protected_tail_ratio": 0.0,
        "retrieved_evidence_ratio": 0.0,
        "hints_ratio": 0.0,
    }

    normalized = {str(key): value for key, value in split.items()}
    unknown = [key for key in normalized if key not in CANONICAL_BUDGET_KEYS]
    if unknown:
        raise validation_error(
            "budget_split contains unknown keys.",
            field="policy.budget_split",
            unknown_keys=sorted(unknown),
        )

    deprecated_headroom = policy.get("headroom_ratio")
    if "headroom_ratio" in normalized:
        try:
            split_headroom = float(normalized["headroom_ratio"])
        except (TypeError, ValueError) as exc:
            raise validation_error(
                "budget_split ratio values must be non-negative numbers.",
                field="policy.budget_split.headroom_ratio",
            ) from exc
        if deprecated_headroom is not None:
            try:
                deprecated_ratio = float(deprecated_headroom)
            except (TypeError, ValueError) as exc:
                raise validation_error(
                    "policy.headroom_ratio must be a non-negative number.",
                    field="policy.headroom_ratio",
                ) from exc
            if deprecated_ratio != split_headroom:
                warnings.append("DEPRECATED_FIELD_NORMALIZED")
    else:
        if deprecated_headroom is not None:
            warnings.append("DEPRECATED_FIELD_NORMALIZED")
            try:
                normalized["headroom_ratio"] = float(deprecated_headroom)
            except (TypeError, ValueError) as exc:
                raise validation_error(
                    "policy.headroom_ratio must be a non-negative number.",
                    field="policy.headroom_ratio",
                ) from exc

    resolved: dict[str, float] = {}
    for key in CANONICAL_BUDGET_KEYS:
        raw_value = normalized.get(key, supplied_defaults[key])
        if isinstance(raw_value, bool):
            raise validation_error(
                "budget_split ratio values must be non-negative numbers.",
                field=f"policy.budget_split.{key}",
            )
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise validation_error(
                "budget_split ratio values must be non-negative numbers.",
                field=f"policy.budget_split.{key}",
            ) from exc
        if value < 0:
            raise validation_error(
                "budget_split must be non-negative and sum to 1.0.",
                field="policy.budget_split",
            )
        resolved[key] = value

    if abs(sum(resolved.values()) - 1.0) > 0.01:
        raise validation_error(
            "budget_split must be non-negative and sum to 1.0 +/- 0.01.",
            field="policy.budget_split",
            sum=sum(resolved.values()),
        )

    return resolved, warnings


def validate_prepare(payload: dict[str, Any]) -> None:
    if payload.get("budget_tokens", 0) <= 0 or payload.get("budget_tokens", 0) > payload.get("context_window_tokens", 0):
        raise validation_error("budget_tokens must be greater than zero and within context_window_tokens.")
    messages = payload.get("request_messages")
    if not isinstance(messages, list) or not messages:
        raise validation_error("request_messages must be a non-empty list.")
    allowed_roles = {"SYSTEM", "DEVELOPER", "USER", "ASSISTANT", "TOOL"}
    allowed_part_types = {"text", "json", "image_ref", "bytes_ref", "tool_call", "tool_result"}
    for index, message in enumerate(messages):
        if message.get("schema_version") != "mneme.message.v0" or "role" not in message or "content" not in message:
            raise validation_error("Invalid mneme.message.v0 message.")
        role = str(message.get("role") or "").upper()
        if role not in allowed_roles:
            raise validation_error(
                "Invalid mneme.message.v0 role.",
                field=f"request_messages[{index}].role",
            )
        content = message.get("content")
        if isinstance(content, list):
            for part_index, part in enumerate(content):
                if not isinstance(part, dict) or part.get("type") not in allowed_part_types:
                    raise validation_error(
                        "Invalid mneme.message.v0 content part type.",
                        field=f"request_messages[{index}].content[{part_index}].type",
                    )
        elif not isinstance(content, str):
            raise validation_error(
                "mneme.message.v0 content must be a string or typed content parts.",
                field=f"request_messages[{index}].content",
            )
    policy = payload.get("policy", {}) if isinstance(payload.get("policy"), dict) else {}
    cost_mode = str(policy.get("cost_mode") or "STANDARD").upper()
    if policy.get("model_bound") is True and cost_mode in {"STANDARD", "QUALITY"}:
        raise validation_error(
            "CHAR_APPROXIMATE token estimates cannot be used for model-bound STANDARD or QUALITY context prepare.",
            reason="CHAR_APPROXIMATE_MODEL_BOUND_PREPARE",
            token_estimate_quality="CHAR_APPROXIMATE",
            tokenizer_source="char_4_fallback",
            requested_cost_mode=cost_mode,
            effective_cost_mode="MINIMAL",
        )
    split = policy.get("budget_split")
    if split is not None and not isinstance(split, dict):
        raise validation_error("policy.budget_split must be an object.", field="policy.budget_split")


def parse_int(payload: dict[str, Any], field: str, *, default: int, minimum: int, maximum: int) -> int:
    raw_value = payload.get(field, default)
    if isinstance(raw_value, bool):
        raise validation_error(f"{field} must be an integer.", field=field)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise validation_error(f"{field} must be an integer.", field=field) from exc
    if value < minimum or value > maximum:
        raise validation_error(f"{field} must be between {minimum} and {maximum}.", field=field)
    return value


def parse_optional_int(payload: dict[str, Any], field: str, *, minimum: int, maximum: int) -> int | None:
    if field not in payload or payload.get(field) is None:
        return None
    return parse_int(payload, field, default=minimum, minimum=minimum, maximum=maximum)


def discovery_page_size(payload: dict[str, Any], *, default: int, maximum: int) -> int:
    if "page_size" in payload and payload.get("page_size") is not None:
        return parse_int(payload, "page_size", default=default, minimum=1, maximum=maximum)
    return parse_int(payload, "limit", default=default, minimum=1, maximum=maximum)


def parse_page_token(payload: dict[str, Any]) -> str | None:
    token = payload.get("page_token")
    if token in (None, ""):
        return None
    if not isinstance(token, str) or not token.isdecimal():
        raise validation_error("page_token must be a non-negative integer cursor.", field="page_token")
    return token


def search_filters(payload: dict[str, Any]) -> dict[str, Any]:
    filters = payload.get("filters") or {}
    if not isinstance(filters, dict):
        raise validation_error("filters must be an object.", field="filters")
    event_types = filters.get("event_types")
    result: dict[str, Any] = {}
    if event_types is not None:
        if not isinstance(event_types, list) or any(not isinstance(item, str) or not item for item in event_types):
            raise validation_error("filters.event_types must be a list of non-empty strings.", field="filters.event_types")
        result["event_types"] = event_types
    after = filters.get("after")
    before = filters.get("before")
    if after is not None:
        if not isinstance(after, str) or not after:
            raise validation_error("filters.after must be an ISO timestamp string.", field="filters.after")
        result["after"] = after
    if before is not None:
        if not isinstance(before, str) or not before:
            raise validation_error("filters.before must be an ISO timestamp string.", field="filters.before")
        result["before"] = before
    return result


def parse_search_scope(payload: dict[str, Any]) -> str:
    scope = str(payload.get("scope") or "LINEAGE").strip().upper()
    if scope in {"SESSION", "LINEAGE", "PROJECT", "GLOBAL", "ALL"}:
        return "GLOBAL" if scope == "ALL" else scope
    raise validation_error("scope must be SESSION, LINEAGE, PROJECT, GLOBAL, or ALL.", field="scope")


def search_session_ids_for_scope(store: Store, session_id: str, scope: str) -> list[str] | None:
    if scope == "GLOBAL":
        return None
    if scope == "SESSION":
        return [session_id]
    if scope == "PROJECT":
        project_key = store.session_project_key(session_id)
        return store.session_ids_for_project(project_key) if project_key else [session_id]
    return store.lineage_session_ids(session_id)


def derive_query(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "USER":
            return str(message.get("content", ""))
    return str(messages[-1].get("content", "")) if messages else ""


def prepare_retrieval_query(
    messages: list[dict[str, Any]],
    execution_state: dict[str, Any],
    *,
    explicit_query: Any,
) -> tuple[str, list[str]]:
    if explicit_query:
        return str(explicit_query), ["policy.retrieval.query"]
    raw_query = derive_query(messages)
    classification = classify_intent(
        raw_query,
        active_entities=execution_state.get("active_entities") or [],
    )
    if classification["intent"] == "CONTINUATION":
        parts: list[str] = []
        sources: list[str] = []
        for field in ("goal", "current_step"):
            value = execution_state.get(field)
            if value:
                parts.append(str(value))
                sources.append(f"execution_state.{field}")
        active_entities = execution_state.get("active_entities")
        if isinstance(active_entities, list) and active_entities:
            parts.extend(str(entity) for entity in active_entities if entity)
            sources.append("execution_state.active_entities")
        last_tool_output = execution_state.get("last_tool_output_summary")
        if last_tool_output:
            parts.append(str(last_tool_output))
            sources.append("execution_state.last_tool_output_summary")
        if parts:
            return " ".join(parts), sources
    return raw_query, ["request_messages.latest_user"]


def approximate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    return sum(token_estimate(str(message.get("content", ""))) for message in messages)


def execution_state_context_block(state: dict[str, Any], *, budget_tokens: int) -> tuple[str, int, str]:
    variants = [
        ("FULL", execution_state_lines(state, decision_limit=5, include_tool_output=True)),
        ("COMPACT", execution_state_lines(state, decision_limit=3, include_tool_output=False)),
        ("MINIMAL", execution_state_lines(state, decision_limit=1, include_tool_output=False, minimal=True)),
    ]
    for compression, lines in variants:
        block = "\n".join(lines)
        if len(lines) == 1:
            return "", 0, "EMPTY"
        block_tokens = token_estimate(block)
        if block_tokens <= budget_tokens:
            return block, block_tokens, compression
    minimal = "\n".join(variants[-1][1])
    if token_estimate(minimal) <= budget_tokens:
        return minimal, token_estimate(minimal), "MINIMAL"
    truncated = truncate_to_token_budget(minimal, budget_tokens)
    if not truncated:
        return "", 0, "DROPPED_FOR_BUDGET"
    return truncated, token_estimate(truncated), "TRUNCATED"


def execution_state_lines(
    state: dict[str, Any],
    *,
    decision_limit: int,
    include_tool_output: bool,
    minimal: bool = False,
) -> list[str]:
    lines = ["[MNEME EXECUTION STATE]"]
    enrichment = state.get("enrichment") if isinstance(state.get("enrichment"), dict) else {}
    if state.get("goal"):
        lines.append(f"Goal: {context_line(state['goal'])}")
    if state.get("current_step"):
        lines.append(f"Current step: {context_line(state['current_step'])}")
    if enrichment.get("intent_label"):
        lines.append(f"Intent: {context_line(enrichment['intent_label'])}")
    topic_tags = enrichment.get("topic_tags") if isinstance(enrichment.get("topic_tags"), list) else []
    if topic_tags:
        lines.append(f"Topic tags: {', '.join(context_line(tag) for tag in topic_tags[:8])}")
    if enrichment.get("decision_summary"):
        lines.append(f"Decision summary: {context_line(enrichment['decision_summary'])}")
    if minimal:
        return lines
    if state.get("last_tool"):
        lines.append(f"Last tool: {context_line(state['last_tool'])}")
    if include_tool_output and state.get("last_tool_output_summary"):
        lines.append(f"Last tool output: {context_line(state['last_tool_output_summary'])}")
    decisions = [
        decision
        for decision in state.get("decision_stack", [])
        if isinstance(decision, dict) and (decision.get("decision") or decision.get("text"))
    ]
    if decisions:
        lines.append("Decisions:")
        for decision in decisions[-decision_limit:]:
            text = decision.get("decision") or decision.get("text")
            rationale = decision.get("rationale")
            suffix = f" | rationale: {context_line(rationale)}" if rationale else ""
            lines.append(f"- {context_line(text)}{suffix}")
    return lines


def truncate_to_token_budget(text: str, budget_tokens: int) -> str:
    if budget_tokens <= 0:
        return ""
    max_chars = max(0, budget_tokens * 4)
    if not max_chars:
        return ""
    return text[:max_chars].rstrip()


def protected_tail_messages(
    messages: list[dict[str, Any]],
    tail_budget_tokens: int,
    *,
    preserve_system_prompt: bool,
    latest_user_message_index: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    system_messages = []
    candidates = messages
    if preserve_system_prompt and messages and messages[0].get("role") == "SYSTEM":
        system_messages = [messages[0]]
        candidates = messages[1:]
    if latest_user_message_index is not None:
        if preserve_system_prompt and messages and messages[0].get("role") == "SYSTEM":
            latest_user_message_index -= 1
        if latest_user_message_index < 0 or latest_user_message_index >= len(candidates):
            latest_user_message_index = None
    if latest_user_message_index is None:
        kept_reversed: list[dict[str, Any]] = []
        used_tokens = 0
        for message in reversed(candidates):
            message_tokens = token_estimate(str(message.get("content", "")))
            if not kept_reversed or used_tokens + message_tokens <= tail_budget_tokens:
                kept_reversed.append(message)
                used_tokens += message_tokens
                continue
            break
        return system_messages + list(reversed(kept_reversed)), used_tokens

    preserved_index = latest_user_message_index
    selected_indices = {preserved_index}
    used_tokens = 0
    for index in range(len(candidates) - 1, -1, -1):
        if index == preserved_index:
            continue
        message_tokens = token_estimate(str(candidates[index].get("content", "")))
        if used_tokens + message_tokens <= tail_budget_tokens:
            selected_indices.add(index)
            used_tokens += message_tokens
            continue
        break
    kept_messages = [candidates[index] for index in sorted(selected_indices)]
    return system_messages + kept_messages, used_tokens


def latest_user_message_index(messages: list[dict[str, Any]]) -> int | None:
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "USER":
            return index
    return None


def pack_retrieved_events(
    events: list[dict[str, Any]],
    retrieved_budget_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    selected: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    used_tokens = 0
    for event in events:
        event_tokens = token_estimate(retrieved_event_wrapper(event))
        if event_tokens <= max(0, retrieved_budget_tokens - used_tokens):
            selected.append(event)
            used_tokens += event_tokens
            continue
        dropped.append({"event_id": event["event_id"], "reason": "RETRIEVED_CONTEXT_BUDGET_EXCEEDED"})
    return selected, dropped, used_tokens


def retrieved_event_line(event: dict[str, Any]) -> str:
    return f"- {event['event_id']}: {text_from_content(event.get('content', {}))}"


def retrieved_event_wrapper(event: dict[str, Any]) -> str:
    event_id = xml_escape(str(event.get("event_id") or ""))
    source_trust = xml_escape(event_source_trust(event))
    freshness = xml_escape(event_freshness(event))
    event_type = xml_escape(str(event.get("type") or ""))
    evidence_text = xml_escape(text_from_content(event.get("content", {})))
    return (
        f'<mneme_untrusted_evidence event_id="{event_id}" '
        f'source_trust="{source_trust}" freshness="{freshness}" event_type="{event_type}">'
        f"{evidence_text}"
        "</mneme_untrusted_evidence>"
    )


def event_source_trust(event: dict[str, Any]) -> str:
    privacy = event.get("privacy") if isinstance(event.get("privacy"), dict) else {}
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    raw_value = privacy.get("source_trust") or metadata.get("source_trust")
    if isinstance(raw_value, str) and raw_value.strip():
        return raw_value.strip().upper()
    event_type = str(event.get("type") or "").upper()
    if event_type in {"TOOL_OUTPUT", "COMMAND_OUTPUT", "EXTERNAL_MCP_CONTENT"}:
        return f"UNTRUSTED_{event_type}"
    return "UNKNOWN"


def event_freshness(event: dict[str, Any]) -> str:
    privacy = event.get("privacy") if isinstance(event.get("privacy"), dict) else {}
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    raw_freshness = event.get("freshness")
    if isinstance(raw_freshness, dict):
        raw_value = raw_freshness.get("value") or raw_freshness.get("status")
    else:
        raw_value = raw_freshness
    raw_value = raw_value or metadata.get("freshness") or privacy.get("freshness")
    if isinstance(raw_value, str):
        normalized = raw_value.strip().upper()
        if normalized in FRESHNESS_VALUES:
            return normalized
    return "RECENT"


def event_conflicting_event_ids(event: dict[str, Any]) -> list[str]:
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    freshness = event.get("freshness") if isinstance(event.get("freshness"), dict) else {}
    candidates = (
        metadata.get("conflicting_event_ids")
        or freshness.get("conflicting_event_ids")
        or metadata.get("freshness_conflicting_event_ids")
        or []
    )
    if not isinstance(candidates, list):
        return []
    return [str(item) for item in candidates if isinstance(item, str) and item]


def apply_freshness_conflicts_to_events(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    conflicting_ids: set[str] = set()
    for event in events:
        if event_freshness(event) == "CURRENT":
            conflicting_ids.update(event_conflicting_event_ids(event))
    if not conflicting_ids:
        return events, [], []
    selected: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    for event in events:
        event_id = str(event.get("event_id") or "")
        if event_id in conflicting_ids and event_freshness(event) != "CURRENT":
            dropped.append({"event_id": event_id, "reason": "FRESHNESS_CONFLICT"})
            continue
        selected.append(event)
    warnings = ["FRESHNESS_CONFLICT"] if dropped else []
    return selected, dropped, warnings


def apply_freshness_conflicts_to_results(
    results: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    conflicting_ids: set[str] = set()
    for result in results:
        if result.get("freshness") == "CURRENT":
            conflicting_ids.update(str(item) for item in result.get("conflicting_event_ids", []) if isinstance(item, str))
    if not conflicting_ids:
        return results, [], []
    selected: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    for result in results:
        event_id = str(result.get("event_id") or "")
        if event_id in conflicting_ids and result.get("freshness") != "CURRENT":
            dropped.append({"event_id": event_id, "reason": "FRESHNESS_CONFLICT"})
            continue
        selected.append(result)
    warnings = [{"code": "FRESHNESS_CONFLICT", "message": "Current adapter/source evidence explicitly conflicted with stored memory evidence."}] if dropped else []
    return selected, dropped, warnings


def xml_escape(value: str) -> str:
    return html.escape(value, quote=True)


def prepare_prompt_helper_blocks(
    store: Store,
    settings: Settings,
    session_id: str,
    *,
    include_helpers: bool,
) -> tuple[str, str, str]:
    if not include_helpers:
        return "", "", ""
    memory_hint = memory_access_hint_block(store, settings, session_id)
    goal_trail = goal_trail_context_block(store.get_recent_unique_goals(session_id, settings.goal_trail_size))
    checkpoint = checkpoint_context_block(store, settings, session_id)
    return memory_hint, goal_trail, checkpoint


def memory_access_hint_block(store: Store, settings: Settings, session_id: str) -> str:
    if not settings.memory_access_hint_enabled:
        return ""
    stats = store.session_stats(session_id)
    lines = [
        "[MNEME MEMORY ACCESS]",
        "Use Mneme memory tools as evidence when past context may matter.",
        "Start with list_segments or context_search; fetch_event only when a snippet is incomplete.",
        "Cite event ids from retrieved evidence instead of guessing or repeating prior work.",
    ]
    if stats["total_events"] > int(settings.protected_tail_turns or 0):
        lines.append(
            f"Memory stats: {stats['total_events']} events, {stats['total_segments']} segments; older context is outside the active tail."
        )
    return "\n".join(lines)


def goal_trail_context_block(goals: list[dict[str, Any]]) -> str:
    if not goals:
        return ""
    lines = ["[MNEME GOAL TRAIL]"]
    for index, item in enumerate(goals):
        timestamp = str(item.get("timestamp") or "")[:16].replace("T", " ")
        marker = " <- current" if index == len(goals) - 1 else ""
        lines.append(f"- {timestamp}: {context_line(item.get('goal') or '')}{marker}")
    return "\n".join(lines)


def checkpoint_context_block(store: Store, settings: Settings, session_id: str) -> str:
    threshold = int(settings.checkpoint_after_n_memory_calls or 0)
    if threshold <= 0:
        return ""
    consecutive = store.recent_memory_tool_count(session_id, settings.memory_tool_names)
    if consecutive < threshold:
        return ""
    state = store.execution_state_or_default(session_id)
    goals = store.get_recent_unique_goals(session_id, limit=5)
    current_goal = state.get("goal") or "<none>"
    prior_goal = ""
    if len(goals) >= 2:
        prior_goal = goals[-2].get("goal") or ""
    elif goals:
        prior_goal = goals[0].get("goal") or ""
    lines = [
        f"[MNEME CHECKPOINT] {consecutive} memory-tool calls happened before this prepare.",
        f"Current goal: {context_line(current_goal)}",
    ]
    if prior_goal and prior_goal != current_goal:
        lines.append(f"Previous goal: {context_line(prior_goal)}")
    lines.append("Continue the useful work, or call get_goal_history if the thread is unclear.")
    return "\n".join(lines)


def prepare_context_blocks(
    memory_hint_block: str,
    goal_trail_block: str,
    state_block: str,
    checkpoint_block: str,
    selected_events: list[dict[str, Any]],
) -> list[str]:
    blocks = []
    if memory_hint_block:
        blocks.append(memory_hint_block)
    if goal_trail_block:
        blocks.append(goal_trail_block)
    if state_block:
        blocks.append(state_block)
    if checkpoint_block:
        blocks.append(checkpoint_block)
    if selected_events:
        evidence = "\n".join(retrieved_event_wrapper(event) for event in selected_events)
        blocks.append(f"[MNEME RETRIEVED EVIDENCE]\n{evidence}".strip())
    return blocks


def context_blocks_tokens(context_blocks: list[str]) -> int:
    return token_estimate("\n\n".join(context_blocks).strip()) if context_blocks else 0


def projected_prepare_tokens(messages: list[dict[str, Any]], context_blocks: list[str]) -> int:
    return approximate_messages_tokens(messages) + context_blocks_tokens(context_blocks)


def cross_session_event_ids(session_id: str, events: list[dict[str, Any]]) -> list[str]:
    return [
        event["event_id"]
        for event in events
        if event.get("session_id") and event.get("session_id") != session_id
    ]


def context_line(value: Any) -> str:
    return " ".join(str(value).split())


def prepare_trace(
    trace_id: str,
    payload: dict[str, Any],
    selected_events: list[dict[str, Any]],
    start: float,
    *,
    selection_reason: str = "KEYWORD_RECENCY",
    execution_state_tokens: int = 0,
    protected_tail_tokens: int = 0,
    dropped_event_refs: list[dict[str, str]] | None = None,
    retrieved_tokens: int | None = None,
    degraded: bool = False,
    context_blocks: list[str] | None = None,
    execution_state_budget_tokens: int | None = None,
    protected_tail_budget_tokens: int | None = None,
    retrieved_evidence_budget_tokens: int | None = None,
    hints_budget_tokens: int = 0,
    minimum_headroom_tokens: int = 0,
    unused_context_slack_tokens: int = 0,
    memory_hint_tokens: int = 0,
    goal_trail_tokens: int = 0,
    checkpoint_tokens: int = 0,
    budget_split: dict[str, float] | None = None,
    cross_session_event_ids: list[str] | None = None,
    state_compression: str = "NONE",
    query_built_from: list[str] | None = None,
    trace_warnings: list[str] | None = None,
) -> dict[str, Any]:
    selected_ids = [event["event_id"] for event in selected_events]
    dropped = dropped_event_refs or []
    blocks = context_blocks or []
    return {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "CONTEXT_PREPARE",
        "session_id": payload["session_id"],
        "turn_id": payload.get("turn_id"),
        "request_id": payload.get("request_id"),
        "prepare_id": payload.get("prepare_id"),
        "policy": payload.get("policy", {}),
        "budget": {
            "budget_tokens": payload.get("budget_tokens"),
            "execution_state_tokens": execution_state_tokens,
            "protected_tail_tokens": protected_tail_tokens,
            "retrieved_tokens": retrieved_tokens if retrieved_tokens is not None else sum(token_estimate(text_from_content(event.get("content", {}))) for event in selected_events),
            "memory_hint_tokens": memory_hint_tokens,
            "goal_trail_tokens": goal_trail_tokens,
            "checkpoint_tokens": checkpoint_tokens,
            "minimum_headroom_tokens": minimum_headroom_tokens,
            "unused_context_slack_tokens": unused_context_slack_tokens,
            "execution_state_budget_tokens": execution_state_budget_tokens,
            "protected_tail_budget_tokens": protected_tail_budget_tokens,
            "retrieved_evidence_budget_tokens": retrieved_evidence_budget_tokens,
            "hints_budget_tokens": hints_budget_tokens,
            "budget_split": budget_split or {},
            "context_blocks": len(blocks),
            "state_compression": state_compression,
        },
        "retrieval": {
            "candidate_count": len(selected_events) + len(dropped),
            "selected_count": len(selected_events),
            "strategies": ["KEYWORD", "RECENCY"],
            "query_built_from": query_built_from or [],
            "degraded": degraded,
            "fallbacks": [],
        },
        "selected_events": [
            {
                "event_id": event["event_id"],
                "reason": selection_reason,
                "score": 1.0,
                "included_as": "RETRIEVED_EVIDENCE",
                "source_trust": event_source_trust(event),
                "freshness": event_freshness(event),
            }
            for event in selected_events
        ],
        "cross_session_event_ids": cross_session_event_ids or [],
        "dropped_events": dropped,
        "latency_ms": {"total": int((time.perf_counter() - start) * 1000), "retrieval": 0, "rerank": 0, "packing": 0},
        "privacy_actions": [],
        "audit_entries": [{"action": "MEMORY_READ", "tool": "context_prepare", "event_ids": selected_ids}],
        "warnings": trace_warnings or [],
        "execution_state_compression_level": state_compression,
    }


def session_resolution(session_id: str, source: str = "EXPLICIT_ARGUMENT") -> dict[str, str]:
    return {"session_id": session_id, "source": source}


def tool_response(
    data: dict[str, Any],
    *,
    trace_id: str | None = None,
    warnings: list[dict[str, Any]] | None = None,
    session_resolution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = {"ok": True, "data": data, "trace_id": trace_id, "warnings": warnings or []}
    if session_resolution is not None:
        response["session_resolution"] = session_resolution
    return response


def audit_memory_tool(
    store: Store,
    session_id: str,
    tool: str,
    event_ids: list[str],
    *,
    retrieval: dict[str, Any] | None = None,
    warnings: list[dict[str, Any]] | None = None,
    audit_mode: str = "FULL",
) -> str | None:
    tracker = getattr(store, "in_flight_reads", None)
    read_scope = tracker.enter(session_id) if tracker is not None else nullcontext()
    with read_scope:
        mode = audit_mode.strip().upper()
        if mode == "DISABLED_TEST_ONLY":
            return None
        trace_id = new_id("trace")
        trace = memory_read_trace(trace_id, session_id, tool, event_ids, retrieval=retrieval, warnings=warnings)
        store.put_trace(trace)
        store.add_audit(session_id, "MEMORY_READ", tool, event_ids, trace_id=trace_id)
        if mode == "TRACE_ONLY":
            return trace_id
        memory_event = {
            "schema_version": "mneme.event.v0",
            "event_id": new_id("memory-read"),
            "session_id": session_id,
            "turn_id": None,
            "agent_id": "mneme",
            "runtime": "MNEME",
            "role": "RUNTIME",
            "type": "MEMORY_READ",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content": {"format": "JSON", "text": canonical_json({"tool": tool, "event_ids": event_ids, "trace_id": trace_id})},
            "parent_event_ids": [],
            "token_estimate": 1,
        }
        store.put_event(memory_event, event_immutable_hash(memory_event), text_from_content(memory_event["content"]), is_memory_read=True)
        store.put_memory_read_evidence_edges(
            session_id=session_id,
            memory_read_event_id=memory_event["event_id"],
            evidence_event_ids=event_ids,
        )
        state = store.execution_state_or_default(session_id)
        state["last_tool"] = tool
        state["last_tool_output_summary"] = memory_read_summary(store, session_id, tool, event_ids)
        store.commit_execution_state(session_id, state)
        return trace_id


def memory_read_summary(store: Store, session_id: str, tool: str, event_ids: list[str]) -> str:
    top_event = store.get_event(session_id, event_ids[0]) if event_ids else None
    top_type = top_event.get("type") if top_event else None
    excerpt = ""
    if top_event:
        excerpt = first_sentence_or_tokens(redact(text_from_content(top_event.get("content", {}))), max_tokens=50)
    summary = (
        f"memory_read:{tool} results={len(event_ids)} "
        f"top_event={event_ids[0] if event_ids else 'null'} "
        f"top_type={top_type if top_type else 'null'} top_excerpt={excerpt}"
    ).strip()
    words = summary.split()
    if len(words) > 120:
        return " ".join(words[:120])
    return summary


def first_sentence_or_tokens(text: str, *, max_tokens: int) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""
    for delimiter in (". ", "? ", "! "):
        index = clean.find(delimiter)
        if index >= 0:
            return clean[: index + 1]
    return " ".join(clean.split()[:max_tokens])


def memory_read_trace(
    trace_id: str,
    session_id: str,
    tool: str,
    event_ids: list[str],
    *,
    retrieval: dict[str, Any] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    trace = {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "MEMORY_READ",
        "session_id": session_id,
        "turn_id": None,
        "tool": tool,
        "selected_event_ids": event_ids,
        "selected_events": [{"event_id": event_id, "reason": "DIRECT_MEMORY_TOOL", "score": 1.0, "included_as": "MEMORY_TOOL_RESULT"} for event_id in event_ids],
        "dropped_events": [],
        "latency_ms": {"total": 0, "retrieval": 0, "rerank": 0, "packing": 0},
        "privacy_actions": [],
        "audit_entries": [{"action": "MEMORY_READ", "tool": tool, "event_ids": event_ids}],
        "warnings": warnings or [],
    }
    if retrieval is not None:
        trace["retrieval"] = retrieval
    return trace


def maybe_trace_segment_drift(
    store: Store,
    event: dict[str, Any],
    classification: dict[str, Any],
    previous_segment: dict[str, Any] | None,
    segment: dict[str, Any] | None,
) -> None:
    if event.get("type") != "USER_MESSAGE":
        return
    if classification.get("intent") not in {INTENT_SWITCH, INTENT_NEW_TASK}:
        return
    if not previous_segment or not segment:
        return
    if previous_segment.get("segment_id") == segment.get("segment_id"):
        return
    store.put_trace(segment_drift_trace(new_id("trace"), event, classification, previous_segment, segment))


def segment_drift_trace(
    trace_id: str,
    event: dict[str, Any],
    classification: dict[str, Any],
    previous_segment: dict[str, Any],
    segment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "SEGMENT_DRIFT",
        "session_id": event["session_id"],
        "turn_id": event.get("turn_id"),
        "event_id": event["event_id"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "signals": classification.get("signals", {}),
        "decision": {
            "intent": classification.get("intent"),
            "drift_reason": segment.get("drift_reason"),
            "drift_score": (classification.get("signals") or {}).get("drift_score"),
            "drift_threshold": (classification.get("signals") or {}).get("drift_threshold"),
            "drift_components": (classification.get("signals") or {}).get("drift_components"),
            "drift_weights": (classification.get("signals") or {}).get("drift_weights"),
        },
        "segment_effect": {
            "closed_segment_id": previous_segment.get("segment_id"),
            "opened_segment_id": segment.get("segment_id"),
            "closed_event_count": previous_segment.get("event_count"),
            "opened_event_count": segment.get("event_count"),
        },
        "fallbacks": [],
        "warnings": [],
    }


def hybrid_context_search(
    store: Store,
    embedding_index: EmbeddingIndex | None,
    *,
    session_id: str,
    query: str,
    top_k: int,
    filters: dict[str, Any],
    scope: str = "LINEAGE",
    project_isolation_key: str | None = None,
    global_session_ids: list[str] | None = None,
    project_session_ids: list[str] | None = None,
    mode: str | None = None,
    reranker: RerankerProvider | None = None,
    reranker_top_k: int = 0,
    routing_mode_weights: Mapping[str, Mapping[str, float]],
    allow_recency_refill: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    strategies: list[str] = []
    fallbacks: list[str] = []
    warnings: list[dict[str, Any]] = []
    semantic_results: list[dict[str, Any]] = []
    degraded = False
    if mode is None:
        raise ValueError("mode must be provided")
    weights = routing_mode_weights[mode]
    if global_session_ids is None and scope == "GLOBAL" and project_isolation_key:
        global_session_ids = store.session_ids_for_project(project_isolation_key)
    scoped_session_ids = project_session_ids if scope == "PROJECT" else global_session_ids
    candidate_ids_by_source: dict[str, list[str]] = {"vector": [], "keyword": [], "graph": [], "refill": []}

    def event_for_result(result: dict[str, Any]) -> dict[str, Any] | None:
        if scope in {"GLOBAL", "PROJECT"}:
            return store.get_event_for_sessions(scoped_session_ids, result["event_id"])
        if scope == "SESSION":
            return store.get_event_for_sessions([session_id], result["event_id"])
        return store.get_event(session_id, result["event_id"])

    def attach_freshness(result: dict[str, Any]) -> None:
        event = event_for_result(result)
        if event is None:
            result["freshness"] = "UNKNOWN"
            return
        result["freshness"] = event_freshness(event)
        conflicting_ids = event_conflicting_event_ids(event)
        if conflicting_ids:
            result["conflicting_event_ids"] = conflicting_ids

    if embedding_index is not None:
        strategies.append("VECTOR")
        if scope in {"GLOBAL", "PROJECT"}:
            semantic = embedding_index.search_global_with_status(query, top_k=top_k * 2)
        else:
            semantic = embedding_index.search_with_status(query, session_id=session_id, top_k=top_k * 2)
        semantic_results = semantic.results
        if semantic.degraded:
            degraded = True
            reason = semantic.fallback_reason or "EMBEDDINGS_UNAVAILABLE"
            fallbacks.append(reason)
            warnings.append(
                {
                    "code": reason,
                    "message": "Embedding retrieval unavailable; keyword/recency fallback used.",
                }
            )

    strategies.extend(["KEYWORD", "RECENCY"])
    if scope in {"GLOBAL", "PROJECT"}:
        keyword_results = store.search_events_for_sessions(scoped_session_ids, query, top_k, **filters)
    elif scope == "SESSION":
        keyword_results = store.search_events_for_sessions([session_id], query, top_k, **filters)
    else:
        keyword_results = store.search_events(session_id, query, top_k, **filters)
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in semantic_results:
        if scope in {"GLOBAL", "PROJECT"}:
            event = store.get_event_for_sessions(scoped_session_ids, item["event_id"])
        elif scope == "SESSION":
            event = store.get_event_for_sessions([session_id], item["event_id"])
        else:
            event = store.get_event(session_id, item["event_id"])
        if not event or not event_matches_filters(event, filters):
            continue
        combined.append(
            {
                "event_id": event["event_id"],
                "session_id": event["session_id"],
                "turn_id": event.get("turn_id"),
                "type": event["type"],
                "timestamp": event["timestamp"],
                "score": item["score"],
                "snippet": text_from_content(event.get("content", {}))[:240],
                "reason": item.get("reason", "VECTOR_COSINE"),
            }
        )
        seen.add(event["event_id"])
        candidate_ids_by_source["vector"].append(str(event["event_id"]))

    for item in keyword_results:
        if item["event_id"] in seen:
            continue
        combined.append(item)
        seen.add(item["event_id"])
        candidate_ids_by_source["keyword"].append(str(item["event_id"]))

    graph_results = graph_dependency_results(store, session_id, combined, seen, filters, top_k)
    if graph_results:
        strategies.append("GRAPH_DEPENDENCY")
        combined.extend(graph_results)
        candidate_ids_by_source["graph"].extend(str(item["event_id"]) for item in graph_results)

    for item in combined:
        attach_freshness(item)

    combined, freshness_dropped, freshness_warnings = apply_freshness_conflicts_to_results(combined)
    warnings.extend(freshness_warnings)

    if allow_recency_refill and len(combined) < top_k:
        refill_results = recency_refill_results(
            store,
            session_id=session_id,
            scope=scope,
            scoped_session_ids=scoped_session_ids,
            filters=filters,
            seen_event_ids={str(item["event_id"]) for item in combined},
            limit=top_k - len(combined),
        )
        if refill_results:
            strategies.append("RECENCY_REFILL")
            warnings.append(
                {
                    "code": "RECENCY_REFILL_USED",
                    "message": "Context search filled remaining slots with recent scoped events.",
                }
            )
            for item in refill_results:
                attach_freshness(item)
            combined.extend(refill_results)
            candidate_ids_by_source["refill"].extend(str(item["event_id"]) for item in refill_results)

    apply_score_breakdowns(
        combined,
        mode=mode,
        scope=scope,
        query=query,
        routing_mode_weights=routing_mode_weights,
    )

    if reranker is not None and combined and query.strip():
        strategies.append("RERANK")
        documents = [str(item.get("snippet", "")) for item in combined]
        try:
            reranked = reranker.rerank(query, documents)
        except Exception:
            reranked = RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")
        if reranked.degraded or not reranked.scores:
            degraded = True
            reason = reranked.fallback_reason or "RERANKER_UNAVAILABLE"
            fallbacks.append(reason)
            warnings.append(
                {
                    "code": reason,
                    "message": "Reranker unavailable; original retrieval ranking used.",
                }
            )
            store.record_reranker_metrics(session_id, reranker_calls=1, reranker_failures=1)
        else:
            combined = reranked_results(combined, reranked.scores)
            if reranker_top_k and reranker_top_k > 0:
                combined = combined[:reranker_top_k]
            store.record_reranker_metrics(session_id, reranker_calls=1, reranker_failures=0)

    selected = combined[:top_k]
    candidate_count_raw = sum(len(ids) for ids in candidate_ids_by_source.values())
    candidate_count_unique = len({event_id for ids in candidate_ids_by_source.values() for event_id in ids})
    retrieval = {
        "candidate_count": candidate_count_raw,
        "candidate_count_raw": candidate_count_raw,
        "candidate_count_unique": candidate_count_unique,
        "source_counts": {source: len(ids) for source, ids in candidate_ids_by_source.items()},
        "candidate_ids_by_source": {source: ids[:20] for source, ids in candidate_ids_by_source.items()},
        "selected_count": len(selected),
        "strategies": strategies,
        "mode": mode,
        "weights": weights,
        "score_breakdowns": [item["score_breakdown"] for item in selected if "score_breakdown" in item],
        "dropped_events": freshness_dropped,
        "degraded": degraded,
        "fallbacks": fallbacks,
    }
    return selected, retrieval, warnings


def recency_refill_results(
    store: Store,
    *,
    session_id: str,
    scope: str,
    scoped_session_ids: list[str] | None,
    filters: dict[str, Any],
    seen_event_ids: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    if scope in {"GLOBAL", "PROJECT"}:
        candidates = store.search_events_for_sessions(scoped_session_ids, "", limit + len(seen_event_ids), **filters)
    elif scope == "SESSION":
        candidates = store.search_events_for_sessions([session_id], "", limit + len(seen_event_ids), **filters)
    else:
        candidates = store.search_events(session_id, "", limit + len(seen_event_ids), **filters)
    refill = []
    for item in candidates:
        event_id = str(item["event_id"])
        if event_id in seen_event_ids:
            continue
        copied = dict(item)
        copied["reason"] = "RECENCY_REFILL"
        copied["score"] = min(float(copied.get("score") or 0.0), 0.5)
        refill.append(copied)
        seen_event_ids.add(event_id)
        if len(refill) >= limit:
            break
    return refill


def search_mode(payload: dict[str, Any], *, settings: Settings) -> str:
    raw = payload.get("mode") or (payload.get("retrieval") or {}).get("mode") if isinstance(payload.get("retrieval"), dict) else payload.get("mode")
    if raw is None:
        return settings.routing_default_mode
    mode = str(raw).strip().lower()
    if mode not in settings.routing_mode_weights:
        raise validation_error("Unsupported retrieval mode.", field="mode")
    return mode


def infer_retrieval_mode(query: str) -> str:
    text = (query or "").lower()
    debug_keywords = (
        "error",
        "fail",
        "failed",
        "traceback",
        "exception",
        "debug",
        "broken",
        "crash",
        "bug",
        "ошибк",
        "не работает",
        "падает",
        "сломал",
    )
    reasoning_keywords = (
        "why",
        "how should",
        "what if",
        "should i",
        "best way",
        "tradeoff",
        "почему",
        "как лучше",
        "что если",
        "стоит ли",
    )
    factual_keywords = ("what is", "when ", "where ", "who ", "list ", "show me", "что такое", "когда", "где", "покажи")
    if any(keyword in text for keyword in debug_keywords):
        return "debugging"
    if any(keyword in text for keyword in reasoning_keywords) or len(text) > 500:
        return "reasoning"
    if any(keyword in text for keyword in factual_keywords):
        return "factual"
    return "general"


def apply_score_breakdowns(
    items: list[dict[str, Any]],
    *,
    mode: str,
    scope: str,
    query: str,
    routing_mode_weights: Mapping[str, Mapping[str, float]],
) -> None:
    if not items:
        return
    weights = routing_mode_weights[mode]
    query_term_count = len([term for term in query.split() if term.strip()]) or 1
    timestamps = [timestamp_seconds(str(item.get("timestamp") or "")) for item in items]
    oldest = min(timestamps)
    newest = max(timestamps)
    span = max(newest - oldest, 1.0)
    for item, timestamp in zip(items, timestamps, strict=False):
        components = {
            "semantic_similarity": normalized_semantic_similarity(item, query_term_count=query_term_count),
            "recency_score": 1.0 if newest == oldest else max(0.0, min(1.0, (timestamp - oldest) / span)),
            "dependency_score": float(item.get("dependency_score") or (1.0 if str(item.get("reason", "")).startswith("GRAPH_DEPENDENCY:") else 0.0)),
            "type_weight": EVENT_TYPE_WEIGHTS.get(str(item.get("type") or ""), 0.5),
        }
        final_score = (
            weights["semantic_similarity"] * components["semantic_similarity"]
            + weights["recency"] * components["recency_score"]
            + weights["dependency"] * components["dependency_score"]
            + weights["type_weight"] * components["type_weight"]
        )
        item["score"] = round(final_score, 6)
        item["score_breakdown"] = {
            "event_id": item["event_id"],
            "mode": mode,
            "final_score": item["score"],
            "components": components,
            "weights": weights,
            "scope_applied": scope,
            "embedding_model_id": None,
        }
    items.sort(key=lambda item: (float(item.get("score", 0.0)), str(item.get("timestamp") or ""), str(item.get("event_id") or "")), reverse=True)


def normalized_semantic_similarity(item: dict[str, Any], *, query_term_count: int) -> float:
    raw = float(item.get("score") or 0.0)
    reason = str(item.get("reason") or "")
    if reason.startswith("GRAPH_DEPENDENCY:"):
        return 0.0
    if reason == "KEYWORD_RECENCY":
        return min(1.0, raw / max(query_term_count, 1))
    if reason == "RECENCY_REFILL":
        return 0.0
    if raw <= 0:
        return 0.0
    return min(1.0, raw / 5.0 if raw > 1.0 else raw)


def timestamp_seconds(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def sorted_resolution_matches(
    matches: list[dict[str, Any]],
    *,
    project_path: str | None,
    thread_id: str | None,
    project_isolation_keys: list[str] | None,
) -> list[dict[str, Any]]:
    return sorted(
        matches,
        key=lambda item: (
            resolution_match_dimensions(
                item,
                project_path=project_path,
                thread_id=thread_id,
                project_isolation_keys=project_isolation_keys,
            ),
            int(item.get("created_at_ms") or 0),
            str(item.get("session_id") or ""),
        ),
        reverse=True,
    )


def best_guess_session_id_for_matches(
    matches: list[dict[str, Any]],
    *,
    project_path: str | None,
    thread_id: str | None,
    project_isolation_keys: list[str] | None,
) -> str | None:
    if len(matches) < 2:
        return matches[0]["session_id"] if matches else None
    top = resolution_match_dimensions(
        matches[0],
        project_path=project_path,
        thread_id=thread_id,
        project_isolation_keys=project_isolation_keys,
    )
    second = resolution_match_dimensions(
        matches[1],
        project_path=project_path,
        thread_id=thread_id,
        project_isolation_keys=project_isolation_keys,
    )
    if top > second:
        return str(matches[0]["session_id"])
    return None


def resolution_match_dimensions(
    item: dict[str, Any],
    *,
    project_path: str | None,
    thread_id: str | None,
    project_isolation_keys: list[str] | None,
) -> tuple[int, int, int]:
    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    exact_thread = int(
        bool(thread_id)
        and normalize_match_value(thread_id)
        in {
            normalize_match_value(str(item.get("session_id") or "")),
            normalize_match_value(str(metadata.get("thread_id") or "")),
        }
    )
    exact_project_path = int(
        bool(project_path)
        and normalize_match_value(project_path)
        in {
            normalize_match_value(str(item.get("project_id") or "")),
            normalize_match_value(str(metadata.get("cwd") or "")),
            normalize_match_value(str(metadata.get("transcript_path") or "")),
        }
    )
    exact_project_key = int(
        bool(project_isolation_keys)
        and str(item.get("project_isolation_key") or "") in set(project_isolation_keys or [])
    )
    return (exact_thread, exact_project_path, exact_project_key)


def reranked_results(items: list[dict[str, Any]], scores: list[dict[str, float | int]]) -> list[dict[str, Any]]:
    reranked: list[dict[str, Any]] = []
    used_indexes: set[int] = set()
    for score in scores:
        index = int(score["index"])
        if index < 0 or index >= len(items) or index in used_indexes:
            continue
        item = dict(items[index])
        item["score"] = float(score["score"])
        item["reason"] = "RERANKED"
        reranked.append(item)
        used_indexes.add(index)
    reranked.extend(item for index, item in enumerate(items) if index not in used_indexes)
    return reranked


def graph_dependency_results(
    store: Store,
    session_id: str,
    seeds: list[dict[str, Any]],
    seen: set[str],
    filters: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for seed in list(seeds):
        for edge in store.graph_edges_for_event(session_id, seed["event_id"]):
            neighbor_id = edge["target_event_id"] if edge["source_event_id"] == seed["event_id"] else edge["source_event_id"]
            if neighbor_id in seen:
                continue
            event = store.get_event(session_id, neighbor_id)
            if not event or not event_matches_filters(event, filters):
                continue
            if event.get("type") == "MEMORY_READ":
                continue
            results.append(
                {
                    "event_id": event["event_id"],
                    "turn_id": event.get("turn_id"),
                    "type": event["type"],
                    "timestamp": event["timestamp"],
                    "score": max(float(seed.get("score", 0.0)) * 0.5, 0.1),
                    "dependency_score": graph_edge_dependency_score(edge["edge_type"]),
                    "snippet": text_from_content(event.get("content", {}))[:240],
                    "reason": f"GRAPH_DEPENDENCY:{edge['edge_type']}",
                }
            )
            seen.add(neighbor_id)
            if len(seeds) + len(results) >= top_k:
                return results
    return results


def graph_edge_dependency_score(edge_type: str) -> float:
    return {
        "TOOL_RESULT": 1.0,
        "TOOL_INPUT": 1.0,
        "PARENT_CHILD": 0.9,
        "DECISION_FOLLOWS": 0.8,
        "MEMORY_READ_EVIDENCE": 0.8,
        "SEGMENT_ANCHOR": 0.7,
        "SEGMENT_MEMBER": 0.5,
        "FOLLOWS": 0.2,
    }.get(edge_type, 0.5)


def event_matches_filters(event: dict[str, Any], filters: dict[str, Any]) -> bool:
    event_types = filters.get("event_types")
    if event_types and event.get("type") not in event_types:
        return False
    after = filters.get("after")
    if after is not None and event.get("timestamp", "") < after:
        return False
    before = filters.get("before")
    if before is not None and event.get("timestamp", "") > before:
        return False
    return True


def last_assistant_entities(store: Store, session_id: str) -> list[str]:
    for event in reversed(store.recent_events(session_id, 20)):
        if event.get("type") == "ASSISTANT_MESSAGE":
            return extract_entities(text_from_content(event.get("content", {})))
    return []


def pack_events_under_token_limit(events: list[dict[str, Any]], max_tokens: int | None) -> tuple[list[dict[str, Any]], bool]:
    if max_tokens is None:
        return events, False
    packed: list[dict[str, Any]] = []
    used_tokens = 0
    truncated = False
    for event in reversed(events):
        event_tokens = token_estimate(text_from_content(event.get("content", {}))[:240])
        if used_tokens + event_tokens > max_tokens:
            truncated = True
            break
        packed.append(event)
        used_tokens += event_tokens
    return list(reversed(packed)), truncated


def summarize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event["event_id"],
            "turn_id": event.get("turn_id"),
            "type": event["type"],
            "timestamp": event["timestamp"],
            "snippet": text_from_content(event.get("content", {}))[:240],
        }
        for event in events
    ]


def event_for_fetch(
    store: Store,
    session_id: str,
    event: dict[str, Any],
    *,
    full: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    response_event = dict(event)
    content = dict(response_event.get("content") or {})
    text = text_from_content(content)
    original_chars = len(text)
    truncated = False
    if not full and original_chars > 4000 and content.get("format") != "BYTES_REF":
        content["text"] = text[:4000]
        response_event["content"] = content
        truncated = True
    segment_id = None
    metadata = response_event.get("metadata")
    if isinstance(metadata, dict):
        segment_id = metadata.get("mneme_segment_id")
    if not segment_id:
        segment_id = store.segment_id_for_event(session_id, event["event_id"])
    return response_event, {
        "segment_id": segment_id,
        "token_estimate": int(event.get("token_estimate") or token_estimate(text)),
        "truncated": truncated,
        "original_chars": original_chars,
    }


def graph_neighbors_for_expand(store: Store, session_id: str, event: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    event_id = str(event["event_id"])
    graph_edges = store.graph_edges_for_event(session_id, event_id)
    if graph_edges:
        neighbors = []
        for graph_edge in graph_edges:
            neighbor_id = (
                graph_edge["target_event_id"]
                if graph_edge["source_event_id"] == event_id
                else graph_edge["source_event_id"]
            )
            neighbor_event = store.get_event(session_id, str(neighbor_id)) or {}
            neighbors.append(
                {
                    "event_id": str(neighbor_id),
                    "edge": str(graph_edge["edge_type"]),
                    "weight": float(graph_edge.get("weight") or 0.0),
                    "timestamp_sort": timestamp_sort_value(neighbor_event.get("timestamp")),
                }
            )
        return sort_graph_neighbors(neighbors, mode)
    neighbors = []
    for parent_id in event.get("parent_event_ids", []):
        if isinstance(parent_id, str):
            parent_event = store.get_event(session_id, parent_id) or {}
            neighbors.append(
                {
                    "event_id": parent_id,
                    "edge": "PARENT",
                    "weight": 1.0,
                    "timestamp_sort": timestamp_sort_value(parent_event.get("timestamp")),
                }
            )
    for child in store.child_events(session_id, event_id):
        neighbors.append(
            {
                "event_id": str(child["event_id"]),
                "edge": "CHILD",
                "weight": 1.0,
                "timestamp_sort": timestamp_sort_value(child.get("timestamp")),
            }
        )
    return sort_graph_neighbors(neighbors, mode)


def sort_graph_neighbors(neighbors: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    mode = mode.upper()
    if mode == "TOOL_CHAIN":
        allowed = {"TOOL_RESULT", "TOOL_INPUT", "PARENT_CHILD", "FOLLOWS", "PARENT", "CHILD", "DECISION_FOLLOWS"}
        precedence = {
            "TOOL_RESULT": 0,
            "TOOL_INPUT": 1,
            "PARENT_CHILD": 2,
            "PARENT": 2,
            "CHILD": 2,
            "FOLLOWS": 2,
            "DECISION_FOLLOWS": 3,
        }
        filtered = [neighbor for neighbor in neighbors if neighbor["edge"] in allowed]
        return sorted(filtered, key=lambda item: (precedence.get(str(item["edge"]), 99), str(item["event_id"])))
    if mode == "CAUSAL":
        allowed = {"PARENT_CHILD", "FOLLOWS", "PARENT", "CHILD", "DECISION_FOLLOWS", "TOOL_RESULT", "TOOL_INPUT"}
        filtered = [neighbor for neighbor in neighbors if neighbor["edge"] in allowed]
        return sorted(
            filtered,
            key=lambda item: (-float(item.get("weight") or 0.0), -float(item.get("timestamp_sort") or 0.0), str(item["event_id"])),
        )
    return sorted(neighbors, key=lambda item: (str(item["edge"]), str(item["event_id"])))


def timestamp_sort_value(timestamp: Any) -> float:
    try:
        return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def expand_graph(
    store: Store,
    session_id: str,
    seed_id: str,
    mode: str,
    depth: int,
    max_events: int,
    *,
    importance_depth_decay: float,
    max_traversal_steps: int,
    max_frontier_size: int,
    max_branching_factor: int,
) -> dict[str, Any]:
    seen: set[str] = set()
    queue: list[tuple[str, str, int]] = [(seed_id, "SEED", 0)]
    output: list[dict[str, Any]] = []
    truncation_reason = None
    truncation_details: dict[str, Any] = {}
    visited_count = 0
    while queue:
        if len(output) >= max_events:
            truncation_reason = "MAX_EVENTS"
            truncation_details = {"dropped_count": len(queue), "frontier_queued": len(queue)}
            break
        event_id, edge, distance = queue.pop(0)
        if event_id in seen:
            continue
        event = store.get_event(session_id, event_id)
        if not event:
            continue
        if visited_count >= max_traversal_steps:
            truncation_reason = "MAX_TRAVERSAL_STEPS"
            truncation_details = {"limit": "max_traversal_steps", "count": max_traversal_steps}
            break
        visited_count += 1
        seen.add(event_id)
        if event.get("type") == "MEMORY_READ":
            continue
        importance_boost = round(float(importance_depth_decay) ** int(distance), 6)
        output.append(
            {
                "event_id": event_id,
                "type": event["type"],
                "edge": edge,
                "depth": distance,
                "importance_boost": importance_boost,
            }
        )
        neighbors = graph_neighbors_for_expand(store, session_id, event, mode)
        if distance >= depth:
            if any(str(neighbor["event_id"]) not in seen for neighbor in neighbors):
                truncation_reason = truncation_reason or "DEPTH_LIMIT"
            continue
        expansion_neighbors = [neighbor for neighbor in neighbors if str(neighbor["event_id"]) not in seen]
        if len(expansion_neighbors) > max_branching_factor:
            expansion_neighbors = expansion_neighbors[:max_branching_factor]
            truncation_reason = truncation_reason or "MAX_BRANCHING_FACTOR"
            truncation_details = {"limit": "max_branching_factor", "count": max_branching_factor}
        for neighbor in expansion_neighbors:
            neighbor_id = str(neighbor["event_id"])
            neighbor_edge = str(neighbor["edge"])
            if neighbor_id not in seen:
                queue.append((neighbor_id, neighbor_edge, distance + 1))
                if len(queue) > max_frontier_size:
                    del queue[max_frontier_size:]
                    truncation_reason = truncation_reason or "MAX_FRONTIER_SIZE"
                    truncation_details = {"limit": "max_frontier_size", "count": max_frontier_size}
                    break
    warnings = []
    if truncation_reason == "MAX_EVENTS":
        warnings.append(
            {
                "code": "GRAPH_TRAVERSAL_LIMIT_REACHED",
                "message": "Graph expansion hit max_events before traversal completed.",
            }
        )
        warnings.append(
            {
                "code": "RESULT_TRUNCATED",
                "message": "Graph expansion hit max_events before traversal completed.",
                "details": truncation_details,
            }
        )
    elif truncation_reason in {"MAX_TRAVERSAL_STEPS", "MAX_FRONTIER_SIZE", "MAX_BRANCHING_FACTOR"}:
        warnings.append(
            {
                "code": "TRAVERSAL_LIMIT_REACHED",
                "message": "Graph expansion stopped at a configured traversal limit.",
                "details": truncation_details,
            }
        )
    elif truncation_reason == "DEPTH_LIMIT":
        warnings.append(
            {
                "code": "GRAPH_DEPTH_LIMIT_REACHED",
                "message": "Graph expansion stopped at the requested depth before all neighbors were visited.",
            }
        )
    return {
        "events": output,
        "truncated": truncation_reason is not None,
        "truncation_reason": truncation_reason,
        "dropped_count": int(truncation_details.get("dropped_count") or 0),
        "frontier_summary": {
            "queued": int(truncation_details.get("frontier_queued") or 0),
            "visited": visited_count,
        },
        "warnings": warnings,
    }


def expand_temporal(store: Store, session_id: str, seed_id: str, max_events: int) -> dict[str, Any]:
    events = sorted(
        store.list_events(session_id),
        key=lambda item: (str(item.get("timestamp") or ""), str(item.get("event_id") or "")),
    )
    seed_index = next((index for index, event in enumerate(events) if event.get("event_id") == seed_id), None)
    if seed_index is None:
        return {
            "events": [],
            "truncated": False,
            "truncation_reason": None,
            "dropped_count": 0,
            "frontier_summary": {"queued": 0, "visited": 0},
            "warnings": [],
        }
    seed = events[seed_index]
    output = [
        {
            "event_id": str(seed["event_id"]),
            "type": seed["type"],
            "edge": "SEED",
            "depth": 0,
            "importance_boost": 1.0,
        }
    ]
    candidates: list[tuple[dict[str, Any], str, int]] = []
    for distance, event in enumerate(reversed(events[:seed_index]), start=1):
        candidates.append((event, "TEMPORAL_PREVIOUS", distance))
    for distance, event in enumerate(events[seed_index + 1 :], start=1):
        candidates.append((event, "TEMPORAL_NEXT", distance))
    for event, edge, distance in candidates[: max(0, max_events - 1)]:
        output.append(
            {
                "event_id": str(event["event_id"]),
                "type": event["type"],
                "edge": edge,
                "depth": distance,
                "importance_boost": 1.0,
            }
        )
    dropped_count = max(0, len(candidates) - max(0, max_events - 1))
    warnings = []
    if dropped_count:
        warnings.append(
            {
                "code": "RESULT_TRUNCATED",
                "message": "Temporal expansion hit max_events before all neighbors were returned.",
                "details": {"dropped_count": dropped_count, "frontier_queued": dropped_count},
            }
        )
    return {
        "events": output[:max_events],
        "truncated": dropped_count > 0,
        "truncation_reason": "MAX_EVENTS" if dropped_count else None,
        "dropped_count": dropped_count,
        "frontier_summary": {"queued": dropped_count, "visited": len(output[:max_events])},
        "warnings": warnings,
    }
