from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .state import default_execution_state, history_entry_from_state
from .utils import canonical_json, new_id, now_ms, text_from_content


RICH_SEGMENT_FIELDS = {
    "events_by_type",
    "first_ts",
    "last_ts",
    "first_user_snippet",
    "last_user_snippet",
    "goal_at_end",
    "topic_tags",
}


def text_from_event(event: dict[str, Any] | None) -> str:
    if not event:
        return ""
    return text_from_content(event.get("content", {}))


def goal_at_timestamp(history: list[dict[str, Any]], timestamp: str) -> str | None:
    goal = None
    for item in history:
        item_ts = str(item.get("timestamp") or "")
        if timestamp and item_ts and item_ts > timestamp:
            continue
        if item.get("goal"):
            goal = item["goal"]
    return goal


def strip_rich_segment_fields(segment: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in segment.items() if key not in RICH_SEGMENT_FIELDS}


class Store:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                  session_id TEXT PRIMARY KEY,
                  data TEXT NOT NULL,
                  project_isolation_key TEXT,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS session_lineage (
                  old_session_id TEXT NOT NULL,
                  new_session_id TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (old_session_id, new_session_id)
                );
                CREATE TABLE IF NOT EXISTS session_context_fill (
                  session_id TEXT PRIMARY KEY,
                  required INTEGER NOT NULL,
                  fulfilled INTEGER NOT NULL,
                  updated_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                  event_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  turn_id TEXT,
                  agent_id TEXT,
                  runtime TEXT,
                  role TEXT NOT NULL,
                  type TEXT NOT NULL,
                  timestamp TEXT NOT NULL,
                  content_text TEXT NOT NULL,
                  event_json TEXT NOT NULL,
                  immutable_hash TEXT NOT NULL,
                  parent_event_ids TEXT NOT NULL,
                  token_estimate INTEGER NOT NULL,
                  is_memory_read INTEGER NOT NULL DEFAULT 0,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_session_created ON events(session_id, created_at_ms);
                CREATE INDEX IF NOT EXISTS idx_events_turn ON events(session_id, turn_id);
                CREATE TABLE IF NOT EXISTS event_graph_edges (
                  source_event_id TEXT NOT NULL,
                  target_event_id TEXT NOT NULL,
                  session_id TEXT NOT NULL,
                  edge_type TEXT NOT NULL,
                  weight REAL NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (source_event_id, target_event_id, edge_type)
                );
                CREATE INDEX IF NOT EXISTS idx_event_graph_edges_session
                  ON event_graph_edges(session_id, source_event_id, target_event_id);
                CREATE TABLE IF NOT EXISTS turns (
                  session_id TEXT NOT NULL,
                  turn_id TEXT NOT NULL,
                  data TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (session_id, turn_id)
                );
                CREATE TABLE IF NOT EXISTS traces (
                  trace_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  turn_id TEXT,
                  data TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_records (
                  audit_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  tool TEXT NOT NULL,
                  event_ids TEXT NOT NULL,
                  trace_id TEXT,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS segments (
                  segment_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  data TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS embedding_index (
                  event_id TEXT NOT NULL,
                  session_id TEXT NOT NULL,
                  segment_id TEXT NOT NULL,
                  embedding BLOB NOT NULL,
                  embedding_model_id TEXT NOT NULL,
                  token_count INTEGER NOT NULL,
                  type TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (event_id, embedding_model_id)
                );
                CREATE INDEX IF NOT EXISTS idx_embedding_index_session_model
                  ON embedding_index(session_id, embedding_model_id);
                CREATE TABLE IF NOT EXISTS embedding_metrics (
                  session_id TEXT PRIMARY KEY,
                  embedding_batches INTEGER NOT NULL DEFAULT 0,
                  embedding_items INTEGER NOT NULL DEFAULT 0,
                  embedding_input_chars INTEGER NOT NULL DEFAULT 0,
                  embedding_failures INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS reranker_metrics (
                  session_id TEXT PRIMARY KEY,
                  reranker_calls INTEGER NOT NULL DEFAULT 0,
                  reranker_failures INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS enrichment_metrics (
                  session_id TEXT PRIMARY KEY,
                  enrichment_calls INTEGER NOT NULL DEFAULT 0,
                  enrichment_failures INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS execution_state (
                  session_id TEXT PRIMARY KEY,
                  state_json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS state_history (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT NOT NULL,
                  timestamp TEXT NOT NULL,
                  goal TEXT,
                  current_step TEXT,
                  intent_label TEXT,
                  decisions_added_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_state_history_session
                  ON state_history(session_id, timestamp);
                """
            )

    def has_session(self, session_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return row is not None

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def put_session(self, data: dict[str, Any]) -> bool:
        session_id = data["session_id"]
        project_key = data.get("privacy", {}).get("project_isolation_key")
        with self.connect() as conn:
            existing = conn.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO sessions(session_id, data, project_isolation_key, created_at_ms) VALUES (?, ?, ?, ?)",
                (session_id, canonical_json(data), project_key, now_ms()),
            )
            return True

    def session_counts(self, session_id: str) -> dict[str, int]:
        with self.connect() as conn:
            event_count = conn.execute(
                "SELECT COUNT(*) AS n FROM events WHERE session_id = ? AND is_memory_read = 0",
                (session_id,),
            ).fetchone()["n"]
            turn_count = conn.execute(
                "SELECT COUNT(*) AS n FROM turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()["n"]
        return {"event_count": int(event_count), "turn_count": int(turn_count)}

    def lineage_counts(self, session_id: str) -> dict[str, int]:
        session_ids = self.lineage_session_ids(session_id)
        placeholders = ", ".join("?" for _ in session_ids)
        with self.connect() as conn:
            event_count = conn.execute(
                f"SELECT COUNT(*) AS n FROM events WHERE session_id IN ({placeholders}) AND is_memory_read = 0",
                session_ids,
            ).fetchone()["n"]
            turn_count = conn.execute(
                f"SELECT COUNT(*) AS n FROM turns WHERE session_id IN ({placeholders})",
                session_ids,
            ).fetchone()["n"]
        return {"event_count": int(event_count), "turn_count": int(turn_count)}

    def set_context_fill_required(self, session_id: str, required: bool) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO session_context_fill(session_id, required, fulfilled, updated_at_ms)
                VALUES (?, ?, 0, ?)
                """,
                (session_id, 1 if required else 0, now_ms()),
            )

    def context_fill_required(self, session_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT required, fulfilled
                FROM session_context_fill
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        return bool(row and row["required"] and not row["fulfilled"])

    def mark_context_fill_fulfilled(self, session_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE session_context_fill
                SET fulfilled = 1, updated_at_ms = ?
                WHERE session_id = ?
                """,
                (now_ms(), session_id),
            )

    def put_session_lineage(self, old_session_id: str, new_session_id: str) -> bool:
        if not old_session_id or not new_session_id or old_session_id == new_session_id:
            return False
        if not self.has_session(old_session_id) or not self.has_session(new_session_id):
            return False
        if new_session_id in self.lineage_session_ids(old_session_id):
            return False
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO session_lineage(old_session_id, new_session_id, created_at_ms)
                VALUES (?, ?, ?)
                """,
                (old_session_id, new_session_id, now_ms()),
            )
            return bool(cursor.rowcount)

    def lineage_session_ids(self, session_id: str) -> list[str]:
        if not session_id:
            return []
        seen = {session_id}
        ordered = [session_id]
        with self.connect() as conn:
            frontier = [session_id]
            while frontier:
                next_frontier: list[str] = []
                for current in frontier:
                    rows = conn.execute(
                        "SELECT old_session_id FROM session_lineage WHERE new_session_id = ?",
                        (current,),
                    ).fetchall()
                    for row in rows:
                        ancestor = row["old_session_id"]
                        if ancestor and ancestor not in seen:
                            seen.add(ancestor)
                            ordered.append(ancestor)
                            next_frontier.append(ancestor)
                frontier = next_frontier

            frontier = [session_id]
            while frontier:
                next_frontier = []
                for current in frontier:
                    rows = conn.execute(
                        "SELECT new_session_id FROM session_lineage WHERE old_session_id = ?",
                        (current,),
                    ).fetchall()
                    for row in rows:
                        descendant = row["new_session_id"]
                        if descendant and descendant not in seen:
                            seen.add(descendant)
                            ordered.append(descendant)
                            next_frontier.append(descendant)
                frontier = next_frontier
        return ordered

    def session_lineage_edges(self, session_id: str) -> list[dict[str, str]]:
        session_ids = self.lineage_session_ids(session_id)
        if not session_ids:
            return []
        placeholders = ", ".join("?" for _ in session_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT old_session_id, new_session_id
                FROM session_lineage
                WHERE old_session_id IN ({placeholders}) OR new_session_id IN ({placeholders})
                ORDER BY created_at_ms ASC
                """,
                [*session_ids, *session_ids],
            ).fetchall()
        return [
            {
                "schema_version": "mneme.session_lineage.v0",
                "old_session_id": row["old_session_id"],
                "new_session_id": row["new_session_id"],
            }
            for row in rows
        ]

    def get_event_hash(self, event_id: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute("SELECT immutable_hash FROM events WHERE event_id = ?", (event_id,)).fetchone()
            return row["immutable_hash"] if row else None

    def put_event(self, event: dict[str, Any], immutable_hash: str, content_text: str, is_memory_read: bool = False) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO events(
                  event_id, session_id, turn_id, agent_id, runtime, role, type, timestamp,
                  content_text, event_json, immutable_hash, parent_event_ids, token_estimate,
                  is_memory_read, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["session_id"],
                    event.get("turn_id"),
                    event.get("agent_id"),
                    event.get("runtime"),
                    event["role"],
                    event["type"],
                    event["timestamp"],
                    content_text,
                    canonical_json(event),
                    immutable_hash,
                    canonical_json(event.get("parent_event_ids", [])),
                    int(event.get("token_estimate") or 0),
                    1 if is_memory_read else 0,
                    now_ms(),
                ),
            )

    def put_event_graph_edges(self, event: dict[str, Any]) -> None:
        parent_ids = [item for item in event.get("parent_event_ids", []) if isinstance(item, str) and item]
        if not parent_ids:
            return
        edges = []
        for parent_id in parent_ids:
            parent = self.get_event(event["session_id"], parent_id)
            edges.append((parent_id, event["event_id"], event["session_id"], graph_edge_type(parent, event), 1.0, now_ms()))
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO event_graph_edges(
                  source_event_id, target_event_id, session_id, edge_type, weight, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                edges,
            )

    def list_event_graph_edges(self, session_id: str) -> list[dict[str, Any]]:
        session_ids = self.lineage_session_ids(session_id)
        placeholders = ", ".join("?" for _ in session_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT source_event_id, target_event_id, session_id, edge_type, weight
                FROM event_graph_edges
                WHERE session_id IN ({placeholders})
                ORDER BY created_at_ms ASC
                """,
                session_ids,
            ).fetchall()
        return [graph_edge_from_row(row) for row in rows]

    def graph_edges_for_event(self, session_id: str, event_id: str) -> list[dict[str, Any]]:
        session_ids = self.lineage_session_ids(session_id)
        placeholders = ", ".join("?" for _ in session_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT source_event_id, target_event_id, session_id, edge_type, weight
                FROM event_graph_edges
                WHERE session_id IN ({placeholders})
                  AND (source_event_id = ? OR target_event_id = ?)
                ORDER BY created_at_ms ASC
                """,
                [*session_ids, event_id, event_id],
            ).fetchall()
        return [graph_edge_from_row(row) for row in rows]

    def put_embedding(
        self,
        *,
        event_id: str,
        session_id: str,
        segment_id: str,
        embedding: bytes,
        embedding_model_id: str,
        token_count: int,
        event_type: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embedding_index(
                  event_id, session_id, segment_id, embedding, embedding_model_id,
                  token_count, type, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    session_id,
                    segment_id,
                    embedding,
                    embedding_model_id,
                    int(token_count),
                    event_type,
                    now_ms(),
                ),
            )

    def list_embeddings(self, session_id: str, embedding_model_id: str) -> list[dict[str, Any]]:
        session_ids = self.lineage_session_ids(session_id)
        return self.list_embeddings_for_sessions(session_ids, embedding_model_id)

    def list_embeddings_for_sessions(
        self,
        session_ids: list[str] | None,
        embedding_model_id: str,
    ) -> list[dict[str, Any]]:
        params: list[Any] = [embedding_model_id]
        session_filter = ""
        if session_ids is not None:
            if not session_ids:
                return []
            placeholders = ", ".join("?" for _ in session_ids)
            session_filter = f" AND session_id IN ({placeholders})"
            params.extend(session_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT event_id, session_id, segment_id, embedding, embedding_model_id, token_count, type, created_at_ms
                FROM embedding_index
                WHERE embedding_model_id = ?{session_filter}
                ORDER BY created_at_ms ASC
                """,
                params,
            ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "session_id": row["session_id"],
                "segment_id": row["segment_id"],
                "embedding": row["embedding"],
                "embedding_model_id": row["embedding_model_id"],
                "token_count": row["token_count"],
                "type": row["type"],
                "created_at_ms": row["created_at_ms"],
            }
            for row in rows
        ]

    def record_embedding_metrics(
        self,
        session_id: str,
        *,
        embedding_batches: int,
        embedding_items: int,
        embedding_input_chars: int,
        embedding_failures: int,
    ) -> None:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM embedding_metrics WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE embedding_metrics
                    SET embedding_batches = embedding_batches + ?,
                        embedding_items = embedding_items + ?,
                        embedding_input_chars = embedding_input_chars + ?,
                        embedding_failures = embedding_failures + ?
                    WHERE session_id = ?
                    """,
                    (
                        int(embedding_batches),
                        int(embedding_items),
                        int(embedding_input_chars),
                        int(embedding_failures),
                        session_id,
                    ),
                )
                return
            conn.execute(
                """
                INSERT INTO embedding_metrics(
                  session_id, embedding_batches, embedding_items,
                  embedding_input_chars, embedding_failures
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    int(embedding_batches),
                    int(embedding_items),
                    int(embedding_input_chars),
                    int(embedding_failures),
                ),
            )

    def embedding_metrics(self, session_id: str) -> dict[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT embedding_batches, embedding_items, embedding_input_chars, embedding_failures
                FROM embedding_metrics
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if not row:
            return {
                "embedding_batches": 0,
                "embedding_items": 0,
                "embedding_input_chars": 0,
                "embedding_failures": 0,
            }
        return {
            "embedding_batches": int(row["embedding_batches"]),
            "embedding_items": int(row["embedding_items"]),
            "embedding_input_chars": int(row["embedding_input_chars"]),
            "embedding_failures": int(row["embedding_failures"]),
        }

    def record_reranker_metrics(
        self,
        session_id: str,
        *,
        reranker_calls: int,
        reranker_failures: int,
    ) -> None:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM reranker_metrics WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE reranker_metrics
                    SET reranker_calls = reranker_calls + ?,
                        reranker_failures = reranker_failures + ?
                    WHERE session_id = ?
                    """,
                    (int(reranker_calls), int(reranker_failures), session_id),
                )
                return
            conn.execute(
                """
                INSERT INTO reranker_metrics(session_id, reranker_calls, reranker_failures)
                VALUES (?, ?, ?)
                """,
                (session_id, int(reranker_calls), int(reranker_failures)),
            )

    def reranker_metrics(self, session_id: str) -> dict[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT reranker_calls, reranker_failures
                FROM reranker_metrics
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if not row:
            return {"reranker_calls": 0, "reranker_failures": 0}
        return {
            "reranker_calls": int(row["reranker_calls"]),
            "reranker_failures": int(row["reranker_failures"]),
        }

    def record_enrichment_metrics(
        self,
        session_id: str,
        *,
        enrichment_calls: int,
        enrichment_failures: int,
    ) -> None:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM enrichment_metrics WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE enrichment_metrics
                    SET enrichment_calls = enrichment_calls + ?,
                        enrichment_failures = enrichment_failures + ?
                    WHERE session_id = ?
                    """,
                    (int(enrichment_calls), int(enrichment_failures), session_id),
                )
                return
            conn.execute(
                """
                INSERT INTO enrichment_metrics(session_id, enrichment_calls, enrichment_failures)
                VALUES (?, ?, ?)
                """,
                (session_id, int(enrichment_calls), int(enrichment_failures)),
            )

    def enrichment_metrics(self, session_id: str) -> dict[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT enrichment_calls, enrichment_failures
                FROM enrichment_metrics
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if not row:
            return {"enrichment_calls": 0, "enrichment_failures": 0}
        return {
            "enrichment_calls": int(row["enrichment_calls"]),
            "enrichment_failures": int(row["enrichment_failures"]),
        }

    def load_execution_state(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM execution_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return json.loads(row["state_json"]) if row else None

    def commit_execution_state(self, session_id: str, state: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO execution_state(session_id, state_json, updated_at) VALUES (?, ?, ?)",
                (session_id, canonical_json(state), now),
            )
            previous = conn.execute(
                """
                SELECT goal, current_step, intent_label
                FROM state_history
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
            entry = history_entry_from_state(state, now)
            changed = not (
                previous
                and previous["goal"] == entry["goal"]
                and previous["current_step"] == entry["current_step"]
                and previous["intent_label"] == entry["intent_label"]
            )
            if changed:
                conn.execute(
                    """
                    INSERT INTO state_history(
                      session_id, timestamp, goal, current_step, intent_label,
                      decisions_added_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        entry["timestamp"],
                        entry["goal"],
                        entry["current_step"],
                        entry["intent_label"],
                        canonical_json(entry["decisions"]) if entry["decisions"] else None,
                    ),
                )

    def execution_state_or_default(self, session_id: str) -> dict[str, Any]:
        return self.load_execution_state(session_id) or self.recover_execution_state_from_history(session_id)

    def recover_execution_state_from_history(self, session_id: str) -> dict[str, Any]:
        state = default_execution_state(session_id)
        history = self.get_state_history(session_id, limit=1)
        if not history:
            return state
        latest = history[-1]
        state["goal"] = latest.get("goal") or ""
        state["current_step"] = latest.get("current_step") or ""
        enrichment = dict(state.get("enrichment") or {})
        enrichment["intent_label"] = latest.get("intent_label")
        state["enrichment"] = enrichment
        decisions = latest.get("decisions") or []
        if decisions:
            state["decision_stack"] = decisions[-20:]
        return state

    def get_state_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, goal, current_step, intent_label, decisions_added_json
                FROM state_history
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, int(limit)),
            ).fetchall()
        history: list[dict[str, Any]] = []
        for row in reversed(rows):
            decisions = []
            if row["decisions_added_json"]:
                decisions = json.loads(row["decisions_added_json"])
            history.append(
                {
                    "schema_version": "mneme.state_history_entry.v0",
                    "timestamp": row["timestamp"],
                    "goal": row["goal"],
                    "current_step": row["current_step"],
                    "intent_label": row["intent_label"],
                    "decisions": decisions,
                }
            )
        return history

    def get_recent_unique_goals(self, session_id: str, limit: int = 3) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, goal
                FROM state_history
                WHERE session_id = ? AND goal IS NOT NULL AND goal != ''
                ORDER BY id DESC
                """,
                (session_id,),
            ).fetchall()
        seen: set[str] = set()
        goals: list[dict[str, Any]] = []
        for row in rows:
            goal = row["goal"]
            if goal in seen:
                continue
            seen.add(goal)
            goals.append({"timestamp": row["timestamp"], "goal": goal})
            if len(goals) >= int(limit):
                break
        return list(reversed(goals))

    def session_stats(self, session_id: str) -> dict[str, int]:
        with self.connect() as conn:
            event_count = conn.execute(
                "SELECT COUNT(*) AS n FROM events WHERE session_id = ? AND is_memory_read = 0",
                (session_id,),
            ).fetchone()["n"]
            segment_count = conn.execute(
                "SELECT COUNT(*) AS n FROM segments WHERE session_id = ?",
                (session_id,),
            ).fetchone()["n"]
        return {"total_events": int(event_count), "total_segments": int(segment_count)}

    def recent_memory_tool_count(self, session_id: str, tool_names: tuple[str, ...]) -> int:
        if not tool_names:
            return 0
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT action, tool
                FROM audit_records
                WHERE session_id = ?
                ORDER BY created_at_ms DESC
                """,
                (session_id,),
            ).fetchall()
        count = 0
        memory_tools = set(tool_names)
        for row in rows:
            if row["action"] == "MEMORY_READ" and row["tool"] in memory_tools:
                count += 1
                continue
            break
        return count

    def list_events(self, session_id: str, *, include_memory_reads: bool = False, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT event_json FROM events WHERE session_id = ?"
        params: list[Any] = [session_id]
        if not include_memory_reads:
            query += " AND is_memory_read = 0"
        query += " ORDER BY created_at_ms ASC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [json.loads(row["event_json"]) for row in rows]

    def list_events_missing_embedding(self, embedding_model_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT e.event_json
            FROM events e
            LEFT JOIN embedding_index i
              ON i.event_id = e.event_id AND i.embedding_model_id = ?
            WHERE e.is_memory_read = 0 AND i.event_id IS NULL
            ORDER BY e.created_at_ms ASC
        """
        params: list[Any] = [embedding_model_id]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [json.loads(row["event_json"]) for row in rows]

    def recent_events(self, session_id: str, max_events: int) -> list[dict[str, Any]]:
        session_ids = self.lineage_session_ids(session_id)
        placeholders = ", ".join("?" for _ in session_ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT event_json FROM events
                WHERE session_id IN ({placeholders}) AND is_memory_read = 0
                ORDER BY created_at_ms DESC
                LIMIT ?
                """,
                [*session_ids, max_events],
            ).fetchall()
        return [json.loads(row["event_json"]) for row in reversed(rows)]

    def get_event(self, session_id: str, event_id: str) -> dict[str, Any] | None:
        session_ids = self.lineage_session_ids(session_id)
        return self.get_event_for_sessions(session_ids, event_id)

    def get_event_for_sessions(self, session_ids: list[str] | None, event_id: str) -> dict[str, Any] | None:
        params: list[Any] = [event_id]
        session_filter = ""
        if session_ids is not None:
            if not session_ids:
                return None
            placeholders = ", ".join("?" for _ in session_ids)
            session_filter = f"session_id IN ({placeholders}) AND "
            params = [*session_ids, event_id]
        with self.connect() as conn:
            row = conn.execute(
                f"SELECT event_json FROM events WHERE {session_filter}event_id = ?",
                params,
            ).fetchone()
            return json.loads(row["event_json"]) if row else None

    def search_events(
        self,
        session_id: str,
        query: str,
        top_k: int,
        *,
        event_types: list[str] | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.search_events_for_sessions(
            self.lineage_session_ids(session_id),
            query,
            top_k,
            event_types=event_types,
            after=after,
            before=before,
        )

    def search_events_for_sessions(
        self,
        session_ids: list[str] | None,
        query: str,
        top_k: int,
        *,
        event_types: list[str] | None = None,
        after: str | None = None,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        terms = [term.lower() for term in query.split() if term.strip()]
        params: list[Any] = []
        session_filter = ""
        if session_ids is not None:
            if not session_ids:
                return []
            placeholders = ", ".join("?" for _ in session_ids)
            session_filter = f"session_id IN ({placeholders}) AND "
            params.extend(session_ids)
        sql = f"""
            SELECT event_id, session_id, turn_id, type, timestamp, content_text, event_json, created_at_ms
            FROM events
            WHERE {session_filter}is_memory_read = 0
        """
        if event_types:
            placeholders = ", ".join("?" for _ in event_types)
            sql += f" AND type IN ({placeholders})"
            params.extend(event_types)
        if after is not None:
            sql += " AND timestamp >= ?"
            params.append(after)
        if before is not None:
            sql += " AND timestamp <= ?"
            params.append(before)
        sql += " ORDER BY created_at_ms DESC"
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        ranked: list[tuple[float, sqlite3.Row]] = []
        for row in rows:
            text = row["content_text"].lower()
            score = sum(1 for term in terms if term in text)
            if not terms:
                score = 1
            if score > 0:
                ranked.append((float(score), row))
        ranked.sort(key=lambda item: (item[0], item[1]["created_at_ms"]), reverse=True)
        results: list[dict[str, Any]] = []
        for score, row in ranked[:top_k]:
            results.append(
                {
                    "event_id": row["event_id"],
                    "session_id": row["session_id"],
                    "turn_id": row["turn_id"],
                    "type": row["type"],
                    "timestamp": row["timestamp"],
                    "score": score,
                    "snippet": row["content_text"][:240],
                    "reason": "KEYWORD_RECENCY",
                }
            )
        return results

    def child_events(self, session_id: str, event_id: str) -> list[dict[str, Any]]:
        children = []
        for lineage_session_id in self.lineage_session_ids(session_id):
            for event in self.list_events(lineage_session_id, include_memory_reads=True):
                if event_id in event.get("parent_event_ids", []):
                    children.append(event)
        return children

    def neighbor_events(self, session_id: str, event_id: str) -> list[dict[str, Any]]:
        seed = self.get_event(session_id, event_id)
        if not seed:
            return []
        neighbors: list[dict[str, Any]] = []
        for parent_id in seed.get("parent_event_ids", []):
            parent = self.get_event(session_id, parent_id)
            if parent:
                neighbors.append({"event_id": parent["event_id"], "edge": "PARENT", "type": parent["type"]})
        for child in self.child_events(session_id, event_id):
            neighbors.append({"event_id": child["event_id"], "edge": "CHILD", "type": child["type"]})
        return neighbors

    def put_turn(self, session_id: str, turn_id: str, data: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO turns(session_id, turn_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                (session_id, turn_id, canonical_json(data), now_ms()),
            )
            segment_id = f"segment-{session_id}"
            segment = {
                "schema_version": "mneme.segment.v0",
                "segment_id": segment_id,
                "session_id": session_id,
                "title": f"Session {session_id}",
                "summary": data.get("outcome", {}).get("summary", "Recorded session activity."),
                "status": "ACTIVE",
            }
            conn.execute(
                "INSERT OR REPLACE INTO segments(segment_id, session_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                (segment_id, session_id, canonical_json(segment), now_ms()),
            )

    def put_trace(self, trace: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO traces(trace_id, session_id, turn_id, data, created_at_ms) VALUES (?, ?, ?, ?, ?)",
                (trace["trace_id"], trace["session_id"], trace.get("turn_id"), canonical_json(trace), now_ms()),
            )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def add_audit(self, session_id: str, action: str, tool: str, event_ids: list[str], trace_id: str | None = None) -> dict[str, Any]:
        record = {
            "audit_id": new_id("audit"),
            "session_id": session_id,
            "action": action,
            "tool": tool,
            "event_ids": event_ids,
            "trace_id": trace_id,
            "created_at_ms": now_ms(),
        }
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO audit_records(audit_id, session_id, action, tool, event_ids, trace_id, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record["audit_id"], session_id, action, tool, canonical_json(event_ids), trace_id, record["created_at_ms"]),
            )
        return record

    def list_audit(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT audit_id, session_id, action, tool, event_ids, trace_id, created_at_ms FROM audit_records WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        return [
            {
                "audit_id": row["audit_id"],
                "session_id": row["session_id"],
                "action": row["action"],
                "tool": row["tool"],
                "event_ids": json.loads(row["event_ids"]),
                "trace_id": row["trace_id"],
                "created_at_ms": row["created_at_ms"],
            }
            for row in rows
        ]

    def list_segments(self, session_id: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        sql = "SELECT data FROM segments WHERE session_id = ? ORDER BY created_at_ms ASC"
        params: list[Any] = [session_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        segments = [json.loads(row["data"]) for row in rows]
        return self._rich_segments(session_id, segments)

    def _rich_segments(self, session_id: str, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events = self.list_events(session_id)
        state = self.execution_state_or_default(session_id)
        enrichment = state.get("enrichment") if isinstance(state.get("enrichment"), dict) else {}
        topic_tags = list(enrichment.get("topic_tags") or [])
        history = self.get_state_history(session_id, limit=1000)
        enriched: list[dict[str, Any]] = []
        for index, segment in enumerate(segments):
            segment_events = self.events_for_segment_data(events, segments, index)
            event_types: dict[str, int] = {}
            user_events: list[dict[str, Any]] = []
            for event in segment_events:
                event_type = str(event.get("type") or "")
                event_types[event_type] = event_types.get(event_type, 0) + 1
                if event_type == "USER_MESSAGE":
                    user_events.append(event)
            first_ts = segment_events[0]["timestamp"] if segment_events else segment.get("created_at")
            last_ts = segment_events[-1]["timestamp"] if segment_events else segment.get("updated_at") or first_ts
            first_user = user_events[0] if user_events else None
            last_user = user_events[-1] if user_events else None
            rich = dict(segment)
            rich["event_count"] = len(segment_events) if segment_events else int(segment.get("event_count") or 0)
            rich["events_by_type"] = event_types
            rich["first_ts"] = first_ts
            rich["last_ts"] = last_ts
            rich["first_user_snippet"] = text_from_event(first_user)[:200] if first_user else None
            rich["last_user_snippet"] = text_from_event(last_user)[:200] if last_user else None
            rich["goal_at_end"] = goal_at_timestamp(history, str(last_ts or "")) or state.get("goal") or None
            rich["topic_tags"] = topic_tags
            enriched.append(rich)
        return enriched

    def events_for_segment_data(
        self,
        events: list[dict[str, Any]],
        segments: list[dict[str, Any]],
        segment_index: int,
    ) -> list[dict[str, Any]]:
        segment = segments[segment_index]
        anchor_ids = set(segment.get("anchor_event_ids") or [])
        start = str(segment.get("created_at") or "")
        next_start = ""
        if segment_index + 1 < len(segments):
            next_start = str(segments[segment_index + 1].get("created_at") or "")
        selected: list[dict[str, Any]] = []
        for event in events:
            event_id = event.get("event_id")
            timestamp = str(event.get("timestamp") or "")
            if event_id in anchor_ids:
                selected.append(event)
                continue
            if start and timestamp < start:
                continue
            if next_start and timestamp >= next_start:
                continue
            if start:
                selected.append(event)
        return selected

    def segment_id_for_event(self, session_id: str, event_id: str) -> str | None:
        segments = self.list_segments(session_id)
        for segment in segments:
            if event_id in set(segment.get("anchor_event_ids") or []):
                return segment.get("segment_id")
        events = self.list_events(session_id)
        raw_segments = [strip_rich_segment_fields(segment) for segment in segments]
        for index, segment in enumerate(raw_segments):
            if any(event.get("event_id") == event_id for event in self.events_for_segment_data(events, raw_segments, index)):
                return segment.get("segment_id")
        return None

    def get_segment_skeleton(self, session_id: str, segment_id: str, max_events: int = 15) -> list[dict[str, Any]]:
        segments = self.list_segments(session_id)
        raw_segments = [strip_rich_segment_fields(segment) for segment in segments]
        segment_index = next((index for index, segment in enumerate(raw_segments) if segment.get("segment_id") == segment_id), None)
        if segment_index is None:
            return []
        events = self.events_for_segment_data(self.list_events(session_id), raw_segments, segment_index)
        user_events = [event for event in events if event.get("type") == "USER_MESSAGE"]
        tool_calls = [event for event in events if event.get("type") == "TOOL_CALL"]
        last_assistant = next((event for event in reversed(events) if event.get("type") == "ASSISTANT_MESSAGE"), None)
        by_id: dict[str, dict[str, Any]] = {event["event_id"]: event for event in user_events}
        for event in tool_calls:
            by_id.setdefault(event["event_id"], event)
        if last_assistant:
            by_id.setdefault(last_assistant["event_id"], last_assistant)
        ordered = sorted(by_id.values(), key=lambda event: event.get("timestamp") or "")
        if len(ordered) > max_events:
            head = ordered[:5]
            tail = ordered[-max(0, max_events - 5):]
            ordered = head + tail
        return [
            {
                "event_id": event["event_id"],
                "type": event["type"],
                "tool_name": event.get("tool", {}).get("name"),
                "timestamp": event["timestamp"],
                "snippet": text_from_event(event)[:200],
            }
            for event in ordered[:max_events]
        ]

    def latest_active_segment(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT data FROM segments
                WHERE session_id = ?
                ORDER BY created_at_ms DESC
                """,
                (session_id,),
            ).fetchall()
        for row in rows:
            segment = json.loads(row["data"])
            if segment.get("status") == "ACTIVE":
                return segment
        return None

    def segment_count(self, session_id: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM segments WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row["n"])

    def put_segment(self, segment: dict[str, Any]) -> None:
        segment_id = segment["segment_id"]
        session_id = segment["session_id"]
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at_ms FROM segments WHERE segment_id = ?",
                (segment_id,),
            ).fetchone()
            created_at_ms = int(existing["created_at_ms"]) if existing else now_ms()
            conn.execute(
                "INSERT OR REPLACE INTO segments(segment_id, session_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                (segment_id, session_id, canonical_json(segment), created_at_ms),
            )

    def export_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {}
        with self.connect() as conn:
            traces = [json.loads(row["data"]) for row in conn.execute("SELECT data FROM traces WHERE session_id = ?", (session_id,))]
            turns = [json.loads(row["data"]) for row in conn.execute("SELECT data FROM turns WHERE session_id = ?", (session_id,))]
            state_row = conn.execute(
                "SELECT state_json FROM execution_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            embeddings = [
                {
                    "event_id": row["event_id"],
                    "segment_id": row["segment_id"],
                    "embedding_model_id": row["embedding_model_id"],
                    "token_count": row["token_count"],
                    "type": row["type"],
                }
                for row in conn.execute(
                    """
                    SELECT event_id, segment_id, embedding_model_id, token_count, type
                    FROM embedding_index
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )
            ]
        return {
            "session": session,
            "events": self.list_events(session_id, include_memory_reads=True),
            "turns": turns,
            "traces": traces,
            "audit_records": self.list_audit(session_id),
            "segments": self.list_segments(session_id),
            "session_lineage": self.session_lineage_edges(session_id),
            "event_graph_edges": self.list_event_graph_edges(session_id),
            "embeddings": embeddings,
            "execution_state": json.loads(state_row["state_json"]) if state_row else None,
            "state_history": self.get_state_history(session_id, limit=1000),
        }

    def delete_session(self, session_id: str) -> bool:
        existed = self.has_session(session_id)
        with self.connect() as conn:
            for table in [
                "events",
                "turns",
                "traces",
                "audit_records",
                "segments",
                "event_graph_edges",
                "embedding_index",
                "embedding_metrics",
                "reranker_metrics",
                "enrichment_metrics",
                "execution_state",
                "state_history",
                "session_context_fill",
                "sessions",
            ]:
                conn.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))
            conn.execute(
                "DELETE FROM session_lineage WHERE old_session_id = ? OR new_session_id = ?",
                (session_id, session_id),
            )
        return existed

    def cost_report(self, session_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            events_count = conn.execute(
                "SELECT COUNT(*) AS n FROM events WHERE session_id = ? AND is_memory_read = 0",
                (session_id,),
            ).fetchone()["n"]
            prepare_rows = conn.execute(
                "SELECT data FROM traces WHERE session_id = ? AND json_extract(data, '$.trace_type') = 'CONTEXT_PREPARE'",
                (session_id,),
            ).fetchall()
            db_bytes = self.path.stat().st_size if self.path.exists() else 0
            index_bytes = conn.execute(
                "SELECT COALESCE(SUM(length(embedding)), 0) AS n FROM embedding_index WHERE session_id = ?",
                (session_id,),
            ).fetchone()["n"]
        embedding_metrics = self.embedding_metrics(session_id)
        reranker_metrics = self.reranker_metrics(session_id)
        enrichment_metrics = self.enrichment_metrics(session_id)
        latencies = [json.loads(row["data"]).get("latency_ms", {}).get("total", 0) for row in prepare_rows]
        latencies.sort()
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0
        embedded_hit_ratio = embedding_metrics["embedding_items"] / events_count if events_count else 0
        return {
            "schema_version": "mneme.cost_report.v0",
            "cost_model_version": "mneme.cost_model.v0",
            "session_id": session_id,
            "mode": "STANDARD",
            "events_ingested": events_count,
            "embedding_batches": embedding_metrics["embedding_batches"],
            "embedding_items": embedding_metrics["embedding_items"],
            "embedding_input_chars": embedding_metrics["embedding_input_chars"],
            "storage_bytes": db_bytes,
            "index_bytes": int(index_bytes or 0),
            "reranker_calls": reranker_metrics["reranker_calls"],
            "enrichment_calls": enrichment_metrics["enrichment_calls"],
            "prepare_calls": len(latencies),
            "prepare_latency_ms_p50": p50,
            "prepare_latency_ms_p95": p95,
            "assembled_prompt_tokens_avg": 0,
            "assembled_prompt_tokens_max": 0,
            "provider_prompt_tokens_with_mneme": 0,
            "provider_prompt_tokens_without_mneme_estimate": 0,
            "estimated_extra_cost": None,
            "cache": {"embedded_event_hit_ratio": embedded_hit_ratio},
            "failures": {
                "embedding_failures": embedding_metrics["embedding_failures"],
                "reranker_failures": reranker_metrics["reranker_failures"],
                "enrichment_failures": enrichment_metrics["enrichment_failures"],
                "prepare_failures": 0,
            },
        }


def graph_edge_type(parent: dict[str, Any] | None, child: dict[str, Any]) -> str:
    parent_type = parent.get("type") if parent else None
    child_type = child.get("type")
    if parent_type == "TOOL_CALL" and child_type == "TOOL_OUTPUT":
        return "TOOL_RESULT"
    if child_type == "DECISION":
        return "DECISION_FOLLOWS"
    return "FOLLOWS"


def graph_edge_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema_version": "mneme.graph_edge.v0",
        "source_event_id": row["source_event_id"],
        "target_event_id": row["target_event_id"],
        "session_id": row["session_id"],
        "edge_type": row["edge_type"],
        "weight": row["weight"],
    }
