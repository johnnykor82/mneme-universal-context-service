from __future__ import annotations

import hashlib
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any

SECRET_PATTERNS = [
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED]",
    ),
    (re.compile(r"(?im)^(\s*(?:Proxy-)?Authorization\s*:\s*).+$"), lambda m: f"{m.group(1)}[REDACTED]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE), "[REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{6,}\b"), "[REDACTED]"),
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{10,}\b"), "[REDACTED]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "[REDACTED]"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "[REDACTED]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "[REDACTED]"),
    (
        re.compile(r"\b([A-Za-z][A-Za-z0-9+.-]*://)([^/\s:@]+):([^@\s/]+)@"),
        lambda m: f"{m.group(1)}[REDACTED]@",
    ),
    (
        re.compile(
            r"(?im)^(\s*[A-Za-z_][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASS|CREDENTIAL|PRIVATE|COOKIE)[A-Za-z0-9_]*\s*=\s*).+$"
        ),
        lambda m: f"{m.group(1)}[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|passwd|secret|authorization)(\s*[:=]\s*)([^\s,;]+)"
        ),
        lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]",
    ),
]

SENSITIVE_EXACT_KEYS = {
    "authorization",
    "proxy_authorization",
    "password",
    "passwd",
    "pass",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credentials",
    "credential",
    "cookie",
}
SENSITIVE_KEY_FRAGMENTS = (
    "_api_key",
    "_secret",
    "_password",
    "_passwd",
    "_private_key",
    "_cookie",
)
SENSITIVE_KEY_SUFFIXES = (
    "_token",
    "_credential",
    "_credentials",
)


class RedactionTimeoutError(RuntimeError):
    pass


def redact_text(value: str) -> str:
    redacted = value
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_text_with_metadata(value: str, field_path: str) -> tuple[str, list[dict[str, str]]]:
    redacted = redact_text(value)
    facts = [redaction_fact(kind="SECRET_PATTERN", field=field_path, original=value)] if redacted != value else []
    return redacted, facts


def redaction_fact(*, kind: str, field: str, original: Any) -> dict[str, str]:
    return {
        "kind": kind,
        "field": field,
        "hash": "sha256:" + hashlib.sha256(str(original).encode("utf-8")).hexdigest(),
    }


def redact(value: Any, *, max_time_ms: int | None = None, _deadline: float | None = None) -> Any:
    deadline = _deadline
    if deadline is None and max_time_ms is not None:
        deadline = time.perf_counter() + (max_time_ms / 1000)
    check_redaction_deadline(deadline)
    if isinstance(value, str):
        redacted = redact_text(value)
        check_redaction_deadline(deadline)
        return redacted
    if isinstance(value, list):
        output = []
        for item in value:
            output.append(redact(item, _deadline=deadline))
            check_redaction_deadline(deadline)
        return output
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if is_sensitive_key(key):
                output[key] = "[REDACTED]"
            else:
                output[key] = redact(item, _deadline=deadline)
            check_redaction_deadline(deadline)
        return output
    return value


def redact_with_metadata(
    value: Any,
    *,
    max_time_ms: int | None = None,
    _deadline: float | None = None,
    _path: str = "",
) -> tuple[Any, list[dict[str, str]]]:
    deadline = _deadline
    if deadline is None and max_time_ms is not None:
        deadline = time.perf_counter() + (max_time_ms / 1000)
    check_redaction_deadline(deadline)
    field_path = _path or "$"
    if isinstance(value, str):
        redacted, facts = redact_text_with_metadata(value, field_path)
        check_redaction_deadline(deadline)
        return redacted, facts
    if isinstance(value, list):
        output = []
        facts: list[dict[str, str]] = []
        for index, item in enumerate(value):
            redacted_item, item_facts = redact_with_metadata(item, _deadline=deadline, _path=f"{field_path}[{index}]")
            output.append(redacted_item)
            facts.extend(item_facts)
            check_redaction_deadline(deadline)
        return output, facts
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        facts: list[dict[str, str]] = []
        for key, item in value.items():
            child_path = f"{field_path}.{key}" if field_path != "$" else str(key)
            if is_sensitive_key(key):
                output[key] = "[REDACTED]"
                facts.append(redaction_fact(kind="SENSITIVE_KEY", field=child_path, original=item))
            else:
                redacted_item, item_facts = redact_with_metadata(item, _deadline=deadline, _path=child_path)
                output[key] = redacted_item
                facts.extend(item_facts)
            check_redaction_deadline(deadline)
        return output, facts
    return value, []


def check_redaction_deadline(deadline: float | None) -> None:
    if deadline is not None and time.perf_counter() > deadline:
        raise RedactionTimeoutError("redaction exceeded max_redaction_time_ms")


def is_sensitive_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.strip().lower().replace("-", "_")
    if normalized in SENSITIVE_EXACT_KEYS:
        return True
    if any(normalized.endswith(suffix) for suffix in SENSITIVE_KEY_SUFFIXES):
        return True
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


@dataclass(frozen=True)
class Principal:
    name: str
    role: str
    project_scopes: tuple[str, ...]

    def as_audit_principal(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "project_scopes": list(self.project_scopes),
        }

    @property
    def all_projects(self) -> bool:
        return "*" in self.project_scopes

    def can_access_project(self, project_key: str | None) -> bool:
        if self.all_projects:
            return True
        if not project_key:
            return False
        return project_key in self.project_scopes


def bearer_token(header: str | None) -> str | None:
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def authenticate_bearer(header: str | None, settings: Any) -> Principal | None:
    if settings.insecure_dev:
        return Principal("insecure-dev-owner", "OWNER", ("*",))
    token = bearer_token(header)
    if not token:
        return None
    for static_token in settings.static_tokens:
        if static_token.token and secrets.compare_digest(token, static_token.token):
            return Principal(
                static_token.name,
                static_token.role,
                tuple(static_token.project_scopes),
            )
    if settings.auth_token and secrets.compare_digest(token, settings.auth_token):
        return Principal("local-owner", "OWNER", ("*",))
    return None


def bearer_is_valid(header: str | None, expected: str | None, insecure_dev: bool) -> bool:
    if insecure_dev:
        return True
    token = bearer_token(header)
    if not expected or not token:
        return False
    return secrets.compare_digest(token, expected)
