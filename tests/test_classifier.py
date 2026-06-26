from __future__ import annotations

from mneme_service.classifier import (
    INTENT_CLARIFICATION,
    INTENT_CONTINUATION,
    INTENT_NEW_TASK,
    INTENT_SWITCH,
    classify_entity_contradiction,
    classify_intent,
    extract_entity_modifiers,
    extract_entities,
)


def test_classifier_detects_english_and_russian_topic_switches() -> None:
    assert classify_intent("New topic: fix the billing parser")["intent"] == INTENT_SWITCH
    assert classify_intent("Давай переключимся на отчеты")["intent"] == INTENT_SWITCH
    assert classify_intent("Новая тема: исправим парсер")["intent"] == INTENT_SWITCH


def test_classifier_detects_clarification_questions_without_switching() -> None:
    assert classify_intent("What did the pytest output mean?")["intent"] == INTENT_CLARIFICATION
    assert classify_intent("Что означает этот вывод pytest")["intent"] == INTENT_CLARIFICATION


def test_classifier_defaults_to_continuation() -> None:
    assert classify_intent("Continue the retrieval work")["intent"] == INTENT_CONTINUATION


def test_classifier_uses_high_embedding_drift_for_new_task() -> None:
    result = classify_intent("Refactor the billing parser", embedding_drift=0.72)
    assert result["intent"] == INTENT_NEW_TASK
    assert result["signals"]["embedding_drift"] == 0.72


def test_classifier_uses_entity_contradiction_as_switch_signal() -> None:
    result = classify_intent("Do not use OAuthFlow anymore", active_entities=["OAuthFlow"])

    assert result["intent"] == INTENT_SWITCH
    assert result["signals"]["entity_contradiction"] is True


def test_classifier_priority_chain_prefers_switch_over_other_signals() -> None:
    result = classify_intent(
        "New topic: why did OAuthFlow fail?",
        embedding_drift=0.92,
        active_entities=["OAuthFlow"],
        last_assistant_entities=["OAuthFlow"],
    )

    assert result["intent"] == INTENT_SWITCH
    assert result["signals"]["explicit_switch"] is True
    assert result["signals"]["question_about_output"] is True


def test_entity_contradiction_uses_five_whitespace_word_window() -> None:
    assert classify_entity_contradiction("Do not use OAuthFlow anymore", ["OAuthFlow"]) is True
    assert classify_entity_contradiction(
        "not one two three four five OAuthFlow",
        ["OAuthFlow"],
    ) is False
    assert classify_entity_contradiction(
        "one two not three four five OAuthFlow",
        ["OAuthFlow"],
    ) is True
    assert classify_entity_contradiction(
        "Use TokenBroker instead of OAuthFlow",
        ["OAuthFlow"],
    ) is True


def test_extract_entity_modifiers_are_deterministic_and_ordered() -> None:
    modifiers = extract_entity_modifiers(
        "replace OAuthFlow with TokenBroker, remove LegacyAPI, ensure strict retries, add PostgreSQL",
        active_entities=["OAuthFlow", "LegacyAPI"],
    )

    assert [(item["modifier_type"], item["entity"], item["value"]) for item in modifiers] == [
        ("REPLACE", "OAuthFlow", "TokenBroker"),
        ("REMOVE", "LegacyAPI", None),
        ("CONSTRAINT", "strict retries", None),
        ("ADD", "PostgreSQL", None),
    ]
    assert all(item["schema_version"] == "mneme.entity_modifier.v0" for item in modifiers)
    assert all(item["source"] == "DETERMINISTIC_PATTERN" for item in modifiers)
    assert all("source_span" in item for item in modifiers)


def test_classifier_marks_question_about_last_assistant_output() -> None:
    entities = extract_entities("Use `ContextRouter` for retrieval.")
    result = classify_intent("Why did ContextRouter choose that event?", last_assistant_entities=entities)

    assert "ContextRouter" in entities
    assert result["intent"] == INTENT_CLARIFICATION
    assert result["signals"]["question_about_output"] is True
