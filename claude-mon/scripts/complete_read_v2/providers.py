#!/usr/bin/env python3
"""M4b: provider adapter protocol. Offline only: no live dispatch exists.

An adapter turns prepared bytes into an observed response. Every response
carries its evidence class: TEST_ONLY adapters can never satisfy a live
gate, and nothing here performs network I/O. The first real provider path
is M4c work and must implement this same protocol plus authenticated
transport, usage capture, and provider request/response IDs.
"""
import hashlib
import json

from . import budget

TERMINAL_STATES = ("ok", "truncated", "refused", "error", "unknown")

ADAPTER_IDENTITY_KEYS = {"adapter", "adapter_version", "evidence_class", "live"}


class AdapterError(ValueError):
    pass


def prepared_request(work_item_id, task_digest, primary_unit_ids, task_spec_digest, model):
    """Canonical request bytes + digest. Model profile validated, never guessed.

    NOTE: this metadata-only form does not establish that source contents
    were delivered. Live paths must use build_complete_request(), whose
    digest binds the actual measured material.
    """
    try:
        budget.validate_profile(model)
    except budget.BudgetError as exc:
        raise AdapterError("E_REQUEST_PROFILE: %s" % (exc,))
    if not primary_unit_ids:
        raise AdapterError("E_REQUEST_EMPTY: request needs primary units")
    if len(set(primary_unit_ids)) != len(primary_unit_ids):
        raise AdapterError("E_REQUEST_DUPLICATE: duplicate primary unit ids")
    for key, value in (("task_digest", task_digest), ("task_spec_digest", task_spec_digest)):
        if not isinstance(value, str) or not value.strip():
            raise AdapterError("E_REQUEST_VALUE: %s must be non-empty" % (key,))
    body = {"schema_version": 2, "work_item_id": work_item_id, "task_digest": task_digest,
            "primary_unit_ids": list(primary_unit_ids),
            "task_spec_digest": task_spec_digest, "model": dict(model)}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


def build_complete_request(work_item_id, task_digest, units_text, instructions,
                         result_schema, context_sections, task_spec_digest,
                         model, counter=None, source_proof=None):
    """One request representation containing all model-visible material.

    units_text: {unit_id: text}. instructions/result_schema/context_sections
    are measured with the profile's counting method and the measurement
    (with method provenance) is embedded. The digest binds material +
    measurement + model profile: any change invalidates measurement and
    approval. Returns (raw_bytes, digest, measurement).
    """
    try:
        budget.validate_profile(model)
    except budget.BudgetError as exc:
        raise AdapterError("E_REQUEST_PROFILE: %s" % (exc,))
    if not isinstance(units_text, dict) or not units_text:
        raise AdapterError("E_REQUEST_EMPTY: request needs units with text")
    for ident, text in units_text.items():
        if not isinstance(ident, str) or not ident.strip():
            raise AdapterError("E_REQUEST_ID: unit id must be non-empty")
        if not isinstance(text, str):
            raise AdapterError("E_REQUEST_TEXT: unit %r text must be str" % (ident,))
    if not isinstance(instructions, str) or not instructions.strip():
        raise AdapterError("E_REQUEST_VALUE: instructions must be non-empty")
    sections = {"instructions": instructions,
                "result_schema": json.dumps(result_schema, sort_keys=True)}
    sections.update({"source_%s" % ident: text for ident, text in sorted(units_text.items())})
    sections.update({"context_%s" % name: text for name, text in sorted(context_sections.items())})
    try:
        measurement = budget.measure_request(model, sections, counter)
    except budget.BudgetError as exc:
        raise AdapterError("E_REQUEST_MEASURE: %s" % (exc,))
    body = {"schema_version": 2, "kind": "complete-request", "work_item_id": work_item_id,
            "task_digest": task_digest, "task_spec_digest": task_spec_digest,
            "primary_unit_ids": sorted(units_text),
            "model": dict(model),
            "encoding": model["encoding"], "measurement": measurement,
            "source_proof": source_proof,
            "materials": sections}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    # Final size/digest cannot live inside the bytes they describe without a
    # circular claim.  The caller re-derives this proof before dispatch.
    measurement = dict(measurement, serialized_characters=len(raw),
                       final_payload_bytes=len(raw),
                       final_payload_sha256=hashlib.sha256(raw).hexdigest(),
                       scope="local-text-sections-plus-final-serialized-size-excluding-provider-framing")
    return raw, hashlib.sha256(raw).hexdigest(), measurement


def final_payload_measurement(raw, model=None, counter=None):
    """External, non-self-referential measurement of exact request bytes.

    When a profile is supplied, this is the authoritative full-payload budget:
    it counts the serialized UTF-8 request itself (not a sum of sections) and
    reserves the profile output before any adapter boundary.
    """
    if not isinstance(raw, bytes):
        raise AdapterError("E_FINAL_PAYLOAD_TYPE: request must be bytes")
    out = {"final_payload_bytes": len(raw),
           "final_payload_sha256": hashlib.sha256(raw).hexdigest()}
    if model is not None:
        try:
            budget.validate_profile(model)
            text = raw.decode("utf-8")
            input_tokens, method = budget.count_tokens(text, model["encoding"], counter)
        except (budget.BudgetError, UnicodeDecodeError) as exc:
            raise AdapterError("E_FINAL_PAYLOAD_MEASURE: %s" % (exc,))
        total = input_tokens + model["output_limit"]
        if total > model["context_limit"]:
            raise AdapterError("E_FINAL_PAYLOAD_BUDGET: input %d + output %d exceeds context %d" %
                               (input_tokens, model["output_limit"], model["context_limit"]))
        profile_raw = json.dumps(model, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8")
        out.update({"schema_version": 1, "request_digest": out["final_payload_sha256"],
                    "profile_digest": hashlib.sha256(profile_raw).hexdigest(),
                    "input_tokens": input_tokens, "output_tokens": model["output_limit"],
                    "context_limit": model["context_limit"], "counting_method": method,
                    "evidence_class": "TEST_ONLY" if counter is not None else "LOCAL_MEASURED"})
    return out


def validate_response(response, expected_unit_ids, raw_digest_actual=None):
    """Check an observed response. Returns (accepted_bool, reason).

    For ok: results must be a mapping whose keys are EXACTLY the expected
    unit ids (no missing, no extra, no substitutes). If raw_digest_actual is
    given (digest of the stored raw bytes), a declared raw_digest must match
    it; responses without result payloads never pass.
    """
    if not isinstance(response, dict):
        return False, "E_RESPONSE_TYPE: response must be an object"
    state = response.get("terminal_state")
    if state not in TERMINAL_STATES:
        return False, "E_RESPONSE_STATE: unknown terminal state %r" % (state,)
    if response.get("evidence_class") not in ("MANUAL_REPORTED", "TEST_ONLY",
                                              "HOST_OBSERVED", "TRANSPORT_OBSERVED"):
        return False, "E_RESPONSE_EVIDENCE: unknown evidence class"
    if state != "ok":
        return False, "E_RESPONSE_STATE: non-ok terminal state %s" % (state,)
    results = response.get("results")
    if not isinstance(results, dict) or not results:
        return False, "E_RESPONSE_RESULTS: ok response needs a non-empty results mapping"
    if sorted(results.keys()) != sorted(expected_unit_ids):
        return False, ("E_RESPONSE_UNITS: result ids %s != expected %s"
                        % (sorted(results.keys()), sorted(expected_unit_ids)))
    for ident in sorted(results):
        value = results[ident]
        if value is None:
            return False, "E_RESPONSE_NULL: unit %s has a null result" % (ident,)
        if isinstance(value, str) and not value.strip():
            return False, "E_RESPONSE_EMPTY: unit %s has an empty result" % (ident,)
        if isinstance(value, dict) and not value:
            return False, "E_RESPONSE_EMPTY: unit %s has an empty result" % (ident,)
    declared = response.get("raw_digest")
    if raw_digest_actual is None or len(raw_digest_actual) != 64:
        return False, "E_RESPONSE_DIGEST: wrapper-computed raw digest missing"
    if declared is not None and declared != raw_digest_actual:
        return False, "E_RESPONSE_DIGEST_SPOOF: declared digest differs from stored bytes"
    return True, ""


class ProviderAdapter:
    """Protocol: dispatch(prepared_bytes) -> observed response dict."""

    adapter_name = "base"
    adapter_version = "0"
    evidence_class = "MANUAL_REPORTED"
    live = False

    def capabilities(self):
        return {"adapter": self.adapter_name, "adapter_version": self.adapter_version,
                "evidence_class": self.evidence_class, "live": self.live}

    def dispatch(self, prepared_bytes):
        raise AdapterError("E_ADAPTER_ABSTRACT: base adapter dispatches nothing")


class TestOnlyAdapter(ProviderAdapter):
    """Scripted responses for offline tests. TEST_ONLY, live=False, always.

    script: list of ("ok", {unit_id: result}) | ("truncate",) | ("refuse", reason) |
    ("error", reason). Any request with live=True is refused outright.
    """

    adapter_name = "test-only"
    adapter_version = "1"
    evidence_class = "TEST_ONLY"

    def __init__(self, script):
        self.script = list(script)

    def dispatch(self, prepared_bytes, live=False):
        if live:
            raise AdapterError("E_ADAPTER_LIVE: test-only adapter never dispatches live")
        try:
            request = json.loads(prepared_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise AdapterError("E_REQUEST_DECODE: %s" % (exc,))
        expected = request.get("primary_unit_ids", [])
        if not self.script:
            raise AdapterError("E_SCRIPT_EXHAUSTED: no scripted behavior left")
        kind, payload = self.script.pop(0)
        base = dict(self.capabilities())
        # No raw_digest here: the trusted wrapper stores the raw response bytes
        # and supplies the digest it computed itself. An adapter must never
        # self-certify its bytes.
        if kind == "ok":
            if sorted((payload or {}).keys()) != sorted(expected):
                raise AdapterError("E_SCRIPT_UNITS: scripted ids do not match request")
            base.update({"terminal_state": "ok", "unit_ids": list(expected),
                         "results": dict(payload)})
            return base
        if kind == "truncate":
            base.update({"terminal_state": "truncated", "unit_ids": []})
            return base
        if kind == "refuse":
            base.update({"terminal_state": "refused", "unit_ids": [],
                         "refusal": str(payload)})
            return base
        base.update({"terminal_state": "error", "unit_ids": [],
                     "error": str(payload)})
        return base
