from __future__ import annotations

from mneme_service.classifier import (
    INTENT_CLARIFICATION,
    INTENT_CONTINUATION,
    INTENT_NEW_TASK,
    INTENT_SWITCH,
    classify_intent,
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


def test_classifier_marks_question_about_last_assistant_output() -> None:
    entities = extract_entities("Use `ContextRouter` for retrieval.")
    result = classify_intent("Why did ContextRouter choose that event?", last_assistant_entities=entities)

    assert "ContextRouter" in entities
    assert result["intent"] == INTENT_CLARIFICATION
    assert result["signals"]["question_about_output"] is True
