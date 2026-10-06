#!/usr/bin/env python3
"""CLI for the Claude Mon verifiable source coverage engine."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from claude_mon_core import (
    build_chunk_manifest,
    get_chunk_payload,
    get_source,
    iter_receipts,
    load_registry,
    record_receipt,
    register_source,
    unitize_source,
    verify_chunk_manifest,
    verify_receipt,
    verify_unit_manifest,
)


def _print(value) -> None:
    print(json.dumps(value, sort_keys=True, ensure_ascii=False))


def main() -> int:
    p = argparse.ArgumentParser(description="Claude Mon: deterministic source coverage, receipts, and staleness checks.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("register")
    r.add_argument("--project", required=True)
    r.add_argument("--source", required=True)
    r.add_argument("--kind", default="text", choices=["text", "binary", "document", "extracted-document"])
    r.add_argument("--optional", action="store_true")
    r.add_argument("--provenance", action="append", default=None)

    u = sub.add_parser("unitize")
    u.add_argument("--project", required=True)
    u.add_argument("--source-id", required=True)
    u.add_argument("--max-unit-bytes", type=int, default=64 * 1024)

    c = sub.add_parser("chunk")
    c.add_argument("--project", required=True)
    c.add_argument("--source-id", required=True)
    c.add_argument("--max-primary-bytes", type=int, default=256 * 1024)
    c.add_argument("--context-units", type=int, default=1)

    pl = sub.add_parser("payload")
    pl.add_argument("--project", required=True)
    pl.add_argument("--source-id", required=True)
    pl.add_argument("--chunk-id", required=True)

    rec = sub.add_parser("receipt")
    rec.add_argument("--project", required=True)
    rec.add_argument("--source-id", required=True)
    rec.add_argument("--task-spec-file", required=True)
    rec.add_argument("--processor", required=True)
    rec.add_argument("--outcomes-file", required=True, help="JSON array of {chunk_id,status,input_sha256}; input_sha256 is required for ok/truncated")

    v = sub.add_parser("verify")
    v.add_argument("--project", required=True)
    v.add_argument("--source-id", required=True)
    v.add_argument("--receipt-id")
    v.add_argument("--task-spec-file")

    s = sub.add_parser("status")
    s.add_argument("--project", required=True)

    args = p.parse_args()
    if args.cmd == "register":
        _print(register_source(args.project, args.source, required=not args.optional, provenance=args.provenance, kind=args.kind))
        return 0
    if args.cmd == "unitize":
        _print(unitize_source(args.project, args.source_id, args.max_unit_bytes))
        return 0
    if args.cmd == "chunk":
        _print(build_chunk_manifest(args.project, args.source_id, args.max_primary_bytes, args.context_units))
        return 0
    if args.cmd == "payload":
        payload = get_chunk_payload(args.project, args.source_id, args.chunk_id)
        payload = {k: v for k, v in payload.items() if k != "bytes"}
        _print(payload)
        return 0
    if args.cmd == "receipt":
        task = Path(args.task_spec_file).read_text(encoding="utf-8")
        outcomes = json.loads(Path(args.outcomes_file).read_text(encoding="utf-8"))
        _print(record_receipt(args.project, args.source_id, task, {"kind": "model", "name": args.processor}, outcomes))
        return 0
    if args.cmd == "verify":
        uv = verify_unit_manifest(args.project, args.source_id)
        cv = verify_chunk_manifest(args.project, args.source_id) if uv.get("ok") else {"ok": False, "status": uv.get("status")}
        out = {"unit_manifest": uv, "chunk_manifest": cv}
        if args.receipt_id:
            task = Path(args.task_spec_file).read_text(encoding="utf-8") if args.task_spec_file else None
            out["receipt"] = verify_receipt(args.project, args.receipt_id, task)
        _print(out)
        ok = uv.get("ok") and cv.get("ok") and ("receipt" not in out or out["receipt"].get("status") == "COMPLETE")
        return 0 if ok else 2
    if args.cmd == "status":
        root = Path(args.project).resolve()
        reg = load_registry(root)
        sources = []
        for source in reg["sources"]:
            receipts = list(iter_receipts(root, source["source_id"]))
            latest = receipts[-1]["receipt_id"] if receipts else None
            latest_status = verify_receipt(root, latest).get("status") if latest else None
            sources.append({
                "source_id": source["source_id"],
                "path": source["path"],
                "kind": source["kind"],
                "required": source["required"],
                "current_sha256": source["current_version"]["sha256"],
                "latest_receipt_id": latest,
                "latest_receipt_status": latest_status,
            })
        _print({"schema": 1, "sources": sources})
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
