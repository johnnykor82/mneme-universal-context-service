from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

import httpx

from .config import ProviderSettings


class RerankerProvider(Protocol):
    def rerank(self, query: str, documents: Sequence[str]) -> "RerankResult":
        """Return relevance scores keyed by original document index."""


@dataclass(frozen=True)
class RerankResult:
    scores: list[dict[str, float | int]]
    degraded: bool = False
    fallback_reason: str | None = None


class HttpRerankerProvider:
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

    def rerank(self, query: str, documents: Sequence[str]) -> RerankResult:
        clean_documents = [str(document) for document in documents]
        if not query.strip() or not clean_documents:
            return RerankResult(scores=[])
        if self.circuit_open:
            return RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")
        if self._open_until and self.clock() >= self._open_until:
            self._consecutive_failures = 0
            self._open_until = 0.0

        endpoint = self._endpoint()
        if endpoint is None or not self.settings.model:
            self._record_failure()
            return RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")

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
                        "query": query,
                        "documents": clean_documents,
                        "top_n": len(clean_documents),
                    },
                )
                response.raise_for_status()
            scores = parse_rerank_scores(response.json(), document_count=len(clean_documents))
            if not scores:
                self._record_failure()
                return RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")
            self._record_success()
            return RerankResult(scores=scores)
        except (httpx.HTTPError, ValueError, TypeError):
            self._record_failure()
            return RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")

    def _endpoint(self) -> str | None:
        if not self.settings.base_url:
            return None
        return f"{self.settings.base_url.rstrip('/')}/rerank"

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._open_until = 0.0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open_until = self.clock() + self.cooldown_seconds


def parse_rerank_scores(payload: dict[str, Any], *, document_count: int) -> list[dict[str, float | int]]:
    raw_results = payload.get("results")
    if raw_results is None:
        raw_results = payload.get("data")
    if raw_results is None and isinstance(payload.get("scores"), list):
        scores = []
        for index, raw_score in enumerate(payload["scores"][:document_count]):
            try:
                scores.append({"index": index, "score": float(raw_score)})
            except (TypeError, ValueError):
                continue
        scores.sort(key=lambda item: float(item["score"]), reverse=True)
        return scores
    if not isinstance(raw_results, list):
        return []

    scores: list[dict[str, float | int]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item["index"])
        except (KeyError, TypeError, ValueError):
            continue
        if index < 0 or index >= document_count:
            continue
        raw_score = item.get("relevance_score", item.get("score"))
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        scores.append({"index": index, "score": score})
    scores.sort(key=lambda item: float(item["score"]), reverse=True)
    return scores
