from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

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

SESSION_DISCOVERY_METADATA_KEYS = (
    "cwd",
    "thread_id",
    "source",
    "transcript_path",
)

AUTH_FAILURE_SESSION_ID = "__auth_failure__"
CURRENT_SCHEMA_VERSION = 1
SQLITE_BUSY_TIMEOUT_MS = 5000
DESTRUCTIVE_MIGRATIONS_BY_SOURCE_VERSION: dict[int, tuple[str, ...]] = {}
FORENSIC_AUDIT_ACTIONS = {
    "MEMORY_READ",
    "SESSION_EXPORT",
    "SESSION_DELETE",
    "AUTH_FAILURE",
    "RETENTION_CLEANUP",
    "MAINTENANCE_SYSTEM_SWEEP",
}


class WriterQueueFull(RuntimeError):
    pass


class StorageBusy(RuntimeError):
    pass


class WriterLane:
    def __init__(self, max_queue_depth: int) -> None:
        self.max_queue_depth = max(1, int(max_queue_depth))
        self._slots = threading.BoundedSemaphore(self.max_queue_depth)
        self._lock = threading.Lock()
        self._in_use = 0

    @contextmanager
    def enter(self) -> Iterator[None]:
        acquired = self._slots.acquire(blocking=False)
        if not acquired:
            raise WriterQueueFull("WRITER_QUEUE_FULL")
        try:
            with self._lock:
                self._in_use += 1
            with self._lock:
                yield
        finally:
            with self._lock:
                self._in_use -= 1
            self._slots.release()

    @property
    def depth(self) -> int:
        with self._lock:
            return max(0, self._in_use)

    @property
    def backlog(self) -> int:
        return self.depth


def is_sqlite_busy_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "locked" in message or "busy" in message


def text_from_event(event: dict[str, Any] | None) -> str:
    if not event:
        return ""
    return text_from_content(event.get("content", {}))


def session_project_key(session: dict[str, Any]) -> str | None:
    privacy = session.get("privacy") if isinstance(session.get("privacy"), dict) else {}
    project_key = privacy.get("project_isolation_key")
    if isinstance(project_key, str) and project_key:
        return project_key
    project_id = session.get("project_id")
    return project_id if isinstance(project_id, str) and project_id else None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def blob_bytes_ref(blob: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": "BYTES_REF",
        "uri": blob["uri"],
        "hash": blob["hash"],
        "size_bytes": blob["size_bytes"],
        "media_type": blob["media_type"],
        "storage_owner": "SERVER",
    }


def blob_record_from_row(row: sqlite3.Row) -> dict[str, Any]:
    metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
    record = {
        "schema_version": "mneme.blob.v0",
        "blob_id": row["blob_id"],
        "uri": row["uri"],
        "owner": row["owner"],
        "session_id": row["session_id"],
        "project_isolation_key": row["project_isolation_key"],
        "hash": row["hash"],
        "size_bytes": int(row["size_bytes"]),
        "media_type": row["media_type"],
        "created_at": row["created_at"],
        "ref_count": int(row["ref_count"]),
        "retention": {
            "delete_with_session": bool(row["delete_with_session"]),
            "expires_at": row["expires_at"],
        },
        "metadata": metadata,
    }
    record["bytes_ref"] = blob_bytes_ref(record)
    return record


def salted_hash(value: str | None, salt: str) -> str | None:
    if not value:
        return None
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


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


def session_matches(
    session: dict[str, Any],
    *,
    query: str | None,
    project_path: str | None,
    thread_id: str | None,
    slug: str | None,
) -> bool:
    if not any([query, project_path, thread_id, slug]):
        return True
    fields = session_discovery_fields(session)
    if thread_id and normalize_match_value(thread_id) not in {normalize_match_value(value) for value in fields["thread_ids"]}:
        return False
    if project_path and not any(matches_text(value, project_path) for value in fields["project_paths"]):
        return False
    if slug and not any(matches_slug(value, slug) for value in fields["all"]):
        return False
    if query and not any(matches_text(value, query) for value in fields["all"]):
        return False
    return True


def session_discovery_fields(session: dict[str, Any]) -> dict[str, list[str]]:
    metadata = session.get("metadata") if isinstance(session.get("metadata"), dict) else {}
    base_fields = [
        session.get("session_id"),
        session.get("agent_id"),
        session.get("runtime"),
        session.get("project_id"),
        session.get("started_at"),
    ]
    metadata_fields = [
        metadata.get(key)
        for key in SESSION_DISCOVERY_METADATA_KEYS
    ]
    project_paths = [session.get("project_id"), metadata.get("cwd"), metadata.get("transcript_path")]
    thread_ids = [session.get("session_id"), metadata.get("thread_id")]
    return {
        "all": [str(value) for value in [*base_fields, *metadata_fields] if isinstance(value, str) and value],
        "project_paths": [str(value) for value in project_paths if isinstance(value, str) and value],
        "thread_ids": [str(value) for value in thread_ids if isinstance(value, str) and value],
    }


def matches_text(value: str, needle: str) -> bool:
    haystack = normalize_match_value(value)
    target = normalize_match_value(needle)
    return bool(target) and (target in haystack or haystack in target)


def matches_slug(value: str, slug: str) -> bool:
    target = normalize_match_value(slug)
    if not target:
        return False
    candidates = {normalize_match_value(value)}
    try:
        candidates.add(normalize_match_value(Path(value).name))
    except (OSError, ValueError):
        pass
    return any(target == candidate or target in candidate for candidate in candidates if candidate)


def normalize_match_value(value: str) -> str:
    return value.strip().lower()


class Store:
    def __init__(
        self,
        path: Path,
        *,
        max_writer_queue_depth: int = 1000,
        startup_integrity_check: bool = True,
        backup_before_migrate: Path | str | None = None,
        no_backup_before_migrate: bool = False,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._enforce_owner_only_permissions(self.path.parent, 0o700)
        self.startup_integrity_check = startup_integrity_check
        self.backup_before_migrate = Path(backup_before_migrate) if backup_before_migrate else None
        self.no_backup_before_migrate = no_backup_before_migrate
        self.migration_backup_result: dict[str, Any] = {
            "backup_path": None,
            "operator_bypass": False,
            "destructive_migrations": [],
        }
        self._init()
        if self.path.exists():
            self._enforce_owner_only_permissions(self.path, 0o600)
        self._writer_lane = WriterLane(max_writer_queue_depth)

    @property
    def writer_queue_depth(self) -> int:
        return self._writer_lane.depth

    @property
    def writer_queue_backlog(self) -> int:
        return self._writer_lane.backlog

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
        return conn

    @contextmanager
    def write_connect(self) -> Iterator[sqlite3.Connection]:
        with self._writer_lane.enter():
            try:
                with self.connect() as conn:
                    yield conn
            except sqlite3.OperationalError as exc:
                if is_sqlite_busy_error(exc):
                    raise StorageBusy("SQLITE_STORAGE_BUSY") from exc
                raise

    def backup_to(self, backup_path: Path | str) -> dict[str, Any]:
        target = Path(backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, sqlite3.connect(target) as backup:
            source.backup(backup)
        result = self.verify_backup(target)
        result["backup_path"] = str(target)
        return result

    @classmethod
    def restore_from_backup(
        cls,
        backup_path: Path | str,
        target_path: Path | str,
        *,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        source_path = Path(backup_path)
        target = Path(target_path)
        cls.verify_backup(source_path)
        if target.exists() and not overwrite:
            raise RuntimeError("RESTORE_TARGET_EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(source_path) as source, sqlite3.connect(target) as restored:
                source.backup(restored)
            result = cls.verify_backup(target)
        except Exception:
            if target.exists():
                target.unlink()
            raise
        result["backup_path"] = str(source_path)
        result["target_path"] = str(target)
        return result

    @staticmethod
    def verify_backup(
        path: Path | str,
        *,
        expected_schema_version: int = CURRENT_SCHEMA_VERSION,
    ) -> dict[str, Any]:
        backup_path = Path(path)
        with sqlite3.connect(backup_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("PRAGMA integrity_check").fetchone()
            integrity = str(row[0]) if row else "missing"
            if integrity.lower() != "ok":
                raise RuntimeError("SQLITE_INTEGRITY_CHECK_FAILED")
            schema_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if schema_version != expected_schema_version:
                raise RuntimeError("BACKUP_SCHEMA_VERSION_MISMATCH")
            has_migration_table = (
                conn.execute(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'schema_migrations'
                    """
                ).fetchone()
                is not None
            )
            if not has_migration_table:
                raise RuntimeError("BACKUP_SCHEMA_MIGRATIONS_MISSING")
            migration_row = conn.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
            migration_version = int(migration_row["version"] or 0)
            if migration_version != schema_version:
                raise RuntimeError("BACKUP_SCHEMA_VERSION_MISMATCH")
            has_blob_table = (
                conn.execute(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'blobs'
                    """
                ).fetchone()
                is not None
            )
            if not has_blob_table and expected_schema_version >= CURRENT_SCHEMA_VERSION:
                raise RuntimeError("BACKUP_BLOBS_TABLE_MISSING")
            blob_rows = conn.execute("SELECT blob_id, hash, content FROM blobs").fetchall() if has_blob_table else []
            for blob in blob_rows:
                content = bytes(blob["content"])
                actual_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
                if actual_hash != blob["hash"]:
                    raise RuntimeError("BLOB_HASH_MISMATCH")
            return {
                "schema_version": schema_version,
                "blob_count": len(blob_rows),
                "integrity": integrity,
            }

    def _init(self) -> None:
        with self.connect() as conn:
            self._check_schema_compatibility(conn)
            self._check_integrity(conn)
            self._ensure_backup_before_destructive_migration(conn)
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version INTEGER PRIMARY KEY,
                  name TEXT NOT NULL,
                  applied_at TEXT NOT NULL
                );
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
                  project_isolation_key TEXT,
                  action TEXT NOT NULL,
                  tool TEXT NOT NULL,
                  event_ids TEXT NOT NULL,
                  trace_id TEXT,
                  principal_json TEXT NOT NULL DEFAULT '{}',
                  request_json TEXT NOT NULL DEFAULT '{}',
                  result_json TEXT NOT NULL DEFAULT '{}',
                  created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_records (
                  principal_name TEXT NOT NULL,
                  method TEXT NOT NULL,
                  path TEXT NOT NULL,
                  idempotency_key TEXT NOT NULL,
                  request_hash TEXT NOT NULL,
                  response_json TEXT NOT NULL,
                  status_code INTEGER NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (principal_name, method, path, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS reindex_jobs (
                  job_id TEXT PRIMARY KEY,
                  scope TEXT NOT NULL,
                  project_isolation_key TEXT,
                  session_id TEXT,
                  status TEXT NOT NULL,
                  data_json TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  updated_at_ms INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_reindex_jobs_scope
                  ON reindex_jobs(scope, project_isolation_key, session_id);
                CREATE INDEX IF NOT EXISTS idx_reindex_jobs_status
                  ON reindex_jobs(status, created_at_ms);
                CREATE TABLE IF NOT EXISTS blobs (
                  blob_id TEXT PRIMARY KEY,
                  uri TEXT NOT NULL UNIQUE,
                  owner TEXT NOT NULL,
                  session_id TEXT NOT NULL,
                  project_isolation_key TEXT NOT NULL,
                  hash TEXT NOT NULL,
                  size_bytes INTEGER NOT NULL,
                  media_type TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  ref_count INTEGER NOT NULL DEFAULT 0,
                  delete_with_session INTEGER NOT NULL DEFAULT 1,
                  expires_at TEXT,
                  metadata_json TEXT NOT NULL,
                  content BLOB NOT NULL,
                  created_at_ms INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_blobs_session
                  ON blobs(session_id, project_isolation_key);
                CREATE INDEX IF NOT EXISTS idx_blobs_hash
                  ON blobs(hash);
                CREATE TABLE IF NOT EXISTS blob_references (
                  blob_id TEXT NOT NULL,
                  session_id TEXT NOT NULL,
                  event_id TEXT NOT NULL,
                  created_at_ms INTEGER NOT NULL,
                  PRIMARY KEY (blob_id, session_id, event_id)
                );
                CREATE INDEX IF NOT EXISTS idx_blob_references_session
                  ON blob_references(session_id, blob_id);
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
            self._ensure_audit_columns(conn)
            self._ensure_state_history_columns(conn)
            self._record_current_schema(conn)

    def _enforce_owner_only_permissions(self, path: Path, mode: int) -> None:
        if os.name != "posix":
            return
        try:
            path.chmod(mode)
        except FileNotFoundError:
            return

    def _check_schema_compatibility(self, conn: sqlite3.Connection) -> None:
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if user_version > CURRENT_SCHEMA_VERSION:
            raise RuntimeError("SCHEMA_VERSION_UNKNOWN_NEWER")
        has_migration_table = (
            conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'schema_migrations'
                """
            ).fetchone()
            is not None
        )
        if not has_migration_table:
            return
        row = conn.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
        migration_version = int(row["version"] or 0)
        if migration_version != user_version:
            raise RuntimeError("SCHEMA_VERSION_MISMATCH")

    def _check_integrity(self, conn: sqlite3.Connection) -> None:
        if not self.startup_integrity_check:
            return
        row = conn.execute("PRAGMA integrity_check").fetchone()
        result = str(row[0]) if row else "missing"
        if result.lower() != "ok":
            raise RuntimeError("SQLITE_INTEGRITY_CHECK_FAILED")

    def _ensure_backup_before_destructive_migration(self, conn: sqlite3.Connection) -> None:
        user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        if user_version >= CURRENT_SCHEMA_VERSION:
            return
        has_migration_table = (
            conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'schema_migrations'
                """
            ).fetchone()
            is not None
        )
        if not has_migration_table:
            return
        destructive_migrations = tuple(DESTRUCTIVE_MIGRATIONS_BY_SOURCE_VERSION.get(user_version, ()))
        if not destructive_migrations:
            return
        if self.backup_before_migrate is None and not self.no_backup_before_migrate:
            raise RuntimeError("BACKUP_REQUIRED_BEFORE_DESTRUCTIVE_MIGRATION")
        if self.backup_before_migrate is not None:
            self.migration_backup_result = self._backup_legacy_database(
                self.backup_before_migrate,
                expected_schema_version=user_version,
                destructive_migrations=destructive_migrations,
            )
            return
        self.migration_backup_result = {
            "backup_path": None,
            "operator_bypass": True,
            "destructive_migrations": list(destructive_migrations),
            "schema_version": user_version,
        }

    def _backup_legacy_database(
        self,
        backup_path: Path,
        *,
        expected_schema_version: int,
        destructive_migrations: Sequence[str],
    ) -> dict[str, Any]:
        target = Path(backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source, sqlite3.connect(target) as backup:
            source.backup(backup)
        result = self.verify_backup(target, expected_schema_version=expected_schema_version)
        result["backup_path"] = str(target)
        result["operator_bypass"] = False
        result["destructive_migrations"] = list(destructive_migrations)
        return result

    def _record_current_schema(self, conn: sqlite3.Connection) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        conn.execute(
            """
            INSERT OR IGNORE INTO schema_migrations(version, name, applied_at)
            VALUES (?, ?, ?)
            """,
            (CURRENT_SCHEMA_VERSION, "initial_v0_schema", now),
        )
        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")

    def get_idempotency_record(
        self,
        *,
        principal_name: str,
        method: str,
        path: str,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT request_hash, response_json, status_code
                FROM idempotency_records
                WHERE principal_name = ?
                  AND method = ?
                  AND path = ?
                  AND idempotency_key = ?
                """,
                (principal_name, method, path, idempotency_key),
            ).fetchone()
        if not row:
            return None
        return {
            "request_hash": row["request_hash"],
            "response": json.loads(row["response_json"]),
            "status_code": int(row["status_code"]),
        }

    def put_idempotency_record(
        self,
        *,
        principal_name: str,
        method: str,
        path: str,
        idempotency_key: str,
        request_hash: str,
        response: dict[str, Any],
        status_code: int = 200,
    ) -> None:
        with self.write_connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO idempotency_records(
                  principal_name, method, path, idempotency_key, request_hash,
                  response_json, status_code, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    principal_name,
                    method,
                    path,
                    idempotency_key,
                    request_hash,
                    canonical_json(response),
                    int(status_code),
                    now_ms(),
                ),
            )

    def put_reindex_job(self, job: dict[str, Any]) -> None:
        now = now_ms()
        with self.write_connect() as conn:
            conn.execute(
                """
                INSERT INTO reindex_jobs(
                  job_id, scope, project_isolation_key, session_id, status,
                  data_json, created_at_ms, updated_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_id"],
                    job["scope"],
                    job.get("project_isolation_key"),
                    job.get("session_id"),
                    job["status"],
                    canonical_json(job),
                    now,
                    now,
                ),
            )

    def get_reindex_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data_json FROM reindex_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return json.loads(row["data_json"]) if row else None

    def update_reindex_job(self, job: dict[str, Any]) -> None:
        with self.write_connect() as conn:
            conn.execute(
                """
                UPDATE reindex_jobs
                SET status = ?, data_json = ?, updated_at_ms = ?
                WHERE job_id = ?
                """,
                (
                    job["status"],
                    canonical_json(job),
                    now_ms(),
                    job["job_id"],
                ),
            )

    def update_event_embedding_status(
        self,
        *,
        session_id: str,
        event_id: str,
        status: str,
        reason: str | None = None,
    ) -> None:
        with self.write_connect() as conn:
            row = conn.execute(
                "SELECT event_json FROM events WHERE session_id = ? AND event_id = ?",
                (session_id, event_id),
            ).fetchone()
            if row is None:
                return
            event = json.loads(row["event_json"])
            ingestion = event.get("ingestion") if isinstance(event.get("ingestion"), dict) else {}
            ingestion["embedding_status"] = status
            if reason:
                ingestion["embedding_error_reason"] = reason
            event["ingestion"] = ingestion
            conn.execute(
                "UPDATE events SET event_json = ? WHERE session_id = ? AND event_id = ?",
                (canonical_json(event), session_id, event_id),
            )

    def list_reindex_jobs(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT data_json FROM reindex_jobs ORDER BY created_at_ms, job_id"
            ).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def count_reindex_candidates(
        self,
        *,
        scope: str,
        project_isolation_key: str | None,
        session_id: str | None,
        statuses: list[str],
        force: bool,
        max_job_events: int,
        embedding_model_id: str | None = None,
    ) -> int:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT e.event_id, e.session_id, e.event_json, s.data AS session_json
                FROM events e
                JOIN sessions s ON s.session_id = e.session_id
                WHERE e.is_memory_read = 0
                ORDER BY e.created_at_ms, e.event_id
                """
            ).fetchall()
            indexed_event_ids: set[str] = set()
            if embedding_model_id:
                indexed_event_ids = {
                    row["event_id"]
                    for row in conn.execute(
                        "SELECT event_id FROM embedding_index WHERE embedding_model_id = ?",
                        (embedding_model_id,),
                    ).fetchall()
                }
        requested_statuses = {status.upper() for status in statuses}
        count = 0
        limit = max(1, int(max_job_events))
        for row in rows:
            try:
                session = json.loads(row["session_json"])
                event = json.loads(row["event_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            event_session_id = str(row["session_id"])
            event_project_key = session_project_key(session)
            if scope == "PROJECT" and event_project_key != project_isolation_key:
                continue
            if scope == "SESSION" and event_session_id != session_id:
                continue
            if not force:
                ingestion = event.get("ingestion") if isinstance(event.get("ingestion"), dict) else {}
                embedding_status = str(ingestion.get("embedding_status") or "").upper()
                missing_active_embedding = bool(
                    embedding_model_id and row["event_id"] not in indexed_event_ids
                )
                if embedding_status not in requested_statuses and not (
                    "PENDING" in requested_statuses and missing_active_embedding
                ):
                    continue
            count += 1
            if count >= limit:
                break
        return count

    def list_reindex_candidates(
        self,
        *,
        scope: str,
        project_isolation_key: str | None,
        session_id: str | None,
        statuses: list[str],
        force: bool,
        embedding_model_id: str | None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT e.event_id, e.session_id, e.event_json, s.data AS session_json
                FROM events e
                JOIN sessions s ON s.session_id = e.session_id
                WHERE e.is_memory_read = 0
                ORDER BY e.created_at_ms, e.event_id
                """
            ).fetchall()
            indexed_event_ids: set[str] = set()
            if embedding_model_id:
                indexed_event_ids = {
                    row["event_id"]
                    for row in conn.execute(
                        "SELECT event_id FROM embedding_index WHERE embedding_model_id = ?",
                        (embedding_model_id,),
                    ).fetchall()
                }
        requested_statuses = {status.upper() for status in statuses}
        candidates: list[dict[str, Any]] = []
        skipped = 0
        for row in rows:
            try:
                session = json.loads(row["session_json"])
                event = json.loads(row["event_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            event_session_id = str(row["session_id"])
            event_project_key = session_project_key(session)
            if scope == "PROJECT" and event_project_key != project_isolation_key:
                continue
            if scope == "SESSION" and event_session_id != session_id:
                continue
            if not force:
                ingestion = event.get("ingestion") if isinstance(event.get("ingestion"), dict) else {}
                embedding_status = str(ingestion.get("embedding_status") or "").upper()
                missing_active_embedding = bool(
                    embedding_model_id and row["event_id"] not in indexed_event_ids
                )
                if embedding_status not in requested_statuses and not (
                    "PENDING" in requested_statuses and missing_active_embedding
                ):
                    continue
            if skipped < offset:
                skipped += 1
                continue
            candidates.append(event)
            if len(candidates) >= max(1, int(limit)):
                break
        return candidates

    def put_blob(
        self,
        *,
        session_id: str,
        project_isolation_key: str,
        content: bytes,
        media_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        blob_id = new_id("blob")
        content_hash = f"sha256:{hashlib.sha256(content).hexdigest()}"
        with self.write_connect() as conn:
            conn.execute(
                """
                INSERT INTO blobs(
                  blob_id, uri, owner, session_id, project_isolation_key, hash,
                  size_bytes, media_type, created_at, ref_count,
                  delete_with_session, expires_at, metadata_json, content,
                  created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    blob_id,
                    f"mneme-blob://{blob_id}",
                    "SERVER",
                    session_id,
                    project_isolation_key,
                    content_hash,
                    len(content),
                    media_type,
                    utc_now_iso(),
                    0,
                    1,
                    None,
                    canonical_json(metadata or {}),
                    content,
                    now_ms(),
                ),
            )
        blob = self.get_blob_metadata(blob_id)
        if blob is None:
            raise RuntimeError("BLOB_WRITE_NOT_VISIBLE")
        return blob

    def put_blob_records_and_events(
        self,
        *,
        blob_records: list[dict[str, Any]],
        event_records: list[dict[str, Any]],
    ) -> None:
        with self.write_connect() as conn:
            for blob in blob_records:
                conn.execute(
                    """
                    INSERT INTO blobs(
                      blob_id, uri, owner, session_id, project_isolation_key,
                      hash, size_bytes, media_type, created_at, ref_count,
                      delete_with_session, expires_at, metadata_json, content,
                      created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        blob["blob_id"],
                        blob["uri"],
                        blob.get("owner", "SERVER"),
                        blob["session_id"],
                        blob["project_isolation_key"],
                        blob["hash"],
                        int(blob["size_bytes"]),
                        blob["media_type"],
                        blob["created_at"],
                        0,
                        1 if blob.get("delete_with_session", True) else 0,
                        blob.get("expires_at"),
                        canonical_json(blob.get("metadata") or {}),
                        blob["content"],
                        now_ms(),
                    ),
                )
            for record in event_records:
                event = record["event"]
                conn.execute(
                    """
                    INSERT INTO events(
                      event_id, session_id, turn_id, agent_id, runtime, role,
                      type, timestamp, content_text, event_json,
                      immutable_hash, parent_event_ids, token_estimate,
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
                        record["content_text"],
                        canonical_json(event),
                        record["immutable_hash"],
                        canonical_json(event.get("parent_event_ids", [])),
                        int(event.get("token_estimate") or 0),
                        1 if record.get("is_memory_read") else 0,
                        now_ms(),
                    ),
                )
                for blob_id in record.get("blob_ref_ids", []):
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO blob_references(
                          blob_id, session_id, event_id, created_at_ms
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (blob_id, event["session_id"], event["event_id"], now_ms()),
                    )
                    if cursor.rowcount > 0:
                        conn.execute(
                            "UPDATE blobs SET ref_count = ref_count + 1 WHERE blob_id = ?",
                            (blob_id,),
                        )

    def get_blob_metadata(self, blob_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT blob_id, uri, owner, session_id, project_isolation_key,
                       hash, size_bytes, media_type, created_at, ref_count,
                       delete_with_session, expires_at, metadata_json
                FROM blobs
                WHERE blob_id = ?
                """,
                (blob_id,),
            ).fetchone()
        return blob_record_from_row(row) if row else None

    def get_blob_content(self, blob_id: str) -> bytes | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT content FROM blobs WHERE blob_id = ?",
                (blob_id,),
            ).fetchone()
        return bytes(row["content"]) if row else None

    def count_blobs_for_session(self, session_id: str) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM blobs WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row["n"]) if row else 0

    def list_blob_metadata_for_session(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT blob_id, uri, owner, session_id, project_isolation_key,
                       hash, size_bytes, media_type, created_at, ref_count,
                       delete_with_session, expires_at, metadata_json
                FROM blobs
                WHERE session_id = ?
                ORDER BY created_at_ms, blob_id
                """,
                (session_id,),
            ).fetchall()
        return [blob_record_from_row(row) for row in rows]

    def garbage_collect_blobs(
        self,
        *,
        project_isolation_key: str | None = None,
        session_id: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        clauses = ["ref_count = 0"]
        params: list[Any] = []
        if project_isolation_key is not None:
            clauses.append("project_isolation_key = ?")
            params.append(project_isolation_key)
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = " AND ".join(clauses)
        with self.write_connect() as conn:
            candidates = [
                row["blob_id"]
                for row in conn.execute(
                    f"SELECT blob_id FROM blobs WHERE {where} ORDER BY created_at_ms, blob_id",
                    params,
                ).fetchall()
            ]
            deleted_count = 0
            if candidates and not dry_run:
                placeholders = ", ".join("?" for _ in candidates)
                conn.execute(
                    f"DELETE FROM blob_references WHERE blob_id IN ({placeholders})",
                    candidates,
                )
                cursor = conn.execute(
                    f"DELETE FROM blobs WHERE blob_id IN ({placeholders})",
                    candidates,
                )
                deleted_count = int(cursor.rowcount)
        return {
            "candidate_count": len(candidates),
            "deleted_count": deleted_count,
            "skipped_count": 0,
            "dry_run": dry_run,
            "warnings": [],
        }

    def delete_blob(self, blob_id: str) -> bool:
        with self.write_connect() as conn:
            row = conn.execute(
                "SELECT ref_count FROM blobs WHERE blob_id = ?",
                (blob_id,),
            ).fetchone()
            if not row:
                return False
            if int(row["ref_count"]) > 0:
                return False
            conn.execute("DELETE FROM blobs WHERE blob_id = ?", (blob_id,))
        return True

    def attach_blob_reference(self, *, blob_id: str, session_id: str, event_id: str) -> bool:
        with self.write_connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO blob_references(
                  blob_id, session_id, event_id, created_at_ms
                ) VALUES (?, ?, ?, ?)
                """,
                (blob_id, session_id, event_id, now_ms()),
            )
            if cursor.rowcount <= 0:
                return False
            conn.execute(
                "UPDATE blobs SET ref_count = ref_count + 1 WHERE blob_id = ?",
                (blob_id,),
            )
        return True

    def detach_blob_reference(self, *, blob_id: str, session_id: str, event_id: str) -> bool:
        with self.write_connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM blob_references
                WHERE blob_id = ? AND session_id = ? AND event_id = ?
                """,
                (blob_id, session_id, event_id),
            )
            if cursor.rowcount <= 0:
                return False
            conn.execute(
                "UPDATE blobs SET ref_count = MAX(ref_count - 1, 0) WHERE blob_id = ?",
                (blob_id,),
            )
        return True

    def _ensure_audit_columns(self, conn: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(audit_records)").fetchall()
        }
        additions = {
            "project_isolation_key": "TEXT",
            "principal_json": "TEXT NOT NULL DEFAULT '{}'",
            "request_json": "TEXT NOT NULL DEFAULT '{}'",
            "result_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE audit_records ADD COLUMN {name} {definition}")

    def _ensure_state_history_columns(self, conn: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(state_history)").fetchall()
        }
        additions = {
            "mode": "TEXT",
            "changed_fields_json": "TEXT NOT NULL DEFAULT '[]'",
            "state_hash": "TEXT",
            "previous_state_hash": "TEXT",
            "provenance_json": "TEXT NOT NULL DEFAULT '{}'",
            "summary_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE state_history ADD COLUMN {name} {definition}")

    def has_session(self, session_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return row is not None

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def session_project_key(self, session_id: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT project_isolation_key FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row["project_isolation_key"] if row else None

    def session_ids_for_project(self, project_isolation_key: str) -> list[str]:
        return self.session_ids_for_projects([project_isolation_key])

    def session_ids_for_projects(self, project_isolation_keys: list[str]) -> list[str]:
        if not project_isolation_keys:
            return []
        placeholders = ", ".join("?" for _ in project_isolation_keys)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT session_id
                FROM sessions
                WHERE project_isolation_key IN ({placeholders})
                ORDER BY created_at_ms ASC
                """,
                project_isolation_keys,
            ).fetchall()
        return [row["session_id"] for row in rows]

    def get_session_summary(self, session_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data, created_at_ms FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return self.session_summary(json.loads(row["data"]), int(row["created_at_ms"]))

    def list_sessions(
        self,
        *,
        query: str | None = None,
        project_path: str | None = None,
        thread_id: str | None = None,
        slug: str | None = None,
        project_isolation_keys: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return self.list_sessions_page(
            query=query,
            project_path=project_path,
            thread_id=thread_id,
            slug=slug,
            project_isolation_keys=project_isolation_keys,
            page_size=limit,
            page_token=None,
        )["sessions"]

    def list_sessions_page(
        self,
        *,
        query: str | None = None,
        project_path: str | None = None,
        thread_id: str | None = None,
        slug: str | None = None,
        project_isolation_keys: list[str] | None = None,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT data, created_at_ms FROM sessions"
            ).fetchall()
        summaries: list[dict[str, Any]] = []
        allowed_projects = set(project_isolation_keys) if project_isolation_keys is not None else None
        sorted_rows = sorted(
            rows,
            key=lambda row: (-int(row["created_at_ms"]), str(json.loads(row["data"]).get("session_id") or "")),
        )
        for row in sorted_rows:
            session = json.loads(row["data"])
            project_key = session_project_key(session)
            if allowed_projects is not None and project_key not in allowed_projects:
                continue
            if not session_matches(
                session,
                query=query,
                project_path=project_path,
                thread_id=thread_id,
                slug=slug,
            ):
                continue
            summaries.append(self.session_summary(session, int(row["created_at_ms"])))
        offset = int(page_token or 0)
        end = offset + int(page_size)
        page = summaries[offset:end]
        next_page_token = str(end) if end < len(summaries) else None
        return {
            "sessions": page,
            "count": len(page),
            "next_page_token": next_page_token,
            "matches_truncated": next_page_token is not None,
            "total_matches": len(summaries),
        }

    def session_summary(self, session: dict[str, Any], created_at_ms: int) -> dict[str, Any]:
        session_id = str(session.get("session_id") or "")
        metadata = session.get("metadata") if isinstance(session.get("metadata"), dict) else {}
        safe_metadata = {
            key: metadata[key]
            for key in SESSION_DISCOVERY_METADATA_KEYS
            if isinstance(metadata.get(key), str) and metadata.get(key)
        }
        counts = self.session_counts(session_id)
        latest_event_timestamp = self.latest_event_timestamp(session_id)
        return {
            "session_id": session_id,
            "agent_id": session.get("agent_id"),
            "runtime": session.get("runtime"),
            "project_id": session.get("project_id"),
            "project_isolation_key": session_project_key(session),
            "status": session.get("status", "ACTIVE"),
            "started_at": session.get("started_at"),
            "ended_at": session.get("ended_at"),
            "created_at_ms": created_at_ms,
            "metadata": safe_metadata,
            "event_count": counts["event_count"],
            "turn_count": counts["turn_count"],
            "latest_event_timestamp": latest_event_timestamp,
        }

    def put_session(self, data: dict[str, Any]) -> bool:
        session_id = data["session_id"]
        project_key = session_project_key(data)
        with self.write_connect() as conn:
            existing = conn.execute("SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO sessions(session_id, data, project_isolation_key, created_at_ms) VALUES (?, ?, ?, ?)",
                (session_id, canonical_json(data), project_key, now_ms()),
            )
            return True

    def close_session(self, session_id: str, ended_at: str) -> tuple[dict[str, Any], bool] | None:
        with self.write_connect() as conn:
            row = conn.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if row is None:
                return None
            session = json.loads(row["data"])
            if session.get("status") == "ENDED":
                return session, False
            session["status"] = "ENDED"
            session["ended_at"] = ended_at
            conn.execute(
                "UPDATE sessions SET data = ? WHERE session_id = ?",
                (canonical_json(session), session_id),
            )
            return session, True

    def latest_event_timestamp(self, session_id: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT timestamp
                FROM events
                WHERE session_id = ? AND is_memory_read = 0
                ORDER BY created_at_ms DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        return row["timestamp"] if row else None

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

    def retention_candidate_counts(self, session_id: str, cutoff_timestamp: str) -> dict[str, int]:
        with self.connect() as conn:
            event_count = conn.execute(
                """
                SELECT COUNT(*) AS n
                FROM events
                WHERE session_id = ? AND is_memory_read = 0 AND timestamp < ?
                """,
                (session_id, cutoff_timestamp),
            ).fetchone()["n"]
        return {"events": int(event_count), "derived_records": 0, "blobs": 0}

    def cleanup_retention(self, session_id: str, cutoff_timestamp: str, *, dry_run: bool) -> dict[str, Any]:
        with self.write_connect() as conn:
            event_ids = [
                row["event_id"]
                for row in conn.execute(
                    """
                    SELECT event_id
                    FROM events
                    WHERE session_id = ? AND is_memory_read = 0 AND timestamp < ?
                    ORDER BY created_at_ms, event_id
                    """,
                    (session_id, cutoff_timestamp),
                ).fetchall()
            ]
            if not event_ids:
                return {
                    "candidate_counts": {"events": 0, "derived_records": 0, "blobs": 0},
                    "deleted_counts": {
                        "events": 0,
                        "derived_records": 0,
                        "traces": 0,
                        "state_history": 0,
                        "graph_edges": 0,
                        "blobs": 0,
                    },
                }
            placeholders = ", ".join("?" for _ in event_ids)
            embedding_count = int(
                conn.execute(
                    f"SELECT COUNT(*) AS n FROM embedding_index WHERE event_id IN ({placeholders})",
                    event_ids,
                ).fetchone()["n"]
            )
            graph_edge_count = int(
                conn.execute(
                    f"""
                    SELECT COUNT(*) AS n
                    FROM event_graph_edges
                    WHERE session_id = ?
                      AND (source_event_id IN ({placeholders}) OR target_event_id IN ({placeholders}))
                    """,
                    [session_id, *event_ids, *event_ids],
                ).fetchone()["n"]
            )
            trace_rows = conn.execute(
                "SELECT trace_id, data FROM traces WHERE session_id = ?",
                (session_id,),
            ).fetchall()
            trace_ids = [
                row["trace_id"]
                for row in trace_rows
                if any(event_id in str(row["data"]) for event_id in event_ids)
            ]
            state_history_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM state_history
                    WHERE session_id = ? AND timestamp < ?
                    """,
                    (session_id, cutoff_timestamp),
                ).fetchone()["n"]
            )
            blob_ref_rows = conn.execute(
                f"""
                SELECT blob_id
                FROM blob_references
                WHERE session_id = ? AND event_id IN ({placeholders})
                """,
                [session_id, *event_ids],
            ).fetchall()
            blob_ref_counts: dict[str, int] = {}
            for row in blob_ref_rows:
                blob_id = str(row["blob_id"])
                blob_ref_counts[blob_id] = blob_ref_counts.get(blob_id, 0) + 1
            derived_records = embedding_count + graph_edge_count + len(trace_ids) + state_history_count
            if dry_run:
                return {
                    "candidate_counts": {
                        "events": len(event_ids),
                        "derived_records": derived_records,
                        "blobs": len(blob_ref_counts),
                    },
                    "deleted_counts": {
                        "events": 0,
                        "derived_records": 0,
                        "traces": 0,
                        "state_history": 0,
                        "graph_edges": 0,
                        "blobs": 0,
                    },
                }
            deleted_counts = {
                "events": 0,
                "derived_records": 0,
                "traces": 0,
                "state_history": 0,
                "graph_edges": 0,
                "blobs": 0,
            }
            cursor = conn.execute(
                f"DELETE FROM embedding_index WHERE event_id IN ({placeholders})",
                event_ids,
            )
            deleted_counts["derived_records"] += int(cursor.rowcount)
            cursor = conn.execute(
                f"""
                DELETE FROM event_graph_edges
                WHERE session_id = ?
                  AND (source_event_id IN ({placeholders}) OR target_event_id IN ({placeholders}))
                """,
                [session_id, *event_ids, *event_ids],
            )
            deleted_counts["graph_edges"] = int(cursor.rowcount)
            deleted_counts["derived_records"] += deleted_counts["graph_edges"]
            if trace_ids:
                trace_placeholders = ", ".join("?" for _ in trace_ids)
                cursor = conn.execute(
                    f"DELETE FROM traces WHERE trace_id IN ({trace_placeholders})",
                    trace_ids,
                )
                deleted_counts["traces"] = int(cursor.rowcount)
                deleted_counts["derived_records"] += deleted_counts["traces"]
            cursor = conn.execute(
                """
                DELETE FROM state_history
                WHERE session_id = ? AND timestamp < ?
                """,
                (session_id, cutoff_timestamp),
            )
            deleted_counts["state_history"] = int(cursor.rowcount)
            deleted_counts["derived_records"] += deleted_counts["state_history"]
            cursor = conn.execute(
                f"""
                DELETE FROM blob_references
                WHERE session_id = ? AND event_id IN ({placeholders})
                """,
                [session_id, *event_ids],
            )
            for blob_id, ref_count in blob_ref_counts.items():
                conn.execute(
                    "UPDATE blobs SET ref_count = MAX(ref_count - ?, 0) WHERE blob_id = ?",
                    (ref_count, blob_id),
                )
            cursor = conn.execute(
                f"DELETE FROM events WHERE session_id = ? AND event_id IN ({placeholders})",
                [session_id, *event_ids],
            )
            deleted_counts["events"] = int(cursor.rowcount)
            return {
                "candidate_counts": {
                    "events": len(event_ids),
                    "derived_records": derived_records,
                    "blobs": len(blob_ref_counts),
                },
                "deleted_counts": deleted_counts,
            }

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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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
            edge_type = graph_edge_type(parent, event)
            edges.append((parent_id, event["event_id"], event["session_id"], edge_type, graph_edge_weight(edge_type), now_ms()))
        with self.write_connect() as conn:
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

    def put_memory_read_evidence_edges(
        self,
        *,
        session_id: str,
        memory_read_event_id: str,
        evidence_event_ids: Sequence[str],
    ) -> None:
        edges = [
            (memory_read_event_id, event_id, session_id, "MEMORY_READ_EVIDENCE", 0.8, now_ms())
            for event_id in evidence_event_ids
            if event_id and self.get_event(session_id, event_id)
        ]
        if not edges:
            return
        with self.write_connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO event_graph_edges(
                  source_event_id, target_event_id, session_id, edge_type, weight, created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                edges,
            )

    def put_segment_member_edge(self, session_id: str, segment: dict[str, Any] | None, event_id: str) -> None:
        if not segment:
            return
        anchor_event_ids = [
            item
            for item in segment.get("anchor_event_ids", [])
            if isinstance(item, str) and item
        ]
        if not anchor_event_ids:
            return
        root_event_id = anchor_event_ids[0]
        if root_event_id == event_id:
            return
        with self.write_connect() as conn:
            rows = conn.execute(
                """
                SELECT event_id
                FROM events
                WHERE session_id = ? AND event_id IN (?, ?)
                """,
                (session_id, root_event_id, event_id),
            ).fetchall()
            visible_event_ids = {str(row["event_id"]) for row in rows}
            if {root_event_id, event_id}.issubset(visible_event_ids):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO event_graph_edges(
                      source_event_id, target_event_id, session_id, edge_type, weight, created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (root_event_id, event_id, session_id, "SEGMENT_MEMBER", graph_edge_weight("SEGMENT_MEMBER"), now_ms()),
                )

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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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
        with self.write_connect() as conn:
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

    def operations_metrics_snapshot(self, embedding_model_id: str | None = None) -> dict[str, Any]:
        with self.connect() as conn:
            provider_rows = {
                "embedding": conn.execute(
                    """
                    SELECT COALESCE(SUM(embedding_batches), 0) AS calls,
                           COALESCE(SUM(embedding_failures), 0) AS failures
                    FROM embedding_metrics
                    """
                ).fetchone(),
                "reranker": conn.execute(
                    """
                    SELECT COALESCE(SUM(reranker_calls), 0) AS calls,
                           COALESCE(SUM(reranker_failures), 0) AS failures
                    FROM reranker_metrics
                    """
                ).fetchone(),
                "enrichment": conn.execute(
                    """
                    SELECT COALESCE(SUM(enrichment_calls), 0) AS calls,
                           COALESCE(SUM(enrichment_failures), 0) AS failures
                    FROM enrichment_metrics
                    """
                ).fetchone(),
            }
            blob_row = conn.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(size_bytes), 0) AS bytes FROM blobs"
            ).fetchone()
            event_rows = conn.execute("SELECT event_json FROM events").fetchall()
            audit_rows = conn.execute("SELECT action FROM audit_records").fetchall()
            trace_rows = conn.execute("SELECT data FROM traces").fetchall()
            state_rows = conn.execute("SELECT summary_json FROM state_history").fetchall()
            embedded_event_ids = set()
            if embedding_model_id:
                embedded_event_ids = {
                    row["event_id"]
                    for row in conn.execute(
                        "SELECT event_id FROM embedding_index WHERE embedding_model_id = ?",
                        (embedding_model_id,),
                    ).fetchall()
                }

        provider_metrics = {
            name: {
                "calls": int(row["calls"]) if row else 0,
                "failures": int(row["failures"]) if row else 0,
                "latency_ms": 0,
            }
            for name, row in provider_rows.items()
        }
        embedding_statuses = {"INDEXED": 0, "PENDING": 0, "FAILED": 0}
        compression_by_type: dict[str, int] = {}
        for row in event_rows:
            try:
                event = json.loads(row["event_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
            ingestion = event.get("ingestion") if isinstance(event.get("ingestion"), dict) else {}
            event_id = str(event.get("event_id") or "")
            status = str(ingestion.get("embedding_status") or metadata.get("embedding_status") or "").upper()
            if embedding_model_id and event_id in embedded_event_ids:
                embedding_statuses["INDEXED"] += 1
            elif status in embedding_statuses:
                embedding_statuses[status] += 1
            elif embedding_model_id and event.get("event_id") not in embedded_event_ids:
                embedding_statuses["PENDING"] += 1
            if metadata.get("compression_applied") is True:
                event_type = str(event.get("type") or "UNKNOWN")
                compression_by_type[event_type] = compression_by_type.get(event_type, 0) + 1

        retention_sweeps = 0
        for row in audit_rows:
            if row["action"] in {"RETENTION_CLEANUP", "MAINTENANCE_SYSTEM_SWEEP"}:
                retention_sweeps += 1

        segment_rollovers: dict[str, int] = {}
        routing_modes: dict[str, int] = {}
        for row in trace_rows:
            try:
                trace = json.loads(row["data"])
            except (TypeError, json.JSONDecodeError):
                continue
            if trace.get("type") == "SEGMENT_DRIFT":
                reason = str(trace.get("decision") or trace.get("reason") or "UNKNOWN")
                segment_rollovers[reason] = segment_rollovers.get(reason, 0) + 1
            retrieval = trace.get("retrieval") if isinstance(trace.get("retrieval"), dict) else {}
            mode = retrieval.get("mode") or trace.get("router_mode")
            if mode:
                label = str(mode)
                routing_modes[label] = routing_modes.get(label, 0) + 1

        intent_labels: dict[str, int] = {}
        for row in state_rows:
            try:
                summary = json.loads(row["summary_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                continue
            label = summary.get("intent_label")
            if label:
                key = str(label)
                intent_labels[key] = intent_labels.get(key, 0) + 1

        return {
            "provider_metrics": provider_metrics,
            "embedding_statuses": embedding_statuses,
            "blob_storage": {
                "count": int(blob_row["count"]) if blob_row else 0,
                "bytes": int(blob_row["bytes"]) if blob_row else 0,
            },
            "retention_sweeps": retention_sweeps,
            "intent_labels": intent_labels,
            "segment_rollovers": segment_rollovers,
            "routing_modes": routing_modes,
            "compression_by_type": compression_by_type,
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
        with self.write_connect() as conn:
            previous_state_row = conn.execute(
                "SELECT state_json FROM execution_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            previous_state = json.loads(previous_state_row["state_json"]) if previous_state_row else default_execution_state(session_id)
            previous_hash = self.execution_state_hash(previous_state)
            state_hash = self.execution_state_hash(state)
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
                      decisions_added_json, mode, changed_fields_json,
                      state_hash, previous_state_hash, provenance_json,
                      summary_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        entry["timestamp"],
                        entry["goal"],
                        entry["current_step"],
                        entry["intent_label"],
                        canonical_json(entry["decisions"]) if entry["decisions"] else None,
                        "AUTO",
                        canonical_json(self.changed_state_fields(previous_state, state)),
                        state_hash,
                        previous_hash,
                        canonical_json({}),
                        canonical_json(
                            {
                                "goal": state.get("goal") or None,
                                "current_step": state.get("current_step") or None,
                            }
                        ),
                    ),
                )

    def execution_state_hash(self, state: dict[str, Any]) -> str:
        return f"sha256:{hashlib.sha256(canonical_json(state).encode('utf-8')).hexdigest()}"

    def changed_state_fields(self, previous: dict[str, Any], state: dict[str, Any]) -> list[str]:
        keys = sorted(set(previous) | set(state))
        return [key for key in keys if previous.get(key) != state.get(key)]

    def update_execution_state(
        self,
        session_id: str,
        *,
        mode: str,
        state_patch: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self.write_connect() as conn:
            previous_row = conn.execute(
                "SELECT state_json FROM execution_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            previous = json.loads(previous_row["state_json"]) if previous_row else default_execution_state(session_id)
            if mode == "REPLACE":
                state = default_execution_state(session_id)
                state.update(state_patch)
            else:
                state = dict(previous)
                state.update(state_patch)
            state["schema_version"] = "mneme.execution_state.v0"
            state["session_id"] = session_id
            previous_hash = self.execution_state_hash(previous)
            state_hash = self.execution_state_hash(state)
            changed_fields = self.changed_state_fields(previous, state)
            conn.execute(
                "INSERT OR REPLACE INTO execution_state(session_id, state_json, updated_at) VALUES (?, ?, ?)",
                (session_id, canonical_json(state), now),
            )
            entry = {
                "schema_version": "mneme.state_history_entry.v0",
                "session_id": session_id,
                "sequence": int(
                    conn.execute(
                        "SELECT COUNT(*) AS n FROM state_history WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()["n"]
                ) + 1,
                "timestamp": now,
                "mode": mode,
                "changed_fields": changed_fields,
                "state_hash": state_hash,
                "previous_state_hash": previous_hash,
                "provenance": provenance,
                "summary": {
                    "goal": state.get("goal") or None,
                    "current_step": state.get("current_step") or None,
                },
                "goal": state.get("goal") or None,
                "current_step": state.get("current_step") or None,
                "intent_label": (state.get("enrichment") or {}).get("intent_label")
                if isinstance(state.get("enrichment"), dict)
                else None,
            }
            conn.execute(
                """
                INSERT INTO state_history(
                  session_id, timestamp, goal, current_step, intent_label,
                  decisions_added_json, mode, changed_fields_json, state_hash,
                  previous_state_hash, provenance_json, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    entry["timestamp"],
                    entry["goal"],
                    entry["current_step"],
                    entry["intent_label"],
                    None,
                    mode,
                    canonical_json(changed_fields),
                    state_hash,
                    previous_hash,
                    canonical_json(provenance),
                    canonical_json(entry["summary"]),
                ),
            )
        return {"state": state, "history_entry": entry}

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
                SELECT id, timestamp, goal, current_step, intent_label,
                       decisions_added_json, mode, changed_fields_json,
                       state_hash, previous_state_hash, provenance_json,
                       summary_json
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
                    "history_id": f"state-history-{row['id']}",
                    "session_id": session_id,
                    "sequence": int(row["id"]),
                    "timestamp": row["timestamp"],
                    "mode": row["mode"] or "AUTO",
                    "changed_fields": json.loads(row["changed_fields_json"] or "[]"),
                    "state_hash": row["state_hash"],
                    "previous_state_hash": row["previous_state_hash"],
                    "provenance": json.loads(row["provenance_json"] or "{}"),
                    "summary": json.loads(row["summary_json"] or "{}"),
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

    def put_turn(
        self,
        session_id: str,
        turn_id: str,
        data: dict[str, Any],
        *,
        segment_ids: list[str] | None = None,
    ) -> None:
        with self.write_connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO turns(session_id, turn_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                (session_id, turn_id, canonical_json(data), now_ms()),
            )
            linked_segment_ids = list(dict.fromkeys(segment_ids or [f"segment-{session_id}"]))
            for segment_id in linked_segment_ids:
                row = conn.execute(
                    "SELECT data, created_at_ms FROM segments WHERE segment_id = ?",
                    (segment_id,),
                ).fetchone()
                if row:
                    segment = json.loads(row["data"])
                    created_at_ms = int(row["created_at_ms"])
                else:
                    segment = {
                        "schema_version": "mneme.segment.v0",
                        "segment_id": segment_id,
                        "session_id": session_id,
                        "title": f"Session {session_id}",
                        "summary": "Recorded session activity.",
                        "status": "ACTIVE",
                    }
                    created_at_ms = now_ms()
                outcome = data.get("outcome") if isinstance(data.get("outcome"), dict) else {}
                if outcome.get("summary"):
                    segment["summary"] = str(outcome["summary"])[:1000]
                metadata = segment.get("metadata") if isinstance(segment.get("metadata"), dict) else {}
                metadata["last_turn_id"] = turn_id
                metadata["last_turn_status"] = str(data.get("status") or "COMPLETED").upper()
                if data.get("completed_at"):
                    metadata["last_turn_completed_at"] = data.get("completed_at")
                if isinstance(data.get("usage"), dict):
                    metadata["last_turn_usage"] = data["usage"]
                segment["metadata"] = metadata
                conn.execute(
                    "INSERT OR REPLACE INTO segments(segment_id, session_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                    (segment_id, session_id, canonical_json(segment), created_at_ms),
                )

    def get_turn(self, session_id: str, turn_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data FROM turns WHERE session_id = ? AND turn_id = ?",
                (session_id, turn_id),
            ).fetchone()
        return json.loads(row["data"]) if row else None

    def put_trace(self, trace: dict[str, Any]) -> None:
        with self.write_connect() as conn:
            conn.execute(
                "INSERT INTO traces(trace_id, session_id, turn_id, data, created_at_ms) VALUES (?, ?, ?, ?, ?)",
                (trace["trace_id"], trace["session_id"], trace.get("turn_id"), canonical_json(trace), now_ms()),
            )

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT data FROM traces WHERE trace_id = ?", (trace_id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def add_audit(
        self,
        session_id: str,
        action: str,
        tool: str,
        event_ids: list[str],
        trace_id: str | None = None,
        *,
        project_isolation_key: str | None = None,
        principal: dict[str, Any] | None = None,
        request: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "schema_version": "mneme.audit_record.v0",
            "audit_id": new_id("audit"),
            "session_id": session_id,
            "project_isolation_key": project_isolation_key,
            "action": action,
            "tool": tool,
            "event_ids": event_ids,
            "trace_id": trace_id,
            "principal": principal or {},
            "request": request or {},
            "result": result or {},
            "created_at_ms": now_ms(),
        }
        with self.write_connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_records(
                  audit_id, session_id, project_isolation_key, action, tool,
                  event_ids, trace_id, principal_json, request_json, result_json,
                  created_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["audit_id"],
                    session_id,
                    project_isolation_key,
                    action,
                    tool,
                    canonical_json(event_ids),
                    trace_id,
                    canonical_json(record["principal"]),
                    canonical_json(record["request"]),
                    canonical_json(record["result"]),
                    record["created_at_ms"],
                ),
            )
        return record

    def list_audit(self, session_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT audit_id, session_id, project_isolation_key, action, tool,
                       event_ids, trace_id, principal_json, request_json,
                       result_json, created_at_ms
                FROM audit_records
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchall()
        return [
            {
                "schema_version": "mneme.audit_record.v0",
                "audit_id": row["audit_id"],
                "session_id": row["session_id"],
                "project_isolation_key": row["project_isolation_key"],
                "action": row["action"],
                "tool": row["tool"],
                "event_ids": json.loads(row["event_ids"]),
                "trace_id": row["trace_id"],
                "principal": json.loads(row["principal_json"]),
                "request": json.loads(row["request_json"]),
                "result": json.loads(row["result_json"]),
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

    def get_segment(self, segment_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT data FROM segments WHERE segment_id = ?",
                (segment_id,),
            ).fetchone()
        if not row:
            return None
        segment = json.loads(row["data"])
        return self._rich_segments(segment["session_id"], [segment])[0]

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

    def segment_events(self, session_id: str, segment_id: str, *, limit: int) -> list[dict[str, Any]]:
        segments = self.list_segments(session_id)
        raw_segments = [strip_rich_segment_fields(segment) for segment in segments]
        segment_index = next((index for index, segment in enumerate(raw_segments) if segment.get("segment_id") == segment_id), None)
        if segment_index is None:
            return []
        return self.events_for_segment_data(self.list_events(session_id), raw_segments, segment_index)[:limit]

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
        anchor_event_ids = [
            item
            for item in segment.get("anchor_event_ids", [])
            if isinstance(item, str) and item
        ]
        with self.write_connect() as conn:
            existing = conn.execute(
                "SELECT created_at_ms FROM segments WHERE segment_id = ?",
                (segment_id,),
            ).fetchone()
            created_at_ms = int(existing["created_at_ms"]) if existing else now_ms()
            conn.execute(
                "INSERT OR REPLACE INTO segments(segment_id, session_id, data, created_at_ms) VALUES (?, ?, ?, ?)",
                (segment_id, session_id, canonical_json(segment), created_at_ms),
            )
            if len(anchor_event_ids) > 1:
                root_event_id = anchor_event_ids[0]
                rows = conn.execute(
                    f"""
                    SELECT event_id
                    FROM events
                    WHERE session_id = ? AND event_id IN ({", ".join("?" for _ in anchor_event_ids)})
                    """,
                    [session_id, *anchor_event_ids],
                ).fetchall()
                visible_event_ids = {str(row["event_id"]) for row in rows}
                if root_event_id in visible_event_ids:
                    edges = [
                        (root_event_id, event_id, session_id, "SEGMENT_ANCHOR", 0.7, now_ms())
                        for event_id in anchor_event_ids[1:]
                        if event_id != root_event_id and event_id in visible_event_ids
                    ]
                    conn.executemany(
                        """
                        INSERT OR IGNORE INTO event_graph_edges(
                          source_event_id, target_event_id, session_id, edge_type, weight, created_at_ms
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        edges,
                    )

    def export_session(self, session_id: str, *, include_audit: bool = False) -> dict[str, Any]:
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
            "schema_version": "mneme.session_export.v0",
            "format": "json",
            "session": session,
            "events": self.list_events(session_id, include_memory_reads=True),
            "turns": turns,
            "traces": traces,
            "audit_records": self.list_audit(session_id) if include_audit else [],
            "segments": self.list_segments(session_id),
            "blobs_metadata": [
                {
                    "blob_id": blob["blob_id"],
                    "uri": blob["uri"],
                    "size_bytes": blob["size_bytes"],
                    "hash": blob["hash"],
                    "media_type": blob["media_type"],
                    "omitted_reason": "FORMAT_JSON_METADATA_ONLY",
                }
                for blob in self.list_blob_metadata_for_session(session_id)
            ],
            "blob_contents": [],
            "session_lineage": self.session_lineage_edges(session_id),
            "event_graph_edges": self.list_event_graph_edges(session_id),
            "embeddings": embeddings,
            "execution_state": json.loads(state_row["state_json"]) if state_row else None,
            "state_history": self.get_state_history(session_id, limit=1000),
            "exported_at": utc_now_iso(),
            "redaction_applied": True,
        }

    def forensic_anchor_from_audit_row(self, row: sqlite3.Row) -> dict[str, Any]:
        salt = secrets.token_hex(16)
        event_ids = json.loads(row["event_ids"]) if row["event_ids"] else []
        principal = json.loads(row["principal_json"]) if row["principal_json"] else {}
        principal_scopes = set(principal.get("project_scopes") or [])
        principal_class = {
            "role": principal.get("role"),
            "all_projects": "*" in principal_scopes,
        }
        session_hash = salted_hash(row["session_id"], salt)
        project_hash = salted_hash(row["project_isolation_key"], salt)
        trace_hash = salted_hash(row["trace_id"], salt)
        event_hashes = [hashed for hashed in (salted_hash(str(event_id), salt) for event_id in event_ids) if hashed]
        return {
            "schema_version": "mneme.audit_record.v0",
            "audit_id": row["audit_id"],
            "session_id": f"deleted-session:{session_hash}",
            "project_isolation_key": f"deleted-project:{project_hash}" if project_hash else None,
            "action": row["action"],
            "tool": row["tool"],
            "event_ids": [],
            "trace_id": None,
            "principal": principal_class,
            "request": {},
            "result": {
                "forensic_anchor": True,
                "session_hash": session_hash,
                "project_hash": project_hash,
                "event_id_hashes": event_hashes,
                "trace_id_hash": trace_hash,
                "event_count": len(event_ids),
                "redaction_applied": True,
            },
            "created_at_ms": row["created_at_ms"],
        }

    def list_forensic_anchors(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT audit_id, session_id, project_isolation_key, action, tool,
                       event_ids, trace_id, principal_json, request_json,
                       result_json, created_at_ms
                FROM audit_records
                WHERE result_json LIKE '%"forensic_anchor":true%'
                   OR result_json LIKE '%"forensic_anchor": true%'
                ORDER BY created_at_ms ASC
                """
            ).fetchall()
        return [
            {
                "schema_version": "mneme.audit_record.v0",
                "audit_id": row["audit_id"],
                "session_id": row["session_id"],
                "project_isolation_key": row["project_isolation_key"],
                "action": row["action"],
                "tool": row["tool"],
                "event_ids": json.loads(row["event_ids"]),
                "trace_id": row["trace_id"],
                "principal": json.loads(row["principal_json"]),
                "request": json.loads(row["request_json"]),
                "result": json.loads(row["result_json"]),
                "created_at_ms": row["created_at_ms"],
            }
            for row in rows
        ]

    def purge_forensic_anchors_older_than(self, *, retention_days: int) -> dict[str, int]:
        if retention_days < 0:
            retention_days = 0
        cutoff_ms = now_ms() - (retention_days * 86400 * 1000)
        predicate = """
            (result_json LIKE '%"forensic_anchor":true%'
             OR result_json LIKE '%"forensic_anchor": true%')
            AND created_at_ms < ?
        """
        with self.write_connect() as conn:
            candidate_count = conn.execute(
                f"SELECT COUNT(*) AS n FROM audit_records WHERE {predicate}",
                (cutoff_ms,),
            ).fetchone()["n"]
            cursor = conn.execute(
                f"DELETE FROM audit_records WHERE {predicate}",
                (cutoff_ms,),
            )
        return {"candidate_count": int(candidate_count), "deleted_count": int(cursor.rowcount)}

    def delete_session(self, session_id: str) -> bool:
        existed = self.has_session(session_id)
        with self.write_connect() as conn:
            audit_rows = conn.execute(
                """
                SELECT audit_id, session_id, project_isolation_key, action, tool,
                       event_ids, trace_id, principal_json, request_json,
                       result_json, created_at_ms
                FROM audit_records
                WHERE session_id = ?
                ORDER BY created_at_ms ASC
                """,
                (session_id,),
            ).fetchall()
            anchors = [
                self.forensic_anchor_from_audit_row(row)
                for row in audit_rows
                if row["action"] in FORENSIC_AUDIT_ACTIONS
            ]
            conn.execute("DELETE FROM blob_references WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM blobs WHERE session_id = ?", (session_id,))
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
            for anchor in anchors:
                conn.execute(
                    """
                    INSERT INTO audit_records(
                      audit_id, session_id, project_isolation_key, action, tool,
                      event_ids, trace_id, principal_json, request_json,
                      result_json, created_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        anchor["audit_id"],
                        anchor["session_id"],
                        anchor["project_isolation_key"],
                        anchor["action"],
                        anchor["tool"],
                        canonical_json(anchor["event_ids"]),
                        anchor["trace_id"],
                        canonical_json(anchor["principal"]),
                        canonical_json(anchor["request"]),
                        canonical_json(anchor["result"]),
                        anchor["created_at_ms"],
                    ),
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
            turn_rows = conn.execute(
                "SELECT data FROM turns WHERE session_id = ?",
                (session_id,),
            ).fetchall()
            session_row = conn.execute(
                "SELECT data FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
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
        turns = [json.loads(row["data"]) for row in turn_rows]
        usage_rows = [
            turn.get("usage")
            for turn in turns
            if isinstance(turn.get("usage"), dict)
        ]
        prompt_tokens = sum(int(usage.get("prompt_tokens") or 0) for usage in usage_rows)
        completion_tokens = sum(int(usage.get("completion_tokens") or 0) for usage in usage_rows)
        tool_calls = sum(int(usage.get("tool_call_count") or usage.get("tool_calls") or 0) for usage in usage_rows)
        provider_breakdown: dict[tuple[str, str], dict[str, Any]] = {}
        for usage in usage_rows:
            provider = usage.get("provider") or usage.get("provider_name")
            if not provider:
                continue
            model = usage.get("model") or usage.get("model_id") or ""
            key = (str(provider), str(model))
            row = provider_breakdown.setdefault(
                key,
                {
                    "provider": str(provider),
                    "model": str(model),
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "tool_calls": 0,
                    "estimated_cost_usd": 0.0,
                },
            )
            row["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
            row["completion_tokens"] += int(usage.get("completion_tokens") or 0)
            row["tool_calls"] += int(usage.get("tool_call_count") or usage.get("tool_calls") or 0)
            if usage.get("cost_usd") is not None:
                row["estimated_cost_usd"] += float(usage.get("cost_usd") or 0)
            elif usage.get("estimated_cost_usd") is not None:
                row["estimated_cost_usd"] += float(usage.get("estimated_cost_usd") or 0)
        started_values = [str(turn.get("started_at")) for turn in turns if turn.get("started_at")]
        completed_values = [str(turn.get("completed_at")) for turn in turns if turn.get("completed_at")]
        session_data = json.loads(session_row["data"]) if session_row else {}
        period_from = min(started_values) if started_values else session_data.get("started_at")
        period_to = max(completed_values) if completed_values else session_data.get("ended_at") or period_from
        return {
            "schema_version": "mneme.cost_report.v0",
            "cost_model_version": "mneme.cost_model.v0",
            "session_id": session_id,
            "mode": "STANDARD",
            "period": {
                "from": period_from,
                "to": period_to,
            },
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "embedding_tokens": embedding_metrics["embedding_input_chars"],
                "reranker_calls": reranker_metrics["reranker_calls"],
                "llm_enrichment_tokens": 0,
                "tool_calls": tool_calls,
            },
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
            "baseline": {
                "provider_prompt_tokens_without_mneme_estimate": 0,
                "methodology": "UNKNOWN",
                "estimate_kind": "COUNTERFACTUAL",
                "savings_claim": False,
            },
            "provider_breakdown": list(provider_breakdown.values()),
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
    if parent_type in {"USER_MESSAGE", "ASSISTANT_MESSAGE", "SYSTEM_MESSAGE"} and child_type == "TOOL_CALL":
        return "TOOL_INPUT"
    if child_type == "DECISION":
        return "DECISION_FOLLOWS"
    return "PARENT_CHILD"


def graph_edge_weight(edge_type: str) -> float:
    return {
        "TOOL_RESULT": 1.0,
        "TOOL_INPUT": 1.0,
        "PARENT_CHILD": 0.9,
        "DECISION_FOLLOWS": 0.8,
        "MEMORY_READ_EVIDENCE": 0.8,
        "SEGMENT_ANCHOR": 0.7,
        "SEGMENT_MEMBER": 0.5,
        "FOLLOWS": 0.2,
    }.get(edge_type, 0.5)


def graph_edge_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "schema_version": "mneme.graph_edge.v0",
        "source_event_id": row["source_event_id"],
        "target_event_id": row["target_event_id"],
        "session_id": row["session_id"],
        "edge_type": row["edge_type"],
        "weight": row["weight"],
    }
