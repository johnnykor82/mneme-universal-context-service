from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping


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

    def summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "configured": self.configured,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
        }


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("mneme.db")
    auth_token: str | None = None
    insecure_dev: bool = False
    host: str = "127.0.0.1"
    port: int = 8765
    require_embeddings: bool = False
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
    max_tool_result_events: int = 50
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
    return settings


def _optional_path(value: str | None) -> Path | None:
    if not value:
        return None
    return Path(value)


def _apply_config_file(settings: Settings, config_path: Path) -> Settings:
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    daemon = raw.get("daemon", {})
    limits = raw.get("limits", {})
    providers = raw.get("providers", {})

    values: dict[str, Any] = {}
    for source in (daemon, limits, _parity_config_values(raw)):
        values.update(_settings_values(source))

    settings = replace(settings, **values)
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
    if "insecure_dev" in source:
        values["insecure_dev"] = _boolish(source["insecure_dev"])
    if "host" in source:
        values["host"] = str(source["host"])
    if "port" in source:
        values["port"] = int(source["port"])
    if "require_embeddings" in source:
        values["require_embeddings"] = _boolish(source["require_embeddings"])
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
    if "max_tool_result_events" in source:
        values["max_tool_result_events"] = int(source["max_tool_result_events"])
    return values


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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _apply_env(settings: Settings, env: Mapping[str, str]) -> Settings:
    values: dict[str, Any] = {}
    if "MNEME_DB_PATH" in env:
        values["db_path"] = Path(env["MNEME_DB_PATH"])
    if "MNEME_AUTH_TOKEN" in env:
        values["auth_token"] = env["MNEME_AUTH_TOKEN"]
    if "MNEME_INSECURE_DEV" in env:
        values["insecure_dev"] = _parse_bool(env["MNEME_INSECURE_DEV"])
    if "MNEME_HOST" in env:
        values["host"] = env["MNEME_HOST"]
    if "MNEME_PORT" in env:
        values["port"] = int(env["MNEME_PORT"])
    if "MNEME_REQUIRE_EMBEDDINGS" in env:
        values["require_embeddings"] = _parse_bool(env["MNEME_REQUIRE_EMBEDDINGS"])
    if "MNEME_MAX_BATCH_EVENTS" in env:
        values["max_batch_events"] = int(env["MNEME_MAX_BATCH_EVENTS"])
    if "MNEME_MAX_EVENT_CONTENT_BYTES" in env:
        values["max_event_content_bytes"] = int(env["MNEME_MAX_EVENT_CONTENT_BYTES"])
    if "MNEME_MAX_TOOL_RESULT_EVENTS" in env:
        values["max_tool_result_events"] = int(env["MNEME_MAX_TOOL_RESULT_EVENTS"])
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
