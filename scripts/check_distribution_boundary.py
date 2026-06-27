#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tarfile
import zipfile
from pathlib import Path


DEFAULT_POLICY = Path("scripts/host_boundary_policy.json")
FORBIDDEN_PREFIXES = ("adapters/", ".agents/skills/")


def load_host_terms(path: Path) -> tuple[str, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    denylist = data.get("denylist")
    if not isinstance(denylist, list) or not denylist:
        raise SystemExit(f"{path}: denylist must be a non-empty list")
    return tuple(str(item).lower() for item in denylist)


def archive_members(path: Path) -> list[str]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    if path.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(path, "r:gz") as archive:
            return archive.getnames()
    raise ValueError(f"unsupported distribution artifact: {path}")


def check_artifact(path: Path, host_terms: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for member in archive_members(path):
        normalized = member.lstrip("./").lower()
        parts = normalized.split("/")
        without_root = "/".join(parts[1:]) if len(parts) > 1 else normalized
        candidates = {normalized, without_root}
        for candidate in candidates:
            if candidate.startswith(FORBIDDEN_PREFIXES):
                errors.append(f"{path}: forbidden host-adapter tree in artifact: {member}")
            if candidate.startswith("mneme_service/"):
                filename = Path(candidate).name
                if any(filename.startswith(f"{host}_") for host in host_terms):
                    errors.append(f"{path}: forbidden host-specific Core module in artifact: {member}")
            if candidate.startswith("tests/"):
                filename = Path(candidate).name
                if any(filename.startswith(f"test_{host}_") for host in host_terms):
                    errors.append(f"{path}: forbidden host-specific test in artifact: {member}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args(argv)

    host_terms = load_host_terms(args.policy)
    errors: list[str] = []
    for artifact in args.artifacts:
        errors.extend(check_artifact(artifact, host_terms))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("distribution boundary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
