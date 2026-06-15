from __future__ import annotations

from typing import Any

from .classifier import INTENT_NEW_TASK, INTENT_SWITCH
from .storage import Store
from .utils import text_from_content, token_estimate


def update_segment_for_event(store: Store, event: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("type") != "USER_MESSAGE":
        return None
    session_id = event["session_id"]
    current = store.latest_active_segment(session_id)
    intent = classification.get("intent")
    if current is None:
        segment = _new_segment(store, event, drift_reason="SESSION_START")
        store.put_segment(segment)
        return segment
    if intent in {INTENT_SWITCH, INTENT_NEW_TASK} and int(current.get("event_count") or 0) > 0:
        closed = dict(current)
        closed["status"] = "CLOSED"
        closed["updated_at"] = event["timestamp"]
        store.put_segment(closed)
        drift_reason = "EXPLICIT_SWITCH" if intent == INTENT_SWITCH else "EMBEDDING_DRIFT"
        segment = _new_segment(store, event, drift_reason=drift_reason)
        store.put_segment(segment)
        return segment
    updated = dict(current)
    updated["event_count"] = int(updated.get("event_count") or 0) + 1
    updated["token_estimate"] = int(updated.get("token_estimate") or 0) + int(event.get("token_estimate") or 0)
    updated["updated_at"] = event["timestamp"]
    anchors = list(updated.get("anchor_event_ids") or [])
    anchors.append(event["event_id"])
    updated["anchor_event_ids"] = anchors
    store.put_segment(updated)
    return updated


def _new_segment(store: Store, event: dict[str, Any], *, drift_reason: str) -> dict[str, Any]:
    text = text_from_content(event.get("content", {})).strip()
    segment_number = store.segment_count(event["session_id"]) + 1
    return {
        "schema_version": "mneme.segment.v0",
        "segment_id": f"segment-{event['session_id']}-{segment_number}",
        "session_id": event["session_id"],
        "title": text[:80] or f"Segment {segment_number}",
        "summary": text[:240] if text else "Recorded session activity.",
        "status": "ACTIVE",
        "event_count": 1,
        "token_estimate": int(event.get("token_estimate") or token_estimate(text)),
        "created_at": event["timestamp"],
        "updated_at": event["timestamp"],
        "anchor_event_ids": [event["event_id"]],
        "drift_reason": drift_reason,
    }
