from __future__ import annotations

import math
import struct
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

import httpx

from .config import ProviderSettings
from .storage import Store
from .utils import text_from_content, token_estimate


TOOL_OUTPUT_COMPRESS_THRESHOLD_TOKENS = 512
TOOL_OUTPUT_COMPRESS_SUMMARY_TOKENS = 256
COLD_START_MIN_SEGMENT_EMBEDDINGS = 3


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        """Return one embedding per input text, preserving input order."""


@dataclass(frozen=True)
class EmbeddingBatchStats:
    embedding_batches: int = 0
    embedding_items: int = 0
    embedding_input_chars: int = 0
    embedding_failures: int = 0

    def plus(self, other: "EmbeddingBatchStats") -> "EmbeddingBatchStats":
        return EmbeddingBatchStats(
            embedding_batches=self.embedding_batches + other.embedding_batches,
            embedding_items=self.embedding_items + other.embedding_items,
            embedding_input_chars=self.embedding_input_chars + other.embedding_input_chars,
            embedding_failures=self.embedding_failures + other.embedding_failures,
        )


@dataclass(frozen=True)
class EmbeddingSearchResult:
    results: list[dict[str, Any]]
    degraded: bool = False
    fallback_reason: str | None = None


class OpenAICompatibleEmbeddingProvider:
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

    def embed_texts(self, texts: Sequence[str]) -> list[list[float] | None]:
        outputs: list[list[float] | None] = [None] * len(texts)
        indexed_inputs: list[tuple[int, str]] = [
            (index, text)
            for index, text in enumerate(texts)
            if isinstance(text, str) and text.strip()
        ]
        if not indexed_inputs:
            return outputs
        if self.circuit_open:
            return outputs
        if self._open_until and self.clock() >= self._open_until:
            self._consecutive_failures = 0
            self._open_until = 0.0

        endpoint = self._endpoint()
        if endpoint is None or not self.settings.model:
            self._record_failure()
            return outputs

        clean_inputs = [text for _, text in indexed_inputs]
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
                    json={"model": self.settings.model, "input": clean_inputs},
                )
                response.raise_for_status()
            data = response.json().get("data", [])
            if len(data) != len(clean_inputs):
                self._record_failure()
                return outputs
            coerced_embeddings: list[list[float]] = []
            for item in data:
                embedding = item.get("embedding") if isinstance(item, dict) else None
                coerced = _coerce_embedding(embedding)
                if not coerced:
                    self._record_failure()
                    return outputs
                coerced_embeddings.append(coerced)
            for (output_index, _), embedding in zip(indexed_inputs, coerced_embeddings):
                outputs[output_index] = embedding
            self._record_success()
            return outputs
        except (httpx.HTTPError, ValueError, TypeError):
            self._record_failure()
            return outputs

    def _endpoint(self) -> str | None:
        if not self.settings.base_url:
            return None
        return f"{self.settings.base_url.rstrip('/')}/embeddings"

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._open_until = 0.0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._open_until = self.clock() + self.cooldown_seconds


class EmbeddingIndex:
    def __init__(
        self,
        store: Store,
        provider: EmbeddingProvider,
        *,
        model_id: str,
        batch_size: int = 16,
        centroid_window: int = 0,
    ) -> None:
        self.store = store
        self.provider = provider
        self.model_id = model_id
        self.batch_size = max(1, int(batch_size or 1))
        self.centroid_window = max(0, int(centroid_window or 0))

    def index_events(self, records: Sequence[dict[str, Any]]) -> EmbeddingBatchStats:
        if not records:
            return EmbeddingBatchStats()

        stats = EmbeddingBatchStats()
        for chunk in _chunks(list(records), self.batch_size):
            texts = [str(record.get("text", "")) for record in chunk]
            batch_stats = EmbeddingBatchStats(
                embedding_batches=1,
                embedding_input_chars=sum(len(text) for text in texts if text.strip()),
            )
            try:
                embeddings = self.provider.embed_texts(texts)
            except Exception:
                stats = stats.plus(EmbeddingBatchStats(embedding_batches=1, embedding_failures=1))
                continue
            if len(embeddings) != len(chunk):
                stats = stats.plus(batch_stats.plus(EmbeddingBatchStats(embedding_failures=1)))
                continue
            valid_embeddings = [embedding for embedding in embeddings if embedding]
            if valid_embeddings:
                dimension = len(valid_embeddings[0])
                if any(len(embedding) != dimension for embedding in valid_embeddings):
                    stats = stats.plus(batch_stats.plus(EmbeddingBatchStats(embedding_failures=1)))
                    continue
            stored = 0
            for record, embedding in zip(chunk, embeddings):
                if not embedding:
                    continue
                try:
                    self.store.put_embedding(
                        event_id=str(record["event_id"]),
                        session_id=str(record["session_id"]),
                        segment_id=str(record["segment_id"]),
                        embedding=_pack_embedding(embedding),
                        embedding_model_id=self.model_id,
                        token_count=int(record.get("token_count") or 0),
                        event_type=str(record.get("type") or ""),
                    )
                    stored += 1
                except Exception:
                    stats = stats.plus(EmbeddingBatchStats(embedding_failures=1))
            failed_batch = 1 if any(text.strip() for text in texts) and stored == 0 else 0
            stats = stats.plus(
                EmbeddingBatchStats(
                    embedding_batches=batch_stats.embedding_batches,
                    embedding_items=stored,
                    embedding_input_chars=batch_stats.embedding_input_chars,
                    embedding_failures=failed_batch,
                )
            )
        return stats

    def search(self, query: str, *, session_id: str, top_k: int = 10) -> list[dict[str, Any]]:
        return self.search_with_status(query, session_id=session_id, top_k=top_k).results

    def search_with_status(self, query: str, *, session_id: str, top_k: int = 10) -> EmbeddingSearchResult:
        return self._search_with_rows(
            query,
            rows=self.store.list_embeddings(session_id, self.model_id),
            top_k=top_k,
        )

    def search_global(self, query: str, *, top_k: int = 10) -> list[dict[str, Any]]:
        return self.search_global_with_status(query, top_k=top_k).results

    def search_global_with_status(self, query: str, *, top_k: int = 10) -> EmbeddingSearchResult:
        return self._search_with_rows(
            query,
            rows=self.store.list_embeddings_for_sessions(None, self.model_id),
            top_k=top_k,
        )

    def search_sessions(
        self,
        query: str,
        *,
        session_ids: Sequence[str],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        return self.search_sessions_with_status(query, session_ids=session_ids, top_k=top_k).results

    def search_sessions_with_status(
        self,
        query: str,
        *,
        session_ids: Sequence[str],
        top_k: int = 10,
    ) -> EmbeddingSearchResult:
        return self._search_with_rows(
            query,
            rows=self.store.list_embeddings_for_sessions(list(session_ids), self.model_id),
            top_k=top_k,
        )

    def _search_with_rows(
        self,
        query: str,
        *,
        rows: Sequence[dict[str, Any]],
        top_k: int = 10,
    ) -> EmbeddingSearchResult:
        if not query.strip():
            return EmbeddingSearchResult([])
        try:
            query_embedding = self.provider.embed_texts([query])
        except Exception:
            return EmbeddingSearchResult([], degraded=True, fallback_reason="EMBEDDINGS_UNAVAILABLE")
        if not query_embedding or not query_embedding[0]:
            return EmbeddingSearchResult([], degraded=True, fallback_reason="EMBEDDINGS_UNAVAILABLE")
        query_vector = query_embedding[0]
        results: list[dict[str, Any]] = []
        for row in rows:
            vector = _unpack_embedding(row["embedding"])
            score = _cosine(query_vector, vector)
            if score <= 0:
                continue
            results.append(
                {
                    "event_id": row["event_id"],
                    "segment_id": row["segment_id"],
                    "embedding_model_id": row["embedding_model_id"],
                    "type": row["type"],
                    "score": score,
                    "reason": "VECTOR_COSINE",
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        if top_k and top_k > 0:
            results = results[:top_k]
        return EmbeddingSearchResult(results)

    def embedding_drift_against_segment(
        self,
        text: str,
        *,
        session_id: str,
        segment_id: str,
        min_embeddings: int = COLD_START_MIN_SEGMENT_EMBEDDINGS,
    ) -> float:
        vectors = [
            _unpack_embedding(row["embedding"])
            for row in self.store.list_embeddings(session_id, self.model_id)
            if row["segment_id"] == segment_id
        ]
        if self.centroid_window > 0:
            vectors = vectors[-self.centroid_window :]
        vectors = [vector for vector in vectors if vector]
        if not vectors:
            return 0.0
        dimension = len(vectors[0])
        vectors = [vector for vector in vectors if len(vector) == dimension]
        if len(vectors) < min_embeddings:
            return 0.0
        try:
            embedded = self.provider.embed_texts([text])
        except Exception:
            return 0.0
        if not embedded or not embedded[0]:
            return 0.0
        centroid = [
            sum(vector[index] for vector in vectors) / len(vectors)
            for index in range(dimension)
        ]
        similarity = _cosine(embedded[0], centroid)
        return min(max((1.0 - similarity) / 2.0, 0.0), 1.0)


def embedding_record_from_event(
    event: dict[str, Any],
    *,
    tool_output_compress_threshold_tokens: int = TOOL_OUTPUT_COMPRESS_THRESHOLD_TOKENS,
    tool_output_summary_tokens: int = TOOL_OUTPUT_COMPRESS_SUMMARY_TOKENS,
) -> dict[str, Any] | None:
    if event.get("type") == "MEMORY_READ":
        return None
    text = text_from_content(event.get("content", {}))
    if not text.strip():
        return None
    text_for_embedding = text
    if event.get("type") == "TOOL_OUTPUT":
        text_for_embedding = summarize_for_embedding(
            text,
            threshold_tokens=tool_output_compress_threshold_tokens,
            summary_tokens=tool_output_summary_tokens,
        )
    metadata = event.get("metadata", {})
    segment_id = metadata.get("mneme_segment_id") if isinstance(metadata, dict) else None
    return {
        "event_id": event["event_id"],
        "session_id": event["session_id"],
        "segment_id": segment_id or f"segment-{event['session_id']}",
        "text": text_for_embedding,
        "token_count": token_estimate(text_for_embedding),
        "type": event["type"],
    }


def summarize_for_embedding(
    content: str,
    *,
    threshold_tokens: int,
    summary_tokens: int,
    chars_per_token: int = 4,
) -> str:
    if not content:
        return content
    threshold_chars = threshold_tokens * chars_per_token
    if len(content) <= threshold_chars:
        return content
    summary_chars = summary_tokens * chars_per_token
    head_chars = summary_chars // 2
    tail_chars = summary_chars - head_chars
    head = content[:head_chars]
    tail = content[-tail_chars:]
    return f"{head}\n...[truncated {len(content) - head_chars - tail_chars} chars]...\n{tail}"


def _coerce_embedding(value: Any) -> list[float] | None:
    if not isinstance(value, list):
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _chunks(records: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [records[index : index + size] for index in range(0, len(records), size)]


def _pack_embedding(embedding: Sequence[float]) -> bytes:
    return struct.pack(f"{len(embedding)}f", *embedding)


def _unpack_embedding(blob: bytes) -> list[float]:
    if not blob:
        return []
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    dim = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(dim))
    left_norm = math.sqrt(sum(left[index] * left[index] for index in range(dim)))
    right_norm = math.sqrt(sum(right[index] * right[index] for index in range(dim)))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
