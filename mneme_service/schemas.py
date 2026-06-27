from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FlexiblePayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class ErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ok": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request.",
                        "retryable": False,
                        "details": {"field": "session_id"},
                        "trace_id": None,
                        "request_id": None,
                    },
                    "warnings": [],
                }
            ]
        }
    )

    ok: Literal[False] = False
    error: ErrorBody
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class SessionResolution(BaseModel):
    session_id: str
    source: Literal["EXPLICIT_ARGUMENT", "TRUSTED_DEFAULT", "HOST_INJECTED", "RESOLVED_BY_TOOL"]


class HealthResponse(BaseModel):
    status: str
    service: str
    api_version: str
    mneme_contract_version: str
    schema_versions: list[str]


class ToolResponseEnvelope(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ok": True,
                    "data": {"results": []},
                    "trace_id": "trace-example",
                    "session_resolution": {
                        "session_id": "session-example",
                        "source": "EXPLICIT_ARGUMENT",
                    },
                    "warnings": [],
                }
            ]
        }
    )

    ok: Literal[True] = True
    data: dict[str, Any]
    trace_id: str | None = None
    session_resolution: SessionResolution | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class ToolRequestPayload(FlexiblePayload):
    pass


class SessionStartRequest(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.session_start.v0",
                    "session_id": "session-example",
                    "agent_id": "agent-1",
                    "runtime": "GENERIC_AGENT",
                    "project_id": "project-1",
                    "privacy": {"project_isolation_key": "project-1"},
                    "metadata": {"cwd": "/repo"},
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str | None = None
    agent_id: str | None = None
    runtime: str | None = None
    project_id: str | None = None
    privacy: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class SessionStartResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "session-example",
                    "created": True,
                    "status": "ACTIVE",
                    "accepted_schema_version": "mneme.session_start.v0",
                    "session_state": {},
                    "warnings": [],
                }
            ]
        }
    )

    session_id: str
    created: bool
    status: str
    accepted_schema_version: str
    session_state: dict[str, Any]
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class SessionSummaryResponse(BaseModel):
    session_id: str
    agent_id: str | None = None
    runtime: str | None = None
    project_id: str | None = None
    project_isolation_key: str | None = None
    status: str
    started_at: str | None = None
    ended_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    event_count: int
    turn_count: int
    segment_count: int
    blob_count: int
    latest_event_timestamp: str | None = None
    latest_event_preview: dict[str, Any] | None = None
    session: dict[str, Any]


class SessionCloseResponse(BaseModel):
    session_id: str
    status: Literal["ENDED"] = "ENDED"
    closed: bool
    ended_at: str
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class ExecutionStateUpdateRequest(FlexiblePayload):
    schema_version: str | None = None
    mode: str | None = None
    state: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None


class ExecutionStateUpdateResponse(BaseModel):
    schema_version: Literal["mneme.execution_state_update_result.v0"] = "mneme.execution_state_update_result.v0"
    session_id: str
    updated: bool
    state: dict[str, Any]
    history_entry: dict[str, Any]


class SegmentStartRequest(FlexiblePayload):
    schema_version: str | None = None
    session_id: str | None = None
    segment_id: str | None = None
    title: str | None = None
    summary: str | None = None
    anchor_event_ids: list[str] | None = None
    provenance: dict[str, Any] | None = None


class SegmentCloseRequest(FlexiblePayload):
    schema_version: str | None = None
    session_id: str | None = None
    closed_at: str | None = None
    summary: str | None = None
    outcome: str | None = None
    anchor_event_ids: list[str] | None = None
    provenance: dict[str, Any] | None = None


class SegmentResponse(BaseModel):
    segment: dict[str, Any]


class SegmentListResponse(BaseModel):
    segments: list[dict[str, Any]]
    next_page_token: str | None = None


class SegmentEventsResponse(BaseModel):
    events: list[dict[str, Any]]
    next_page_token: str | None = None


class MessageContentPart(FlexiblePayload):
    type: Literal["text", "json", "image_ref", "bytes_ref", "tool_call", "tool_result"]
    text: str | None = None
    uri: str | None = None
    media_type: str | None = None
    data: Any | None = None


class Message(FlexiblePayload):
    schema_version: Literal["mneme.message.v0"]
    role: Literal["SYSTEM", "DEVELOPER", "USER", "ASSISTANT", "TOOL"]
    content: str | list[MessageContentPart]
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetentionCleanupRequest(FlexiblePayload):
    schema_version: str | None = None
    dry_run: bool | None = None
    force_active_cleanup: bool | None = None


class RetentionCleanupResponse(BaseModel):
    schema_version: Literal["mneme.retention_cleanup_result.v0"] = "mneme.retention_cleanup_result.v0"
    session_id: str
    status: str
    cutoff_timestamp: str
    candidate_counts: dict[str, int]
    deleted_counts: dict[str, int]
    orphan_counts: dict[str, int]
    dry_run: bool
    force_active_cleanup: bool
    active_session_skipped: bool
    skipped_active_session: bool
    events_deleted: int = 0
    state_history_deleted: int = 0
    graph_edges_deleted: int = 0
    blobs_deleted: int = 0
    blobs_orphaned: int = 0
    in_flight_reads_blocked: int = 0
    warnings: list[str] = Field(default_factory=list)


class EventBatchRequest(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.event_batch.v0",
                    "session_id": "session-example",
                    "events": [
                        {
                            "schema_version": "mneme.event.v0",
                            "event_id": "event-example",
                            "session_id": "session-example",
                            "turn_id": "turn-1",
                            "agent_id": "agent-1",
                            "runtime": "GENERIC_AGENT",
                            "role": "USER",
                            "type": "USER_MESSAGE",
                            "timestamp": "2026-06-09T12:00:00Z",
                            "content": {"format": "TEXT", "text": "Continue."},
                            "parent_event_ids": [],
                        }
                    ],
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str | None = None
    events: list[dict[str, Any]] | None = None


class EventBatchResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "session-example",
                    "accepted": 1,
                    "duplicates": 0,
                    "rejected": [],
                    "stored_event_ids": ["event-example"],
                    "blob_refs": [],
                }
            ]
        }
    )

    session_id: str
    accepted: int
    duplicates: int
    rejected: list[dict[str, Any]]
    stored_event_ids: list[str]
    blob_refs: list[dict[str, Any]] = Field(default_factory=list)


class BlobBytesRef(BaseModel):
    format: Literal["BYTES_REF"] = "BYTES_REF"
    uri: str
    hash: str
    size_bytes: int
    media_type: str
    storage_owner: Literal["SERVER"] = "SERVER"


class BlobRetention(BaseModel):
    delete_with_session: bool = True
    expires_at: str | None = None


class BlobRecordResponse(BaseModel):
    schema_version: Literal["mneme.blob.v0"] = "mneme.blob.v0"
    blob_id: str
    uri: str
    owner: Literal["SERVER"] = "SERVER"
    session_id: str
    project_isolation_key: str
    hash: str
    size_bytes: int
    media_type: str
    created_at: str
    ref_count: int
    retention: BlobRetention
    metadata: dict[str, Any] = Field(default_factory=dict)
    bytes_ref: BlobBytesRef


class BlobDeleteResponse(BaseModel):
    blob_id: str
    deleted: bool


class BlobGcRequest(FlexiblePayload):
    scope: str | None = None
    project_isolation_key: str | None = None
    session_id: str | None = None
    dry_run: bool = True


class BlobGcResponse(BaseModel):
    candidate_count: int
    deleted_count: int
    skipped_count: int
    dry_run: bool
    warnings: list[str] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    text: str


class TurnCompleteRequest(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.turn.v0",
                    "session_id": "session-example",
                    "turn_id": "turn-1",
                    "status": "COMPLETED",
                    "started_at": "2026-06-09T12:00:00Z",
                    "completed_at": "2026-06-09T12:00:45Z",
                    "event_ids": ["event-example"],
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str | None = None
    turn_id: str | None = None
    turn_sequence: int | None = None
    agent_id: str | None = None
    runtime: str | None = None
    status: Literal["STARTED", "COMPLETED", "FAILED", "INTERRUPTED", "CANCELLED"] | None = None
    started_at: str | None = None
    completed_at: str | None = None
    event_ids: list[str] | None = None
    prepare_ids: list[str] | None = None
    trace_ids: list[str] | None = None
    usage: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class TurnCompleteResponse(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.turn_complete_result.v0",
                    "session_id": "session-example",
                    "turn_id": "turn-1",
                    "status": "COMPLETED",
                    "recorded": True,
                    "warnings": [],
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str
    turn_id: str
    status: str
    recorded: bool | None = None


class ContextPrepareRequest(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.context_prepare_request.v0",
                    "session_id": "session-example",
                    "messages": [{"role": "USER", "content": "What changed?"}],
                    "budget": {"max_tokens": 4096},
                    "budget_split": {
                        "execution_state_ratio": 0.15,
                        "retrieved_evidence_ratio": 0.45,
                        "protected_tail_ratio": 0.30,
                        "headroom_ratio": 0.10,
                    },
                    "retrieval": {"query": "recent changes", "top_k": 5},
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str | None = None
    messages: list[dict[str, Any]] | None = None
    budget: dict[str, Any] | None = None
    budget_split: dict[str, Any] | None = None
    retrieval: dict[str, Any] | None = None


class ContextPrepareResponse(FlexiblePayload):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "mneme.context_prepare_result.v0",
                    "session_id": "session-example",
                    "messages": [],
                    "trace_id": "trace-example",
                    "warnings": [],
                }
            ]
        },
    )

    schema_version: str | None = None
    session_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class TraceResponse(FlexiblePayload):
    schema_version: Literal["mneme.trace.v0"] = "mneme.trace.v0"
    trace_id: str
    session_id: str
    trace_type: str
    created_at_ms: int | None = None


class CostReportResponse(FlexiblePayload):
    schema_version: Literal["mneme.cost_report.v0"] = "mneme.cost_report.v0"
    session_id: str
    period: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    events_ingested: int
    prepare_calls: int
    embedding_batches: int = 0
    reranker_calls: int = 0
    llm_enrichment_calls: int = 0
    estimated_cost: dict[str, Any] | None = None
    baseline: dict[str, Any] = Field(default_factory=dict)
    provider_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class ReindexRequest(FlexiblePayload):
    scope: str | None = None
    project_isolation_key: str | None = None
    session_id: str | None = None
    statuses: list[str] | None = None
    force: bool = False
    max_job_events: int | None = None


class ReindexCancelRequest(FlexiblePayload):
    reason: str | None = None


class ReindexJobProgress(BaseModel):
    candidate_count: int
    processed_count: int
    failed_count: int


class ReindexJobResponse(BaseModel):
    schema_version: Literal["mneme.reindex_job.v0"] = "mneme.reindex_job.v0"
    job_id: str
    scope: Literal["ALL", "PROJECT", "SESSION"]
    project_isolation_key: str | None = None
    session_id: str | None = None
    statuses: list[str]
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "WAITING_FOR_PROVIDER"]
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    progress: ReindexJobProgress
    error: dict[str, Any] | None = None


class SessionReadinessRequest(FlexiblePayload):
    session_id: str | None = None
    query: str | None = None
    scope: str | None = None
    top_k: int | None = None
    require_evidence: bool | None = None
    filters: dict[str, Any] | None = None


class ProviderCapability(BaseModel):
    enabled: bool
    configured: bool
    available: bool
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key_configured: bool
    last_health: str | dict[str, Any]


IntegrationLevel = Literal[
    "TOOLS_ONLY",
    "EVENT_INGEST",
    "PREPARE_INPUT",
    "CONTEXT_ENGINE",
    "COMPACTION_OWNER",
    "FULL_RUNTIME",
]


class AdapterIntegrationClaim(BaseModel):
    level: IntegrationLevel
    host_lifecycle: list[str] = Field(default_factory=list)
    context_prepare: str
    writes_enabled_by_default: bool


class CapabilitiesIntegrationDepth(BaseModel):
    max_supported: IntegrationLevel
    supported_levels: list[IntegrationLevel]
    unsupported_or_future: list[IntegrationLevel]
    supports_prepare_input: bool
    supports_context_engine: bool
    supports_compaction_owner: bool
    supports_full_runtime: bool
    adapter_claims: dict[str, AdapterIntegrationClaim]


class CapabilitiesLimits(BaseModel):
    max_batch_events: int
    max_event_content_bytes: int
    max_blob_bytes: int
    max_session_id_length: int
    max_batch_total_blob_bytes: int
    max_multipart_metadata_overhead_bytes: int
    max_multipart_transaction_bytes: int
    max_export_blob_inline_bytes: int
    max_export_session_memory_bytes: int
    top_k: int
    top_k_max: int
    page_size_default: int
    page_size_max: int
    expand_context_depth_default: int
    expand_context_depth_max: int
    expand_context_max_events_default: int
    expand_context_max_events_max: int
    max_latency_ms_default: int
    max_parent_event_ids: int
    idempotency_key_min_retention_seconds: int
    graph_importance_depth_decay: float


class CapabilitiesTokenizer(BaseModel):
    tokenizer_id: str
    token_estimate_quality: str


class CapabilitiesStorage(BaseModel):
    sqlite_wal: bool
    blob_driver: str
    schema_version: int
    migration_status: str
    vector_acceleration: str


class DeltaExtractionCapability(BaseModel):
    enabled: bool
    schema_version: Literal["mneme.entity_modifier.v0"]
    sources: list[Literal["DETERMINISTIC_PATTERN", "ADAPTER_SIGNAL", "PROVIDER_GUARDED"]]
    automatic_update_scope: list[Literal["execution_state.active_entities"]]
    provider_guarded_enabled: bool
    provider_guarded_policy: str
    conflict_order: list[Literal["REPLACE", "REMOVE", "CONSTRAINT", "ADD"]]


class CapabilitiesResponse(BaseModel):
    api_version: str
    service_version: str
    mneme_contract_version: str
    supported_cost_modes: list[str]
    default_cost_mode: str
    strict_cost_mode: bool
    supports_embeddings: bool
    requires_embeddings: bool
    supports_reranking: bool
    supports_llm_enrichment: bool
    supports_context_prepare: bool
    supports_mcp_tools: bool
    supports_blob_store: bool
    supports_blob_range_reads: bool
    supports_export_bundle: bool
    supported_export_formats: list[str]
    supports_project_isolation: bool
    supports_session_readiness: bool
    supports_retention_cleanup: bool
    supports_reindex_jobs: bool
    supports_reindex_job_polling: bool
    supports_openapi: bool
    supports_metrics: bool
    metrics_format: str
    delta_extraction: DeltaExtractionCapability
    auth_schemes: list[str]
    integration_depth: CapabilitiesIntegrationDepth
    supported_schema_versions: dict[str, list[str]]
    mcp_tool_versions: dict[str, str]
    limits: CapabilitiesLimits
    tokenizer: CapabilitiesTokenizer
    storage: CapabilitiesStorage
    mcp_tools: list[str]
    providers: dict[str, ProviderCapability]
    max_batch_events: int
    max_event_content_bytes: int
    max_tool_result_events: int
