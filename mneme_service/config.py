from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping


_DEFAULT_ROUTER_WEIGHTS: dict[str, dict[str, float]] = {
    "general": {"semantic_similarity": 0.40, "recency": 0.20, "dependency": 0.30, "type_weight": 0.10},
    "reasoning": {"semantic_similarity": 0.35, "recency": 0.15, "dependency": 0.40, "type_weight": 0.10},
    "factual": {"semantic_similarity": 0.50, "recency": 0.30, "dependency": 0.10, "type_weight": 0.10},
    "debugging": {"semantic_similarity": 0.30, "recency": 0.40, "dependency": 0.10, "type_weight": 0.20},
}
_ROUTER_WEIGHT_KEYS = frozenset({"semantic_similarity", "recency", "dependency", "type_weight"})


def _default_routing_mode_weights() -> dict[str, dict[str, float]]:
    return {mode: dict(values) for mode, values in _DEFAULT_ROUTER_WEIGHTS.items()}


def _copy_routing_mode_weights(weights: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    return {mode: dict(values) for mode, values in weights.items()}


@dataclass(frozen=True)
class ProviderHealth:
    status: str = "UNKNOWN"
    checked_at_ms: int | None = None
    failure_count: int = 0
    last_error_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checked_at_ms": self.checked_at_ms,
            "failure_count": self.failure_count,
            "last_error_code": self.last_error_code,
        }


@dataclass(frozen=True)
class ProviderSettings:
    enabled: bool = False
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    timeout_seconds: float = 30.0
    batch_size: int = 16

    @property
    def configured(self) -> bool:
        return bool(self.provider and self.model)

    @property
    def available(self) -> bool:
        return self.enabled and self.configured

    @property
    def requires_api_key(self) -> bool:
        return self.provider in {"openai_compatible", "jina"}

    def runtime_available(self, *, injected_provider: bool = False) -> bool:
        if not self.enabled or not self.configured:
            return False
        return injected_provider or not self.requires_api_key or bool(self.api_key)

    def summary(self, *, available: bool | None = None, health: ProviderHealth | None = None) -> dict[str, Any]:
        runtime_available = self.runtime_available() if available is None else available
        health_body = health.as_dict() if health is not None else "UNKNOWN"
        live_status = health.status if health is not None else "UNKNOWN"
        live_health_checked = bool(health is not None and health.checked_at_ms is not None)
        return {
            "enabled": self.enabled,
            "configured": self.configured,
            "available": runtime_available,
            "availability_basis": "CONFIGURATION_AND_CREDENTIALS" if runtime_available else "NOT_RUNTIME_AVAILABLE",
            "live_status": live_status,
            "live_health_checked": live_health_checked,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "last_health": health_body,
        }


@dataclass(frozen=True)
class StaticTokenSettings:
    name: str
    token: str | None = None
    token_env: str | None = None
    token_file: Path | None = None
    project_scopes: tuple[str, ...] = ("*",)
    role: str = "OWNER"


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("mneme.db")
    auth_token: str | None = None
    auth_token_file: Path | None = None
    auth_token_env: str = "MNEME_AUTH_TOKEN"
    auth_mode: str = "owner_token"
    static_tokens: tuple[StaticTokenSettings, ...] = ()
    insecure_dev: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    require_embeddings: bool = False
    strict_cost_mode: bool = False
    active_window_tokens: int = 0
    context_window_usage_percent: float = 0.70
    protected_tail_turns: int = 64
    state_budget_ratio: float = 0.05
    retrieved_budget_ratio: float = 0.30
    protected_tail_ratio: float = 0.55
    pass_through_overhead_initial: int = 16_000
    segmentation_enabled: bool = True
    drift_threshold: float = 0.35
    drift_weights: tuple[float, float, float] = (0.4, 0.3, 0.3)
    centroid_cache_size: int = 100
    centroid_window: int = 200
    router_top_k: int = 0
    router_min_candidates: int = 12
    dependency_max_depth: int = 4
    dependency_decay: float = 0.6
    reranker_top_k: int = 0
    enricher_every_n_turns: int = 5
    enricher_on_segment_boundary: bool = True
    enricher_max_history_turns: int = 10
    enricher_timeout_seconds: float = 30.0
    enricher_max_tokens: int = 1500
    tool_output_compress_threshold_tokens: int = 500
    tool_output_summary_tokens: int = 100
    reindex_on_model_change: bool = False
    memory_access_hint_enabled: bool = True
    goal_trail_size: int = 3
    checkpoint_after_n_memory_calls: int = 5
    memory_tool_names: tuple[str, ...] = (
        "context_search",
        "fetch_event",
        "expand_context",
        "list_segments",
        "get_goal_history",
    )
    max_batch_events: int = 200
    max_event_content_bytes: int = 1_048_576
    max_blob_bytes: int = 2_097_152
    max_session_id_length: int = 256
    max_batch_total_blob_bytes: int = 20_971_520
    max_multipart_metadata_overhead_bytes: int = 2_097_152
    max_multipart_transaction_bytes: int = 23_068_672
    max_multipart_transaction_ms: int = 2000
    max_export_blob_inline_bytes: int = 0
    max_export_session_memory_bytes: int = 33_554_432
    idempotency_key_min_retention_seconds: int = 604_800
    max_writer_queue_depth: int = 1000
    startup_integrity_check: bool = True
    backup_before_migrate: Path | None = None
    no_backup_before_migrate: bool = False
    metrics_enabled: bool = True
    metrics_format: str = "prometheus"
    max_tool_result_events: int = 50
    retention_sweep_interval_seconds: int = 3600
    retention_sweep_on_startup: bool = True
    retention_sweep_on_session_close: bool = True
    retention_force_active_cleanup: bool = False
    vacuum_max_duration_ms: int = 500
    checkpoint_max_pages: int = 1000
    reindex_enqueue_when_provider_unavailable: bool = False
    reindex_foreground_write_priority: bool = True
    reindex_max_job_events: int = 10000
    reindex_max_events_per_transaction: int = 10
    reindex_yield_between_transactions_ms: int = 50
    reindex_provider_wait_timeout_seconds: int = 86400
    reindex_provider_max_requests_per_minute: int = 60
    reindex_provider_circuit_breaker_min_calls: int = 10
    reindex_provider_circuit_breaker_failure_ratio: float = 0.5
    reindex_provider_circuit_breaker_open_seconds: int = 60
    reindex_provider_circuit_breaker_half_open_requests: int = 2
    reindex_provider_recovery_ramp_initial_requests_per_minute: int = 10
    graph_importance_depth_decay: float = 0.5
    graph_max_traversal_steps: int = 1000
    graph_max_frontier_size: int = 500
    graph_max_branching_factor: int = 64
    routing_default_mode: str = "general"
    routing_mode_weights: dict[str, dict[str, float]] = field(default_factory=_default_routing_mode_weights)
    max_redaction_time_ms: int = 250
    binary_blob_extractor_policy: str = "DISABLED"
    audit_mode: str = "FULL"
    allow_unaudited_tools_for_tests: bool = False
    audit_forensic_retention_days: int = 90
    audit_anonymize_deleted_session_audit: bool = True
    project_isolation_key: str | None = None
    embeddings: ProviderSettings = field(default_factory=ProviderSettings)
    reranker: ProviderSettings = field(default_factory=ProviderSettings)
    llm_enrichment: ProviderSettings = field(default_factory=ProviderSettings)


def load_settings(
    *,
    config_path: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    cli_overrides: Mapping[str, Any] | None = None,
) -> Settings:
    """Load settings with precedence: CLI > env > config file > defaults."""
    env_map = os.environ if env is None else env
    resolved_config = Path(config_path) if config_path else _optional_path(env_map.get("MNEME_CONFIG"))
    settings = Settings()

    if resolved_config is not None:
        settings = _apply_config_file(settings, resolved_config)

    settings = _apply_env(settings, env_map)
    settings = _apply_cli(settings, cli_overrides or {})
    settings = _resolve_auth_tokens(settings, env_map)
    return validate_settings(settings)


def _optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value)


def _apply_config_file(settings: Settings, config_path: Path) -> Settings:
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    daemon = raw.get("daemon", {})
    limits = raw.get("limits", {})
    providers = raw.get("providers", {})
    auth = raw.get("auth", {})

    values: dict[str, Any] = {}
    for source in (
        daemon,
        limits,
        _parity_config_values(raw),
        raw.get("indexing", {}),
        raw.get("maintenance", {}),
        _prefixed_values(raw.get("maintenance", {}).get("reindex", {}), "reindex_"),
        _prefixed_values(raw.get("retrieval", {}).get("graph", {}), "graph_"),
        _prefixed_values(raw.get("audit", {}), "audit_"),
        auth,
    ):
        values.update(_settings_values(source))
    values.update(_routing_values_from_retrieval(raw.get("retrieval", {})))

    settings = replace(settings, **values)
    if isinstance(auth, Mapping) and "static_tokens" in auth:
        settings = replace(settings, static_tokens=_static_tokens_from_config(auth["static_tokens"]))
    return replace(
        settings,
        embeddings=_provider_from_mapping(settings.embeddings, providers.get("embeddings", {})),
        reranker=_provider_from_mapping(settings.reranker, providers.get("reranker", {})),
        llm_enrichment=_provider_from_mapping(
            settings.llm_enrichment,
            providers.get("llm_enrichment", {}),
        ),
    )


def _settings_values(source: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if "db_path" in source:
        values["db_path"] = Path(str(source["db_path"]))
    if "auth_token" in source:
        values["auth_token"] = _optional_str(source["auth_token"])
    if "token_env" in source:
        values["auth_token_env"] = str(source["token_env"])
    if "token_file" in source:
        values["auth_token_file"] = Path(str(source["token_file"]))
    if "auth_token_file" in source:
        values["auth_token_file"] = Path(str(source["auth_token_file"]))
    if "mode" in source:
        values["auth_mode"] = str(source["mode"])
    if "insecure_dev" in source:
        values["insecure_dev"] = _boolish(source["insecure_dev"])
    if "host" in source:
        values["host"] = str(source["host"])
    if "port" in source:
        values["port"] = int(source["port"])
    if "require_embeddings" in source:
        values["require_embeddings"] = _boolish(source["require_embeddings"])
    if "strict_cost_mode" in source:
        values["strict_cost_mode"] = _boolish(source["strict_cost_mode"])
    if "active_window_tokens" in source:
        values["active_window_tokens"] = int(source["active_window_tokens"])
    if "context_window_usage_percent" in source:
        values["context_window_usage_percent"] = float(source["context_window_usage_percent"])
    if "protected_tail_turns" in source:
        values["protected_tail_turns"] = int(source["protected_tail_turns"])
    if "state_budget_ratio" in source:
        values["state_budget_ratio"] = float(source["state_budget_ratio"])
    if "retrieved_budget_ratio" in source:
        values["retrieved_budget_ratio"] = float(source["retrieved_budget_ratio"])
    if "protected_tail_ratio" in source:
        values["protected_tail_ratio"] = float(source["protected_tail_ratio"])
    if "pass_through_overhead_initial" in source:
        values["pass_through_overhead_initial"] = int(source["pass_through_overhead_initial"])
    if "segmentation_enabled" in source:
        values["segmentation_enabled"] = _boolish(source["segmentation_enabled"])
    if "drift_threshold" in source:
        values["drift_threshold"] = float(source["drift_threshold"])
    if "drift_weights" in source:
        values["drift_weights"] = _float_tuple(source["drift_weights"], expected=3)
    if "centroid_cache_size" in source:
        values["centroid_cache_size"] = int(source["centroid_cache_size"])
    if "centroid_window" in source:
        values["centroid_window"] = int(source["centroid_window"])
    if "router_top_k" in source:
        values["router_top_k"] = int(source["router_top_k"])
    if "router_min_candidates" in source:
        values["router_min_candidates"] = int(source["router_min_candidates"])
    if "dependency_max_depth" in source:
        values["dependency_max_depth"] = int(source["dependency_max_depth"])
    if "dependency_decay" in source:
        values["dependency_decay"] = float(source["dependency_decay"])
    if "reranker_top_k" in source:
        values["reranker_top_k"] = int(source["reranker_top_k"])
    if "enricher_every_n_turns" in source:
        values["enricher_every_n_turns"] = int(source["enricher_every_n_turns"])
    if "enricher_on_segment_boundary" in source:
        values["enricher_on_segment_boundary"] = _boolish(source["enricher_on_segment_boundary"])
    if "enricher_max_history_turns" in source:
        values["enricher_max_history_turns"] = int(source["enricher_max_history_turns"])
    if "enricher_timeout_seconds" in source:
        values["enricher_timeout_seconds"] = float(source["enricher_timeout_seconds"])
    if "enricher_max_tokens" in source:
        values["enricher_max_tokens"] = int(source["enricher_max_tokens"])
    if "tool_output_compress_threshold_tokens" in source:
        values["tool_output_compress_threshold_tokens"] = int(source["tool_output_compress_threshold_tokens"])
    if "tool_output_summary_tokens" in source:
        values["tool_output_summary_tokens"] = int(source["tool_output_summary_tokens"])
    if "reindex_on_model_change" in source:
        values["reindex_on_model_change"] = _boolish(source["reindex_on_model_change"])
    if "memory_access_hint_enabled" in source:
        values["memory_access_hint_enabled"] = _boolish(source["memory_access_hint_enabled"])
    if "goal_trail_size" in source:
        values["goal_trail_size"] = int(source["goal_trail_size"])
    if "checkpoint_after_n_memory_calls" in source:
        values["checkpoint_after_n_memory_calls"] = int(source["checkpoint_after_n_memory_calls"])
    if "memory_tool_names" in source:
        values["memory_tool_names"] = _str_tuple(source["memory_tool_names"])
    if "max_batch_events" in source:
        values["max_batch_events"] = int(source["max_batch_events"])
    if "max_event_content_bytes" in source:
        values["max_event_content_bytes"] = int(source["max_event_content_bytes"])
    if "max_blob_bytes" in source:
        values["max_blob_bytes"] = int(source["max_blob_bytes"])
    if "max_session_id_length" in source:
        values["max_session_id_length"] = int(source["max_session_id_length"])
    if "max_batch_total_blob_bytes" in source:
        values["max_batch_total_blob_bytes"] = int(source["max_batch_total_blob_bytes"])
    if "max_multipart_metadata_overhead_bytes" in source:
        values["max_multipart_metadata_overhead_bytes"] = int(source["max_multipart_metadata_overhead_bytes"])
    if "max_multipart_transaction_bytes" in source:
        values["max_multipart_transaction_bytes"] = int(source["max_multipart_transaction_bytes"])
    if "max_multipart_transaction_ms" in source:
        values["max_multipart_transaction_ms"] = int(source["max_multipart_transaction_ms"])
    if "max_export_blob_inline_bytes" in source:
        values["max_export_blob_inline_bytes"] = int(source["max_export_blob_inline_bytes"])
    if "max_export_session_memory_bytes" in source:
        values["max_export_session_memory_bytes"] = int(source["max_export_session_memory_bytes"])
    if "idempotency_key_min_retention_seconds" in source:
        values["idempotency_key_min_retention_seconds"] = int(source["idempotency_key_min_retention_seconds"])
    if "max_writer_queue_depth" in source:
        values["max_writer_queue_depth"] = int(source["max_writer_queue_depth"])
    if "startup_integrity_check" in source:
        values["startup_integrity_check"] = _boolish(source["startup_integrity_check"])
    if "backup_before_migrate" in source:
        values["backup_before_migrate"] = Path(str(source["backup_before_migrate"]))
    if "no_backup_before_migrate" in source:
        values["no_backup_before_migrate"] = _boolish(source["no_backup_before_migrate"])
    if "metrics_enabled" in source:
        values["metrics_enabled"] = _boolish(source["metrics_enabled"])
    if "metrics_format" in source:
        values["metrics_format"] = str(source["metrics_format"])
    if "max_tool_result_events" in source:
        values["max_tool_result_events"] = int(source["max_tool_result_events"])
    if "retention_sweep_interval_seconds" in source:
        values["retention_sweep_interval_seconds"] = int(source["retention_sweep_interval_seconds"])
    if "retention_sweep_on_startup" in source:
        values["retention_sweep_on_startup"] = _boolish(source["retention_sweep_on_startup"])
    if "retention_sweep_on_session_close" in source:
        values["retention_sweep_on_session_close"] = _boolish(source["retention_sweep_on_session_close"])
    if "retention_force_active_cleanup" in source:
        values["retention_force_active_cleanup"] = _boolish(source["retention_force_active_cleanup"])
    if "vacuum_max_duration_ms" in source:
        values["vacuum_max_duration_ms"] = int(source["vacuum_max_duration_ms"])
    if "checkpoint_max_pages" in source:
        values["checkpoint_max_pages"] = int(source["checkpoint_max_pages"])
    if "reindex_enqueue_when_provider_unavailable" in source:
        values["reindex_enqueue_when_provider_unavailable"] = _boolish(source["reindex_enqueue_when_provider_unavailable"])
    if "reindex_foreground_write_priority" in source:
        values["reindex_foreground_write_priority"] = _boolish(source["reindex_foreground_write_priority"])
    if "reindex_max_job_events" in source:
        values["reindex_max_job_events"] = int(source["reindex_max_job_events"])
    if "reindex_max_events_per_transaction" in source:
        values["reindex_max_events_per_transaction"] = int(source["reindex_max_events_per_transaction"])
    if "reindex_yield_between_transactions_ms" in source:
        values["reindex_yield_between_transactions_ms"] = int(source["reindex_yield_between_transactions_ms"])
    if "reindex_provider_wait_timeout_seconds" in source:
        values["reindex_provider_wait_timeout_seconds"] = int(source["reindex_provider_wait_timeout_seconds"])
    if "reindex_provider_max_requests_per_minute" in source:
        values["reindex_provider_max_requests_per_minute"] = int(source["reindex_provider_max_requests_per_minute"])
    if "reindex_provider_circuit_breaker_min_calls" in source:
        values["reindex_provider_circuit_breaker_min_calls"] = int(source["reindex_provider_circuit_breaker_min_calls"])
    if "reindex_provider_circuit_breaker_failure_ratio" in source:
        values["reindex_provider_circuit_breaker_failure_ratio"] = float(source["reindex_provider_circuit_breaker_failure_ratio"])
    if "reindex_provider_circuit_breaker_open_seconds" in source:
        values["reindex_provider_circuit_breaker_open_seconds"] = int(source["reindex_provider_circuit_breaker_open_seconds"])
    if "reindex_provider_circuit_breaker_half_open_requests" in source:
        values["reindex_provider_circuit_breaker_half_open_requests"] = int(source["reindex_provider_circuit_breaker_half_open_requests"])
    if "reindex_provider_recovery_ramp_initial_requests_per_minute" in source:
        values["reindex_provider_recovery_ramp_initial_requests_per_minute"] = int(source["reindex_provider_recovery_ramp_initial_requests_per_minute"])
    if "graph_importance_depth_decay" in source:
        values["graph_importance_depth_decay"] = float(source["graph_importance_depth_decay"])
    if "graph_max_traversal_steps" in source:
        values["graph_max_traversal_steps"] = int(source["graph_max_traversal_steps"])
    if "graph_max_frontier_size" in source:
        values["graph_max_frontier_size"] = int(source["graph_max_frontier_size"])
    if "graph_max_branching_factor" in source:
        values["graph_max_branching_factor"] = int(source["graph_max_branching_factor"])
    if "routing_default_mode" in source:
        values["routing_default_mode"] = str(source["routing_default_mode"]).strip().lower()
    if "routing_mode_weights" in source:
        values["routing_mode_weights"] = _routing_mode_weights_from_mapping(source["routing_mode_weights"])
    if "max_redaction_time_ms" in source:
        values["max_redaction_time_ms"] = int(source["max_redaction_time_ms"])
    if "binary_blob_extractor_policy" in source:
        values["binary_blob_extractor_policy"] = str(source["binary_blob_extractor_policy"]).strip().upper()
    if "audit_forensic_retention_days" in source:
        values["audit_forensic_retention_days"] = int(source["audit_forensic_retention_days"])
    if "audit_anonymize_deleted_session_audit" in source:
        values["audit_anonymize_deleted_session_audit"] = _boolish(source["audit_anonymize_deleted_session_audit"])
    if "audit_mode" in source:
        values["audit_mode"] = str(source["audit_mode"]).strip().upper()
    if "audit_allow_unaudited_tools_for_tests" in source:
        values["allow_unaudited_tools_for_tests"] = _boolish(source["audit_allow_unaudited_tools_for_tests"])
    if "allow_unaudited_tools_for_tests" in source:
        values["allow_unaudited_tools_for_tests"] = _boolish(source["allow_unaudited_tools_for_tests"])
    if "project_isolation_key" in source:
        values["project_isolation_key"] = _optional_str(source["project_isolation_key"])
    return values


def _prefixed_values(source: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        return {}
    return {f"{prefix}{key}": value for key, value in source.items()}


def validate_settings(settings: Settings) -> Settings:
    if not 1 <= settings.max_session_id_length <= 256:
        raise ValueError("max_session_id_length must be between 1 and 256.")
    if settings.max_multipart_transaction_bytes < (
        settings.max_batch_total_blob_bytes + settings.max_multipart_metadata_overhead_bytes
    ):
        raise ValueError(
            "max_multipart_transaction_bytes must be at least "
            "max_batch_total_blob_bytes + max_multipart_metadata_overhead_bytes."
        )
    positive_ints = {
        "idempotency_key_min_retention_seconds": settings.idempotency_key_min_retention_seconds,
        "max_writer_queue_depth": settings.max_writer_queue_depth,
        "max_multipart_transaction_ms": settings.max_multipart_transaction_ms,
        "graph_max_traversal_steps": settings.graph_max_traversal_steps,
        "graph_max_frontier_size": settings.graph_max_frontier_size,
        "graph_max_branching_factor": settings.graph_max_branching_factor,
        "reindex_provider_max_requests_per_minute": settings.reindex_provider_max_requests_per_minute,
        "reindex_provider_circuit_breaker_min_calls": settings.reindex_provider_circuit_breaker_min_calls,
        "reindex_provider_circuit_breaker_open_seconds": settings.reindex_provider_circuit_breaker_open_seconds,
        "reindex_provider_circuit_breaker_half_open_requests": settings.reindex_provider_circuit_breaker_half_open_requests,
        "tool_output_compress_threshold_tokens": settings.tool_output_compress_threshold_tokens,
        "tool_output_summary_tokens": settings.tool_output_summary_tokens,
        "max_redaction_time_ms": settings.max_redaction_time_ms,
    }
    for name, value in positive_ints.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive.")
    if not 0 < settings.graph_importance_depth_decay <= 1:
        raise ValueError("importance_depth_decay must be in (0, 1].")
    if not 0 < settings.reindex_provider_circuit_breaker_failure_ratio <= 1:
        raise ValueError("provider_circuit_breaker_failure_ratio must be in (0, 1].")
    if settings.tool_output_summary_tokens >= settings.tool_output_compress_threshold_tokens:
        raise ValueError("tool_output_summary_tokens must be lower than tool_output_compress_threshold_tokens.")
    if settings.metrics_format != "prometheus":
        raise ValueError("metrics_format must be prometheus.")
    if settings.audit_mode not in {"FULL", "TRACE_ONLY", "DISABLED_TEST_ONLY"}:
        raise ValueError("audit_mode must be FULL, TRACE_ONLY, or DISABLED_TEST_ONLY.")
    if settings.binary_blob_extractor_policy not in {"DISABLED", "EXPLICIT_TEXT_ONLY"}:
        raise ValueError("binary_blob_extractor_policy must be DISABLED or EXPLICIT_TEXT_ONLY.")
    _validate_routing_settings(settings)
    if settings.audit_mode == "DISABLED_TEST_ONLY" and not settings.allow_unaudited_tools_for_tests:
        raise ValueError(
            "DISABLED_TEST_ONLY audit mode requires MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS=true."
        )
    return settings


def _validate_routing_settings(settings: Settings) -> None:
    default_mode = settings.routing_default_mode.strip().lower()
    available_modes = set(settings.routing_mode_weights)
    if default_mode not in available_modes:
        raise ValueError(
            "routing_default_mode must be one of configured routing modes: "
            f"{sorted(available_modes)}."
        )

    for mode, weights in settings.routing_mode_weights.items():
        if set(weights) != _ROUTER_WEIGHT_KEYS:
            raise ValueError(
                "routing_mode_weights must include exactly semantic_similarity, recency, dependency, type_weight"
            )
        normalized: list[tuple[str, float]] = []
        for key, value in weights.items():
            weight = float(value)
            if weight < 0:
                raise ValueError(f"routing weight {key} for mode {mode} must be non-negative.")
            normalized.append((key, weight))
        if abs(sum(weight for _, weight in normalized) - 1.0) > 0.01:
            raise ValueError(f"routing weights for mode {mode} must sum to 1.0 ± 0.01.")


def _validate_routing_mode(mode: str) -> str:
    return str(mode).strip().lower()


def _parity_config_values(raw: Mapping[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for section_name in ("budget", "retrieval", "embedding_index", "memory"):
        section = raw.get(section_name, {})
        if isinstance(section, Mapping):
            values.update(section)

    segmentation = raw.get("segmentation", {})
    if isinstance(segmentation, Mapping):
        values.update(segmentation)
        if "enabled" in segmentation:
            values["segmentation_enabled"] = segmentation["enabled"]

    enrichment = raw.get("enrichment", {})
    if isinstance(enrichment, Mapping):
        values.update(enrichment)
        aliases = {
            "every_n_turns": "enricher_every_n_turns",
            "on_segment_boundary": "enricher_on_segment_boundary",
            "max_history_turns": "enricher_max_history_turns",
            "timeout_seconds": "enricher_timeout_seconds",
            "max_tokens": "enricher_max_tokens",
        }
        for source_key, target_key in aliases.items():
            if source_key in enrichment:
                values[target_key] = enrichment[source_key]
    return values


def _provider_from_mapping(provider: ProviderSettings, source: Mapping[str, Any]) -> ProviderSettings:
    if not source:
        return provider
    values: dict[str, Any] = {}
    if "enabled" in source:
        values["enabled"] = _boolish(source["enabled"])
    if "provider" in source:
        values["provider"] = _optional_str(source["provider"])
    if "model" in source:
        values["model"] = _optional_str(source["model"])
    if "base_url" in source:
        values["base_url"] = _optional_str(source["base_url"])
    if "api_key" in source:
        values["api_key"] = _optional_str(source["api_key"])
    if "timeout_seconds" in source:
        values["timeout_seconds"] = float(source["timeout_seconds"])
    if "batch_size" in source:
        values["batch_size"] = int(source["batch_size"])
    return replace(provider, **values)


def _static_tokens_from_config(source: Any) -> tuple[StaticTokenSettings, ...]:
    tokens: list[StaticTokenSettings] = []
    for item in source if isinstance(source, list) else []:
        if not isinstance(item, Mapping):
            raise ValueError("auth.static_tokens entries must be tables.")
        name = _optional_str(item.get("name"))
        if not name:
            raise ValueError("auth.static_tokens entries require name.")
        tokens.append(
            StaticTokenSettings(
                name=name,
                token=_optional_str(item.get("token")),
                token_env=_optional_str(item.get("token_env")),
                token_file=Path(str(item["token_file"])) if item.get("token_file") else None,
                project_scopes=_str_tuple(item.get("project_scopes", ["*"])),
                role=str(item.get("role") or "OWNER").upper(),
            )
        )
    return tuple(tokens)


def _resolve_auth_tokens(settings: Settings, env: Mapping[str, str]) -> Settings:
    auth_token = settings.auth_token
    if not auth_token and settings.auth_token_env in env:
        auth_token = _optional_str(env[settings.auth_token_env])
    if not auth_token and settings.auth_token_file:
        auth_token = _read_token_file(settings.auth_token_file, label="auth token")
    static_tokens = tuple(_resolve_static_token(token, env) for token in settings.static_tokens)
    return replace(settings, auth_token=auth_token, static_tokens=static_tokens)


def _resolve_static_token(token: StaticTokenSettings, env: Mapping[str, str]) -> StaticTokenSettings:
    value = token.token
    if not value and token.token_env:
        value = _optional_str(env.get(token.token_env))
    if not value and token.token_file:
        value = _read_token_file(token.token_file, label=f"static token {token.name}")
    if not value:
        raise ValueError(f"static token {token.name} requires token, token_env, or token_file.")
    return replace(token, token=value)


def _read_token_file(path: Path, *, label: str) -> str:
    try:
        mode = path.stat().st_mode
        if mode & 0o077:
            raise ValueError(f"{label} file must be owner-readable only: {path}")
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError(f"Unable to read {label} file: {path}") from exc
    if not token:
        raise ValueError(f"{label} file is empty: {path}")
    return token


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _routing_mode_weights_from_mapping(source: Any) -> dict[str, dict[str, float]]:
    if not isinstance(source, Mapping):
        raise ValueError("routing_mode_weights must be a mapping.")
    values: dict[str, dict[str, float]] = {}
    for mode_name, weights in source.items():
        mode_key = str(mode_name).strip().lower()
        if not isinstance(weights, Mapping):
            raise ValueError(f"routing_mode_weights[{mode_key}] must be a mapping.")
        values[mode_key] = {str(key): float(value) for key, value in weights.items()}
    return values


def _merge_routing_mode_weights(
    base: Mapping[str, Mapping[str, float]],
    override: Mapping[str, Mapping[str, float]],
) -> dict[str, dict[str, float]]:
    merged = _copy_routing_mode_weights(base)
    for mode, weights in override.items():
        mode_key = str(mode).strip().lower()
        merged[mode_key] = {str(key): float(value) for key, value in weights.items()}
    return merged


def _routing_values_from_retrieval(source: Any) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        return {}
    routing = source.get("routing")
    if not isinstance(routing, Mapping):
        return {}

    values: dict[str, Any] = {}
    if "default_mode" in routing:
        values["routing_default_mode"] = str(routing["default_mode"]).strip().lower()
    if "weights" in routing:
        values["routing_mode_weights"] = _merge_routing_mode_weights(
            _DEFAULT_ROUTER_WEIGHTS,
            _routing_mode_weights_from_mapping(routing.get("weights", {})),
        )
    return values


def _patch_routing_weight(
    source: Mapping[str, Mapping[str, float]],
    mode: str,
    component: str,
    value: float,
) -> dict[str, dict[str, float]]:
    updated = _copy_routing_mode_weights(source)
    mode_key = str(mode).strip().lower()
    component_key = str(component).strip()
    weights = updated.setdefault(mode_key, {key: 0.0 for key in _ROUTER_WEIGHT_KEYS})
    weights[component_key] = float(value)
    return updated


def _apply_env(settings: Settings, env: Mapping[str, str]) -> Settings:
    values: dict[str, Any] = {}
    if "MNEME_DB_PATH" in env:
        values["db_path"] = Path(env["MNEME_DB_PATH"])
    if "MNEME_AUTH_TOKEN" in env:
        values["auth_token"] = env["MNEME_AUTH_TOKEN"]
    if "MNEME_AUTH_TOKEN_FILE" in env:
        values["auth_token_file"] = Path(env["MNEME_AUTH_TOKEN_FILE"])
    if "MNEME_INSECURE_DEV" in env:
        values["insecure_dev"] = _parse_bool(env["MNEME_INSECURE_DEV"])
    if "MNEME_HOST" in env:
        values["host"] = env["MNEME_HOST"]
    if "MNEME_PORT" in env:
        values["port"] = int(env["MNEME_PORT"])
    if "MNEME_REQUIRE_EMBEDDINGS" in env:
        values["require_embeddings"] = _parse_bool(env["MNEME_REQUIRE_EMBEDDINGS"])
    if "MNEME_STRICT_COST_MODE" in env:
        values["strict_cost_mode"] = _parse_bool(env["MNEME_STRICT_COST_MODE"])
    if "MNEME_MAX_BATCH_EVENTS" in env:
        values["max_batch_events"] = int(env["MNEME_MAX_BATCH_EVENTS"])
    if "MNEME_MAX_EVENT_CONTENT_BYTES" in env:
        values["max_event_content_bytes"] = int(env["MNEME_MAX_EVENT_CONTENT_BYTES"])
    if "MNEME_MAX_BLOB_BYTES" in env:
        values["max_blob_bytes"] = int(env["MNEME_MAX_BLOB_BYTES"])
    if "MNEME_MAX_SESSION_ID_LENGTH" in env:
        values["max_session_id_length"] = int(env["MNEME_MAX_SESSION_ID_LENGTH"])
    if "MNEME_MAX_BATCH_TOTAL_BLOB_BYTES" in env:
        values["max_batch_total_blob_bytes"] = int(env["MNEME_MAX_BATCH_TOTAL_BLOB_BYTES"])
    if "MNEME_MAX_MULTIPART_METADATA_OVERHEAD_BYTES" in env:
        values["max_multipart_metadata_overhead_bytes"] = int(
            env["MNEME_MAX_MULTIPART_METADATA_OVERHEAD_BYTES"]
        )
    if "MNEME_MAX_MULTIPART_TRANSACTION_BYTES" in env:
        values["max_multipart_transaction_bytes"] = int(env["MNEME_MAX_MULTIPART_TRANSACTION_BYTES"])
    if "MNEME_MAX_MULTIPART_TRANSACTION_MS" in env:
        values["max_multipart_transaction_ms"] = int(env["MNEME_MAX_MULTIPART_TRANSACTION_MS"])
    if "MNEME_MAX_EXPORT_BLOB_INLINE_BYTES" in env:
        values["max_export_blob_inline_bytes"] = int(env["MNEME_MAX_EXPORT_BLOB_INLINE_BYTES"])
    if "MNEME_MAX_EXPORT_SESSION_MEMORY_BYTES" in env:
        values["max_export_session_memory_bytes"] = int(env["MNEME_MAX_EXPORT_SESSION_MEMORY_BYTES"])
    if "MNEME_IDEMPOTENCY_KEY_MIN_RETENTION_SECONDS" in env:
        values["idempotency_key_min_retention_seconds"] = int(
            env["MNEME_IDEMPOTENCY_KEY_MIN_RETENTION_SECONDS"]
        )
    if "MNEME_MAX_TOOL_RESULT_EVENTS" in env:
        values["max_tool_result_events"] = int(env["MNEME_MAX_TOOL_RESULT_EVENTS"])
    if "MNEME_MAX_WRITER_QUEUE_DEPTH" in env:
        values["max_writer_queue_depth"] = int(env["MNEME_MAX_WRITER_QUEUE_DEPTH"])
    if "MNEME_BACKUP_BEFORE_MIGRATE" in env:
        values["backup_before_migrate"] = Path(env["MNEME_BACKUP_BEFORE_MIGRATE"])
    if "MNEME_NO_BACKUP_BEFORE_MIGRATE" in env:
        values["no_backup_before_migrate"] = _parse_bool(env["MNEME_NO_BACKUP_BEFORE_MIGRATE"])
    if "MNEME_STARTUP_INTEGRITY_CHECK" in env:
        values["startup_integrity_check"] = _parse_bool(env["MNEME_STARTUP_INTEGRITY_CHECK"])
    if "MNEME_ACTIVE_WINDOW_TOKENS" in env:
        values["active_window_tokens"] = int(env["MNEME_ACTIVE_WINDOW_TOKENS"])
    if "MNEME_CONTEXT_WINDOW_USAGE_PERCENT" in env:
        values["context_window_usage_percent"] = float(env["MNEME_CONTEXT_WINDOW_USAGE_PERCENT"])
    if "MNEME_PROTECTED_TAIL_TURNS" in env:
        values["protected_tail_turns"] = int(env["MNEME_PROTECTED_TAIL_TURNS"])
    if "MNEME_STATE_BUDGET_RATIO" in env:
        values["state_budget_ratio"] = float(env["MNEME_STATE_BUDGET_RATIO"])
    if "MNEME_RETRIEVED_BUDGET_RATIO" in env:
        values["retrieved_budget_ratio"] = float(env["MNEME_RETRIEVED_BUDGET_RATIO"])
    if "MNEME_PROTECTED_TAIL_RATIO" in env:
        values["protected_tail_ratio"] = float(env["MNEME_PROTECTED_TAIL_RATIO"])
    if "MNEME_PASS_THROUGH_OVERHEAD_INITIAL" in env:
        values["pass_through_overhead_initial"] = int(env["MNEME_PASS_THROUGH_OVERHEAD_INITIAL"])
    if "MNEME_SEGMENTATION_ENABLED" in env:
        values["segmentation_enabled"] = _parse_bool(env["MNEME_SEGMENTATION_ENABLED"])
    if "MNEME_DRIFT_THRESHOLD" in env:
        values["drift_threshold"] = float(env["MNEME_DRIFT_THRESHOLD"])
    if "MNEME_DRIFT_WEIGHTS" in env:
        values["drift_weights"] = _float_tuple(env["MNEME_DRIFT_WEIGHTS"], expected=3)
    if "MNEME_CENTROID_CACHE_SIZE" in env:
        values["centroid_cache_size"] = int(env["MNEME_CENTROID_CACHE_SIZE"])
    if "MNEME_CENTROID_WINDOW" in env:
        values["centroid_window"] = int(env["MNEME_CENTROID_WINDOW"])
    if "MNEME_ROUTER_TOP_K" in env:
        values["router_top_k"] = int(env["MNEME_ROUTER_TOP_K"])
    if "MNEME_ROUTER_MIN_CANDIDATES" in env:
        values["router_min_candidates"] = int(env["MNEME_ROUTER_MIN_CANDIDATES"])
    if "MNEME_DEPENDENCY_MAX_DEPTH" in env:
        values["dependency_max_depth"] = int(env["MNEME_DEPENDENCY_MAX_DEPTH"])
    if "MNEME_DEPENDENCY_DECAY" in env:
        values["dependency_decay"] = float(env["MNEME_DEPENDENCY_DECAY"])
    if "MNEME_RERANKER_TOP_K" in env:
        values["reranker_top_k"] = int(env["MNEME_RERANKER_TOP_K"])
    if "MNEME_ENRICHER_EVERY_N_TURNS" in env:
        values["enricher_every_n_turns"] = int(env["MNEME_ENRICHER_EVERY_N_TURNS"])
    if "MNEME_ENRICHER_ON_SEGMENT_BOUNDARY" in env:
        values["enricher_on_segment_boundary"] = _parse_bool(env["MNEME_ENRICHER_ON_SEGMENT_BOUNDARY"])
    if "MNEME_ENRICHER_MAX_HISTORY_TURNS" in env:
        values["enricher_max_history_turns"] = int(env["MNEME_ENRICHER_MAX_HISTORY_TURNS"])
    if "MNEME_ENRICHER_TIMEOUT_SECONDS" in env:
        values["enricher_timeout_seconds"] = float(env["MNEME_ENRICHER_TIMEOUT_SECONDS"])
    if "MNEME_ENRICHER_MAX_TOKENS" in env:
        values["enricher_max_tokens"] = int(env["MNEME_ENRICHER_MAX_TOKENS"])
    if "MNEME_TOOL_OUTPUT_COMPRESS_THRESHOLD_TOKENS" in env:
        values["tool_output_compress_threshold_tokens"] = int(env["MNEME_TOOL_OUTPUT_COMPRESS_THRESHOLD_TOKENS"])
    if "MNEME_TOOL_OUTPUT_SUMMARY_TOKENS" in env:
        values["tool_output_summary_tokens"] = int(env["MNEME_TOOL_OUTPUT_SUMMARY_TOKENS"])
    if "MNEME_BINARY_BLOB_EXTRACTOR_POLICY" in env:
        values["binary_blob_extractor_policy"] = env["MNEME_BINARY_BLOB_EXTRACTOR_POLICY"].strip().upper()
    if "MNEME_REINDEX_ON_MODEL_CHANGE" in env:
        values["reindex_on_model_change"] = _parse_bool(env["MNEME_REINDEX_ON_MODEL_CHANGE"])
    if "MNEME_MEMORY_ACCESS_HINT_ENABLED" in env:
        values["memory_access_hint_enabled"] = _parse_bool(env["MNEME_MEMORY_ACCESS_HINT_ENABLED"])
    if "MNEME_GOAL_TRAIL_SIZE" in env:
        values["goal_trail_size"] = int(env["MNEME_GOAL_TRAIL_SIZE"])
    if "MNEME_CHECKPOINT_AFTER_N_MEMORY_CALLS" in env:
        values["checkpoint_after_n_memory_calls"] = int(env["MNEME_CHECKPOINT_AFTER_N_MEMORY_CALLS"])
    if "MNEME_MEMORY_TOOL_NAMES" in env:
        values["memory_tool_names"] = _str_tuple(env["MNEME_MEMORY_TOOL_NAMES"])
    if "MNEME_METRICS_ENABLED" in env:
        values["metrics_enabled"] = _parse_bool(env["MNEME_METRICS_ENABLED"])
    if "MNEME_METRICS_FORMAT" in env:
        values["metrics_format"] = env["MNEME_METRICS_FORMAT"]
    if "MNEME_RETENTION_SWEEP_INTERVAL_SECONDS" in env:
        values["retention_sweep_interval_seconds"] = int(env["MNEME_RETENTION_SWEEP_INTERVAL_SECONDS"])
    if "MNEME_RETENTION_SWEEP_ON_STARTUP" in env:
        values["retention_sweep_on_startup"] = _parse_bool(env["MNEME_RETENTION_SWEEP_ON_STARTUP"])
    if "MNEME_RETENTION_SWEEP_ON_SESSION_CLOSE" in env:
        values["retention_sweep_on_session_close"] = _parse_bool(
            env["MNEME_RETENTION_SWEEP_ON_SESSION_CLOSE"]
        )
    if "MNEME_RETENTION_FORCE_ACTIVE_CLEANUP" in env:
        values["retention_force_active_cleanup"] = _parse_bool(env["MNEME_RETENTION_FORCE_ACTIVE_CLEANUP"])
    if "MNEME_VACUUM_MAX_DURATION_MS" in env:
        values["vacuum_max_duration_ms"] = int(env["MNEME_VACUUM_MAX_DURATION_MS"])
    if "MNEME_CHECKPOINT_MAX_PAGES" in env:
        values["checkpoint_max_pages"] = int(env["MNEME_CHECKPOINT_MAX_PAGES"])
    if "MNEME_REINDEX_ENQUEUE_WHEN_PROVIDER_UNAVAILABLE" in env:
        values["reindex_enqueue_when_provider_unavailable"] = _parse_bool(
            env["MNEME_REINDEX_ENQUEUE_WHEN_PROVIDER_UNAVAILABLE"]
        )
    if "MNEME_REINDEX_FOREGROUND_WRITE_PRIORITY" in env:
        values["reindex_foreground_write_priority"] = _parse_bool(
            env["MNEME_REINDEX_FOREGROUND_WRITE_PRIORITY"]
        )
    if "MNEME_REINDEX_MAX_JOB_EVENTS" in env:
        values["reindex_max_job_events"] = int(env["MNEME_REINDEX_MAX_JOB_EVENTS"])
    if "MNEME_REINDEX_MAX_EVENTS_PER_TRANSACTION" in env:
        values["reindex_max_events_per_transaction"] = int(env["MNEME_REINDEX_MAX_EVENTS_PER_TRANSACTION"])
    if "MNEME_REINDEX_YIELD_BETWEEN_TRANSACTIONS_MS" in env:
        values["reindex_yield_between_transactions_ms"] = int(
            env["MNEME_REINDEX_YIELD_BETWEEN_TRANSACTIONS_MS"]
        )
    if "MNEME_REINDEX_PROVIDER_WAIT_TIMEOUT_SECONDS" in env:
        values["reindex_provider_wait_timeout_seconds"] = int(
            env["MNEME_REINDEX_PROVIDER_WAIT_TIMEOUT_SECONDS"]
        )
    if "MNEME_REINDEX_PROVIDER_MAX_REQUESTS_PER_MINUTE" in env:
        values["reindex_provider_max_requests_per_minute"] = int(
            env["MNEME_REINDEX_PROVIDER_MAX_REQUESTS_PER_MINUTE"]
        )
    if "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_MIN_CALLS" in env:
        values["reindex_provider_circuit_breaker_min_calls"] = int(
            env["MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_MIN_CALLS"]
        )
    if "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_FAILURE_RATIO" in env:
        values["reindex_provider_circuit_breaker_failure_ratio"] = float(
            env["MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_FAILURE_RATIO"]
        )
    if "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_OPEN_SECONDS" in env:
        values["reindex_provider_circuit_breaker_open_seconds"] = int(
            env["MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_OPEN_SECONDS"]
        )
    if "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_HALF_OPEN_REQUESTS" in env:
        values["reindex_provider_circuit_breaker_half_open_requests"] = int(
            env["MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_HALF_OPEN_REQUESTS"]
        )
    if "MNEME_REINDEX_PROVIDER_RECOVERY_RAMP_INITIAL_REQUESTS_PER_MINUTE" in env:
        values["reindex_provider_recovery_ramp_initial_requests_per_minute"] = int(
            env["MNEME_REINDEX_PROVIDER_RECOVERY_RAMP_INITIAL_REQUESTS_PER_MINUTE"]
        )
    if "MNEME_MAX_REDACTION_TIME_MS" in env:
        values["max_redaction_time_ms"] = int(env["MNEME_MAX_REDACTION_TIME_MS"])
    if "MNEME_AUDIT_FORENSIC_RETENTION_DAYS" in env:
        values["audit_forensic_retention_days"] = int(env["MNEME_AUDIT_FORENSIC_RETENTION_DAYS"])
    if "MNEME_AUDIT_ANONYMIZE_DELETED_SESSION_AUDIT" in env:
        values["audit_anonymize_deleted_session_audit"] = _parse_bool(
            env["MNEME_AUDIT_ANONYMIZE_DELETED_SESSION_AUDIT"]
        )
    if "MNEME_AUDIT_MODE" in env:
        values["audit_mode"] = env["MNEME_AUDIT_MODE"].strip().upper()
    if "MNEME_ROUTING_DEFAULT_MODE" in env:
        values["routing_default_mode"] = env["MNEME_ROUTING_DEFAULT_MODE"].strip().lower()
    if "MNEME_ROUTING_WEIGHT_DEBUGGING_DEPENDENCY" in env:
        values["routing_mode_weights"] = _patch_routing_weight(
            settings.routing_mode_weights,
            "debugging",
            "dependency",
            float(env["MNEME_ROUTING_WEIGHT_DEBUGGING_DEPENDENCY"]),
        )
    if "MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS" in env:
        values["allow_unaudited_tools_for_tests"] = _parse_bool(env["MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS"])

    settings = replace(settings, **values)
    return replace(
        settings,
        embeddings=_provider_from_env(
            settings.embeddings,
            env,
            enabled="MNEME_EMBEDDINGS_ENABLED",
            provider_key="MNEME_EMBEDDING_PROVIDER",
            model="MNEME_EMBEDDING_MODEL",
            base_url="MNEME_EMBEDDING_BASE_URL",
            api_key="MNEME_EMBEDDING_API_KEY",
        ),
        reranker=_provider_from_env(
            settings.reranker,
            env,
            enabled="MNEME_RERANKER_ENABLED",
            provider_key="MNEME_RERANKER_PROVIDER",
            model="MNEME_RERANKER_MODEL",
            base_url="MNEME_RERANKER_BASE_URL",
            api_key="MNEME_RERANKER_API_KEY",
        ),
        llm_enrichment=_provider_from_env(
            settings.llm_enrichment,
            env,
            enabled="MNEME_LLM_ENRICHMENT_ENABLED",
            provider_key="MNEME_LLM_PROVIDER",
            model="MNEME_LLM_MODEL",
            base_url="MNEME_LLM_BASE_URL",
            api_key="MNEME_LLM_API_KEY",
        ),
    )


def _provider_from_env(
    current: ProviderSettings,
    env: Mapping[str, str],
    *,
    enabled: str,
    provider_key: str,
    model: str,
    base_url: str,
    api_key: str,
) -> ProviderSettings:
    values: dict[str, Any] = {}
    if enabled in env:
        values["enabled"] = _parse_bool(env[enabled])
    if provider_key in env:
        values["provider"] = env[provider_key]
    if model in env:
        values["model"] = env[model]
    if base_url in env:
        values["base_url"] = env[base_url]
    if api_key in env:
        values["api_key"] = env[api_key]
    return replace(current, **values)


def _parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _parse_bool(value)
    return bool(value)


def _float_tuple(value: Any, *, expected: int | None = None) -> tuple[float, ...]:
    if isinstance(value, str):
        raw_items = [item.strip() for item in value.split(",") if item.strip()]
    else:
        raw_items = list(value)
    items = tuple(float(item) for item in raw_items)
    if expected is not None and len(items) != expected:
        raise ValueError(f"Expected {expected} float values, got {len(items)}.")
    return items


def _str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        raw_items = [item.strip() for item in value.split(",")]
    else:
        raw_items = [str(item).strip() for item in value]
    return tuple(item for item in raw_items if item)


def _apply_cli(settings: Settings, overrides: Mapping[str, Any]) -> Settings:
    values = _settings_values({key: value for key, value in overrides.items() if value is not None})
    if overrides.get("routing_default_mode") is not None:
        values["routing_default_mode"] = _validate_routing_mode(overrides["routing_default_mode"])
    if overrides.get("routing_weight_debugging_dependency") is not None:
        values["routing_mode_weights"] = _patch_routing_weight(
            settings.routing_mode_weights,
            "debugging",
            "dependency",
            float(overrides["routing_weight_debugging_dependency"]),
        )
    settings = replace(settings, **values)
    return replace(
        settings,
        embeddings=_provider_from_cli(settings.embeddings, overrides, "embeddings", "embedding"),
        reranker=_provider_from_cli(settings.reranker, overrides, "reranker", "reranker"),
        llm_enrichment=_provider_from_cli(settings.llm_enrichment, overrides, "llm_enrichment", "llm"),
    )


def _provider_from_cli(
    current: ProviderSettings,
    overrides: Mapping[str, Any],
    nested_name: str,
    flat_prefix: str,
) -> ProviderSettings:
    values: dict[str, Any] = {}
    nested = overrides.get(nested_name)
    if isinstance(nested, Mapping):
        values.update({key: value for key, value in nested.items() if value is not None})

    for field in ("enabled", "provider", "model", "base_url", "api_key", "timeout_seconds", "batch_size"):
        flat_key = f"{flat_prefix}_{field}"
        if flat_key in overrides and overrides[flat_key] is not None:
            values[field] = overrides[flat_key]

    if "enabled" in values and isinstance(values["enabled"], str):
        values["enabled"] = _parse_bool(values["enabled"])
    return _provider_from_mapping(current, values)
