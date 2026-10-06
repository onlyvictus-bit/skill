"""M3/M4 coordinated task eligibility, using CM proof as the evidence owner.

This module intentionally has no Beads executable or database dependency.  It
accepts a complete *observed* graph snapshot from an adapter, validates it,
freezes its canonical bytes in the existing CAS, and evaluates task
prerequisites against this ledger's actual accepted proof.  ``FIXTURE_*``
observations are useful offline policy evidence only; they never mean a native
runtime has been qualified.

The durable registry uses namespaced keys in the pre-existing ``meta`` table
instead of a second task database.  Event history remains the ledger's sole
canonical history owner.
"""
import hashlib
import json

from . import artifacts, ledger, partition, providers, results

POLICY_VERSION = 1
SNAPSHOT_VERSION = 1
CONTEXT_VERSION = 1
HARD_KINDS = ("hard",)
INFORMATIONAL_KINDS = ("informational",)
ALLOWED_KINDS = HARD_KINDS + INFORMATIONAL_KINDS
NATIVE_OBSERVATIONS = ("FIXTURE_NATIVE_UNQUALIFIED", "NATIVE_UNQUALIFIED")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _fail(code, message):
    raise ledger.LedgerError("%s: %s" % (code, message))


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        _fail("E_COORD_VALUE", "%s must be a non-empty string" % name)
    return value


def _sha(value, name):
    if not isinstance(value, str) or len(value) != 64:
        _fail("E_COORD_DIGEST", "%s must be a SHA-256 digest" % name)
    try:
        int(value, 16)
    except ValueError:
        _fail("E_COORD_DIGEST", "%s must be a SHA-256 digest" % name)
    return value.lower()


def _exact_object(value, required, where):
    if not isinstance(value, dict):
        _fail("E_COORD_SCHEMA", "%s must be an object" % where)
    unknown = sorted(set(value) - set(required))
    missing = sorted(set(required) - set(value))
    if unknown or missing:
        _fail("E_COORD_SCHEMA", "%s unknown=%s missing=%s" %
              (where, unknown, missing))
    return value


def validate_policy(policy, work_item_id=None):
    required = ("schema_version", "coordination_required", "workspace_id", "task_id",
                "run_id", "source_id", "source_digest", "profile_digest",
                "requirement_digest", "fence")
    _exact_object(policy, required, "policy")
    if policy["schema_version"] != POLICY_VERSION:
        _fail("E_COORD_POLICY_VERSION", "unsupported policy version")
    if policy["coordination_required"] is not True:
        _fail("E_COORD_POLICY", "registered policy must require coordination")
    for key in ("workspace_id", "task_id", "run_id", "source_id", "fence"):
        _text(policy[key], "policy.%s" % key)
    for key in ("source_digest", "profile_digest", "requirement_digest"):
        _sha(policy[key], "policy.%s" % key)
    if work_item_id is not None and policy["task_id"] != work_item_id:
        _fail("E_COORD_POLICY_TASK", "policy task_id must equal CM work item id")
    return dict(policy)


def validate_snapshot(snapshot):
    required = ("schema_version", "workspace_id", "requirement_digest", "revision",
                "native_observation", "nodes", "edges", "complete", "page_complete")
    _exact_object(snapshot, required, "graph snapshot")
    if snapshot["schema_version"] != SNAPSHOT_VERSION:
        _fail("E_COORD_GRAPH_VERSION", "unsupported graph snapshot version")
    _text(snapshot["workspace_id"], "graph.workspace_id")
    _sha(snapshot["requirement_digest"], "graph.requirement_digest")
    _text(snapshot["revision"], "graph.revision")
    if snapshot["native_observation"] not in NATIVE_OBSERVATIONS:
        _fail("E_COORD_OBSERVATION", "unsupported native observation label")
    if snapshot["complete"] is not True or snapshot["page_complete"] is not True:
        _fail("E_COORD_GRAPH_PARTIAL", "all graph and ready pages must be observed")
    if not isinstance(snapshot["nodes"], list) or not snapshot["nodes"]:
        _fail("E_COORD_GRAPH_NODE", "nodes must be a non-empty complete list")
    if not all(isinstance(node, str) and node.strip() for node in snapshot["nodes"]):
        _fail("E_COORD_GRAPH_NODE", "node ids must be non-empty strings")
    nodes = list(snapshot["nodes"])
    if len(nodes) != len(set(nodes)):
        _fail("E_COORD_GRAPH_NODE", "duplicate node id")
    if not isinstance(snapshot["edges"], list):
        _fail("E_COORD_GRAPH_EDGE", "edges must be a list")
    normalized_edges = []
    for edge in snapshot["edges"]:
        _exact_object(edge, ("from", "to", "kind"), "graph edge")
        src, dst, kind = edge["from"], edge["to"], edge["kind"]
        if src not in nodes or dst not in nodes:
            _fail("E_COORD_GRAPH_NODE", "edge has missing or foreign endpoint")
        if src == dst:
            _fail("E_COORD_GRAPH_SELF", "self dependency is forbidden")
        if kind not in ALLOWED_KINDS:
            _fail("E_COORD_GRAPH_KIND", "unsupported relation kind %r" % kind)
        normalized_edges.append({"from": src, "to": dst, "kind": kind})
    if len({(e["from"], e["to"], e["kind"]) for e in normalized_edges}) != len(normalized_edges):
        _fail("E_COORD_GRAPH_EDGE", "duplicate edge")
    hard = {node: [] for node in nodes}
    for edge in normalized_edges:
        if edge["kind"] == "hard":
            hard[edge["to"]].append(edge["from"])
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            _fail("E_COORD_GRAPH_CYCLE", "hard prerequisite cycle includes %s" % node)
        if node in visited:
            return
        visiting.add(node)
        for parent in hard[node]:
            visit(parent)
        visiting.remove(node)
        visited.add(node)
    for node in nodes:
        visit(node)
    # Preserve caller order in the frozen evidence; it is part of the observed
    # adapter reply.  Its canonical serialization pins that exact observation.
    return dict(snapshot)


def snapshot_digest(snapshot):
    return _digest(validate_snapshot(snapshot))


def observed_context(policy, snapshot):
    """Create an explicit adapter-observed context for an offline fixture.

    Production adapters must construct the same strict shape from a fresh
    complete read.  This helper's result is labelled by the snapshot itself;
    it does not turn a fixture into native evidence.
    """
    policy = validate_policy(policy)
    snapshot = validate_snapshot(snapshot)
    return {"schema_version": CONTEXT_VERSION, "workspace_id": policy["workspace_id"],
            "task_id": policy["task_id"], "run_id": policy["run_id"],
            "source_id": policy["source_id"], "source_digest": policy["source_digest"],
            "profile_digest": policy["profile_digest"],
            "requirement_digest": policy["requirement_digest"], "fence": policy["fence"],
            "revision": snapshot["revision"], "snapshot_digest": snapshot_digest(snapshot),
            "snapshot": snapshot}


def context_envelope(contexts):
    """Bind the complete fresh observation set for a dependency closure."""
    if not isinstance(contexts, dict) or not contexts:
        _fail("E_COORD_CONTEXT", "complete context map is required")
    for task_id, context in contexts.items():
        if not isinstance(task_id, str) or not task_id.strip() or not isinstance(context, dict):
            _fail("E_COORD_CONTEXT", "context map contains an invalid task/context")
    return {"contexts": dict(contexts)}


def _split_context(current_context, work_item_id):
    if not isinstance(current_context, dict):
        _fail("E_COORD_CONTEXT", "current observed context is required")
    if set(current_context) == {"contexts"}:
        contexts = current_context["contexts"]
        if not isinstance(contexts, dict) or work_item_id not in contexts:
            _fail("E_COORD_CONTEXT", "complete context map lacks %s" % work_item_id)
        return contexts[work_item_id], contexts
    return current_context, {work_item_id: current_context}


def _validate_context(context, policy, expected_snapshot_digest):
    required = ("schema_version", "workspace_id", "task_id", "run_id", "source_id",
                "source_digest", "profile_digest", "requirement_digest", "fence",
                "revision", "snapshot_digest", "snapshot")
    if not isinstance(context, dict):
        _fail("E_COORD_CONTEXT", "current observed context is required")
    _exact_object(context, required, "current coordination context")
    if context["schema_version"] != CONTEXT_VERSION:
        _fail("E_COORD_CONTEXT", "unsupported context version")
    # A context is only observed facts.  It does not carry an accepted flag or
    # a caller-selected mode, both of which could create a bypass.
    for key in ("workspace_id", "task_id", "run_id", "source_id", "source_digest",
                "profile_digest", "requirement_digest", "fence"):
        if context[key] != policy[key]:
            _fail("E_COORD_CONTEXT", "%s does not match frozen approved policy" % key)
    snapshot = validate_snapshot(context["snapshot"])
    current = snapshot_digest(snapshot)
    if context["snapshot_digest"] != current or current != expected_snapshot_digest:
        _fail("E_COORD_CONTEXT", "graph snapshot does not match frozen current basis")
    if context["revision"] != snapshot["revision"]:
        _fail("E_COORD_CONTEXT", "revision does not match observed graph")
    if snapshot["workspace_id"] != policy["workspace_id"] or \
            snapshot["requirement_digest"] != policy["requirement_digest"]:
        _fail("E_COORD_CONTEXT", "observed graph is foreign to approved policy")
    return snapshot


def _meta_key(work_item_id):
    return "coordination:" + work_item_id


def _load(db, work_item_id):
    value = ledger.coordination_get(db, work_item_id)
    if value is None:
        return None
    _exact_object(value, ("policy", "snapshot_digest"), "coordination registry")
    policy = validate_policy(value["policy"], work_item_id)
    digest = _sha(value["snapshot_digest"], "registry.snapshot_digest")
    return policy, digest


def register_task(db, work_item_id, policy, snapshot, artifacts_dir):
    """Freeze one approved coordinated CM work item and its complete graph.

    Registry replacement is refused.  A changed graph/policy is a new
    approval/version decision, not an in-place caller mutation.
    """
    item = db.execute("SELECT id, source_id FROM work_items WHERE id=?", (work_item_id,)).fetchone()
    if item is None:
        _fail("E_COORD_WORK", "unknown CM work item %s" % work_item_id)
    policy = validate_policy(policy, work_item_id)
    if policy["source_id"] != item["source_id"]:
        _fail("E_COORD_POLICY_SOURCE", "approved source_id differs from CM work item")
    snapshot = validate_snapshot(snapshot)
    if snapshot["workspace_id"] != policy["workspace_id"] or \
            snapshot["requirement_digest"] != policy["requirement_digest"]:
        _fail("E_COORD_GRAPH_POLICY", "snapshot must bind the approved workspace and requirement digest")
    if work_item_id not in snapshot["nodes"]:
        _fail("E_COORD_GRAPH_NODE", "CM work item absent from observed graph")
    digest = artifacts.store_bytes(artifacts_dir, _canonical(snapshot))
    existing = _load(db, work_item_id)
    if existing is not None:
        if existing == (policy, digest):
            return {"work_item_id": work_item_id, "snapshot_digest": digest, "idempotent": True}
        _fail("E_COORD_REPLACE", "registered task policy/snapshot is immutable")
    ledger.coordination_put(db, work_item_id,
                            {"policy": policy, "snapshot_digest": digest})
    return {"work_item_id": work_item_id, "snapshot_digest": digest, "idempotent": False}


def _hard_predecessors(snapshot, work_item_id):
    return sorted(edge["from"] for edge in snapshot["edges"]
                  if edge["kind"] == "hard" and edge["to"] == work_item_id)


def _attempt_proof(db, work_item_id, artifacts_dir, policy, attempt_id, require_accepted):
    """Read-only strict proof inspection used for dependencies and acceptance.

    This deliberately repeats the load-bearing checks rather than trusting an
    accepted projection, a Beads close field, a caller flag, or a private
    marker.  It is safe for the ledger's low-level ACCEPTED hook because it
    has no state mutations.
    """
    row = db.execute("SELECT a.*, w.task_digest, w.source_id FROM attempts a "
                     "JOIN work_items w ON w.id=a.work_item_id WHERE a.id=? AND a.work_item_id=?",
                     (attempt_id, work_item_id)).fetchone()
    wanted_state = "ACCEPTED" if require_accepted else "VALIDATED"
    if row is None or row["state"] != wanted_state:
        return False, "attempt is not %s" % wanted_state
    if not all(isinstance(row[key], str) and len(row[key]) == 64
               for key in ("request_digest", "response_digest")):
        return False, "attempt lacks stored request/response evidence"
    measurement_digest = ledger.request_measurement_binding(db, attempt_id, row["request_digest"])
    if not measurement_digest or not row["approval_id"]:
        return False, "attempt lacks measurement or consumed approval evidence"
    try:
        request_raw = artifacts.open_verified(artifacts_dir, row["request_digest"])
        request = json.loads(request_raw.decode("utf-8"))
        response_raw = artifacts.open_verified(artifacts_dir, row["response_digest"])
        response = json.loads(response_raw.decode("utf-8"))
        measurement = json.loads(artifacts.open_verified(artifacts_dir, measurement_digest).decode("utf-8"))
    except Exception as exc:
        return False, "CAS evidence unreadable: %s" % type(exc).__name__
    proof = request.get("source_proof")
    if request.get("work_item_id") != work_item_id or request.get("task_digest") != row["task_digest"] \
            or not isinstance(proof, dict) or proof.get("source_id") != policy["source_id"] \
            or proof.get("source_digest") != policy["source_digest"] or row["source_id"] != policy["source_id"]:
        return False, "request task/source basis differs from approved policy"
    try:
        source = artifacts.open_verified(artifacts_dir, proof["source_artifact_digest"])
        manifest = json.loads(artifacts.open_verified(artifacts_dir, proof["manifest_artifact_digest"]).decode("utf-8"))
    except Exception as exc:
        return False, "frozen source/manifest unreadable: %s" % type(exc).__name__
    if partition.validate_manifest(source, manifest) or manifest.get("source_id") != policy["source_id"] \
            or manifest.get("source_digest") != policy["source_digest"] \
            or manifest.get("manifest_digest") != proof.get("manifest_digest"):
        return False, "frozen source/manifest basis invalid"
    profile = request.get("model")
    try:
        profile_raw = json.dumps(profile, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False).encode("utf-8")
        if profile.get("encoding") != "test-char" or profile.get("counting_method") != "test":
            return False, "coordinated offline proof requires deterministic test-char counting"
        exact = providers.final_payload_measurement(request_raw, profile, counter=lambda value: value)
    except Exception as exc:
        return False, "stored request/profile invalid: %s" % type(exc).__name__
    if hashlib.sha256(profile_raw).hexdigest() != policy["profile_digest"] \
            or measurement.get("request_digest") != row["request_digest"] \
            or measurement.get("profile_digest") != hashlib.sha256(profile_raw).hexdigest() \
            or measurement.get("final_payload_sha256") != exact["final_payload_sha256"] \
            or measurement != exact:
        return False, "exact request measurement/profile binding invalid"
    expected = request.get("primary_unit_ids")
    if expected != sorted(unit["id"] for unit in manifest["units"]):
        return False, "request must cover the complete coordinated task manifest"
    if proof.get("primary_unit_hashes") != {u["id"]:u["sha256"] for u in manifest["units"]}:
        return False, "request primary source hashes differ"
    for unit in manifest["units"]:
        a,b = unit["range"]
        if request.get("materials",{}).get("source_"+unit["id"]) != source[a:b].decode("utf-8"):
            return False, "request material differs from source"
    response_ok, _reason = providers.validate_response(response, sorted(expected), row["response_digest"])
    if not response_ok or response.get("evidence_class") != "TEST_ONLY":
        return False, "stored response is not a complete observed result"
    records = [response["results"][unit_id] for unit_id in expected]
    rich_ok, _errors = results.validate_rich_results(records, source, manifest, row["task_digest"],
                                                     attempt_id, expected_ids=expected)
    if not rich_ok or any(r.get("disposition") != "resolved" for r in records):
        return False, "stored result records are not full source-attached evidence"
    approval = db.execute("SELECT * FROM approvals WHERE id=? AND attempt_id=?", (row["approval_id"], attempt_id)).fetchone()
    if approval is None or approval["consumed"] != 1 or approval["request_digest"] != row["request_digest"] \
            or any(approval[key] != profile.get(key) for key in ("provider", "model", "endpoint", "purpose")) \
            or approval["max_output_tokens"] != profile.get("output_limit"):
        return False, "consumed approval is not bound to the actual request"
    try:
        limits = json.loads(approval["limits_json"])
    except (TypeError, ValueError):
        return False, "approval limits are malformed"
    if limits.get("max_spend") != profile.get("max_spend", 0):
        return False, "approval spend limit differs from request profile"
    return True, {"attempt_id":attempt_id,"request_digest":row["request_digest"],
                  "response_digest":row["response_digest"],"measurement_digest":measurement_digest,
                  "approval_id":row["approval_id"]}


def _complete_proof(db, work_item_id, artifacts_dir, policy):
    attempt_id = ledger.accepted_attempt(db, work_item_id)
    if not attempt_id:
        return False, "no current accepted CM attempt"
    return _attempt_proof(db, work_item_id, artifacts_dir, policy, attempt_id, True)


def evaluate(db, work_item_id, artifacts_dir, current_context, phase):
    """Return a structured current-applicability decision, never mutate state."""
    checked = ledger.verify_history(db)
    if checked["internal_chain"]!="VERIFIED" or checked["projection_replay"]=="FAILED":
        return {"ok":False,"coordinated":True,"phase":phase,"blocked":[work_item_id],
                "ready":[],"reason":"E_COORD_HISTORY: altered history/projection cannot select OFF mode"}
    registered = _load(db, work_item_id)
    if registered is None:
        return {"ok": True, "coordinated": False, "phase": phase, "blocked": [], "ready": []}
    if ledger.unresolved_delivery(db,work_item_id) is not None:
        return {"ok":False,"coordinated":True,"phase":phase,"blocked":[work_item_id],
                "ready":[],"reason":"E_COORD_DELIVERY_UNKNOWN: retained uncertain delivery requires reconciliation or a distinct approved run/basis"}
    policy, frozen_digest = registered
    try:
        own_context, contexts = _split_context(current_context, work_item_id)
        snapshot = _validate_context(own_context, policy, frozen_digest)
        try:
            stored = artifacts.open_verified(artifacts_dir,frozen_digest)
        except (OSError,TypeError) as exc:
            _fail("E_COORD_GRAPH_CAS","frozen graph artifact unavailable: "+str(exc))
        if stored!=_canonical(snapshot):
            _fail("E_COORD_GRAPH_CAS","frozen graph artifact differs from exact observed snapshot")
    except ledger.LedgerError as exc:
        return {"ok": False, "coordinated": True, "phase": phase,
                "blocked": [work_item_id], "ready": [], "reason": str(exc)}
    blocked = []
    ready = []
    prerequisites = {}
    for predecessor in _hard_predecessors(snapshot, work_item_id):
        parent = _load(db, predecessor)
        if parent is None:
            blocked.append(predecessor + ": unregistered prerequisite")
            continue
        parent_policy, parent_digest = parent
        if parent_policy["workspace_id"] != policy["workspace_id"] or \
                parent_policy["requirement_digest"] != policy["requirement_digest"] or \
                parent_digest != frozen_digest:
            blocked.append(predecessor + ": foreign or changed prerequisite basis")
            continue
        try:
            parent_context = contexts.get(predecessor)
            if parent_context is None:
                _fail("E_COORD_CONTEXT", "fresh prerequisite context missing for %s" % predecessor)
            _validate_context(parent_context, parent_policy, parent_digest)
        except ledger.LedgerError as exc:
            blocked.append(predecessor + ": " + str(exc))
            continue
        complete, detail = _complete_proof(db, predecessor, artifacts_dir, parent_policy)
        if complete:
            ancestor = evaluate(db, predecessor, artifacts_dir, {"contexts":contexts}, "consume")
            if not ancestor["ok"]:
                blocked.append(predecessor+": stale dependency closure "+str(ancestor.get("blocked")))
                continue
            ready.append(predecessor)
            prerequisites[predecessor] = detail
        else:
            blocked.append(predecessor + ": " + detail)
    basis = {"policy_digest":_digest(policy),"snapshot_digest":frozen_digest,"prerequisites":prerequisites}
    if not blocked and phase in ("consume","report","recall","resume"):
        accepted = ledger.accepted_attempt(db,work_item_id)
        if accepted:
            complete, detail = _complete_proof(db,work_item_id,artifacts_dir,policy)
            if not complete:
                blocked.append(work_item_id+": "+detail)
            else:
                request = json.loads(artifacts.open_verified(artifacts_dir,detail["request_digest"]))
                if request.get("materials",{}).get("context_coordination_basis") != _canonical(basis).decode("utf-8"):
                    blocked.append(work_item_id+": historical prerequisite basis no longer applicable")
    return {"ok": not blocked, "coordinated": True, "phase": phase,
            "blocked": blocked, "ready": ready, "snapshot_digest": frozen_digest,
            "revision": snapshot["revision"], "basis":basis}


def guard(db, work_item_id, artifacts_dir, current_context, phase, attempt_id=None):
    """Fail closed before every coordinated execution/consumption boundary."""
    if _load(db,work_item_id) is not None:
        checked = ledger.verify_history(db)
        if checked["internal_chain"]!="VERIFIED" or checked["projection_replay"]!="VERIFIED":
            _fail("E_COORD_HISTORY","unverified or altered canonical history/projections")
    result = evaluate(db, work_item_id, artifacts_dir, current_context, phase)
    if not result["ok"]:
        reason = result.get("reason") or "; ".join(result.get("blocked", [])) or "not applicable"
        prefix = ("E_COORD_CONTEXT" if str(reason).startswith(("E_COORD_CONTEXT", "E_COORD_SCHEMA"))
                  else "E_COORD_BLOCKED")
        _fail(prefix, reason)
    if attempt_id is not None:
        row = db.execute("SELECT work_item_id FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        if row is None or row["work_item_id"] != work_item_id:
            _fail("E_COORD_ATTEMPT", "attempt does not belong to guarded work item")
        if result["coordinated"] and phase != "prepare":
            row = db.execute("SELECT request_digest FROM attempts WHERE id=?",(attempt_id,)).fetchone()
            request = json.loads(artifacts.open_verified(artifacts_dir,row["request_digest"]))
            if request.get("materials",{}).get("context_coordination_basis") != _canonical(result["basis"]).decode("utf-8"):
                _fail("E_COORD_BASIS","prepared prerequisite/graph basis changed; old approval cannot be reused")
    return result


def require_transition_guard(db, attempt_id, coordination_context=None, to_state="ACCEPTED"):
    """Low-level ACCEPTED guard called by ledger.transition.

    All protected state transitions recheck the module-owned policy. Acceptance
    re-reads real evidence; no caller token or persistent boolean can pass it.
    """
    row = db.execute("SELECT work_item_id FROM attempts WHERE id=?", (attempt_id,)).fetchone()
    if row is None or _load(db, row["work_item_id"]) is None:
        return True
    # The ledger accepts an opaque sidecar only from the runner so it can
    # re-evaluate against the same CAS before its atomic ACCEPTED transition.
    if not isinstance(coordination_context, dict) or set(coordination_context) != {"context", "artifacts_dir"} \
            or not isinstance(coordination_context["artifacts_dir"], str):
        _fail("E_COORD_CONTEXT", "accept transition requires runner context and artifacts directory")
    phase = {"PREPARED":"prepare","DISPATCHING":"dispatch","ACCEPTED":"accept"}[to_state]
    guard(db, row["work_item_id"], coordination_context["artifacts_dir"],
          coordination_context["context"], phase, attempt_id)
    if to_state == "ACCEPTED":
        policy, _ = _load(db,row["work_item_id"])
        ok, detail = _attempt_proof(db,row["work_item_id"],coordination_context["artifacts_dir"],policy,attempt_id,False)
        if not ok:
            _fail("E_COORD_ACCEPT_GUARD",detail)
    return True


def ready_blocked(db, artifacts_dir, current_contexts):
    """Evaluate every registered task; caller must provide a context per task.

    Missing contexts are reported as blocked instead of being silently omitted,
    preventing top-k/pagination views from hiding a dependency blocker.
    """
    rows = db.execute("SELECT key FROM meta WHERE key LIKE 'coordination:%' AND key NOT LIKE 'coordination:accept-proof:%' ORDER BY key").fetchall()
    out = {"ready": [], "blocked": {}}
    for row in rows:
        work_item_id = row["key"].split(":", 1)[1]
        context = current_contexts if set(current_contexts)=={"contexts"} else {"contexts":current_contexts}
        decision = evaluate(db, work_item_id, artifacts_dir, context, "report")
        if ledger.accepted_attempt(db,work_item_id):
            if not decision["ok"]:
                out["blocked"][work_item_id] = decision.get("blocked") or [decision.get("reason","unknown")]
            continue
        if decision["ok"]:
            out["ready"].append(work_item_id)
        else:
            out["blocked"][work_item_id] = decision.get("blocked") or [decision.get("reason", "unknown")]
    return out
