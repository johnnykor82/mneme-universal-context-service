from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def token_estimate(value: str) -> int:
    return max(1, (len(value) + 3) // 4) if value else 0


def text_from_content(content: dict[str, Any]) -> str:
    if content.get("format") == "BYTES_REF":
        return f"{content.get('media_type', '')} {content.get('uri', '')} {content.get('hash', '')}".strip()
    text = content.get("text", "")
    if isinstance(text, str):
        return text
    return canonical_json(text)
