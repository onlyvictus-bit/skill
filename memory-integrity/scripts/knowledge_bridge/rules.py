#!/usr/bin/env python3
"""Phase 5: typed read-only rule adapter (Datalog flavor), opt-in capable.

Facts are (predicate, args-tuple). Rules are {head, body} with variables as
UPPERCASE-leading strings. Stratified negation: `("not", subfact)` is allowed
only over EDB (input-fact) predicates, evaluated against the input set.
Forward chaining stops at max_derived facts or fixpoint; cyclic rules
terminate by bound, reported in stop_reason. Every derivation carries
provenance (rule index + grounding). Rules never write the graph and never
promote authority: output is derived evidence only. Standard library only.
"""
MAX_DEFAULT_DERIVED = 10000


class RuleError(ValueError):
    pass


def _is_var(term):
    return isinstance(term, str) and term[:1].isupper()


def _match(pattern, fact, bindings):
    if pattern[0] != fact[0] or len(pattern[1]) != len(fact[1]):
        return None
    bindings = dict(bindings)
    for part, value in zip(pattern[1], fact[1]):
        if _is_var(part):
            if part in bindings and bindings[part] != value:
                return None
            bindings[part] = value
        elif part != value:
            return None
    return bindings


def _ground(head, bindings):
    return (head[0], tuple(bindings.get(a, a) if _is_var(a) else a for a in head[1]))


def forward_chain(facts, rules, max_derived=MAX_DEFAULT_DERIVED):
    """Run rules to fixpoint-or-bound. Returns {derived, derivations, stop_reason}."""
    if not isinstance(max_derived, int) or max_derived <= 0:
        raise RuleError("E_RULE_BOUND: max_derived must be a positive int")
    known = set()
    for fact in facts:
        if not (isinstance(fact, tuple) and len(fact) == 2
                and isinstance(fact[0], str) and isinstance(fact[1], tuple)):
            raise RuleError("E_RULE_FACT: facts must be (predicate, args-tuple)")
        known.add(fact)
    edb_predicates = {f[0] for f in known}
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict) or "head" not in rule or "body" not in rule:
            raise RuleError("E_RULE_SHAPE: rule %d needs head/body" % (idx,))
        for literal in rule["body"]:
            if isinstance(literal, tuple) and literal[0] == "not":
                if literal[1][0] not in edb_predicates:
                    raise RuleError("E_RULE_STRATIFICATION: negation only over input facts")
    derived, derivations = [], []
    changed = True
    while changed:
        changed = False
        for idx, rule in enumerate(rules):
            partial = [{}]
            for literal in rule["body"]:
                negated = isinstance(literal, tuple) and literal[0] == "not"
                pattern = literal[1] if negated else literal
                stepped = []
                for bindings in partial:
                    if negated:
                        if not any(_match(pattern, fact, bindings) is not None
                                   for fact in known):
                            stepped.append(bindings)
                        continue
                    for fact in sorted(known):
                        hit = _match(pattern, fact, bindings)
                        if hit is not None:
                            stepped.append(hit)
                partial = stepped
            for bindings in partial:
                grounded = _ground(rule["head"], bindings)
                if grounded not in known:
                    known.add(grounded)
                    derived.append(grounded)
                    derivations.append({"fact": grounded, "rule": idx,
                                       "bindings": bindings,
                                       "provenance": "rule-%d" % (idx,)})
                    if len(derived) >= max_derived:
                        return {"derived": derived, "derivations": derivations,
                                "stop_reason": "bound termination: max_derived reached"}
                    changed = True
    return {"derived": derived, "derivations": derivations,
            "stop_reason": "fixpoint termination: no new facts"}
