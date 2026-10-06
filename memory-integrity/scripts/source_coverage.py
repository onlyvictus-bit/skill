#!/usr/bin/env python3
"""Deterministic source coverage ledger for UTF-8 text/code.

This proves byte preservation and processing coverage of the canonical UTF-8
source representation. It does NOT prove OCR/PDF extraction correctness or
human/model semantic understanding.
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

SCHEMA_VERSION = 1
RECEIPT_STATUSES = {"COMPLETE", "PARTIAL", "TRUNCATED", "ERROR"}
EXTRACTION_STATUSES = {"NOT_APPLICABLE", "COMPLETE", "PARTIAL", "ERROR", "UNKNOWN"}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _utf8_safe_end(raw, start, tentative_end):
    if tentative_end >= len(raw):
        return len(raw)
    end = tentative_end
    # If raw[end] is a continuation byte, end is inside a code point.
    while end > start and (raw[end] & 0xC0) == 0x80:
        end -= 1
    if end == start:
        # max_bytes too small for the next code point; advance to its end.
        end = tentative_end
        while end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end += 1
        if end <= start:
            raise ValueError("cannot choose a UTF-8 boundary")
    return end


def _chunk_ranges(raw, max_bytes):
    if max_bytes < 1:
        raise ValueError("max_bytes must be >= 1")
    start = 0
    while start < len(raw):
        tentative = min(len(raw), start + max_bytes)
        end = _utf8_safe_end(raw, start, tentative)
        # Prefer a newline boundary when it does not make the chunk tiny.
        if end < len(raw):
            nl = raw.rfind(b"\n", start + 1, end + 1)
            if nl >= 0 and (nl + 1 - start) >= max(1, max_bytes // 2):
                end = nl + 1
        if end <= start:
            raise ValueError("chunker made no progress")
        yield start, end
        start = end


def ingest_text(source_path, output_dir, max_bytes=65536, origin_path=None, extractor=None, extraction_status="NOT_APPLICABLE"):
    source = Path(source_path).resolve()
    out = Path(output_dir).resolve()
    if extraction_status not in EXTRACTION_STATUSES:
        raise ValueError("invalid extraction_status %r" % extraction_status)
    origin = Path(origin_path).resolve() if origin_path is not None else source
    origin_raw = origin.read_bytes()
    raw = source.read_bytes()
    # Strict decode establishes the canonical representation contract.
    raw.decode("utf-8", errors="strict")
    out.mkdir(parents=True, exist_ok=True)
    chunks_dir = out / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    chunks = []
    for idx, (start, end) in enumerate(_chunk_ranges(raw, int(max_bytes)), 1):
        chunk_id = "CHUNK-%06d" % idx
        payload = raw[start:end]
        filename = "%s.txt" % chunk_id
        (chunks_dir / filename).write_bytes(payload)
        chunks.append({
            "chunk_id": chunk_id,
            "start_byte": start,
            "end_byte": end,
            "size_bytes": len(payload),
            "sha256": sha256_bytes(payload),
            "file": "chunks/%s" % filename,
        })

    base = {
        "schema_version": SCHEMA_VERSION,
        "source_path": str(source),
        "source_size_bytes": len(raw),
        "source_sha256": sha256_bytes(raw),
        "encoding": "utf-8",
        "origin": {
            "path": str(origin),
            "sha256": sha256_bytes(origin_raw),
            "size_bytes": len(origin_raw),
            "extractor": extractor,
            "extraction_status": extraction_status,
        },
        "chunking": {"kind": "utf8-primary-byte-ranges", "max_bytes": int(max_bytes)},
        "chunks": chunks,
    }
    manifest = dict(base)
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(base))
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_manifest(path):
    p = Path(path).resolve()
    manifest = json.loads(p.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported manifest schema_version: %r" % manifest.get("schema_version"))
    base = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    actual = sha256_bytes(canonical_json_bytes(base))
    if actual != manifest.get("manifest_sha256"):
        raise ValueError("manifest_sha256 mismatch")
    return p, manifest


def reassemble(manifest_path):
    mp, manifest = load_manifest(manifest_path)
    root = mp.parent
    chunks = sorted(manifest["chunks"], key=lambda c: c["start_byte"])
    expected_start = 0
    parts = []
    for chunk in chunks:
        if chunk["start_byte"] != expected_start:
            raise ValueError("primary byte coverage gap/overlap before %s" % chunk["chunk_id"])
        data = (root / chunk["file"]).read_bytes()
        if len(data) != chunk["size_bytes"]:
            raise ValueError("chunk size mismatch: %s" % chunk["chunk_id"])
        if sha256_bytes(data) != chunk["sha256"]:
            raise ValueError("chunk hash mismatch: %s" % chunk["chunk_id"])
        if chunk["end_byte"] - chunk["start_byte"] != len(data):
            raise ValueError("chunk range mismatch: %s" % chunk["chunk_id"])
        parts.append(data)
        expected_start = chunk["end_byte"]
    if expected_start != manifest["source_size_bytes"]:
        raise ValueError("primary byte coverage ends at %d, expected %d" % (expected_start, manifest["source_size_bytes"]))
    rebuilt = b"".join(parts)
    if sha256_bytes(rebuilt) != manifest["source_sha256"]:
        raise ValueError("reassembled source hash mismatch")
    return rebuilt


def record_receipt(manifest_path, receipts_path, chunk_id, status, result_sha256=None, note=None):
    _, manifest = load_manifest(manifest_path)
    if status not in RECEIPT_STATUSES:
        raise ValueError("invalid status %r" % status)
    by_id = {c["chunk_id"]: c for c in manifest["chunks"]}
    if chunk_id not in by_id:
        raise ValueError("unknown chunk_id %r" % chunk_id)
    chunk = by_id[chunk_id]
    existing = _read_receipts(receipts_path)
    prior_attempts = [
        int(r.get("attempt", 0))
        for r in existing
        if r.get("chunk_id") == chunk_id
        and r.get("source_sha256") == manifest["source_sha256"]
        and r.get("manifest_sha256") == manifest["manifest_sha256"]
        and isinstance(r.get("attempt", 0), int)
    ]
    attempt = max(prior_attempts, default=0) + 1
    receipt = {
        "schema_version": 1,
        "attempt": attempt,
        "receipt_id": "READ-%s-%s" % (chunk_id, dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")),
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_sha256": manifest["source_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "chunk_id": chunk_id,
        "chunk_sha256": chunk["sha256"],
        "status": status,
    }
    if result_sha256:
        receipt["result_sha256"] = result_sha256
    if note:
        receipt["note"] = note
    rp = Path(receipts_path)
    rp.parent.mkdir(parents=True, exist_ok=True)
    with rp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return receipt


def mark_all_complete(manifest_path, receipts_path):
    """TEST FIXTURE HELPER. Never use this to claim real model processing."""
    _, manifest = load_manifest(manifest_path)
    Path(receipts_path).write_text("", encoding="utf-8")
    for chunk in manifest["chunks"]:
        record_receipt(manifest_path, receipts_path, chunk["chunk_id"], "COMPLETE")


def _read_receipts(path):
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line_no, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid receipt JSON at line %d: %s" % (line_no, exc))
        rows.append(row)
    return rows


def verify(manifest_path, receipts_path):
    mp, manifest = load_manifest(manifest_path)
    chunks = manifest["chunks"]
    chunk_ids = [c["chunk_id"] for c in chunks]
    by_id = {c["chunk_id"]: c for c in chunks}

    integrity_errors = []
    try:
        rebuilt = reassemble(mp)
        if len(rebuilt) != manifest["source_size_bytes"]:
            integrity_errors.append("reassembly_size_mismatch")
    except Exception as exc:
        integrity_errors.append(str(exc))

    source = Path(manifest["source_path"])
    if not source.exists():
        stale = True
        current_source_sha256 = None
    else:
        current_source_sha256 = sha256_bytes(source.read_bytes())
        stale = current_source_sha256 != manifest["source_sha256"]

    origin_meta = manifest.get("origin") or {
        "path": manifest["source_path"],
        "sha256": manifest["source_sha256"],
        "extraction_status": "NOT_APPLICABLE",
    }
    origin = Path(origin_meta["path"])
    if not origin.exists():
        origin_stale = True
        current_origin_sha256 = None
    else:
        current_origin_sha256 = sha256_bytes(origin.read_bytes())
        origin_stale = current_origin_sha256 != origin_meta.get("sha256")
    stale = stale or origin_stale
    extraction_status = origin_meta.get("extraction_status", "UNKNOWN")

    receipts = _read_receipts(receipts_path)
    receipt_map = {}
    foreign_receipts = []
    invalid_receipts = []
    for row in receipts:
        cid = row.get("chunk_id")
        if cid not in by_id:
            foreign_receipts.append(cid)
            continue
        if row.get("source_sha256") != manifest["source_sha256"] or row.get("manifest_sha256") != manifest["manifest_sha256"]:
            invalid_receipts.append(row.get("receipt_id"))
            continue
        if row.get("chunk_sha256") != by_id[cid]["sha256"] or row.get("status") not in RECEIPT_STATUSES:
            invalid_receipts.append(row.get("receipt_id"))
            continue
        receipt_map.setdefault(cid, []).append(row)

    duplicates = []
    effective = {}
    for cid, rows in receipt_map.items():
        attempts = [r.get("attempt") for r in rows]
        valid_attempts = [a for a in attempts if isinstance(a, int) and a >= 1]
        if len(valid_attempts) != len(rows) or len(set(valid_attempts)) != len(valid_attempts):
            duplicates.append(cid)
            continue
        effective[cid] = max(rows, key=lambda r: r["attempt"])
    duplicates = sorted(duplicates)
    missing = sorted(cid for cid in chunk_ids if cid not in effective and cid not in duplicates)
    noncomplete = sorted(
        cid for cid, row in effective.items()
        if row.get("status") != "COMPLETE"
    )

    if stale:
        status = "STALE"
    elif integrity_errors or duplicates or foreign_receipts or invalid_receipts:
        status = "INVALID"
    elif missing or noncomplete:
        status = "PARTIAL"
    else:
        status = "COVERAGE_COMPLETE"

    overall_status = (
        "READY"
        if status == "COVERAGE_COMPLETE" and extraction_status in {"NOT_APPLICABLE", "COMPLETE"}
        else "BLOCKED"
    )

    return {
        "overall_status": overall_status,
        "coverage_status": status,
        "extraction_status": extraction_status,
        "source_sha256": manifest["source_sha256"],
        "current_source_sha256": current_source_sha256,
        "origin_sha256": origin_meta.get("sha256"),
        "current_origin_sha256": current_origin_sha256,
        "manifest_sha256": manifest["manifest_sha256"],
        "source_size_bytes": manifest["source_size_bytes"],
        "required_chunks": len(chunks),
        "receipt_rows": len(receipts),
        "missing_chunk_ids": missing,
        "noncomplete_chunk_ids": noncomplete,
        "duplicate_primary_chunk_ids": duplicates,
        "foreign_receipt_chunk_ids": foreign_receipts,
        "invalid_receipt_ids": invalid_receipts,
        "integrity_errors": integrity_errors,
        "origin_stale": origin_stale,
        "stale": stale,
        "proof_scope": "byte-preservation + chunk-processing coverage of canonical UTF-8 source; not semantic understanding",
    }


def pending(manifest_path, receipts_path):
    report = verify(manifest_path, receipts_path)
    ids = sorted(set(report["missing_chunk_ids"] + report["noncomplete_chunk_ids"]))
    return report, ids


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("source")
    p_ingest.add_argument("output_dir")
    p_ingest.add_argument("--max-bytes", type=int, default=65536)
    p_ingest.add_argument("--origin", default=None, help="original binary/source when canonical text is extracted")
    p_ingest.add_argument("--extractor", default=None, help="extractor identity/version, e.g. docling:2.x")
    p_ingest.add_argument("--extraction-status", choices=sorted(EXTRACTION_STATUSES), default="NOT_APPLICABLE")

    p_receipt = sub.add_parser("receipt")
    p_receipt.add_argument("manifest")
    p_receipt.add_argument("receipts")
    p_receipt.add_argument("chunk_id")
    p_receipt.add_argument("status", choices=sorted(RECEIPT_STATUSES))
    p_receipt.add_argument("--result-sha256")
    p_receipt.add_argument("--note")

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("manifest")
    p_verify.add_argument("receipts")

    p_pending = sub.add_parser("pending")
    p_pending.add_argument("manifest")
    p_pending.add_argument("receipts")

    args = ap.parse_args()
    try:
        if args.command == "ingest":
            m = ingest_text(
                args.source,
                args.output_dir,
                args.max_bytes,
                origin_path=args.origin,
                extractor=args.extractor,
                extraction_status=args.extraction_status,
            )
            print(json.dumps({
                "status": "INGESTED",
                "manifest": str(Path(args.output_dir).resolve() / "manifest.json"),
                "source_sha256": m["source_sha256"],
                "manifest_sha256": m["manifest_sha256"],
                "chunks": len(m["chunks"]),
                "source_size_bytes": m["source_size_bytes"],
            }, indent=2))
            return 0
        if args.command == "receipt":
            r = record_receipt(args.manifest, args.receipts, args.chunk_id, args.status, args.result_sha256, args.note)
            print(json.dumps(r, indent=2))
            return 0
        if args.command == "verify":
            report = verify(args.manifest, args.receipts)
            print(json.dumps(report, indent=2))
            return 0 if report["overall_status"] == "READY" else 1
        report, ids = pending(args.manifest, args.receipts)
        print(json.dumps({
            "overall_status": report["overall_status"],
            "coverage_status": report["coverage_status"],
            "extraction_status": report["extraction_status"],
            "pending_chunk_ids": ids,
        }, indent=2))
        return 0 if not ids and report["overall_status"] == "READY" else 1
    except Exception as exc:
        print("SOURCE COVERAGE: ERROR - %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
