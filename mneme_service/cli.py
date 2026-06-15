from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

import uvicorn

from .app import create_app
from .config import Settings, load_settings
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

    if args.command == "benchmark":
        from .benchmarks import run_local_benchmark

        result = run_local_benchmark(event_count=args.events, db_path=args.db)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
