from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from mneme_service.storage import CURRENT_SCHEMA_VERSION, Store


def read_pragma(path: Path, name: str) -> int | str:
    with sqlite3.connect(path) as conn:
        return conn.execute(f"PRAGMA {name}").fetchone()[0]


def test_store_initializes_schema_version_migration_history_and_busy_timeout(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"

    store = Store(db_path)

    assert read_pragma(db_path, "user_version") == CURRENT_SCHEMA_VERSION
    with store.connect() as conn:
        migrations = conn.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert [(row["version"], row["name"]) for row in migrations] == [
        (CURRENT_SCHEMA_VERSION, "initial_v0_schema")
    ]
    assert busy_timeout > 0
    assert journal_mode == "wal"


def test_store_enforces_owner_only_database_file_permissions(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_dir.chmod(0o777)
    db_path = data_dir / "mneme.db"
    db_path.touch()
    db_path.chmod(0o666)

    Store(db_path)

    assert data_dir.stat().st_mode & 0o077 == 0
    assert db_path.stat().st_mode & 0o077 == 0


def test_store_initializes_owned_blob_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"

    Store(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {"blobs", "blob_references"}.issubset(tables)


def test_store_blob_reference_attach_detach_updates_ref_count_once(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    blob = store.put_blob(
        session_id="session-blob",
        project_isolation_key="project-blob",
        content=b"blob bytes",
        media_type="application/octet-stream",
    )

    assert store.get_blob_metadata(blob["blob_id"])["ref_count"] == 0
    assert store.attach_blob_reference(
        blob_id=blob["blob_id"],
        session_id="session-blob",
        event_id="event-blob",
    ) is True
    assert store.attach_blob_reference(
        blob_id=blob["blob_id"],
        session_id="session-blob",
        event_id="event-blob",
    ) is False
    assert store.get_blob_metadata(blob["blob_id"])["ref_count"] == 1

    assert store.detach_blob_reference(
        blob_id=blob["blob_id"],
        session_id="session-blob",
        event_id="event-blob",
    ) is True
    assert store.detach_blob_reference(
        blob_id=blob["blob_id"],
        session_id="session-blob",
        event_id="event-blob",
    ) is False
    assert store.get_blob_metadata(blob["blob_id"])["ref_count"] == 0


def test_backup_restore_roundtrip_preserves_sqlite_and_blob_hashes(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    backup_path = tmp_path / "mneme.backup.db"
    restored_path = tmp_path / "mneme.restored.db"
    store = Store(db_path)
    blob = store.put_blob(
        session_id="session-backup",
        project_isolation_key="project-backup",
        content=b"backup blob bytes",
        media_type="application/octet-stream",
    )

    backup = store.backup_to(backup_path)

    assert backup["schema_version"] == CURRENT_SCHEMA_VERSION
    assert backup["blob_count"] == 1
    assert backup_path.exists()

    restore = Store.restore_from_backup(backup_path, restored_path)
    restored = Store(restored_path)

    assert restore["schema_version"] == CURRENT_SCHEMA_VERSION
    assert restore["blob_count"] == 1
    assert restored.get_blob_content(blob["blob_id"]) == b"backup blob bytes"


def test_restore_from_backup_rejects_corrupt_blob_hash(tmp_path: Path) -> None:
    backup_path = tmp_path / "mneme.backup.db"
    target_path = tmp_path / "mneme.restored.db"
    store = Store(tmp_path / "mneme.db")
    blob = store.put_blob(
        session_id="session-backup-corrupt",
        project_isolation_key="project-backup",
        content=b"original",
        media_type="application/octet-stream",
    )
    store.backup_to(backup_path)
    with sqlite3.connect(backup_path) as conn:
        conn.execute("UPDATE blobs SET content = ? WHERE blob_id = ?", (b"corrupted", blob["blob_id"]))

    with pytest.raises(RuntimeError, match="BLOB_HASH_MISMATCH"):
        Store.restore_from_backup(backup_path, target_path)

    assert not target_path.exists()


def test_store_counts_blobs_for_session(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    store.put_blob(
        session_id="session-a",
        project_isolation_key="project-a",
        content=b"a",
        media_type="application/octet-stream",
    )
    store.put_blob(
        session_id="session-a",
        project_isolation_key="project-a",
        content=b"b",
        media_type="application/octet-stream",
    )
    store.put_blob(
        session_id="session-b",
        project_isolation_key="project-b",
        content=b"c",
        media_type="application/octet-stream",
    )

    assert store.count_blobs_for_session("session-a") == 2
    assert store.count_blobs_for_session("session-b") == 1
    assert store.count_blobs_for_session("session-missing") == 0


def test_store_put_blob_records_and_events_is_atomic(tmp_path: Path) -> None:
    store = Store(tmp_path / "mneme.db")
    event_record = {
        "event": {
            "event_id": "event-txn",
            "session_id": "session-txn",
            "turn_id": "turn-1",
            "agent_id": "agent-1",
            "runtime": "HERMES",
            "role": "TOOL",
            "type": "TOOL_OUTPUT",
            "timestamp": "2026-06-09T12:00:01Z",
            "content": {
                "format": "BYTES_REF",
                "uri": "mneme-blob://blob-txn",
                "hash": "sha256:txn",
                "size_bytes": 3,
                "media_type": "application/octet-stream",
                "storage_owner": "SERVER",
            },
            "parent_event_ids": [],
            "token_estimate": 1,
        },
        "immutable_hash": "hash-txn",
        "content_text": "application/octet-stream mneme-blob://blob-txn sha256:txn",
        "is_memory_read": False,
        "blob_ref_ids": ["blob-txn"],
    }
    blob_record = {
        "blob_id": "blob-txn",
        "uri": "mneme-blob://blob-txn",
        "owner": "SERVER",
        "session_id": "session-txn",
        "project_isolation_key": "project-txn",
        "hash": "sha256:txn",
        "size_bytes": 3,
        "media_type": "application/octet-stream",
        "created_at": "2026-06-09T12:00:00Z",
        "delete_with_session": True,
        "expires_at": None,
        "metadata": {},
        "content": b"txn",
    }

    store.put_blob_records_and_events(
        blob_records=[blob_record],
        event_records=[event_record],
    )

    assert store.get_event("session-txn", "event-txn") is not None
    assert store.get_blob_metadata("blob-txn")["ref_count"] == 1

    failed_blob = {**blob_record, "blob_id": "blob-failed", "uri": "mneme-blob://blob-failed"}
    with pytest.raises(sqlite3.IntegrityError):
        store.put_blob_records_and_events(
            blob_records=[failed_blob],
            event_records=[event_record],
        )

    assert store.get_blob_metadata("blob-failed") is None
    assert store.count_blobs_for_session("session-txn") == 1


def test_store_reopening_current_database_keeps_migration_history_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    Store(db_path)
    Store(db_path)

    with sqlite3.connect(db_path) as conn:
        migrations = conn.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()

    assert migrations == [(CURRENT_SCHEMA_VERSION, "initial_v0_schema")]


def test_store_refuses_unknown_newer_schema_version(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA user_version = 999")

    with pytest.raises(RuntimeError, match="SCHEMA_VERSION_UNKNOWN_NEWER"):
        Store(db_path)


def test_store_refuses_user_version_and_migration_history_mismatch(tmp_path: Path) -> None:
    db_path = tmp_path / "mneme.db"
    Store(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA user_version = 0")

    with pytest.raises(RuntimeError, match="SCHEMA_VERSION_MISMATCH"):
        Store(db_path)


def test_store_startup_integrity_check_can_be_explicitly_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_integrity_check(store: Store, conn: sqlite3.Connection) -> None:
        if store.startup_integrity_check:
            raise RuntimeError("SQLITE_INTEGRITY_CHECK_FAILED")

    monkeypatch.setattr(Store, "_check_integrity", fake_integrity_check)

    Store(tmp_path / "disabled.db", startup_integrity_check=False)
    with pytest.raises(RuntimeError, match="SQLITE_INTEGRITY_CHECK_FAILED"):
        Store(tmp_path / "enabled.db")


def test_destructive_migration_requires_backup_or_explicit_bypass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "legacy.db"
    backup_path = tmp_path / "legacy.before-migrate.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA user_version = 0")
        conn.execute(
            """
            CREATE TABLE schema_migrations (
              version INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (0, 'legacy_v0', '2026-01-01T00:00:00Z')"
        )

    monkeypatch.setattr(
        "mneme_service.storage.DESTRUCTIVE_MIGRATIONS_BY_SOURCE_VERSION",
        {0: ("drop_legacy_payloads",)},
    )

    with pytest.raises(RuntimeError, match="BACKUP_REQUIRED_BEFORE_DESTRUCTIVE_MIGRATION"):
        Store(db_path)

    store = Store(db_path, backup_before_migrate=backup_path)

    assert backup_path.exists()
    assert store.migration_backup_result["backup_path"] == str(backup_path)
    assert store.migration_backup_result["destructive_migrations"] == ["drop_legacy_payloads"]
    assert Store.verify_backup(backup_path, expected_schema_version=0)["schema_version"] == 0


def test_destructive_migration_allows_explicit_no_backup_bypass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "legacy-no-backup.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA user_version = 0")
        conn.execute(
            """
            CREATE TABLE schema_migrations (
              version INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              applied_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (0, 'legacy_v0', '2026-01-01T00:00:00Z')"
        )

    monkeypatch.setattr(
        "mneme_service.storage.DESTRUCTIVE_MIGRATIONS_BY_SOURCE_VERSION",
        {0: ("drop_legacy_payloads",)},
    )

    store = Store(db_path, no_backup_before_migrate=True)

    assert store.migration_backup_result["backup_path"] is None
    assert store.migration_backup_result["operator_bypass"] is True
    assert store.migration_backup_result["destructive_migrations"] == ["drop_legacy_payloads"]
