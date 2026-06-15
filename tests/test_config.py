from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.cli import build_parser, settings_from_serve_args
from mneme_service.config import ProviderSettings, Settings, load_settings


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
        "provider": "openai_compatible",
        "model": "text-embedding-3-small",
        "base_url": "https://example.test/v1",
        "api_key_configured": True,
    }
    assert "sk-test-secret" not in str(summary)


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
    assert body["providers"]["reranker"]["enabled"] is False
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
            "--memory-access-hint-enabled",
        ]
    )

    settings = settings_from_serve_args(args)

    assert settings.router_min_candidates == 7
    assert settings.centroid_window == 55
    assert settings.enricher_max_tokens == 777
    assert settings.memory_access_hint_enabled is True


def test_example_config_is_parseable_and_contains_no_real_secrets() -> None:
    example = Path("mneme.example.toml")

    text = example.read_text(encoding="utf-8")
    settings = load_settings(config_path=example, env={})

    assert settings.embeddings.provider == "openai_compatible"
    assert settings.embeddings.model
    assert "sk-" not in text
    assert "real-token" not in text.lower()
