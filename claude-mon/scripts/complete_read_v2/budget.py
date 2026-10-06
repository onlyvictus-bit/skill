#!/usr/bin/env python3
"""M4a: model profiles, complete-request measurement, batch planning.

Every number here is either measured with a stated method or refused.
Unknown limits, unknown encodings, and MB-to-token inference are errors,
not estimates. Output reserve is planned with the same rigor as input:
a request that fits on input but cannot return its required rows is split,
never truncated.
"""
from . import contracts  # noqa: F401  (schema enums live here; kept import-visible)


class BudgetError(ValueError):
    pass


PROFILE_KEYS = {"schema_version", "provider", "model", "encoding", "encoding_version",
                "context_limit", "output_limit", "counting_method", "endpoint", "purpose",
                "max_spend"}
PROFILE_REQUIRED_KEYS = {"schema_version", "provider", "model", "encoding", "encoding_version",
                         "context_limit", "output_limit", "counting_method"}


def validate_profile(profile):
    """A profile with unknown limits or encoding is unusable, not guessable."""
    if not isinstance(profile, dict):
        raise BudgetError("E_PROFILE_TYPE: profile must be an object")
    unknown = sorted(set(profile) - PROFILE_KEYS)
    if unknown:
        raise BudgetError("E_SCHEMA_FIELD: profile unsupported field(s): %s" % (", ".join(unknown)))
    missing = sorted(PROFILE_REQUIRED_KEYS - set(profile))
    if missing:
        raise BudgetError("E_SCHEMA_REQUIRED: profile missing: %s" % (", ".join(missing)))
    if profile.get("schema_version") != 2:
        raise BudgetError("E_SCHEMA_VERSION: profile schema must be 2")
    for key in ("provider", "model", "encoding", "counting_method"):
        value = profile.get(key)
        if not isinstance(value, str) or not value.strip():
            raise BudgetError("E_PROFILE_VALUE: profile.%s must be non-empty" % (key,))
    for key in ("context_limit", "output_limit"):
        value = profile.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise BudgetError("E_PROFILE_LIMIT: profile.%s must be a positive int" % (key,))
    value = profile.get("max_spend", 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise BudgetError("E_PROFILE_LIMIT: profile.max_spend must be a non-negative number")
    return profile


def _tiktoken_counter(encoding):
    try:
        import tiktoken
    except ImportError:
        raise BudgetError("E_TOKENIZER_ABSENT: tiktoken not installed; supply counter= explicitly")
    try:
        enc = tiktoken.get_encoding(encoding)
    except Exception as exc:
        raise BudgetError("E_TOKENIZER_ENCODING: unknown encoding %r: %s" % (encoding, exc))
    return enc.encode_ordinary


def count_tokens(text, encoding, counter=None):
    """Count with tiktoken, or with an explicitly injected counter (tests/pilots).

    The method used is always returned alongside the count so no number ever
    travels without its provenance.
    """
    if not isinstance(text, str):
        raise BudgetError("E_COUNT_TYPE: text must be str")
    if counter is None:
        encode = _tiktoken_counter(encoding)
        method = "tiktoken:%s" % (encoding,)
    else:
        encode = counter
        method = "injected-counter"
    try:
        pieces = encode(text)
    except Exception as exc:
        raise BudgetError("E_COUNT_FAILED: %s" % (exc,))
    return len(list(pieces)), method


def _require_nonneg_int(value, where):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BudgetError("E_BUDGET_VALUE: %s must be a non-negative int" % (where,))
    return value


def _require_pos_int(value, where):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BudgetError("E_BUDGET_VALUE: %s must be a positive int" % (where,))
    return value


def measure_request(profile, sections, counter=None):
    """Measure every named section plus framing. sections: {name: str}."""
    validate_profile(profile)
    if not isinstance(sections, dict) or not sections:
        raise BudgetError("E_REQUEST_EMPTY: request needs at least one section")
    breakdown, total, methods = {}, 0, set()
    for name in sorted(sections):
        text = sections[name]
        if not isinstance(text, str):
            raise BudgetError("E_REQUEST_TYPE: section %r must be str" % (name,))
        count, method = count_tokens(text, profile["encoding"], counter)
        breakdown[name] = count
        methods.add(method)
        total += count
    return {"input_tokens": total, "breakdown": breakdown,
            "methods": sorted(methods), "encoding": profile["encoding"],
            "scope": "local-text-excluding-provider-framing"}


def plan_batches(profile, units, per_unit_output, reasoning_reserve=0, safety_reserve=0):
    """Pack pre-measured units into request batches honoring input AND output.

    units: [{id, input_tokens}] measured by the caller with measure_request/
    count_tokens (the method travels with those numbers). per_unit_output:
    reserved output tokens per unit result row. Returns batches of unit-id
    lists sharing one parent mapping; raises instead of dropping anything.
    """
    validate_profile(profile)
    reasoning_reserve = _require_nonneg_int(reasoning_reserve, "reasoning_reserve")
    safety_reserve = _require_nonneg_int(safety_reserve, "safety_reserve")
    per_unit_output = _require_pos_int(per_unit_output, "per_unit_output")
    limit, out_limit = profile["context_limit"], profile["output_limit"]
    usable_in = limit - safety_reserve
    if usable_in <= 0:
        raise BudgetError("E_BUDGET_SAFETY: safety reserve covers the context")
    seen = set()
    for unit in units:
        if not isinstance(unit, dict):
            raise BudgetError("E_BATCH_RECORD: unit record must be an object")
        ident = unit.get("id")
        if not isinstance(ident, str) or not ident.strip():
            raise BudgetError("E_BATCH_RECORD: unit id must be non-empty")
        if ident in seen:
            raise BudgetError("E_BATCH_DUPLICATE: duplicate unit id %r" % (ident,))
        seen.add(ident)
        _require_nonneg_int(unit.get("input_tokens"), "unit %s input_tokens" % (ident,))
    batches, current, in_sum, out_sum = [], [], 0, 0
    for unit in units:
        need_in = unit["input_tokens"]
        if need_in > usable_in:
            raise BudgetError("E_BUDGET_UNIT_INPUT: unit %s exceeds usable input" % (unit["id"],))
        if per_unit_output + reasoning_reserve > out_limit:
            raise BudgetError("E_BUDGET_UNIT_OUTPUT: unit %s output cannot fit" % (unit["id"],))
        overflow_in = in_sum + need_in > usable_in
        overflow_out = out_sum + per_unit_output + reasoning_reserve > out_limit
        overflow_total = (in_sum + need_in + out_sum + per_unit_output
                          + reasoning_reserve + safety_reserve > limit)
        if current and (overflow_in or overflow_out or overflow_total):
            batches.append(current)
            current, in_sum, out_sum = [], 0, 0
        current.append(unit["id"])
        in_sum += need_in
        out_sum += per_unit_output
    if current:
        batches.append(current)
    by_id = {u["id"]: u["input_tokens"] for u in units}
    for batch in batches:
        batch_in = sum(by_id[i] for i in batch)
        batch_out = per_unit_output * len(batch)
        if batch_in > usable_in:
            raise BudgetError("E_BUDGET_INPUT: batch input %d exceeds usable %d"
                              % (batch_in, usable_in))
        if batch_out + reasoning_reserve > out_limit:
            raise BudgetError("E_BUDGET_OUTPUT: batch output exceeds limit")
        if batch_in + batch_out + reasoning_reserve + safety_reserve > limit:
            raise BudgetError("E_BUDGET_TOTAL: batch needs %d of %d context tokens"
                              % (batch_in + batch_out + reasoning_reserve + safety_reserve,
                                 limit))
    assigned = sorted(i for b in batches for i in b)
    expected = sorted(u["id"] for u in units)
    if assigned != expected:
        raise BudgetError("E_BATCH_LOSS: planner dropped units")
    return {"batches": batches, "input_budget": usable_in,
            "output_limit": profile["output_limit"], "inputs": "caller-measured"}


def qualify_for_live(profile, methods):
    """A measurement qualifies a live request only with provider-grade counting.

    Injected/test counters stay valid for offline tests but can never support
    a live gate. Returns (ok_bool, reasons list).
    """
    reasons = []
    try:
        validate_profile(profile)
    except BudgetError as exc:
        return False, ["profile invalid: %s" % (exc,)]
    for method in methods or []:
        if not method.startswith("tiktoken:"):
            reasons.append("non-qualified counting method: %s" % (method,))
    try:
        _tiktoken_counter(profile["encoding"])
    except BudgetError as exc:
        reasons.append(str(exc))
    if profile.get("counting_method") == "injected-counter":
        reasons.append("profile declares synthetic counting")
    return (not reasons), reasons
