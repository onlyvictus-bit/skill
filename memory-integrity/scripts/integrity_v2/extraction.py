#!/usr/bin/env python3
"""M2: extraction contract shell. No extractors run here.

Every rich-document conversion is an extraction EVENT with a frozen
extractor identity, an expected original inventory, produced elements, and
diagnostics. Direct text takes the EXACT_TEXT route only when original and
canonical identities match byte-for-byte. Unknown stays UNKNOWN; COMPLETE
requires a reconciled inventory, never parser success alone.

The state vocabulary is local but conformance-tested against the engine's
capabilities output: any drift fails loudly instead of forking meaning.
"""
EXTRACTION_STATES = (
    "EXACT_TEXT",
    "INVENTORY_CHECKED",
    "VERIFIED_TO_DECLARED_REFERENCE",
    "PARTIAL",
    "UNSUPPORTED",
    "UNKNOWN",
    "ERROR",
)

PROFILE_KEYS = {"schema_version", "extractor", "version", "config_digest",
                "supported_features"}
EVENT_KEYS = {"schema_version", "source_digest", "canonical_digest", "extractor",
              "extractor_version", "config_digest", "expected_inventory",
              "produced_elements", "diagnostics", "state"}


class ExtractionError(ValueError):
    pass


def validate_profile(profile):
    if not isinstance(profile, dict):
        raise ExtractionError("E_SCHEMA_TYPE: profile must be an object")
    unknown = sorted(set(profile) - PROFILE_KEYS)
    if unknown:
        raise ExtractionError("E_SCHEMA_FIELD: profile unsupported field(s): %s"
                              % (", ".join(unknown)))
    missing = sorted(PROFILE_KEYS - set(profile))
    if missing:
        raise ExtractionError("E_SCHEMA_REQUIRED: profile missing: %s" % (", ".join(missing)))
    if profile.get("schema_version") != 2:
        raise ExtractionError("E_SCHEMA_VERSION: profile schema must be 2")
    for key in ("extractor", "version", "config_digest"):
        value = profile.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ExtractionError("E_SCHEMA_VALUE: profile.%s must be non-empty" % (key,))
    if not isinstance(profile.get("supported_features"), list):
        raise ExtractionError("E_SCHEMA_TYPE: profile.supported_features must be a list")
    return profile


def direct_text_event(original_digest, canonical_digest):
    """EXACT_TEXT only on byte-identical original/canonical. Else UNKNOWN."""
    if isinstance(original_digest, str) and original_digest \
            and original_digest == canonical_digest:
        return {"schema_version": 2, "route": "direct-text", "state": "EXACT_TEXT"}
    return {"schema_version": 2, "route": "direct-text", "state": "UNKNOWN",
            "reason": "original and canonical identities differ; rich route required"}


def validate_event(event):
    if not isinstance(event, dict):
        raise ExtractionError("E_SCHEMA_TYPE: event must be an object")
    unknown = sorted(set(event) - EVENT_KEYS)
    if unknown:
        raise ExtractionError("E_SCHEMA_FIELD: event unsupported field(s): %s"
                              % (", ".join(unknown)))
    missing = sorted(EVENT_KEYS - set(event))
    if missing:
        raise ExtractionError("E_SCHEMA_REQUIRED: event missing: %s" % (", ".join(missing)))
    if event.get("schema_version") != 2:
        raise ExtractionError("E_SCHEMA_VERSION: event schema must be 2")
    if event.get("state") not in EXTRACTION_STATES:
        raise ExtractionError("E_SCHEMA_ENUM: unknown extraction state %r" % (event.get("state"),))
    expected = event.get("expected_inventory") or {}
    produced = event.get("produced_elements") or {}
    if not isinstance(expected, dict) or not isinstance(produced, dict):
        raise ExtractionError("E_EXTRACTION_COUNTS: inventories must be objects")
    if event["state"] == "EXACT_TEXT":
        for key in ("source_digest", "canonical_digest"):
            value = event.get(key)
            if not isinstance(value, str) or not value:
                raise ExtractionError("E_EXTRACTION_IDENTITY: EXACT_TEXT needs %s" % (key,))
        if event["source_digest"] != event["canonical_digest"]:
            raise ExtractionError("E_EXTRACTION_IDENTITY: EXACT_TEXT digests differ")
    if event["state"] == "INVENTORY_CHECKED" or event["state"] == "VERIFIED_TO_DECLARED_REFERENCE":
        if not expected or not produced:
            raise ExtractionError("E_EXTRACTION_EMPTY: claimed inventory needs non-empty expected and produced maps")
        missing_parts = [k for k in expected if k not in produced]
        if missing_parts:
            raise ExtractionError("E_EXTRACTION_GAP: claimed %s but missing inventory: %s"
                                  % (event["state"], ", ".join(sorted(missing_parts))))
        for key, want in expected.items():
            got = produced.get(key)
            if isinstance(want, int) and got != want:
                raise ExtractionError("E_EXTRACTION_SHORTFALL: %s expected %r, produced %r"
                                      % (key, want, got))
        diagnostics = event.get("diagnostics") or []
        if not isinstance(diagnostics, (list, tuple, dict)):
            raise ExtractionError("E_EXTRACTION_DIAGNOSTICS: diagnostics must be a collection")
        items = diagnostics.values() if isinstance(diagnostics, dict) else diagnostics
        errors = [d for d in items if isinstance(d, str) and d.upper().startswith("ERROR")]
        if errors:
            raise ExtractionError("E_EXTRACTION_ERROR: error diagnostics prohibit a complete claim")
    return event


def readiness_from_state(state):
    """Map an extraction state to a readiness layer value."""
    if state in ("EXACT_TEXT", "INVENTORY_CHECKED", "VERIFIED_TO_DECLARED_REFERENCE"):
        return "READY"
    if state in ("PARTIAL", "UNKNOWN"):
        return "PARTIAL"
    return "BLOCKED"
