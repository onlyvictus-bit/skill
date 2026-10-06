#!/usr/bin/env python3
"""M2: composed readiness from separate layer verdicts. No counters override.

Overall is READY_FOR_DECLARED_TASK only when every required layer is READY.
A NOT_REQUIRED layer needs a stated reason. Progress counts are reported for
information and can never flip the headline.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

LAYERS = ("scope", "extraction", "coverage", "execution", "results",
          "semantic", "persistence")
READY = "READY"
PARTIAL = "PARTIAL"
BLOCKED = "BLOCKED"
STALE = "STALE"
FAILED = "FAILED"
NOT_REQUIRED = "NOT_REQUIRED"
OVERALL = ("READY_FOR_DECLARED_TASK", "PARTIAL", "BLOCKED", "STALE", "FAILED")


class ReportError(ValueError):
    pass


def compose(layers, reasons=None, counts=None):
    """Format a layer map. FORMATTER ONLY: accepting caller layers as proof
    is a trust-boundary error (all-exempt maps still compose READY here).
    Authoritative gates must use compose_verified() with observed evidence."""
    reasons = reasons or {}
    unknown = sorted(set(layers) - set(LAYERS))
    if unknown:
        raise ReportError("E_LAYER_UNKNOWN: %s" % (", ".join(unknown)))
    missing = sorted(set(LAYERS) - set(layers))
    if missing:
        raise ReportError("E_LAYER_MISSING: %s" % (", ".join(missing)))
    for name, verdict in layers.items():
        if verdict not in (READY, PARTIAL, BLOCKED, STALE, FAILED, NOT_REQUIRED):
            raise ReportError("E_LAYER_VALUE: %s=%r" % (name, verdict))
        if verdict == NOT_REQUIRED and not (reasons.get(name) or "").strip():
            raise ReportError("E_LAYER_REASON: NOT_REQUIRED needs a reason: %s" % (name,))
    required = {n: v for n, v in layers.items() if v != NOT_REQUIRED}
    if any(v == FAILED for v in required.values()):
        overall = "FAILED"
    elif any(v == BLOCKED for v in required.values()):
        overall = "BLOCKED"
    elif any(v == STALE for v in required.values()):
        overall = "STALE"
    elif any(v == PARTIAL for v in required.values()):
        overall = "PARTIAL"
    else:
        overall = "READY_FOR_DECLARED_TASK"
    return {"overall": overall, "layers": dict(layers), "reasons": dict(reasons),
            "counts": dict(counts or {})}


def compose_verified(layers, reasons=None, evidence=None, empty_set_authorized=False,
                     evidence_root=None):
    """Authoritative composition: READY layers must cite observed evidence.

    evidence: {layer: [evidence_digest, ...]} of digests produced by the
    engine/ledger/extraction/semantic/watchdog runs behind each layer.
    A READY layer with no cited evidence, or an all-NOT_REQUIRED map without
    empty_set_authorized, composes BLOCKED, never READY.
    """
    reasons = reasons or {}
    evidence = evidence or {}
    out = compose(layers, reasons)
    if out["overall"] != "READY_FOR_DECLARED_TASK":
        return out
    required = [n for n, v in layers.items() if v != NOT_REQUIRED]
    if not required and not empty_set_authorized:
        return {"overall": "BLOCKED", "layers": dict(layers), "reasons": dict(reasons),
                "counts": {}, "blockers": ["E_EVIDENCE_EMPTY_SET: no required layer; "
                                           "empty-set operations need explicit authorization"]}
    blockers = []
    root = Path(evidence_root).resolve() if evidence_root is not None else None
    for name in required:
        digests = evidence.get(name, [])
        if not isinstance(digests, list) or not digests:
            blockers.append("E_EVIDENCE_MISSING: layer %s cites no observed evidence" % (name,))
            continue
        # A string that looks like a digest has no authority by itself.  The
        # caller must bind it to a real, non-symlinked file beneath the proof
        # root; the fresh verifier below independently re-derives all claims.
        if root is None:
            blockers.append("E_EVIDENCE_UNRESOLVED: layer %s has no proof root" % name)
            continue
        for item in digests:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                blockers.append("E_EVIDENCE_SHAPE: layer %s needs path+sha256 proof" % name)
                break
            try:
                untrusted = root / item["path"]
                if untrusted.is_symlink() or any(parent.is_symlink() for parent in untrusted.parents
                                                  if parent != root.parent):
                    raise ValueError("symlink")
                path = untrusted.resolve()
                path.relative_to(root)
                actual = _sha256_file(path)
            except (OSError, TypeError, ValueError):
                blockers.append("E_EVIDENCE_PATH: layer %s proof is unavailable" % name)
                break
            if path.is_symlink() or actual != item["sha256"] or not _is_sha256(actual):
                blockers.append("E_EVIDENCE_HASH: layer %s proof is unbound" % name)
                break
    if blockers:
        return {"overall": "BLOCKED", "layers": dict(layers), "reasons": dict(reasons),
                "counts": {}, "blockers": blockers}
    # This function intentionally remains a display formatter.  A local file
    # can prove only its own bytes, not that it was the engine/ledger evidence
    # for a particular source/task/run.  `verify_run` derives that linkage.
    return {"overall": "BLOCKED", "layers": dict(layers), "reasons": dict(reasons),
            "counts": {}, "blockers": ["E_EVIDENCE_FORMATTER_ONLY: use verify_run for authoritative status"],
            "evidence": {n: list(evidence.get(n, [])) for n in required}}


RUN_REQUIRED = {"source.bin", "manifest.json", "task.json", "profile.json", "scope.json",
                "extraction.json", "semantic.json", "ledger.sqlite"}


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _is_sha256(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _canonical_digest(record, excluded):
    body = {key: value for key, value in record.items() if key not in excluded}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _blocked(*items, overall="BLOCKED", counts=None):
    return {"overall": overall, "ok": False, "blockers": list(items),
            "counts": dict(counts or {}), "evidence_class": "TEST_ONLY"}


def _read_json(path, label):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReportError("E_RUN_%s_JSON: %s" % (label.upper(), exc))
    if not isinstance(value, dict):
        raise ReportError("E_RUN_%s_TYPE: expected an object" % label.upper())
    return value


def _validate_v3_binding(record, label, run_map):
    needed = {"schema_version", "source_id", "source_digest", "task_digest", "generation"}
    if not needed <= set(record) or record.get("schema_version") != 3:
        raise ReportError("E_RUN_%s_SCHEMA: expected schema v3 binding" % label.upper())
    expected = {"source_id": run_map["source_id"],
                "source_digest": run_map["source_digests"].get(run_map["source_id"]),
                "task_digest": run_map["task_digest"], "generation": run_map["generation"]}
    for key, value in expected.items():
        if record.get(key) != value:
            raise ReportError("E_RUN_%s_BINDING: %s differs from run map" % (label.upper(), key))


def _validate_ledger(ledger_path, root, run_map, source, manifest):
    """Read, never mutate, the companion SQLite evidence and CAS records."""
    try:
        db = sqlite3.connect("file:%s?mode=ro" % ledger_path.as_posix(), uri=True)
        db.row_factory = sqlite3.Row
        version = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        if version is None or version["value"] != "4":
            raise ReportError("E_LEDGER_SCHEMA: expected schema 4")
        pending = db.execute("SELECT id FROM attempts WHERE state NOT IN ('ACCEPTED','REFUSED','TRUNCATED','RETRYABLE_ERROR','INVALID_RESULT','DELIVERY_UNKNOWN','CANCELLED','STALE')").fetchall()
        if pending:
            raise ReportError("E_LEDGER_TRANSIENT: unfinished attempt evidence")
        rows = db.execute("SELECT w.id work_id,w.task_digest,w.source_id,a.id attempt_id,a.state,a.request_digest,a.response_digest,a.approval_id,ap.request_digest approval_request,ap.provider,ap.model,ap.endpoint,ap.purpose,ap.max_output_tokens,ap.limits_json,ap.consumed FROM accepted ac JOIN attempts a ON a.id=ac.attempt_id JOIN work_items w ON w.id=a.work_item_id LEFT JOIN approvals ap ON ap.id=a.approval_id WHERE ac.revoked=0").fetchall()
    except sqlite3.Error as exc:
        raise ReportError("E_LEDGER_READ: %s" % exc)
    finally:
        try:
            db.close()
        except Exception:
            pass
    expected = [u["id"] for u in manifest.get("units", [])]
    records, blockers = [], []
    for row in rows:
        values = dict(row)
        if values["state"] != "ACCEPTED" or values["task_digest"] != run_map["task_digest"] or values["source_id"] != run_map["source_id"]:
            blockers.append("E_LEDGER_BINDING: accepted row is not bound to frozen work")
            continue
        if not all(isinstance(values.get(k), str) and _is_sha256(values[k]) for k in ("request_digest", "response_digest", "approval_request")):
            blockers.append("E_LEDGER_ARTIFACT: accepted row lacks bound request/response/approval")
            continue
        if values["request_digest"] != values["approval_request"] or values["consumed"] != 1:
            blockers.append("E_LEDGER_APPROVAL: approval is not exact and consumed")
            continue
        if not all(isinstance(values.get(k), str) and values[k].strip() for k in ("provider", "model", "endpoint", "purpose")) or not isinstance(values["max_output_tokens"], int) or values["max_output_tokens"] <= 0:
            blockers.append("E_LEDGER_APPROVAL: approval basis is incomplete")
            continue
        for digest, kind in ((values["request_digest"], "request"), (values["response_digest"], "response")):
            p = root / "artifacts" / digest
            if not p.is_file() or p.is_symlink() or _sha256_file(p) != digest:
                blockers.append("E_LEDGER_%s: CAS artifact absent or mismatched" % kind.upper())
        try:
            request = _read_json(root / "artifacts" / values["request_digest"], "request")
        except ReportError as exc:
            blockers.append(str(exc)); continue
        expected_task = run_map["task_digest"]
        primary = request.get("primary_unit_ids")
        if request.get("kind") != "complete-request" or request.get("work_item_id") != values["work_id"] \
                or request.get("task_digest") != expected_task or request.get("task_spec_digest") != expected_task \
                or not isinstance(primary, list) or not primary or len(primary) != len(set(primary)) \
                or any(unit_id not in expected for unit_id in primary):
            blockers.append("E_REQUEST_BINDING: request does not bind accepted work/task/primary units")
            continue
        model = request.get("model")
        if not isinstance(model, dict) or any(model.get(key) != values[key] for key in ("provider", "model", "endpoint", "purpose")) \
                or model.get("output_limit") != values["max_output_tokens"]:
            blockers.append("E_REQUEST_APPROVAL: request profile differs from consumed approval")
            continue
        try:
            limits = json.loads(values.get("limits_json") or "{}")
        except (TypeError, ValueError):
            blockers.append("E_LEDGER_LIMITS: approval limits are unreadable"); continue
        if not isinstance(limits, dict) or limits.get("max_spend") != model.get("max_spend"):
            blockers.append("E_LEDGER_LIMITS: request spend basis differs from approval"); continue
        materials = request.get("materials")
        if not isinstance(materials, dict):
            blockers.append("E_REQUEST_MATERIALS: request source material absent"); continue
        table = {unit["id"]: unit for unit in manifest.get("units", [])}
        if any(materials.get("source_" + unit_id) != source[table[unit_id]["range"][0]:table[unit_id]["range"][1]].decode("utf-8")
               for unit_id in primary):
            blockers.append("E_REQUEST_SOURCE: request material differs from frozen source"); continue
        try:
            record = _read_json(root / "artifacts" / values["response_digest"], "response")
        except ReportError as exc:
            blockers.append(str(exc)); continue
        if record.get("terminal_state") != "ok" or record.get("evidence_class") != "TEST_ONLY" or not isinstance(record.get("results"), dict) or not record["results"]:
            blockers.append("E_RESULT_ENVELOPE: response must be a TEST_ONLY successful result map"); continue
        required = {"schema_version", "unit_id", "source_digest", "attempt_id", "original_excerpt",
                    "excerpt_sha256", "interpretation", "findings", "disposition", "task_digest"}
        if sorted(record["results"]) != sorted(primary):
            blockers.append("E_RESULT_REQUEST_SCOPE: response units differ from request primary units"); continue
        for unit_id, rich in record["results"].items():
            if not isinstance(rich, dict) or set(rich) != required or rich.get("unit_id") != unit_id or rich.get("schema_version") != 2 or rich.get("attempt_id") != values["attempt_id"] or rich.get("task_digest") != run_map["task_digest"]:
                blockers.append("E_RESULT_BINDING: rich result schema or identity invalid"); continue
            unit = next((u for u in manifest.get("units", []) if u.get("id") == unit_id), None)
            if unit is None:
                blockers.append("E_RESULT_UNIT: foreign result unit"); continue
            excerpt = source[unit["range"][0]:unit["range"][1]].decode("utf-8")
            if rich.get("source_digest") != run_map["source_digests"][run_map["source_id"]] or rich.get("original_excerpt") != excerpt or rich.get("excerpt_sha256") != hashlib.sha256(excerpt.encode("utf-8")).hexdigest() or not isinstance(rich.get("interpretation"), str) or not rich["interpretation"].strip() or not isinstance(rich.get("findings"), list):
                blockers.append("E_RESULT_CONTENT: rich result fails frozen source validation"); continue
            records.append(rich)
    found = [r["unit_id"] for r in records]
    if sorted(found) != sorted(expected) or len(found) != len(set(found)):
        blockers.append("E_RESULT_COVERAGE: accepted rich results do not exactly cover manifest units")
    return records, blockers


def verify_run(run_map_path, source_digests_now, claude_mon_root):
    """Fresh disk verifier for the R2 offline layout; no caller verdict is trusted."""
    from integrity_v2 import engine_client, recall, semantic, source_audit
    try:
        loaded = recall.load_run_map(run_map_path, source_digests_now)
    except Exception as exc:
        message = str(exc)
        return _blocked(message, overall="STALE" if message.startswith("E_RUNMAP_STALE") else "BLOCKED")
    run_map = loaded["run_map"]
    if not loaded["current"]:
        return _blocked("E_RUN_STALE: source version changed", overall="STALE")
    root = Path(run_map["run_dir"]).resolve()
    try:
        ok, _handshake = engine_client.handshake(
            claude_mon_root, expect_schema_version=2,
            expect_digest=source_audit.PINNED_SCHEMA_DIGEST)
        if not ok:
            raise ReportError("E_RUN_COMPANION: explicit companion handshake/pin failed")
        artifacts = run_map["artifact_digests"]
        if not RUN_REQUIRED <= set(artifacts):
            raise ReportError("E_RUN_ARTIFACTS: missing required proof file")
        source = (root / "source.bin").read_bytes()
        if hashlib.sha256(source).hexdigest() != run_map["source_digests"][run_map["source_id"]]:
            raise ReportError("E_RUN_SOURCE: source.bin is not frozen source")
        manifest = _read_json(root / "manifest.json", "manifest")
        task = _read_json(root / "task.json", "task")
        profile = _read_json(root / "profile.json", "profile")
        scope = _read_json(root / "scope.json", "scope")
        extraction = _read_json(root / "extraction.json", "extraction")
        semantic_record = _read_json(root / "semantic.json", "semantic")
        if manifest.get("source_id") != run_map["source_id"] or manifest.get("source_digest") != run_map["source_digests"][run_map["source_id"]]:
            raise ReportError("E_RUN_MANIFEST_BINDING")
        manifest_errors = source_audit.validate_with_engine(claude_mon_root, source, manifest)
        if manifest_errors:
            raise ReportError("E_RUN_MANIFEST: " + repr(manifest_errors))
        task_digest = _canonical_digest(task, {"task_digest"})
        profile_digest = _canonical_digest(profile, {"profile_digest"})
        if ("task_digest" in task and task["task_digest"] != task_digest) \
                or ("profile_digest" in profile and profile["profile_digest"] != profile_digest):
            raise ReportError("E_RUN_TASK_PROFILE_SELF_DIGEST")
        if task_digest != run_map["task_digest"] or profile_digest != run_map["profile_digest"]:
            raise ReportError("E_RUN_TASK_PROFILE_BINDING")
        for label, record in (("scope", scope), ("extraction", extraction), ("semantic", semantic_record)):
            _validate_v3_binding(record, label, run_map)
        expected_ids = [u.get("id") for u in manifest.get("units", [])]
        if not expected_ids or len(expected_ids) != len(set(expected_ids)):
            raise ReportError("E_RUN_MANIFEST_UNITS")
        if scope.get("required_unit_ids") != expected_ids:
            raise ReportError("E_RUN_SCOPE_COVERAGE")
        if extraction.get("expected") != {"units": len(expected_ids)} or extraction.get("produced") != {"units": len(expected_ids)} or extraction.get("diagnostics") != [] or extraction.get("evidence_class") != "TEST_ONLY" or extraction.get("format") != "utf8-text":
            raise ReportError("E_RUN_EXTRACTION")
        reviews = semantic_record.get("reviews")
        ready, semantic_blockers = semantic.strict_ready(reviews, expected_ids=expected_ids,
                                                         source_digest=run_map["source_digests"][run_map["source_id"]], task_digest=run_map["task_digest"])
        records, ledger_blockers = _validate_ledger(root / "ledger.sqlite", root, run_map, source, manifest)
        ledger_blockers.extend(source_audit.validate_saved_run_with_engine(claude_mon_root, root))
        counts = {"units": len(expected_ids), "accepted_results": len(records), "reviews": len(reviews) if isinstance(reviews, list) else 0}
        if ledger_blockers:
            return _blocked(*ledger_blockers, counts=counts)
        if not ready:
            return _blocked("E_RUN_SEMANTIC: " + repr(semantic_blockers), overall="PARTIAL", counts=counts)
    except (ReportError, OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        return _blocked(str(exc))
    return {"overall": "VERIFIED_OFFLINE", "ok": True, "blockers": [], "counts": counts,
            "evidence_class": "TEST_ONLY", "semantic_limit": "review evidence only; not comprehension proof"}


def verify_coordinated_workspace(args):
    """R3 report/recall route; owning CM guard rechecks current closure/history.

    Core R2 run maps cannot substitute for a coordinated task. The public
    route also rereads every declared current source before consuming proof.
    """
    import coordination_workflow
    return coordination_workflow.verify(args)
