# Core Adapter Test Coverage Mapping

Phase 11 removes Codex-specific implementation from Mneme Core after the
Codex adapter repository gained its own contract and boundary checks. This
mapping records every deleted Core-side Codex test and the replacement coverage
or no-Core-behavior rationale.

## Replacement Anchors

- `tests/test_core_adapter_boundary.py`: Core/adapter boundary, neutral MCP
  instructions, neutral capabilities, CLI command surface, README/install docs.
- `tests/test_release_docs.py`: generic release, package, benchmark, storage,
  operations, migration, provider, and LLM-claim documentation checks.
- `tests/test_contract.py`: generic REST session/event/turn/idempotency,
  redaction, discovery, and capabilities contracts.
- `tests/test_context_prepare.py`: generic `/v1/context/prepare` behavior.
- `tests/test_mcp_contract.py`: generic MCP tool/REST parity, session
  resolution, default-session validation, and token-safe MCP CLI behavior.
- `mneme-codex-adapter` tests, captured in
  `.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/02-codex-adapter-sync-first/mneme-codex-adapter-sync.patch`.

## Deleted Test Mapping

| Deleted Core test | Replacement / rationale |
|---|---|
| `tests/test_codex_ingest.py::test_codex_transcript_normalizes_to_session_events_and_turn_payloads` | Adapter-owned transcript normalization; covered by `mneme-codex-adapter` ingest tests. Core keeps generic session/event schemas in `tests/test_openapi.py` and REST behavior in `tests/test_contract.py`. |
| `tests/test_codex_ingest.py::test_codex_transcript_imports_through_rest_and_replay_is_idempotent` | Adapter-owned import flow; Core idempotency is generic and covered by `tests/test_contract.py`. |
| `tests/test_codex_ingest.py::test_codex_imported_secret_is_redacted_before_storage_and_search` | Adapter-owned transcript source; Core redaction before persistence/search remains covered by generic contract tests. |
| `tests/test_codex_ingest.py::test_codex_ingest_cli_accepts_input_base_url_token_and_timeout` | Adapter CLI command; covered in `mneme-codex-adapter` CLI tests. Core must not expose `codex-ingest`, enforced by `tests/test_core_adapter_boundary.py`. |
| `tests/test_codex_ingest.py::test_codex_ingest_usage_docs_are_offline_reference_only` | Adapter documentation; covered in adapter repository. Core must not contain `adapters/codex`, enforced by `tests/test_core_adapter_boundary.py`. |
| `tests/test_codex_hooks.py::test_codex_hook_normalizes_to_session_and_stable_event_payloads` | Adapter-owned hook normalization; covered by `mneme-codex-adapter` hook tests. |
| `tests/test_codex_hooks.py::test_codex_hook_normalizes_real_codex_desktop_fields` | Adapter-owned host payload handling; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_imports_through_rest_and_replay_is_idempotent` | Adapter-owned import flow plus generic Core idempotency in `tests/test_contract.py`. |
| `tests/test_codex_hooks.py::test_codex_hook_import_capture_file_replays_real_capture_through_rest` | Adapter-owned capture replay; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_prepare_preview_writes_context_file` | Adapter-owned preview file; Core keeps request-only context preparation in `tests/test_context_prepare.py`. |
| `tests/test_codex_hooks.py::test_codex_hook_secret_is_redacted_after_service_ingestion` | Adapter source plus generic Core redaction/search coverage in `tests/test_contract.py`. |
| `tests/test_codex_hooks.py::test_codex_hook_ingest_cli_accepts_input_event_and_dry_run` | Adapter CLI; Core absence enforced by `tests/test_core_adapter_boundary.py`. |
| `tests/test_codex_hooks.py::test_codex_hook_ingest_cli_dry_run_prints_normalized_payload` | Adapter CLI dry run; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_prepare_preview_cli_dry_run_writes_jsonl` | Adapter CLI preview; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_prepare_preview_cli_selects_event_from_capture_jsonl` | Adapter CLI capture selection; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_validation_reports_enablement_readiness_without_content_leak` | Adapter payload validation; covered by adapter tests. Core redaction remains generic. |
| `tests/test_codex_hooks.py::test_codex_hook_capture_file_validation_summarizes_jsonl` | Adapter capture validation; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_capture_validation_accepts_real_codex_desktop_payload_shapes` | Adapter host-payload validation; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_capture_file_validation_reports_missing_file` | Adapter file validation; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_capture_cli_appends_jsonl_record` | Adapter CLI capture; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_validate_cli_prints_capture_summary` | Adapter CLI validation; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_render_capture_config_uses_explicit_python_runner` | Adapter hook config rendering; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_render_write_config_keeps_validation_warning_and_token_env` | Adapter hook config rendering; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_render_config_cli_prints_json` | Adapter CLI rendering; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_codex_hook_render_context_preview_config_cli_prints_user_prompt_hook` | Adapter CLI rendering; covered by adapter tests. |
| `tests/test_codex_hooks.py::test_project_local_codex_hooks_file_is_ignored` | Host-specific ignore rule; adapter-owned. Core repository no longer contains hook examples. |
| `tests/test_codex_hooks.py::test_codex_hook_capture_example_is_capture_only_and_publication_friendly` | Adapter example docs; covered in adapter repository. |
| `tests/test_codex_hooks.py::test_codex_hooks_usage_doc_keeps_auto_write_disabled_until_verified` | Adapter docs; covered in adapter repository. |
| `tests/test_codex_adapter.py::test_mcp_server_instructions_teach_codex_memory_contract` | Replaced by host-neutral `tests/test_core_adapter_boundary.py::test_mcp_server_instructions_are_host_neutral_memory_contract`. |
| `tests/test_codex_adapter.py::test_repo_local_mneme_memory_skill_contract_exists` | Adapter-owned skill; Core absence enforced by `tests/test_core_adapter_boundary.py`. |
| `tests/test_codex_adapter.py::test_agents_snippet_tells_codex_when_to_use_mneme` | Adapter-owned AGENTS snippet; covered in adapter repository. |
| `tests/test_codex_adapter.py::test_codex_hook_contract_example_is_disabled_until_payloads_are_verified` | Adapter-owned hook example; covered in adapter repository. |
| `tests/test_codex_adapter.py::test_codex_docs_capture_multi_machine_install_constraints` | Adapter installation docs; covered in adapter repository. Core install docs remain host-neutral. |
| `tests/test_codex_adapter.py::test_publication_docs_gate_github_second_machine_rehearsal` | Split across generic publication checks in `tests/test_release_docs.py` and adapter-owned second-machine rehearsal checks. |
| `tests/test_codex_adapter.py::test_core_package_discovery_excludes_host_adapters` | Preserved as `tests/test_release_docs.py::test_core_package_discovery_excludes_host_adapters`. |
| `tests/test_codex_adapter.py::test_readme_core_release_does_not_present_codex_adapter_docs_or_commands` | Replaced by `tests/test_core_adapter_boundary.py::test_core_readme_points_to_adapter_repo_without_embedded_codex_runbook`. |
| `tests/test_codex_adapter.py::test_release_docs_describe_benchmark_smoke_methodology_without_savings_claims` | Preserved as `tests/test_release_docs.py::test_release_docs_describe_benchmark_smoke_methodology_without_savings_claims`. |
| `tests/test_codex_adapter.py::test_installation_docs_describe_at_rest_storage_guidance` | Preserved as `tests/test_release_docs.py::test_installation_docs_describe_at_rest_storage_guidance`. |
| `tests/test_codex_adapter.py::test_operations_runbook_describes_restart_and_in_flight_behavior` | Preserved as `tests/test_release_docs.py::test_operations_runbook_describes_restart_and_in_flight_behavior`. |
| `tests/test_codex_adapter.py::test_installation_docs_describe_migration_backup_release_notes` | Preserved as `tests/test_release_docs.py::test_installation_docs_describe_migration_backup_release_notes`. |
| `tests/test_codex_adapter.py::test_publication_docs_require_real_embedding_and_reranker_smoke` | Preserved as `tests/test_release_docs.py::test_publication_docs_require_real_embedding_and_reranker_smoke`, with adapter docs removed from the source set. |
| `tests/test_codex_adapter.py::test_publication_docs_do_not_overclaim_llm_answer_synthesis` | Preserved as `tests/test_release_docs.py::test_publication_docs_do_not_overclaim_llm_answer_synthesis`. |
| `tests/test_codex_adapter.py::test_codex_global_setup_creates_safe_runtime_files` | Adapter setup behavior; covered by `mneme-codex-adapter` setup tests. |
| `tests/test_codex_adapter.py::test_codex_status_reports_missing_daemon_without_token_leak` | Adapter status behavior; covered by adapter tests. |
| `tests/test_codex_adapter.py::test_codex_service_install_dry_run_is_token_safe` | Adapter service-install behavior; covered by adapter tests. |
