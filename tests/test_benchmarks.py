from __future__ import annotations

import json
from pathlib import Path

from mneme_service.cli import main


def test_local_benchmark_returns_adapter_independent_summary(tmp_path: Path) -> None:
    from mneme_service.benchmarks import run_local_benchmark

    report = run_local_benchmark(event_count=8, db_path=tmp_path / "bench.db")

    assert report["schema_version"] == "mneme.benchmark_report.v0"
    assert report["mode"] == "LOCAL_FAKE_PROVIDERS"
    assert report["event_count"] == 8
    assert report["ingest"]["accepted"] == 8
    assert report["retrieval"]["result_count"] > 0
    assert report["context_prepare"]["message_count"] > 0
    assert report["costs"]["embedding_items"] >= 8
    assert report["provider_calls"]["embedding_batches"] >= 1
    assert report["timings_ms"]["ingest"] >= 0
    assert report["timings_ms"]["context_prepare"] >= 0


def test_cli_benchmark_prints_json_report(tmp_path: Path, capsys) -> None:
    main(["benchmark", "--events", "6", "--db", str(tmp_path / "bench.db")])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert report["schema_version"] == "mneme.benchmark_report.v0"
    assert report["event_count"] == 6
    assert report["ingest"]["accepted"] == 6
    assert report["db_path"] == str(tmp_path / "bench.db")
