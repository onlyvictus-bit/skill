#!/usr/bin/env python3
"""v2 contract schemas, evidence/state enums, and compatibility handshake.

Standard library only. These definitions are normative for M0-M3: unknown
fields, enums, or schema versions are rejected, never guessed. A fake or
hand-written record can never satisfy a v2 gate because gates consume only
validated structures produced through these checks.
"""
import hashlib
import json

from . import ENGINE_NAME, ENGINE_VERSION, SCHEMA_VERSION

EVIDENCE_CLASSES = (
    "MANUAL_REPORTED",
    "TEST_ONLY",
    "HOST_OBSERVED",
    "TRANSPORT_OBSERVED",
)

RECEIPT_STATES = (
    "COMPLETE",
    "PARTIAL",
    "TRUNCATED",
    "ERROR",
    "STALE",
)

ATTEMPT_STATES = (
    "QUEUED",
    "PREPARED",
    "AWAITING_APPROVAL",
    "DISPATCHING",
    "RESPONSE_SAVED",
    "VALIDATED",
    "ACCEPTED",
    "REFUSED",
    "TRUNCATED",
    "RETRYABLE_ERROR",
    "INVALID_RESULT",
    "DELIVERY_UNKNOWN",
    "CANCELLED",
    "STALE",
)

EXTRACTION_STATES = (
    "EXACT_TEXT",
    "INVENTORY_CHECKED",
    "VERIFIED_TO_DECLARED_REFERENCE",
    "PARTIAL",
    "UNSUPPORTED",
    "UNKNOWN",
    "ERROR",
)


class ContractError(ValueError):
    """Raised for any schema/enum/identity violation. Never caught to mean success."""


def canonical_contracts():
    """The exact semantic surface covered by schema_digest()."""
    return {
        "engine": ENGINE_NAME,
        "schema_version": SCHEMA_VERSION,
        "evidence_classes": list(EVIDENCE_CLASSES),
        "receipt_states": list(RECEIPT_STATES),
        "attempt_states": list(ATTEMPT_STATES),
        "extraction_states": list(EXTRACTION_STATES),
        # Kept separate from schema_version: this is a fail-closed policy
        # evolution within schema 2.  A m9 pin must not silently accept R2.
        "r2_policy_version": "r2-dispatch-evidence-1",
        "r3_policy_version": "r3-coordinated-offline-history-3",
        "ledger_schema_version": 4,
        "coordination_policy_required_keys": ["schema_version","coordination_required","workspace_id",
            "task_id","run_id","source_id","source_digest","profile_digest","requirement_digest","fence"],
        "coordination_snapshot_required_keys": ["schema_version","workspace_id","requirement_digest",
            "revision","native_observation","nodes","edges","complete","page_complete"],
        "coordination_relations": ["hard","informational"],
        "coordination_entrypoints": ["prepare","legacy_dispatch_refused","adapter_dispatch","accept",
            "ledger_PREPARED","ledger_DISPATCHING","ledger_ACCEPTED","preflight","report","recall","resume"],
        "coordination_request_binding": "context_coordination_basis exact graph/policy/prerequisite proof refs",
        "dispatch_start_contract":"guard, single-use approval consumption and DISPATCHING share one ledger transaction",
        "coordinated_generic_dispatch":"refused; only start_approved_dispatch may enter DISPATCHING",
        "coordinated_uncertain_delivery":"blocks replacement and current eligibility; reason-only retry note is insufficient",
        "spent_approval_recovery":"AWAITING_APPROVAL with consumed approval recovers to DELIVERY_UNKNOWN",
        "spent_approval_cancellation":"coordinated CANCELLED/RETRYABLE_ERROR refused without saved response; reconcile uncertain delivery",
        "history_contract": {"chain":"central-single-writer","event_projection_atomic":True,
            "projection":"full canonical snapshots with per-event typed delta replay",
            "checkpoint":"cm-history-checkpoint-v1","current_head_anchor_required":True,
            "prefix_anchor_fields":["anchored_through_seq","current_head_anchored"],
            "checkpoint_owner":"separately retained verifier input","without_checkpoint":"UNVERIFIED",
            "native_beads_qualified":False},
        "complete_request_required_keys": [
            "schema_version", "kind", "work_item_id", "task_digest",
            "task_spec_digest", "primary_unit_ids", "model", "measurement",
            "source_proof", "materials"],
        "source_proof_required_keys": [
            "source_id", "source_digest", "manifest_digest",
            "source_artifact_digest", "manifest_artifact_digest",
            "primary_unit_hashes"],
        "final_payload_measurement_required_keys": [
            "schema_version", "request_digest", "profile_digest",
            "final_payload_bytes", "final_payload_sha256", "input_tokens",
            "output_tokens", "context_limit", "counting_method", "evidence_class"],
        "approval_binding_required_keys": [
            "provider", "model", "endpoint", "purpose", "max_output_tokens",
            "limits_json:max_spend"],
        "rich_result_binding_required_keys": [
            "unit_id", "source_digest", "task_digest", "attempt_id",
            "original_excerpt", "excerpt_sha256", "interpretation", "findings",
            "disposition"],
        "run_map_required_keys": [
            "schema_version", "run_dir", "generation", "source_digests",
            "artifact_digests", "source_id", "task_digest", "profile_digest"],
    }


def schema_digest():
    """SHA-256 over canonical contract JSON. Any semantic change alters it."""
    raw = json.dumps(canonical_contracts(), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def no_duplicate_keys(pairs):
    """json.loads object_pairs_hook: duplicate keys are a hard error."""
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ContractError("E_DUP_KEY: duplicate JSON key %r" % (key,))
        obj[key] = value
    return obj


def loads_strict(text):
    """Parse canonical JSON; duplicate keys and malformed input raise ContractError."""
    try:
        return json.loads(text, object_pairs_hook=no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ContractError("E_JSON_INVALID: %s" % (exc,))
    except ContractError:
        raise


def require_keys(obj, required, allowed, where):
    if not isinstance(obj, dict):
        raise ContractError("E_SCHEMA_TYPE: %s must be an object" % (where,))
    unknown = sorted(set(obj) - set(allowed))
    if unknown:
        raise ContractError("E_SCHEMA_FIELD: %s has unsupported field(s): %s"
                            % (where, ", ".join(unknown)))
    missing = sorted(set(required) - set(obj))
    if missing:
        raise ContractError("E_SCHEMA_REQUIRED: %s missing required field(s): %s"
                            % (where, ", ".join(missing)))
    return obj


def require_schema_version(doc, where):
    if doc.get("schema_version") != SCHEMA_VERSION and doc.get("schema") != SCHEMA_VERSION:
        raise ContractError("E_SCHEMA_VERSION: %s must carry schema version %r"
                            % (where, SCHEMA_VERSION))
    return True


def require_enum(value, allowed, where):
    if value not in allowed:
        raise ContractError("E_SCHEMA_ENUM: %s must be one of %s, got %r"
                            % (where, sorted(allowed), value))
    return True


def require_sha256(value, where):
    if not isinstance(value, str) or len(value) != 64:
        raise ContractError("E_DIGEST_LENGTH: %s must be 64 hex chars" % (where,))
    try:
        int(value, 16)
    except ValueError:
        raise ContractError("E_DIGEST_FORMAT: %s must be hex" % (where,))
    return True


def require_unique_ids(rows, where):
    seen = set()
    for idx, row in enumerate(rows):
        ident = row.get("id") if isinstance(row, dict) else None
        if not isinstance(ident, str) or not ident.strip():
            raise ContractError("E_SCHEMA_VALUE: %s[%d].id must be a non-empty string"
                                % (where, idx))
        if ident in seen:
            raise ContractError("E_ID_DUPLICATE: duplicate id %r in %s" % (ident, where))
        seen.add(ident)
    return seen


def capabilities_envelope(commands=()):
    return {
        "ok": True,
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "schema_digest": schema_digest(),
        "evidence_classes": list(EVIDENCE_CLASSES),
        "receipt_states": list(RECEIPT_STATES),
        "attempt_states": list(ATTEMPT_STATES),
        "extraction_states": list(EXTRACTION_STATES),
        "commands": list(commands),
        "coordination_offline_policy": True,
        "native_beads_qualified": False,
        "history_schema": 4,
    }


def check_capabilities(env, expect_schema_version=SCHEMA_VERSION, expect_digest=None):
    """Validate an engine capabilities envelope. Returns (ok, error_dict|None)."""
    if not isinstance(env, dict) or env.get("ok") is not True:
        return False, {"code": "E_COMPANION_BAD_ENVELOPE",
                       "message": "engine did not return ok:true capabilities"}
    if env.get("schema_version") != expect_schema_version:
        return False, {"code": "E_SCHEMA_MISMATCH",
                       "message": "engine schema_version %r != expected %r"
                                  % (env.get("schema_version"), expect_schema_version)}
    digest = env.get("schema_digest", "")
    if not isinstance(digest, str) or len(digest) != 64:
        return False, {"code": "E_DIGEST_FORMAT",
                       "message": "engine schema_digest is not 64 hex chars"}
    if expect_digest is not None and digest.lower() != expect_digest.lower():
        return False, {"code": "E_DIGEST_MISMATCH",
                       "message": "engine schema_digest does not match pinned contract"}
    return True, None
