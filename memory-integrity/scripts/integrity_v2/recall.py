#!/usr/bin/env python3
"""M7: source-aware recall over authoritative local artifacts.

Indexes are rebuildable derivatives: exact sources, unit results, and run
maps live on disk independently of any embedding or summary. Questions
using all/every/totals/absence route through exhaustive enumeration over
the required set — never top-k retrieval. A changed source digest
invalidates cached answers; history stays labeled with its source version.
"""
import json
import hashlib
from pathlib import Path


class RecallError(ValueError):
    pass


def recall_coordinated_workspace(args):
    """Consume only a freshly verified complete coordinated workspace.

    Returns no recalled records on stale/revoked/incomplete dependencies.
    No cached summary or previously accepted flag bypasses this route.
    """
    from . import report
    out = report.verify_coordinated_workspace(args)
    if out.get("ok") is not True:
        out.pop("recall",None)
    return out


def build_index(units_text, source_digest):
    """units_text: {unit_id: text}. Returns a rebuildable in-memory index."""
    if not isinstance(units_text, dict) or not units_text:
        raise RecallError("E_INDEX_EMPTY: index needs units")
    return {"source_digest": source_digest,
            "units": dict(units_text)}


def open_unit(index, unit_id):
    try:
        return index["units"][unit_id]
    except KeyError:
        raise RecallError("E_UNIT_UNKNOWN: %r" % (unit_id,))


def locate(index, phrase, max_hits=50):
    """Substring locator. Returns [{unit_id}] in source order, not ranked."""
    if not phrase:
        raise RecallError("E_LOCATE_EMPTY: phrase required")
    ids = sorted(index["units"])
    hits = [{"unit_id": ident} for ident in ids if phrase in index["units"][ident]]
    truncated = len(hits) > max_hits
    return {"hits": hits[:max_hits], "truncated": truncated,
            "mode": "locator-not-semantic-search"}


def exhaustive(index, predicate, required_ids=None):
    """Apply predicate to EVERY required unit. No top-k shortcut.

    predicate(unit_id, text) -> True/False/None (None = abstain).
    Returns {matched, unmatched, abstained, coverage_basis}.
    """
    wanted = list(required_ids) if required_ids is not None else sorted(index["units"])
    unknown = [i for i in wanted if i not in index["units"]]
    if unknown:
        raise RecallError("E_EXHAUSTIVE_SCOPE: unknown units %s" % (unknown,))
    matched, unmatched, abstained = [], [], []
    for ident in wanted:
        verdict = predicate(ident, index["units"][ident])
        if verdict is True:
            matched.append(ident)
        elif verdict is False:
            unmatched.append(ident)
        else:
            abstained.append(ident)
    return {"matched": matched, "unmatched": unmatched, "abstained": abstained,
            "coverage_basis": {"units": len(wanted), "source_digest": index["source_digest"]}}


def save_run_map(path, run_map):
    for key in ("run_dir", "source_digests", "artifact_digests", "generation"):
        if key not in run_map:
            raise RecallError("E_RUNMAP_FIELD: missing %s" % (key,))
    Path(path).write_text(json.dumps(run_map, indent=2, sort_keys=True), encoding="utf-8")
    return run_map


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_digest(value):
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _strict_v3(run_map, source_digests_now):
    required = {"schema_version", "run_dir", "generation", "source_digests", "artifact_digests",
                "source_id", "task_digest", "profile_digest"}
    if not required <= set(run_map) or run_map.get("schema_version") != 3:
        raise RecallError("E_RUNMAP_V3: v3 run map is incomplete")
    root = Path(run_map["run_dir"])
    if not root.is_dir() or root.is_symlink():
        raise RecallError("E_RUNMAP_RUNDIR: run directory absent or symlinked")
    sources, artifacts = run_map["source_digests"], run_map["artifact_digests"]
    if not sources or not artifacts or set(sources) != set(source_digests_now):
        raise RecallError("E_RUNMAP_SOURCE_SET: current source IDs must exactly match frozen map")
    if run_map.get("source_id") not in sources:
        raise RecallError("E_RUNMAP_SOURCE_ID: selected source is not frozen")
    for collection in (sources, artifacts):
        if not isinstance(collection, dict) or any(not _valid_digest(v) for v in collection.values()):
            raise RecallError("E_RUNMAP_DIGEST: all v3 digests must be SHA-256")
    required_files = {"source.bin", "manifest.json", "task.json", "profile.json", "scope.json",
                      "extraction.json", "semantic.json", "ledger.sqlite"}
    if not required_files <= set(artifacts):
        raise RecallError("E_RUNMAP_ARTIFACTS: required run artifacts are not all bound")
    for rel, digest in artifacts.items():
        p = Path(rel)
        if p.is_absolute() or ".." in p.parts or not rel or p.parts[0] == ".":
            raise RecallError("E_RUNMAP_PATH: artifact path is not bounded")
        target = root / p
        try:
            target.relative_to(root)
        except ValueError:
            raise RecallError("E_RUNMAP_PATH: artifact escapes run directory")
        relative_chain = [target] + list(target.parents)
        if (not target.is_file() or any(part.is_symlink() for part in relative_chain
                                        if part != root.parent)
                or _sha256_file(target) != digest):
            raise RecallError("E_RUNMAP_ARTIFACT: artifact missing, symlinked, or hash-mismatched: %s" % rel)
    if source_digests_now != sources:
        raise RecallError("E_RUNMAP_STALE: source content no longer equals frozen map")


def load_run_map(path, source_digests_now):
    """Reopen a run map in a fresh process. Changed sources invalidate.

    The stored map itself is validated first: missing keys, a non-directory
    run_dir, or an empty generation is a corrupt map (RecallError), never a
    current one. Artifact-file existence additionally needs a defined run-dir
    layout contract, which this loader does not invent: maps whose artifacts
    cannot be located must be re-verified by the owning runner.
    """
    try:
        run_map = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecallError("E_RUNMAP_UNREADABLE: %s" % (exc,))
    if not isinstance(run_map, dict):
        raise RecallError("E_RUNMAP_TYPE: run map must be an object")
    for key in ("run_dir", "source_digests", "artifact_digests", "generation"):
        if key not in run_map:
            raise RecallError("E_RUNMAP_FIELD: missing %s" % (key,))
    if not isinstance(run_map["source_digests"], dict) \
            or not isinstance(run_map["artifact_digests"], dict):
        raise RecallError("E_RUNMAP_TYPE: digest maps must be objects")
    if not isinstance(run_map["generation"], str) or not run_map["generation"].strip():
        raise RecallError("E_RUNMAP_GENERATION: generation must be non-empty")
    for where in ("source_digests", "artifact_digests"):
        for name, digest in run_map[where].items():
            if not isinstance(digest, str) or not digest.strip():
                raise RecallError("E_RUNMAP_DIGEST: %s[%s] must be non-empty" % (where, name))
    if not Path(run_map["run_dir"]).is_dir():
        raise RecallError("E_RUNMAP_RUNDIR: run dir %r absent; map is stale"
                          % (run_map["run_dir"],))
    if run_map.get("schema_version") == 3:
        _strict_v3(run_map, source_digests_now)
    stale = {k: v for k, v in run_map.get("source_digests", {}).items()
             if source_digests_now.get(k) != v}
    # Pre-v3 maps never bound a portable artifact layout. They are readable
    # history but cannot be used as fresh authoritative evidence.
    return {"run_map": run_map, "stale_sources": sorted(stale),
            "current": not stale and run_map.get("schema_version") == 3,
            "historical_unverified": run_map.get("schema_version") != 3}
