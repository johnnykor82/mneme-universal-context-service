from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .classifier import INTENT_NEW_TASK, INTENT_SWITCH, classify_intent, extract_entities
from .config import Settings
from .embeddings import EmbeddingIndex, EmbeddingProvider, OpenAICompatibleEmbeddingProvider, embedding_record_from_event
from .enrichment import (
    EnrichmentProvider,
    EnrichmentResult,
    HttpLLMEnrichmentProvider,
    apply_enrichment_updates,
)
from .errors import (
    MnemeError,
    bad_request,
    conflict,
    failed_precondition,
    not_found,
    payload_too_large,
    unauthenticated,
    validation_error,
)
from .reranker import HttpRerankerProvider, RerankerProvider, RerankResult
from .security import bearer_is_valid, redact
from .segments import update_segment_for_event
from .session_drift import LINEAGE_KEYS, classify_session_start, first_metadata_string
from .state import apply_event_to_state
from .storage import Store
from .tool_names import TOOL_NAMES
from .utils import canonical_json, new_id, sha256_text, text_from_content, token_estimate

SUPPORTED_SCHEMAS = {
    "session": ["mneme.session.v0"],
    "event_batch": ["mneme.event_batch.v0"],
    "event": ["mneme.event.v0"],
    "turn": ["mneme.turn.v0"],
    "context_prepare_request": ["mneme.context_prepare_request.v0"],
    "context_prepare_response": ["mneme.context_prepare_response.v0"],
    "message": ["mneme.message.v0"],
    "trace": ["mneme.trace.v0"],
    "cost_report": ["mneme.cost_report.v0"],
    "session_state": ["mneme.session_state.v0"],
    "session_lineage": ["mneme.session_lineage.v0"],
    "graph_edge": ["mneme.graph_edge.v0"],
    "execution_state": ["mneme.execution_state.v0"],
    "state_history_entry": ["mneme.state_history_entry.v0"],
}

ROUTER_MODE_WEIGHTS = {
    "general": {"similarity": 0.6, "recency": 0.2, "dependency": 0.1, "type": 0.1},
    "reasoning": {"similarity": 0.7, "recency": 0.15, "dependency": 0.05, "type": 0.1},
    "factual": {"similarity": 0.55, "recency": 0.3, "dependency": 0.05, "type": 0.1},
    "debugging": {"similarity": 0.35, "recency": 0.35, "dependency": 0.2, "type": 0.1},
    "clarification": {"similarity": 0.4, "recency": 0.35, "dependency": 0.15, "type": 0.1},
}


def create_app(
    settings: Settings | None = None,
    *,
    embedding_provider: EmbeddingProvider | None = None,
    reranker_provider: RerankerProvider | None = None,
    enrichment_provider: EnrichmentProvider | None = None,
) -> FastAPI:
    settings = settings or Settings()
    if settings.require_embeddings and not settings.embeddings.available:
        raise RuntimeError(
            "Embeddings are required but no enabled, configured embedding provider is available."
        )
    store = Store(settings.db_path)
    embedding_index: EmbeddingIndex | None = None
    if settings.embeddings.available:
        provider = embedding_provider or OpenAICompatibleEmbeddingProvider(settings.embeddings)
        embedding_index = EmbeddingIndex(
            store,
            provider,
            model_id=settings.embeddings.model or "",
            batch_size=settings.embeddings.batch_size,
            centroid_window=settings.centroid_window,
        )
        if settings.reindex_on_model_change:
            reindex_missing_embeddings(store, embedding_index, settings)
    reranker: RerankerProvider | None = None
    if settings.reranker.available:
        reranker = reranker_provider or HttpRerankerProvider(settings.reranker)
    enricher: EnrichmentProvider | None = None
    if settings.llm_enrichment.available:
        enricher = enrichment_provider or HttpLLMEnrichmentProvider(settings.llm_enrichment)
    app = FastAPI(title="Mneme Context Service", version="0.1.0")
    app.state.settings = settings
    app.state.store = store
    app.state.embedding_index = embedding_index
    app.state.reranker = reranker
    app.state.enrichment_provider = enricher

    @app.exception_handler(MnemeError)
    async def mneme_error_handler(_: Request, exc: MnemeError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=redact(exc.detail))

    def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
        if not bearer_is_valid(authorization, settings.auth_token, settings.insecure_dev):
            raise unauthenticated()

    def require_session(session_id: str) -> None:
        if not store.has_session(session_id):
            raise not_found("Session not found.", **session_not_found_details(store, session_id))

    @app.get("/v1/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "OK",
            "service": "mneme-context-service",
            "api_version": "v1",
            "schema_versions": ["mneme.session.v0", "mneme.event.v0", "mneme.trace.v0"],
        }

    @app.get("/v1/capabilities")
    async def capabilities( _auth: None = Depends(require_auth)) -> dict[str, Any]:
        return {
            "api_version": "v1",
            "supported_cost_modes": ["MINIMAL", "STANDARD", "QUALITY"],
            "default_cost_mode": "STANDARD",
            "supports_embeddings": settings.embeddings.available,
            "requires_embeddings": settings.require_embeddings,
            "supports_reranking": settings.reranker.available,
            "supports_llm_enrichment": settings.llm_enrichment.available,
            "supports_context_prepare": True,
            "supports_mcp_tools": True,
            "mcp_tools": list(TOOL_NAMES),
            "providers": {
                "embeddings": settings.embeddings.summary(),
                "reranker": settings.reranker.summary(),
                "llm_enrichment": settings.llm_enrichment.summary(),
            },
            "auth_schemes": ["BEARER_TOKEN"],
            "max_batch_events": settings.max_batch_events,
            "max_event_content_bytes": settings.max_event_content_bytes,
            "max_tool_result_events": settings.max_tool_result_events,
            "supported_schema_versions": SUPPORTED_SCHEMAS,
        }

    @app.post("/v1/readiness/session")
    async def session_readiness(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        require_evidence = bool(payload.get("require_evidence", True))
        top_k = parse_int(payload, "top_k", default=1, minimum=1, maximum=10)
        query = optional_payload_str(payload, "query") or ""
        safe_query = redact(query)
        filters = search_filters(payload)
        scope_payload = dict(payload)
        scope_payload["scope"] = payload.get("scope") or "SESSION"
        scope = parse_search_scope(scope_payload)

        if query:
            results, retrieval, warnings = hybrid_context_search(
                store,
                embedding_index,
                session_id=session_id,
                query=safe_query,
                top_k=top_k,
                filters=filters,
                scope=scope,
                reranker=reranker,
                reranker_top_k=settings.reranker_top_k,
            )
            evidence_ids = [item["event_id"] for item in results]
            check = "context_search"
        else:
            events = store.recent_events(session_id, top_k)
            results = summarize_events(events)
            retrieval = {
                "candidate_count": len(results),
                "selected_count": len(results),
                "strategies": ["RECENT"],
                "degraded": False,
                "fallbacks": [],
            }
            warnings = []
            evidence_ids = [item["event_id"] for item in results]
            check = "recall_recent"

        if require_evidence and not evidence_ids:
            raise failed_precondition(
                "Session readiness check found no evidence.",
                session_id=session_id,
                reason="NO_EVIDENCE",
                query=safe_query,
                required_check=check,
                evidence_count=0,
            )

        trace_id = audit_memory_tool(
            store,
            session_id,
            "session_readiness",
            evidence_ids,
            retrieval=retrieval,
            warnings=warnings,
        )
        return tool_response(
            {
                "ready": True,
                "session_id": session_id,
                "required_check": check,
                "evidence_count": len(evidence_ids),
                "evidence_event_ids": evidence_ids,
                "checks": {
                    "authenticated": True,
                    "session_found": True,
                    "evidence_found": bool(evidence_ids),
                },
            },
            trace_id=trace_id,
            warnings=warnings,
        )

    @app.post("/v1/sessions/start")
    async def start_session(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        require_schema(payload, "session")
        if "session_id" not in payload or "agent_id" not in payload or "runtime" not in payload:
            raise validation_error("Session requires session_id, agent_id, and runtime.")
        clean = redact(payload)
        created = store.put_session(clean)
        metadata = clean.get("metadata") if isinstance(clean.get("metadata"), dict) else {}
        lineage_session_id = first_metadata_string(metadata, LINEAGE_KEYS)
        if lineage_session_id:
            store.put_session_lineage(lineage_session_id, clean["session_id"])
        counts = store.session_counts(clean["session_id"])
        lineage_counts = store.lineage_counts(clean["session_id"])
        session_state = classify_session_start(
            clean,
            created=created,
            prior_event_count=counts["event_count"],
            prior_turn_count=counts["turn_count"],
            lineage_event_count=lineage_counts["event_count"],
            lineage_turn_count=lineage_counts["turn_count"],
        )
        store.set_context_fill_required(clean["session_id"], bool(session_state["requires_context_fill"]))
        return {
            "session_id": clean["session_id"],
            "created": created,
            "status": "ACTIVE",
            "accepted_schema_version": "mneme.session.v0",
            "session_state": session_state,
        }

    @app.post("/v1/events")
    async def ingest_events(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        require_schema(payload, "event_batch")
        session_id = payload.get("session_id")
        if not isinstance(session_id, str):
            raise validation_error("Event batch requires session_id.")
        require_session(session_id)
        events = payload.get("events")
        if not isinstance(events, list):
            raise validation_error("Event batch requires events list.")
        if len(events) > settings.max_batch_events:
            raise payload_too_large("Event batch exceeds max_batch_events.", max_batch_events=settings.max_batch_events)

        accepted = 0
        duplicates = 0
        rejected: list[dict[str, Any]] = []
        stored_ids: list[str] = []
        embedding_events: list[dict[str, Any]] = []
        for raw_event in events:
            require_schema(raw_event, "event")
            if raw_event.get("session_id") != session_id:
                rejected.append({"event_id": raw_event.get("event_id"), "code": "VALIDATION_ERROR", "message": "Event session_id does not match batch."})
                continue
            normalized = normalize_event(raw_event)
            content = normalized.get("content", {})
            if content.get("format") != "BYTES_REF":
                size = len(text_from_content(content).encode("utf-8"))
                if size > settings.max_event_content_bytes:
                    raise payload_too_large("Inline event content exceeds max_event_content_bytes.", max_event_content_bytes=settings.max_event_content_bytes)
            clean = redact(normalized)
            clean["ingestion"] = {
                **clean.get("ingestion", {}),
                "status": "STORED",
                "embedding_status": "PENDING" if embedding_index else "NOT_CONFIGURED",
            }
            text = text_from_content(clean.get("content", {}))
            immutable_hash = event_immutable_hash(clean)
            existing_hash = store.get_event_hash(clean["event_id"])
            if existing_hash is not None:
                if existing_hash != immutable_hash:
                    raise conflict("Event id reused with incompatible immutable fields.", event_id=clean["event_id"])
                duplicates += 1
                continue
            previous_state = store.execution_state_or_default(session_id)
            store.put_event(clean, immutable_hash, text, is_memory_read=clean["type"] == "MEMORY_READ")
            store.put_event_graph_edges(clean)
            state = apply_event_to_state(previous_state, clean)
            previous_segment = store.latest_active_segment(session_id) if clean["type"] == "USER_MESSAGE" else None
            embedding_drift = 0.0
            if embedding_index and previous_segment:
                embedding_drift = embedding_index.embedding_drift_against_segment(
                    text,
                    session_id=session_id,
                    segment_id=previous_segment["segment_id"],
                )
            classification = classify_intent(
                text,
                embedding_drift=embedding_drift,
                active_entities=previous_state.get("active_entities") or [],
                last_assistant_entities=last_assistant_entities(store, session_id),
            )
            segment = update_segment_for_event(store, clean, classification)
            if segment:
                state["segment_id"] = segment["segment_id"]
            if should_run_enrichment(settings, clean, state, previous_segment, segment):
                state = apply_optional_enrichment(store, enricher, clean, state)
            store.commit_execution_state(session_id, state)
            maybe_trace_segment_drift(store, clean, classification, previous_segment, segment)
            accepted += 1
            stored_ids.append(clean["event_id"])
            if embedding_index:
                event_for_embedding = dict(clean)
                if segment:
                    metadata = dict(event_for_embedding.get("metadata", {}))
                    metadata["mneme_segment_id"] = segment["segment_id"]
                    event_for_embedding["metadata"] = metadata
                embedding_events.append(event_for_embedding)

        if embedding_index and embedding_events:
            records = [
                record
                for record in (
                    embedding_record_from_event(
                        event,
                        tool_output_compress_threshold_tokens=settings.tool_output_compress_threshold_tokens,
                        tool_output_summary_tokens=settings.tool_output_summary_tokens,
                    )
                    for event in embedding_events
                )
                if record is not None
            ]
            if records:
                stats = embedding_index.index_events(records)
                store.record_embedding_metrics(
                    session_id,
                    embedding_batches=stats.embedding_batches,
                    embedding_items=stats.embedding_items,
                    embedding_input_chars=stats.embedding_input_chars,
                    embedding_failures=stats.embedding_failures,
                )

        return {"session_id": session_id, "accepted": accepted, "duplicates": duplicates, "rejected": rejected, "stored_event_ids": stored_ids}

    @app.post("/v1/turns/complete")
    async def complete_turn(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        require_schema(payload, "turn")
        session_id = require_payload_str(payload, "session_id")
        turn_id = require_payload_str(payload, "turn_id")
        require_session(session_id)
        store.put_turn(session_id, turn_id, redact(payload))
        return {"session_id": session_id, "turn_id": turn_id, "status": "RECORDED", "segment_ids": [f"segment-{session_id}"]}

    @app.post("/v1/context/prepare")
    async def prepare_context(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        start = time.perf_counter()
        require_schema(payload, "context_prepare_request")
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        validate_prepare(payload)
        clean_payload = redact(payload)
        policy = clean_payload.get("policy", {})
        request_id = clean_payload.get("request_id") or new_id("request")
        prepare_id = clean_payload.get("prepare_id") or request_id
        trace_id = new_id("trace")
        if policy.get("mode") == "OFF":
            trace = prepare_trace(trace_id, clean_payload, [], start)
            store.put_trace(trace)
            return {"schema_version": "mneme.context_prepare_response.v0", "request_id": request_id, "prepare_id": prepare_id, "session_id": session_id, "turn_id": clean_payload.get("turn_id"), "changed": False, "messages": [], "trace_id": trace_id, "warnings": ["POLICY_OFF"]}

        resume_fill_required = store.context_fill_required(session_id)
        retrieval_policy = policy.get("retrieval", {})
        query = retrieval_policy.get("query") or derive_query(clean_payload["request_messages"])
        retrieval_top_k = int(retrieval_policy.get("top_k", 24))
        retrieval_scope = parse_search_scope({"scope": retrieval_policy.get("scope") or policy.get("scope") or "LINEAGE"})
        search_session_ids = search_session_ids_for_scope(store, session_id, retrieval_scope)
        results = store.search_events_for_sessions(search_session_ids, query, retrieval_top_k)
        candidate_ids = [item["event_id"] for item in results[:8]]
        candidate_events = [store.get_event_for_sessions(search_session_ids, event_id) for event_id in candidate_ids]
        candidate_events = [event for event in candidate_events if event]
        if not policy.get("include_retrieved_events", True):
            candidate_events = []
        selection_reason = "KEYWORD_RECENCY"
        if resume_fill_required and not candidate_events:
            candidate_events = store.recent_events(session_id, 8)
            selection_reason = "RESUME_CONTEXT_FILL"
        retrieved_ratio = float(policy.get("budget_split", {}).get("retrieved_context_ratio", settings.retrieved_budget_ratio))
        selected_events, dropped_event_refs, retrieved_tokens = pack_retrieved_events(
            candidate_events,
            int(int(clean_payload["budget_tokens"]) * retrieved_ratio),
        )
        selected_ids = [event["event_id"] for event in selected_events]

        state_block = ""
        execution_state_tokens = 0
        state_compression = "NONE"
        if policy.get("include_execution_state"):
            state_ratio = float(policy.get("budget_split", {}).get("execution_state_ratio", settings.state_budget_ratio))
            state_budget_tokens = int(clean_payload["budget_tokens"] * state_ratio)
            candidate_state_block, candidate_tokens, compression = execution_state_context_block(
                store.execution_state_or_default(session_id),
                budget_tokens=state_budget_tokens,
            )
            if candidate_state_block:
                if candidate_tokens <= state_budget_tokens:
                    state_block = candidate_state_block
                    execution_state_tokens = candidate_tokens
                    state_compression = compression

        request_tokens = approximate_messages_tokens(clean_payload["request_messages"])
        budget_tokens = int(clean_payload["budget_tokens"])
        messages = list(clean_payload["request_messages"])
        protected_tail_tokens = 0
        tail_changed = False
        if policy.get("include_recent_tail") and request_tokens > budget_tokens:
            tail_ratio = float(policy.get("budget_split", {}).get("recent_tail_ratio", settings.protected_tail_ratio))
            messages, protected_tail_tokens = protected_tail_messages(
                clean_payload["request_messages"],
                int(budget_tokens * tail_ratio),
                preserve_system_prompt=bool(policy.get("preserve_system_prompt", True)),
            )
            tail_changed = messages != clean_payload["request_messages"]

        headroom_ratio = float(policy.get("budget_split", {}).get("headroom_ratio", policy.get("headroom_ratio", 0.1)))
        headroom_tokens = int(budget_tokens * headroom_ratio)
        memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
            store,
            settings,
            session_id,
            include_helpers=bool(state_block or selected_events),
        )
        context_blocks = prepare_context_blocks(
            memory_hint_block,
            goal_trail_block,
            state_block,
            checkpoint_block,
            selected_events,
        )
        if projected_prepare_tokens(messages, context_blocks) + headroom_tokens > budget_tokens and (
            memory_hint_block or goal_trail_block or checkpoint_block
        ):
            memory_hint_block = ""
            goal_trail_block = ""
            checkpoint_block = ""
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
        if projected_prepare_tokens(messages, context_blocks) + headroom_tokens > budget_tokens and selected_events:
            dropped_event_refs.extend(
                {"event_id": event["event_id"], "reason": "CONTEXT_COLLISION_BUDGET_EXCEEDED"}
                for event in selected_events
            )
            selected_events = []
            selected_ids = []
            retrieved_tokens = 0
            memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
                store,
                settings,
                session_id,
                include_helpers=bool(state_block),
            )
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
        if projected_prepare_tokens(messages, context_blocks) + headroom_tokens > budget_tokens and state_block:
            state_block = ""
            execution_state_tokens = 0
            state_compression = "DROPPED_FOR_BUDGET"
            memory_hint_block, goal_trail_block, checkpoint_block = prepare_prompt_helper_blocks(
                store,
                settings,
                session_id,
                include_helpers=bool(selected_events),
            )
            context_blocks = prepare_context_blocks(
                memory_hint_block,
                goal_trail_block,
                state_block,
                checkpoint_block,
                selected_events,
            )
        if policy.get("include_recent_tail") and projected_prepare_tokens(messages, context_blocks) + headroom_tokens > budget_tokens:
            preserve_system = bool(policy.get("preserve_system_prompt", True))
            available_for_messages = max(0, budget_tokens - headroom_tokens - context_blocks_tokens(context_blocks))
            system_tokens = (
                token_estimate(str(clean_payload["request_messages"][0].get("content", "")))
                if preserve_system and clean_payload["request_messages"] and clean_payload["request_messages"][0].get("role") == "SYSTEM"
                else 0
            )
            messages, protected_tail_tokens = protected_tail_messages(
                clean_payload["request_messages"],
                max(0, available_for_messages - system_tokens),
                preserve_system_prompt=preserve_system,
            )
            tail_changed = messages != clean_payload["request_messages"]
        degraded = projected_prepare_tokens(messages, context_blocks) + headroom_tokens > budget_tokens

        trace = prepare_trace(
            trace_id,
            clean_payload,
            selected_events,
            start,
            selection_reason=selection_reason,
            execution_state_tokens=execution_state_tokens,
            protected_tail_tokens=protected_tail_tokens,
            dropped_event_refs=dropped_event_refs,
            retrieved_tokens=retrieved_tokens,
            degraded=degraded,
            context_blocks=context_blocks,
            memory_hint_tokens=token_estimate(memory_hint_block),
            goal_trail_tokens=token_estimate(goal_trail_block),
            checkpoint_tokens=token_estimate(checkpoint_block),
            cross_session_event_ids=cross_session_event_ids(session_id, selected_events),
            state_compression=state_compression,
        )
        store.put_trace(trace)
        store.add_audit(session_id, "MEMORY_READ", "context_prepare", selected_ids, trace_id=trace_id)

        if not selected_events and not state_block and not tail_changed and request_tokens < budget_tokens:
            return {"schema_version": "mneme.context_prepare_response.v0", "request_id": request_id, "prepare_id": prepare_id, "session_id": session_id, "turn_id": clean_payload.get("turn_id"), "changed": False, "messages": [], "trace_id": trace_id, "warnings": ["REQUEST_UNDER_BUDGET"]}
        if resume_fill_required and selected_events:
            store.mark_context_fill_fulfilled(session_id)
        if not context_blocks and not tail_changed:
            return {"schema_version": "mneme.context_prepare_response.v0", "request_id": request_id, "prepare_id": prepare_id, "session_id": session_id, "turn_id": clean_payload.get("turn_id"), "changed": False, "messages": [], "trace_id": trace_id, "warnings": ["NO_CONTEXT_AVAILABLE"]}
        context_message_role = None
        if context_blocks:
            memory_message = {
                "schema_version": "mneme.message.v0",
                "role": "ASSISTANT",
                "content": "\n\n".join(context_blocks).strip(),
                "metadata": {"mneme_generated": True, "trace_id": trace_id},
            }
            context_message_role = memory_message["role"]
            insert_at = 1 if messages and messages[0].get("role") == "SYSTEM" else 0
            messages.insert(insert_at, memory_message)
        return {
            "schema_version": "mneme.context_prepare_response.v0",
            "request_id": request_id,
            "prepare_id": prepare_id,
            "session_id": session_id,
            "turn_id": clean_payload.get("turn_id"),
            "changed": True,
            "messages": messages,
            "trace_id": trace_id,
            "trace": {
                "budget_tokens": clean_payload["budget_tokens"],
                "input_request_tokens": request_tokens,
                "system_prompt_tokens": token_estimate(messages[0].get("content", "")) if messages else 0,
                "execution_state_tokens": execution_state_tokens,
                "protected_tail_tokens": protected_tail_tokens,
                "retrieved_tokens": retrieved_tokens,
                "headroom_tokens": headroom_tokens,
                "candidate_count": len(results),
                "context_blocks": len(context_blocks),
                "memory_hint_tokens": token_estimate(memory_hint_block),
                "goal_trail_tokens": token_estimate(goal_trail_block),
                "checkpoint_tokens": token_estimate(checkpoint_block),
                "state_compression": state_compression,
                "selected_event_ids": selected_ids,
                "selected_event_refs": [{"event_id": event_id, "reason": selection_reason} for event_id in selected_ids],
                "cross_session_event_ids": cross_session_event_ids(session_id, selected_events),
                "dropped_event_refs": dropped_event_refs,
                "degraded": degraded,
            },
            "adapter_metadata": {
                "can_insert_automatically": False,
                "insertion_mode": "request-only context block; host hook required for automatic insertion",
                "context_message_role": context_message_role,
                "trace_id": trace_id,
            },
            "warnings": [],
            "cost_estimate": {"embedding_calls": 0, "reranker_calls": 0, "enrichment_calls": 0},
        }

    @app.post("/v1/tools/resolve_session")
    async def resolve_session(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        limit = parse_int(payload, "limit", default=10, minimum=1, maximum=50)
        session_id = optional_payload_str(payload, "session_id")
        project_path = optional_payload_str(payload, "project_path")
        thread_id = optional_payload_str(payload, "thread_id")
        slug = optional_payload_str(payload, "slug")
        query = optional_payload_str(payload, "query")
        if not any([session_id, project_path, thread_id, slug, query]):
            raise validation_error(
                "resolve_session requires session_id, project_path, thread_id, slug, or query.",
                field="session_id",
            )

        exact = store.get_session_summary(session_id) if session_id and store.has_session(session_id) else None
        if exact:
            return tool_response(
                {
                    "resolved_session_id": exact["session_id"],
                    "resolution": "EXACT_SESSION_ID",
                    "matches": [exact],
                }
            )

        search_query = query or session_id
        matches = store.list_sessions(
            query=search_query,
            project_path=project_path,
            thread_id=thread_id,
            slug=slug,
            limit=limit,
        )
        resolved_session_id = matches[0]["session_id"] if len(matches) == 1 else None
        if resolved_session_id:
            resolution = "SINGLE_MATCH"
            warnings: list[dict[str, Any]] = []
        elif matches:
            resolution = "AMBIGUOUS"
            warnings = [{"code": "AMBIGUOUS_SESSION", "message": "Multiple sessions matched; pass a more specific session_id, thread_id, or project_path."}]
        else:
            resolution = "NOT_FOUND"
            warnings = [{"code": "SESSION_NOT_FOUND", "message": "No session matched; check that REST/importer/hooks write to the same Mneme database as this MCP server."}]
        return tool_response(
            {
                "resolved_session_id": resolved_session_id,
                "resolution": resolution,
                "matches": matches,
            },
            warnings=warnings,
        )

    @app.post("/v1/tools/list_sessions")
    async def list_sessions(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        limit = parse_int(payload, "limit", default=20, minimum=1, maximum=100)
        sessions = store.list_sessions(
            query=optional_payload_str(payload, "query"),
            project_path=optional_payload_str(payload, "project_path"),
            thread_id=optional_payload_str(payload, "thread_id"),
            slug=optional_payload_str(payload, "slug"),
            limit=limit,
        )
        return tool_response({"sessions": sessions, "count": len(sessions)})

    @app.post("/v1/tools/context_search")
    async def context_search(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        query = redact(str(payload.get("query", "")))
        top_k = parse_int(payload, "top_k", default=10, minimum=1, maximum=100)
        filters = search_filters(payload)
        scope = parse_search_scope(payload)
        results, retrieval, warnings = hybrid_context_search(
            store,
            embedding_index,
            session_id=session_id,
            query=query,
            top_k=top_k,
            filters=filters,
            scope=scope,
            reranker=reranker,
            reranker_top_k=settings.reranker_top_k,
        )
        trace_id = audit_memory_tool(
            store,
            session_id,
            "context_search",
            [item["event_id"] for item in results],
            retrieval=retrieval,
            warnings=warnings,
        )
        return tool_response({"results": results}, trace_id=trace_id, warnings=warnings)

    @app.post("/v1/tools/fetch_event")
    async def fetch_event(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        event_id = require_payload_str(payload, "event_id")
        require_session(session_id)
        event = store.get_event(session_id, event_id)
        if not event:
            raise not_found("Event not found.", event_id=event_id)
        response_event, metadata = event_for_fetch(store, session_id, event, full=bool(payload.get("full")))
        neighbors = store.neighbor_events(session_id, event_id) if payload.get("include_neighbors") else []
        exposed_event_ids = [event_id, *[neighbor["event_id"] for neighbor in neighbors]]
        trace_id = audit_memory_tool(store, session_id, "fetch_event", exposed_event_ids)
        return tool_response({"event": response_event, "metadata": metadata, "neighbors": neighbors}, trace_id=trace_id)

    @app.post("/v1/tools/expand_context")
    async def expand_context(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        seed_id = require_payload_str(payload, "seed_event_id")
        require_session(session_id)
        max_events = min(parse_int(payload, "max_events", default=12, minimum=1, maximum=200), settings.max_tool_result_events)
        depth = parse_int(payload, "depth", default=2, minimum=0, maximum=5)
        mode = str(payload.get("mode") or "GRAPH").strip().upper()
        if mode == "SEGMENT":
            segment_id = store.segment_id_for_event(session_id, seed_id)
            if not segment_id:
                raise not_found("Segment not found for seed event.", event_id=seed_id)
            events = store.get_segment_skeleton(session_id, segment_id, max_events=max_events)
            trace_id = audit_memory_tool(store, session_id, "expand_context", [item["event_id"] for item in events])
            truncated = len(events) >= max_events
            warnings = [{"code": "RESULT_TRUNCATED", "message": "Segment skeleton hit max_events."}] if truncated else []
            return tool_response(
                {"seed_event_id": seed_id, "mode": "SEGMENT", "segment_id": segment_id, "truncated": truncated, "events": events},
                trace_id=trace_id,
                warnings=warnings,
            )
        events = expand_graph(store, session_id, seed_id, depth, max_events)
        trace_id = audit_memory_tool(store, session_id, "expand_context", [item["event_id"] for item in events])
        truncated = len(events) >= max_events
        warnings = [{"code": "RESULT_TRUNCATED", "message": "Graph expansion hit max_events before traversal completed."}] if truncated else []
        return tool_response({"seed_event_id": seed_id, "mode": mode, "truncated": truncated, "events": events}, trace_id=trace_id, warnings=warnings)

    @app.post("/v1/tools/recall_recent")
    async def recall_recent(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        turns = parse_int(payload, "turns", default=3, minimum=1, maximum=100)
        events = store.recent_events(session_id, turns * 10)
        if payload.get("include_tool_outputs") is False:
            events = [event for event in events if event.get("type") != "TOOL_OUTPUT"]
        max_tokens = parse_optional_int(payload, "max_tokens", minimum=1, maximum=200000)
        events, truncated = pack_events_under_token_limit(events, max_tokens)
        trace_id = audit_memory_tool(store, session_id, "recall_recent", [event["event_id"] for event in events])
        warnings = [{"code": "RESULT_TRUNCATED", "message": "Recent recall hit max_tokens before all candidate events fit."}] if truncated else []
        return tool_response({"events": summarize_events(events)}, trace_id=trace_id, warnings=warnings)

    @app.post("/v1/tools/list_segments")
    async def list_segments(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        page_size = parse_int(payload, "page_size", default=20, minimum=1, maximum=1000)
        segments = store.list_segments(session_id, limit=page_size)
        trace_id = audit_memory_tool(store, session_id, "list_segments", [])
        return tool_response({"segments": segments, "next_page_token": None}, trace_id=trace_id)

    @app.post("/v1/tools/get_execution_state")
    async def get_execution_state(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        state = store.execution_state_or_default(session_id)
        trace_id = audit_memory_tool(store, session_id, "get_execution_state", [])
        return tool_response(state, trace_id=trace_id)

    @app.post("/v1/tools/get_goal_history")
    async def get_goal_history(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        session_id = require_payload_str(payload, "session_id")
        require_session(session_id)
        limit = parse_int(payload, "limit", default=20, minimum=1, maximum=200)
        history = store.get_state_history(session_id, limit=limit)
        trace_id = audit_memory_tool(store, session_id, "get_goal_history", [])
        return tool_response({"history": history}, trace_id=trace_id)

    @app.post("/v1/tools/explain_context")
    async def explain_context(payload: dict[str, Any], _auth: None = Depends(require_auth)) -> dict[str, Any]:
        trace = store.get_trace(require_payload_str(payload, "trace_id"))
        if not trace:
            raise not_found("Trace not found.", trace_id=payload.get("trace_id"))
        event_id = payload.get("event_id")
        selected = next((event for event in trace.get("selected_events", []) if event.get("event_id") == event_id), None)
        read_trace_id = audit_memory_tool(store, trace["session_id"], "explain_context", [event_id] if selected and isinstance(event_id, str) else [])
        return tool_response({"trace_id": trace["trace_id"], "event_id": event_id, "included": selected is not None, "reason": selected.get("reason") if selected else None, "score": selected.get("score") if selected else None, "layer": selected.get("included_as") if selected else None}, trace_id=read_trace_id)

    @app.get("/v1/traces/{trace_id}")
    async def get_trace(trace_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        trace = store.get_trace(trace_id)
        if not trace:
            raise not_found("Trace not found.", trace_id=trace_id)
        return trace

    @app.get("/v1/costs/session/{session_id}")
    async def cost_report(session_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        require_session(session_id)
        return store.cost_report(session_id)

    @app.get("/v1/sessions/{session_id}/export")
    async def export_session(session_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        require_session(session_id)
        return store.export_session(session_id)

    @app.delete("/v1/sessions/{session_id}")
    async def delete_session(session_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        deleted = store.delete_session(session_id)
        return {"session_id": session_id, "deleted": deleted}

    return app


def require_schema(payload: dict[str, Any], schema_key: str) -> None:
    if payload.get("schema_version") not in SUPPORTED_SCHEMAS[schema_key]:
        raise bad_request("Unsupported schema_version.", schema_version=payload.get("schema_version"))


def require_payload_str(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise validation_error(f"Missing required field {field}.", field=field)
    return value


def optional_payload_str(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise validation_error(f"{field} must be a non-empty string.", field=field)
    return value


def session_not_found_details(store: Store, session_id: str) -> dict[str, Any]:
    candidates = store.list_sessions(query=session_id, limit=5)
    return {
        "session_id": session_id,
        "reason": "SESSION_ID_NOT_FOUND",
        "hint": "Do not guess Mneme session_id. Call resolve_session with project_path/thread_id/slug or list_sessions to find a valid session.",
        "discovery_tools": ["resolve_session", "list_sessions"],
        "candidate_sessions": candidates,
    }


def normalize_event(raw_event: dict[str, Any]) -> dict[str, Any]:
    required = ["event_id", "session_id", "agent_id", "runtime", "role", "type", "timestamp", "content"]
    for field in required:
        if field not in raw_event:
            raise validation_error("Event missing required field.", field=field)
    event = dict(raw_event)
    event.setdefault("parent_event_ids", [])
    event.setdefault("token_estimate", token_estimate(text_from_content(event["content"])))
    return event


def event_immutable_hash(event: dict[str, Any]) -> str:
    content = event.get("content", {})
    immutable = {
        "session_id": event.get("session_id"),
        "turn_id": event.get("turn_id"),
        "agent_id": event.get("agent_id"),
        "runtime": event.get("runtime"),
        "role": event.get("role"),
        "type": event.get("type"),
        "timestamp": event.get("timestamp"),
        "content_hash": content.get("hash") or sha256_text(text_from_content(content)),
        "tool_name": event.get("tool", {}).get("name"),
        "tool_call_id": event.get("tool", {}).get("call_id"),
        "parent_event_ids": event.get("parent_event_ids", []),
    }
    return sha256_text(canonical_json(immutable))


def apply_optional_enrichment(
    store: Store,
    enricher: EnrichmentProvider | None,
    event: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    if enricher is None:
        return state
    try:
        result = enricher.enrich(event, state)
    except Exception:
        result = EnrichmentResult(updates={}, degraded=True, fallback_reason="LLM_ENRICHMENT_UNAVAILABLE")
    store.record_enrichment_metrics(
        event["session_id"],
        enrichment_calls=1,
        enrichment_failures=1 if result.degraded else 0,
    )
    if result.degraded or not result.updates:
        return state
    return apply_enrichment_updates(state, redact(result.updates))


def reindex_missing_embeddings(store: Store, embedding_index: EmbeddingIndex, settings: Settings) -> None:
    events = store.list_events_missing_embedding(embedding_index.model_id)
    if not events:
        return
    records_by_session: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        record = embedding_record_from_event(
            event,
            tool_output_compress_threshold_tokens=settings.tool_output_compress_threshold_tokens,
            tool_output_summary_tokens=settings.tool_output_summary_tokens,
        )
        if record is None:
            continue
        records_by_session.setdefault(str(record["session_id"]), []).append(record)
    for session_id, records in records_by_session.items():
        stats = embedding_index.index_events(records)
        store.record_embedding_metrics(
            session_id,
            embedding_batches=stats.embedding_batches,
            embedding_items=stats.embedding_items,
            embedding_input_chars=stats.embedding_input_chars,
            embedding_failures=stats.embedding_failures,
        )


def should_run_enrichment(
    settings: Settings,
    event: dict[str, Any],
    state: dict[str, Any],
    previous_segment: dict[str, Any] | None,
    segment: dict[str, Any] | None,
) -> bool:
    if event.get("type") != "USER_MESSAGE":
        return False
    every_n = int(settings.enricher_every_n_turns or 0)
    if every_n > 0 and int(state.get("turn_count") or 0) % every_n == 0:
        return True
    if not settings.enricher_on_segment_boundary or not previous_segment or not segment:
        return False
    return previous_segment.get("segment_id") != segment.get("segment_id")


def validate_prepare(payload: dict[str, Any]) -> None:
    if payload.get("budget_tokens", 0) <= 0 or payload.get("budget_tokens", 0) > payload.get("context_window_tokens", 0):
        raise validation_error("budget_tokens must be greater than zero and within context_window_tokens.")
    messages = payload.get("request_messages")
    if not isinstance(messages, list) or not messages:
        raise validation_error("request_messages must be a non-empty list.")
    for message in messages:
        if message.get("schema_version") != "mneme.message.v0" or "role" not in message or "content" not in message:
            raise validation_error("Invalid mneme.message.v0 message.")
    split = payload.get("policy", {}).get("budget_split")
    if split:
        values = list(split.values())
        if any(value < 0 for value in values) or abs(sum(values) - 1.0) > 0.01:
            raise validation_error("budget_split must be non-negative and sum to 1.0.")


def parse_int(payload: dict[str, Any], field: str, *, default: int, minimum: int, maximum: int) -> int:
    raw_value = payload.get(field, default)
    if isinstance(raw_value, bool):
        raise validation_error(f"{field} must be an integer.", field=field)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise validation_error(f"{field} must be an integer.", field=field) from exc
    if value < minimum or value > maximum:
        raise validation_error(f"{field} must be between {minimum} and {maximum}.", field=field)
    return value


def parse_optional_int(payload: dict[str, Any], field: str, *, minimum: int, maximum: int) -> int | None:
    if field not in payload or payload.get(field) is None:
        return None
    return parse_int(payload, field, default=minimum, minimum=minimum, maximum=maximum)


def search_filters(payload: dict[str, Any]) -> dict[str, Any]:
    filters = payload.get("filters") or {}
    if not isinstance(filters, dict):
        raise validation_error("filters must be an object.", field="filters")
    event_types = filters.get("event_types")
    result: dict[str, Any] = {}
    if event_types is not None:
        if not isinstance(event_types, list) or any(not isinstance(item, str) or not item for item in event_types):
            raise validation_error("filters.event_types must be a list of non-empty strings.", field="filters.event_types")
        result["event_types"] = event_types
    after = filters.get("after")
    before = filters.get("before")
    if after is not None:
        if not isinstance(after, str) or not after:
            raise validation_error("filters.after must be an ISO timestamp string.", field="filters.after")
        result["after"] = after
    if before is not None:
        if not isinstance(before, str) or not before:
            raise validation_error("filters.before must be an ISO timestamp string.", field="filters.before")
        result["before"] = before
    return result


def parse_search_scope(payload: dict[str, Any]) -> str:
    scope = str(payload.get("scope") or "LINEAGE").strip().upper()
    if scope in {"SESSION", "LINEAGE", "GLOBAL", "ALL"}:
        return "GLOBAL" if scope == "ALL" else scope
    raise validation_error("scope must be SESSION, LINEAGE, GLOBAL, or ALL.", field="scope")


def search_session_ids_for_scope(store: Store, session_id: str, scope: str) -> list[str] | None:
    if scope == "GLOBAL":
        return None
    if scope == "SESSION":
        return [session_id]
    return store.lineage_session_ids(session_id)


def derive_query(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "USER":
            return str(message.get("content", ""))
    return str(messages[-1].get("content", "")) if messages else ""


def approximate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    return sum(token_estimate(str(message.get("content", ""))) for message in messages)


def execution_state_context_block(state: dict[str, Any], *, budget_tokens: int) -> tuple[str, int, str]:
    variants = [
        ("FULL", execution_state_lines(state, decision_limit=5, include_tool_output=True)),
        ("COMPACT", execution_state_lines(state, decision_limit=3, include_tool_output=False)),
        ("MINIMAL", execution_state_lines(state, decision_limit=1, include_tool_output=False, minimal=True)),
    ]
    for compression, lines in variants:
        block = "\n".join(lines)
        if len(lines) == 1:
            return "", 0, "EMPTY"
        block_tokens = token_estimate(block)
        if block_tokens <= budget_tokens:
            return block, block_tokens, compression
    minimal = "\n".join(variants[-1][1])
    if token_estimate(minimal) <= budget_tokens:
        return minimal, token_estimate(minimal), "MINIMAL"
    truncated = truncate_to_token_budget(minimal, budget_tokens)
    if not truncated:
        return "", 0, "DROPPED_FOR_BUDGET"
    return truncated, token_estimate(truncated), "TRUNCATED"


def execution_state_lines(
    state: dict[str, Any],
    *,
    decision_limit: int,
    include_tool_output: bool,
    minimal: bool = False,
) -> list[str]:
    lines = ["[MNEME EXECUTION STATE]"]
    enrichment = state.get("enrichment") if isinstance(state.get("enrichment"), dict) else {}
    if state.get("goal"):
        lines.append(f"Goal: {context_line(state['goal'])}")
    if state.get("current_step"):
        lines.append(f"Current step: {context_line(state['current_step'])}")
    if enrichment.get("intent_label"):
        lines.append(f"Intent: {context_line(enrichment['intent_label'])}")
    topic_tags = enrichment.get("topic_tags") if isinstance(enrichment.get("topic_tags"), list) else []
    if topic_tags:
        lines.append(f"Topic tags: {', '.join(context_line(tag) for tag in topic_tags[:8])}")
    if enrichment.get("decision_summary"):
        lines.append(f"Decision summary: {context_line(enrichment['decision_summary'])}")
    if minimal:
        return lines
    if state.get("last_tool"):
        lines.append(f"Last tool: {context_line(state['last_tool'])}")
    if include_tool_output and state.get("last_tool_output_summary"):
        lines.append(f"Last tool output: {context_line(state['last_tool_output_summary'])}")
    decisions = [
        decision
        for decision in state.get("decision_stack", [])
        if isinstance(decision, dict) and (decision.get("decision") or decision.get("text"))
    ]
    if decisions:
        lines.append("Decisions:")
        for decision in decisions[-decision_limit:]:
            text = decision.get("decision") or decision.get("text")
            rationale = decision.get("rationale")
            suffix = f" | rationale: {context_line(rationale)}" if rationale else ""
            lines.append(f"- {context_line(text)}{suffix}")
    return lines


def truncate_to_token_budget(text: str, budget_tokens: int) -> str:
    if budget_tokens <= 0:
        return ""
    max_chars = max(0, budget_tokens * 4)
    if not max_chars:
        return ""
    return text[:max_chars].rstrip()


def protected_tail_messages(
    messages: list[dict[str, Any]],
    tail_budget_tokens: int,
    *,
    preserve_system_prompt: bool,
) -> tuple[list[dict[str, Any]], int]:
    system_messages = []
    candidates = messages
    if preserve_system_prompt and messages and messages[0].get("role") == "SYSTEM":
        system_messages = [messages[0]]
        candidates = messages[1:]
    kept_reversed: list[dict[str, Any]] = []
    used_tokens = 0
    for message in reversed(candidates):
        message_tokens = token_estimate(str(message.get("content", "")))
        if not kept_reversed or used_tokens + message_tokens <= tail_budget_tokens:
            kept_reversed.append(message)
            used_tokens += message_tokens
            continue
        break
    return system_messages + list(reversed(kept_reversed)), used_tokens


def pack_retrieved_events(
    events: list[dict[str, Any]],
    retrieved_budget_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    selected: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    used_tokens = 0
    for event in events:
        event_tokens = token_estimate(retrieved_event_line(event))
        if event_tokens <= max(0, retrieved_budget_tokens - used_tokens):
            selected.append(event)
            used_tokens += event_tokens
            continue
        dropped.append({"event_id": event["event_id"], "reason": "RETRIEVED_CONTEXT_BUDGET_EXCEEDED"})
    return selected, dropped, used_tokens


def retrieved_event_line(event: dict[str, Any]) -> str:
    return f"- {event['event_id']}: {text_from_content(event.get('content', {}))}"


def prepare_prompt_helper_blocks(
    store: Store,
    settings: Settings,
    session_id: str,
    *,
    include_helpers: bool,
) -> tuple[str, str, str]:
    if not include_helpers:
        return "", "", ""
    memory_hint = memory_access_hint_block(store, settings, session_id)
    goal_trail = goal_trail_context_block(store.get_recent_unique_goals(session_id, settings.goal_trail_size))
    checkpoint = checkpoint_context_block(store, settings, session_id)
    return memory_hint, goal_trail, checkpoint


def memory_access_hint_block(store: Store, settings: Settings, session_id: str) -> str:
    if not settings.memory_access_hint_enabled:
        return ""
    stats = store.session_stats(session_id)
    lines = [
        "[MNEME MEMORY ACCESS]",
        "Use Mneme memory tools as evidence when past context may matter.",
        "Start with list_segments or context_search; fetch_event only when a snippet is incomplete.",
        "Cite event ids from retrieved evidence instead of guessing or repeating prior work.",
    ]
    if stats["total_events"] > int(settings.protected_tail_turns or 0):
        lines.append(
            f"Memory stats: {stats['total_events']} events, {stats['total_segments']} segments; older context is outside the active tail."
        )
    return "\n".join(lines)


def goal_trail_context_block(goals: list[dict[str, Any]]) -> str:
    if not goals:
        return ""
    lines = ["[MNEME GOAL TRAIL]"]
    for index, item in enumerate(goals):
        timestamp = str(item.get("timestamp") or "")[:16].replace("T", " ")
        marker = " <- current" if index == len(goals) - 1 else ""
        lines.append(f"- {timestamp}: {context_line(item.get('goal') or '')}{marker}")
    return "\n".join(lines)


def checkpoint_context_block(store: Store, settings: Settings, session_id: str) -> str:
    threshold = int(settings.checkpoint_after_n_memory_calls or 0)
    if threshold <= 0:
        return ""
    consecutive = store.recent_memory_tool_count(session_id, settings.memory_tool_names)
    if consecutive < threshold:
        return ""
    state = store.execution_state_or_default(session_id)
    goals = store.get_recent_unique_goals(session_id, limit=5)
    current_goal = state.get("goal") or "<none>"
    prior_goal = ""
    if len(goals) >= 2:
        prior_goal = goals[-2].get("goal") or ""
    elif goals:
        prior_goal = goals[0].get("goal") or ""
    lines = [
        f"[MNEME CHECKPOINT] {consecutive} memory-tool calls happened before this prepare.",
        f"Current goal: {context_line(current_goal)}",
    ]
    if prior_goal and prior_goal != current_goal:
        lines.append(f"Previous goal: {context_line(prior_goal)}")
    lines.append("Continue the useful work, or call get_goal_history if the thread is unclear.")
    return "\n".join(lines)


def prepare_context_blocks(
    memory_hint_block: str,
    goal_trail_block: str,
    state_block: str,
    checkpoint_block: str,
    selected_events: list[dict[str, Any]],
) -> list[str]:
    blocks = []
    if memory_hint_block:
        blocks.append(memory_hint_block)
    if goal_trail_block:
        blocks.append(goal_trail_block)
    if state_block:
        blocks.append(state_block)
    if checkpoint_block:
        blocks.append(checkpoint_block)
    if selected_events:
        evidence = "\n".join(retrieved_event_line(event) for event in selected_events)
        blocks.append(f"[MNEME RETRIEVED EVIDENCE]\n{evidence}".strip())
    return blocks


def context_blocks_tokens(context_blocks: list[str]) -> int:
    return token_estimate("\n\n".join(context_blocks).strip()) if context_blocks else 0


def projected_prepare_tokens(messages: list[dict[str, Any]], context_blocks: list[str]) -> int:
    return approximate_messages_tokens(messages) + context_blocks_tokens(context_blocks)


def cross_session_event_ids(session_id: str, events: list[dict[str, Any]]) -> list[str]:
    return [
        event["event_id"]
        for event in events
        if event.get("session_id") and event.get("session_id") != session_id
    ]


def context_line(value: Any) -> str:
    return " ".join(str(value).split())


def prepare_trace(
    trace_id: str,
    payload: dict[str, Any],
    selected_events: list[dict[str, Any]],
    start: float,
    *,
    selection_reason: str = "KEYWORD_RECENCY",
    execution_state_tokens: int = 0,
    protected_tail_tokens: int = 0,
    dropped_event_refs: list[dict[str, str]] | None = None,
    retrieved_tokens: int | None = None,
        degraded: bool = False,
        context_blocks: list[str] | None = None,
        memory_hint_tokens: int = 0,
        goal_trail_tokens: int = 0,
        checkpoint_tokens: int = 0,
        cross_session_event_ids: list[str] | None = None,
        state_compression: str = "NONE",
) -> dict[str, Any]:
    selected_ids = [event["event_id"] for event in selected_events]
    dropped = dropped_event_refs or []
    blocks = context_blocks or []
    return {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "CONTEXT_PREPARE",
        "session_id": payload["session_id"],
        "turn_id": payload.get("turn_id"),
        "request_id": payload.get("request_id"),
        "prepare_id": payload.get("prepare_id"),
        "policy": payload.get("policy", {}),
        "budget": {
            "budget_tokens": payload.get("budget_tokens"),
            "execution_state_tokens": execution_state_tokens,
            "protected_tail_tokens": protected_tail_tokens,
            "retrieved_tokens": retrieved_tokens if retrieved_tokens is not None else sum(token_estimate(text_from_content(event.get("content", {}))) for event in selected_events),
            "memory_hint_tokens": memory_hint_tokens,
            "goal_trail_tokens": goal_trail_tokens,
            "checkpoint_tokens": checkpoint_tokens,
            "context_blocks": len(blocks),
            "state_compression": state_compression,
        },
        "retrieval": {"candidate_count": len(selected_events) + len(dropped), "selected_count": len(selected_events), "strategies": ["KEYWORD", "RECENCY"], "degraded": degraded, "fallbacks": []},
        "selected_events": [{"event_id": event_id, "reason": selection_reason, "score": 1.0, "included_as": "RETRIEVED_EVIDENCE"} for event_id in selected_ids],
        "cross_session_event_ids": cross_session_event_ids or [],
        "dropped_events": dropped,
        "latency_ms": {"total": int((time.perf_counter() - start) * 1000), "retrieval": 0, "rerank": 0, "packing": 0},
        "privacy_actions": [],
        "audit_entries": [{"action": "MEMORY_READ", "tool": "context_prepare", "event_ids": selected_ids}],
        "warnings": [],
    }


def tool_response(data: dict[str, Any], *, trace_id: str | None = None, warnings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"ok": True, "data": data, "trace_id": trace_id, "warnings": warnings or []}


def audit_memory_tool(
    store: Store,
    session_id: str,
    tool: str,
    event_ids: list[str],
    *,
    retrieval: dict[str, Any] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> str:
    trace_id = new_id("trace")
    trace = memory_read_trace(trace_id, session_id, tool, event_ids, retrieval=retrieval, warnings=warnings)
    store.put_trace(trace)
    store.add_audit(session_id, "MEMORY_READ", tool, event_ids, trace_id=trace_id)
    memory_event = {
        "schema_version": "mneme.event.v0",
        "event_id": new_id("memory-read"),
        "session_id": session_id,
        "turn_id": None,
        "agent_id": "mneme",
        "runtime": "MNEME",
        "role": "RUNTIME",
        "type": "MEMORY_READ",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "content": {"format": "JSON", "text": canonical_json({"tool": tool, "event_ids": event_ids, "trace_id": trace_id})},
        "parent_event_ids": [],
        "token_estimate": 1,
    }
    store.put_event(memory_event, event_immutable_hash(memory_event), text_from_content(memory_event["content"]), is_memory_read=True)
    return trace_id


def memory_read_trace(
    trace_id: str,
    session_id: str,
    tool: str,
    event_ids: list[str],
    *,
    retrieval: dict[str, Any] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    trace = {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "MEMORY_READ",
        "session_id": session_id,
        "turn_id": None,
        "tool": tool,
        "selected_event_ids": event_ids,
        "selected_events": [{"event_id": event_id, "reason": "DIRECT_MEMORY_TOOL", "score": 1.0, "included_as": "MEMORY_TOOL_RESULT"} for event_id in event_ids],
        "dropped_events": [],
        "latency_ms": {"total": 0, "retrieval": 0, "rerank": 0, "packing": 0},
        "privacy_actions": [],
        "audit_entries": [{"action": "MEMORY_READ", "tool": tool, "event_ids": event_ids}],
        "warnings": warnings or [],
    }
    if retrieval is not None:
        trace["retrieval"] = retrieval
    return trace


def maybe_trace_segment_drift(
    store: Store,
    event: dict[str, Any],
    classification: dict[str, Any],
    previous_segment: dict[str, Any] | None,
    segment: dict[str, Any] | None,
) -> None:
    if event.get("type") != "USER_MESSAGE":
        return
    if classification.get("intent") not in {INTENT_SWITCH, INTENT_NEW_TASK}:
        return
    if not previous_segment or not segment:
        return
    if previous_segment.get("segment_id") == segment.get("segment_id"):
        return
    store.put_trace(segment_drift_trace(new_id("trace"), event, classification, previous_segment, segment))


def segment_drift_trace(
    trace_id: str,
    event: dict[str, Any],
    classification: dict[str, Any],
    previous_segment: dict[str, Any],
    segment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "mneme.trace.v0",
        "trace_id": trace_id,
        "trace_type": "SEGMENT_DRIFT",
        "session_id": event["session_id"],
        "turn_id": event.get("turn_id"),
        "event_id": event["event_id"],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "signals": classification.get("signals", {}),
        "decision": {
            "intent": classification.get("intent"),
            "drift_reason": segment.get("drift_reason"),
        },
        "segment_effect": {
            "closed_segment_id": previous_segment.get("segment_id"),
            "opened_segment_id": segment.get("segment_id"),
            "closed_event_count": previous_segment.get("event_count"),
            "opened_event_count": segment.get("event_count"),
        },
        "fallbacks": [],
        "warnings": [],
    }


def hybrid_context_search(
    store: Store,
    embedding_index: EmbeddingIndex | None,
    *,
    session_id: str,
    query: str,
    top_k: int,
    filters: dict[str, Any],
    scope: str = "LINEAGE",
    reranker: RerankerProvider | None = None,
    reranker_top_k: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    strategies: list[str] = []
    fallbacks: list[str] = []
    warnings: list[dict[str, Any]] = []
    semantic_results: list[dict[str, Any]] = []
    degraded = False
    mode = infer_retrieval_mode(query)
    weights = ROUTER_MODE_WEIGHTS[mode]

    if embedding_index is not None:
        strategies.append("VECTOR")
        if scope == "GLOBAL":
            semantic = embedding_index.search_global_with_status(query, top_k=top_k * 2)
        else:
            semantic = embedding_index.search_with_status(query, session_id=session_id, top_k=top_k * 2)
        semantic_results = semantic.results
        if semantic.degraded:
            degraded = True
            reason = semantic.fallback_reason or "EMBEDDINGS_UNAVAILABLE"
            fallbacks.append(reason)
            warnings.append(
                {
                    "code": reason,
                    "message": "Embedding retrieval unavailable; keyword/recency fallback used.",
                }
            )

    strategies.extend(["KEYWORD", "RECENCY"])
    if scope == "GLOBAL":
        keyword_results = store.search_events_for_sessions(None, query, top_k, **filters)
    else:
        keyword_results = store.search_events(session_id, query, top_k, **filters)
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in semantic_results:
        event = store.get_event_for_sessions(None, item["event_id"]) if scope == "GLOBAL" else store.get_event(session_id, item["event_id"])
        if not event or not event_matches_filters(event, filters):
            continue
        combined.append(
            {
                "event_id": event["event_id"],
                "session_id": event["session_id"],
                "turn_id": event.get("turn_id"),
                "type": event["type"],
                "timestamp": event["timestamp"],
                "score": item["score"],
                "snippet": text_from_content(event.get("content", {}))[:240],
                "reason": item.get("reason", "VECTOR_COSINE"),
            }
        )
        seen.add(event["event_id"])

    for item in keyword_results:
        if item["event_id"] in seen:
            continue
        combined.append(item)
        seen.add(item["event_id"])

    graph_results = graph_dependency_results(store, session_id, combined, seen, filters, top_k)
    if graph_results:
        strategies.append("GRAPH_DEPENDENCY")
        combined.extend(graph_results)

    if reranker is not None and combined and query.strip():
        strategies.append("RERANK")
        documents = [str(item.get("snippet", "")) for item in combined]
        try:
            reranked = reranker.rerank(query, documents)
        except Exception:
            reranked = RerankResult(scores=[], degraded=True, fallback_reason="RERANKER_UNAVAILABLE")
        if reranked.degraded or not reranked.scores:
            degraded = True
            reason = reranked.fallback_reason or "RERANKER_UNAVAILABLE"
            fallbacks.append(reason)
            warnings.append(
                {
                    "code": reason,
                    "message": "Reranker unavailable; original retrieval ranking used.",
                }
            )
            store.record_reranker_metrics(session_id, reranker_calls=1, reranker_failures=1)
        else:
            combined = reranked_results(combined, reranked.scores)
            if reranker_top_k and reranker_top_k > 0:
                combined = combined[:reranker_top_k]
            store.record_reranker_metrics(session_id, reranker_calls=1, reranker_failures=0)

    selected = combined[:top_k]
    retrieval = {
        "candidate_count": len(semantic_results) + len(keyword_results) + len(graph_results),
        "selected_count": len(selected),
        "strategies": strategies,
        "mode": mode,
        "weights": weights,
        "degraded": degraded,
        "fallbacks": fallbacks,
    }
    return selected, retrieval, warnings


def infer_retrieval_mode(query: str) -> str:
    text = (query or "").lower()
    debug_keywords = (
        "error",
        "fail",
        "failed",
        "traceback",
        "exception",
        "debug",
        "broken",
        "crash",
        "bug",
        "ошибк",
        "не работает",
        "падает",
        "сломал",
    )
    reasoning_keywords = (
        "why",
        "how should",
        "what if",
        "should i",
        "best way",
        "tradeoff",
        "почему",
        "как лучше",
        "что если",
        "стоит ли",
    )
    factual_keywords = ("what is", "when ", "where ", "who ", "list ", "show me", "что такое", "когда", "где", "покажи")
    if any(keyword in text for keyword in debug_keywords):
        return "debugging"
    if any(keyword in text for keyword in reasoning_keywords) or len(text) > 500:
        return "reasoning"
    if any(keyword in text for keyword in factual_keywords):
        return "factual"
    if text.strip().endswith("?"):
        return "clarification"
    return "general"


def reranked_results(items: list[dict[str, Any]], scores: list[dict[str, float | int]]) -> list[dict[str, Any]]:
    reranked: list[dict[str, Any]] = []
    used_indexes: set[int] = set()
    for score in scores:
        index = int(score["index"])
        if index < 0 or index >= len(items) or index in used_indexes:
            continue
        item = dict(items[index])
        item["score"] = float(score["score"])
        item["reason"] = "RERANKED"
        reranked.append(item)
        used_indexes.add(index)
    reranked.extend(item for index, item in enumerate(items) if index not in used_indexes)
    return reranked


def graph_dependency_results(
    store: Store,
    session_id: str,
    seeds: list[dict[str, Any]],
    seen: set[str],
    filters: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for seed in list(seeds):
        for edge in store.graph_edges_for_event(session_id, seed["event_id"]):
            neighbor_id = edge["target_event_id"] if edge["source_event_id"] == seed["event_id"] else edge["source_event_id"]
            if neighbor_id in seen:
                continue
            event = store.get_event(session_id, neighbor_id)
            if not event or not event_matches_filters(event, filters):
                continue
            results.append(
                {
                    "event_id": event["event_id"],
                    "turn_id": event.get("turn_id"),
                    "type": event["type"],
                    "timestamp": event["timestamp"],
                    "score": max(float(seed.get("score", 0.0)) * 0.5, 0.1),
                    "snippet": text_from_content(event.get("content", {}))[:240],
                    "reason": f"GRAPH_DEPENDENCY:{edge['edge_type']}",
                }
            )
            seen.add(neighbor_id)
            if len(seeds) + len(results) >= top_k:
                return results
    return results


def event_matches_filters(event: dict[str, Any], filters: dict[str, Any]) -> bool:
    event_types = filters.get("event_types")
    if event_types and event.get("type") not in event_types:
        return False
    after = filters.get("after")
    if after is not None and event.get("timestamp", "") < after:
        return False
    before = filters.get("before")
    if before is not None and event.get("timestamp", "") > before:
        return False
    return True


def last_assistant_entities(store: Store, session_id: str) -> list[str]:
    for event in reversed(store.recent_events(session_id, 20)):
        if event.get("type") == "ASSISTANT_MESSAGE":
            return extract_entities(text_from_content(event.get("content", {})))
    return []


def pack_events_under_token_limit(events: list[dict[str, Any]], max_tokens: int | None) -> tuple[list[dict[str, Any]], bool]:
    if max_tokens is None:
        return events, False
    packed: list[dict[str, Any]] = []
    used_tokens = 0
    truncated = False
    for event in reversed(events):
        event_tokens = token_estimate(text_from_content(event.get("content", {}))[:240])
        if used_tokens + event_tokens > max_tokens:
            truncated = True
            break
        packed.append(event)
        used_tokens += event_tokens
    return list(reversed(packed)), truncated


def summarize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": event["event_id"],
            "turn_id": event.get("turn_id"),
            "type": event["type"],
            "timestamp": event["timestamp"],
            "snippet": text_from_content(event.get("content", {}))[:240],
        }
        for event in events
    ]


def event_for_fetch(
    store: Store,
    session_id: str,
    event: dict[str, Any],
    *,
    full: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    response_event = dict(event)
    content = dict(response_event.get("content") or {})
    text = text_from_content(content)
    original_chars = len(text)
    truncated = False
    if not full and original_chars > 4000 and content.get("format") != "BYTES_REF":
        content["text"] = text[:4000]
        response_event["content"] = content
        truncated = True
    segment_id = None
    metadata = response_event.get("metadata")
    if isinstance(metadata, dict):
        segment_id = metadata.get("mneme_segment_id")
    if not segment_id:
        segment_id = store.segment_id_for_event(session_id, event["event_id"])
    return response_event, {
        "segment_id": segment_id,
        "token_estimate": int(event.get("token_estimate") or token_estimate(text)),
        "truncated": truncated,
        "original_chars": original_chars,
    }


def expand_graph(store: Store, session_id: str, seed_id: str, depth: int, max_events: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    queue: list[tuple[str, str, int]] = [(seed_id, "SEED", 0)]
    output: list[dict[str, Any]] = []
    while queue and len(output) < max_events:
        event_id, edge, distance = queue.pop(0)
        if event_id in seen:
            continue
        event = store.get_event(session_id, event_id)
        if not event:
            continue
        seen.add(event_id)
        output.append({"event_id": event_id, "type": event["type"], "edge": edge})
        if distance >= depth:
            continue
        graph_edges = store.graph_edges_for_event(session_id, event_id)
        if graph_edges:
            for graph_edge in graph_edges:
                neighbor_id = graph_edge["target_event_id"] if graph_edge["source_event_id"] == event_id else graph_edge["source_event_id"]
                queue.append((neighbor_id, graph_edge["edge_type"], distance + 1))
            continue
        for parent_id in event.get("parent_event_ids", []):
            queue.append((parent_id, "PARENT", distance + 1))
        for child in store.child_events(session_id, event_id):
            queue.append((child["event_id"], "CHILD", distance + 1))
    return output
