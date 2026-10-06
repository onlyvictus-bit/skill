#!/usr/bin/env python3
"""M4: offline attempt driver + unified dispatch path. No live dispatch exists.

prepare builds the unified complete request (material + measurement +
digest); the same bytes are approved and dispatched. dispatch() drives the
legacy scripted FakeProvider path. dispatch_via_adapter() drives the
provider-adapter protocol with single-use approvals and wrapper-computed
response digests. dispatch_live() raises unconditionally.
"""
import hashlib
import json
import os

from . import artifacts, budget, ledger, partition


class ProviderError(Exception):
    pass


class ProviderRefusal(Exception):
    pass


class ProviderTruncated(Exception):
    def __init__(self, partial):
        super().__init__("truncated response")
        self.partial = partial


class LiveNotImplemented(NotImplementedError):
    pass


class FakeProvider:
    """Deterministic scripted provider. TEST_ONLY: never live evidence.

    script: list of ("ok", bytes) | ("truncate", bytes) | ("refuse", str) |
    ("error", str). Exhausted script raises ProviderError.
    """

    def __init__(self, script):
        self.script = list(script)

    def dispatch(self, request_bytes):
        if not self.script:
            raise ProviderError("script exhausted")
        kind, payload = self.script.pop(0)
        if kind == "ok":
            return payload
        if kind == "truncate":
            raise ProviderTruncated(payload)
        if kind == "refuse":
            raise ProviderRefusal(payload)
        raise ProviderError(payload)


def prepare(db, artifacts_dir, work_item_id, task_digest, units_text, instructions,
            result_schema, context_sections, task_spec_digest, model, counter=None,
            *, manifest=None, source_bytes=None, coordination_context=None):
    """Prepare from the unified complete request: material, measurement, digest.

    The same bytes are measured, approved, and dispatched. Everything the
    model will see is inside the digest; IDs alone never constitute a request.
    """
    from . import providers, results
    item = db.execute("SELECT * FROM work_items WHERE id=?", (work_item_id,)).fetchone()
    if item is None:
        raise ledger.LedgerError("E_PREPARE_UNKNOWN: no work item %s" % (work_item_id,))
    if task_digest != item["task_digest"]:
        raise ledger.LedgerError("E_PREPARE_TASK: request task %r != work item task %r"
                                 % (task_digest, item["task_digest"]))
    from . import coordination
    # Before any attempt or CAS write: coordinated work cannot be downgraded
    # by omitting context or by using an otherwise legacy entrypoint.
    coordinated = coordination.guard(db, work_item_id, artifacts_dir, coordination_context, "prepare")
    if coordinated["coordinated"]:
        policy = coordination._load(db,work_item_id)[0]
        if manifest is None or source_bytes is None or manifest.get("source_digest") != policy["source_digest"] or hashlib.sha256(json.dumps(model,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest() != policy["profile_digest"] or sorted(units_text) != sorted(u["id"] for u in manifest["units"]):
            raise ledger.LedgerError("E_COORD_PREPARE_BASIS: actual source/profile/complete scope differ from frozen policy")
        context_sections = dict(context_sections)
        context_sections["coordination_basis"] = json.dumps(coordinated["basis"],sort_keys=True,separators=(",",":"),ensure_ascii=False)
    latest = ledger._latest_attempt(db, work_item_id)
    if latest is not None:
        if latest["state"] == "DELIVERY_UNKNOWN" and not _retry_authorized(
                db, work_item_id, latest["id"]):
            raise ledger.LedgerError("E_RECOVERY_UNKNOWN: %s needs an explicit retry decision"
                                     % (latest["id"],))
        revoked = db.execute("SELECT revoked FROM accepted WHERE attempt_id=?", (latest["id"],)).fetchone()
        if latest["state"] in ("PREPARED", "AWAITING_APPROVAL", "DISPATCHING",
                               "RESPONSE_SAVED", "VALIDATED") or \
                (latest["state"] == "ACCEPTED" and (revoked is None or not revoked["revoked"])):
            raise ledger.LedgerError("E_RECOVERY_RESUME: %s is %s; continue it, do not prepare again"
                                     % (latest["id"], latest["state"]))
    source_proof = None
    if manifest is not None or source_bytes is not None:
        if manifest is None or source_bytes is None:
            raise ledger.LedgerError("E_PREPARE_SOURCE: manifest and source bytes are required together")
        errors = partition.validate_manifest(source_bytes, manifest)
        if errors:
            raise ledger.LedgerError("E_PREPARE_SOURCE: %s" % errors[0])
        if manifest.get("source_id") != item["source_id"]:
            raise ledger.LedgerError("E_PREPARE_SOURCE: manifest source does not match work item")
        table = {unit["id"]: unit for unit in manifest["units"]}
        primary_hashes = {}
        for unit_id, text in units_text.items():
            unit = table.get(unit_id)
            if unit is None or source_bytes[unit["range"][0]:unit["range"][1]].decode("utf-8") != text:
                raise ledger.LedgerError("E_PREPARE_SOURCE: submitted unit %s differs from frozen source" % unit_id)
            primary_hashes[unit_id] = unit["sha256"]
        source_artifact = artifacts.store_bytes(artifacts_dir, source_bytes)
        manifest_raw = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8")
        manifest_artifact = artifacts.store_bytes(artifacts_dir, manifest_raw)
        source_proof = {"source_id": item["source_id"], "source_digest": manifest["source_digest"],
                        "manifest_digest": manifest["manifest_digest"],
                        "source_artifact_digest": source_artifact,
                        "manifest_artifact_digest": manifest_artifact,
                        "primary_unit_hashes": primary_hashes}
    raw, digest, _measurement = providers.build_complete_request(
        work_item_id, task_digest, units_text, instructions, result_schema,
        context_sections, task_spec_digest, model, counter, source_proof=source_proof)
    exact_measurement = providers.final_payload_measurement(raw, model, counter)
    stored = artifacts.store_bytes(artifacts_dir, raw)
    if stored != digest:
        raise ledger.LedgerError("E_REQUEST_STORE: stored digest mismatch")
    attempt_id = ledger.begin_attempt(db, work_item_id)
    ledger.transition(db, attempt_id, "PREPARED", request_digest=digest,
                      coordination_context={"context":coordination_context,"artifacts_dir":str(artifacts_dir)})
    measurement_raw = json.dumps(exact_measurement, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8")
    measurement_digest = artifacts.store_bytes(artifacts_dir, measurement_raw)
    ledger.bind_request_measurement(db, attempt_id, digest, measurement_digest)
    return attempt_id, digest


def consent_check(policy):
    """Current user policy: one explicit approval per external call.

    Only {"mode": "per-call", "approval_ref": <non-empty>} passes. Batch,
    auto, and standing approvals are rejected as unknown policy: unattended
    execution needs an explicit policy change, never a silent default.
    Returns the approval reference.
    """
    if not isinstance(policy, dict) or policy.get("mode") != "per-call":
        raise ledger.LedgerError("E_CONSENT_POLICY: only per-call approval is supported")
    ref = policy.get("approval_ref", "")
    if not isinstance(ref, str) or not ref.strip():
        raise ledger.LedgerError("E_APPROVAL_REF: approval reference required")
    return ref.strip()


def approve(db, attempt_id, approval_ref, policy=None):
    if policy is None:
        policy = {"mode": "per-call", "approval_ref": approval_ref}
    elif policy.get("approval_ref", approval_ref) != approval_ref:
        raise ledger.LedgerError("E_APPROVAL_MISMATCH: policy ref differs from approval ref")
    ref = consent_check(policy)
    ledger.transition(db, attempt_id, "AWAITING_APPROVAL", approval_ref=ref)
    return attempt_id


def dispatch(db, artifacts_dir, provider, attempt_id, *, coordination_context=None):
    row = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None or row["state"] != "AWAITING_APPROVAL" or not row["approval_ref"]:
        raise ledger.LedgerError("E_DISPATCH_UNAPPROVED: attempt not approved")
    from . import coordination
    coordination.guard(db, row["work_item_id"], artifacts_dir, coordination_context,
                       "dispatch", attempt_id)
    request = artifacts.open_verified(artifacts_dir, row["request_digest"])
    if ledger.coordination_get(db,row["work_item_id"]) is not None:
        raise ledger.LedgerError("E_COORD_LEGACY: coordinated tasks require strict adapter dispatch")
    ledger.transition(db, attempt_id, "DISPATCHING")
    try:
        response = provider.dispatch(request)
    except ProviderTruncated as exc:
        digest = artifacts.store_bytes(artifacts_dir, exc.partial)
        ledger.transition(db, attempt_id, "RESPONSE_SAVED", response_digest=digest)
        ledger.transition(db, attempt_id, "TRUNCATED", error="provider truncated")
        return attempt_id
    except ProviderRefusal as exc:
        digest = artifacts.store_bytes(artifacts_dir, str(exc).encode("utf-8"))
        ledger.transition(db, attempt_id, "RESPONSE_SAVED", response_digest=digest)
        ledger.transition(db, attempt_id, "REFUSED", error="provider refused")
        return attempt_id
    except Exception as exc:
        ledger.transition(db, attempt_id, "DELIVERY_UNKNOWN",
                          error="%s: %s" % (type(exc).__name__, exc))
        return attempt_id
    digest = artifacts.store_bytes(artifacts_dir, response)
    ledger.transition(db, attempt_id, "RESPONSE_SAVED", response_digest=digest)
    return attempt_id


def validate(db, artifacts_dir, attempt_id, check_fn):
    row = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None or not row["response_digest"]:
        raise ledger.LedgerError("E_VALIDATE_NORESPONSE: nothing to validate")
    response = artifacts.open_verified(artifacts_dir, row["response_digest"])
    try:
        ok, reason = check_fn(response)
    except Exception as exc:
        ledger.transition(db, attempt_id, "INVALID_RESULT",
                          error="validator raised %s: %s" % (type(exc).__name__, exc))
        return attempt_id
    if ok:
        ledger.transition(db, attempt_id, "VALIDATED")
    else:
        ledger.transition(db, attempt_id, "INVALID_RESULT", error=reason or "check failed")
    return attempt_id


def accept(db, artifacts_dir, attempt_id, expect_task_digest,
           manifest, source_bytes, expect_approval, *, coordination_context=None):
    """Strict acceptance: re-verify the whole basis before ACCEPTED.

    Checks work-item task identity, manifest validity + source binding,
    stored request task/unit binding, stored response validity, and approval
    identity/scope. Any mismatch raises LedgerError; nothing is accepted on
    declaration. expect_approval: {provider, model, endpoint, purpose,
    max_output_tokens}. Ledger-only transitions must not be used as gates.
    """
    from . import providers, results
    row = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None:
        raise ledger.LedgerError("E_ACCEPT_UNKNOWN: no such attempt")
    if row["state"] != "VALIDATED":
        raise ledger.LedgerError("E_ACCEPT_STATE: attempt is %s, not VALIDATED"
                                 % (row["state"],))
    from . import coordination
    coordination.guard(db, row["work_item_id"], artifacts_dir, coordination_context,
                       "accept", attempt_id)
    item = db.execute("SELECT * FROM work_items WHERE id=?",
                      (row["work_item_id"],)).fetchone()
    if item is None or expect_task_digest != item["task_digest"]:
        raise ledger.LedgerError("E_ACCEPT_TASK: work item task mismatch")
    manifest_errors = partition.validate_manifest(source_bytes, manifest)
    if manifest_errors:
        raise ledger.LedgerError("E_ACCEPT_MANIFEST: %s" % (manifest_errors[0],))
    if manifest.get("source_id") != item["source_id"]:
        raise ledger.LedgerError("E_ACCEPT_SOURCE: manifest source %r != work item source %r"
                                 % (manifest.get("source_id"), item["source_id"]))
    try:
        request = json.loads(artifacts.open_verified(artifacts_dir, row["request_digest"]).decode("utf-8"))
    except Exception as exc:
        raise ledger.LedgerError("E_ACCEPT_REQUEST: stored request unreadable: %s" % (exc,))
    if request.get("task_digest") != expect_task_digest \
            or request.get("task_digest") != item["task_digest"]:
        raise ledger.LedgerError("E_ACCEPT_TASK: stored request task mismatch")
    proof = request.get("source_proof")
    if not isinstance(proof, dict) or proof.get("source_id") != item["source_id"] \
            or proof.get("source_digest") != manifest.get("source_digest") \
            or proof.get("manifest_digest") != manifest.get("manifest_digest"):
        raise ledger.LedgerError("E_ACCEPT_SOURCE_PROOF: frozen source proof required")
    if artifacts.open_verified(artifacts_dir, proof["source_artifact_digest"]) != source_bytes \
            or json.loads(artifacts.open_verified(artifacts_dir, proof["manifest_artifact_digest"])) != manifest:
        raise ledger.LedgerError("E_ACCEPT_SOURCE_PROOF: frozen artifacts differ")
    measurement_ref = ledger.request_measurement_binding(db, attempt_id, row["request_digest"])
    if not measurement_ref:
        raise ledger.LedgerError("E_ACCEPT_MEASUREMENT: persisted exact request measurement required")
    measurement = json.loads(artifacts.open_verified(artifacts_dir, measurement_ref))
    profile = request.get("model", {})
    profile_raw = json.dumps(profile, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if measurement.get("request_digest") != row["request_digest"] \
            or measurement.get("profile_digest") != hashlib.sha256(profile_raw).hexdigest() \
            or measurement.get("final_payload_bytes") != len(artifacts.open_verified(artifacts_dir, row["request_digest"])) \
            or not isinstance(measurement.get("input_tokens"), int) \
            or isinstance(measurement.get("input_tokens"), bool) \
            or measurement["input_tokens"] < 0 \
            or measurement.get("output_tokens") != profile.get("output_limit") \
            or measurement.get("context_limit") != profile.get("context_limit") \
            or measurement["input_tokens"] + measurement["output_tokens"] > measurement["context_limit"]:
        raise ledger.LedgerError("E_ACCEPT_MEASUREMENT: exact basis/budget invalid")
    expected = sorted(u["id"] for u in manifest.get("units", []))
    requested = request.get("primary_unit_ids", [])
    if not requested or sorted(set(requested)) != sorted(requested) \
            or any(i not in expected for i in requested):
        raise ledger.LedgerError("E_ACCEPT_UNITS: request units not a clean manifest subset")
    table = {u["id"]: u for u in manifest.get("units", [])}
    materials = request.get("materials", {})
    for ident in requested:
        start, end = table[ident]["range"]
        try:
            actual = source_bytes[start:end].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ledger.LedgerError("E_ACCEPT_SOURCE: unit %s undecodable: %s" % (ident, exc))
        if materials.get("source_%s" % (ident,)) != actual:
            raise ledger.LedgerError("E_ACCEPT_SOURCE: request text for %s != frozen source" % (ident,))
    if not row["response_digest"]:
        raise ledger.LedgerError("E_ACCEPT_NORESPONSE: nothing validated")
    try:
        response = json.loads(artifacts.open_verified(artifacts_dir, row["response_digest"]).decode("utf-8"))
    except Exception as exc:
        raise ledger.LedgerError("E_ACCEPT_RESPONSE: stored response unreadable: %s" % (exc,))
    ok, reason = providers.validate_response(response, sorted(requested), row["response_digest"])
    if not ok:
        raise ledger.LedgerError("E_ACCEPT_RESPONSE: %s" % (reason,))
    # A provider wrapper marker is not an accepted audit result.  Every
    # requested unit needs a full, source-attached record bound to this exact
    # task and attempt; strings and [] cannot silently become semantic proof.
    records = [response["results"][ident] for ident in requested]
    rich_ok, rich_errors = results.validate_rich_results(
        records, source_bytes, manifest, item["task_digest"], attempt_id,
        expected_ids=requested)
    if not rich_ok:
        raise ledger.LedgerError("E_ACCEPT_RICH_RESULTS: %s" % (rich_errors[0],))
    approval = db.execute("SELECT * FROM approvals WHERE id=? AND attempt_id=?",
                          (row["approval_id"], attempt_id)).fetchone() \
        if row["approval_id"] else None
    if approval is None:
        raise ledger.LedgerError("E_ACCEPT_APPROVAL: no consumed approval for attempt")
    if approval["consumed"] != 1 or any(approval[key] != profile.get(key)
            for key in ("provider", "model", "endpoint", "purpose")) \
            or approval["max_output_tokens"] != profile.get("output_limit") \
            or json.loads(approval["limits_json"]).get("max_spend") != profile.get("max_spend", 0):
        raise ledger.LedgerError("E_ACCEPT_APPROVAL: consumed approval differs from actual request profile")
    for key in ("provider", "model", "endpoint", "purpose"):
        if approval[key] != expect_approval.get(key):
            raise ledger.LedgerError("E_ACCEPT_APPROVAL: approval %s mismatch" % (key,))
    if approval["max_output_tokens"] != expect_approval.get("max_output_tokens"):
        raise ledger.LedgerError("E_ACCEPT_APPROVAL: approval output limit mismatch")
    if row["request_digest"] != approval["request_digest"]:
        raise ledger.LedgerError("E_ACCEPT_APPROVAL: approval bound to another request")
    # The low-level state transition has a separate coordinated-task guard;
    # publish its bounded marker only after all strict acceptance checks pass.
    ledger.transition(db, attempt_id, "ACCEPTED", coordination_context={
        "context": coordination_context, "artifacts_dir": str(artifacts_dir)})
    return attempt_id


def dispatch_live(*_args, **_kwargs):
    raise LiveNotImplemented("live provider dispatch is M4 work; use FakeProvider")


def dispatch_via_adapter(db, artifacts_dir, adapter, attempt_id, approval_id,
                         *, coordination_context=None):
    """Unified dispatch: approved exact bytes -> adapter -> saved raw -> validated.

    The approval is consumed BEFORE the adapter runs (a spy adapter proves
    non-dispatch on every rejection path). The wrapper stores the raw
    response bytes and computes their digest itself; adapter-declared
    digests must match or the response is rejected as spoofed.
    """
    from . import providers
    row = db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None:
        raise ledger.LedgerError("E_DISPATCH_UNKNOWN: no such attempt")
    if row["state"] != "AWAITING_APPROVAL":
        raise ledger.LedgerError("E_DISPATCH_STATE: attempt is %s, not approved" % (row["state"],))
    from . import coordination
    # This is before approval consumption and the adapter boundary.
    coordination.guard(db, row["work_item_id"], artifacts_dir, coordination_context,
                       "dispatch", attempt_id)
    prepared = artifacts.open_verified(artifacts_dir, row["request_digest"])
    try:
        request_body = json.loads(prepared.decode("utf-8"))
        expected = request_body.get("primary_unit_ids", [])
    except (ValueError, UnicodeDecodeError) as exc:
        raise ledger.LedgerError("E_DISPATCH_REQUEST: stored request unreadable: %s" % (exc,))
    exact = providers.final_payload_measurement(prepared)
    if exact["final_payload_sha256"] != row["request_digest"]:
        raise ledger.LedgerError("E_DISPATCH_MEASUREMENT: final serialized request digest mismatch")
    proof = request_body.get("source_proof")
    if not isinstance(proof, dict):
        raise ledger.LedgerError("E_DISPATCH_SOURCE: request lacks frozen source/manifest proof")
    try:
        source = artifacts.open_verified(artifacts_dir, proof["source_artifact_digest"])
        manifest = json.loads(artifacts.open_verified(
            artifacts_dir, proof["manifest_artifact_digest"]).decode("utf-8"))
    except Exception as exc:
        raise ledger.LedgerError("E_DISPATCH_SOURCE: stored source proof unreadable: %s" % exc)
    errors = partition.validate_manifest(source, manifest)
    if errors or manifest.get("source_digest") != proof.get("source_digest") \
            or manifest.get("manifest_digest") != proof.get("manifest_digest"):
        raise ledger.LedgerError("E_DISPATCH_SOURCE: frozen manifest/source proof is invalid")
    table = {unit["id"]: unit for unit in manifest["units"]}
    for unit_id in expected:
        unit = table.get(unit_id)
        if unit is None or proof.get("primary_unit_hashes", {}).get(unit_id) != unit["sha256"] \
                or request_body.get("materials", {}).get("source_" + unit_id) != \
                source[unit["range"][0]:unit["range"][1]].decode("utf-8"):
            raise ledger.LedgerError("E_DISPATCH_SOURCE: request material is not bound to frozen unit %s" % unit_id)
    profile = request_body.get("model")
    try:
        budget.validate_profile(profile)
    except budget.BudgetError as exc:
        raise ledger.LedgerError("E_DISPATCH_PROFILE: %s" % (exc,))
    measurement_digest = ledger.request_measurement_binding(db, attempt_id, row["request_digest"])
    if not measurement_digest:
        raise ledger.LedgerError("E_DISPATCH_MEASUREMENT: no persisted exact payload measurement")
    try:
        measured = json.loads(artifacts.open_verified(artifacts_dir, measurement_digest).decode("utf-8"))
    except Exception as exc:
        raise ledger.LedgerError("E_DISPATCH_MEASUREMENT: stored measurement unreadable: %s" % exc)
    profile_raw = json.dumps(profile, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False).encode("utf-8")
    if measured.get("request_digest") != row["request_digest"] \
            or measured.get("profile_digest") != __import__("hashlib").sha256(profile_raw).hexdigest() \
            or measured.get("final_payload_bytes") != len(prepared) \
            or measured.get("final_payload_sha256") != row["request_digest"]:
        raise ledger.LedgerError("E_DISPATCH_MEASUREMENT: payload/profile proof mismatch")
    if not isinstance(measured.get("input_tokens"), int) or measured["input_tokens"] < 0 \
            or measured.get("output_tokens") != profile["output_limit"] \
            or measured.get("context_limit") != profile["context_limit"] \
            or measured["input_tokens"] + measured["output_tokens"] > measured["context_limit"]:
        raise ledger.LedgerError("E_DISPATCH_BUDGET: exact payload measurement exceeds or lacks context budget")
    approval = db.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    if approval is None or approval["consumed"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL: approval missing or consumed")
    if approval["attempt_id"] != attempt_id or approval["request_digest"] != row["request_digest"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL: approval is not bound to this exact attempt/request")
    # These fields are mandatory for strict dispatch.  Legacy profiles can be
    # prepared for inspection but cannot cross an adapter boundary.
    for key in ("endpoint", "purpose"):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise ledger.LedgerError("E_DISPATCH_PROFILE: profile.%s is required before dispatch" % key)
    if approval["provider"] != profile["provider"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_PROVIDER: approval/provider mismatch")
    if approval["model"] != profile["model"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_MODEL: approval/model mismatch")
    if approval["endpoint"] != profile["endpoint"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_ENDPOINT: approval/endpoint mismatch")
    if approval["purpose"] != profile["purpose"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_PURPOSE: approval/purpose mismatch")
    if approval["max_output_tokens"] != profile["output_limit"]:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_OUTPUT: approval/output limit mismatch")
    try:
        limits = json.loads(approval["limits_json"])
    except ValueError as exc:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_LIMITS: invalid approval limits: %s" % exc)
    if limits.get("max_spend") != profile.get("max_spend", 0):
        raise ledger.LedgerError("E_DISPATCH_APPROVAL_SPEND: approval/spend limit mismatch")
    # This release is an offline fixture workflow.  Do not let a caller smuggle
    # a network-capable adapter through the otherwise unified dispatch API.
    try:
        capabilities = adapter.capabilities()
    except Exception as exc:
        raise ledger.LedgerError("E_DISPATCH_ADAPTER: adapter capabilities unavailable: %s" % exc)
    if not isinstance(capabilities, dict) or capabilities.get("live") is not False \
            or capabilities.get("evidence_class") != "TEST_ONLY":
        raise ledger.LedgerError("E_DISPATCH_ADAPTER: R2 permits only non-live TEST_ONLY adapters")
    try:
        ledger.start_approved_dispatch(db, approval_id, attempt_id, row["request_digest"],{
            "context":coordination_context,"artifacts_dir":str(artifacts_dir)})
    except ledger.LedgerError as exc:
        raise ledger.LedgerError("E_DISPATCH_APPROVAL: %s" % (exc,))
    try:
        response = adapter.dispatch(prepared)
    except Exception as exc:
        ledger.transition(db, attempt_id, "DELIVERY_UNKNOWN",
                          error="%s: %s" % (type(exc).__name__, exc))
        return attempt_id
    if not isinstance(response, dict):
        ledger.transition(db, attempt_id, "DELIVERY_UNKNOWN",
                          error="adapter returned non-object")
        return attempt_id
    raw_resp = json.dumps(response, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    raw_digest = artifacts.store_bytes(artifacts_dir, raw_resp)
    ledger.transition(db, attempt_id, "RESPONSE_SAVED", response_digest=raw_digest)
    ok, reason = providers.validate_response(response, expected, raw_digest)
    if ok:
        ledger.transition(db, attempt_id, "VALIDATED")
    else:
        ledger.transition(db, attempt_id, "INVALID_RESULT", error=reason)
    return attempt_id


def record_retry_decision(db, work_item_id, attempt_id, reason):
    """Explicit human decision to retry after uncertain delivery."""
    if not (reason or "").strip():
        raise ledger.LedgerError("E_RETRY_REASON: retry decision needs a reason")
    row = db.execute("SELECT state FROM attempts WHERE id=? AND work_item_id=?",
                     (attempt_id, work_item_id)).fetchone()
    if row is None:
        raise ledger.LedgerError("E_RETRY_UNKNOWN: no such attempt for work item")
    if row["state"] != "DELIVERY_UNKNOWN":
        raise ledger.LedgerError("E_RETRY_STATE: attempt is %s, not uncertain" % (row["state"],))
    ledger.event(db, "RETRY_AUTHORIZED", work_item_id, "%s: %s" % (attempt_id, reason))
    return True


def _retry_authorized(db, work_item_id, attempt_id):
    rows = db.execute("SELECT detail FROM events WHERE kind='RETRY_AUTHORIZED'"
                      " AND work_item_id=?", (work_item_id,)).fetchall()
    return any((d["detail"] or "").split(":")[0] == attempt_id for d in rows)


def preflight(db, work_item_id, manifest, source_bytes, profile, per_unit_output,
              expect_task_digest=None, counter=None, reasoning_reserve=0, safety_reserve=0,
              coordination_context=None, artifacts_dir=None):
    """Local readiness gate. No dispatch, no network. Returns (pass_bool, notes).

    Fails closed on: invalid manifest, invalid profile, unmeasurable or
    over-budget batches, unreconciled transient attempts for this work item.
    """
    notes = []
    item = db.execute("SELECT * FROM work_items WHERE id=?", (work_item_id,)).fetchone()
    if item is None:
        return False, ["BLOCKED: unknown work item %s" % (work_item_id,)]
    from . import coordination
    try:
        coordination.guard(db,work_item_id,artifacts_dir,coordination_context,"preflight")
    except (ledger.LedgerError, OSError, TypeError) as exc:
        return False,["BLOCKED: "+str(exc)]
    if manifest.get("source_id") != item["source_id"]:
        return False, ["BLOCKED: manifest source %r != work item source %r"
                       % (manifest.get("source_id"), item["source_id"])]
    if expect_task_digest is not None and expect_task_digest != item["task_digest"]:
        return False, ["BLOCKED: work item task %r != expected %r"
                       % (item["task_digest"], expect_task_digest)]
    manifest_errors = partition.validate_manifest(source_bytes, manifest)
    if manifest_errors:
        return False, ["BLOCKED: manifest invalid: %s" % (manifest_errors[0],)]
    try:
        budget.validate_profile(profile)
    except budget.BudgetError as exc:
        return False, ["BLOCKED: profile invalid: %s" % (exc,)]
    units = []
    for unit in manifest["units"]:
        start, end = unit["range"]
        try:
            count, _ = budget.count_tokens(source_bytes[start:end].decode("utf-8"),
                                           profile["encoding"], counter)
        except (budget.BudgetError, UnicodeDecodeError) as exc:
            return False, ["BLOCKED: unit %s unmeasurable: %s" % (unit["id"], exc)]
        units.append({"id": unit["id"], "input_tokens": count})
    try:
        plan = budget.plan_batches(profile, units, per_unit_output,
                                   reasoning_reserve, safety_reserve)
    except budget.BudgetError as exc:
        return False, ["BLOCKED: budget infeasible: %s" % (exc,)]
    stale = db.execute("SELECT id, state FROM attempts WHERE work_item_id=? AND state IN"
                       " ('PREPARED','AWAITING_APPROVAL','DISPATCHING')",
                       (work_item_id,)).fetchall()
    if stale:
        return False, ["BLOCKED: unreconciled attempts: %s"
                       % (", ".join(r["id"] for r in stale),)]
    uncertain = db.execute("SELECT id FROM attempts WHERE work_item_id=? AND state='DELIVERY_UNKNOWN'",
                           (work_item_id,)).fetchall()
    for row in uncertain:
        if not _retry_authorized(db, work_item_id, row["id"]):
            return False, ["BLOCKED: %s delivery uncertain; record a retry decision first"
                           % (row["id"],)]
    saved = db.execute("SELECT id, state FROM attempts WHERE work_item_id=? AND state IN"
                       " ('RESPONSE_SAVED','VALIDATED','ACCEPTED')",
                       (work_item_id,)).fetchall()
    if saved:
        return False, ["ACTION resume %s (%s): continue from the saved result, do not resend"
                       % (saved[0]["id"], saved[0]["state"])]
    return True, ["batches=%d input_budget=%d" % (len(plan["batches"]), plan["input_budget"])]


def crash_probe(db_path, artifacts_dir, work_item_id, mode):
    """Subprocess entry for kill tests. Dies via os._exit (no cleanup)."""
    db = ledger.connect(db_path)
    ledger.create_work_item(db, work_item_id, "task-digest-probe", "SRC-PROBE")
    attempt_id, _ = prepare(db, artifacts_dir, work_item_id, "task-digest-probe",
                            {"U000001": '{"value": 7}'}, "check the value",
                            {"type": "object"}, {}, "spec-digest-probe",
                            {"schema_version": 2, "provider": "fake", "model": "probe-1",
                             "encoding": "e", "encoding_version": "v",
                             "context_limit": 100000, "output_limit": 10000,
                             "counting_method": "test"},
                            counter=lambda text: text.split())
    approve(db, attempt_id, "probe-approval")
    if mode == "die-in-dispatch":
        ledger.transition(db, attempt_id, "DISPATCHING")
        os._exit(137)
    provider = FakeProvider([("ok", b'{"units":["U000001"]}')])
    dispatch(db, artifacts_dir, provider, attempt_id)
    if mode == "die-after-save":
        os._exit(137)
    raise AssertionError("unknown crash mode %r" % (mode,))
