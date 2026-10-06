#!/usr/bin/env python3
"""M1: scope/binding audit. Read-only: presence, hash freshness, manifest
binding, empty-scope refusal. Deep manifest validation is delegated to an
explicit claude-mon engine copy (same explicit-path rule as the handshake);
this module never validates with an implicit or bundled second implementation.
"""
import hashlib
import json
import sys
from pathlib import Path

PINNED_SCHEMA_DIGEST = "bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _scope_digest(sources):
    digest = hashlib.sha256()
    for entry in sorted(sources, key=lambda e: e["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def audit_scope(scope, current_files, manifests, engine_root=None,
                expected_schema_digest=PINNED_SCHEMA_DIGEST):
    """scope: freeze_scope record. current_files: {relpath: bytes}.
    manifests: {source_id: manifest dict}. Returns (verdict, findings list)."""
    findings = []
    if not isinstance(scope, dict) or scope.get("schema_version") != 2:
        return "BLOCKED", ["E_SCOPE_SCHEMA: scope is not a v2 scope record"]
    if scope.get("frozen") is not True or scope.get("verdict") != "FROZEN":
        return "BLOCKED", ["E_SCOPE_UNFROZEN: scope lacks a freeze record; "
                           "unfrozen caller dicts never satisfy an audit"]
    try:
        if scope.get("scope_digest") != _scope_digest(scope.get("sources", [])):
            return "BLOCKED", ["E_SCOPE_DIGEST: scope digest mismatch"]
    except (KeyError, TypeError, AttributeError):
        return "BLOCKED", ["E_SCOPE_SCHEMA: scope sources malformed"]
    if not scope.get("sources"):
        return "BLOCKED", ["E_EMPTY_SCOPE: required source set is empty"]
    if engine_root is not None:
        from integrity_v2 import engine_client
        if not isinstance(expected_schema_digest, str) or len(expected_schema_digest) != 64:
            return "BLOCKED", ["E_ENGINE_PIN: a 64-character pinned schema digest is required"]
        ok, payload = engine_client.handshake(engine_root, expect_schema_version=2,
                                              expect_digest=expected_schema_digest)
        if not ok:
            return "BLOCKED", ["E_ENGINE_HANDSHAKE: %s"
                               % (payload.get("error", payload),)]
    by_path = {s["path"]: s for s in scope["sources"]}
    for rel in sorted(set(by_path) | set(current_files)):
        if rel not in current_files:
            findings.append("E_SOURCE_MISSING: registered but absent: %s" % (rel,))
            continue
        if rel not in by_path:
            findings.append("E_SCOPE_DRIFT: unregistered file appeared: %s" % (rel,))
            continue
        live = _sha256_bytes(current_files[rel])
        if live != by_path[rel]["sha256"]:
            findings.append("E_SOURCE_STALE: %s changed since freeze" % (rel,))
    by_id = {}
    for entry in scope["sources"]:
        manifest = manifests.get(entry["path"], manifests.get(entry.get("source_id", "")))
        if manifest is None:
            findings.append("E_MANIFEST_MISSING: no manifest for %s" % (entry["path"],))
            continue
        if manifest.get("source_digest") != _sha256_bytes(current_files.get(entry["path"], b"\x00")) \
                and entry["path"] in current_files:
            findings.append("E_SOURCE_BINDING_MISMATCH: manifest for %s bound elsewhere"
                            % (entry["path"],))
        by_id[entry["path"]] = manifest
    if engine_root is not None:
        for rel, manifest in by_id.items():
            if rel not in current_files:
                continue
            errors = validate_with_engine(engine_root, current_files[rel], manifest)
            findings.extend("E_MANIFEST_INVALID(%s): %s" % (rel, e) for e in errors)
    if any(f.startswith("E_SOURCE_MISSING") or f.startswith("E_EMPTY_SCOPE") for f in findings):
        return "BLOCKED", findings
    if findings:
        return "STALE", findings
    return "READY", []


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def validate_with_engine(engine_root, source_bytes, manifest):
    """Run partition.validate_manifest inside the explicit engine copy.

    Implemented via a subprocess hosted probe so this module never embeds a
    second copy of the partition rules. Returns a list of error strings.
    """
    import subprocess
    import tempfile
    probe = (
        "import json,sys;"
        "sys.path.insert(0,%r);"
        "from complete_read_v2 import partition;"
        "src=open(sys.argv[1],'rb').read();"
        "man=json.load(open(sys.argv[2]));"
        "print(json.dumps(partition.validate_manifest(src,man)))"
    ) % (str(Path(engine_root) / "scripts"),)
    with tempfile.TemporaryDirectory(prefix="source-audit-") as temp:
        src_path, man_path = str(Path(temp) / "src.bin"), str(Path(temp) / "man.json")
        Path(src_path).write_bytes(source_bytes)
        Path(man_path).write_text(json.dumps(manifest), encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, "-c", probe, src_path, man_path],
                                  text=True, capture_output=True, timeout=120)
        except (OSError, subprocess.SubprocessError) as exc:
            return ["E_ENGINE_PROBE: %s" % (exc,)]
    if proc.returncode != 0:
        return ["E_ENGINE_PROBE: %s" % ((proc.stderr or "")[-300:])]
    try:
        result = json.loads(proc.stdout)
    except (ValueError, TypeError):
        return ["E_ENGINE_PROBE_BAD_JSON"]
    return result if isinstance(result, list) else ["E_ENGINE_PROBE_BAD_SHAPE"]


def load_manifest_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_saved_run_with_engine(engine_root, run_dir):
    """Non-mutating companion proof inspection, through the explicit root."""
    import subprocess
    probe = ("import sys; sys.path.insert(0,%r); "
             "from complete_read_v2 import proof; proof.main()") % str(Path(engine_root) / "scripts")
    try:
        proc = subprocess.run([sys.executable, "-B", "-c", probe, str(run_dir)],
                              capture_output=True, text=True, encoding="utf-8", timeout=60)
        if proc.returncode != 0:
            return ["E_ENGINE_PROOF_EXIT: " + proc.stderr[-500:]]
        value = json.loads(proc.stdout)
        return value if isinstance(value, list) else ["E_ENGINE_PROOF_SHAPE"]
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return ["E_ENGINE_PROOF: " + str(exc)]
