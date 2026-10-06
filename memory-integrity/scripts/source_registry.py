#!/usr/bin/env python3
"""Canonical multi-source registry and source-basis auditor.

This binds a governed task to exact source identities. It composes with
source_coverage.py; it does not replace extraction or semantic auditing.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from . import source_coverage
except ImportError:  # direct script execution
    import source_coverage

SCHEMA_VERSION = 1
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
VALID_AUTHORITIES = {"AUTHORITATIVE", "SUPPORTING", "DERIVED", "EPHEMERAL"}


def _canonical_json_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _hash_file(path):
    return _sha256_bytes(Path(path).read_bytes())


def _rel_or_abs(path, base):
    p = Path(path).resolve()
    try:
        return str(p.relative_to(base.resolve()))
    except ValueError:
        return str(p)


def _resolve(stored, base):
    p = Path(stored)
    return p if p.is_absolute() else (base / p).resolve()


def _payload(registry):
    return {"schema_version": registry["schema_version"], "sources": registry["sources"]}


def _save_registry(path, registry):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    registry = dict(_payload(registry))
    registry["registry_sha256"] = _sha256_bytes(_canonical_json_bytes(_payload(registry)))
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registry


def init_registry(path):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError("registry already exists: %s" % path)
    return _save_registry(path, {"schema_version": SCHEMA_VERSION, "sources": []})


def load_registry(path):
    path = Path(path).resolve()
    registry = json.loads(path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported registry schema_version: %r" % registry.get("schema_version"))
    if not isinstance(registry.get("sources"), list):
        raise ValueError("registry sources must be a list")
    actual = _sha256_bytes(_canonical_json_bytes(_payload(registry)))
    if registry.get("registry_sha256") != actual:
        raise ValueError("registry_sha256 mismatch")
    return path, registry


def register_source(registry_path, source_id, source_path, manifest_path=None, receipts_path=None,
                    required=True, authority="AUTHORITATIVE", role="source"):
    rp, registry = load_registry(registry_path)
    if not isinstance(source_id, str) or not SOURCE_ID_RE.match(source_id):
        raise ValueError("invalid source_id %r" % source_id)
    if any(s.get("source_id") == source_id for s in registry["sources"]):
        raise ValueError("duplicate source_id %r" % source_id)
    if authority not in VALID_AUTHORITIES:
        raise ValueError("authority must be one of %s" % sorted(VALID_AUTHORITIES))
    source = Path(source_path).resolve()
    if not source.is_file():
        raise ValueError("source file not found: %s" % source)
    source_raw = source.read_bytes()

    manifest_sha256 = None
    canonical_source_sha256 = None
    extraction_status = None
    stored_manifest = None
    stored_receipts = None
    if manifest_path is not None:
        mp, manifest = source_coverage.load_manifest(manifest_path)
        canonical_source_sha256 = manifest["source_sha256"]
        manifest_sha256 = manifest["manifest_sha256"]
        extraction_status = (manifest.get("origin") or {}).get("extraction_status", "UNKNOWN")
        # Registry source_path denotes the authoritative source being bound.
        # For direct text this equals the manifest source. For extracted docs,
        # callers should register the original separately and the canonical
        # representation as another source if both are authoritative inputs.
        if _hash_file(source) != canonical_source_sha256:
            raise ValueError("registered source hash does not match coverage manifest source_sha256")
        stored_manifest = _rel_or_abs(mp, rp.parent)
        if receipts_path is not None:
            stored_receipts = _rel_or_abs(Path(receipts_path).resolve(), rp.parent)
    elif receipts_path is not None:
        raise ValueError("receipts_path requires manifest_path")

    entry = {
        "source_id": source_id,
        "source_path": _rel_or_abs(source, rp.parent),
        "registered_source_sha256": _sha256_bytes(source_raw),
        "source_size_bytes": len(source_raw),
        "required": bool(required),
        "authority": authority,
        "role": str(role),
        "coverage_manifest_path": stored_manifest,
        "coverage_receipts_path": stored_receipts,
        "manifest_sha256": manifest_sha256,
        "canonical_source_sha256": canonical_source_sha256,
        "extraction_status": extraction_status,
    }
    registry["sources"].append(entry)
    registry["sources"].sort(key=lambda s: s["source_id"])
    _save_registry(rp, registry)
    return entry


def _source_basis_digest(registry):
    basis = []
    for s in sorted((x for x in registry["sources"] if x.get("required")), key=lambda x: x["source_id"]):
        basis.append({
            "source_id": s["source_id"],
            "registered_source_sha256": s["registered_source_sha256"],
            "manifest_sha256": s.get("manifest_sha256"),
            "required": True,
            "authority": s.get("authority"),
            "role": s.get("role"),
        })
    return _sha256_bytes(_canonical_json_bytes({"schema_version": 1, "required_sources": basis}))


def audit_registry(registry_path):
    rp, registry = load_registry(registry_path)
    results = []
    blocked_required = []
    ready_required = 0
    required_total = 0

    for entry in sorted(registry["sources"], key=lambda s: s["source_id"]):
        required = bool(entry.get("required"))
        if required:
            required_total += 1
        source = _resolve(entry["source_path"], rp.parent)
        exists = source.is_file()
        current_hash = _hash_file(source) if exists else None
        registered_hash = entry["registered_source_sha256"]
        source_stale = current_hash != registered_hash

        coverage = "UNTRACKED"
        extraction = entry.get("extraction_status") or "UNKNOWN"
        coverage_overall = "BLOCKED"
        details = None
        mp = entry.get("coverage_manifest_path")
        rr = entry.get("coverage_receipts_path")
        if mp and rr:
            try:
                details = source_coverage.verify(_resolve(mp, rp.parent), _resolve(rr, rp.parent))
                coverage = details["coverage_status"]
                extraction = details["extraction_status"]
                coverage_overall = details["overall_status"]
            except Exception as exc:
                coverage = "INVALID"
                details = {"error": "%s: %s" % (type(exc).__name__, exc)}
        elif mp:
            coverage = "PARTIAL"
            details = {"error": "coverage receipts path not registered"}

        if source_stale:
            coverage = "STALE"
            coverage_overall = "BLOCKED"

        ready = (not source_stale) and coverage_overall == "READY"
        if required and ready:
            ready_required += 1
        if required and not ready:
            blocked_required.append(entry["source_id"])

        results.append({
            "source_id": entry["source_id"],
            "required": required,
            "authority": entry.get("authority"),
            "role": entry.get("role"),
            "registered_source_sha256": registered_hash,
            "current_source_sha256": current_hash,
            "source_stale": source_stale,
            "extraction": extraction,
            "coverage": coverage,
            "overall": "READY" if ready else "BLOCKED",
            "details": details,
        })

    overall = "READY" if not blocked_required else "BLOCKED"
    return {
        "overall": overall,
        "source_basis_digest": _source_basis_digest(registry),
        "registry_sha256": registry["registry_sha256"],
        "required_sources": required_total,
        "ready_required_sources": ready_required,
        "blocked_required_source_ids": blocked_required,
        "sources": results,
        "proof_scope": "exact identity + current coverage readiness of registered required sources; not semantic understanding",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("registry")

    p_reg = sub.add_parser("register")
    p_reg.add_argument("registry")
    p_reg.add_argument("source_id")
    p_reg.add_argument("source")
    p_reg.add_argument("--manifest")
    p_reg.add_argument("--receipts")
    p_reg.add_argument("--optional", action="store_true")
    p_reg.add_argument("--authority", choices=sorted(VALID_AUTHORITIES), default="AUTHORITATIVE")
    p_reg.add_argument("--role", default="source")

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("registry")

    args = ap.parse_args()
    try:
        if args.command == "init":
            print(json.dumps(init_registry(args.registry), indent=2))
            return 0
        if args.command == "register":
            row = register_source(
                args.registry, args.source_id, args.source,
                manifest_path=args.manifest, receipts_path=args.receipts,
                required=not args.optional, authority=args.authority, role=args.role,
            )
            print(json.dumps(row, indent=2))
            return 0
        report = audit_registry(args.registry)
        print(json.dumps(report, indent=2))
        return 0 if report["overall"] == "READY" else 1
    except Exception as exc:
        print("SOURCE REGISTRY: ERROR - %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
