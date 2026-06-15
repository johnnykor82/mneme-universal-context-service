from __future__ import annotations

import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"(?i)(api[_-]?key|token|password|authorization)(\s*[:=]\s*)([^\s,;]+)"),
]


def redact_text(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)("):
            redacted = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", redacted)
        else:
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if lowered in {"authorization", "password", "token", "api_key", "apikey"}:
                output[key] = "[REDACTED]"
            else:
                output[key] = redact(item)
        return output
    return value


def bearer_is_valid(header: str | None, expected: str | None, insecure_dev: bool) -> bool:
    if insecure_dev:
        return True
    if not expected or not header:
        return False
    return header == f"Bearer {expected}"
