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
    serve.add_argument("--centroid-window", type=int, default=None)
    serve.add_argument("--enricher-max-tokens", type=int, default=None)
    serve.add_argument("--memory-access-hint-enabled", dest="memory_access_hint_enabled", action="store_true", default=None)
    serve.add_argument("--memory-access-hint-disabled", dest="memory_access_hint_enabled", action="store_false")

    mcp = subcommands.add_parser("mcp")
    mcp.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    mcp.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    mcp.add_argument("--timeout", type=float, default=10.0)

    codex_ingest = subcommands.add_parser("codex-ingest")
    codex_ingest.add_argument("--input", type=Path, required=True)
    codex_ingest.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_ingest.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
    codex_ingest.add_argument("--timeout", type=float, default=10.0)

    codex_hook_ingest = subcommands.add_parser("codex-hook-ingest")
    codex_hook_ingest.add_argument("--input", type=Path, required=True)
    codex_hook_ingest.add_argument("--event", default=None)
    codex_hook_ingest.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_hook_ingest.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
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
    codex_hook_import_capture.add_argument("--timeout", type=float, default=10.0)

    codex_hook_prepare_preview = subcommands.add_parser("codex-hook-prepare-preview")
    codex_hook_prepare_preview.add_argument("--input", type=Path, required=True)
    codex_hook_prepare_preview.add_argument("--event", default=None)
    codex_hook_prepare_preview.add_argument("--output", type=Path, default=Path(DEFAULT_CODEX_CONTEXT_PREVIEW_OUTPUT))
    codex_hook_prepare_preview.add_argument("--base-url", default=os.environ.get("MNEME_BASE_URL", "http://127.0.0.1:8765"))
    codex_hook_prepare_preview.add_argument("--token", default=os.environ.get("MNEME_AUTH_TOKEN"))
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

    benchmark = subcommands.add_parser("benchmark")
    benchmark.add_argument("--events", type=int, default=30)
    benchmark.add_argument("--db", type=Path, default=None)

    return parser


def settings_from_serve_args(args: argparse.Namespace) -> Settings:
    return load_settings(
        config_path=args.config,
        cli_overrides={
            "db_path": args.db,
            "host": args.host,
            "port": args.port,
            "auth_token": args.auth_token,
            "insecure_dev": args.insecure_dev,
            "require_embeddings": args.require_embeddings,
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
            "memory_access_hint_enabled": args.memory_access_hint_enabled,
        },
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "serve":
        settings = settings_from_serve_args(args)
        if settings.host not in {"127.0.0.1", "localhost", "::1"} and not settings.insecure_dev:
            raise SystemExit("Refusing non-loopback bind without --insecure-dev.")
        app = create_app(settings)
        uvicorn.run(app, host=settings.host, port=settings.port)
        return

    if args.command == "mcp":
        server = create_mcp_server(base_url=args.base_url, token=args.token, timeout=args.timeout)
        server.run("stdio")
        return

    if args.command == "codex-ingest":
        transcript = json.loads(args.input.read_text(encoding="utf-8"))
        result = asyncio.run(
            import_codex_transcript(
                transcript,
                base_url=args.base_url,
                token=args.token,
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
                    token=args.token,
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
                token=args.token,
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
                token=args.token,
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

    if args.command == "benchmark":
        from .benchmarks import run_local_benchmark

        result = run_local_benchmark(event_count=args.events, db_path=args.db)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
