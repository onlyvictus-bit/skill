"""Read-only R2 dispatch-basis verification; never invokes an adapter."""
import json
from pathlib import Path
import sqlite3
from . import artifacts, budget, ledger, providers


def inspect_run(root, run_map):
    root = Path(root)
    source = (root / "source.bin").read_bytes()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    task = json.loads((root / "task.json").read_text(encoding="utf-8"))
    profile0 = json.loads((root / "profile.json").read_text(encoding="utf-8"))
    profile = {k:v for k,v in profile0.items() if k != "profile_digest"}
    budget.validate_profile(profile)
    if profile.get("encoding") != "test-char" or profile.get("counting_method") != "test":
        return ["E_PROOF_COUNTING: fresh offline proof requires deterministic test-char profile"]
    table = {u["id"]:u for u in manifest["units"]}
    chunks = {c["id"]:c for c in manifest["chunks"]}
    cas = root / "artifacts"
    errors = []
    db = sqlite3.connect((root / "ledger.sqlite").resolve().as_uri()+"?mode=ro",uri=True)
    db.row_factory = sqlite3.Row
    try:
        checked_history = ledger.verify_history(db)
        if checked_history["internal_chain"] != "VERIFIED" or checked_history["projection_replay"] != "VERIFIED":
            return ["E_PROOF_HISTORY: "+json.dumps(checked_history,sort_keys=True)]
        rows = db.execute("SELECT a.* FROM attempts a JOIN accepted ac ON ac.attempt_id=a.id AND ac.work_item_id=a.work_item_id WHERE ac.revoked=0").fetchall()
        if {r["work_item_id"] for r in rows} != set(chunks) or len(rows) != len(chunks):
            return ["E_PROOF_CHUNK_SET: accepted work does not match exact manifest chunks"]
        for row in rows:
            raw = artifacts.open_verified(cas,row["request_digest"])
            request = json.loads(raw)
            chunk = chunks[row["work_item_id"]]
            if request.get("model") != profile or request.get("primary_unit_ids") != sorted(chunk["primary"]):
                errors.append("E_PROOF_REQUEST_PROFILE_SCOPE"); continue
            if request.get("materials",{}).get("instructions") != task.get("instructions"):
                errors.append("E_PROOF_INSTRUCTIONS"); continue
            proof = request.get("source_proof")
            if not isinstance(proof,dict) or proof.get("source_id") != manifest["source_id"] or proof.get("source_digest") != manifest["source_digest"] or proof.get("manifest_digest") != manifest["manifest_digest"]:
                errors.append("E_PROOF_SOURCE_BINDING"); continue
            frozen = artifacts.open_verified(cas,proof["source_artifact_digest"])
            frozen_manifest = json.loads(artifacts.open_verified(cas,proof["manifest_artifact_digest"]))
            if frozen != source or frozen_manifest != manifest or proof.get("primary_unit_hashes") != {i:table[i]["sha256"] for i in chunk["primary"]}:
                errors.append("E_PROOF_FROZEN_SOURCE"); continue
            for ident in chunk["context_before"]+chunk["context_after"]:
                start,end=table[ident]["range"]
                matches=[v for k,v in request["materials"].items() if k.startswith("context_") and k.endswith(ident)]
                if matches != [source[start:end].decode("utf-8")]:
                    errors.append("E_PROOF_CONTEXT_MATERIAL")
            md = ledger.request_measurement_binding(db,row["id"],row["request_digest"])
            if not md:
                errors.append("E_PROOF_MEASUREMENT_MISSING"); continue
            measured = json.loads(artifacts.open_verified(cas,md))
            exact = providers.final_payload_measurement(raw,profile,counter=lambda value:value)
            if measured != exact:
                errors.append("E_PROOF_MEASUREMENT_MISMATCH"); continue
            refs = [row["request_digest"],row["response_digest"],md,proof["source_artifact_digest"],proof["manifest_artifact_digest"]]
            if any(run_map["artifact_digests"].get("artifacts/"+d) != d for d in refs):
                errors.append("E_PROOF_CAS_MAP_BINDING"); continue
            response=json.loads(artifacts.open_verified(cas,row["response_digest"]))
            if any(r.get("disposition") != "resolved" for r in response["results"].values()):
                errors.append("E_PROOF_UNRESOLVED_RESULT")
    finally:
        db.close()
    return errors


def main():
    import sys
    try:
        root=Path(sys.argv[1])
        rm=json.loads((root / "run-map.json").read_text(encoding="utf-8"))
        output=inspect_run(root,rm)
    except Exception as exc:
        output=["E_PROOF_READ: "+type(exc).__name__+": "+str(exc)]
    print(json.dumps(output,ensure_ascii=True))

