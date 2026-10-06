#!/usr/bin/env python3
"""M9: offline acceptance driver. No network, no live models, no installs.

run_full_pipeline() drives freeze -> manifest -> budget -> ledger attempts
-> results -> semantic callbacks -> report on synthetic corpora with a
scripted TEST_ONLY adapter. Semantic judgment is injected as a callable
(the memory-integrity checker in tests), never invented here. Fault
entrypoints expose each injection separately so tests assert block-or-recover
per case. Mechanical scale is measured separately from semantic depth.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import (artifacts, budget, inventory, ledger,  # noqa: E402
                              partition, providers, results, runner)


def words(text):
    return text.split()


def default_profile(**over):
    base = {"schema_version": 2, "provider": "test-only", "model": "acceptance-1",
            "encoding": "e", "encoding_version": "v", "context_limit": 1000000,
            "output_limit": 100000, "counting_method": "synthetic-word-split",
            "endpoint": "test-only-transport", "purpose": "acceptance", "max_spend": 0}
    base.update(over)
    return base


def run_full_pipeline(work_root, filename, data, task, interpretations=None,
                      per_unit_output=50, profile=None):
    """Full offline pipeline (adapter leg carries recorded markers; content is
    verified afterwards by results/semantic checks, never by this driver)."""
    profile = profile or default_profile()
    interpretations = interpretations or {}
    root = Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / filename).write_bytes(data)
    db = ledger.connect(root / "ledger.db")
    art = str(root / "artifacts")
    try:
        scope = inventory.freeze_scope(root, [filename])
        manifest = partition.build_manifest("SRC-ACC", data)
        assert partition.validate_manifest(data, manifest) == []
        units = {u["id"]: data[u["range"][0]:u["range"][1]].decode("utf-8")
                 for u in manifest["units"]}
        measurement = budget.measure_request(
            profile, {"instructions": task["instructions"],
                      "schema": json.dumps(task["schema"], sort_keys=True),
                      **{"source_%s" % k: v for k, v in units.items()}}, counter=words)
        batches = budget.plan_batches(
            profile, [{"id": k, "input_tokens": len(v.split())} for k, v in units.items()],
            per_unit_output)["batches"]
        accepted, results_out = [], []
        for chunk in manifest["chunks"]:
            wid = chunk["id"]
            ledger.create_work_item(db, wid, task["digest"], "SRC-ACC")
            attempt, _ = runner.prepare(
                db, art, wid, task["digest"],
                {uid: units[uid] for uid in chunk["primary"]},
                task["instructions"], {"type": "object"}, {}, task["spec_digest"],
                profile, counter=words, manifest=manifest, source_bytes=data)
            runner.approve(db, attempt, "acceptance-approval")
            row = db.execute("SELECT request_digest FROM attempts WHERE id=?",
                             (attempt,)).fetchone()
            approval = ledger.issue_approval(
                db, attempt, row["request_digest"], profile["provider"], profile["model"],
                profile["endpoint"], profile["purpose"], profile["output_limit"],
                {"max_spend": profile["max_spend"]})
            script = [("ok", {uid: results.make_result(
                data, manifest, uid, task["digest"], attempt,
                interpretations.get(uid, "recorded")) for uid in chunk["primary"]})]
            runner.dispatch_via_adapter(db, art, providers.TestOnlyAdapter(script),
                                        attempt, approval)
            runner.accept(db, art, attempt, task["digest"], manifest, data,
                          {"provider": profile["provider"], "model": profile["model"],
                           "endpoint": profile["endpoint"], "purpose": profile["purpose"],
                           "max_output_tokens": profile["output_limit"]})
            accepted.append(attempt)
            for uid in chunk["primary"]:
                results_out.append(results.make_result(
                    data, manifest, uid, task["digest"], attempt,
                    interpretations.get(uid, "recorded: no interpretation supplied")))
        return {"units": len(units), "chunks": len(manifest["chunks"]),
                "batches": len(batches), "accepted": len(accepted),
                "measurement_methods": measurement["methods"],
                "scope_digest": scope["scope_digest"],
                "manifest_digest": manifest["manifest_digest"],
                "results": results_out, "manifest": manifest, "data": data,
                "db_path": str(root / "ledger.db"), "artifacts": art}
    finally:
        db.close()


def fault_omit_file(work_root):
    root = Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    try:
        inventory.freeze_scope(root, ["absent.txt"])
        return {"blocked": False}
    except Exception as exc:
        return {"blocked": True, "error": "%s: %s" % (type(exc).__name__, exc)}


def fault_empty_scope():
    from complete_read_v2.inventory import EmptyScopeError
    try:
        inventory.freeze_scope(Path(work_root_tmp()), [])
        return {"blocked": False}
    except EmptyScopeError as exc:
        return {"blocked": True, "error": str(exc)}


def work_root_tmp():
    import tempfile
    tmp = tempfile.mkdtemp(prefix="fault-")
    return tmp


def fault_swap_manifest(data_a, data_b):
    man_b = partition.build_manifest("SRC-B", data_b)
    errors = partition.validate_manifest(data_a, man_b)
    return {"blocked": bool(errors), "errors": errors}


def fault_duplicate_chunk(data):
    man = partition.build_manifest("SRC-1", data)
    man["chunks"].append(dict(man["chunks"][0]))
    errors = partition.validate_manifest(data, man)
    return {"blocked": bool(errors), "errors": errors}


def fault_wrong_payload(data):
    man = partition.build_manifest("SRC-1", data)
    man["chunks"][0]["payload_sha256"] = "0" * 64
    errors = partition.validate_manifest(data, man)
    return {"blocked": bool(errors), "errors": errors}


def fault_gap(data):
    man = partition.build_manifest("SRC-1", data)
    victim = man["units"][0]["id"]
    man["units"] = [u for u in man["units"] if u["id"] != victim]
    for chunk in man["chunks"]:
        chunk["primary"] = [p for p in chunk["primary"] if p != victim]
    errors = partition.validate_manifest(data, man)
    return {"blocked": bool(errors), "errors": errors}


def fault_bad_encoding():
    try:
        partition.unitize(b"\xff\xfe\x80 bad")
        return {"blocked": False}
    except Exception as exc:
        return {"blocked": True, "error": "%s" % (exc,)}


def fault_oversize_unit():
    data = b"ok\n" + b"y" * 500 + b"\nend\n"
    man = partition.build_manifest("SRC-1", data, max_unit_bytes=100)
    errors = partition.validate_manifest(data, man)
    children = [u for u in man["units"] if u["parent"] is not None]
    over = [u for u in man["units"] if u["range"][1] - u["range"][0] > 100]
    return {"blocked": bool(errors), "errors": errors, "children": len(children),
            "oversize_remaining": len(over)}


def fault_task_change(work_root, data):
    import tempfile
    tmp = work_root or tempfile.mkdtemp(prefix="fault-task-")
    db = ledger.connect(str(Path(tmp) / "ledger.db"))
    try:
        ledger.create_work_item(db, "W1", "task-v1", "SRC-1")
        man = partition.build_manifest("SRC-1", data)
        ok, notes = runner.preflight(db, "W1", man, data, default_profile(), 50,
                                     expect_task_digest="task-v2", counter=words)
        return {"blocked": not ok, "notes": notes}
    finally:
        db.close()


def fault_corrupt_response_artifact(work_root, data):
    import tempfile
    tmp = work_root or tempfile.mkdtemp(prefix="fault-art-")
    db = ledger.connect(str(Path(tmp) / "ledger.db"))
    art = str(Path(tmp) / "artifacts")
    try:
        ledger.create_work_item(db, "W1", "t", "SRC-1")
        source = b"hi"
        manifest = partition.build_manifest("SRC-1", source)
        att, _ = runner.prepare(db, art, "W1", "t", {"U000001": "hi"}, "do",
                                {"type": "object"}, {}, "spec",
                                default_profile(), counter=words, manifest=manifest,
                                source_bytes=source)
        runner.approve(db, att, "ref")
        row = db.execute("SELECT request_digest FROM attempts WHERE id=?", (att,)).fetchone()
        p = default_profile()
        approval = ledger.issue_approval(db, att, row["request_digest"], p["provider"], p["model"],
                                         p["endpoint"], p["purpose"], p["output_limit"],
                                         {"max_spend": p["max_spend"]})
        runner.dispatch_via_adapter(
            db, art, providers.TestOnlyAdapter([("ok", {"U000001": "r"})]), att, approval)
        raw = db.execute("SELECT response_digest FROM attempts WHERE id=?",
                         (att,)).fetchone()["response_digest"]
        Path(art, raw).write_bytes(b"tampered")
        try:
            artifacts.open_verified(art, raw)
            return {"blocked": False}
        except artifacts.ArtifactError as exc:
            return {"blocked": True, "error": str(exc)}
    finally:
        db.close()
