#!/usr/bin/env python3
"""M2: strict memory round-trip checks over an injected backend. No network.

A backend implements remember(text) -> record, search(query) -> response,
fetch(record_id) -> record|None, delete(record_id) -> response. Responses are
plain dicts; every shape anomaly is BLIND/UNVERIFIED, never an invented
empty collection. Same-process seed+verify can only ever yield
BOUNDARY_UNVERIFIED: a fresh client proves a fresh client, never a restarted
service. Real boundary proof needs backend.boundary_evidence() carrying an
observed service generation change.
"""
REQUIRED_RECORD_KEYS = {"id", "text"}


class WatchdogError(ValueError):
    pass


def _record_shape(record, where):
    if not isinstance(record, dict):
        raise WatchdogError("E_WATCHDOG_SHAPE: %s record is not an object" % (where,))
    missing = sorted(REQUIRED_RECORD_KEYS - set(record))
    if missing:
        raise WatchdogError("E_WATCHDOG_SHAPE: %s record missing: %s" % (where, ",".join(missing)))
    if not isinstance(record["id"], str) or not record["id"]:
        raise WatchdogError("E_WATCHDOG_SHAPE: %s record id unusable" % (where,))
    if not isinstance(record["text"], str):
        raise WatchdogError("E_WATCHDOG_SHAPE: %s record text unusable" % (where,))
    return record


def strict_roundtrip(backend, scope, canary_text):
    """Remember, search, verify exact id+content, delete, prove absence."""
    try:
        stored = _record_shape(backend.remember(canary_text), "remember")
        if stored["text"] != canary_text:
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_CONTENT: stored text differs"}
        response = backend.search(canary_text)
        if not isinstance(response, dict) or not isinstance(response.get("hits"), list):
            return {"verdict": "BLIND", "reason": "E_WATCHDOG_SHAPE: search response malformed"}
        for hit in response["hits"]:
            _record_shape(hit, "search-hit")
        matches = [h for h in response["hits"] if h.get("id") == stored["id"]]
        if not matches:
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_ABSENT: canary id not recalled"}
        if any(h.get("text") != canary_text for h in matches):
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_CONTENT: recalled text differs"}
        direct = backend.fetch(stored["id"])
        if direct is None:
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_ABSENT: direct fetch missed"}
        _record_shape(direct, "fetch")
        if direct["id"] != stored["id"]:
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_IDENTITY: fetched wrong record"}
        if direct["text"] != canary_text:
            return {"verdict": "FAILED", "reason": "E_WATCHDOG_CONTENT: fetched text differs"}
        deleted = backend.delete(stored["id"])
        if not isinstance(deleted, dict) or deleted.get("deleted") is not True:
            return {"verdict": "FAILED",
                    "reason": "E_WATCHDOG_DELETE_UNCONFIRMED",
                    "canary_id": stored["id"]}
        if backend.fetch(stored["id"]) is not None:
            return {"verdict": "FAILED",
                    "reason": "E_WATCHDOG_GHOST: direct fetch survives delete",
                    "canary_id": stored["id"]}
        again = backend.search(canary_text)
        if not isinstance(again, dict) or not isinstance(again.get("hits"), list):
            return {"verdict": "BLIND", "reason": "E_WATCHDOG_SHAPE: post-delete search malformed",
                    "canary_id": stored["id"]}
        for hit in again["hits"]:
            _record_shape(hit, "post-delete-search-hit")
        ghosts = [h for h in again["hits"] if h.get("id") == stored["id"]]
        if ghosts:
            return {"verdict": "FAILED",
                    "reason": "E_WATCHDOG_GHOST: search recalls deleted canary",
                    "canary_id": stored["id"]}
    except WatchdogError as exc:
        return {"verdict": "BLIND", "reason": str(exc)}
    except Exception as exc:
        return {"verdict": "BLIND",
                "reason": "E_WATCHDOG_TRANSPORT: %s: %s" % (type(exc).__name__, exc)}
    return {"verdict": "HEALTHY", "scope": scope, "boundary": "BOUNDARY_UNVERIFIED",
            "note": "same-process probe only; service restart not proven"}


def boundary_verdict(declared, evidence):
    """Map declared boundary + observed evidence to a persistence verdict."""
    if declared not in ("same_session", "service_restart", "datastore_restore"):
        raise WatchdogError("E_BOUNDARY_UNKNOWN: %r" % (declared,))
    if declared == "same_session":
        return "BOUNDARY_UNVERIFIED"
    if not isinstance(evidence, dict):
        return "BOUNDARY_UNVERIFIED"
    # Caller-supplied scalar values demonstrate only a claimed composition;
    # they do not observe a service or datastore boundary.  A future backend
    # adapter may supply an independently verifiable boundary artifact, but
    # this local watchdog has no such mechanism.
    if evidence.get("boundary_artifact_verified") is not True:
        return "BOUNDARY_UNVERIFIED"
    before, after = evidence.get("generation_before"), evidence.get("generation_after")
    for gen in (before, after):
        if isinstance(gen, bool) or not isinstance(gen, (str, int)) or gen == "":
            return "BOUNDARY_UNVERIFIED"
    if before == after:
        return "BOUNDARY_UNVERIFIED"
    if evidence.get("same_data_identity") is not True:
        return "BOUNDARY_UNVERIFIED"
    # No qualified live boundary observer exists in the offline release.
    # Even a caller-provided 'verified' boolean cannot substitute for one.
    return "BOUNDARY_UNVERIFIED"
