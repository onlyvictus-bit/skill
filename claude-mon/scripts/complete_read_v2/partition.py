#!/usr/bin/env python3
"""M1: exact byte/structural units, strict partition manifests, verification.

Units are line spans with half-open byte ranges [start, end). Oversized lines
are subdivided into byte-safe child spans with parent lineage; the bound is
never quietly exceeded. Chunks partition primary units exactly once; context
copies are informational and never count toward coverage. Verification
recomputes everything from the frozen source bytes: stored payload hashes and
stored manifest digests are both re-derived, never trusted.
"""
import hashlib

from .contracts import (
    ContractError,
    require_keys,
    require_sha256,
    require_unique_ids,
)

MANIFEST_KEYS = {"schema_version", "source_id", "source_digest", "max_primary_bytes",
                 "units", "chunks", "manifest_digest"}
UNIT_KEYS = {"id", "range", "sha256", "parent", "kind", "ordinal"}
UNIT_KINDS = {"line", "line-span"}
CHUNK_KEYS = {"id", "primary", "context_before", "context_after", "payload_sha256"}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def decode_strict(data):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("E_ENCODING: source is not strict UTF-8: %s" % (exc,))


def _split_bytes_safe(blob, bound):
    """Split bytes into pieces <= bound at UTF-8 character boundaries."""
    pieces, pos = [], 0
    while pos < len(blob):
        end = min(pos + bound, len(blob))
        while end > pos and (blob[end] if end < len(blob) else 0) & 0xC0 == 0x80:
            end -= 1
        if end == pos:
            raise ContractError("E_UNIT_UNSCHEDULABLE: bound %d below one encoded char" % (bound,))
        pieces.append(blob[pos:end])
        pos = end
    return pieces


def unitize(source_bytes, max_unit_bytes=65536):
    """Line units with exact byte ranges. Oversized lines become child spans."""
    text = decode_strict(source_bytes)
    units, pos, ordinal = [], 0, 0
    for lineno, line in enumerate(text.splitlines(keepends=True), start=1):
        blob = line.encode("utf-8")
        if len(blob) <= max_unit_bytes:
            units.append({"id": "U%06d" % (ordinal + 1,), "range": [pos, pos + len(blob)],
                          "sha256": sha256_bytes(blob), "parent": None,
                          "kind": "line", "ordinal": ordinal})
            ordinal += 1
        else:
            parent = "U%06d" % (ordinal + 1,)
            for idx, piece in enumerate(_split_bytes_safe(blob, max_unit_bytes), start=1):
                units.append({"id": "%s.%d" % (parent, idx),
                              "range": [pos, pos + len(piece)],
                              "sha256": sha256_bytes(piece), "parent": parent,
                              "kind": "line-span", "ordinal": ordinal})
                pos += len(piece)
                ordinal += 1
            continue
        pos += len(blob)
    if pos != len(source_bytes):
        raise ContractError("E_UNITIZE: unit ranges cover %d of %d bytes" % (pos, len(source_bytes)))
    return units


def chunk_units(units, max_primary_bytes=262144, context_units=1):
    """Greedy ordered pack. Raises if one unit alone exceeds the chunk bound."""
    chunks, current, current_bytes, number = [], [], 0, 0
    ids = [u["id"] for u in units]
    for unit, size in ((u, u["range"][1] - u["range"][0]) for u in units):
        if size > max_primary_bytes:
            raise ContractError("E_CHUNK_UNSCHEDULABLE: unit %s (%d bytes) exceeds chunk bound %d"
                                % (unit["id"], size, max_primary_bytes))
        if current and current_bytes + size > max_primary_bytes:
            chunks.append((number, current))
            current, current_bytes = [], 0
        if not current:
            number += 1
        current.append(unit["id"])
        current_bytes += size
    if current:
        chunks.append((number, current))
    out = []
    position = {ident: idx for idx, ident in enumerate(ids)}
    for number, primary in chunks:
        idx = [position[pid] for pid in primary]
        before = [ids[i] for i in range(max(0, min(idx) - context_units), min(idx))]
        after = [ids[i] for i in range(max(idx) + 1, min(len(ids), max(idx) + 1 + context_units))]
        out.append({"id": "C%08d" % (number,), "primary": primary,
                    "context_before": before, "context_after": after, "payload_sha256": None})
    return out


def payload_bytes(source_bytes, manifest, chunk, table=None):
    """Exact dispatched material: context_before + primary + context_after.

    Declared context is part of the payload, never silently dropped: a chunk
    whose payload lacks its declared neighbors fails validation.
    """
    order = list(chunk.get("context_before", [])) + list(chunk.get("primary", [])) \
        + list(chunk.get("context_after", []))
    return b"".join(source_bytes[u["range"][0]:u["range"][1]]
                    for u in _units_by_id(manifest, order, table))


def _units_by_id(manifest, ids, table=None):
    if table is None:
        table = {u["id"]: u for u in manifest["units"]}
    try:
        return [table[i] for i in ids]
    except KeyError as exc:
        raise ContractError("E_REF_UNIT: chunk references unknown unit %s" % (exc,))


def build_manifest(source_id, source_bytes, max_unit_bytes=65536,
                   max_primary_bytes=262144, context_units=1):
    units = unitize(source_bytes, max_unit_bytes)
    chunks = chunk_units(units, max_primary_bytes, context_units)
    manifest = {"schema_version": 2, "source_id": source_id,
                "source_digest": sha256_bytes(source_bytes),
                "max_primary_bytes": max_primary_bytes,
                "units": units, "chunks": chunks, "manifest_digest": None}
    table = {u["id"]: u for u in units}
    for chunk in chunks:
        chunk["payload_sha256"] = sha256_bytes(payload_bytes(source_bytes, manifest, chunk,
                                                              table))
    manifest["manifest_digest"] = manifest_digest(manifest)
    return manifest


def manifest_digest(manifest):
    import json
    body = {k: v for k, v in manifest.items() if k != "manifest_digest"}
    return sha256_bytes(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8"))


def validate_manifest(source_bytes, manifest):
    """Recompute everything. Returns list of error strings (empty = valid)."""
    errors = []
    try:
        decode_strict(source_bytes)
    except ContractError as exc:
        return [str(exc)]
    try:
        require_keys(manifest, MANIFEST_KEYS - {"manifest_digest"}, MANIFEST_KEYS, "manifest")
    except ContractError as exc:
        return [str(exc)]
    if manifest.get("schema_version") != 2:
        return ["E_SCHEMA_VERSION: manifest schema must be 2"]
    try:
        require_sha256(manifest.get("source_digest", ""), "manifest.source_digest")
    except ContractError as exc:
        return [str(exc)]
    if manifest["source_digest"] != sha256_bytes(source_bytes):
        return ["E_SOURCE_BINDING_MISMATCH: manifest bound to a different source"]
    units = manifest.get("units", [])
    try:
        require_unique_ids(units, "manifest.units")
    except ContractError as exc:
        return [str(exc)]
    size = len(source_bytes)
    cursor = 0
    for idx, unit in enumerate(units):
        try:
            require_keys(unit, UNIT_KEYS, UNIT_KEYS, "manifest.units")
        except ContractError as exc:
            return [str(exc)]
        if unit.get("kind") not in UNIT_KINDS:
            return ["E_UNIT_KIND: unit %s has unknown kind %r" % (unit.get("id"), unit.get("kind"))]
        ordinal = unit.get("ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
            return ["E_UNIT_ORDINAL: unit %s ordinal must be a non-negative int"
                    % (unit.get("id"),)]
        if idx > 0 and ordinal <= units[idx - 1].get("ordinal", -1):
            return ["E_UNIT_ORDINAL: unit %s ordinal not strictly increasing"
                    % (unit.get("id"),)]
        start, end = unit.get("range", [None, None])
        if not isinstance(start, int) or not isinstance(end, int) or start != cursor or end <= start:
            if isinstance(start, int) and isinstance(end, int) and start < cursor and end > start:
                return ["E_RANGE_OVERLAP: unit %s overlaps previous coverage" % (unit.get("id"),)]
            if isinstance(start, int) and start > cursor:
                return ["E_RANGE_GAP: missing bytes [%d, %d)" % (cursor, start)]
            return ["E_RANGE_ORDER: unit %s out of order" % (unit.get("id"),)]
        if end > size:
            return ["E_RANGE_BOUNDS: unit %s exceeds source" % (unit.get("id"),)]
        if sha256_bytes(source_bytes[start:end]) != unit.get("sha256"):
            return ["E_UNIT_HASH: unit %s content mismatch" % (unit.get("id"),)]
        cursor = end
    if cursor != size:
        return ["E_RANGE_GAP: missing trailing bytes [%d, %d)" % (cursor, size)]
    chunks = manifest.get("chunks", [])
    try:
        require_unique_ids(chunks, "manifest.chunks")
    except ContractError as exc:
        return [str(exc)]
    unit_ids = {u["id"] for u in units}
    table = {u["id"]: u for u in units}
    position = {u["id"]: n for n, u in enumerate(units)}
    covered = []
    for chunk in chunks:
        try:
            require_keys(chunk, CHUNK_KEYS, CHUNK_KEYS, "manifest.chunks")
        except ContractError as exc:
            return [str(exc)]
        for pid in chunk.get("primary", []):
            if pid not in unit_ids:
                return ["E_REF_UNIT: chunk %s references unknown unit %s"
                        % (chunk.get("id"), pid)]
            covered.append(pid)
        for cid in list(chunk.get("context_before", [])) + list(chunk.get("context_after", [])):
            if cid not in unit_ids:
                return ["E_REF_UNIT: chunk %s references unknown context %s"
                        % (chunk.get("id"), cid)]
        prim_pos = sorted(position[pid] for pid in chunk.get("primary", []))
        before = list(chunk.get("context_before", []))
        after = list(chunk.get("context_after", []))
        if not prim_pos:
            return ["E_CHUNK_EMPTY: chunk %s has no primary units" % (chunk.get("id"),)]
        if [position[pid] for pid in chunk.get("primary", [])] != list(range(prim_pos[0], prim_pos[-1] + 1)):
            return ["E_PRIMARY_ORDER: chunk %s primary units are not one ordered run" %
                    (chunk.get("id"),)]
        if [position[c] for c in before] != list(range(prim_pos[0] - len(before), prim_pos[0])):
            return ["E_CONTEXT_ORDER: chunk %s context_before is not the adjacent run"
                    % (chunk.get("id"),)]
        if [position[c] for c in after] != list(range(prim_pos[-1] + 1, prim_pos[-1] + 1 + len(after))):
            return ["E_CONTEXT_ORDER: chunk %s context_after is not the adjacent run"
                    % (chunk.get("id"),)]
        primary_bytes = sum(table[pid]["range"][1] - table[pid]["range"][0]
                            for pid in chunk.get("primary", []))
        if primary_bytes > manifest.get("max_primary_bytes", 0):
            return ["E_CHUNK_BOUND: chunk %s primary %d bytes exceeds declared bound %d"
                    % (chunk.get("id"), primary_bytes, manifest.get("max_primary_bytes", 0))]
        expect = sha256_bytes(payload_bytes(source_bytes, manifest, chunk, table))
        if chunk.get("payload_sha256") != expect:
            return ["E_PAYLOAD_MISMATCH: chunk %s payload hash wrong" % (chunk.get("id"),)]
    if sorted(covered) != sorted(unit_ids):
        from collections import Counter
        counts = Counter(covered)
        missing = sorted(unit_ids - set(covered))
        dupes = sorted(i for i, c in counts.items() if c > 1)
        if missing:
            return ["E_PARTITION_GAP: units without primary chunk: %s" % (",".join(missing))]
        return ["E_PARTITION_DUPLICATE: units in several primary chunks: %s" % (",".join(dupes))]
    if manifest.get("manifest_digest") != manifest_digest(manifest):
        return ["E_MANIFEST_DIGEST_MISMATCH: stored manifest digest is stale or forged"]
    return []


def reassemble(source_bytes, manifest):
    """Concatenate units in range order. Byte equality with source is the test."""
    units = sorted(manifest["units"], key=lambda u: u["range"][0])
    return b"".join(source_bytes[u["range"][0]:u["range"][1]] for u in units)
