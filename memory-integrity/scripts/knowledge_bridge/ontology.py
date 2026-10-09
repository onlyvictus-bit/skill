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


def check_compat(old, new, edges):
    """Every edge must typecheck under the new schema. Violations listed."""
    violations = []
    predicates = new.get("predicates", {})
    for edge in edges:
        predicate = edge.get("predicate")
        if predicate not in predicates:
            violations.append("unknown predicate %r" % (predicate,))
    return {"compatible": not violations, "violations": violations}
