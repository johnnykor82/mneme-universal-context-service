#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_ALLOWLIST = Path("scripts/publication_hygiene_allowlist.json")
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
DEFAULT_SCAN_PATHS = [
    "README.md",
    "docs",
    "mneme_service",
    "tests",
    "pyproject.toml",
    "mneme.example.toml",
    ".github",
]

DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("user_home_path", re.compile(r"/Users/(?!<name>)[^/\s`'\"]+/")),
    ("windows_home_path", re.compile(r"C:\\Users\\(?!<name>)[^\\\s`'\"]+\\")),
    ("api_key_prefix", re.compile(r"\b(?:sk-[A-Za-z0-9][A-Za-z0-9_-]{5,}|ghp_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|xoxb-[A-Za-z0-9-]{8,})\b")),
    (
        "bearer_literal",
        re.compile(
            r"\bBearer\s+(?!auth(?:entication)?\b|security\b|tokens?\b)[A-Za-z0-9._:-]{6,}\b",
            re.IGNORECASE,
        ),
    ),
    ("private_database_url", re.compile(r"\b(?:postgres://|mongodb\+srv://)[^\s`'\"]+")),
    (
        "env_assignment",
        re.compile(
            r"^\s*(?:export\s+)?(?:[A-Z0-9]+_)*(?:TOKEN|SECRET|PASSWORD|API_KEY|DATABASE_URL)(?:_[A-Z0-9]+)*\s*=\s*(?![\"']?[<\[]|\$\(|[\"']?\$\(|replace-|example|placeholder|None\b)\S.*",
            re.MULTILINE,
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    detector: str
    excerpt: str

    def key(self) -> str:
        return f"{self.path}:{self.line}:{self.detector}:{self.excerpt}"


def load_allowlist(path: Path) -> list[re.Pattern[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    patterns: list[re.Pattern[str]] = []
    for index, entry in enumerate(entries):
        if set(entry) != {"pattern", "scope", "reason"}:
            raise SystemExit(f"{path}: entry {index} must contain pattern, scope, reason")
        patterns.append(re.compile(str(entry["pattern"])))
    return patterns


def is_allowed(finding: Finding, allowlist: list[re.Pattern[str]]) -> bool:
    key = finding.key()
    return any(pattern.search(key) for pattern in allowlist)


def iter_files(root: Path, selected_paths: Iterable[str]) -> Iterable[Path]:
    for item in selected_paths:
        path = root / item
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES:
                yield child


def scan_text(path_label: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        for name, pattern in DETECTORS:
            if pattern.search(line):
                findings.append(Finding(path_label, line_no, name, line.strip()[:220]))
    return findings


def archive_text_members(path: Path) -> Iterable[tuple[str, str]]:
    if path.suffix == ".whl" or path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if Path(name).suffix.lower() not in TEXT_SUFFIXES:
                    continue
                yield name, archive.read(name).decode("utf-8", errors="ignore")
        return
    if path.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile() or Path(member.name).suffix.lower() not in TEXT_SUFFIXES:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                yield member.name, extracted.read().decode("utf-8", errors="ignore")
        return
    raise ValueError(f"unsupported artifact: {path}")


def check_publication_hygiene(root: Path, artifacts: list[Path], allowlist_path: Path) -> list[Finding]:
    allowlist = load_allowlist(allowlist_path)
    findings: list[Finding] = []
    for path in iter_files(root, DEFAULT_SCAN_PATHS):
        label = path.relative_to(root).as_posix()
        findings.extend(scan_text(label, path.read_text(encoding="utf-8", errors="ignore")))
    for artifact in artifacts:
        for member_name, text in archive_text_members(artifact):
            findings.extend(scan_text(f"{artifact.name}!{member_name}", text))
    return [finding for finding in findings if not is_allowed(finding, allowlist)]


def default_artifacts(root: Path) -> list[Path]:
    dist = root / "dist"
    if not dist.exists():
        return []
    return sorted([*dist.glob("*.whl"), *dist.glob("*.tar.gz"), *dist.glob("*.tgz")])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("artifacts", nargs="*", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    artifacts = args.artifacts or default_artifacts(root)
    findings = check_publication_hygiene(root, artifacts, args.allowlist)
    if findings:
        for finding in findings:
            print(finding.key(), file=sys.stderr)
        return 1
    print("publication hygiene check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
