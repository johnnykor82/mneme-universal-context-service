# Core/Adapter Dependency Extraction Audit

Status: Phase 11 Task 03 audit  
Date: 2026-06-27  
Scope: Core-side Codex artifacts that must be removed from Mneme Core only
after adapter sync and coverage-preservation gates pass.

## Decision Rules

- `move to adapter`: Codex-specific behavior belongs in
  `johnnykor82/mneme-codex-adapter`.
- `delete as Codex-specific`: Core should drop the artifact after equivalent
  adapter ownership or generic Core coverage exists.
- `promote to Core`: host-neutral logic must move to a Core module/API before
  deleting the Codex-specific source.
- `defer`: keep only until a named gate is satisfied; do not treat it as final
  Core ownership.

No new shared SDK/schema package is required by this audit. The current public
REST/MCP contract plus adapter-owned local request/response models are enough
for the approved refactor.

## Audit Table

| Source file | Unit/function/artifact | Decision | Rationale | Target file/API | Required tests before deletion | Risk/notes |
|---|---|---|---|---|---|---|
| `mneme_service/codex_ingest.py` | `CodexIngestPayloads` | move to adapter | Adapter-local DTO for Codex transcript normalization. | `mneme_codex_adapter.ingest.CodexIngestPayloads` | Adapter `tests/test_codex_ingest.py`; Core generic session/event/turn OpenAPI tests remain. | No Core REST/MCP behavior depends on this dataclass. |
| `mneme_service/codex_ingest.py` | `CodexIngestError` | move to adapter | Error type wraps adapter HTTP failures. | `mneme_codex_adapter.ingest.CodexIngestError` | Adapter ingest/hook tests that assert REST failure handling where needed. | A future public client error type would require a separate approved SDK spec. |
| `mneme_service/codex_ingest.py` | `normalize_codex_transcript` | move to adapter | Parses Codex transcript shape into Mneme REST payloads. Host-specific parsing is adapter-owned. | `mneme_codex_adapter.ingest.normalize_codex_transcript` | Adapter transcript normalization tests; Core `tests/test_openapi.py::test_openapi_documents_core_route_request_and_response_models`. | Core must retain only generic REST schemas. |
| `mneme_service/codex_ingest.py` | `import_codex_transcript` | move to adapter | Adapter calls Core through public `/v1/sessions/start`, `/v1/events`, `/v1/turns/complete`. | `mneme_codex_adapter.ingest.import_codex_transcript` | Adapter isolated suite against fresh Core wheel; Core contract tests for the three endpoints. | Do not keep a Core CLI wrapper for this. |
| `mneme_service/codex_ingest.py` | `_message_to_event` | move to adapter | Codex transcript message mapping is host-specific. | `mneme_codex_adapter.ingest._message_to_event` | Adapter normalization tests; Core event schema tests. | Uses generic `token_estimate`, which already remains in Core `utils.py`. |
| `mneme_service/codex_ingest.py` | `_default_event_type` | move to adapter | Codex role fallback mapping is adapter-owned. | `mneme_codex_adapter.ingest._default_event_type` | Adapter normalization tests. | No promotion needed. |
| `mneme_service/codex_ingest.py` | `_default_event_id` | move to adapter | Codex deterministic event id format is adapter-owned. | `mneme_codex_adapter.ingest._default_event_id` | Adapter idempotent replay tests. | Core idempotency remains endpoint-level. |
| `mneme_service/codex_ingest.py` | `_safe_id` | move to adapter | Local identifier sanitizer used by Codex mapping. | `mneme_codex_adapter.ingest._safe_id` | Adapter tests for generated ids. | Do not promote a shared helper unless another Core module needs it. |
| `mneme_service/codex_ingest.py` | `_required_object`, `_required_str` | move to adapter | Adapter-local input validation helpers. | `mneme_codex_adapter.ingest` | Adapter invalid-input tests if expanded. | Core schema validation remains in REST endpoint validators. |
| `mneme_service/codex_ingest.py` | `_post_json`, `_response_json` | move to adapter | Thin HTTP helper for adapter REST calls. | `mneme_codex_adapter.ingest` | Adapter REST ingest tests; optional future public client tests if a client package is approved. | Do not promote to Core now; Core already has `rest_client.py` for MCP-side needs. |
| `mneme_service/codex_hooks.py` | `CodexHookPayloads` | move to adapter | Adapter-local DTO for Codex hook session/event/turn payloads. | `mneme_codex_adapter.hooks.CodexHookPayloads` | Adapter hook normalization/import tests. | Core generic lifecycle schemas remain tested elsewhere. |
| `mneme_service/codex_hooks.py` | `CODEX_HOOK_MATCHERS` and context preview constants | move to adapter | Codex hook names and defaults are host-specific. | `mneme_codex_adapter.hooks` | Adapter hook config rendering tests. | No Core ownership. |
| `mneme_service/codex_hooks.py` | `normalize_codex_hook_payload` | move to adapter | Translates Codex hook payloads to Mneme REST payloads. | `mneme_codex_adapter.hooks.normalize_codex_hook_payload` | Adapter hook normalization and import tests; Core session/event/turn endpoint tests. | Core must not know Codex hook field names. |
| `mneme_service/codex_hooks.py` | `_turn_complete_payload` | move to adapter | Stop-hook-to-turn-complete mapping is Codex lifecycle logic. | `mneme_codex_adapter.hooks._turn_complete_payload` | Adapter Stop hook tests; Core `/v1/turns/complete` final-status tests. | Core retains only endpoint behavior, not Stop hook interpretation. |
| `mneme_service/codex_hooks.py` | `import_codex_hook_payload` | move to adapter | Adapter submits normalized hook payloads to Core REST. | `mneme_codex_adapter.hooks.import_codex_hook_payload` | Adapter hook REST replay tests against Core wheel. | Core cleanup must remove the `mneme codex-hook-ingest` command. |
| `mneme_service/codex_hooks.py` | `import_codex_hook_capture_file` | move to adapter | Reads Codex capture files and posts to Core. | `mneme_codex_adapter.hooks.import_codex_hook_capture_file` | Adapter capture replay tests. | Capture-file format is host-specific. |
| `mneme_service/codex_hooks.py` | `build_codex_context_prepare_request` | move to adapter | Builds a Codex-flavored `/v1/context/prepare` request. | `mneme_codex_adapter.hooks.build_codex_context_prepare_request` | Adapter context preview test; Core generic context-prepare tests for canonical budget keys. | Task 02 fixed stale budget keys here. |
| `mneme_service/codex_hooks.py` | `prepare_codex_context_preview` | move to adapter | Preview-file workflow is Codex adapter UX, not Core behavior. | `mneme_codex_adapter.hooks.prepare_codex_context_preview` | Adapter context preview test against Core wheel. | Core keeps `/v1/context/prepare` only. |
| `mneme_service/codex_hooks.py` | `capture_codex_hook_payload` | move to adapter | Codex hook capture JSONL is adapter tooling. | `mneme_codex_adapter.hooks.capture_codex_hook_payload` | Adapter capture CLI tests. | No Core ownership. |
| `mneme_service/codex_hooks.py` | `current_codex_hook_timestamp` | move to adapter | Timestamp helper exists for Codex hook capture commands. | `mneme_codex_adapter.hooks.current_codex_hook_timestamp` | Adapter CLI dry-run/capture tests. | Core time helpers remain generic elsewhere. |
| `mneme_service/codex_hooks.py` | `validate_codex_hook_payload` | move to adapter | Validates Codex hook payloads for enablement. | `mneme_codex_adapter.hooks.validate_codex_hook_payload` | Adapter validation tests. | Core should not validate host hook completeness. |
| `mneme_service/codex_hooks.py` | `validate_codex_hook_capture_file` | move to adapter | Capture-file validation is adapter-owned. | `mneme_codex_adapter.hooks.validate_codex_hook_capture_file` | Adapter capture validation tests. | No Core dependency. |
| `mneme_service/codex_hooks.py` | `select_codex_hook_capture_item` | move to adapter | Selects host-specific capture records. | `mneme_codex_adapter.hooks.select_codex_hook_capture_item` | Adapter context preview CLI tests. | No Core dependency. |
| `mneme_service/codex_hooks.py` | `render_codex_hook_config` | move to adapter | Renders Codex hook config. | `mneme_codex_adapter.hooks.render_codex_hook_config` | Adapter config rendering tests. | Core README should point to adapter docs instead. |
| `mneme_service/codex_hooks.py` | `render_codex_context_preview_hook_config` | move to adapter | Renders Codex preview hook config. | `mneme_codex_adapter.hooks.render_codex_context_preview_hook_config` | Adapter config rendering tests. | No Core ownership. |
| `mneme_service/codex_hooks.py` | `_session_id`, `_hook_event_name`, `_hook_timestamp`, `_event_id` | move to adapter | Codex hook identity/timestamp derivation is host-specific. | `mneme_codex_adapter.hooks` | Adapter normalization/idempotency tests. | Core continues to validate normalized IDs at endpoint boundary. |
| `mneme_service/codex_hooks.py` | `_content_text`, `_prepare_prompt_text`, `_format_hook_value` | move to adapter | Codex payload summarization and preview text are adapter-owned. | `mneme_codex_adapter.hooks` | Adapter normalization/preview tests. | Do not promote prompt rendering to Core. |
| `mneme_service/codex_hooks.py` | `_enrich_event_metadata` | move to adapter | Adds Codex-specific metadata keys. | `mneme_codex_adapter.hooks` | Adapter metadata tests. | Core stores metadata generically. |
| `mneme_service/codex_hooks.py` | `_has_supported_content`, `_has_text`, `_has_text_value` | move to adapter | Adapter validation helpers. | `mneme_codex_adapter.hooks` | Adapter validation tests. | No promotion needed. |
| `mneme_service/codex_hooks.py` | `_utc_now`, `_append_jsonl`, `_load_capture_items`, `_capture_item` | move to adapter | Capture-file utility logic is adapter-owned. | `mneme_codex_adapter.hooks` | Adapter capture file tests. | Generic file helpers are not required by Core. |
| `mneme_service/codex_hooks.py` | `_render_hook_command`, `_render_context_preview_command` | move to adapter | Shell command construction is Codex adapter config behavior. | `mneme_codex_adapter.hooks` | Adapter render-config tests. | Commands must point at `mneme_codex_adapter.cli`, not Core `mneme_service.cli`. |
| `mneme_service/codex_setup.py` | `setup_codex_desktop_global` | move to adapter | Installs Codex-specific local runtime files and examples. | `mneme_codex_adapter.setup.setup_codex_desktop_global` | Adapter setup tests; Core package boundary tests. | Core setup command must be removed. |
| `mneme_service/codex_setup.py` | `codex_desktop_status` | move to adapter | Codex doctor/status UX is host-specific. | `mneme_codex_adapter.setup.codex_desktop_status` | Adapter status tests, including token-safe output and configurable service label. | Core health/capabilities endpoints remain generic. |
| `mneme_service/codex_setup.py` | `resolve_token`, `_read_token`, `_token_source` | move to adapter | Reads adapter install-root token files. | `mneme_codex_adapter.setup` | Adapter token-safe setup/status tests. | Core keeps generic token-file config validation in `config.py`. |
| `mneme_service/codex_setup.py` | `codex_service_install`, `codex_service_start`, `codex_service_stop`, `codex_service_uninstall` | move to adapter | macOS LaunchAgent management for Codex install root. | `mneme_codex_adapter.setup` | Adapter service dry-run/status tests. | Core must not own host service lifecycle. |
| `mneme_service/codex_setup.py` | `codex_service_status`, `codex_service_logs` | move to adapter | LaunchAgent status/log paths are host install concerns. | `mneme_codex_adapter.setup` | Adapter status/log tests. | Task 02 fixed plist collision through service label configurability. |
| `mneme_service/codex_setup.py` | `_install_root`, `_ensure_dir`, `_write_secret_env`, `_write_text_file`, `_write_json_file`, `_write_executable` | move to adapter | Local file creation helpers for Codex install root. | `mneme_codex_adapter.setup` | Adapter setup tests. | Core storage permission tests remain in `tests/test_storage.py`. |
| `mneme_service/codex_setup.py` | `_serve_script`, `_mcp_script` | move to adapter | Adapter-generated scripts launch Core as an external daemon/MCP server. | `mneme_codex_adapter.setup` using public `mneme` CLI or module invocation | Adapter setup tests; Core `tests/test_config.py` for `serve`/`mcp` CLI. | Core keeps `mneme serve` and `mneme mcp`, but not Codex wrapper generation. |
| `mneme_service/codex_setup.py` | `_capability_summary`, `_http_get_json` | move to adapter | Adapter status summarizes Core public endpoints. | `mneme_codex_adapter.setup` | Adapter doctor/status tests; Core health/capabilities contract tests. | A future generic client may be separate, not needed now. |
| `mneme_service/codex_setup.py` | `_entrypoint` | move to adapter | Checks adapter install-root command shims. | `mneme_codex_adapter.setup` | Adapter status tests. | Host-specific. |
| `mneme_service/codex_setup.py` | `_service_paths`, `_launchd_plist`, `_launchd_domain`, `_run_command`, `_tail_file`, `_service_warnings` | move to adapter | macOS LaunchAgent implementation details are adapter-owned. | `mneme_codex_adapter.setup` | Adapter service tests; no Core test required beyond boundary checks. | No live LaunchAgent should be touched by Core tests. |
| `mneme_service/codex_setup.py` | `_default_config` | move to adapter | Adapter starter config for Codex install. | `mneme_codex_adapter.setup` | Adapter setup tests; Core config parser tests remain. | Core example config can stay generic only. |
| `mneme_service/codex_setup.py` | `_status_next_steps` | move to adapter | Codex troubleshooting UX. | `mneme_codex_adapter.setup` | Adapter doctor/status tests. | Host-specific text. |
| `mneme_service/codex_setup.py` | `_sample_transcript` | move to adapter | Codex sample transcript data. | `mneme_codex_adapter.setup` or adapter docs fixtures | Adapter setup/ingest tests. | Core must not ship Codex samples. |
| `mneme_service/cli.py` | Imports from `.codex_hooks`, `.codex_ingest`, `.codex_setup` | delete as Codex-specific | Core CLI should expose only Core commands. | Adapter `mneme-codex` CLI owns Codex imports. | Core CLI tests for `serve`, `mcp`, `benchmark`, `maintenance`; boundary import check. | Remove only after adapter CLI patch is published or preserved. |
| `mneme_service/cli.py` | `codex-ingest`, `codex-hook-*`, `codex-setup`, `codex-doctor`, `codex-status`, `codex-service` parser wiring | delete as Codex-specific | Host commands belong under `mneme-codex`, not `mneme`. | `mneme_codex_adapter.cli` | Adapter CLI parser tests; Core CLI negative/boundary tests. | Core cleanup must update docs that mention these commands. |
| `mneme_service/cli.py` | Codex command execution branches in `main` | delete as Codex-specific | Calls adapter-only logic from Core CLI. | `mneme_codex_adapter.cli.main` | Adapter CLI dry-run/setup/service tests; Core CLI smoke tests. | Removing these branches should also remove imports and constants. |
| `adapters/codex/` | Codex install, MCP, hook, ingest, dogfood docs and examples | move to adapter | Host docs/examples are adapter product surface. | Adapter repo docs/adapters directory | Adapter docs tests; Core docs pointer test. | Core may keep one short link to adapter repository. |
| `.agents/skills/mneme-memory/SKILL.md` | Codex Mneme operating skill | move to adapter | Skill is Codex-agent-specific adapter behavior. | `mneme_codex_adapter/skills/mneme-memory/SKILL.md` | Adapter skill-install test; Core boundary check that skill is absent from package/tree after cleanup. | Local installed plugin copy may exist outside Core repo; do not delete live user skill. |
| `tests/test_codex_ingest.py` | Codex transcript tests | delete as Codex-specific | Tests adapter behavior, not Core behavior. | Adapter `tests/test_codex_ingest.py` | Replacement Core tests for generic session/event/turn endpoints remain in `tests/test_contract.py` and `tests/test_openapi.py`. | Task 04 must record 1:1 test coverage mapping. |
| `tests/test_codex_hooks.py` | Codex hook tests | delete as Codex-specific | Tests adapter hook parsing/config/preview. | Adapter `tests/test_codex_hooks.py` | Core generic context-prepare, event ingest, and turn-complete tests. | Keep until Task 04 mapping is written. |
| `tests/test_codex_adapter.py` | Core release-boundary and Codex setup/docs tests | split: promote generic boundary checks, move/delete Codex docs tests | Some tests protect Core package boundary; others validate adapter docs/setup. | Generic boundary tests in Core; adapter docs/setup tests in adapter repo. | Core replacement tests for package discovery, no host modules/docs in wheel/sdist, README pointer only. | This is the main coverage-preservation hotspot for Task 04. |
| `README.md` | Development-checkout Codex adapter references | defer then delete/shorten | Current README already distinguishes Core and adapter; after cleanup it should keep only a short adapter repo pointer. | Core README adapter index/pointer section | Core docs boundary tests. | Do not remove public adapter discovery link entirely. |
| `docs/INSTALLATION.md` | Multi-machine Codex setup and adapter publication text | defer then move/shorten | Host setup guidance belongs in adapter docs, but Core install docs may point to official adapters. | Adapter install docs plus short Core pointer | Core docs boundary tests; adapter install docs tests. | Preserve generic Core install/daemon instructions. |
| `docs/MNEME_V0_COMPLIANCE_MATRIX.md` and reviewer packets | Historical Codex evidence references | defer | Historical compliance evidence may mention Codex tests/batches; not active adapter implementation. | Leave as history or move to reviewer archive if boundary check needs allowlist. | Boundary documentation allowlist check. | Do not rewrite historical evidence without explicit review. |
| `docs/MNEME_CORE_ADAPTER_BOUNDARY_REFACTOR_SPEC.md` and `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md` | Codex mentions in approved boundary docs | defer | These docs intentionally explain the split and are allowed boundary evidence. | Core docs | Docs boundary tests should allow these files. | Keep as canonical Phase 11 evidence. |

## Coverage Preservation Required For Task 04

Before deleting Core-side Codex modules/tests, Task 04 must keep or add generic
Core coverage for:

- `/v1/sessions/start`, `/v1/events`, and `/v1/turns/complete` request/response
  contracts and idempotent replay behavior.
- `/v1/context/prepare` canonical budget keys, latest-user protection, and
  evidence wrapper behavior.
- OpenAPI typed schemas for session/event/turn/context-prepare surfaces.
- Core CLI `serve`, `mcp`, `benchmark`, and `maintenance` commands after Codex
  subcommands are removed.
- Package/tree/distribution checks proving Core contains no host adapter
  implementation, Codex docs/examples, or Codex skill files.
- README/docs checks proving Core has only short adapter repository pointers.

## Abort Gate Review

The audit found no hidden generic behavior that requires a new SDK/schema
package before Core cleanup. The one generic behavior used by adapters is the
already public REST/MCP contract. If Task 04 discovers a missing generic test
while deleting Codex files, it should add the generic test first rather than
promoting Codex-specific code into Core.
