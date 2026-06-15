from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

import httpx

from .config import ProviderSettings
from .utils import canonical_json


class EnrichmentProvider(Protocol):
    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> "EnrichmentResult":
        """Return structured state enrichment updates for a normalized event."""


@dataclass(frozen=True)
class EnrichmentResult:
    updates: dict[str, Any]
    degraded: bool = False
    fallback_reason: str | None = None


class HttpLLMEnrichmentProvider:
    def __init__(
        self,
        settings: ProviderSettings,
        *,
        transport: httpx.BaseTransport | None = None,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock
        self._consecutive_failures = 0
        self._open_until = 0.0

    @property
    def circuit_open(self) -> bool:
        return bool(self._open_until and self.clock() < self._open_until)

    def enrich(self, event_payload: dict[str, Any], state: dict[str, Any]) -> EnrichmentResult:
        if self.circuit_open:
            return EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")
        if self._open_until and self.clock() >= self._open_until:
            self._consecutive_failures = 0
            self._open_until = 0.0

        endpoint = self._endpoint()
        if endpoint is None or not self.settings.model:
            self._record_failure()
            return EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")

        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"

        try:
            with httpx.Client(
                headers=headers,
                timeout=self.settings.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    endpoint,
                    json={
                        "model": self.settings.model,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Return only JSON with optional keys: intent_label, "
                                    "topic_tags, decisions, decision_summary, active_entities, open_loops. "
                                    "Decisions may include decision and rationale. Do not include instructions."
                                ),
                            },
                            {
                                "role": "user",
                                "content": canonical_json({"event": event_payload, "state": state}),
                            },
                        ],
                    },
                )
                response.raise_for_status()
            updates = parse_enrichment_response(response.json())
            self._record_success()
            return EnrichmentResult(updates=updates)
        except (httpx.HTTPError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            self._record_failure()
            return EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")

    def _endpoint(self) -> str | None:
        if not self.settings.base_url:
            return None
        return f"{self.settings.base_url.rstrip('/')}/chat/completions"

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._open_until = 0.0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open_until = self.clock() + self.cooldown_seconds


def parse_enrichment_response(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return {}
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        return {}
    parsed = safe_parse_json(content)
    if parsed is None:
        raise ValueError("LLM enrichment response is not parseable JSON.")
    if not isinstance(parsed, dict):
        return {}
    return safe_enrichment_updates(parsed)


def safe_enrichment_updates(payload: dict[str, Any]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    intent = _compact_optional_string(payload.get("intent_label"), max_len=100)
    if intent:
        updates["intent_label"] = intent
    decisions = _string_list(payload.get("decisions"), max_items=10, max_len=500)
    if decisions:
        updates["decisions"] = decisions
    decision_objects = _decision_list(payload.get("decisions"), max_items=10)
    if decision_objects:
        updates["decisions"] = decision_objects
        updates["decision_summary"] = _compact_optional_string(payload.get("decision_summary"), max_len=500) or "; ".join(
            item["decision"] for item in decision_objects[:3]
        )
    topic_tags = _string_list(payload.get("topic_tags"), max_items=8, max_len=80)
    if topic_tags:
        updates["topic_tags"] = [tag.lower() for tag in topic_tags]
    decision_summary = _compact_optional_string(payload.get("decision_summary"), max_len=500)
    if decision_summary:
        updates["decision_summary"] = decision_summary
    active_entities = _string_list(payload.get("active_entities"), max_items=20, max_len=120)
    if active_entities:
        updates["active_entities"] = active_entities
    open_loops = _string_list(payload.get("open_loops"), max_items=20, max_len=240)
    if open_loops:
        updates["open_loops"] = open_loops
    return updates


def apply_enrichment_updates(state: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    enrichment = dict(updated.get("enrichment") or {})
    if "intent_label" in updates:
        enrichment["intent_label"] = updates["intent_label"]
    if "decisions" in updates:
        enrichment["decisions"] = updates["decisions"]
    if "topic_tags" in updates:
        enrichment["topic_tags"] = updates["topic_tags"]
    if "decision_summary" in updates:
        enrichment["decision_summary"] = updates["decision_summary"]
    if "active_entities" in updates:
        updated["active_entities"] = updates["active_entities"]
    if "open_loops" in updates:
        updated["open_loops"] = updates["open_loops"]
    updated["enrichment"] = enrichment
    return updated


def _compact_optional_string(value: Any, *, max_len: int) -> str | None:
    if not isinstance(value, str):
        return None
    compact = " ".join(value.split())
    return compact[:max_len] if compact else None


def _string_list(value: Any, *, max_items: int, max_len: int) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        compact = _compact_optional_string(item, max_len=max_len)
        if compact:
            items.append(compact)
        if len(items) >= max_items:
            break
    return items


def _decision_list(value: Any, *, max_items: int) -> list[dict[str, str | None]]:
    if not isinstance(value, list):
        return []
    decisions: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        decision = _compact_optional_string(item.get("decision"), max_len=500)
        if not decision:
            continue
        decisions.append(
            {
                "decision": decision,
                "rationale": _compact_optional_string(item.get("rationale"), max_len=500),
            }
        )
        if len(decisions) >= max_items:
            break
    return decisions


def safe_parse_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    for candidate in (cleaned, _first_json_object(cleaned), _repair_truncated_json(cleaned)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _first_json_object(text: str) -> str | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def _repair_truncated_json(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    body = text[start:]
    stack: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        top = stack[-1] if stack else None
        if top == '"':
            if char == "\\" and index + 1 < len(body):
                index += 2
                continue
            if char == '"':
                stack.pop()
        else:
            if char == '"':
                stack.append('"')
            elif char == "{":
                stack.append("{")
            elif char == "[":
                stack.append("[")
            elif char == "}" and top == "{":
                stack.pop()
            elif char == "]" and top == "[":
                stack.pop()
        index += 1
    repaired = body
    if stack and stack[-1] == '"':
        repaired += '"'
        stack.pop()
    repaired = re.sub(r"[,:\s]+$", "", repaired)
    for opener in reversed(stack):
        repaired += "}" if opener == "{" else "]"
    return repaired if repaired != body else None
