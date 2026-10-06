#!/usr/bin/env python3
"""Stable structural unit inventory for source-linked audits.

Units provide human/audit-friendly identities (lines or paragraphs) while the
separate source_coverage ledger remains the byte-preservation authority.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from . import source_coverage
except ImportError:
    import source_coverage

SCHEMA_VERSION = 1
VALID_MODES = {"lines", "paragraphs"}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _unit_ranges(raw, mode):
    if mode == "lines":
        start = 0
        for part in raw.splitlines(keepends=True):
            end = start + len(part)
            yield start, end
            start = end
        if start < len(raw):
            yield start, len(raw)
        return

    # Paragraph units include their trailing blank-line separators so that the
    # inventory covers every canonical byte exactly once. This is a structural
    # locator, not a linguistic sentence parser.
    start = 0
    for m in re.finditer(br"(?:\r?\n[ \t]*\r?\n)+", raw):
        end = m.end()
        if end > start:
            yield start, end
            start = end
    if start < len(raw):
        yield start, len(raw)


def _load_coverage(path, source_sha):
    if path is None:
        return None
    _, manifest = source_coverage.load_manifest(path)
    if manifest["source_sha256"] != source_sha:
        raise ValueError("coverage manifest source hash does not match structural source")
    return manifest


def build_inventory(source_path, output_path, mode="lines", coverage_manifest=None):
    if mode not in VALID_MODES:
        raise ValueError("mode must be one of %s" % sorted(VALID_MODES))
    source = Path(source_path).resolve()
    raw = source.read_bytes()
    raw.decode("utf-8", errors="strict")
    source_sha = _sha(raw)
    coverage = _load_coverage(coverage_manifest, source_sha)
    prefix = "L" if mode == "lines" else "P"

    units = []
    expected = 0
    for idx, (start, end) in enumerate(_unit_ranges(raw, mode), 1):
        if start != expected or end <= start:
            raise ValueError("unit coverage gap/overlap at unit %d" % idx)
        data = raw[start:end]
        chunk_ids = []
        if coverage is not None:
            for chunk in coverage["chunks"]:
                if chunk["end_byte"] > start and chunk["start_byte"] < end:
                    chunk_ids.append(chunk["chunk_id"])
        units.append({
            "unit_id": "%s%06d" % (prefix, idx),
            "start_byte": start,
            "end_byte": end,
            "size_bytes": len(data),
            "sha256": _sha(data),
            "chunk_ids": chunk_ids,
        })
        expected = end
    if expected != len(raw):
        raise ValueError("unit coverage ends at %d, expected %d" % (expected, len(raw)))

    base = {
        "schema_version": SCHEMA_VERSION,
        "source_path": str(source),
        "source_sha256": source_sha,
        "source_size_bytes": len(raw),
        "encoding": "utf-8",
        "mode": mode,
        "coverage_manifest_sha256": coverage.get("manifest_sha256") if coverage else None,
        "units": units,
    }
    inv = dict(base)
    inv["unit_manifest_sha256"] = _sha(_canon(base))
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return inv


def load_inventory(path):
    p = Path(path).resolve()
    inv = json.loads(p.read_text(encoding="utf-8"))
    if inv.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported unit schema_version")
    base = {k: v for k, v in inv.items() if k != "unit_manifest_sha256"}
    if _sha(_canon(base)) != inv.get("unit_manifest_sha256"):
        raise ValueError("unit_manifest_sha256 mismatch")
    return p, inv


def reassemble_units(path):
    _, inv = load_inventory(path)
    source = Path(inv["source_path"])
    raw = source.read_bytes()
    parts = []
    expected = 0
    for unit in inv["units"]:
        if unit["start_byte"] != expected:
            raise ValueError("unit range gap/overlap before %s" % unit["unit_id"])
        data = raw[unit["start_byte"]:unit["end_byte"]]
        if len(data) != unit["size_bytes"] or _sha(data) != unit["sha256"]:
            raise ValueError("unit content mismatch: %s" % unit["unit_id"])
        parts.append(data)
        expected = unit["end_byte"]
    rebuilt = b"".join(parts)
    if expected != inv["source_size_bytes"] or _sha(rebuilt) != inv["source_sha256"]:
        raise ValueError("unit reassembly mismatch")
    return rebuilt


def verify_inventory(path):
    _, inv = load_inventory(path)
    source = Path(inv["source_path"])
    if not source.is_file():
        return {"overall": "STALE", "reason": "source missing", "source_sha256": inv["source_sha256"], "current_source_sha256": None}
    current = _sha(source.read_bytes())
    if current != inv["source_sha256"]:
        return {"overall": "STALE", "reason": "source hash changed", "source_sha256": inv["source_sha256"], "current_source_sha256": current}
    try:
        rebuilt = reassemble_units(path)
    except Exception as exc:
        return {"overall": "INVALID", "reason": "%s: %s" % (type(exc).__name__, exc), "source_sha256": inv["source_sha256"], "current_source_sha256": current}
    return {
        "overall": "READY",
        "mode": inv["mode"],
        "units": len(inv["units"]),
        "source_size_bytes": len(rebuilt),
        "source_sha256": inv["source_sha256"],
        "unit_manifest_sha256": inv["unit_manifest_sha256"],
        "proof_scope": "stable structural locators + exact byte coverage; not sentence-level semantic understanding",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p_build = sub.add_parser("build")
    p_build.add_argument("source")
    p_build.add_argument("output")
    p_build.add_argument("--mode", choices=sorted(VALID_MODES), default="lines")
    p_build.add_argument("--coverage-manifest")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("inventory")
    args = ap.parse_args()
    try:
        if args.command == "build":
            print(json.dumps(build_inventory(args.source, args.output, args.mode, args.coverage_manifest), indent=2))
            return 0
        report = verify_inventory(args.inventory)
        print(json.dumps(report, indent=2))
        return 0 if report["overall"] == "READY" else 1
    except Exception as exc:
        print("STRUCTURAL UNITS: ERROR - %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
