#!/usr/bin/env python3
"""M1: frozen required-source set with immutable snapshots.

freeze_scope() copies each required file once into a content-addressed
snapshot store, hashing the stream during the copy and rechecking source
identity afterwards. A concurrent edit yields SOURCE_CHANGED, never a mixed
snapshot. An empty required set is refused unless the caller explicitly
passes allow_empty=True, which returns a NOT_APPLICABLE verdict scope.
"""
import hashlib
import os
from pathlib import Path

from .contracts import ContractError, require_sha256, require_unique_ids

SNAPSHOT_DIRNAME = ".snapshot"


class EmptyScopeError(ContractError):
    pass


class SourceChangedError(ContractError):
    pass


class PathEscapeError(ContractError):
    pass


def _resolve_inside(root, rel):
    root = Path(root).resolve()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise PathEscapeError("E_PATH_ESCAPE: %s escapes run root" % (rel,))
    if candidate.is_symlink():
        raise PathEscapeError("E_PATH_SYMLINK: %s is a symlink" % (rel,))
    return candidate


def _hash_stream(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_source(root, rel, store):
    """Copy one file to store/<sha256> and re-verify source identity."""
    root = Path(root).resolve()
    store = Path(store).resolve()
    candidate = _resolve_inside(root, rel)
    if not candidate.is_file():
        raise ContractError("E_SOURCE_MISSING: required source not a file: %s" % (rel,))
    try:
        pre_stat = candidate.stat()
        pre_digest = _hash_stream(candidate)
    except OSError as exc:
        raise ContractError("E_SOURCE_UNREADABLE: %s: %s" % (rel, exc))
    store.mkdir(parents=True, exist_ok=True)
    target = store / pre_digest
    if target.is_file():
        if _hash_stream(target) != pre_digest \
                or target.stat().st_size != pre_stat.st_size:
            raise ContractError("E_SNAPSHOT_CORRUPT: existing snapshot for %s fails re-verification; "
                                "quarantined, never trusted" % (rel,))
    else:
        tmp = store / (pre_digest + ".tmp-%d" % (os.getpid(),))
        with open(candidate, "rb") as src, open(tmp, "wb") as dst:
            while True:
                block = src.read(65536)
                if not block:
                    break
                dst.write(block)
        if _hash_stream(tmp) != pre_digest:
            tmp.unlink(missing_ok=True)
            raise ContractError("E_SNAPSHOT_MISMATCH: copied bytes differ: %s" % (rel,))
        tmp.replace(target)
    try:
        post_stat = candidate.stat()
        post_digest = _hash_stream(candidate)
    except OSError as exc:
        raise ContractError("E_SOURCE_UNREADABLE: %s: %s" % (rel, exc))
    if (post_stat.st_mtime_ns != pre_stat.st_mtime_ns or post_stat.st_size != pre_stat.st_size
            or post_digest != pre_digest):
        raise SourceChangedError("E_SOURCE_CHANGED: %s changed during snapshot" % (rel,))
    return {"path": Path(rel).as_posix(), "sha256": pre_digest,
            "bytes": len(target.read_bytes())}


def scope_digest(sources):
    h = hashlib.sha256()
    for entry in sorted(sources, key=lambda e: e["path"]):
        h.update(entry["path"].encode("utf-8"))
        h.update(b"\0")
        h.update(entry["sha256"].encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def freeze_scope(run_dir, paths, store_name=SNAPSHOT_DIRNAME, allow_empty=False):
    """Freeze an explicit required-source list. Returns the scope record."""
    run_dir = Path(run_dir).resolve()
    if not paths and not allow_empty:
        raise EmptyScopeError("E_EMPTY_SCOPE: required source set is empty")
    sources = []
    for rel in paths:
        sources.append(snapshot_source(run_dir, rel, run_dir / store_name))
    require_unique_ids([{"id": s["path"]} for s in sources], "scope.sources")
    record = {
        "schema_version": 2,
        "frozen": True,
        "verdict": "NOT_APPLICABLE" if not sources else "FROZEN",
        "sources": sorted(sources, key=lambda e: e["path"]),
    }
    record["scope_digest"] = scope_digest(record["sources"]) if sources else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    for entry in record["sources"]:
        require_sha256(entry["sha256"], "scope.sources.sha256")
    return record
