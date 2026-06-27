from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_minimal_project(root: Path) -> None:
    (root / "mneme_service").mkdir()
    (root / "mneme_service/__init__.py").write_text("", encoding="utf-8")
    (root / "mneme_service/app.py").write_text("VALUE = 'neutral'\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests/test_contract.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(
        "[tool.setuptools.packages.find]\ninclude = [\"mneme_service*\"]\n",
        encoding="utf-8",
    )


def write_policy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "version": "1",
                "denylist": ["codex", "hermes", "cursor", "openai_agents", "claude_code", "langgraph"],
                "allowlist": [],
                "exemptions": [],
            }
        ),
        encoding="utf-8",
    )


def test_core_boundary_script_passes_clean_project_and_fails_host_artifacts(tmp_path: Path) -> None:
    write_minimal_project(tmp_path)
    policy = tmp_path / "policy.json"
    write_policy(policy)

    clean = run_script("scripts/check_core_boundary.py", "--root", str(tmp_path), "--policy", str(policy))
    assert clean.returncode == 0, clean.stderr

    (tmp_path / "mneme_service/codex_hooks.py").write_text("VALUE = 'adapter'\n", encoding="utf-8")
    dirty = run_script("scripts/check_core_boundary.py", "--root", str(tmp_path), "--policy", str(policy))
    assert dirty.returncode == 1
    assert "forbidden host-specific module path" in dirty.stderr


def test_distribution_boundary_script_rejects_host_artifacts(tmp_path: Path) -> None:
    clean = tmp_path / "clean.whl"
    with zipfile.ZipFile(clean, "w") as archive:
        archive.writestr("mneme_service/app.py", "VALUE = 'neutral'\n")

    clean_result = run_script("scripts/check_distribution_boundary.py", str(clean))
    assert clean_result.returncode == 0, clean_result.stderr

    dirty = tmp_path / "dirty.whl"
    with zipfile.ZipFile(dirty, "w") as archive:
        archive.writestr("mneme_service/codex_hooks.py", "VALUE = 'adapter'\n")
    dirty_result = run_script("scripts/check_distribution_boundary.py", str(dirty))
    assert dirty_result.returncode == 1
    assert "forbidden host-specific Core module" in dirty_result.stderr

    dirty_sdist = tmp_path / "dirty.tar.gz"
    with tarfile.open(dirty_sdist, "w:gz") as archive:
        file_path = tmp_path / "test_codex_hooks.py"
        file_path.write_text("def test_adapter(): pass\n", encoding="utf-8")
        archive.add(file_path, arcname="pkg-0.1.0/tests/test_codex_hooks.py")
    sdist_result = run_script("scripts/check_distribution_boundary.py", str(dirty_sdist))
    assert sdist_result.returncode == 1
    assert "forbidden host-specific test" in sdist_result.stderr


def test_distribution_boundary_script_uses_host_policy_for_future_hosts(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "version": "1",
                "denylist": ["futurehost"],
                "allowlist": [],
                "exemptions": [],
            }
        ),
        encoding="utf-8",
    )
    dirty = tmp_path / "dirty.whl"
    with zipfile.ZipFile(dirty, "w") as archive:
        archive.writestr("mneme_service/futurehost_hooks.py", "VALUE = 'adapter'\n")

    result = run_script("scripts/check_distribution_boundary.py", "--policy", str(policy), str(dirty))

    assert result.returncode == 1
    assert "forbidden host-specific Core module" in result.stderr


def test_contract_version_script_passes_current_core_contract() -> None:
    result = run_script("scripts/check_contract_version.py")
    assert result.returncode == 0, result.stderr


def test_publication_hygiene_script_detects_findings_and_honors_allowlist(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/README.md").write_text("home /Users/openclaw/project\n", encoding="utf-8")
    (tmp_path / "mneme_service").mkdir()
    (tmp_path / "mneme_service/app.py").write_text("TOKEN=sk-real-looking-token\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.json"
    allowlist.write_text(json.dumps({"version": "1", "entries": []}), encoding="utf-8")

    dirty = run_script(
        "scripts/check_publication_hygiene.py",
        "--root",
        str(tmp_path),
        "--allowlist",
        str(allowlist),
    )
    assert dirty.returncode == 1
    assert "user_home_path" in dirty.stderr
    assert "api_key_prefix" in dirty.stderr

    allowlist.write_text(
        json.dumps(
            {
                "version": "1",
                "entries": [
                    {
                        "pattern": ".*user_home_path.*",
                        "scope": "test",
                        "reason": "fixture",
                    },
                    {
                        "pattern": ".*api_key_prefix.*",
                        "scope": "test",
                        "reason": "fixture",
                    },
                    {
                        "pattern": ".*env_assignment.*",
                        "scope": "test",
                        "reason": "fixture",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    clean = run_script(
        "scripts/check_publication_hygiene.py",
        "--root",
        str(tmp_path),
        "--allowlist",
        str(allowlist),
    )
    assert clean.returncode == 0, clean.stderr
