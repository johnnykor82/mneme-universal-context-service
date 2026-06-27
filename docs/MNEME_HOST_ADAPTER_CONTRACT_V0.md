# Mneme Host Adapter Contract v0

Status: Approved planning contract for Phase 11

## Purpose

Mneme Core is a host-neutral memory service. Host-specific behavior belongs in
adapter packages or third-party host integrations that call Mneme through public
REST/MCP contracts.

This document defines the public integration boundary for adapters. It is not a
Codex setup guide and does not make Codex behavior part of Core.

## Core Responsibilities

Mneme Core owns:

- REST API implementation and OpenAPI schema.
- MCP tools that expose Core memory behavior.
- Storage, retrieval, context preparation, traces, costs, metrics,
  authentication, redaction, blobs, migrations, and maintenance.
- Machine-readable contract version metadata.
- Generic adapter contract documentation and neutral conformance tests.

Mneme Core does not own:

- host hook handlers;
- host transcript parsers;
- host setup, doctor, service, or skill-install commands;
- host-specific docs, payload examples, or runtime tests beyond short adapter
  repository pointers.

## Adapter Responsibilities

A host adapter owns translation between its host runtime and Mneme Core:

- validating host hook or transcript inputs;
- mapping host lifecycle events to Mneme sessions, events, turns, and context
  requests;
- packaging host-specific skills, docs, setup, status, and service helpers;
- declaring its supported Mneme Core contract version range;
- proving compatibility through tests against Core's public REST/MCP contract.

Adapters must not import `mneme_service.*` internals from the Core daemon
package. If future shared Python types are needed, they must be introduced as a
separate public package with its own approved contract.

## Contract Version

The canonical Core contract version is stored in
`docs/MNEME_CONTRACT_VERSION`.

Core exposes the same value through:

- OpenAPI `info.version`;
- `/v1/health.mneme_contract_version`;
- `/v1/capabilities.mneme_contract_version`.

Adapters must reject or warn on Core contract versions outside their declared
supported range.

## Integration Path

Adapters integrate through public REST/MCP behavior:

1. Discover health and capabilities.
2. Start or resolve sessions.
3. Ingest events and complete turns when the host lifecycle supports it.
4. Use `context_search`, `fetch_event`, `expand_context`, or
   `/v1/context/prepare` according to the adapter's integration depth.
5. Record audit-safe traces and errors without leaking bearer tokens or host
   secrets.

The public contract is the REST/MCP surface and OpenAPI schema, not private
Core Python functions.
