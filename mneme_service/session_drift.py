from __future__ import annotations

from typing import Any


SESSION_FRESH = "FRESH"
SESSION_RESUME = "RESUME"

RESUME_SOURCE_NEW_SESSION = "NEW_SESSION"
RESUME_SOURCE_EXISTING_EVENTS = "EXISTING_SESSION_EVENTS"
RESUME_SOURCE_ADAPTER_METADATA = "ADAPTER_METADATA"

RESUME_LIFECYCLE_VALUES = {"RESUME", "RESUMED", "RESTART", "RESTARTED"}
LINEAGE_KEYS = ("parent_session_id", "previous_session_id", "resume_of_session_id", "lineage_session_id")


def classify_session_start(
    session: dict[str, Any],
    *,
    created: bool,
    prior_event_count: int,
    prior_turn_count: int,
    lineage_event_count: int | None = None,
    lineage_turn_count: int | None = None,
) -> dict[str, Any]:
    lineage_event_count = prior_event_count if lineage_event_count is None else lineage_event_count
    lineage_turn_count = prior_turn_count if lineage_turn_count is None else lineage_turn_count
    metadata = session.get("metadata") if isinstance(session.get("metadata"), dict) else {}
    lifecycle = str(metadata.get("lifecycle", "")).upper()
    lineage_session_id = first_metadata_string(metadata, LINEAGE_KEYS)
    adapter_resume_requested = (
        metadata.get("resume") is True
        or lifecycle in RESUME_LIFECYCLE_VALUES
        or lineage_session_id is not None
    )
    has_prior_events = lineage_event_count > 0 or lineage_turn_count > 0

    if has_prior_events:
        classification = SESSION_RESUME
        resume_source = RESUME_SOURCE_EXISTING_EVENTS
    elif adapter_resume_requested:
        classification = SESSION_RESUME
        resume_source = RESUME_SOURCE_ADAPTER_METADATA
    else:
        classification = SESSION_FRESH
        resume_source = RESUME_SOURCE_NEW_SESSION

    return {
        "schema_version": "mneme.session_state.v0",
        "classification": classification,
        "resume_source": resume_source,
        "requires_context_fill": classification == SESSION_RESUME and has_prior_events,
        "signals": {
            "created": created,
            "prior_event_count": prior_event_count,
            "prior_turn_count": prior_turn_count,
            "lineage_event_count": lineage_event_count,
            "lineage_turn_count": lineage_turn_count,
            "adapter_resume_requested": adapter_resume_requested,
            "lifecycle": lifecycle or None,
            "lineage_session_id": lineage_session_id,
        },
    }


def first_metadata_string(metadata: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None
