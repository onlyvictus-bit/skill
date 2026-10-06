"""Frozen, policy-validated task graphs for the optional Beads bridge.

This module intentionally does *not* call ``bd`` or decide that a task is
accepted.  A Beads ready/closed field is an operational observation only.
The companion's current evidence policy remains the only input that can make a
hard prerequisite eligible.  The functions are pure so that M3/M4 policy can
be tested without a native database; a native adapter must supply the same
fully-read snapshot before it can be used in M7.
"""
from __future__ import annotations

import hashlib
import json


HARD_RELATION = "hard"
INFORMATIONAL_RELATION = "informational"
SUPPORTED_RELATIONS = frozenset((HARD_RELATION, INFORMATIONAL_RELATION))


class GraphContractError(ValueError):
    """The imported graph is incomplete or has unsupported semantics."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _task_ids(raw_tasks, workspace):
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise GraphContractError("E_GRAPH_TASKS: non-empty task list required")
    ids = []
    for task in raw_tasks:
        if isinstance(task, str):
            task_id, task_workspace = task, workspace
        elif isinstance(task, dict):
            task_id = task.get("id")
            task_workspace = task.get("workspace", workspace)
        else:
            raise GraphContractError("E_GRAPH_TASK_TYPE: task must be id or object")
        if not isinstance(task_id, str) or not task_id.strip():
            raise GraphContractError("E_GRAPH_TASK_ID: non-empty task id required")
        if task_workspace != workspace:
            raise GraphContractError("E_GRAPH_FOREIGN_TASK: %s" % task_id)
        ids.append(task_id)
    if len(ids) != len(set(ids)):
        raise GraphContractError("E_GRAPH_DUPLICATE_TASK")
    return tuple(sorted(ids))


def _normalise_edges(raw_edges, task_ids, workspace):
    if not isinstance(raw_edges, list):
        raise GraphContractError("E_GRAPH_EDGES: list required")
    known = set(task_ids)
    edges = []
    for edge in raw_edges:
        if not isinstance(edge, dict):
            raise GraphContractError("E_GRAPH_EDGE_TYPE: edge object required")
        source, target, relation = edge.get("from"), edge.get("to"), edge.get("relation")
        if edge.get("workspace", workspace) != workspace:
            raise GraphContractError("E_GRAPH_FOREIGN_EDGE")
        if relation not in SUPPORTED_RELATIONS:
            raise GraphContractError("E_GRAPH_UNSUPPORTED_RELATION: %r" % relation)
        if source not in known or target not in known:
            raise GraphContractError("E_GRAPH_MISSING_NODE: %r -> %r" % (source, target))
        if source == target:
            raise GraphContractError("E_GRAPH_SELF_EDGE: %s" % source)
        edges.append({"from": source, "to": target, "relation": relation})
    unique = {(e["from"], e["to"], e["relation"]) for e in edges}
    if len(unique) != len(edges):
        raise GraphContractError("E_GRAPH_DUPLICATE_EDGE")
    return tuple(sorted(edges, key=lambda e: (e["from"], e["to"], e["relation"])))


def _reject_hard_cycles(task_ids, edges):
    outgoing = {task: [] for task in task_ids}
    for edge in edges:
        if edge["relation"] == HARD_RELATION:
            outgoing[edge["from"]].append(edge["to"])
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            raise GraphContractError("E_GRAPH_CYCLE: hard prerequisite cycle at %s" % node)
        if node in visited:
            return
        visiting.add(node)
        for child in outgoing[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for task in task_ids:
        visit(task)


def freeze_snapshot(raw):
    """Validate and canonically freeze a fully read task/edge graph.

    The returned digest is a *basis locator*, not proof that a native Beads
    query was complete.  Native code must record pagination/read evidence
    separately and refuse a partial result before calling this function.
    Edge direction is prerequisite ``from`` -> dependent ``to``.
    """
    if not isinstance(raw, dict):
        raise GraphContractError("E_GRAPH_INPUT: object required")
    workspace, revision = raw.get("workspace"), raw.get("revision")
    if not isinstance(workspace, str) or not workspace.strip():
        raise GraphContractError("E_GRAPH_WORKSPACE: non-empty workspace required")
    if not isinstance(revision, str) or not revision.strip():
        raise GraphContractError("E_GRAPH_REVISION: non-empty revision required")
    task_ids = _task_ids(raw.get("tasks"), workspace)
    edges = _normalise_edges(raw.get("edges", []), task_ids, workspace)
    _reject_hard_cycles(task_ids, edges)
    frozen = {
        "schema_version": 1,
        "workspace": workspace,
        "revision": revision,
        "tasks": list(task_ids),
        "edges": list(edges),
        "complete_read": raw.get("complete_read"),
        "evidence_class": raw.get("evidence_class"),
    }
    if frozen["complete_read"] is not True:
        raise GraphContractError("E_GRAPH_PARTIAL_READ: cannot prove absent blockers")
    if frozen["evidence_class"]!="TEST_ONLY":
        raise GraphContractError("E_GRAPH_EVIDENCE_CLASS: explicit TEST_ONLY required before native qualification")
    frozen["graph_digest"] = _digest(frozen)
    return frozen


def hard_prerequisites(frozen, task_id, transitive=True):
    """Return all hard predecessor ids, deterministically, after validation."""
    if not isinstance(frozen, dict) or "graph_digest" not in frozen:
        raise GraphContractError("E_GRAPH_UNFROZEN: use freeze_snapshot first")
    if frozen["graph_digest"]!=_digest({k:v for k,v in frozen.items() if k!="graph_digest"}):
        raise GraphContractError("E_GRAPH_CHANGED: frozen graph bytes changed")
    if task_id not in frozen["tasks"]:
        raise GraphContractError("E_GRAPH_UNKNOWN_TASK: %s" % task_id)
    incoming = {task: [] for task in frozen["tasks"]}
    for edge in frozen["edges"]:
        if edge["relation"] == HARD_RELATION:
            incoming[edge["to"]].append(edge["from"])
    if not transitive:
        return tuple(sorted(incoming[task_id]))
    answer, todo = set(), list(incoming[task_id])
    while todo:
        current = todo.pop()
        if current not in answer:
            answer.add(current)
            todo.extend(incoming[current])
    return tuple(sorted(answer))


def eligibility(frozen, task_id, core_evidence):
    """Return an explainable scheduling eligibility decision.

    ``core_evidence`` is supplied by the CM shared eligibility capability. A
    native ``closed`` status is deliberately ignored; it is retained only in
    the explanation so manual native closure cannot unlock dependent work.
    """
    prerequisites = hard_prerequisites(frozen, task_id)
    if not isinstance(core_evidence, dict):
        raise GraphContractError("E_GRAPH_EVIDENCE: mapping required")
    blockers = []
    observations = {}
    for prerequisite in prerequisites:
        item = core_evidence.get(prerequisite)
        eligible = isinstance(item, dict) and item.get("eligible") is True
        observations[prerequisite] = {
            "core_eligible": eligible,
            "native_state": item.get("native_state") if isinstance(item, dict) else None,
        }
        if not eligible:
            blockers.append(prerequisite)
    return {
        "task_id": task_id,
        "graph_digest": frozen["graph_digest"],
        "prerequisites": list(prerequisites),
        "blockers": blockers,
        "eligible": not blockers,
        "observations": observations,
        "note": "native scheduling/closed state is not evidence eligibility",
    }
