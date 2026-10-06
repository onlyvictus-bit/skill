"""Branch observation and conservative TEST_ONLY three-way merge policy.

Git source identity and Dolt task-database identity are explicitly separate.
This module previews task-state data only; it never merges user source code or
calls ``bd vc merge``.  Native application remains disabled until M7.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import os

from . import graph


class MergeRefused(ValueError):
    pass


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                          text=True, encoding="utf-8", timeout=5, check=False)


def observe_git_workspace(path):
    """Read a Git identity if one exists; non-Git is a declared boundary."""
    path = Path(path)
    probe = _git(path, "rev-parse", "--show-toplevel")
    if probe.returncode != 0:
        return {"kind": "NON_GIT", "git_observed": False, "workspace": str(path),
                "reason": "no observable Git repository"}
    root = Path(probe.stdout.strip())
    head = _git(root, "rev-parse", "HEAD")
    base = _git(root, "rev-parse", "HEAD^" if head.returncode == 0 else "HEAD")
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    names = _git(root,"ls-files","-z","--cached","--others","--exclude-standard")
    if status.returncode or names.returncode:
        raise MergeRefused("E_GIT_OBSERVATION_PARTIAL")
    contents = []
    for rel in sorted(set(names.stdout.split("\0"))-{ "" }):
        source_path = root/rel
        if not source_path.resolve().is_relative_to(root.resolve()):
            raise MergeRefused("E_GIT_PATH_ESCAPE")
        if source_path.is_symlink():
            contents.append((rel,"symlink",os.readlink(source_path)))
        elif source_path.is_file():
            contents.append((rel,"file",hashlib.sha256(source_path.read_bytes()).hexdigest()))
        else:
            contents.append((rel,"deleted",None))
    source_digest = _digest({"status":status.stdout,"contents":contents})
    branch_name = _git(root,"symbolic-ref","--quiet","--short","HEAD")
    git_dir = _git(root,"rev-parse","--absolute-git-dir")
    return {
        "kind": "GIT", "git_observed": True, "workspace": str(path),
        "repository_root": str(root), "repository_id": hashlib.sha256(str(root).encode("utf-8")).hexdigest(),
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "branch": branch_name.stdout.strip() if branch_name.returncode==0 else "DETACHED_OR_UNBORN",
        "worktree_git_dir":git_dir.stdout.strip() if git_dir.returncode==0 else None,
        "base": base.stdout.strip() if base.returncode == 0 else None,
        "dirty_source_digest": source_digest, "dirty": bool(status.stdout.strip()),
    }


def _validate_origin(origin, label):
    if not isinstance(origin, dict):
        raise MergeRefused("E_MERGE_%s_ORIGIN" % label.upper())
    for key in ("database", "branch", "head", "tasks", "edges", "evidence", "cas_digest","evidence_class"):
        if key not in origin:
            raise MergeRefused("E_MERGE_%s_%s" % (label.upper(), key.upper()))
    if origin.get("evidence_class") != "TEST_ONLY":
        raise MergeRefused("E_MERGE_UNSUPPORTED_EVIDENCE_CLASS")
    if not isinstance(origin["tasks"], dict) or not isinstance(origin["evidence"], dict):
        raise MergeRefused("E_MERGE_%s_STATE" % label.upper())
    for key in ("database","branch","head"):
        if not isinstance(origin[key],str) or not origin[key].strip():
            raise MergeRefused("E_MERGE_IDENTITY")
    if not isinstance(origin["cas_digest"],str) or len(origin["cas_digest"])!=64:
        raise MergeRefused("E_MERGE_CAS")
    try:
        int(origin["cas_digest"],16)
    except ValueError as exc:
        raise MergeRefused("E_MERGE_CAS") from exc


def _map_merge(base, source, target, category):
    keys = sorted(set(base) | set(source) | set(target))
    merged, conflicts = {}, []
    sentinel = object()
    for key in keys:
        before, left, right = base.get(key, sentinel), source.get(key, sentinel), target.get(key, sentinel)
        if left == right:
            chosen = left
        elif right == before:
            chosen = left
        elif left == before:
            chosen = right
        else:
            conflicts.append({"category": category, "key": key, "base": None if before is sentinel else before,
                              "source": None if left is sentinel else left, "target": None if right is sentinel else right})
            continue
        if chosen is not sentinel:
            merged[key] = chosen
    return merged, conflicts


def _changes(base,other):
    return [{"id":key,"before_present":key in base,"after_present":key in other,
             "before":base.get(key),"after":other.get(key)}
            for key in sorted(set(base)|set(other))
            if (key in base)!=(key in other) or base.get(key)!=other.get(key)]


def _edge_map(origin):
    result = {}
    for edge in origin["edges"]:
        if not isinstance(edge, dict):
            raise MergeRefused("E_MERGE_EDGE_TYPE")
        # The endpoints, rather than the full relation tuple, are the logical
        # dependency identity.  Thus source changing a hard edge to
        # informational while target removes it is a conflict, not two
        # unrelated edits that happen to have adjacent spelling.
        key = "%s\x00%s" % (edge.get("from"), edge.get("to"))
        if key in result:
            raise MergeRefused("E_MERGE_DUPLICATE_EDGE")
        result[key] = {"from": edge.get("from"), "to": edge.get("to"), "relation": edge.get("relation")}
    return result


def preview_merge(base, source, target, common_ancestor):
    """Make a deterministic three-way preview, refusing conflict magic.

    ``common_ancestor`` must be observed rather than inferred from branch names.
    The caller is responsible for reading native heads and must call apply with
    those heads again, so a moved head is not silently merged.
    """
    for value, label in ((base, "base"), (source, "source"), (target, "target")):
        _validate_origin(value, label)
    if not isinstance(common_ancestor, str) or not common_ancestor:
        raise MergeRefused("E_MERGE_UNKNOWN_ANCESTRY")
    if base["head"] != common_ancestor:
        raise MergeRefused("E_MERGE_BASE_NOT_COMMON_ANCESTOR")
    if len({base["database"], source["database"], target["database"]}) != 1:
        raise MergeRefused("E_MERGE_FOREIGN_DATABASE")
    tasks, conflicts = _map_merge(base["tasks"], source["tasks"], target["tasks"], "task_state")
    evidence, more = _map_merge(base["evidence"], source["evidence"], target["evidence"], "evidence_basis")
    conflicts.extend(more)
    edge_map, more = _map_merge(_edge_map(base), _edge_map(source), _edge_map(target), "dependency")
    conflicts.extend(more)
    graph_error = None
    if not conflicts:
        try:
            graph.freeze_snapshot({"workspace": "merge:%s" % base["database"], "revision": _digest({"tasks": tasks, "edges": edge_map}),
                                   "tasks": sorted(tasks), "edges": list(edge_map.values()), "complete_read": True,"evidence_class":"TEST_ONLY"})
        except graph.GraphContractError as exc:
            graph_error = str(exc)
            conflicts.append({"category": "resulting_graph", "key": "graph", "reason": graph_error})
    preview = {
        "schema_version": 1, "mode": "TEST_ONLY_PREVIEW", "mergeable": not conflicts,
        "common_ancestor": common_ancestor,
        "base_origin": {k: base[k] for k in ("database", "branch", "head", "cas_digest", "evidence_class")},
        "source_origin": {k: source[k] for k in ("database", "branch", "head", "cas_digest", "evidence_class")},
        "target_origin": {k: target[k] for k in ("database", "branch", "head", "cas_digest", "evidence_class")},
        "source_head_at_preview": source["head"], "target_head_at_preview": target["head"],
        "conflicts": conflicts, "merged_tasks": tasks if not conflicts else None,
        "changed_tasks":{"source":_changes(base["tasks"],source["tasks"]),"target":_changes(base["tasks"],target["tasks"])},
        "changed_edges":{"source":_changes(_edge_map(base),_edge_map(source)),"target":_changes(_edge_map(base),_edge_map(target))},
        "changed_evidence":{"source":_changes(base["evidence"],source["evidence"]),"target":_changes(base["evidence"],target["evidence"])},
        "evidence_applicability":{"fresh_evidence_required":True,"accepted_evidence_imported":False,
            "tasks_to_revalidate":sorted(tasks),"reason":"merged head is a new approved applicability basis"},
        "merged_edges": list(edge_map.values()) if not conflicts else None,
        "merged_evidence": evidence if not conflicts else None,
        "graph_error": graph_error,
        "note": "no ours/theirs strategy; conflict requires explicit resolution event",
    }
    preview["preview_digest"] = _digest(preview)
    return preview


def apply_fixture_preview(preview, current_source_head, current_target_head):
    """Apply only a clean in-memory preview after stable-head re-observation.

    It returns the exact merge event payload that CM's central ledger must bind
    to its intent/outcome records.  It never uses an old approval or changes a
    real task database.
    """
    if not isinstance(preview, dict) or preview.get("mode") != "TEST_ONLY_PREVIEW":
        raise MergeRefused("E_MERGE_PREVIEW")
    if preview.get("preview_digest")!=_digest({k:v for k,v in preview.items() if k!="preview_digest"}):
        raise MergeRefused("E_MERGE_PREVIEW_CHANGED")
    if not preview.get("mergeable"):
        raise MergeRefused("E_MERGE_CONFLICT: explicit resolution required")
    if current_source_head != preview.get("source_head_at_preview") or current_target_head != preview.get("target_head_at_preview"):
        raise MergeRefused("E_MERGE_MOVED_HEAD")
    payload = {
        "common_ancestor": preview["common_ancestor"],
        "base_origin": dict(preview["base_origin"]),
        "base_cas_digest": preview["base_origin"]["cas_digest"],
        "source_origin": dict(preview["source_origin"]),
        "target_origin": dict(preview["target_origin"]),
        "source_cas_digest": preview["source_origin"]["cas_digest"],
        "target_cas_digest": preview["target_origin"]["cas_digest"],
        "merged_graph_digest": _digest({"tasks": preview["merged_tasks"], "edges": preview["merged_edges"]}),
        "fresh_evidence_required": True,
        "approval_reused": False,
    }
    return {"status": "TEST_ONLY_MERGED", "event_payload": payload,
            "merged_tasks": dict(preview["merged_tasks"]), "merged_edges": list(preview["merged_edges"]),
            "approval_reused": False, "fresh_evidence_required": True}


def freeze_origin(origin,cas_module,store):
    """Retain exact fixture origin bytes with a non-self-referential CAS ref."""
    body = {k:v for k,v in origin.items() if k!="cas_digest"}
    frozen = dict(body,cas_digest=cas_module.store_bytes(store,_canon(body).encode("utf-8")))
    _validate_origin(frozen,"frozen")
    return frozen


def _retained_origins(payload,cas_module,store):
    origins=[]
    for name in ("base","source","target"):
        digest=payload[name+"_cas_digest"]
        body=json.loads(cas_module.open_verified(store,digest))
        origin=dict(body,cas_digest=digest)
        _validate_origin(origin,name)
        if {k:origin[k] for k in ("database","branch","head","cas_digest","evidence_class")}!=payload[name+"_origin"]:
            raise MergeRefused("E_MERGE_RETAINED_ORIGIN_MISMATCH")
        origins.append(origin)
    return origins


def _retained_result(payload,cas_module,store):
    base,source,target=_retained_origins(payload,cas_module,store)
    preview=preview_merge(base,source,target,payload["common_ancestor"])
    if preview["preview_digest"]!=payload["preview_digest"]:
        raise MergeRefused("E_MERGE_RETAINED_PREVIEW_MISMATCH")
    merged=apply_fixture_preview(preview,source["head"],target["head"])
    if merged["event_payload"]["merged_graph_digest"]!=payload["merged_graph_digest"]:
        raise MergeRefused("E_MERGE_RETAINED_GRAPH_MISMATCH")
    return merged


def verify_retained_merge(payload,cas_module,store):
    """Reopen both origins, base and result at every current consumption."""
    merged=_retained_result(payload,cas_module,store)
    actual=json.loads(cas_module.open_verified(store,payload["merged_result_digest"]))
    if actual!=merged or payload.get("evidence_refs")!=[payload[n+"_cas_digest"] for n in ("base","source","target")]+[payload["merged_result_digest"]]:
        raise MergeRefused("E_MERGE_RETAINED_RESULT_MISMATCH")
    return True


def reconcile_central_fixture_merge(journal,cas_module,store,operation_id):
    """Reconstruct a pure fixture result from retained intent, never retry native.

    A native merge outcome cannot be inferred this way. This seam is explicitly
    TEST_ONLY and only seals the deterministic fixture policy result.
    """
    previous=journal.last(operation_id)
    if not previous or previous["kind"] not in ("NATIVE_MERGE_INTENT","NATIVE_MERGE_OUTCOME"):
        raise MergeRefused("E_MERGE_RECONCILE_STATE")
    payload=previous["payload"]
    if previous["kind"]=="NATIVE_MERGE_OUTCOME":
        verify_retained_merge(payload,cas_module,store)
        return {"status":"IDEMPOTENT_TEST_ONLY_MERGED","fresh_evidence_required":True,"approval_reused":False}
    merged=_retained_result(payload,cas_module,store)
    digest=cas_module.store_bytes(store,_canon(merged).encode("utf-8"))
    outcome=dict(payload,merged_result_digest=digest,
                 evidence_refs=payload["evidence_refs"]+[digest],
                 recovery="pure fixture result reconstruction; no native operation")
    verify_retained_merge(outcome,cas_module,store)
    journal.append("NATIVE_MERGE_OUTCOME",operation_id,outcome)
    return dict(merged,status="TEST_ONLY_RECONCILED_MERGE")


def apply_central_fixture_merge(base,source,target,ancestor,source_head,target_head,
                               journal,cas_module,store,operation_id):
    """Observe three-way policy and retain both CAS origins in CM central chain.

    This applies task state in a fixture, never source code or a native DB.
    Merged closure/status is not CM acceptance. Old task policy/approvals are
    not migrated; an approved successor basis and fresh audit are required.
    """
    preview = preview_merge(base,source,target,ancestor)
    merged = apply_fixture_preview(preview,source_head,target_head)
    for origin in (base,source,target):
        actual = json.loads(cas_module.open_verified(store,origin["cas_digest"]))
        if actual!={k:v for k,v in origin.items() if k!="cas_digest"}:
            raise MergeRefused("E_MERGE_ORIGIN_CAS_MISMATCH")
    previous = journal.last(operation_id)
    payload = dict(merged["event_payload"],base_cas_digest=base["cas_digest"],
                   preview_digest=preview["preview_digest"],evidence_class="TEST_ONLY",
                   evidence_refs=[base["cas_digest"],source["cas_digest"],target["cas_digest"]])
    if previous:
        if previous["payload"].get("preview_digest")!=preview["preview_digest"]:
            raise MergeRefused("E_MERGE_OPERATION_REBIND")
        if previous["kind"]=="NATIVE_MERGE_OUTCOME":
            verify_retained_merge(previous["payload"],cas_module,store)
            return dict(merged,status="IDEMPOTENT_TEST_ONLY_MERGED")
        return {"status":"UNKNOWN","action":"reconcile interrupted merge intent; no repeated application"}
    journal.append("NATIVE_MERGE_INTENT",operation_id,payload)
    merged_digest = cas_module.store_bytes(store,_canon(merged).encode("utf-8"))
    journal.append("NATIVE_MERGE_OUTCOME",operation_id,dict(payload,merged_result_digest=merged_digest,
                    evidence_refs=payload["evidence_refs"]+[merged_digest]))
    return merged
