#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


DEFAULT_POLICY = Path("scripts/host_boundary_policy.json")


def load_policy(path: Path) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    required = {"version", "denylist", "allowlist", "exemptions"}
    unexpected = set(policy) - required
    if unexpected:
        raise SystemExit(f"{path}: unexpected keys: {', '.join(sorted(unexpected))}")
    missing = required - set(policy)
    if missing:
        raise SystemExit(f"{path}: missing required keys: {', '.join(sorted(missing))}")
    if not isinstance(policy["denylist"], list) or not policy["denylist"]:
        raise SystemExit(f"{path}: denylist must be a non-empty list")
    if not isinstance(policy["allowlist"], list):
        raise SystemExit(f"{path}: allowlist must be a list")
    if not isinstance(policy["exemptions"], list):
        raise SystemExit(f"{path}: exemptions must be a list")
    for index, exemption in enumerate(policy["exemptions"]):
        if set(exemption) != {"pattern", "reason", "scope"}:
            raise SystemExit(f"{path}: exemption {index} must contain pattern, reason, scope")
        re.compile(str(exemption["pattern"]))
    return policy


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def package_include_patterns(root: Path) -> list[str]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return []
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return (
        data.get("tool", {})
        .get("setuptools", {})
        .get("packages", {})
        .get("find", {})
        .get("include", [])
    )


def check_boundary(root: Path, policy_path: Path) -> list[str]:
    root = root.resolve()
    policy = load_policy(policy_path)
    denylist = [str(item).lower() for item in policy["denylist"]]
    # SQLite cursors are ordinary Core implementation details; path/package
    # checks still reject Cursor-specific modules through the full denylist.
    source_text_denylist = [host for host in denylist if host != "cursor"]
    errors: list[str] = []

    forbidden_paths = [
        "adapters",
        ".agents/skills",
    ]
    for item in forbidden_paths:
        path = root / item
        if path.exists():
            errors.append(f"forbidden host-adapter tree exists: {item}")

    service_dir = root / "mneme_service"
    if service_dir.exists():
        for path in sorted(service_dir.rglob("*.py")):
            rel = relpath(path, root)
            lower_rel = rel.lower()
            stem = path.stem.lower()
            if any(stem.startswith(f"{host}_") or f"/{host}_" in lower_rel for host in denylist):
                errors.append(f"forbidden host-specific module path: {rel}")
            text = path.read_text(encoding="utf-8").lower()
            for host in source_text_denylist:
                if host in text:
                    errors.append(f"forbidden host identifier '{host}' in Core source: {rel}")

    tests_dir = root / "tests"
    if tests_dir.exists():
        for path in sorted(tests_dir.glob("test_*.py")):
            name = path.name.lower()
            for host in denylist:
                if name.startswith(f"test_{host}_"):
                    errors.append(f"forbidden host-specific Core test file: {relpath(path, root)}")

    include = package_include_patterns(root)
    if include and include != ["mneme_service*"]:
        errors.append(f"unexpected package discovery include patterns: {include!r}")
    for pattern in include:
        lower = str(pattern).lower()
        if lower.startswith("adapters") or any(host in lower for host in denylist):
            errors.append(f"host-specific package discovery pattern: {pattern}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)

    errors = check_boundary(args.root, args.policy)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("core boundary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
