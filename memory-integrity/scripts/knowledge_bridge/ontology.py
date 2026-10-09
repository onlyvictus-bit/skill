#!/usr/bin/env python3
"""Phase 5: versioned ontology schema beside the fixed predicate matrix.

Versions accumulate; migrate() diffs schemas and checks a set of edges for
backward compatibility, listing violations instead of silently accepting.
Type violations are evidence, never auto-repaired. Standard library only.
"""
SCHEMAS = {
    1: {"predicates": {"DEPENDS_ON": (["Component", "Symbol"], ["Component", "Symbol"]),
                       "REFERENCES": (["*"], ["*"])},
        "types": ["Component", "Symbol"]},
    2: {"predicates": {"DEPENDS_ON": (["Component", "Symbol"], ["Component", "Symbol"]),
                       "REFERENCES": (["*"], ["*"]),
                       "CONTRADICTS": (["Assertion"], ["Assertion"])},
        "types": ["Component", "Symbol", "Assertion"]},
}


class OntologyError(ValueError):
    pass


def schema(version):
    if version not in SCHEMAS:
        raise OntologyError("E_ONTOLOGY_VERSION: unknown schema %r" % (version,))
    import copy
    return {"version": version, "predicates": dict(SCHEMAS[version]["predicates"]),
            "types": list(SCHEMAS[version]["types"])}


def migrate(old, version):
    """Return the target schema plus a diff. Never mutates inputs."""
    new = schema(version)
    old_preds = set(old.get("predicates", {}))
    new_preds = set(new["predicates"])
    return {"schema": new,
            "diff": {"added_predicates": sorted(new_preds - old_preds),
                     "removed_predicates": sorted(old_preds - new_preds),
                     "from_version": old.get("version"),
                     "to_version": version}}


def check_compat(old, new, edges, nodes=None):
    """Every edge must typecheck under the new schema. Violations listed.

    With nodes [{id, type}], subject/object endpoint types are validated
    against the predicate domain/range ("*" matches anything). Without
    nodes, only predicate names are checked (weaker; documented).
    """
    violations = []
    predicates = new.get("predicates", {})
    types = {n.get("id"): n.get("type") for n in (nodes or []) if isinstance(n, dict)}
    for edge in edges:
        predicate = edge.get("predicate")
        if predicate not in predicates:
            violations.append("unknown predicate %r" % (predicate,))
            continue
        if nodes is None:
            continue
        domain, delivery = predicates[predicate]
        for role, allowed in (("subject", domain), ("object", delivery)):
            actual = types.get(edge.get(role))
            if actual is None:
                violations.append("untyped endpoint %s=%r" % (role, edge.get(role)))
            elif "*" not in allowed and actual not in allowed:
                violations.append("type violation: %s %s is %s, needs one of %s"
                                  % (role, edge.get(role), actual, sorted(allowed)))
    return {"compatible": not violations, "violations": violations}
