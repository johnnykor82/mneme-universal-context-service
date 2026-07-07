from __future__ import annotations

import re
from pathlib import Path

PACKAGE_VERSION = "0.1.2"
_FALLBACK_CONTRACT_VERSION = "0.7.5"
_SEMVER_LINE = re.compile(r"\d+\.\d+\.\d+\n?")


def _contract_version_path() -> Path:
    return Path(__file__).resolve().parent.parent / "docs" / "MNEME_CONTRACT_VERSION"


def read_contract_version(path: Path | None = None) -> str:
    version_path = path or _contract_version_path()
    try:
        raw = version_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _FALLBACK_CONTRACT_VERSION
    if not _SEMVER_LINE.fullmatch(raw):
        raise RuntimeError(f"Invalid Mneme contract version file: {version_path}")
    return raw.rstrip("\n")


CONTRACT_VERSION = read_contract_version()
