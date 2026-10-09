#!/usr/bin/env python3
"""Phase 5: deterministic NER/event shadow extraction. No models, no merging.

Spans are heuristic candidates with byte ranges, ambiguity flags, negation
state and human_checked=False. review_span() flips the flag only through an
explicit reviewer call. Events carry observed/hypothetical/negated/quoted
modality from local markers. Nothing here writes the graph or merges
entities: output is a candidate list for supervised review. Stdlib only.
"""
import re

_MULTIWORD = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
_SINGLE = re.compile(r"\b([A-Z][a-z]{2,})\b")
_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_NEGATION = re.compile(r"\b(not|never|no|without|denies|denied|refused)\b", re.I)
_HYPOTHETICAL = re.compile(r"\b(might|may|could|would|perhaps|possibly|if)\b", re.I)
_QUOTE = re.compile(r"\"([^\"]+)\"")
_STOPWORDS = {"The", "A", "An", "She", "He", "They", "Monday", "Tuesday",
             "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def _sentence_bounds(text, pos):
    start = max(text.rfind(".", 0, pos), text.rfind("!", 0, pos),
                text.rfind("?", 0, pos)) + 1
    end = len(text)
    for mark in (".", "!", "?"):
        found = text.find(mark, pos)
        if found != -1:
            end = min(end, found + 1)
    return start, end


def _negated(text, start, end):
    begin, finish = _sentence_bounds(text, start)
    return _NEGATION.search(text[begin:finish]) is not None


def extract(text):
    """Candidate spans. Every span: text, byte range, kind, ambiguity,
    negation state, human_checked False."""
    if not isinstance(text, str):
        raise ValueError("E_NER_INPUT: text must be str")
    raw = text.encode("utf-8")

    def _bytes(start_char, end_char):
        return [len(text[:start_char].encode("utf-8")),
                len(text[:end_char].encode("utf-8"))]
    spans = []

    def span(match, kind):
        spans.append({"text": match.group(1),
                      "byte_range": _bytes(match.start(1), match.end(1)),
                      "kind": kind, "ambiguous": False,
                      "negated": _negated(text, match.start(1), match.end(1)),
                      "human_checked": False})
    for match in _MULTIWORD.finditer(text):
        span(match, "entity")
    singles = {}
    for match in _SINGLE.finditer(text):
        if match.group(1) in _STOPWORDS:
            continue
        covered = any(s <= match.start(1) and match.end(1) <= e
                      for s, e in [(m.start(1), m.end(1)) for m in _MULTIWORD.finditer(text)])
        if covered:
            continue
        singles.setdefault(match.group(1), []).append(match)
    for word, occurrences in singles.items():
        for occurrence in occurrences:
            spans.append({"text": word,
                          "byte_range": _bytes(occurrence.start(1), occurrence.end(1)),
                          "kind": "entity", "ambiguous": len(occurrences) > 1,
                          "negated": _negated(text, occurrence.start(1),
                                              occurrence.end(1)),
                          "human_checked": False})
    for match in _DATE.finditer(text):
        span(match, "date")
    for first in [s for s in spans if s["kind"] == "entity"]:
        for second in [s for s in spans if s["kind"] == "entity" and s is not first]:
            if first["text"] in second["text"] or second["text"] in first["text"]:
                first["ambiguous"] = True
                second["ambiguous"] = True
    spans.sort(key=lambda s: s["byte_range"][0])
    for span_record in spans:
        start, end = span_record["byte_range"]
        if raw[start:end].decode("utf-8", errors="replace") != span_record["text"]:
            raise ValueError("E_NER_SPAN: byte range mismatch")
    return spans


def review_span(span_record, approved, reviewer="human"):
    """Explicit human review flips human_checked. Nothing implicit."""
    if not isinstance(span_record, dict) or "text" not in span_record:
        raise ValueError("E_NER_SPAN_RECORD: span record required")
    if approved is not True:
        raise ValueError("E_NER_APPROVAL: approval must be explicit True")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("E_NER_REVIEWER: reviewer identity required")
    updated = dict(span_record, human_checked=True, reviewer=reviewer)
    return updated


def extract_events(text):
    """Event candidates with modality. Quoted speech is quoted, never observed."""
    if not isinstance(text, str):
        raise ValueError("E_EVENT_INPUT: text must be str")
    quoted = [(m.start(), m.end()) for m in _QUOTE.finditer(text)]
    events = []
    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[a-z]+){0,4}\s+(?:meet|meets|vote|votes|signed|sign|decided|decide|announced|announce|record|records))\b", text):
        start = match.start(1)
        begin, _ = _sentence_bounds(text, start)
        clause = text[begin:start + len(match.group(1)) + 1]
        modality = "quoted" if any(s <= start < e for s, e in quoted) else "observed"
        if _HYPOTHETICAL.search(clause):
            modality = "hypothetical"
        if _NEGATION.search(text[begin:start]):
            modality = "negated"
        events.append({"text": match.group(1),
                       "byte_range": [len(text[:start].encode("utf-8")),
                                      len(text[:start + len(match.group(1))].encode("utf-8"))],
                       "type": "event", "actors": [], "modality": modality,
                       "human_checked": False})
    for event in events:
        start, end = event["byte_range"]
        if text.encode("utf-8")[start:end].decode("utf-8", errors="replace") != event["text"]:
            raise ValueError("E_NER_SPAN: event byte range mismatch")
    return events
