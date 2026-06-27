# Mneme Core/Adapter Boundary Refactor Specification

Status: Approved for spec-driven planning
Date: 2026-06-27
Owner: Mneme project
Intended next step: create `.planning/` execution plan, then obtain Planning
Gate approval before implementation

## 1. Reviewer Summary

This document specifies a corrective refactor for Mneme's repository and package
boundaries.

Mneme's intended architecture is:

- `mneme-universal-context-service` is the universal, host-neutral Core memory
  service.
- Host-specific behavior lives outside Core, in adapter packages or in
  third-party host integrations that use Mneme's public REST/MCP contracts.
- `mneme-codex-adapter` owns Codex-specific behavior.

The current public Core repository has accumulated Codex-specific modules,
docs, tests, and a Codex operating skill as a compatibility shortcut during the
v0 compliance update. That contradicts the intended Core/Adapter boundary and
has already caused drift: Core tests pass, while the standalone Codex adapter
repository has failing tests against the updated Core behavior.

This refactor restores the intended architecture. It does not add new memory
features. It moves host-specific Codex implementation and tests out of Core,
updates the standalone adapter to match the current Core contract, and adds
explicit boundary rules so this mistake is less likely to recur.

## 1.1 Review Revision Notes

Draft v0.2 incorporated the first review round. Draft v0.3 incorporated the
second review round. Draft v0.4 incorporated the third review round. Draft v0.5
incorporates the fourth review round. The main changes are:

- make the migration adapter-first: copy/sync Codex behavior into the adapter
  and make adapter tests pass before deleting the Core copy;
- add a dependency extraction audit before removing Core-side Codex modules, so
  generic Core behavior is promoted to neutral Core APIs instead of being lost;
- decide that the adapter must not import `mneme_service.*` internals; REST/MCP
  is the official integration contract, and any future shared Python types must
  live in a deliberately published lightweight SDK/schema package;
- replace fragile grep-only boundary checks with structural module/package
  checks and wheel/sdist contents checks;
- require cross-repository verification where the adapter is tested against the
  newly built Core artifact, not an accidentally preinstalled Core package;
- add a concrete contract version mechanism based on
  `docs/MNEME_CONTRACT_VERSION`;
- add static CI guards that forbid adapter imports from `mneme_service.*`;
- require clean verification environments with recorded Core artifact identity;
- require generic Core contract tests to replace coverage previously provided
  by deleted Codex-specific tests;
- define the dependency audit artifact format and abort gate before Core
  cleanup;
- define initial host denylist/allowlist expectations for boundary checks;
- define exact contract-version fields, boundary-policy schema, publication
  hygiene inputs, cross-repository evidence format, rollback/version sequencing,
  and OpenAPI-based adapter drift checks;
- normalize runtime paths in verification evidence, add Windows home-path
  hygiene detectors, and make Core/adapter contract-range mismatch a hard
  cross-repository CI failure.
- record project-owner approval to proceed to spec-driven planning on
  2026-06-27.

## 2. Current Context And Evidence

### 2.1 Repositories

Current intended repositories:

| Repository | Intended role |
|---|---|
| `johnnykor82/mneme-universal-context-service` | Mneme Core: REST/MCP daemon, storage, retrieval, context preparation, provider integration, generic docs/tests. |
| `johnnykor82/mneme-codex-adapter` | Codex adapter: Codex hooks, transcript ingestion, setup/doctor/service commands, Codex docs, Codex operating skill. |

Feedback from the second environment on 2026-06-26 reported:

- Core updated from `01f969d1011a715f20d7dbb4f8779b18072945ef` to `47f52d8`.
- Adapter updated from `d0415287b9643422cef4063e5bc2b3ba73e72a5b` to `2a76286`.
- Core tests passed: `315 passed, 1 warning`.
- Runtime smoke on port `8766` passed.
- Standalone adapter repository tests failed: `3 failed, 30 passed`.

The failing standalone adapter tests were:

- `tests/test_codex_hooks.py::test_codex_hook_prepare_preview_writes_context_file`
- `tests/test_codex_ingest.py::test_codex_transcript_imports_through_rest_and_replay_is_idempotent`
- `tests/test_setup.py::test_status_reports_missing_daemon_without_token_leak`

Observed failure causes:

- Adapter ingest still expected turn status `RECORDED`; updated Core returns
  `COMPLETED`.
- Adapter hook preview used an older `/v1/context/prepare` request shape.
- Adapter status expected `service.plist_exists is False`; current status
  behavior reports true when the LaunchAgent plist exists.

### 2.2 Existing specification already identifies the boundary

`docs/MNEME_STANDALONE_SPEC.md`, Section 7, currently states the target
publication boundary:

- Core repository: daemon, REST/MCP server, storage, retrieval, context
  assembly, provider clients, generic tests, generic docs.
- Codex adapter repository: Codex-specific CLI, hooks, skills, setup, doctor,
  service management, and Codex docs.
- Future adapters: separate packages.

The same section also records a current gap:

> if adapter code remains under `adapters/codex` in the core checkout, the
> release plan must either move it to the adapter package or mark it as
> development-only and exclude it from core distribution artifacts.

This refactor turns that recorded gap into an explicit corrective change.

### 2.3 Current Core tree contains Codex-specific artifacts

The current Core checkout contains Codex-specific implementation and test files,
including:

- `mneme_service/codex_hooks.py`
- `mneme_service/codex_ingest.py`
- `mneme_service/codex_setup.py`
- `adapters/codex/...`
- `.agents/skills/mneme-memory/SKILL.md`
- `tests/test_codex_hooks.py`
- `tests/test_codex_ingest.py`
- `tests/test_codex_adapter.py`

These files are useful, but they belong to the Codex adapter product boundary,
not to Mneme Core.

## 3. Problem Statement

Mneme Core currently carries host-specific Codex behavior. This causes four
problems.

### 3.1 Core is no longer purely universal

Core should not know how Codex hooks, transcripts, setup files, LaunchAgents,
or Codex operating skills work. If Core accepts Codex-specific implementation,
future Hermes, Cursor, OpenAI Agents SDK, Claude Code, LangGraph, or custom
agent integrations may also try to add their runtime-specific code to Core.

That turns Core into a collection of host integrations instead of a stable
memory service.

### 3.2 Drift between Core and adapter becomes likely

The same Codex behavior now exists in two places:

- Core-side `mneme_service.codex_*`
- Standalone adapter-side `mneme_codex_adapter.*`

Once the copies diverge, one repository can pass tests while the other fails.
The 2026-06-26 feedback shows exactly this failure mode.

### 3.3 Public API boundaries become unclear

Adapter authors should integrate through public REST/MCP contracts. If Core
ships host-specific Python modules, integration authors may import internal
modules instead of using the stable service contract. That makes future Core
changes harder and encourages undocumented dependencies.

### 3.4 Verification can become falsely positive

Core tests may pass because Core contains a newer copy of Codex integration
logic, while the actual standalone adapter package used by users still fails.
This creates a false "all green" state.

## 4. Architectural Decision

This refactor chooses Variant C:

Core is memory. Adapter is translator.

Mneme Core must remain host-neutral. Host-specific code must live in adapter
packages or in third-party host projects that call Mneme through public REST/MCP
contracts.

### 4.1 Normative boundary

Mneme Core MUST contain:

- REST API implementation and OpenAPI schemas.
- MCP memory tools that proxy or expose Core behavior.
- Storage, retrieval, ranking, context assembly, traces, costs, metrics,
  security, auth, blobs, migrations, and maintenance.
- Generic provider clients and provider capability reporting.
- Generic host adapter contract documentation.
- Generic adapter conformance fixtures or tests that do not implement a
  specific host runtime and do not use host-specific payloads, paths, file
  names, identifiers, or setup flows.
- Generic conformance tests may use mock adapters or neutral sample clients, but
  they MUST test only Core REST/MCP behavior and MUST NOT import adapter
  repository code.
- Short pointers to known adapter repositories when useful for discovery.

Mneme Core MUST NOT contain:

- Codex hook handlers.
- Codex transcript parsers.
- Codex setup, doctor, service, or skill-install commands.
- Codex operating skills such as `mneme-memory`.
- Codex-specific docs, tutorials, config examples, payload examples, setup
  flows, or troubleshooting instructions, except for a short pointer to the
  standalone adapter repository.
- Hermes-specific lifecycle code.
- Cursor/OpenAI Agents SDK/Claude Code/LangGraph-specific runtime logic.
- Host-specific tests that validate one adapter's behavior instead of generic
  Core contracts.

A test is host-specific if it uses host-specific payloads, paths, file names,
identifiers, setup flows, environment assumptions, or fixtures, even when the
assertion ultimately targets a Core REST/MCP endpoint.

### 4.2 Adapter responsibility

The Codex adapter MUST own:

- Codex hook payload validation and ingestion.
- Codex transcript parsing.
- Codex context-preview behavior.
- Codex setup, doctor, status, service, and skill commands.
- Codex-specific docs, examples, and config snippets.
- `mneme-memory` Codex operating skill.
- Codex adapter tests.

The adapter SHOULD call Core through REST/MCP contracts. It SHOULD NOT require
private Core Python modules for Codex-specific behavior.

The adapter MUST NOT import `mneme_service.*` modules from Core. If future
Python-native sharing is needed, it must be introduced as a separate,
deliberately published lightweight package such as `mneme-client` or
`mneme-schemas`, with its own public compatibility contract. That future package
is outside the scope of this refactor unless explicitly approved later.

Because shared Python schemas are out of scope, adapter-owned local request and
response models MUST be checked against Core's official OpenAPI schema or
equivalent REST/MCP contract fixture. The adapter may generate local types from
OpenAPI or validate request/response examples against OpenAPI in CI. It MUST
NOT copy private Core dataclasses, private Pydantic models, or private function
signatures as an undocumented compatibility layer.

### 4.3 Third-party direct integration path

Not every host integration must be a separate official adapter repository.

A third-party project MAY integrate Mneme directly by calling public REST/MCP
contracts from inside that host's own plugin, service, or agent runtime. That is
allowed and expected.

However, such host-specific integration code MUST NOT be added to Mneme Core.
The integration belongs either in:

- a separate adapter package/repository, or
- the third-party host project itself.

Core's responsibility is to document the public REST/MCP contracts well enough
for these integrations.

## 4.4 Contract Versioning Policy

Mneme Core MUST publish a machine-readable contract version for the public
REST/MCP surface used by adapters.

For this refactor, the initial mechanism is:

- Core stores the canonical contract version in `docs/MNEME_CONTRACT_VERSION`.
- `docs/MNEME_CONTRACT_VERSION` is a UTF-8 text file containing exactly one
  SemVer line: `MAJOR.MINOR.PATCH`, with an optional trailing newline and no
  prefix or surrounding prose.
- Core OpenAPI metadata uses `info.version` and MUST equal
  `docs/MNEME_CONTRACT_VERSION`.
- Core runtime metadata uses the field name `mneme_contract_version` in
  `/v1/health` and `/v1/capabilities`, and both values MUST equal
  `docs/MNEME_CONTRACT_VERSION`.
- The contract-version check fails the build if any required surface is missing
  the field, reports a different version, or cannot be inspected.
- If a future Core variant removes `/v1/health` or `/v1/capabilities`, that
  removal is itself a contract change and must be handled through the SemVer
  rules below before the check may be changed.
- The Codex adapter declares a supported range such as
  `mneme-core-contract >=0.7,<0.8` in adapter metadata or a documented adapter
  constant.

Versioning follows SemVer-style compatibility:

- MAJOR changes for removal or rename of public REST/MCP endpoints, request
  fields, response fields, enum values, tool names, or behavior required by an
  adapter.
- MAJOR changes for changing a public field type, requiredness, or semantic
  meaning in a backward-incompatible way.
- MINOR changes for adding optional request fields, optional response fields,
  endpoints, tools, capabilities, or metadata.
- PATCH changes for documentation clarifications, bug fixes that preserve the
  documented contract, and implementation changes invisible to public REST/MCP
  callers.

An adapter may accept a Core version only if the published Core contract version
falls within the adapter's declared supported range.

Contract-change sequencing:

1. A Core PR that changes the public REST/MCP contract updates
   `docs/MNEME_CONTRACT_VERSION`, OpenAPI metadata generation, runtime metadata,
   and Core contract tests in the same PR.
2. If the change is breaking, the Core PR is labeled or documented as
   `contract-change:major` and must not be treated as adapter-compatible until
   the adapter PR is ready.
3. The adapter PR updates its supported Core contract range, request/response
   validation, and tests, and links to the Core PR or commit.
4. Cross-repository CI runs after both revisions are available and records the
   exact Core and adapter revisions tested together.
5. Merge/release order must preserve a green compatible pair: either merge Core
   and adapter in a coordinated release window or release adapter support before
   users are directed to the new Core contract.

## 5. Goals

### G-001: Restore Core neutrality

After the refactor, the Core repository and distributable package must not
contain host-specific adapter implementation code.

### G-002: Make Codex adapter the source of truth for Codex behavior

Codex hooks, transcript ingestion, setup/status/service commands, docs, examples,
and `mneme-memory` skill must be owned by `mneme-codex-adapter`.

### G-003: Preserve current working functionality

Users must still be able to run Core and Codex adapter together. The refactor
must not remove working Codex integration; it must move and synchronize it.

### G-004: Prevent future boundary drift

The boundary must be recorded in normative documentation, tests, and package
checks so future agents do not reintroduce host-specific code into Core.

### G-005: Keep REST/MCP as the integration contract

Adapter behavior must be validated against the public Core contracts, not
against private implementation details.

### G-006: Make Core/adapter compatibility explicit

The adapter must declare which Mneme Core contract version or version range it
supports, and Core breaking changes must require a documented contract/version
change before adapter tests are updated.

## 6. Non-Goals

This refactor does not:

- add new retrieval, ranking, redaction, blob, or context assembly behavior;
- change Core REST/MCP semantics unless needed to document an already-shipped
  contract;
- implement new adapters beyond Codex;
- make MCP alone perform automatic prompt replacement;
- remove the ability for third-party projects to integrate directly with Core;
- publish secrets or machine-specific local configuration.

## 7. Requirements

### R-001: Core package boundary

The Core Python package must not include host-specific adapter modules.

Acceptance:

- `mneme_service/codex_hooks.py` is absent from Core.
- `mneme_service/codex_ingest.py` is absent from Core.
- `mneme_service/codex_setup.py` is absent from Core.
- Core package discovery is verified against an explicit allowlist of Core
  package prefixes and an explicit denylist of host-specific prefixes.
- The Core wheel and sdist do not include adapter packages, Codex skills, or
  host runtime modules.

### R-002: Core repository boundary

The Core repository must not depend on Codex-specific files for its test suite
or user-facing documentation.

Acceptance:

- Core tests pass without `tests/test_codex_*`.
- Generic Core REST/MCP contract tests cover all Core behaviors previously
  validated by deleted Codex-specific tests.
- Core docs do not require `adapters/codex/...`.
- Core README points Codex users to `mneme-codex-adapter`, but does not include
  Codex setup instructions as Core instructions.

### R-003: Adapter owns Codex implementation

The standalone Codex adapter repository must contain the Codex-specific code
needed for current Codex behavior.

Acceptance:

- Adapter has hook validation/import implementation.
- Adapter has transcript ingest implementation.
- Adapter has setup/status/service/doctor/skill implementation.
- Adapter has `mneme-memory` skill source-of-truth.

### R-004: Adapter sync with current Core

The Codex adapter must be updated to match the approved Core REST/MCP contract
shipped by Core commit `47f52d8` or a later approved Core commit.

Acceptance:

- Adapter records the exact Core baseline commit or version used during this
  migration.
- Adapter ingest tests expect `schema_version: mneme.turn_complete_result.v0`.
- Adapter ingest tests expect final turn status `COMPLETED`.
- Adapter context-preview request shape matches the current
  `/v1/context/prepare` schema.
- Adapter setup/status tests match current LaunchAgent plist behavior.
- Adapter tests exercise Core through public REST/MCP behavior or local adapter
  logic, not through `mneme_service.*` imports.
- Adapter request/response examples or generated local models validate against
  the Core OpenAPI schema or equivalent REST/MCP contract fixture in CI.
- Adapter source code and tests pass an AST-based static check that forbids
  `import mneme_service` and `from mneme_service... import ...`.
- Adapter can install and run without a local Core repository checkout on
  `PYTHONPATH`.

### R-005: Public integration documentation

Core must document how integrations should use Mneme without putting
host-specific implementation into Core.

Acceptance:

- Core docs explain that official adapters live separately.
- Core docs explain that third-party projects may integrate directly through
  REST/MCP.
- Core docs link to `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md`.
- Core docs avoid implying that Codex adapter code is part of Core.

### R-006: Boundary enforcement tests

Core must include tests or checks that catch reintroduction of host-specific
implementation.

Acceptance:

- A Core test/check fails if `mneme_service/codex_*` or other known
  host-specific implementation modules reappear.
- A Core test/check fails if package discovery includes adapter packages.
- A Core test/check fails if the built wheel or sdist contains adapter package
  trees, Codex operating skills, or host-specific runtime modules.
- The check uses structural package/tree assertions plus a documented host-name
  denylist/allowlist, not only free-text grep.
- The check is generic enough to add future host names.
- The host boundary policy is checked in as
  `scripts/host_boundary_policy.json` or an equivalent documented file consumed
  by the boundary checks.
- `scripts/host_boundary_policy.json` uses this schema:
  `version: string`, `denylist: string[]`, `allowlist: string[]`, and
  `exemptions: {pattern: string, reason: string, scope: string}[]`.
- Changes to `scripts/host_boundary_policy.json` require pull-request review
  and a passing boundary-check run.
- The initial host denylist includes `codex`, `hermes`, `cursor`,
  `openai_agents`, `claude_code`, and `langgraph`.
- The allowlist explicitly permits only neutral Core references, public adapter
  repository pointers, and host names inside this boundary specification or an
  approved adapter index.
- Core CI runs the boundary and distribution checks on every pull request.

### R-007: Compatibility verification

The final result must be verified as a combined product, not only as isolated
repositories.

Acceptance:

- Core tests pass.
- Adapter tests pass.
- Core and adapter compile.
- Adapter tests run against a newly built Core artifact from the migration
  branch, not against a stale globally installed or editable Core package.
- Adapter verification uses a fresh virtual environment or equivalent isolated
  environment.
- Verification records the Core wheel/sdist filename, hash, contract version,
  Core commit, adapter commit, and `pip freeze` or equivalent installed package
  evidence.
- Cross-repository verification evidence is recorded as JSON with fields:
  `core_commit`, `core_contract_version`, `core_artifact_path`,
  `core_artifact_sha256`, `adapter_commit`, `adapter_supported_contract_range`,
  `verification_started_at`, `verification_commands`, `pip_freeze`,
  `runtime_database_ref`, `runtime_state_ref`, and `result`.
- `runtime_database_ref` and `runtime_state_ref` MUST be normalized labels or
  relative references such as `temp-db-1` and `temp-state-1`; they MUST NOT
  contain real absolute user or machine paths.
- Cross-repository CI MUST fail if `core_contract_version` is outside
  `adapter_supported_contract_range`.
- CI stores the cross-repository verification JSON as an artifact for at least
  90 days or until the next release, whichever is longer.
- Editable install smoke passes.
- GitHub install smoke passes or is explicitly deferred with a documented
  reason.
- Runtime smoke proves adapter can ingest events and read them back through
  Core memory tools.
- Runtime smoke uses a clean temporary database, clean temporary state
  directory, and temporary token so stale state cannot satisfy the test.

### R-008: Dependency extraction audit

Before Core-side Codex modules are deleted, the implementation must identify
whether they contain generic Core behavior that should survive in Core under a
host-neutral API or module.

Acceptance:

- Each current Core-side Codex module is audited before removal:
  `mneme_service/codex_hooks.py`, `mneme_service/codex_ingest.py`, and
  `mneme_service/codex_setup.py`.
- Any generic validation, REST payload construction, daemon health, status, or
  error-handling logic already used by Core is either already available through
  public Core REST/MCP contracts or is promoted to a neutral Core module/API
  before the Codex-specific module is removed.
- Logic used only by adapters must move to the adapter or be deferred to a
  future approved `mneme-client` or `mneme-schemas` package; it must not be
  promoted to Core merely because it is useful to an adapter.
- The default audit decision is adapter-first: a unit is promoted to Core only
  when the audit shows it is already used by Core or required to preserve an
  existing public Core REST/MCP contract.
- Promoted neutral Core logic receives generic Core tests before the original
  Codex-specific module is removed.
- The audit result is recorded in
  `docs/reviews/core_adapter_dependency_audit.md` with a Markdown table
  containing: source file, unit/function, decision (`move to adapter`,
  `promote to Core`, `delete as Codex-specific`, `defer`), rationale, target
  file/API, required tests, and evidence link.
- `docs/reviews/core_adapter_dependency_audit.md` is committed before Phase 4
  starts.
- Every `promote to Core` row links to the PR, commit, or reviewer packet entry
  that adds the required generic Core tests.

### R-009: Contract version compatibility

Core and adapter compatibility must be explicit enough that future Core changes
do not silently break adapters.

Acceptance:

- Core publishes or documents the relevant REST/MCP contract version used by
  this adapter.
- The Codex adapter declares its supported Core contract version or version
  range.
- A breaking REST/MCP contract change, as defined in Section 4.4, requires a
  documented MAJOR contract version change and adapter compatibility update.
- Cross-repository verification records the exact Core artifact and adapter
  revision tested together.
- Core CI verifies that `docs/MNEME_CONTRACT_VERSION`, OpenAPI metadata, and
  capabilities/health metadata report the same contract version when those
  surfaces exist.

## 8. Proposed Repository Layout

### 8.1 Core repository after refactor

Expected Core layout:

```text
mneme-universal-context-service/
  mneme_service/
    app.py
    benchmarks.py
    classifier.py
    cli.py
    config.py
    embeddings.py
    enrichment.py
    errors.py
    mcp_server.py
    reranker.py
    rest_client.py
    schemas.py
    security.py
    segments.py
    session_drift.py
    state.py
    storage.py
    tool_names.py
    utils.py
  docs/
    MNEME_STANDALONE_SPEC.md
    ...
  tests/
    test_contract.py
    test_mcp_contract.py
    test_openapi.py
    ...
```

Core should not contain:

```text
mneme_service/codex_*.py
adapters/codex/
.agents/skills/mneme-memory/
tests/test_codex_*.py
```

### 8.2 Codex adapter repository after refactor

Expected adapter ownership:

```text
mneme-codex-adapter/
  mneme_codex_adapter/
    hooks.py
    ingest.py
    setup.py
    cli.py
    service.py
    skills/mneme-memory/SKILL.md
  docs/
    Codex install and usage docs
  tests/
    test_codex_hooks.py
    test_codex_ingest.py
    test_setup.py
    ...
```

Exact names may differ, but ownership must be clear.

## 9. Dependency Direction

Allowed:

- Adapter depends on Core's public REST/MCP contract.
- Adapter calls Core through HTTP REST.
- Adapter launches or configures Core as an external daemon.
- Adapter exposes MCP tools from Core to Codex.
- Adapter includes Codex-specific CLI commands under `mneme-codex`.
- Adapter may depend on a future published `mneme-client` or `mneme-schemas`
  package only if that package is explicitly created as a public contract
  surface.

Not allowed:

- Core imports adapter modules.
- Core contains host-specific implementation modules.
- Core tests require adapter implementation files.
- Adapter imports `mneme_service.*` from the Core daemon package.
- Adapter depends on private Core Python functions for Codex-specific parsing or
  hook behavior.
- Host-specific behavior is added to Core because it is convenient for one
  adapter.

## 10. Migration Strategy

### Phase 1: Spec and boundary documentation

Update the approved Core documentation before implementation:

- `docs/MNEME_STANDALONE_SPEC.md`
- `docs/MNEME_HOST_ADAPTER_CONTRACT_V0.md`
- Core `README.md`
- optionally an ADR such as `docs/adr/ADR-001-core-adapter-boundary.md`

The documentation must explicitly choose Variant C.

### Phase 2: Adapter sync first

Update `mneme-codex-adapter` while the Core-side Codex copy still exists as a
temporary migration source:

- trace every dependency and public/private call used by Core-side
  `mneme_service.codex_*` modules;
- confirm that required Core behavior is reachable through REST/MCP, adapter
  local logic, or a promoted neutral Core API approved by Phase 3;
- copy or port the current working Codex behavior from Core-side
  `mneme_service.codex_*` into adapter-owned modules;
- update adapter tests for `COMPLETED` turn status;
- update context-preview request payload;
- update setup/status LaunchAgent expectations;
- make `mneme-memory` skill source-of-truth in the adapter;
- ensure adapter docs are complete enough for Codex users;
- make adapter tests pass against the current Core REST/MCP contract without
  importing `mneme_service.*`;
- add an adapter CI/static check that rejects `mneme_service.*` imports in
  source and tests.

This phase is complete only when the standalone adapter is green against a newly
built Core artifact from the migration branch.

Abort gate: if this phase cannot make the adapter green without private Core
imports, Core cleanup MUST NOT start. The migration must stop and produce a
gap report listing the missing public Core contract or approved neutral Core
API needed by the adapter.

### Phase 3: Dependency extraction audit

Audit Core-side Codex modules before deleting them:

- identify which units are purely Codex-specific and should move to the
  adapter;
- identify any generic logic hidden in Codex modules;
- promote generic logic to host-neutral Core modules or public REST/MCP
  contracts before removing the Codex-specific module;
- record the decision for each audited unit in the required audit table;
- add generic Core tests for every promoted unit before deleting the Codex
  source module.

Abort gate: if the audit finds generic behavior that cannot be safely promoted
within the non-goals of this refactor, Core cleanup MUST NOT remove the
corresponding Codex module until the project owner approves a separate spec
change or decides to move that behavior fully into the adapter.

### Phase 4: Core cleanup

Remove Codex-specific files from Core only after Phase 2 and Phase 3 pass:

- move remaining Codex docs/examples to adapter or replace them with short
  repository pointers;
- remove Codex-specific modules from `mneme_service`;
- remove Codex-specific tests from Core;
- add or update generic Core contract tests that preserve coverage for Core
  REST/MCP behavior previously exercised through deleted Codex-specific tests;
- record a Markdown 1:1 mapping table with one row for every deleted
  Codex-specific Core test, mapping it to its replacement generic Core REST/MCP
  test, or to an explicit rationale if no Core behavior was covered by that
  deleted test;
- update Core CLI so `mneme` exposes only Core commands;
- keep only generic REST/MCP behavior and generic contract tests.

### Phase 5: Boundary checks

Add checks to prevent recurrence:

- Core boundary test for host-specific modules and package trees.
- Core packaging test that the wheel/sdist does not include adapter code,
  Codex skills, or host runtime modules.
- Adapter test that skill install reads from adapter package data.
- Documentation check that Core points users to adapter docs instead of carrying
  host setup docs.
- Contract/version check that adapter declares the supported Core contract
  range.
- Adapter static import-boundary check for `mneme_service.*`.
- Automated cross-repository CI job that installs the newly built Core artifact
  into a clean adapter environment and runs adapter tests.
- The cross-repository CI job also runs adapter OpenAPI/REST-MCP contract drift
  checks and records the required verification JSON artifact.

### Phase 6: End-to-end verification

Run isolated and combined checks:

- Core unit/contract suite.
- Adapter unit/contract suite.
- Compile checks for both repositories.
- Adapter tests against the newly built Core wheel/sdist from this branch.
- Editable install smoke.
- GitHub install smoke.
- Runtime smoke with Core daemon plus Codex adapter ingestion/search.

Rollback gate: if any Phase 6 check fails after Core cleanup, the release
candidate is blocked. The implementation must either restore the last known
working Core/adapter boundary state or fix the failing phase before approval.

If rollback changes the Core contract version or Core artifact identity, the
adapter must be retested against the rolled-back artifact and the
cross-repository verification JSON must be regenerated. A rollback must not
leave adapter metadata claiming support for a Core contract version that was not
verified after the rollback.

## 11. Verification Commands

Exact paths may vary by machine. The implementation plan must replace
placeholders with real checkout paths.

### Core verification

```bash
cd /path/to/mneme-universal-context-service
env TMPDIR=/private/tmp .venv/bin/python -m pytest -q
env TMPDIR=/private/tmp .venv/bin/python -m compileall -q mneme_service tests
python -m build
python scripts/check_core_boundary.py
python scripts/check_distribution_boundary.py dist/*.whl dist/*.tar.gz
python scripts/check_contract_version.py
python scripts/check_publication_hygiene.py
```

The implementation may choose different script names, but it must provide
equivalent checked-in commands that:

- verify Core source/package boundaries structurally;
- verify wheel/sdist contents structurally;
- verify the contract version is consistent across
  `docs/MNEME_CONTRACT_VERSION`, OpenAPI metadata, and runtime metadata when
  runtime metadata exists.
- verify publication hygiene before release.

The boundary checks must use structural package/tree assertions and an explicit
host-name denylist/allowlist. Free-text search may be used as a supporting
signal, but it must not be the only boundary check. The checks must distinguish
forbidden runtime implementation from allowed generic documentation references
and short adapter repository pointers.

The publication hygiene check must flag likely secrets, bearer tokens, API keys,
private database URLs, `.env` values, user-home absolute paths such as
`/Users/<name>/...` and `C:\Users\<name>\...`, and machine-specific local config
paths. It may allow generic placeholders such as `/path/to/...`, `<tmpdir>`, or
neutral temporary directory examples that do not identify a real user or
machine.

`check_publication_hygiene.py` scans Core source, docs, tests, wheel contents,
and sdist contents. It exits with code `0` only when no unapproved finding is
present, and exits non-zero on any likely secret or machine-specific path. The
minimum detectors include token/key prefixes such as `ghp_`, `xoxb-`, and
`sk-`, bearer-token literals, private database URLs such as `postgres://...`
and `mongodb+srv://...`, `.env` value patterns, `/Users/[^/]+/` paths,
`C:\\Users\\[^\\]+\\` paths, and equivalent platform home-directory paths. Any
false-positive exception must be recorded in
`scripts/publication_hygiene_allowlist.json` with `pattern`, `scope`, and
`reason`.

### Adapter verification

```bash
cd /path/to/mneme-codex-adapter
python -m venv /private/tmp/mneme-adapter-verify-venv
/private/tmp/mneme-adapter-verify-venv/bin/python -m pip install --upgrade pip
/private/tmp/mneme-adapter-verify-venv/bin/python -m pip install --force-reinstall /path/to/mneme-universal-context-service/dist/*.whl
/private/tmp/mneme-adapter-verify-venv/bin/python -m pip install -e .
/private/tmp/mneme-adapter-verify-venv/bin/python scripts/check_no_core_internal_imports.py
/private/tmp/mneme-adapter-verify-venv/bin/python scripts/check_core_contract_drift.py --openapi /path/to/mneme-universal-context-service/openapi.json
env TMPDIR=/private/tmp /private/tmp/mneme-adapter-verify-venv/bin/python -m compileall -q mneme_codex_adapter tests
env TMPDIR=/private/tmp /private/tmp/mneme-adapter-verify-venv/bin/python -m pytest -q
/private/tmp/mneme-adapter-verify-venv/bin/python -m pip freeze
```

The adapter verification environment must be isolated enough to prove that
tests are running against the newly built Core artifact, not an older editable
checkout or globally installed package. The verification log must record the
Core artifact filename, hash, Core commit, Core contract version, adapter
commit, and installed package list.

The adapter import-boundary check must parse Python imports with `ast` or an
equivalent structural parser. A supporting text search is acceptable, but it is
not sufficient as the only check.

The adapter contract-drift check must validate adapter request/response samples
or generated local models against the Core OpenAPI schema or equivalent REST/MCP
contract fixture. It must fail if adapter-local models require fields, types,
or enum values that are not supported by the Core contract version under test.

### Combined runtime smoke

```bash
# Start Core daemon with a temporary database and token.
# Run Codex adapter ingest against it.
# Replay ingest and confirm duplicates.
# Run context_search and fetch_event through Core memory tools.
# Run mneme-codex setup --dry-run and confirm no token leakage.
```

The runtime smoke must create a new temporary database and state directory for
each run, and must fail if it can only pass by reading data from a previous run.

## 12. Success Criteria

The refactor is complete only when all criteria are met:

| ID | Criterion | Required evidence |
|---|---|---|
| SC-001 | Core package is host-neutral. | Core package/tree check shows no host-specific implementation modules. |
| SC-002 | Codex adapter owns Codex behavior. | Adapter repo contains hooks, ingest, setup/status/service, docs, and skill. |
| SC-003 | Core tests pass without Codex-specific tests. | Core pytest result recorded. |
| SC-004 | Generic Core contract coverage replaces deleted Codex-specific test coverage. | Mapping from deleted Codex tests to generic REST/MCP tests recorded. |
| SC-005 | Adapter tests pass against updated Core. | Adapter pytest result recorded from clean env. |
| SC-006 | Combined runtime smoke passes. | Health, capabilities, ingest, replay, search, fetch evidence recorded from clean temp DB/state. |
| SC-007 | Docs explain direct REST/MCP integration path. | Core docs reviewed. |
| SC-008 | Boundary is protected against recurrence. | Boundary test/check exists and runs in CI. |
| SC-009 | No secrets or machine-specific paths are published. | Secret/path scan recorded with tool or reviewed command. |
| SC-010 | Core distribution artifacts are host-neutral. | Wheel/sdist boundary check result recorded. |
| SC-011 | Adapter is tested against the newly built Core artifact. | Adapter verification records Core artifact path/hash/version and adapter revision. |
| SC-012 | Core/adapter contract compatibility is explicit. | `docs/MNEME_CONTRACT_VERSION` and adapter supported range are documented and checked. |
| SC-013 | Dependency extraction audit is complete. | Each Core-side Codex module has a recorded move/promote/delete/defer decision. |
| SC-014 | Adapter source has no private Core imports. | AST import-boundary check result recorded. |
| SC-015 | Abort/rollback gates are respected. | Reviewer packet records any triggered gate and its resolution. |

## 13. Reviewer Checklist

The following points are no longer open design questions; they are the review
checklist for approving this document as the next implementation spec.

1. Variant C is clearly stated: Mneme Core is host-neutral memory service;
   host-specific behavior lives in adapters or third-party integrations.
2. No Codex-specific implementation, skill, setup docs, or runtime tests remain
   in Core except short repository pointers.
3. The dependency extraction audit prevents accidental deletion of generic Core
   behavior and prevents adapter-only helpers from being promoted into Core.
4. The `mneme_service.*` import ban is both normative and mechanically enforced
   in adapter CI.
5. Artifact-based verification is isolated and records enough evidence to avoid
   stale install false positives.
6. Contract version compatibility is machine-readable and has SemVer-style
   breaking-change rules.
7. The acceptance criteria are specific enough to become `.planning/spec.md`
   after project-owner approval.

## 14. Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Codex behavior breaks during move. | Users lose working Codex integration. | Move behavior into adapter first, run adapter tests and runtime smoke before removing Core copy. |
| Core accidentally keeps hidden Codex dependency. | Boundary remains unclear. | Add package/tree boundary checks. |
| Adapter imports private Core internals. | Future Core changes break adapter unexpectedly. | Forbid `mneme_service.*` imports; use REST/MCP or a future approved public SDK/schema package. |
| Core tests become too narrow after removing Codex tests. | Core regressions missed. | Keep generic REST/MCP contract tests that cover the same Core behavior without Codex fixtures. |
| Documentation becomes split and confusing. | Users do not know what to install. | Core README explains Core; adapter README explains Codex; Core links to adapter. |
| False positive verification. | Release appears ready while adapter fails. | Require both repo test suites and combined runtime smoke. |
| Adapter tests accidentally use stale Core install. | Verification passes against the wrong artifact. | Force reinstall the newly built Core artifact in the adapter test environment and record artifact identity. |
| Generic Core logic is deleted with Codex modules. | Core loses reusable behavior or public contracts become weaker. | Run dependency extraction audit before Core cleanup and promote generic logic first. |
| Contract compatibility remains implicit. | Future Core changes silently break adapters. | Record Core contract version and adapter supported version range. |
| Boundary audit expands into new feature work. | Refactor grows beyond approved scope. | Promote only logic already used by Core; move adapter-only logic to adapter or defer to future approved SDK/schema spec. |
| Runtime smoke passes from stale state. | Verification misses a broken ingest/search path. | Use clean temporary database, state directory, and token for every smoke run. |
| CI checks are added but not wired. | Boundary regressions return later. | Require boundary, distribution, import, contract-drift, and contract-version checks in CI. |

## 15. Out-of-Scope Changes

Do not include these in this refactor unless a separate approved spec change is
created:

- new host adapters besides Codex;
- new retrieval algorithms;
- new provider integrations;
- database schema redesign unrelated to boundary cleanup;
- REST/MCP breaking changes;
- new Python SDK/schema package;
- global Codex config changes on user machines;
- live Hermes changes;
- direct edits to live `hermes-mneme`.

## 16. Proposed Planning Scope After Approval

If this document is approved, create a dedicated spec-driven planning scope:

```text
.planning/spec.md
.planning/roadmap.md
.planning/findings.md
.planning/progress.md
.planning/work/11-core-adapter-boundary-and-codex-adapter-sync/plan.md
```

The first implementation phase should not start until the Planning Gate is
cleared.

Recommended phases:

1. Boundary spec amendment and ADR.
2. Adapter repository sync for Codex behavior.
3. Dependency extraction audit and generic Core promotion.
4. Core cleanup and package boundary enforcement.
5. Contract version and CI enforcement.
6. Cross-repository install and runtime smoke verification.
7. Publication and reviewer packet update.

## 17. Approval Gate

This document is not approved until the reviewer and project owner agree that:

- the Core/Adapter boundary is correctly stated;
- the migration plan preserves working Codex integration;
- the verification plan covers Core, adapter, and combined runtime behavior;
- the document is suitable to become the source `.planning/spec.md` for
  spec-driven planning.

Implementation must not begin from this document until the corresponding
spec-driven Planning Gate is cleared by explicit project-owner approval.
