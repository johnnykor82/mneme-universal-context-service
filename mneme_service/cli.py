from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Sequence

import uvicorn

from .app import create_app
from .config import Settings, load_settings
from .storage import Store
from .codex_hooks import (
    DEFAULT_CODEX_CONTEXT_BUDGET_TOKENS,
    DEFAULT_CODEX_CONTEXT_PREVIEW_OUTPUT,
    DEFAULT_CODEX_CONTEXT_WINDOW_TOKENS,
    capture_codex_hook_payload,
    current_codex_hook_timestamp,
    import_codex_hook_capture_file,
    import_codex_hook_payload,
    normalize_codex_hook_payload,
    prepare_codex_context_preview,
    render_codex_context_preview_hook_config,
    render_codex_hook_config,
    select_codex_hook_capture_item,
    validate_codex_hook_capture_file,
)
from .codex_ingest import import_codex_transcript
from .codex_setup import (
    DEFAULT_CODEX_BASE_URL,
    DEFAULT_CODEX_INSTALL_ROOT,
    DEFAULT_CODEX_SERVICE_LABEL,
    codex_service_install,
    codex_service_logs,
    codex_service_start,
    codex_service_status,
    codex_service_stop,
    codex_service_uninstall,
    codex_desktop_status,
    resolve_token,
    setup_codex_desktop_global,
)
from .mcp_server import create_mcp_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mneme")
    subcommands = parser.add_subparsers(dest="command", required=True)

    serve = subcommands.add_parser("serve")
    serve.add_argument("--config", type=Path, default=None)
    serve.add_argument("--db", type=Path, default=None)
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--token", dest="auth_token", default=None)
    serve.add_argument("--token-file", dest="auth_token_file", type=Path, default=None)
    serve.add_argument("--insecure-dev", action="store_true", default=None)
    serve.add_argument("--secure", dest="insecure_dev", action="store_false")
    serve.add_argument("--require-embeddings", dest="require_embeddings", action="store_true", default=None)
    serve.add_argument("--allow-missing-embeddings", dest="require_embeddings", action="store_false")
    serve.add_argument("--embeddings-enabled", dest="embedding_enabled", action="store_true", default=None)
    serve.add_argument("--embeddings-disabled", dest="embedding_enabled", action="store_false")
    serve.add_argument("--embedding-provider", default=None)
    serve.add_argument("--embedding-model", default=None)
    serve.add_argument("--embedding-base-url", default=None)
    serve.add_argument("--embedding-api-key", default=None)
    serve.add_argument("--reranker-enabled", dest="reranker_enabled", action="store_true", default=None)
    serve.add_argument("--reranker-disabled", dest="reranker_enabled", action="store_false")
    serve.add_argument("--reranker-provider", default=None)
    serve.add_argument("--reranker-model", default=None)
    serve.add_argument("--reranker-base-url", default=None)
    serve.add_argument("--reranker-api-key", default=None)
    serve.add_argument("--llm-enrichment-enabled", dest="llm_enabled", action="store_true", default=None)
    serve.add_argument("--llm-enrichment-disabled", dest="llm_enabled", action="store_false")
    serve.add_argument("--llm-provider", default=None)
    serve.add_argument("--llm-model", default=None)
    serve.add_argument("--llm-base-url", default=None)
    serve.add_argument("--llm-api-key", default=None)
    serve.add_argument("--router-min-candidates", type=int, default=None)
    serve.add_argument("--routing-default-mode", default=None)
    serve.add_argument("--routing-weight-debugging-dependency", type=float, default=None)
    serve.add_argument("--centroid-window", type=int, default=None)
    serve.add_argument("--enricher-max-tokens", type=int, default=None)
    serve.add_argument("--max-writer-queue-depth", type=int, default=None)
    serve.add_argument("--strict-cost-mode", dest="strict_cost_mode", action="store_true", default=None)
    serve.add_argument("--relaxed-cost-mode", dest="strict_cost_mode", action="store_false")
    serve.add_argument("--max-blob-bytes", type=int, default=None)
    serve.add_argument("--max-session-id-length", type=int, default=None)
    serve.add_argument("--max-batch-total-blob-bytes", type=int, default=None)
    serve.add_argument("--max-multipart-metadata-overhead-bytes", type=int, default=None)
    serve.add_argument("--max-multipart-transaction-bytes", type=int, default=None)
    serve.add_argument("--max-multipart-transaction-ms", type=int, default=None)
    serve.add_argument("--max-export-blob-inline-bytes", type=int, default=None)
    serve.add_argument("--max-export-session-memory-bytes", type=int, default=None)
    serve.add_argument("--idempotency-key-min-retention-seconds", type=int, default=None)
    serve.add_argument("--startup-integrity-check", dest="startup_integrity_check", action="store_true", default=None)
    serve.add_argument("--no-startup-integrity-check", dest="startup_integrity_check", action="store_false")
    serve.add_argument("--metrics-enabled", dest="metrics_enabled", action="store_true", default=None)
    serve.add_argument("--metrics-disabled", dest="metrics_enabled", action="store_false")
    serve.add_argument("--metrics-format", default=None)
    serve.add_argument("--retention-sweep-interval-seconds", type=int, default=None)
    serve.add_argument(
        "--retention-sweep-on-startup",
        dest="retention_sweep_on_startup",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-retention-sweep-on-startup",
        dest="retention_sweep_on_startup",
        action="store_false",
    )
    serve.add_argument(
        "--retention-sweep-on-session-close",
        dest="retention_sweep_on_session_close",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-retention-sweep-on-session-close",
        dest="retention_sweep_on_session_close",
        action="store_false",
    )
    serve.add_argument(
        "--retention-force-active-cleanup",
        dest="retention_force_active_cleanup",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-retention-force-active-cleanup",
        dest="retention_force_active_cleanup",
        action="store_false",
    )
    serve.add_argument("--vacuum-max-duration-ms", type=int, default=None)
    serve.add_argument("--checkpoint-max-pages", type=int, default=None)
    serve.add_argument("--reindex-max-job-events", type=int, default=None)
    serve.add_argument("--reindex-max-events-per-transaction", type=int, default=None)
    serve.add_argument("--reindex-yield-between-transactions-ms", type=int, default=None)
    serve.add_argument("--reindex-provider-wait-timeout-seconds", type=int, default=None)
    serve.add_argument("--reindex-provider-max-requests-per-minute", type=int, default=None)
    serve.add_argument("--reindex-provider-circuit-breaker-min-calls", type=int, default=None)
    serve.add_argument("--reindex-provider-circuit-breaker-failure-ratio", type=float, default=None)
    serve.add_argument("--reindex-provider-circuit-breaker-open-seconds", type=int, default=None)
    serve.add_argument("--reindex-provider-circuit-breaker-half-open-requests", type=int, default=None)
    serve.add_argument(
        "--reindex-provider-recovery-ramp-initial-requests-per-minute",
        type=int,
        default=None,
    )
    serve.add_argument("--max-redaction-time-ms", type=int, default=None)
    serve.add_argument("--max-tool-result-events", type=int, default=None)
    serve.add_argument(
        "--reindex-enqueue-when-provider-unavailable",
        dest="reindex_enqueue_when_provider_unavailable",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-reindex-enqueue-when-provider-unavailable",
        dest="reindex_enqueue_when_provider_unavailable",
        action="store_false",
    )
    serve.add_argument(
        "--reindex-foreground-write-priority",
        dest="reindex_foreground_write_priority",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-reindex-foreground-write-priority",
        dest="reindex_foreground_write_priority",
        action="store_false",
    )
    serve.add_argument("--audit-forensic-retention-days", type=int, default=None)
    serve.add_argument(
        "--audit-anonymize-deleted-session-audit",
        dest="audit_anonymize_deleted_session_audit",
        action="store_true",
        default=None,
    )
    serve.add_argument(
        "--no-audit-anonymize-deleted-session-audit",
        dest="audit_anonymize_deleted_session_audit",
        action="store_false",
    )
    serve.add_argument("--backup-before-migrate", type=Path, default=None)
    serve.add_argument("--no-backup-before-migrate", action="store_true", default=None)
    serve.add_argument("--memory-access-hint-enabled", dest="memory_access_hint_enabled", action="store_true", default=None)
    serve.add_argument("--memory-access-hint-disabled", dest="memory_access_hint_enabled", action="store_false")

    mcp = subcommands.add_parser("mcp")
    mcp.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    mcp.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    mcp.add_argument("--timeout", type=float, default=10.0)
    mcp.add_argument("--default-session-id", default=os.environ.get("MNEME_MCP_DEFAULT_SESSION_ID"))

    codex_ingest = subcommands.add_parser("codex-ingest")
    codex_ingest.add_argument("--input", type=Path, required=True)
    codex_ingest.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_ingest.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_ingest.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_ingest.add_argument("--timeout", type=float, default=10.0)

    codex_hook_ingest = subcommands.add_parser("codex-hook-ingest")
    codex_hook_ingest.add_argument("--input", type=Path, required=True)
    codex_hook_ingest.add_argument("--event", default=None)
    codex_hook_ingest.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_hook_ingest.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_hook_ingest.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_hook_ingest.add_argument("--timeout", type=float, default=10.0)
    codex_hook_ingest.add_argument("--dry-run", action="store_true")

    codex_hook_capture = subcommands.add_parser("codex-hook-capture")
    codex_hook_capture.add_argument("--input", type=Path, required=True)
    codex_hook_capture.add_argument("--event", default=None)
    codex_hook_capture.add_argument("--output", type=Path, required=True)

    codex_hook_validate = subcommands.add_parser("codex-hook-validate")
    codex_hook_validate.add_argument("--input", type=Path, required=True)
    codex_hook_validate.add_argument("--event", default=None)

    codex_hook_import_capture = subcommands.add_parser("codex-hook-import-capture")
    codex_hook_import_capture.add_argument("--input", type=Path, required=True)
    codex_hook_import_capture.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_hook_import_capture.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_hook_import_capture.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_hook_import_capture.add_argument("--timeout", type=float, default=10.0)

    codex_hook_prepare_preview = subcommands.add_parser("codex-hook-prepare-preview")
    codex_hook_prepare_preview.add_argument("--input", type=Path, required=True)
    codex_hook_prepare_preview.add_argument("--event", default=None)
    codex_hook_prepare_preview.add_argument("--output", type=Path, default=Path(DEFAULT_CODEX_CONTEXT_PREVIEW_OUTPUT))
    codex_hook_prepare_preview.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_hook_prepare_preview.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_hook_prepare_preview.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_hook_prepare_preview.add_argument("--timeout", type=float, default=10.0)
    codex_hook_prepare_preview.add_argument("--context-window-tokens", type=int, default=DEFAULT_CODEX_CONTEXT_WINDOW_TOKENS)
    codex_hook_prepare_preview.add_argument("--budget-tokens", type=int, default=DEFAULT_CODEX_CONTEXT_BUDGET_TOKENS)
    codex_hook_prepare_preview.add_argument("--dry-run", action="store_true")

    codex_hook_render_config = subcommands.add_parser("codex-hook-render-config")
    codex_hook_render_config.add_argument("--mode", choices=["capture", "dry-run", "write"], required=True)
    codex_hook_render_config.add_argument("--python", default=sys.executable)
    codex_hook_render_config.add_argument("--capture-output", default=".local/mneme-codex-hooks.jsonl")
    codex_hook_render_config.add_argument(
        "--base-url",
        default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"),
    )
    codex_hook_render_config.add_argument("--token-env", default="MNEME_AUTH_TOKEN")
    codex_hook_render_config.add_argument("--timeout", type=float, default=10.0)
    codex_hook_render_config.add_argument("--output", type=Path, default=None)

    codex_hook_render_context_preview = subcommands.add_parser("codex-hook-render-context-preview-config")
    codex_hook_render_context_preview.add_argument("--python", default=sys.executable)
    codex_hook_render_context_preview.add_argument("--preview-output", default=DEFAULT_CODEX_CONTEXT_PREVIEW_OUTPUT)
    codex_hook_render_context_preview.add_argument(
        "--base-url",
        default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"),
    )
    codex_hook_render_context_preview.add_argument("--token-env", default="MNEME_AUTH_TOKEN")
    codex_hook_render_context_preview.add_argument("--timeout", type=float, default=10.0)
    codex_hook_render_context_preview.add_argument("--context-window-tokens", type=int, default=DEFAULT_CODEX_CONTEXT_WINDOW_TOKENS)
    codex_hook_render_context_preview.add_argument("--budget-tokens", type=int, default=DEFAULT_CODEX_CONTEXT_BUDGET_TOKENS)
    codex_hook_render_context_preview.add_argument("--output", type=Path, default=None)

    codex_setup = subcommands.add_parser("codex-setup")
    codex_setup_targets = codex_setup.add_subparsers(dest="target", required=True)
    codex_desktop_setup = codex_setup_targets.add_parser("codex-desktop")
    codex_desktop_setup.add_argument("--global", dest="global_install", action="store_true")
    codex_desktop_setup.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_desktop_setup.add_argument("--base-url", default=DEFAULT_CODEX_BASE_URL)
    codex_desktop_setup.add_argument("--python", default=sys.executable)
    codex_desktop_setup.add_argument("--dry-run", action="store_true")
    codex_desktop_setup.add_argument("--force-token", action="store_true")

    codex_doctor = subcommands.add_parser("codex-doctor")
    codex_doctor.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_doctor.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", DEFAULT_CODEX_BASE_URL))
    codex_doctor.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_doctor.add_argument("--timeout", type=float, default=2.0)

    codex_status = subcommands.add_parser("codex-status")
    codex_status.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
    codex_status.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", DEFAULT_CODEX_BASE_URL))
    codex_status.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_status.add_argument("--timeout", type=float, default=2.0)

    codex_service = subcommands.add_parser("codex-service")
    codex_service_actions = codex_service.add_subparsers(dest="action", required=True)
    for action_name in ("install", "start", "stop", "status", "logs", "uninstall"):
        action = codex_service_actions.add_parser(action_name)
        action.add_argument("--install-root", type=Path, default=Path(DEFAULT_CODEX_INSTALL_ROOT))
        action.add_argument("--label", default=DEFAULT_CODEX_SERVICE_LABEL)
        if action_name in {"install", "start", "stop", "uninstall"}:
            action.add_argument("--dry-run", action="store_true")
        if action_name == "install":
            action.add_argument("--start", action="store_true")
        if action_name == "logs":
            action.add_argument("--lines", type=int, default=80)

    benchmark = subcommands.add_parser("benchmark")
    benchmark.add_argument("--events", type=int, default=30)
    benchmark.add_argument("--db", type=Path, default=None)

    maintenance = subcommands.add_parser("maintenance")
    maintenance_actions = maintenance.add_subparsers(dest="action", required=True)
    maintenance_backup = maintenance_actions.add_parser("backup")
    maintenance_backup.add_argument("--db", type=Path, required=True)
    maintenance_backup.add_argument("--output", type=Path, required=True)
    maintenance_restore = maintenance_actions.add_parser("restore")
    maintenance_restore.add_argument("--backup", type=Path, required=True)
    maintenance_restore.add_argument("--target", type=Path, required=True)
    maintenance_restore.add_argument("--overwrite", action="store_true")
    maintenance_blob_gc = maintenance_actions.add_parser("blob-gc")
    maintenance_blob_gc.add_argument("--db", type=Path, required=True)
    maintenance_blob_gc.add_argument("--project-isolation-key", default=None)
    maintenance_blob_gc.add_argument("--session-id", default=None)
    maintenance_blob_gc.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    maintenance_blob_gc.add_argument("--execute", dest="dry_run", action="store_false")

    return parser


def settings_from_serve_args(args: argparse.Namespace) -> Settings:
    return load_settings(
        config_path=args.config,
        cli_overrides={
            "db_path": args.db,
            "host": args.host,
            "port": args.port,
            "auth_token": args.auth_token,
            "auth_token_file": args.auth_token_file,
            "insecure_dev": args.insecure_dev,
            "require_embeddings": args.require_embeddings,
            "strict_cost_mode": args.strict_cost_mode,
            "max_blob_bytes": args.max_blob_bytes,
            "max_session_id_length": args.max_session_id_length,
            "max_batch_total_blob_bytes": args.max_batch_total_blob_bytes,
            "max_multipart_metadata_overhead_bytes": args.max_multipart_metadata_overhead_bytes,
            "max_multipart_transaction_bytes": args.max_multipart_transaction_bytes,
            "max_multipart_transaction_ms": args.max_multipart_transaction_ms,
            "max_export_blob_inline_bytes": args.max_export_blob_inline_bytes,
            "max_export_session_memory_bytes": args.max_export_session_memory_bytes,
            "idempotency_key_min_retention_seconds": args.idempotency_key_min_retention_seconds,
            "startup_integrity_check": args.startup_integrity_check,
            "metrics_enabled": args.metrics_enabled,
            "metrics_format": args.metrics_format,
            "retention_sweep_interval_seconds": args.retention_sweep_interval_seconds,
            "retention_sweep_on_startup": args.retention_sweep_on_startup,
            "retention_sweep_on_session_close": args.retention_sweep_on_session_close,
            "retention_force_active_cleanup": args.retention_force_active_cleanup,
            "vacuum_max_duration_ms": args.vacuum_max_duration_ms,
            "checkpoint_max_pages": args.checkpoint_max_pages,
            "reindex_enqueue_when_provider_unavailable": args.reindex_enqueue_when_provider_unavailable,
            "reindex_foreground_write_priority": args.reindex_foreground_write_priority,
            "reindex_max_job_events": args.reindex_max_job_events,
            "reindex_max_events_per_transaction": args.reindex_max_events_per_transaction,
            "reindex_yield_between_transactions_ms": args.reindex_yield_between_transactions_ms,
            "reindex_provider_wait_timeout_seconds": args.reindex_provider_wait_timeout_seconds,
            "reindex_provider_max_requests_per_minute": args.reindex_provider_max_requests_per_minute,
            "reindex_provider_circuit_breaker_min_calls": args.reindex_provider_circuit_breaker_min_calls,
            "reindex_provider_circuit_breaker_failure_ratio": args.reindex_provider_circuit_breaker_failure_ratio,
            "reindex_provider_circuit_breaker_open_seconds": args.reindex_provider_circuit_breaker_open_seconds,
            "reindex_provider_circuit_breaker_half_open_requests": args.reindex_provider_circuit_breaker_half_open_requests,
            "reindex_provider_recovery_ramp_initial_requests_per_minute": args.reindex_provider_recovery_ramp_initial_requests_per_minute,
            "max_redaction_time_ms": args.max_redaction_time_ms,
            "max_tool_result_events": args.max_tool_result_events,
            "audit_forensic_retention_days": args.audit_forensic_retention_days,
            "audit_anonymize_deleted_session_audit": args.audit_anonymize_deleted_session_audit,
            "routing_default_mode": args.routing_default_mode,
            "routing_weight_debugging_dependency": args.routing_weight_debugging_dependency,
            "embedding_enabled": args.embedding_enabled,
            "embedding_provider": args.embedding_provider,
            "embedding_model": args.embedding_model,
            "embedding_base_url": args.embedding_base_url,
            "embedding_api_key": args.embedding_api_key,
            "reranker_enabled": args.reranker_enabled,
            "reranker_provider": args.reranker_provider,
            "reranker_model": args.reranker_model,
            "reranker_base_url": args.reranker_base_url,
            "reranker_api_key": args.reranker_api_key,
            "llm_enabled": args.llm_enabled,
            "llm_provider": args.llm_provider,
            "llm_model": args.llm_model,
            "llm_base_url": args.llm_base_url,
            "llm_api_key": args.llm_api_key,
            "router_min_candidates": args.router_min_candidates,
            "centroid_window": args.centroid_window,
            "enricher_max_tokens": args.enricher_max_tokens,
            "max_writer_queue_depth": args.max_writer_queue_depth,
            "backup_before_migrate": args.backup_before_migrate,
            "no_backup_before_migrate": args.no_backup_before_migrate,
            "memory_access_hint_enabled": args.memory_access_hint_enabled,
        },
    )


def validate_serve_security(settings: Settings) -> None:
    if settings.host not in {"127.0.0.1", "localhost", "::1"} and settings.insecure_dev:
        raise SystemExit("Refusing --insecure-dev on non-loopback bind.")
    if settings.host not in {"127.0.0.1", "localhost", "::1"} and not settings.insecure_dev:
        raise SystemExit("Refusing non-loopback bind without --insecure-dev.")


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "serve":
        settings = settings_from_serve_args(args)
        validate_serve_security(settings)
        app = create_app(settings)
        uvicorn.run(app, host=settings.host, port=settings.port)
        return

    if args.command == "mcp":
        server = create_mcp_server(
            base_url=args.base_url,
            token=args.token,
            timeout=args.timeout,
            default_session_id=args.default_session_id,
        )
        server.run("stdio")
        return

    if args.command == "codex-ingest":
        transcript = json.loads(args.input.read_text(encoding="utf-8"))
        result = asyncio.run(
            import_codex_transcript(
                transcript,
                base_url=args.base_url,
                token=resolve_token(token=args.token, install_root=args.install_root),
                timeout=args.timeout,
            )
        )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-ingest":
        raw = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
        payload = json.loads(raw)
        captured_at = current_codex_hook_timestamp()
        if args.dry_run:
            normalized = normalize_codex_hook_payload(payload, event_name=args.event, captured_at=captured_at)
            result = {
                "dry_run": True,
                "session": normalized.session,
                "event_batch": normalized.event_batch,
            }
        else:
            result = asyncio.run(
                import_codex_hook_payload(
                    payload,
                    event_name=args.event,
                    captured_at=captured_at,
                    base_url=args.base_url,
                    token=resolve_token(token=args.token, install_root=args.install_root),
                    timeout=args.timeout,
                )
            )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-capture":
        raw = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
        payload = json.loads(raw)
        result = capture_codex_hook_payload(payload, output_path=args.output, event_name=args.event)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-validate":
        result = validate_codex_hook_capture_file(args.input, event_name=args.event)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-import-capture":
        result = asyncio.run(
            import_codex_hook_capture_file(
                args.input,
                base_url=args.base_url,
                token=resolve_token(token=args.token, install_root=args.install_root),
                timeout=args.timeout,
            )
        )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-prepare-preview":
        if str(args.input) == "-":
            raw = sys.stdin.read()
            payload = json.loads(raw)
            captured_at = None
            event_name = args.event
            if isinstance(payload, dict) and isinstance(payload.get("payload"), dict):
                event_name = event_name or payload.get("event_name")
                captured_at = payload.get("captured_at") if isinstance(payload.get("captured_at"), str) else None
                payload = payload["payload"]
        else:
            item_event_name, payload, captured_at = select_codex_hook_capture_item(args.input, event_name=args.event)
            event_name = args.event or item_event_name
        result = asyncio.run(
            prepare_codex_context_preview(
                payload,
                event_name=event_name,
                captured_at=captured_at,
                output_path=args.output,
                base_url=args.base_url,
                token=resolve_token(token=args.token, install_root=args.install_root),
                timeout=args.timeout,
                context_window_tokens=args.context_window_tokens,
                budget_tokens=args.budget_tokens,
                dry_run=args.dry_run,
            )
        )
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-hook-render-config":
        result = render_codex_hook_config(
            mode=args.mode,
            python=args.python,
            capture_output=args.capture_output,
            base_url=args.base_url,
            token_env=args.token_env,
            timeout=args.timeout,
        )
        text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        if args.output is None:
            print(text)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return

    if args.command == "codex-hook-render-context-preview-config":
        result = render_codex_context_preview_hook_config(
            python=args.python,
            output=args.preview_output,
            base_url=args.base_url,
            token_env=args.token_env,
            timeout=args.timeout,
            context_window_tokens=args.context_window_tokens,
            budget_tokens=args.budget_tokens,
        )
        text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
        if args.output is None:
            print(text)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        return

    if args.command == "codex-setup":
        if args.target != "codex-desktop":
            raise SystemExit(f"Unsupported Codex setup target: {args.target}")
        if not args.global_install:
            raise SystemExit("codex-setup codex-desktop currently requires --global.")
        result = setup_codex_desktop_global(
            install_root=args.install_root,
            base_url=args.base_url,
            python=args.python,
            dry_run=args.dry_run,
            force_token=args.force_token,
        )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return

    if args.command in {"codex-doctor", "codex-status"}:
        result = codex_desktop_status(
            install_root=args.install_root,
            base_url=args.base_url,
            token=args.token,
            timeout=args.timeout,
        )
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "codex-service":
        if args.action == "install":
            result = codex_service_install(
                install_root=args.install_root,
                label=args.label,
                start=args.start,
                dry_run=args.dry_run,
            )
        elif args.action == "start":
            result = codex_service_start(
                install_root=args.install_root,
                label=args.label,
                dry_run=args.dry_run,
            )
        elif args.action == "stop":
            result = codex_service_stop(
                install_root=args.install_root,
                label=args.label,
                dry_run=args.dry_run,
            )
        elif args.action == "status":
            result = codex_service_status(install_root=args.install_root, label=args.label)
        elif args.action == "logs":
            result = codex_service_logs(
                install_root=args.install_root,
                label=args.label,
                lines=args.lines,
            )
        elif args.action == "uninstall":
            result = codex_service_uninstall(
                install_root=args.install_root,
                label=args.label,
                dry_run=args.dry_run,
            )
        else:
            raise SystemExit(f"Unsupported Codex service action: {args.action}")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "benchmark":
        from .benchmarks import run_local_benchmark

        result = run_local_benchmark(event_count=args.events, db_path=args.db)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return

    if args.command == "maintenance":
        if args.action == "backup":
            result = Store(args.db).backup_to(args.output)
        elif args.action == "restore":
            result = Store.restore_from_backup(args.backup, args.target, overwrite=args.overwrite)
        elif args.action == "blob-gc":
            result = Store(args.db).garbage_collect_blobs(
                project_isolation_key=args.project_isolation_key,
                session_id=args.session_id,
                dry_run=args.dry_run,
            )
        else:
            raise SystemExit(f"Unsupported maintenance action: {args.action}")
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
