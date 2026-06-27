from __future__ import annotations

import tomllib
from pathlib import Path


POSITIVE_OVERCLAIMS = (
    "will automatically replace",
    "automatically replaces",
    "rewrites every codex request",
    "hidden prompt authority",
)


def assert_no_positive_prompt_replacement_claim(text: str) -> None:
    lower = text.lower()
    for phrase in POSITIVE_OVERCLAIMS:
        assert phrase not in lower


def test_core_package_discovery_excludes_host_adapters() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_find = pyproject["tool"]["setuptools"]["packages"]["find"]
    include = package_find["include"]
    checklist = Path("docs/PUBLICATION_CHECKLIST.md").read_text(encoding="utf-8").lower()

    assert include == ["mneme_service*"]
    assert all(not pattern.startswith("adapters") for pattern in include)
    assert "without host-specific adapters" in checklist
    assert "separate codex adapter repository/package" in checklist


def test_release_docs_describe_benchmark_smoke_methodology_without_savings_claims() -> None:
    docs = {
        "readme": Path("README.md").read_text(encoding="utf-8").lower(),
        "installation": Path("docs/INSTALLATION.md").read_text(encoding="utf-8").lower(),
        "testing": Path("docs/TESTING_AND_CI.md").read_text(encoding="utf-8").lower(),
        "benchmarks": Path("docs/BENCHMARKS.md").read_text(encoding="utf-8").lower(),
    }
    combined = "\n".join(docs.values())

    for text in docs.values():
        assert "mneme benchmark" in text
    assert "local fake providers" in combined
    assert "no external provider calls" in combined
    assert "comparative baseline" in combined
    assert "not proof of token or cost" in combined
    assert "not automatic prompt replacement" in combined
    assert_no_positive_prompt_replacement_claim(combined)


def test_installation_docs_describe_at_rest_storage_guidance() -> None:
    docs = Path("docs/INSTALLATION.md").read_text(encoding="utf-8").lower()

    assert "database path" in docs
    assert "0600" in docs
    assert "0700" in docs
    assert "sqlcipher" in docs
    assert "os-encrypted volume" in docs
    assert "not enterprise confidential" in docs


def test_operations_runbook_describes_restart_and_in_flight_behavior() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [Path("docs/INSTALLATION.md"), Path("docs/TESTING_AND_CI.md")]
    ).lower()

    assert "operations runbook" in docs
    assert "config changes require restart" in docs
    assert "in-flight requests" in docs
    assert "idempotency-key" in docs
    assert "retryable=true" in docs
    assert "structured logs" in docs
    assert "request id" in docs
    assert "trace id" in docs


def test_installation_docs_describe_migration_backup_release_notes() -> None:
    docs = Path("docs/INSTALLATION.md").read_text(encoding="utf-8").lower()

    assert "migration and release notes" in docs
    assert "migration impacts" in docs
    assert "--backup-before-migrate" in docs
    assert "--no-backup-before-migrate" in docs
    assert "destructive migration" in docs
    assert "tested python versions" in docs


def test_publication_docs_require_real_embedding_and_reranker_smoke() -> None:
    paths = [
        Path("task_plan.md"),
        Path("findings.md"),
        Path("docs/PUBLICATION_CHECKLIST.md"),
        Path("docs/PROVIDER_CONFIGURATION.md"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()

    assert "require_embeddings" in combined
    assert "requires_embeddings" in combined
    assert "dogfood/public-readiness" in combined
    assert "semantic memory requires embeddings" in combined
    assert "embedding_items > 0" in combined
    assert "embedding_failures == 0" in combined
    assert "reranker_calls > 0" in combined
    assert "reranker_failures == 0" in combined
    assert "keyword-only" in combined


def test_publication_docs_do_not_overclaim_llm_answer_synthesis() -> None:
    paths = [
        Path("task_plan.md"),
        Path("findings.md"),
        Path("docs/PUBLICATION_CHECKLIST.md"),
        Path("docs/PROVIDER_CONFIGURATION.md"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()

    assert "structured llm enrichment" in combined
    assert "not a separate natural-language answer-synthesis endpoint" in combined
    assert "do not claim answer synthesis" in combined
