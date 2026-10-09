#!/usr/bin/env python3
"""Phase 5: bounded community query + iterative deepening (DRIFT flavor).

Disabled by default: enable() with a written approval returns a handle;
without it every operation refuses. Budgets (hops, nodes, steps, depth)
are mandatory; stop reasons are explicit. Private nodes are barriers, never
leaked. Communities are deterministic connected components — an honest
structural grouping, not a learned partition. Citations name traversed
nodes. Standard library only.
"""


import hashlib
import hmac
import json
import os


_PROCESS_KEY = os.urandom(32)
_ISSUED = {}
_ISSUE_COUNTER = [0]


class GraphragError(ValueError):
    pass


def _handle_ok(handle):
    if not isinstance(handle, dict) or handle.get("enabled") is not True:
        return False
    token = handle.get("token")
    return isinstance(token, str) and _ISSUED.get(token) == (
        handle.get("approver"), handle.get("scope"), handle.get("graph_sha256"))


def enable(approval):
    # The key is supplied by a trusted deployment, not a caller's review note.
    key = os.environ.get('GRAPHRAG_APPROVAL_KEY', '')
    if not isinstance(approval, dict) or not key:
        raise GraphragError('E_GRAPHRAG_APPROVAL: trusted signed approval required')
    approver, scope, graph_sha = (approval.get('approver'), approval.get('scope'),
                                   approval.get('graph_sha256'))
    signature = approval.get('signature')
    if not all(isinstance(v, str) and v for v in (approver, scope, graph_sha, signature)):
        raise GraphragError('E_GRAPHRAG_APPROVAL: incomplete signed approval')
    signed = ('graphrag:' + approver + ':' + scope + ':' + graph_sha).encode()
    expected = hmac.new(key.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise GraphragError('E_GRAPHRAG_APPROVAL: invalid signature')
    _ISSUE_COUNTER[0] += 1
    token = hashlib.sha256(_PROCESS_KEY + approval["approver"].encode()
                           + approval["scope"].encode()
                           + str(_ISSUE_COUNTER[0]).encode()).hexdigest()
    _ISSUED[token] = (approver, scope, graph_sha)
    return {"enabled": True, "token": token, "approver": approver,
            "scope": scope, "graph_sha256": graph_sha}


def _neighbors(graph, node, hop=1):
    out = set()
    frontier = {node}
    seen = {node}
    for _ in range(hop):
        nxt = set()
        for edge in graph.get("edges", []):
            if edge.get("subject") in frontier and edge.get("object") not in seen:
                nxt.add(edge["object"])
            if edge.get("object") in frontier and edge.get("subject") not in seen:
                nxt.add(edge["subject"])
        seen |= nxt
        frontier = nxt
    return seen - {node}


def communities(graph):
    """Deterministic connected components over undirected edges."""
    parent = {}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for node in graph.get("nodes", []):
        parent.setdefault(node.get("id"), node.get("id"))
    for edge in graph.get("edges", []):
        first, second = edge.get("subject"), edge.get("object")
        if first in parent and second in parent:
            first, second = find(first), find(second)
            parent[first] = second
    groups = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)
    return [sorted(members) for members in sorted(groups.values())]


def _graph_authorized(graph, handle):
    if not _handle_ok(handle) or not isinstance(graph, dict):
        return False
    project_id = graph.get('project_id')
    if not isinstance(project_id, str) or not project_id or handle.get('scope') != project_id:
        return False
    digest = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return hmac.compare_digest(digest, handle.get('graph_sha256', ''))


def query(graph, start, max_hops=2, max_nodes=100, handle=None):
    """Breadth-first community query honoring budgets and private barriers."""
    if not _graph_authorized(graph, handle):
        raise GraphragError('E_GRAPHRAG_DISABLED: verified graph-bound approval required')
    for name, value in (("max_hops", max_hops), ("max_nodes", max_nodes)):
        if not isinstance(value, int) or value <= 0:
            raise GraphragError("E_GRAPHRAG_BUDGET: %s must be a positive int" % (name,))
    private = {n.get("id") for n in graph.get("nodes", []) if n.get("private")}
    visited, frontier, citations = [], {start}, []
    depth = {start: 0}
    while frontier and len(visited) < max_nodes:
        node = sorted(frontier)[0]
        frontier.discard(node)
        if node in visited or node in private:
            continue
        visited.append(node)
        citations.append(node)
        if len(visited) >= max_nodes:
            break
        if depth[node] >= max_hops:
            continue
        for peer in sorted(_neighbors(graph, node, 1)):
            if peer not in visited and peer not in private and len(visited) + len(frontier) < max_nodes:
                depth.setdefault(peer, depth[node] + 1)
                frontier.add(peer)
    return {"visited": visited, "citations": citations,
            "budgets": {"max_hops": max_hops, "max_nodes": max_nodes}}


def drift(graph, start, max_depth=3, max_steps=50, handle=None):
    """Bounded iterative deepening. Stops with an explicit reason."""
    if not _graph_authorized(graph, handle):
        raise GraphragError('E_GRAPHRAG_DISABLED: verified graph-bound approval required')
    for name, value in (("max_depth", max_depth), ("max_steps", max_steps)):
        if not isinstance(value, int) or value <= 0:
            raise GraphragError("E_GRAPHRAG_BUDGET: %s must be a positive int" % (name,))
    private = {n.get("id") for n in graph.get("nodes", []) if n.get("private")}
    visited, depth_seen, steps = [], {start: 0}, 0
    stack = [start]
    while stack and steps < max_steps:
        node = stack.pop()
        steps += 1
        if node in visited or node in private:
            continue
        visited.append(node)
        if depth_seen[node] >= max_depth:
            continue
        for peer in sorted(_neighbors(graph, node, 1)):
            if peer not in visited and peer not in private:
                depth_seen.setdefault(peer, depth_seen[node] + 1)
                stack.append(peer)
    if steps >= max_steps:
        reason = "budget-exhausted"
    elif any(depth_seen.get(n, 0) >= max_depth for n in visited):
        reason = "depth-cap"
    else:
        reason = "no-new-evidence"
    return {"visited": visited, "steps": steps, "stop_reason": reason}
