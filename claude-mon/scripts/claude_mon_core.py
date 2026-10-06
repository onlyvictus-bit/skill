#!/usr/bin/env python3
"""Deterministic source coverage primitives for Claude Mon.

Core guarantees are intentionally narrow:
- source identity is SHA-256 over original bytes;
- UTF-8 text is split into deterministic, independently-decodable byte units;
- primary chunk coverage is exact and non-overlapping;
- receipts are immutable run files and status is derived from current evidence;
- COMPLETE means coverage for a bound task, never semantic correctness.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


class ClaudeMonError(RuntimeError):
    pass


class IntegrityError(ClaudeMonError):
    pass


class PathSafetyError(ClaudeMonError):
    pass


STATUS_COMPLETE = "COMPLETE"
STATUS_PARTIAL = "PARTIAL"
STATUS_TRUNCATED = "TRUNCATED"
STATUS_ERROR = "ERROR"
STATUS_STALE = "STALE"

REGISTRY_REL = Path("docs/fable/claude-mon/sources.json")
RECEIPTS_REL = Path("docs/fable/claude-mon/receipts/runs")
CACHE_REL = Path(".claude-mon/cache")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, block_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _root(project_root: str | Path) -> Path:
    return Path(project_root).resolve()


def _safe_path(project_root: str | Path, source_path: str | Path) -> tuple[Path, str]:
    root = _root(project_root)
    p = Path(source_path)
    if not p.is_absolute():
        p = root / p
    resolved = p.resolve()
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise PathSafetyError(f"source escapes project root: {source_path}") from exc
    if not resolved.is_file():
        raise PathSafetyError(f"source is not a regular file: {source_path}")
    return resolved, rel.as_posix()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _atomic_write_json(path: Path, value: Any) -> None:
    _atomic_write_bytes(path, canonical_json_bytes(value) + b"\n")


def load_registry(project_root: str | Path) -> dict[str, Any]:
    path = _root(project_root) / REGISTRY_REL
    if not path.exists():
        return {"schema": 1, "sources": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("sources"), list):
        raise IntegrityError("invalid Claude Mon source registry")
    return data


def _source_from_registry(registry: dict[str, Any], source_id: str) -> dict[str, Any]:
    matches = [s for s in registry["sources"] if s.get("source_id") == source_id]
    if len(matches) != 1:
        raise IntegrityError(f"source_id must resolve exactly once: {source_id}")
    return matches[0]


def get_source(project_root: str | Path, source_id: str) -> dict[str, Any]:
    return _source_from_registry(load_registry(project_root), source_id)


def register_source(
    project_root: str | Path,
    source_path: str | Path,
    required: bool = True,
    provenance: list[str] | None = None,
    kind: str = "text",
) -> dict[str, Any]:
    if kind not in {"text", "binary", "document", "extracted-document"}:
        raise ValueError(f"unsupported source kind: {kind}")
    root = _root(project_root)
    abs_path, rel = _safe_path(root, source_path)
    content_hash = sha256_file(abs_path)
    size = abs_path.stat().st_size
    source_id = "SRC-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16].upper()
    registry = load_registry(root)
    existing = next((s for s in registry["sources"] if s.get("source_id") == source_id), None)
    version = {"sha256": content_hash, "byte_size": size}
    if existing is None:
        source = {
            "source_id": source_id,
            "path": rel,
            "kind": kind,
            "required": bool(required),
            "provenance": list(provenance or []),
            "current_version": version,
            "versions": [version],
        }
        registry["sources"].append(source)
        registry["sources"].sort(key=lambda x: x["source_id"])
    else:
        if existing.get("path") != rel:
            raise IntegrityError(f"source id collision for path {rel}")
        existing["kind"] = kind
        existing["required"] = bool(required)
        if provenance is not None:
            existing["provenance"] = list(provenance)
        hashes = [v.get("sha256") for v in existing.get("versions", [])]
        if content_hash not in hashes:
            existing.setdefault("versions", []).append(version)
        existing["current_version"] = version
        source = existing
    _atomic_write_json(root / REGISTRY_REL, registry)
    return json.loads(json.dumps(source))


def _source_abs_path(project_root: Path, source: dict[str, Any]) -> Path:
    abs_path, rel = _safe_path(project_root, source["path"])
    if rel != source["path"]:
        raise PathSafetyError("registry path does not normalize to itself")
    return abs_path


def _version_cache_dir(project_root: Path, source: dict[str, Any]) -> Path:
    return project_root / CACHE_REL / source["source_id"] / source["current_version"]["sha256"]


def _largest_valid_utf8_prefix(data: bytes, limit: int) -> int:
    cut = min(limit, len(data))
    if cut == 0:
        return 0
    last_error: UnicodeDecodeError | None = None
    for back in range(0, 5):
        candidate = cut - back
        if candidate <= 0:
            break
        try:
            data[:candidate].decode("utf-8", "strict")
            return candidate
        except UnicodeDecodeError as exc:
            last_error = exc
            # A malformed sequence well before the boundary is a real source error.
            if exc.start < candidate - 4:
                raise
    if last_error is not None:
        raise last_error
    raise UnicodeDecodeError("utf-8", data, 0, min(1, len(data)), "unable to find UTF-8 boundary")


def _iter_utf8_segments(path: Path, max_unit_bytes: int) -> Iterable[bytes]:
    if max_unit_bytes <= 0:
        raise ValueError("max_unit_bytes must be positive")
    carry = b""
    with path.open("rb") as f:
        while True:
            block = f.read(max_unit_bytes)
            eof = not block
            data = carry + block
            if eof:
                if data:
                    data.decode("utf-8", "strict")
                    yield data
                break
            if len(data) <= max_unit_bytes:
                try:
                    data.decode("utf-8", "strict")
                    yield data
                    carry = b""
                    continue
                except UnicodeDecodeError as exc:
                    # Only tolerate a split sequence at the end; reject malformed UTF-8 elsewhere.
                    if exc.start < len(data) - 4:
                        raise
            cut = _largest_valid_utf8_prefix(data, max_unit_bytes)
            piece, carry = data[:cut], data[cut:]
            if not piece:
                raise UnicodeDecodeError("utf-8", data, 0, min(1, len(data)), "no progress while segmenting")
            yield piece


def _write_jsonl_atomic(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp = Path(tmp_name)
    h = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as f:
            for row in rows:
                line = canonical_json_bytes(row) + b"\n"
                f.write(line)
                h.update(line)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return h.hexdigest()


def unitize_source(project_root: str | Path, source_id: str, max_unit_bytes: int = 64 * 1024) -> dict[str, Any]:
    root = _root(project_root)
    source = get_source(root, source_id)
    if source.get("kind") not in {"text", "extracted-document"}:
        raise IntegrityError("unitize_source supports UTF-8 text/extracted-document sources only")
    path = _source_abs_path(root, source)
    current_hash = sha256_file(path)
    if current_hash != source["current_version"]["sha256"]:
        raise IntegrityError("source changed since registration; register it again before unitizing")
    cache = _version_cache_dir(root, source)
    units_path = cache / "units.jsonl"
    byte_offset = 0
    line_no = 1
    unit_count = 0

    def rows():
        nonlocal byte_offset, line_no, unit_count
        for unit_count, segment in enumerate(_iter_utf8_segments(path, max_unit_bytes), start=1):
            start = byte_offset
            end = start + len(segment)
            newline_count = segment.count(b"\n")
            row = {
                "unit_id": f"U{unit_count:08d}",
                "ordinal": unit_count,
                "start_byte": start,
                "end_byte": end,
                "byte_size": len(segment),
                "sha256": sha256_bytes(segment),
                "line_start": line_no,
                "line_end": line_no + newline_count,
            }
            byte_offset = end
            line_no += newline_count
            yield row

    units_sha = _write_jsonl_atomic(units_path, rows())
    # Empty file has no rows; still validate UTF-8 and produce an empty manifest.
    if path.stat().st_size == 0:
        path.read_bytes().decode("utf-8", "strict")
    manifest = {
        "schema": 1,
        "source_id": source_id,
        "source_sha256": source["current_version"]["sha256"],
        "byte_size": source["current_version"]["byte_size"],
        "max_unit_bytes": max_unit_bytes,
        "unit_count": unit_count,
        "units_path": units_path.relative_to(root).as_posix(),
        "units_sha256": units_sha,
    }
    _atomic_write_json(cache / "unit_manifest.json", manifest)
    return manifest


def _load_unit_manifest(project_root: Path, source: dict[str, Any]) -> dict[str, Any]:
    path = _version_cache_dir(project_root, source) / "unit_manifest.json"
    if not path.exists():
        raise IntegrityError("unit manifest missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("source_sha256") != source["current_version"]["sha256"]:
        raise IntegrityError("unit manifest source hash mismatch")
    return data


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify_unit_manifest(project_root: str | Path, source_id: str) -> dict[str, Any]:
    root = _root(project_root)
    source = get_source(root, source_id)
    source_path = _source_abs_path(root, source)
    current = sha256_file(source_path)
    if current != source["current_version"]["sha256"]:
        return {"ok": False, "status": STATUS_STALE, "reason": "SOURCE_HASH_MISMATCH"}
    manifest = _load_unit_manifest(root, source)
    units_path = root / manifest["units_path"]
    if sha256_file(units_path) != manifest["units_sha256"]:
        return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_MANIFEST_DIGEST_MISMATCH"}
    rows = _load_jsonl(units_path)
    if len(rows) != manifest["unit_count"]:
        return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_COUNT_MISMATCH"}
    expected_start = 0
    with source_path.open("rb") as f:
        for i, row in enumerate(rows, start=1):
            if row.get("ordinal") != i or row.get("unit_id") != f"U{i:08d}":
                return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_ORDER_MISMATCH"}
            if row.get("start_byte") != expected_start or row.get("end_byte", -1) < row.get("start_byte", 0):
                return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_RANGE_GAP_OR_OVERLAP"}
            size = row["end_byte"] - row["start_byte"]
            data = f.read(size)
            if len(data) != size or sha256_bytes(data) != row.get("sha256"):
                return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_CONTENT_HASH_MISMATCH", "unit_id": row.get("unit_id")}
            try:
                data.decode("utf-8", "strict")
            except UnicodeDecodeError:
                return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_INVALID_UTF8", "unit_id": row.get("unit_id")}
            expected_start = row["end_byte"]
        extra = f.read(1)
    if expected_start != source_path.stat().st_size or extra:
        return {"ok": False, "status": STATUS_ERROR, "reason": "UNIT_RANGE_DOES_NOT_COVER_SOURCE"}
    return {"ok": True, "status": STATUS_COMPLETE, "unit_count": len(rows), "byte_size": expected_start}


def _payload_for_units(source_path: Path, unit_rows: dict[str, dict[str, Any]], unit_ids: list[str]) -> bytes:
    out = bytearray()
    with source_path.open("rb") as f:
        for uid in unit_ids:
            row = unit_rows[uid]
            f.seek(row["start_byte"])
            out.extend(f.read(row["end_byte"] - row["start_byte"]))
    return bytes(out)


def build_chunk_manifest(
    project_root: str | Path,
    source_id: str,
    max_primary_bytes: int = 256 * 1024,
    context_units: int = 1,
) -> dict[str, Any]:
    if max_primary_bytes <= 0:
        raise ValueError("max_primary_bytes must be positive")
    if context_units < 0:
        raise ValueError("context_units cannot be negative")
    root = _root(project_root)
    source = get_source(root, source_id)
    uv = verify_unit_manifest(root, source_id)
    if not uv["ok"]:
        raise IntegrityError(f"unit manifest is not valid: {uv}")
    um = _load_unit_manifest(root, source)
    units = _load_jsonl(root / um["units_path"])
    unit_by_id = {u["unit_id"]: u for u in units}
    chunks: list[dict[str, Any]] = []
    index = 0
    while index < len(units):
        start = index
        total = 0
        primary: list[str] = []
        while index < len(units):
            size = units[index]["byte_size"]
            if primary and total + size > max_primary_bytes:
                break
            primary.append(units[index]["unit_id"])
            total += size
            index += 1
            if total >= max_primary_bytes:
                break
        before = [u["unit_id"] for u in units[max(0, start - context_units):start]]
        after = [u["unit_id"] for u in units[index:min(len(units), index + context_units)]]
        payload_ids = before + primary + after
        payload = _payload_for_units(_source_abs_path(root, source), unit_by_id, payload_ids)
        chunks.append(
            {
                "chunk_id": f"C{len(chunks)+1:08d}",
                "ordinal": len(chunks) + 1,
                "primary_units": primary,
                "context_before": before,
                "context_after": after,
                "primary_bytes": total,
                "payload_sha256": sha256_bytes(payload),
            }
        )
    cache = _version_cache_dir(root, source)
    chunks_path = cache / "chunks.jsonl"
    chunks_sha = _write_jsonl_atomic(chunks_path, iter(chunks))
    manifest = {
        "schema": 1,
        "source_id": source_id,
        "source_sha256": source["current_version"]["sha256"],
        "unit_manifest_sha256": um["units_sha256"],
        "max_primary_bytes": max_primary_bytes,
        "context_units": context_units,
        "chunk_count": len(chunks),
        "chunks_path": chunks_path.relative_to(root).as_posix(),
        "chunks_sha256": chunks_sha,
    }
    _atomic_write_json(cache / "chunk_manifest.json", manifest)
    return manifest


def _load_chunk_manifest(project_root: Path, source: dict[str, Any]) -> dict[str, Any]:
    path = _version_cache_dir(project_root, source) / "chunk_manifest.json"
    if not path.exists():
        raise IntegrityError("chunk manifest missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("source_sha256") != source["current_version"]["sha256"]:
        raise IntegrityError("chunk manifest source hash mismatch")
    return data


def verify_chunk_manifest(project_root: str | Path, source_id: str, trust_manifest_digest: bool = True) -> dict[str, Any]:
    root = _root(project_root)
    source = get_source(root, source_id)
    uv = verify_unit_manifest(root, source_id)
    if not uv["ok"]:
        return uv
    um = _load_unit_manifest(root, source)
    cm = _load_chunk_manifest(root, source)
    chunks_path = root / cm["chunks_path"]
    if trust_manifest_digest and sha256_file(chunks_path) != cm["chunks_sha256"]:
        return {"ok": False, "status": STATUS_ERROR, "reason": "CHUNK_MANIFEST_DIGEST_MISMATCH"}
    units = _load_jsonl(root / um["units_path"])
    expected = [u["unit_id"] for u in units]
    expected_set = set(expected)
    chunks = _load_jsonl(chunks_path)
    primary = [uid for c in chunks for uid in c.get("primary_units", [])]
    counts = Counter(primary)
    missing = [uid for uid in expected if counts[uid] == 0]
    duplicates = sorted(uid for uid, count in counts.items() if count > 1)
    unknown = sorted(uid for uid in counts if uid not in expected_set)
    order = [uid for uid in primary if uid in expected_set and counts[uid] >= 1]
    order_ok = order == expected if not duplicates and not missing and not unknown else False
    ok = not missing and not duplicates and not unknown and order_ok
    return {
        "ok": ok,
        "status": STATUS_COMPLETE if ok else STATUS_ERROR,
        "missing_units": missing,
        "duplicate_primary_units": duplicates,
        "unknown_primary_units": unknown,
        "order_ok": order_ok,
        "expected_unit_count": len(expected),
        "primary_occurrences": len(primary),
    }



def get_chunk_payload(project_root: str | Path, source_id: str, chunk_id: str) -> dict[str, Any]:
    root = _root(project_root)
    source = get_source(root, source_id)
    if sha256_file(_source_abs_path(root, source)) != source["current_version"]["sha256"]:
        raise IntegrityError("source changed since registration; register and rebuild manifests")
    um = _load_unit_manifest(root, source)
    cm = _load_chunk_manifest(root, source)
    if sha256_file(root / cm["chunks_path"]) != cm["chunks_sha256"]:
        raise IntegrityError("chunk manifest digest mismatch")
    units = _load_jsonl(root / um["units_path"])
    unit_by_id = {u["unit_id"]: u for u in units}
    chunks = _load_jsonl(root / cm["chunks_path"])
    matches = [c for c in chunks if c.get("chunk_id") == chunk_id]
    if len(matches) != 1:
        raise IntegrityError(f"chunk_id must resolve exactly once: {chunk_id}")
    chunk = matches[0]
    ids = chunk.get("context_before", []) + chunk.get("primary_units", []) + chunk.get("context_after", [])
    try:
        payload = _payload_for_units(_source_abs_path(root, source), unit_by_id, ids)
    except KeyError as exc:
        raise IntegrityError(f"chunk references unknown unit: {exc}") from exc
    digest = sha256_bytes(payload)
    if digest != chunk.get("payload_sha256"):
        raise IntegrityError("chunk payload hash mismatch")
    text = payload.decode("utf-8", "strict")
    return {
        "chunk_id": chunk_id,
        "primary_units": list(chunk.get("primary_units", [])),
        "context_before": list(chunk.get("context_before", [])),
        "context_after": list(chunk.get("context_after", [])),
        "payload_sha256": digest,
        "text": text,
        "bytes": payload,
    }

def task_spec_sha256(task_spec: str) -> str:
    return sha256_bytes(task_spec.encode("utf-8"))


def derive_receipt_status(expected_chunk_ids: list[str], chunk_outcomes: list[dict[str, Any]]) -> str:
    ids = [o.get("chunk_id") for o in chunk_outcomes]
    expected = set(expected_chunk_ids)
    counts = Counter(ids)
    if any(uid not in expected for uid in ids) or any(count > 1 for count in counts.values()):
        return STATUS_ERROR
    statuses = [o.get("status") for o in chunk_outcomes]
    if any(status == "error" for status in statuses):
        return STATUS_ERROR
    if any(status == "truncated" for status in statuses):
        return STATUS_TRUNCATED
    if any(status not in {"ok", "error", "truncated"} for status in statuses):
        return STATUS_ERROR
    if set(ids) != expected:
        return STATUS_PARTIAL
    if all(status == "ok" for status in statuses):
        return STATUS_COMPLETE
    return STATUS_PARTIAL


def record_receipt(
    project_root: str | Path,
    source_id: str,
    task_spec: str,
    processor: dict[str, Any],
    chunk_outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    root = _root(project_root)
    source = get_source(root, source_id)
    cm_verify = verify_chunk_manifest(root, source_id)
    if not cm_verify["ok"]:
        raise IntegrityError(f"cannot record receipt for invalid chunk manifest: {cm_verify}")
    um = _load_unit_manifest(root, source)
    cm = _load_chunk_manifest(root, source)
    chunks = _load_jsonl(root / cm["chunks_path"])
    expected = [c["chunk_id"] for c in chunks]
    payloads = {c["chunk_id"]: c["payload_sha256"] for c in chunks}
    normalized_outcomes = []
    for item in chunk_outcomes:
        row = dict(item)
        cid = row.get("chunk_id")
        if cid in payloads and row.get("status") in {"ok", "truncated"}:
            supplied_hash = row.get("input_sha256")
            if supplied_hash is None:
                row["status"] = "error"
                row["integrity_error"] = "MISSING_INPUT_HASH"
            elif supplied_hash != payloads[cid]:
                row["status"] = "error"
                row["integrity_error"] = "INPUT_HASH_MISMATCH"
        normalized_outcomes.append(row)
    status = derive_receipt_status(expected, normalized_outcomes)
    rid = "READ-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12].upper()
    receipt = {
        "schema": 1,
        "receipt_id": rid,
        "created_at": utc_now(),
        "source_id": source_id,
        "source_sha256": source["current_version"]["sha256"],
        "unit_manifest_sha256": um["units_sha256"],
        "chunk_manifest_sha256": cm["chunks_sha256"],
        "task_spec_sha256": task_spec_sha256(task_spec),
        "processor": dict(processor),
        "chunk_outcomes": normalized_outcomes,
        "status": status,
        "coverage_only": True,
        "semantic_correctness_proven": False,
    }
    path = root / RECEIPTS_REL / f"{rid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(receipt) + b"\n"
    with path.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return receipt


def _find_receipt_path(project_root: Path, receipt_id: str) -> Path:
    path = project_root / RECEIPTS_REL / f"{receipt_id}.json"
    if not path.exists():
        raise IntegrityError(f"receipt not found: {receipt_id}")
    return path


def verify_receipt(project_root: str | Path, receipt_id: str, task_spec: str | None = None) -> dict[str, Any]:
    root = _root(project_root)
    receipt = json.loads(_find_receipt_path(root, receipt_id).read_text(encoding="utf-8"))
    source = get_source(root, receipt["source_id"])
    result = {
        "receipt_id": receipt_id,
        "source_id": receipt["source_id"],
        "coverage_only": True,
        "semantic_correctness_proven": False,
    }
    if source["current_version"]["sha256"] != receipt.get("source_sha256"):
        result.update({"ok": False, "status": STATUS_STALE, "reason": "SOURCE_VERSION_CHANGED"})
        return result
    if task_spec is not None and task_spec_sha256(task_spec) != receipt.get("task_spec_sha256"):
        result.update({"ok": False, "status": STATUS_ERROR, "reason": "TASK_SPEC_MISMATCH"})
        return result
    try:
        um = _load_unit_manifest(root, source)
        cm = _load_chunk_manifest(root, source)
    except IntegrityError as exc:
        result.update({"ok": False, "status": STATUS_ERROR, "reason": str(exc)})
        return result
    if receipt.get("unit_manifest_sha256") != um.get("units_sha256") or receipt.get("chunk_manifest_sha256") != cm.get("chunks_sha256"):
        result.update({"ok": False, "status": STATUS_STALE, "reason": "MANIFEST_BASIS_CHANGED"})
        return result
    if not verify_chunk_manifest(root, receipt["source_id"])["ok"]:
        result.update({"ok": False, "status": STATUS_ERROR, "reason": "CURRENT_CHUNK_MANIFEST_INVALID"})
        return result
    chunks = _load_jsonl(root / cm["chunks_path"])
    expected = [c["chunk_id"] for c in chunks]
    payloads = {c["chunk_id"]: c["payload_sha256"] for c in chunks}
    outcomes = receipt.get("chunk_outcomes", [])
    for row in outcomes:
        cid = row.get("chunk_id")
        if cid in payloads and row.get("status") in {"ok", "truncated"}:
            if row.get("input_sha256") != payloads[cid]:
                result.update({"ok": False, "status": STATUS_ERROR, "reason": "INPUT_HASH_INTEGRITY_FAILED"})
                return result
    status = derive_receipt_status(expected, outcomes)
    result.update({"ok": status == STATUS_COMPLETE, "status": status})
    return result


def iter_receipts(project_root: str | Path, source_id: str | None = None) -> Iterable[dict[str, Any]]:
    root = _root(project_root)
    directory = root / RECEIPTS_REL
    if not directory.exists():
        return []
    rows = []
    for path in sorted(directory.glob("READ-*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if source_id is None or rec.get("source_id") == source_id:
            rows.append(rec)
    return rows
