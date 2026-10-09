#!/usr/bin/env python3
"""Phase 5: read-only SPARQL-subset projection over in-memory graphs.

Supports SELECT ?vars WHERE { triple patterns } with . separators, LIMIT,
and a wallTimeout. Triple terms are IRIs-as-strings or ?variables; anything
else (OPTIONAL, UNION, FILTER, property paths, updates, LOAD) is refused.
Nodes flagged hidden/private are excluded unless include_hidden carries a
written justification. Injection is structurally impossible: the grammar has
no escape into evaluation. Standard library only.
"""
import re
import time

_IRI = r"[A-Za-z][A-Za-z0-9_.:/-]*"
_VAR = r"\?[A-Za-z][A-Za-z0-9_]*"
_TERM = r"(?:%s|%s)" % (_VAR, _IRI)
_PATTERN = re.compile(r"\s*(%s)\s+(%s)\s+(%s)\s*\.?" % (_TERM, _TERM, _TERM))


class SparqlError(ValueError):
    pass


def _parse_select(query):
    head = re.fullmatch(r"\s*SELECT\s+((?:\?\w+\s*)+)WHERE\s*\{(.*)\}\s*",
                        query, re.DOTALL | re.IGNORECASE)
    if not head:
        raise SparqlError("E_SPARQL_GRAMMAR: only SELECT ?v WHERE { patterns }")
    variables = re.findall(r"\?(\w+)", head.group(1))
    if not variables or len(set(variables)) != len(variables):
        raise SparqlError("E_SPARQL_VARS: distinct variables required")
    body = head.group(2).strip()
    if not body:
        raise SparqlError("E_SPARQL_EMPTY: empty pattern block")
    patterns = []
    for chunk in body.split("."):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = _PATTERN.fullmatch(chunk)
        if match is None:
            raise SparqlError("E_SPARQL_PATTERN: unsupported pattern %r" % (chunk[:60],))
        patterns.append(tuple(match.groups()))
    if not patterns:
        raise SparqlError("E_SPARQL_EMPTY: no triple patterns")
    return variables, patterns


def _triples(graph):
    for edge in graph.get("edges", []):
        yield (str(edge.get("subject")), str(edge.get("predicate")),
               str(edge.get("object")))


def _hidden_ids(graph):
    return {n.get("id") for n in graph.get("nodes", [])
            if isinstance(n, dict) and (n.get("hidden") or n.get("private"))}


def query(graph, query_text, limit=100, timeout=10, include_hidden=None):
    """Run a read-only SELECT. Returns [row-dict]. Refuses everything else."""
    if not isinstance(limit, int) or limit < 0:
        raise SparqlError("E_SPARQL_LIMIT: limit must be a non-negative int")
    if include_hidden is not None and not (
            isinstance(include_hidden, str) and include_hidden.strip()):
        raise SparqlError("E_SPARQL_HIDDEN: including hidden nodes needs a written reason")
    if not isinstance(graph, dict):
        raise SparqlError("E_SPARQL_GRAPH: graph must be an object")
    variables, patterns = _parse_select(query_text)
    if limit == 0:
        return []
    hidden = set() if include_hidden else _hidden_ids(graph)
    deadline = time.perf_counter() + timeout
    rows, seen = [], set()
    triples = list(_triples(graph))
    partials = [{}]
    for pattern in patterns:
        stepped = []
        for bindings in partials:
            for triple in triples:
                if time.perf_counter() > deadline:
                    raise SparqlError("E_SPARQL_TIMEOUT: query exceeded budget")
                merged = dict(bindings)
                ok = True
                for term, value in zip(pattern, triple):
                    if term.startswith("?"):
                        name = term[1:]
                        if name in merged and merged[name] != value:
                            ok = False
                            break
                        merged[name] = value
                    elif term != value:
                        ok = False
                        break
                if ok:
                    stepped.append(merged)
        partials = stepped
        if not partials:
            break
    for bindings in partials:
        if any(v in hidden for v in bindings.values()):
            continue
        row = tuple((var, bindings.get(var)) for var in variables)
        if row not in seen:
            seen.add(row)
            rows.append({var: bindings.get(var) for var in variables})
            if len(rows) >= limit:
                break
    return rows
