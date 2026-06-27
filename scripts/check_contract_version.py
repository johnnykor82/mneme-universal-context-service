#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def check_contract_version(root: Path) -> list[str]:
    errors: list[str] = []
    version_file = root / "docs/MNEME_CONTRACT_VERSION"
    if not version_file.exists():
        return [f"missing contract version file: {version_file}"]
    contract_version = version_file.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(contract_version):
        errors.append(f"contract version is not SemVer MAJOR.MINOR.PATCH: {contract_version!r}")

    from mneme_service.app import create_app
    from mneme_service.config import Settings

    token = "contract-version-check-token"
    with tempfile.TemporaryDirectory(prefix="mneme-contract-version-") as temp_dir:
        client = TestClient(create_app(Settings(db_path=Path(temp_dir) / "mneme.db", auth_token=token)))
        openapi = client.get("/openapi.json")
        if openapi.status_code != 200:
            errors.append(f"openapi status {openapi.status_code}")
        elif openapi.json().get("info", {}).get("version") != contract_version:
            errors.append("OpenAPI info.version does not match docs/MNEME_CONTRACT_VERSION")

        health = client.get("/v1/health")
        if health.status_code != 200:
            errors.append(f"health status {health.status_code}")
        elif health.json().get("mneme_contract_version") != contract_version:
            errors.append("/v1/health mneme_contract_version mismatch")

        capabilities = client.get("/v1/capabilities", headers={"Authorization": f"Bearer {token}"})
        if capabilities.status_code != 200:
            errors.append(f"capabilities status {capabilities.status_code}")
        elif capabilities.json().get("mneme_contract_version") != contract_version:
            errors.append("/v1/capabilities mneme_contract_version mismatch")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    errors = check_contract_version(args.root.resolve())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("contract version check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
