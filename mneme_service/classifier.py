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
ENTITY_NEGATION_TERMS = ("not", "no", "without", "instead of", "remove", "delete", "never", "don't", "do not", "не", "нет")
REPLACEMENT_PATTERNS = (
    re.compile(r"\breplace\s+(.+?)\s+with\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE),
    re.compile(r"\buse\s+(.+?)\s+instead\s+of\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE),
    re.compile(r"\b(.+?)\s+instead\s+of\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE),
)
REMOVE_RE = re.compile(r"\b(?:remove|delete|without|no)\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE)
ADD_RE = re.compile(r"\b(?:add|include|use)\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE)
CONSTRAINT_RE = re.compile(r"\b(?:must|needs to|should|ensure|make it)\s+(.+?)(?=[,.;!?]|$)", re.IGNORECASE)
WORD_RE = re.compile(r"[\w']+", re.UNICODE)


def classify_intent(
    message: str,
    *,
    embedding_drift: float = 0.0,
    drift_score: float | None = None,
    drift_threshold: float = DRIFT_NEW_TASK_THRESHOLD,
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
    elif embedding_drift > drift_threshold or (drift_score is not None and drift_score > drift_threshold):
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
            "drift_score": drift_score if drift_score is not None else embedding_drift,
            "drift_threshold": drift_threshold,
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
    if not message or not active_entities:
        return False
    if replacement_modifiers(message, active_entities):
        return True
    words = normalized_words(message)
    if not words:
        return False
    for entity in active_entities:
        entity_words = normalized_words(entity)
        if not entity_words:
            continue
        width = len(entity_words)
        for index in range(0, len(words) - width + 1):
            if words[index : index + width] != entity_words:
                continue
            window = words[max(0, index - 5) : index]
            if contains_term(window, ENTITY_NEGATION_TERMS):
                return True
    return False


def classify_question_about_output(message: str, last_assistant_entities: Sequence[str]) -> bool:
    if not last_assistant_entities or not is_question(message):
        return False
    lowered = message.lower()
    return any(entity and entity.lower() in lowered for entity in last_assistant_entities)


def normalized_words(text: str) -> list[str]:
    return [match.group(0).strip("'").lower() for match in WORD_RE.finditer(text) if match.group(0).strip("'")]


def contains_term(words: Sequence[str], terms: Sequence[str]) -> bool:
    for term in terms:
        term_words = normalized_words(term)
        if not term_words:
            continue
        width = len(term_words)
        for index in range(0, len(words) - width + 1):
            if list(words[index : index + width]) == term_words:
                return True
    return False


def extract_entity_modifiers(message: str, active_entities: Sequence[str] | None = None) -> list[dict[str, Any]]:
    active = list(active_entities or [])
    modifiers: list[dict[str, Any]] = []
    claimed_spans: list[tuple[int, int]] = []

    for modifier in replacement_modifiers(message, active):
        modifiers.append(modifier)
        claimed_spans.append((modifier["source_span"]["start_char"], modifier["source_span"]["end_char"]))

    for match in REMOVE_RE.finditer(message):
        if span_overlaps(match.span(), claimed_spans):
            continue
        entity = matching_active_entity(match.group(1), active)
        if entity:
            modifiers.append(entity_modifier("REMOVE", entity, None, match.span(1)))

    for match in CONSTRAINT_RE.finditer(message):
        if span_overlaps(match.span(), claimed_spans):
            continue
        phrase = clean_entity_phrase(match.group(1))
        if phrase:
            modifiers.append(entity_modifier("CONSTRAINT", phrase, None, match.span(1)))

    for match in ADD_RE.finditer(message):
        if span_overlaps(match.span(), claimed_spans):
            continue
        entity = clean_entity_phrase(match.group(1))
        if entity:
            modifiers.append(entity_modifier("ADD", entity, None, match.span(1)))

    order = {"REPLACE": 0, "REMOVE": 1, "CONSTRAINT": 2, "ADD": 3}
    return sorted(modifiers, key=lambda item: (order[item["modifier_type"]], item["source_span"]["start_char"]))


def replacement_modifiers(message: str, active_entities: Sequence[str]) -> list[dict[str, Any]]:
    modifiers: list[dict[str, Any]] = []
    for pattern_index, pattern in enumerate(REPLACEMENT_PATTERNS):
        for match in pattern.finditer(message):
            if pattern_index == 0:
                old_raw, new_raw = match.group(1), match.group(2)
                old_span = match.span(1)
            else:
                new_raw, old_raw = match.group(1), match.group(2)
                old_span = match.span(2)
            entity = matching_active_entity(old_raw, active_entities)
            value = clean_entity_phrase(new_raw)
            if entity and value:
                modifiers.append(entity_modifier("REPLACE", entity, value, old_span))
    return modifiers


def matching_active_entity(candidate: str, active_entities: Sequence[str]) -> str | None:
    candidate_words = normalized_words(candidate)
    if not candidate_words:
        return None
    for entity in active_entities:
        if normalized_words(entity) == candidate_words:
            return entity
    return None


def clean_entity_phrase(value: str) -> str:
    return value.strip().strip(" \t\r\n,.;:!?()[]{}<>\"'")


def span_overlaps(span: tuple[int, int], claimed_spans: Sequence[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < claimed_end and end > claimed_start for claimed_start, claimed_end in claimed_spans)


def entity_modifier(modifier_type: str, entity: str, value: str | None, source_span: tuple[int, int]) -> dict[str, Any]:
    return {
        "schema_version": "mneme.entity_modifier.v0",
        "modifier_type": modifier_type,
        "entity": entity,
        "value": value,
        "source": "DETERMINISTIC_PATTERN",
        "source_span": {"start_char": source_span[0], "end_char": source_span[1]},
    }
