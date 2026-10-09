#!/usr/bin/env python3
"""Phase 2: canonical truth maintenance over an append-only event log.

One registry: assertions carry OBSERVED/DERIVED/INFERRED/HYPOTHESIS claims,
CURRENT/RETRACTED/CONFLICTED/UNKNOWN truth, bitemporal valid/known windows,
and provenance. Retractions cascade to derived descendants, preserve history,
and are idempotent. Replay is deterministic: duplicate operation IDs apply
once. Entity merges are explicit and reversible; proximity never auto-merges.
Fable decisions project read-only; contradictions flag review, never override.
Standard library only.
"""
CLAIM_TYPES = ("OBSERVED", "DERIVED", "INFERRED", "HYPOTHESIS")
TRUTH_STATES = ("CURRENT", "RETRACTED", "CONFLICTED", "UNKNOWN")
ANTONYMS = (("up", "down"), ("allow", "deny"), ("true", "false"),
            ("always", "never"), ("accept", "reject"), ("open", "closed"))


class TruthError(ValueError):
    pass


def new_store():
    return {"events": [], "seen_ops": [], "claims": {}, "edges": [],
            "entities": {}, "matches": [], "merges": []}


def events(store):
    return list(store["events"])


def event_count(store):
    return len(store["events"])


def history(store, ident):
    return [e for e in store["events"]
            if e.get("id") == ident
            or ident in e.get("premises", [])
            or ident in e.get("pair", [])]


def status(store, ident):
    claim = store["claims"].get(ident)
    if claim is None:
        raise TruthError("E_TRUTH_UNKNOWN: %s" % (ident,))
    return claim["truth"]


def _record(store, event):
    if event.get("op_id") in store["seen_ops"]:
        return store, False
    store = {"events": store["events"] + [event],
             "seen_ops": store["seen_ops"] + [event["op_id"]],
             "claims": {k: dict(v) for k, v in store["claims"].items()},
             "edges": list(store["edges"]),
             "entities": {k: dict(v) for k, v in store["entities"].items()},
             "matches": list(store["matches"]),
             "merges": list(store["merges"])}
    return store, True


def _check_claim(record):
    if not isinstance(record, dict):
        raise TruthError("E_TRUTH_RECORD: assertion must be an object")
    if not isinstance(record.get("id"), str) or not record["id"].strip():
        raise TruthError("E_TRUTH_ID: assertion id required")
    claim = record.get("claim", {})
    if claim.get("type") not in CLAIM_TYPES:
        raise TruthError("E_TRUTH_CLAIM: type must be one of %s" % (sorted(CLAIM_TYPES),))
    if not isinstance(claim.get("text"), str) or not claim["text"].strip():
        raise TruthError("E_TRUTH_TEXT: claim text required")
    prov = record.get("provenance", {})
    for key in ("source_digest", "generation", "producer"):
        if not isinstance(prov.get(key), str) or not prov[key].strip():
            raise TruthError("E_TRUTH_PROVENANCE: %s required" % (key,))


def assert_claim(store, record, op_id, premises=(), valid_from=None,
                 valid_to=None, known_from=None, known_to=None):
    _check_claim(record)
    store, fresh = _record(store, {"op": "ASSERT", "op_id": op_id,
                                   "id": record["id"], "record": record,
                                   "premises": list(premises),
                                   "valid_from": valid_from or "",
                                   "valid_to": valid_to or "~",
                                   "known_from": known_from or "",
                                   "known_to": known_to or "~"})
    if not fresh:
        return store
    store["claims"][record["id"]] = {
        "truth": "CURRENT", "record": record, "premises": list(premises),
        "valid_from": valid_from or "", "valid_to": valid_to or "~",
        "known_from": known_from or "", "known_to": known_to or "~"}
    return store


def _descendants(store, ident):
    children = {cid for cid, c in store["claims"].items()
                if ident in c.get("premises", [])}
    changed = True
    while changed:
        changed = False
        for cid, c in store["claims"].items():
            if cid not in children and any(p in children for p in c.get("premises", [])):
                children.add(cid)
                changed = True
    return children


def retract(store, ident, reason, op_id):
    if not (reason or "").strip():
        raise TruthError("E_TRUTH_REASON: retraction needs a reason")
    if ident not in store["claims"]:
        raise TruthError("E_TRUTH_UNKNOWN: %s" % (ident,))
    store, fresh = _record(store, {"op": "RETRACT", "op_id": op_id,
                                   "id": ident, "reason": reason})
    if not fresh:
        return store, []
    if store["claims"][ident]["truth"] == "RETRACTED":
        return store, []
    affected = [ident] + sorted(_descendants(store, ident))
    for cid in affected:
        store["claims"][cid]["truth"] = "RETRACTED"
    return store, affected


def contradicts(store, first, second, op_id):
    for ident in (first, second):
        if ident not in store["claims"]:
            raise TruthError("E_TRUTH_UNKNOWN: %s" % (ident,))
    store, fresh = _record(store, {"op": "CONTRADICT", "op_id": op_id,
                                   "pair": [first, second]})
    if not fresh:
        return store
    store["edges"].append({"predicate": "CONTRADICTS", "subject": first,
                           "object": second})
    for ident in (first, second):
        if store["claims"][ident]["truth"] == "CURRENT":
            store["claims"][ident]["truth"] = "CONFLICTED"
    return store


def correct(store, ident, note, valid_from, valid_to, op_id):
    if ident not in store["claims"]:
        raise TruthError("E_TRUTH_UNKNOWN: %s" % (ident,))
    store, fresh = _record(store, {"op": "CORRECT", "op_id": op_id,
                                   "id": ident, "note": note,
                                   "valid_from": valid_from, "valid_to": valid_to})
    if not fresh:
        return store
    store["claims"][ident]["valid_from"] = valid_from
    store["claims"][ident]["valid_to"] = valid_to
    return store


def _visible(store, moment, window):
    moment = str(moment)
    return sorted(cid for cid, c in store["claims"].items()
                  if c["truth"] == "CURRENT"
                  and c[window[0]] <= moment
                  and moment < c[window[1]])


def as_valid_at(store, moment):
    return _visible(store, moment, ("valid_from", "valid_to"))


def known_as_of(store, moment):
    return _visible(store, moment, ("known_from", "known_to"))


def register_entity(store, eid, aliases, op_id):
    if not isinstance(eid, str) or not eid.strip():
        raise TruthError("E_ENTITY_ID: entity id required")
    if not isinstance(aliases, list) or not aliases:
        raise TruthError("E_ENTITY_ALIASES: aliases required")
    store, fresh = _record(store, {"op": "ENTITY_REGISTER", "op_id": op_id,
                                   "id": eid, "aliases": list(aliases)})
    if not fresh:
        return store
    store["entities"][eid] = {"aliases": list(aliases), "canonical": eid}
    return store


def possible_match(store, first, second, score, op_id):
    for eid in (first, second):
        if eid not in store["entities"]:
            raise TruthError("E_ENTITY_UNKNOWN: %s" % (eid,))
    store, fresh = _record(store, {"op": "ENTITY_MATCH", "op_id": op_id,
                                   "pair": [first, second], "score": score})
    if fresh:
        store["matches"].append({"pair": [first, second], "score": score})
    return store


def merge_entities(store, canonical, other, kind, op_id):
    if kind != "same-as":
        raise TruthError("E_ENTITY_KIND: only explicit same-as merges; "
                         "possible-match never auto-merges")
    for eid in (canonical, other):
        if eid not in store["entities"]:
            raise TruthError("E_ENTITY_UNKNOWN: %s" % (eid,))
    store, fresh = _record(store, {"op": "ENTITY_MERGE", "op_id": op_id,
                                   "id": other, "canonical": canonical,
                                   "kind": kind})
    if fresh:
        store["merges"].append({"other": other, "canonical": canonical})
        store["entities"][other]["canonical"] = canonical
    return store


def unmerge_entities(store, canonical, other, op_id):
    store, fresh = _record(store, {"op": "ENTITY_UNMERGE", "op_id": op_id,
                                   "id": other, "canonical": canonical})
    if fresh:
        store["entities"][other]["canonical"] = other
    return store


def canonical_of(store, eid):
    if eid not in store["entities"]:
        raise TruthError("E_ENTITY_UNKNOWN: %s" % (eid,))
    return store["entities"][eid]["canonical"]


def _antonym_hit(first, second):
    first_words = set(first.lower().split())
    second_words = set(second.lower().split())
    return any(a in first_words and b in second_words
               or b in first_words and a in second_words
               for a, b in ANTONYMS)


def project_fable_decisions(store, decisions):
    """Read-only projection of Fable decisions. Returns (view, writes).

    Writes are always []: projection never mutates the store or Fable.
    Decisions contradicting CURRENT claims are flagged for review, never
    auto-overridden.
    """
    nodes = [{"id": d["id"], "kind": "Decision",
              "rationale": d.get("rationale", ""),
              "evidence": list(d.get("evidence", [])),
              "time": d.get("time", ""),
              "superseded_by": d.get("superseded_by")} for d in decisions]
    flags = []
    current = [(cid, c["record"]["claim"]["text"]) for cid, c in store["claims"].items()
               if c["truth"] == "CURRENT"]
    for node in nodes:
        if not node["evidence"] or any(
                _antonym_hit(node["rationale"], text) for _, text in current):
            flags.append({"id": node["id"], "review": "contradiction-or-ungrounded"})
    return {"nodes": nodes, "review_flags": flags}, []


def replay(event_list):
    store = new_store()
    for event in event_list:
        op = event.get("op")
        if op == "ASSERT":
            store = assert_claim(store, event["record"], event["op_id"],
                                 premises=event.get("premises", []),
                                 valid_from=event.get("valid_from") or None,
                                 valid_to=(None if event.get("valid_to") == "~"
                                           else event.get("valid_to")),
                                 known_from=event.get("known_from") or None,
                                 known_to=(None if event.get("known_to") == "~"
                                           else event.get("known_to")))
        elif op == "RETRACT":
            store, _ = retract(store, event["id"], event.get("reason", "replay"),
                               event["op_id"])
        elif op == "CONTRADICT":
            store = contradicts(store, *event["pair"], event["op_id"])
        elif op == "CORRECT":
            store = correct(store, event["id"], event.get("note", ""),
                            event["valid_from"], event["valid_to"], event["op_id"])
        elif op == "ENTITY_REGISTER":
            store = register_entity(store, event["id"], event["aliases"], event["op_id"])
        elif op == "ENTITY_MATCH":
            store = possible_match(store, *event["pair"], event.get("score", 0),
                                   event["op_id"])
        elif op == "ENTITY_MERGE":
            store = merge_entities(store, event["canonical"], event["id"],
                                   "same-as", event["op_id"])
        elif op == "ENTITY_UNMERGE":
            store = unmerge_entities(store, event["canonical"], event["id"],
                                     event["op_id"])
        else:
            raise TruthError("E_REPLAY_OP: unknown op %r" % (op,))
    return store
