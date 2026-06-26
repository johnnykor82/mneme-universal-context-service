from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.cli import build_parser, main, settings_from_serve_args, validate_serve_security
from mneme_service.config import ProviderHealth, ProviderSettings, Settings, StaticTokenSettings, load_settings
from mneme_service.security import authenticate_bearer
from mneme_service.storage import Store


TOKEN = "test-token"


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def test_settings_precedence_is_cli_then_env_then_config_then_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[daemon]
db_path = "from-file.db"
host = "0.0.0.0"
port = 7777
auth_token = "file-token"
max_batch_events = 12

[providers.embeddings]
enabled = true
provider = "file-embedding-provider"
model = "file-embedding-model"
base_url = "http://file-embedding.local/v1"
api_key = "file-embedding-secret"
timeout_seconds = 11.5
batch_size = 7

[providers.reranker]
enabled = true
provider = "file-reranker-provider"
model = "file-reranker-model"
base_url = "http://file-reranker.local/v1"

[providers.llm_enrichment]
enabled = false
provider = "file-llm-provider"
model = "file-llm-model"
base_url = "http://file-llm.local/v1"
""".strip(),
        encoding="utf-8",
    )

    env = {
        "MNEME_PORT": "8888",
        "MNEME_EMBEDDING_MODEL": "env-embedding-model",
        "MNEME_EMBEDDING_API_KEY": "env-embedding-secret",
        "MNEME_RERANKER_ENABLED": "false",
        "MNEME_LLM_ENRICHMENT_ENABLED": "true",
    }

    settings = load_settings(
        config_path=config_path,
        env=env,
        cli_overrides={
            "port": 9999,
            "embeddings": {"model": "cli-embedding-model"},
        },
    )

    assert settings.port == 9999
    assert settings.host == "0.0.0.0"
    assert settings.auth_token == "file-token"
    assert settings.max_batch_events == 12
    assert settings.embeddings.enabled is True
    assert settings.embeddings.provider == "file-embedding-provider"
    assert settings.embeddings.model == "cli-embedding-model"
    assert settings.embeddings.base_url == "http://file-embedding.local/v1"
    assert settings.embeddings.api_key == "env-embedding-secret"
    assert settings.embeddings.timeout_seconds == 11.5
    assert settings.embeddings.batch_size == 7
    assert settings.reranker.enabled is False
    assert settings.llm_enrichment.enabled is True
    assert settings.llm_enrichment.provider == "file-llm-provider"


def test_loads_v0_foundation_config_sections(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[daemon]
strict_cost_mode = true
max_blob_bytes = 2048
max_session_id_length = 128
max_batch_total_blob_bytes = 3000
max_multipart_metadata_overhead_bytes = 500
max_multipart_transaction_bytes = 4000
max_multipart_transaction_ms = 1500
max_export_blob_inline_bytes = 0
max_export_session_memory_bytes = 9000
idempotency_key_min_retention_seconds = 123
max_writer_queue_depth = 42
startup_integrity_check = true
metrics_enabled = true
metrics_format = "prometheus"

[maintenance]
retention_sweep_interval_seconds = 60
retention_sweep_on_startup = false
retention_sweep_on_session_close = true
retention_force_active_cleanup = true
vacuum_max_duration_ms = 250
checkpoint_max_pages = 333

[maintenance.reindex]
enqueue_when_provider_unavailable = true
foreground_write_priority = false
max_job_events = 444
max_events_per_transaction = 5
yield_between_transactions_ms = 25
provider_wait_timeout_seconds = 600
provider_max_requests_per_minute = 12
provider_circuit_breaker_min_calls = 4
provider_circuit_breaker_failure_ratio = 0.75
provider_circuit_breaker_open_seconds = 9
provider_circuit_breaker_half_open_requests = 2
provider_recovery_ramp_initial_requests_per_minute = 6

[retrieval.graph]
importance_depth_decay = 0.25
max_traversal_steps = 33
max_frontier_size = 22
max_branching_factor = 11

[indexing]
max_redaction_time_ms = 111
binary_blob_extractor_policy = "DISABLED"

[audit]
forensic_retention_days = 45
anonymize_deleted_session_audit = false

[auth]
project_isolation_key = "repo-a"
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_path=config_path, env={})

    assert settings.strict_cost_mode is True
    assert settings.max_blob_bytes == 2048
    assert settings.max_session_id_length == 128
    assert settings.max_batch_total_blob_bytes == 3000
    assert settings.max_multipart_metadata_overhead_bytes == 500
    assert settings.max_multipart_transaction_bytes == 4000
    assert settings.max_multipart_transaction_ms == 1500
    assert settings.max_export_session_memory_bytes == 9000
    assert settings.idempotency_key_min_retention_seconds == 123
    assert settings.max_writer_queue_depth == 42
    assert settings.startup_integrity_check is True
    assert settings.metrics_enabled is True
    assert settings.metrics_format == "prometheus"
    assert settings.retention_sweep_interval_seconds == 60
    assert settings.retention_sweep_on_startup is False
    assert settings.retention_force_active_cleanup is True
    assert settings.vacuum_max_duration_ms == 250
    assert settings.checkpoint_max_pages == 333
    assert settings.reindex_enqueue_when_provider_unavailable is True
    assert settings.reindex_foreground_write_priority is False
    assert settings.reindex_max_job_events == 444
    assert settings.reindex_max_events_per_transaction == 5
    assert settings.reindex_provider_circuit_breaker_failure_ratio == 0.75
    assert settings.graph_importance_depth_decay == 0.25
    assert settings.graph_max_traversal_steps == 33
    assert settings.graph_max_frontier_size == 22
    assert settings.graph_max_branching_factor == 11
    assert settings.max_redaction_time_ms == 111
    assert settings.binary_blob_extractor_policy == "DISABLED"
    assert settings.audit_forensic_retention_days == 45
    assert settings.audit_anonymize_deleted_session_audit is False
    assert settings.project_isolation_key == "repo-a"


def test_later_phase_config_parity_env_precedence(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[daemon]
max_session_id_length = 16
strict_cost_mode = false
max_blob_bytes = 2048
startup_integrity_check = true
metrics_enabled = true
metrics_format = "prometheus"
max_tool_result_events = 4

[maintenance]
retention_sweep_interval_seconds = 10
retention_sweep_on_startup = true
vacuum_max_duration_ms = 100
checkpoint_max_pages = 7

[maintenance.reindex]
reindex_max_events_per_transaction = 2
reindex_provider_circuit_breaker_failure_ratio = 0.2
reindex_provider_recovery_ramp_initial_requests_per_minute = 6

[audit]
forensic_retention_days = 30
anonymize_deleted_session_audit = true
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env={
            "MNEME_STRICT_COST_MODE": "true",
            "MNEME_MAX_SESSION_ID_LENGTH": "24",
            "MNEME_MAX_BLOB_BYTES": "333",
            "MNEME_STARTUP_INTEGRITY_CHECK": "false",
            "MNEME_METRICS_ENABLED": "false",
            "MNEME_METRICS_FORMAT": "prometheus",
            "MNEME_MAX_REDACTION_TIME_MS": "123",
            "MNEME_RETENTION_FORCE_ACTIVE_CLEANUP": "true",
            "MNEME_RETENTION_SWEEP_INTERVAL_SECONDS": "20",
            "MNEME_REINDEX_MAX_JOB_EVENTS": "9",
            "MNEME_REINDEX_MAX_EVENTS_PER_TRANSACTION": "2",
            "MNEME_REINDEX_PROVIDER_RECOVERY_RAMP_INITIAL_REQUESTS_PER_MINUTE": "6",
            "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_OPEN_SECONDS": "11",
            "MNEME_REINDEX_PROVIDER_CIRCUIT_BREAKER_FAILURE_RATIO": "0.77",
            "MNEME_AUDIT_FORENSIC_RETENTION_DAYS": "45",
            "MNEME_AUDIT_ANONYMIZE_DELETED_SESSION_AUDIT": "false",
        },
        cli_overrides={"strict_cost_mode": False},
    )

    assert settings.strict_cost_mode is False
    assert settings.max_session_id_length == 24
    assert settings.max_blob_bytes == 333
    assert settings.startup_integrity_check is False
    assert settings.metrics_enabled is False
    assert settings.metrics_format == "prometheus"
    assert settings.max_redaction_time_ms == 123
    assert settings.retention_force_active_cleanup is True
    assert settings.retention_sweep_interval_seconds == 20
    assert settings.reindex_max_job_events == 9
    assert settings.reindex_max_events_per_transaction == 2
    assert settings.reindex_provider_recovery_ramp_initial_requests_per_minute == 6
    assert settings.reindex_provider_circuit_breaker_failure_ratio == 0.77
    assert settings.reindex_provider_circuit_breaker_open_seconds == 11
    assert settings.audit_forensic_retention_days == 45
    assert settings.audit_anonymize_deleted_session_audit is False


def test_routing_config_from_toml_supported(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[retrieval.routing]
default_mode = "reasoning"

[retrieval.routing.weights.general]
semantic_similarity = 0.40
recency = 0.20
dependency = 0.30
type_weight = 0.10

[retrieval.routing.weights.reasoning]
semantic_similarity = 0.35
recency = 0.15
dependency = 0.40
type_weight = 0.10
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_path=config_path, env={})

    assert settings.routing_default_mode == "reasoning"
    assert settings.routing_mode_weights["reasoning"]["dependency"] == 0.40
    assert settings.routing_mode_weights["general"]["type_weight"] == 0.10
    assert settings.routing_mode_weights["debugging"]["dependency"] == 0.10


def test_routing_cli_overrides_default_mode_and_weight(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[retrieval.routing]
default_mode = "reasoning"

[retrieval.routing.weights.debugging]
semantic_similarity = 0.30
recency = 0.30
dependency = 0.39
type_weight = 0.0
""".strip(),
        encoding="utf-8",
    )

    parser = build_parser()
    args = parser.parse_args(
        [
            "serve",
            "--config",
            str(config_path),
            "--routing-default-mode",
            "factual",
            "--routing-weight-debugging-dependency",
            "0.40",
        ]
    )

    settings = settings_from_serve_args(args)

    assert settings.routing_default_mode == "factual"
    assert settings.routing_mode_weights["debugging"]["dependency"] == 0.40


def test_routing_env_override_sets_default_mode_and_dependency_weight(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[retrieval.routing]
default_mode = "reasoning"

[retrieval.routing.weights.debugging]
semantic_similarity = 0.30
recency = 0.30
dependency = 0.39
type_weight = 0.0
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env={
            "MNEME_ROUTING_DEFAULT_MODE": "general",
            "MNEME_ROUTING_WEIGHT_DEBUGGING_DEPENDENCY": "0.40",
        },
    )

    assert settings.routing_default_mode == "general"
    assert settings.routing_mode_weights["debugging"]["dependency"] == 0.40


def test_invalid_routing_config_rejects_bad_modes_and_weights(tmp_path: Path) -> None:
    invalid_missing_keys = tmp_path / "mneme.toml"
    invalid_missing_keys.write_text(
        """
[retrieval.routing]
default_mode = "missing"

[retrieval.routing.weights.general]
semantic_similarity = 0.40
recency = 0.20
dependency = 0.30
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="routing_default_mode"):
        load_settings(config_path=invalid_missing_keys, env={})

    invalid_negative = tmp_path / "mneme-negative.toml"
    invalid_negative.write_text(
        """
[retrieval.routing]
default_mode = "general"

[retrieval.routing.weights.general]
semantic_similarity = 0.40
recency = -0.20
dependency = 0.30
type_weight = 0.50
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="non-negative"):
        load_settings(config_path=invalid_negative, env={})

    invalid_sum = tmp_path / "mneme-sum.toml"
    invalid_sum.write_text(
        """
[retrieval.routing]
default_mode = "general"

[retrieval.routing.weights.general]
semantic_similarity = 0.80
recency = 0.20
dependency = 0.10
type_weight = 0.10
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sum to 1.0"):
        load_settings(config_path=invalid_sum, env={})


def test_audit_disabled_only_by_explicit_test_daemon_config(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[audit]
mode = "DISABLED_TEST_ONLY"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="DISABLED_TEST_ONLY"):
        load_settings(config_path=config_path, env={})

    settings = load_settings(
        config_path=config_path,
        env={"MNEME_ALLOW_UNAUDITED_TOOLS_FOR_TESTS": "true"},
    )

    assert settings.audit_mode == "DISABLED_TEST_ONLY"
    assert settings.allow_unaudited_tools_for_tests is True


def test_auth_token_file_static_registry_and_owner_fallback(tmp_path: Path) -> None:
    owner_token_file = tmp_path / "owner.token"
    owner_token_file.write_text("owner-file-token\n", encoding="utf-8")
    owner_token_file.chmod(0o600)
    scoped_token_file = tmp_path / "scoped.token"
    scoped_token_file.write_text("scoped-file-token\n", encoding="utf-8")
    scoped_token_file.chmod(0o600)
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        f"""
[auth]
token_file = "{owner_token_file}"

[[auth.static_tokens]]
name = "codex-repo-a"
token_file = "{scoped_token_file}"
project_scopes = ["repo-a"]
role = "ADAPTER"
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(config_path=config_path, env={})

    assert settings.auth_token == "owner-file-token"
    assert settings.auth_token_file == owner_token_file
    assert settings.static_tokens == (
        StaticTokenSettings(
            name="codex-repo-a",
            token="scoped-file-token",
            token_file=scoped_token_file,
            project_scopes=("repo-a",),
            role="ADAPTER",
        ),
    )
    owner = authenticate_bearer("Bearer owner-file-token", settings)
    assert owner is not None
    assert owner.as_audit_principal() == {
        "name": "local-owner",
        "role": "OWNER",
        "project_scopes": ["*"],
    }
    scoped = authenticate_bearer("Bearer scoped-file-token", settings)
    assert scoped is not None
    assert scoped.as_audit_principal() == {
        "name": "codex-repo-a",
        "role": "ADAPTER",
        "project_scopes": ["repo-a"],
    }


def test_auth_token_file_rejects_group_or_world_readable_permissions(tmp_path: Path) -> None:
    token_file = tmp_path / "owner.token"
    token_file.write_text("owner-file-token\n", encoding="utf-8")
    token_file.chmod(0o644)
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        f"""
[auth]
token_file = "{token_file}"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="owner-readable"):
        load_settings(config_path=config_path, env={})


def test_static_token_file_rejects_group_or_world_readable_permissions(tmp_path: Path) -> None:
    token_file = tmp_path / "scoped.token"
    token_file.write_text("scoped-file-token\n", encoding="utf-8")
    token_file.chmod(0o640)
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        f"""
[auth]
auth_token = "owner-token"

[[auth.static_tokens]]
name = "codex-repo-a"
token_file = "{token_file}"
project_scopes = ["repo-a"]
role = "ADAPTER"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="owner-readable"):
        load_settings(config_path=config_path, env={})


@pytest.mark.parametrize(
    ("config_text", "expected"),
    [
        ("[daemon]\nmax_session_id_length = 0", "max_session_id_length"),
        (
            """
[daemon]
max_batch_total_blob_bytes = 3000
max_multipart_metadata_overhead_bytes = 500
max_multipart_transaction_bytes = 3499
""",
            "max_multipart_transaction_bytes",
        ),
        ("[retrieval.graph]\nimportance_depth_decay = 1.5", "importance_depth_decay"),
        (
            """
[indexing]
tool_output_compress_threshold_tokens = 100
tool_output_summary_tokens = 100
""",
            "tool_output_summary_tokens",
        ),
        ("[indexing]\nmax_redaction_time_ms = 0", "max_redaction_time_ms"),
        ("[indexing]\nbinary_blob_extractor_policy = \"AUTO\"", "binary_blob_extractor_policy"),
    ],
)
def test_invalid_v0_foundation_config_fails_startup(
    tmp_path: Path,
    config_text: str,
    expected: str,
) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(config_text.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=expected):
        load_settings(config_path=config_path, env={})


def test_provider_summary_is_secret_safe() -> None:
    provider = ProviderSettings(
        enabled=True,
        provider="openai_compatible",
        model="text-embedding-3-small",
        base_url="https://example.test/v1",
        api_key="sk-test-secret",
    )

    summary = provider.summary()

    assert summary == {
        "enabled": True,
        "configured": True,
        "available": True,
        "provider": "openai_compatible",
        "model": "text-embedding-3-small",
        "base_url": "https://example.test/v1",
        "api_key_configured": True,
        "last_health": "UNKNOWN",
    }
    assert "sk-test-secret" not in str(summary)


def test_provider_summary_tracks_runtime_health_from_success_and_failure() -> None:
    provider = ProviderSettings(
        enabled=True,
        provider="openai_compatible",
        model="text-embedding-3-small",
        base_url="https://example.test/v1",
        api_key="sk-test-secret",
    )

    healthy = provider.summary(
        health=ProviderHealth(
            status="AVAILABLE",
            checked_at_ms=1234,
            failure_count=0,
            last_error_code=None,
        )
    )
    degraded = provider.summary(
        health=ProviderHealth(
            status="DEGRADED",
            checked_at_ms=5678,
            failure_count=2,
            last_error_code="EMBEDDINGS_UNAVAILABLE",
        )
    )

    assert healthy["last_health"] == {
        "status": "AVAILABLE",
        "checked_at_ms": 1234,
        "failure_count": 0,
        "last_error_code": None,
    }
    assert degraded["last_health"] == {
        "status": "DEGRADED",
        "checked_at_ms": 5678,
        "failure_count": 2,
        "last_error_code": "EMBEDDINGS_UNAVAILABLE",
    }
    assert "sk-test-secret" not in str(healthy)
    assert "sk-test-secret" not in str(degraded)


def test_enabled_http_provider_without_api_key_fails_startup(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        embeddings=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-3-small",
            base_url="https://embedding.example.test/v1",
        ),
    )

    with pytest.raises(RuntimeError, match="embeddings provider requires an API key"):
        create_app(settings)


def test_capabilities_reflect_provider_configuration_without_leaking_secrets(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        embeddings=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="text-embedding-3-small",
            base_url="https://embedding.example.test/v1",
            api_key="sk-embedding-secret",
        ),
        reranker=ProviderSettings(
            enabled=False,
            provider="jina",
            model="jina-reranker-v2",
            base_url="https://rerank.example.test/v1",
            api_key="sk-reranker-secret",
        ),
        llm_enrichment=ProviderSettings(
            enabled=True,
            provider="openai_compatible",
            model="gpt-test",
            base_url="https://llm.example.test/v1",
            api_key="sk-llm-secret",
        ),
    )
    api = TestClient(create_app(settings))

    response = api.get("/v1/capabilities", headers=auth_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["supports_embeddings"] is True
    assert body["requires_embeddings"] is False
    assert body["supports_reranking"] is False
    assert body["supports_llm_enrichment"] is True
    assert body["providers"]["embeddings"]["api_key_configured"] is True
    assert body["providers"]["embeddings"]["available"] is True
    assert body["providers"]["reranker"]["enabled"] is False
    assert body["providers"]["reranker"]["available"] is False
    assert "sk-embedding-secret" not in str(body)
    assert "sk-reranker-secret" not in str(body)
    assert "sk-llm-secret" not in str(body)


def test_required_embeddings_fail_fast_when_provider_is_unavailable(tmp_path: Path) -> None:
    settings = Settings(
        db_path=tmp_path / "mneme.db",
        auth_token=TOKEN,
        require_embeddings=True,
        embeddings=ProviderSettings(enabled=False),
    )

    with pytest.raises(RuntimeError, match="Embeddings are required"):
        create_app(settings)


def test_required_embeddings_setting_comes_from_config_env_and_cli(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[daemon]
require_embeddings = false
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env={"MNEME_REQUIRE_EMBEDDINGS": "true"},
        cli_overrides={"require_embeddings": False},
    )

    assert settings.require_embeddings is False


def test_max_writer_queue_depth_comes_from_config_env_and_cli(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[daemon]
max_writer_queue_depth = 17
""".strip(),
        encoding="utf-8",
    )

    env_settings = load_settings(
        config_path=config_path,
        env={"MNEME_MAX_WRITER_QUEUE_DEPTH": "23"},
    )
    settings = load_settings(
        config_path=config_path,
        env={"MNEME_MAX_WRITER_QUEUE_DEPTH": "23"},
        cli_overrides={"max_writer_queue_depth": 31},
    )

    assert env_settings.max_writer_queue_depth == 23
    assert settings.max_writer_queue_depth == 31


def test_loads_hermes_mneme_parity_knobs_from_config_env_and_cli(tmp_path: Path) -> None:
    config_path = tmp_path / "mneme.toml"
    config_path.write_text(
        """
[budget]
active_window_tokens = 60000
context_window_usage_percent = 0.66
protected_tail_turns = 32
state_budget_ratio = 0.06
retrieved_budget_ratio = 0.31
protected_tail_ratio = 0.52
pass_through_overhead_initial = 12000

[segmentation]
enabled = true
drift_threshold = 0.42
drift_weights = [0.5, 0.25, 0.25]
centroid_cache_size = 77
centroid_window = 123

[retrieval]
router_top_k = 50
router_min_candidates = 9
dependency_max_depth = 5
dependency_decay = 0.55
reranker_top_k = 20

[enrichment]
every_n_turns = 4
on_segment_boundary = false
max_history_turns = 8
timeout_seconds = 22.5
max_tokens = 900

[embedding_index]
tool_output_compress_threshold_tokens = 700
tool_output_summary_tokens = 140
reindex_on_model_change = true

[memory]
memory_access_hint_enabled = false
goal_trail_size = 5
checkpoint_after_n_memory_calls = 3
memory_tool_names = ["context_search", "fetch_event"]
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env={
            "MNEME_ROUTER_MIN_CANDIDATES": "11",
            "MNEME_CENTROID_WINDOW": "222",
            "MNEME_ENRICHER_MAX_TOKENS": "1000",
        },
        cli_overrides={
            "dependency_decay": 0.7,
            "memory_access_hint_enabled": True,
        },
    )

    assert settings.active_window_tokens == 60000
    assert settings.context_window_usage_percent == 0.66
    assert settings.protected_tail_turns == 32
    assert settings.state_budget_ratio == 0.06
    assert settings.retrieved_budget_ratio == 0.31
    assert settings.protected_tail_ratio == 0.52
    assert settings.pass_through_overhead_initial == 12000
    assert settings.segmentation_enabled is True
    assert settings.drift_threshold == 0.42
    assert settings.drift_weights == (0.5, 0.25, 0.25)
    assert settings.centroid_cache_size == 77
    assert settings.centroid_window == 222
    assert settings.router_top_k == 50
    assert settings.router_min_candidates == 11
    assert settings.dependency_max_depth == 5
    assert settings.dependency_decay == 0.7
    assert settings.reranker_top_k == 20
    assert settings.enricher_every_n_turns == 4
    assert settings.enricher_on_segment_boundary is False
    assert settings.enricher_max_history_turns == 8
    assert settings.enricher_timeout_seconds == 22.5
    assert settings.enricher_max_tokens == 1000
    assert settings.tool_output_compress_threshold_tokens == 700
    assert settings.tool_output_summary_tokens == 140
    assert settings.reindex_on_model_change is True
    assert settings.memory_access_hint_enabled is True
    assert settings.goal_trail_size == 5
    assert settings.checkpoint_after_n_memory_calls == 3
    assert settings.memory_tool_names == ("context_search", "fetch_event")


def test_serve_cli_accepts_core_parity_knobs(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "serve",
            "--db",
            str(tmp_path / "mneme.db"),
            "--router-min-candidates",
            "7",
            "--centroid-window",
            "55",
            "--enricher-max-tokens",
            "777",
            "--max-writer-queue-depth",
            "19",
            "--memory-access-hint-enabled",
        ]
    )

    settings = settings_from_serve_args(args)

    assert settings.router_min_candidates == 7
    assert settings.centroid_window == 55
    assert settings.enricher_max_tokens == 777
    assert settings.max_writer_queue_depth == 19
    assert settings.memory_access_hint_enabled is True


def test_serve_cli_accepts_later_phase_config(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "serve",
            "--db",
            str(tmp_path / "mneme.db"),
            "--strict-cost-mode",
            "--max-blob-bytes",
            "123456",
            "--max-session-id-length",
            "88",
            "--max-batch-total-blob-bytes",
            "222222",
            "--max-multipart-metadata-overhead-bytes",
            "5000",
            "--max-multipart-transaction-bytes",
            "23000000",
            "--max-multipart-transaction-ms",
            "2500",
            "--max-export-session-memory-bytes",
            "8888",
            "--idempotency-key-min-retention-seconds",
            "901",
            "--no-startup-integrity-check",
            "--metrics-disabled",
            "--metrics-format",
            "prometheus",
            "--retention-sweep-interval-seconds",
            "19",
            "--no-retention-sweep-on-startup",
            "--retention-sweep-on-session-close",
            "--retention-force-active-cleanup",
            "--vacuum-max-duration-ms",
            "1250",
            "--checkpoint-max-pages",
            "77",
            "--reindex-enqueue-when-provider-unavailable",
            "--no-reindex-foreground-write-priority",
            "--reindex-max-job-events",
            "3333",
            "--reindex-max-events-per-transaction",
            "12",
            "--reindex-yield-between-transactions-ms",
            "25",
            "--reindex-provider-wait-timeout-seconds",
            "100",
            "--reindex-provider-max-requests-per-minute",
            "19",
            "--reindex-provider-circuit-breaker-min-calls",
            "8",
            "--reindex-provider-circuit-breaker-failure-ratio",
            "0.31",
            "--reindex-provider-circuit-breaker-open-seconds",
            "70",
            "--reindex-provider-circuit-breaker-half-open-requests",
            "3",
            "--reindex-provider-recovery-ramp-initial-requests-per-minute",
            "11",
            "--max-tool-result-events",
            "66",
            "--max-redaction-time-ms",
            "250",
            "--audit-forensic-retention-days",
            "99",
            "--no-audit-anonymize-deleted-session-audit",
        ]
    )

    settings = settings_from_serve_args(args)

    assert settings.strict_cost_mode is True
    assert settings.max_blob_bytes == 123456
    assert settings.max_session_id_length == 88
    assert settings.max_batch_total_blob_bytes == 222222
    assert settings.max_multipart_metadata_overhead_bytes == 5000
    assert settings.max_multipart_transaction_bytes == 23000000
    assert settings.max_multipart_transaction_ms == 2500
    assert settings.max_export_session_memory_bytes == 8888
    assert settings.idempotency_key_min_retention_seconds == 901
    assert settings.startup_integrity_check is False
    assert settings.metrics_enabled is False
    assert settings.metrics_format == "prometheus"
    assert settings.retention_sweep_interval_seconds == 19
    assert settings.retention_sweep_on_startup is False
    assert settings.retention_sweep_on_session_close is True
    assert settings.retention_force_active_cleanup is True
    assert settings.vacuum_max_duration_ms == 1250
    assert settings.checkpoint_max_pages == 77
    assert settings.reindex_enqueue_when_provider_unavailable is True
    assert settings.reindex_foreground_write_priority is False
    assert settings.reindex_max_job_events == 3333
    assert settings.reindex_max_events_per_transaction == 12
    assert settings.reindex_yield_between_transactions_ms == 25
    assert settings.reindex_provider_wait_timeout_seconds == 100
    assert settings.reindex_provider_max_requests_per_minute == 19
    assert settings.reindex_provider_circuit_breaker_min_calls == 8
    assert settings.reindex_provider_circuit_breaker_failure_ratio == 0.31
    assert settings.reindex_provider_circuit_breaker_open_seconds == 70
    assert settings.reindex_provider_circuit_breaker_half_open_requests == 3
    assert settings.reindex_provider_recovery_ramp_initial_requests_per_minute == 11
    assert settings.max_tool_result_events == 66
    assert settings.max_redaction_time_ms == 250
    assert settings.audit_forensic_retention_days == 99
    assert settings.audit_anonymize_deleted_session_audit is False


def test_maintenance_backup_restore_cli_parses_paths(tmp_path: Path) -> None:
    parser = build_parser()

    backup = parser.parse_args(
        [
            "maintenance",
            "backup",
            "--db",
            str(tmp_path / "mneme.db"),
            "--output",
            str(tmp_path / "backup.db"),
        ]
    )
    restore = parser.parse_args(
        [
            "maintenance",
            "restore",
            "--backup",
            str(tmp_path / "backup.db"),
            "--target",
            str(tmp_path / "restored.db"),
        ]
    )

    assert backup.action == "backup"
    assert backup.db == tmp_path / "mneme.db"
    assert backup.output == tmp_path / "backup.db"
    assert restore.action == "restore"
    assert restore.backup == tmp_path / "backup.db"
    assert restore.target == tmp_path / "restored.db"


def test_serve_cli_accepts_destructive_migration_backup_controls(tmp_path: Path) -> None:
    parser = build_parser()
    backup_path = tmp_path / "before-migrate.db"
    args = parser.parse_args(
        [
            "serve",
            "--db",
            str(tmp_path / "mneme.db"),
            "--backup-before-migrate",
            str(backup_path),
            "--no-backup-before-migrate",
        ]
    )

    settings = settings_from_serve_args(args)

    assert settings.backup_before_migrate == backup_path
    assert settings.no_backup_before_migrate is True


def test_maintenance_blob_gc_cli_parses_and_runs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    db_path = tmp_path / "mneme.db"
    store = Store(db_path)
    blob = store.put_blob(
        session_id="session-cli-gc",
        project_isolation_key="project-cli-gc",
        content=b"orphan",
        media_type="application/octet-stream",
    )

    parsed = parser.parse_args(
        [
            "maintenance",
            "blob-gc",
            "--db",
            str(db_path),
            "--project-isolation-key",
            "project-cli-gc",
            "--execute",
        ]
    )
    main(
        [
            "maintenance",
            "blob-gc",
            "--db",
            str(db_path),
            "--project-isolation-key",
            "project-cli-gc",
            "--execute",
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert parsed.action == "blob-gc"
    assert parsed.db == db_path
    assert parsed.project_isolation_key == "project-cli-gc"
    assert parsed.dry_run is False
    assert output["candidate_count"] == 1
    assert output["deleted_count"] == 1
    assert output["dry_run"] is False
    assert store.get_blob_metadata(blob["blob_id"]) is None


def test_serve_cli_rejects_insecure_dev_on_non_loopback(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "serve",
            "--db",
            str(tmp_path / "mneme.db"),
            "--host",
            "0.0.0.0",
            "--insecure-dev",
        ]
    )
    settings = settings_from_serve_args(args)

    with pytest.raises(SystemExit, match="Refusing --insecure-dev on non-loopback bind"):
        validate_serve_security(settings)


def test_safe_docs_and_generated_templates_do_not_recommend_token_argv() -> None:
    checked_paths = [
        Path("README.md"),
        Path("docs/INSTALLATION.md"),
        Path("adapters/codex/MNEME_CODEX_MCP_USAGE.md"),
        Path("adapters/codex/MNEME_CODEX_INGEST_USAGE.md"),
        Path("adapters/codex/CODEX_DOGFOOD_RESTART_SETUP.md"),
        Path("mneme_service/codex_setup.py"),
        Path("mneme_service/codex_hooks.py"),
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in checked_paths)

    assert '--token "$MNEME_AUTH_TOKEN"' not in combined
    assert '--token "${token_env}"' not in combined


def test_example_config_is_parseable_and_contains_no_real_secrets() -> None:
    example = Path("mneme.example.toml")

    text = example.read_text(encoding="utf-8")
    settings = load_settings(config_path=example, env={})

    assert settings.embeddings.provider == "openai_compatible"
    assert settings.embeddings.model
    assert "sk-" not in text
    assert "real-token" not in text.lower()
