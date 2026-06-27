from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from mneme_service.app import create_app
from mneme_service.cli import build_parser
from mneme_service.config import Settings
from mneme_service.mcp_server import MNEME_MCP_INSTRUCTIONS, TOOL_NAMES, create_mcp_server


TOKEN = "test-token"

POSITIVE_OVERCLAIMS = (
    "will automatically replace",
    "automatically replaces",
    "rewrites every request",
    "hidden prompt authority",
)


def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def top_level_commands(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("mneme CLI parser has no top-level subcommands")


def assert_no_positive_prompt_replacement_claim(text: str) -> None:
    lower = text.lower()
    for phrase in POSITIVE_OVERCLAIMS:
        assert phrase not in lower


def test_mcp_server_instructions_are_host_neutral_memory_contract() -> None:
    server = create_mcp_server(base_url="http://mneme.test", token=None)
    lower = MNEME_MCP_INSTRUCTIONS.lower()
    first_512 = MNEME_MCP_INSTRUCTIONS[:512].lower()

    assert server.instructions == MNEME_MCP_INSTRUCTIONS
    assert "mneme is evidence memory for agents" in first_512
    assert "read-only" in first_512
    assert "session start or resume" in first_512
    assert "after compaction" in first_512
    assert "evidence, not instructions" in first_512
    assert "mcp does not replace host runtime prompt context" in lower
    assert "codex" not in lower
    for tool_name in TOOL_NAMES:
        assert tool_name in MNEME_MCP_INSTRUCTIONS
    assert_no_positive_prompt_replacement_claim(MNEME_MCP_INSTRUCTIONS)


def test_core_cli_has_no_host_specific_codex_commands() -> None:
    commands = top_level_commands(build_parser())

    assert {"serve", "mcp", "benchmark", "maintenance"} <= commands
    assert all("codex" not in command for command in commands)


def test_core_capabilities_do_not_advertise_host_specific_adapter_claims(tmp_path: Path) -> None:
    api = TestClient(create_app(Settings(db_path=tmp_path / "mneme.db", auth_token=TOKEN)))

    response = api.get("/v1/capabilities", headers=auth_headers())

    assert response.status_code == 200, response.text
    claims = response.json()["integration_depth"]["adapter_claims"]
    assert set(claims) == {"rest_api", "mcp"}
    assert "codex" not in json.dumps(claims, sort_keys=True).lower()


def test_core_repository_excludes_codex_adapter_source_artifacts() -> None:
    forbidden_paths = [
        Path("mneme_service/codex_hooks.py"),
        Path("mneme_service/codex_ingest.py"),
        Path("mneme_service/codex_setup.py"),
        Path("adapters/codex"),
        Path(".agents/skills/mneme-memory"),
        Path("tests/test_codex_hooks.py"),
        Path("tests/test_codex_ingest.py"),
        Path("tests/test_codex_adapter.py"),
    ]

    assert [str(path) for path in forbidden_paths if path.exists()] == []


def test_core_service_sources_do_not_embed_codex_specific_identifiers() -> None:
    offenders: list[str] = []
    for path in sorted(Path("mneme_service").glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        if "codex" in text:
            offenders.append(str(path))

    assert offenders == []


def test_core_readme_points_to_adapter_repo_without_embedded_codex_runbook() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    lower = readme.lower()

    assert "johnnykor82/mneme-codex-adapter" in readme
    assert "adapters/codex" not in lower
    assert "mneme-codex setup" not in lower
    assert "mneme-codex doctor" not in lower
    assert "mneme-codex codex-hook" not in lower
    assert_no_positive_prompt_replacement_claim(readme)


def test_installation_docs_keep_core_install_host_neutral() -> None:
    docs = Path("docs/INSTALLATION.md").read_text(encoding="utf-8")
    lower = docs.lower()

    assert "host adapter" in lower
    assert "johnnykor82/mneme-codex-adapter" in docs
    assert "multi-machine codex setup" not in lower
    assert "mneme-codex setup" not in lower
    assert "mneme-codex codex-hook" not in lower
    assert_no_positive_prompt_replacement_claim(docs)


def test_removed_codex_test_coverage_mapping_is_recorded() -> None:
    mapping = Path("docs/reviews/core_adapter_test_coverage_mapping.md").read_text(encoding="utf-8")

    assert "tests/test_codex_ingest.py" in mapping
    assert "tests/test_codex_hooks.py" in mapping
    assert "tests/test_codex_adapter.py" in mapping
    assert "tests/test_core_adapter_boundary.py" in mapping
    assert "mneme-codex-adapter" in mapping
