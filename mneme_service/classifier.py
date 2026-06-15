from __future__ import annotations

import re
from typing import Any, Sequence


INTENT_CONTINUATION = "CONTINUATION"
INTENT_SWITCH = "SWITCH"
INTENT_NEW_TASK = "NEW_TASK"
INTENT_CLARIFICATION = "CLARIFICATION"
DRIFT_NEW_TASK_THRESHOLD = 0.35

SWITCH_PATTERNS = (
    r"\bnew topic\b",
    r"\bswitch(?:ing)? to\b",
    r"\blet'?s switch\b",
    r"\bforget that\b",
    r"\binstead of that\b",
    r"давай переключим",
    r"переключимся",
    r"забудь это",
    r"новая тема",
)

EN_QUESTION_WORDS = {
    "what",
    "why",
    "how",
    "when",
    "where",
    "who",
    "which",
    "is",
    "are",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "would",
    "will",
}

RU_QUESTION_WORDS = {
    "что",
    "почему",
    "как",
    "когда",
    "где",
    "кто",
    "откуда",
    "зачем",
    "какой",
    "какая",
    "какое",
    "какие",
    "сколько",
    "куда",
}

_PROPER_NOUN_RE = re.compile(r"\b[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9_-]{2,}\b")
_BACKTICK_RE = re.compile(r"`([^`\n]{2,40})`")
_DQUOTE_RE = re.compile(r"\"([^\"\n]{2,40})\"")
_SQUOTE_RE = re.compile(r"'([^'\n]{2,40})'")
_PROPER_NOUN_STOPWORDS = {
    "the",
    "and",
    "this",
    "that",
    "you",
    "your",
    "это",
    "эта",
    "этот",
    "мы",
    "вы",
    "мой",
}
NEGATION_WORDS = ("not", "no", "never", "don't", "do not", "не", "нет")


def classify_intent(
    message: str,
    *,
    embedding_drift: float = 0.0,
    active_entities: Sequence[str] | None = None,
    last_assistant_entities: Sequence[str] | None = None,
) -> dict[str, Any]:
    explicit_switch = any(re.search(pattern, message, re.IGNORECASE) for pattern in SWITCH_PATTERNS)
    question = is_question(message)
    entity_contradiction = classify_entity_contradiction(message, active_entities or [])
    question_about_output = classify_question_about_output(message, last_assistant_entities or [])
    if explicit_switch:
        intent = INTENT_SWITCH
    elif entity_contradiction:
        intent = INTENT_SWITCH
    elif embedding_drift > DRIFT_NEW_TASK_THRESHOLD:
        intent = INTENT_NEW_TASK
    elif question:
        intent = INTENT_CLARIFICATION
    else:
        intent = INTENT_CONTINUATION
    return {
        "schema_version": "mneme.intent_classification.v0",
        "intent": intent,
        "signals": {
            "explicit_switch": explicit_switch,
            "entity_contradiction": entity_contradiction,
            "question": question,
            "question_about_output": question_about_output,
            "embedding_drift": embedding_drift,
        },
    }


def is_question(message: str) -> bool:
    stripped = message.strip()
    if not stripped:
        return False
    if stripped.endswith("?"):
        return True
    first = re.split(r"\s+", stripped, maxsplit=1)[0].lower().strip(".,!:;-—()[]{}'\"")
    return first in EN_QUESTION_WORDS or first in RU_QUESTION_WORDS


def extract_entities(text: str, *, max_entities: int = 30) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()

    def push(token: str) -> None:
        cleaned = token.strip().strip(".,;:!?()[]{}<>")
        if len(cleaned) < 2:
            return
        lowered = cleaned.lower()
        if lowered in _PROPER_NOUN_STOPWORDS or lowered in seen:
            return
        seen.add(lowered)
        found.append(cleaned)

    for pattern in (_BACKTICK_RE, _DQUOTE_RE, _SQUOTE_RE, _PROPER_NOUN_RE):
        for match in pattern.findall(text):
            push(match)
    return found[:max_entities]


def classify_entity_contradiction(message: str, active_entities: Sequence[str]) -> bool:
    lowered = message.lower()
    if not any(word in lowered for word in NEGATION_WORDS):
        return False
    return any(entity and entity.lower() in lowered for entity in active_entities)


def classify_question_about_output(message: str, last_assistant_entities: Sequence[str]) -> bool:
    if not last_assistant_entities or not is_question(message):
        return False
    lowered = message.lower()
    return any(entity and entity.lower() in lowered for entity in last_assistant_entities)
