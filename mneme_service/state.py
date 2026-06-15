from __future__ import annotations

from typing import Any

from .utils import text_from_content


STATE_SCHEMA_VERSION = "mneme.execution_state.v0"
HISTORY_ENTRY_SCHEMA_VERSION = "mneme.state_history_entry.v0"


def default_execution_state(session_id: str) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "session_id": session_id,
        "goal": "",
        "current_step": "",
        "open_loops": [],
        "last_tool": None,
        "last_tool_output_summary": None,
        "decision_stack": [],
        "active_entities": [],
        "turn_count": 0,
        "segment_id": f"segment-{session_id}",
        "enrichment": {
            "decision_summary": None,
            "intent_label": None,
            "topic_tags": [],
        },
    }


def apply_event_to_state(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    updated = dict(state)
    updated.setdefault("schema_version", STATE_SCHEMA_VERSION)
    updated.setdefault("session_id", event["session_id"])
    updated.setdefault("open_loops", [])
    updated.setdefault("decision_stack", [])
    updated.setdefault("active_entities", [])
    updated.setdefault("turn_count", 0)
    updated.setdefault("segment_id", f"segment-{event['session_id']}")
    updated.setdefault(
        "enrichment",
        {"decision_summary": None, "intent_label": None, "topic_tags": []},
    )
    event_type = event.get("type")
    text = text_from_content(event.get("content", {})).strip()

    if event_type == "USER_MESSAGE" and text:
        updated["turn_count"] = int(updated.get("turn_count") or 0) + 1
        if not updated.get("goal"):
            updated["goal"] = text[:500]
        updated["current_step"] = text[:300]
    elif event_type == "TOOL_CALL":
        tool_name = event.get("tool", {}).get("name")
        if tool_name:
            updated["last_tool"] = tool_name
    elif event_type == "TOOL_OUTPUT":
        tool_name = event.get("tool", {}).get("name")
        if tool_name:
            updated["last_tool"] = tool_name
        if text:
            updated["last_tool_output_summary"] = text[:100] + ("..." if len(text) > 100 else "")
    elif event_type == "ASSISTANT_MESSAGE" and text:
        updated["current_step"] = text[:200]
    elif event_type == "DECISION" and text:
        decisions = list(updated.get("decision_stack") or [])
        metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
        rationale = metadata.get("rationale")
        decisions.append(
            {
                "event_id": event["event_id"],
                "timestamp": event["timestamp"],
                "decision": text[:500],
                "rationale": str(rationale)[:500] if rationale else None,
                "text": text[:500],
            }
        )
        updated["decision_stack"] = decisions[-20:]
    return updated


def history_entry_from_state(state: dict[str, Any], timestamp: str) -> dict[str, Any]:
    enrichment = state.get("enrichment") or {}
    return {
        "schema_version": HISTORY_ENTRY_SCHEMA_VERSION,
        "timestamp": timestamp,
        "goal": state.get("goal") or None,
        "current_step": state.get("current_step") or None,
        "intent_label": enrichment.get("intent_label"),
        "decisions": enrichment.get("decisions") or [],
    }
