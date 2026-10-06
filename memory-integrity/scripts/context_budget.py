#!/usr/bin/env python3
"""Fail-closed token accounting for bounded model context.

`tiktoken` is optional at package level but mandatory for token operations.
Never guess an encoding for an unknown model. Context limits are supplied by
configuration/provider metadata; the tokenizer does not define them.
"""

import argparse
import json
import sys

try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None


def _require_tiktoken():
    if tiktoken is None:
        raise RuntimeError(
            "tiktoken is not installed; exact token accounting is unavailable. "
            "Install tiktoken in the execution environment or use byte-level source coverage only."
        )
    return tiktoken


def resolve_encoding(model=None, explicit_encoding=None):
    tk = _require_tiktoken()
    if explicit_encoding:
        return tk.get_encoding(explicit_encoding)
    if not model:
        raise ValueError("provide model or explicit_encoding")
    try:
        return tk.encoding_for_model(model)
    except KeyError as exc:
        raise KeyError(
            "model %r is not recognized by tiktoken; provide an explicit encoding instead of guessing" % model
        ) from exc


def count_tokens(text, encoding):
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return len(encoding.encode(text))


def calculate_input_budget(context_limit, reserved_output_tokens, fixed_overhead_tokens=0, safety_margin_tokens=0):
    vals = {
        "context_limit": context_limit,
        "reserved_output_tokens": reserved_output_tokens,
        "fixed_overhead_tokens": fixed_overhead_tokens,
        "safety_margin_tokens": safety_margin_tokens,
    }
    for name, value in vals.items():
        if not isinstance(value, int) or value < 0:
            raise ValueError("%s must be a non-negative integer" % name)
    if context_limit <= 0:
        raise ValueError("context_limit must be > 0")
    budget = context_limit - reserved_output_tokens - fixed_overhead_tokens - safety_margin_tokens
    if budget <= 0:
        raise ValueError("reserved output/overhead leaves no positive input budget")
    return budget


def fit_candidates(candidates, budget, encoding):
    if not isinstance(budget, int) or budget < 0:
        raise ValueError("budget must be a non-negative integer")
    normalized = []
    for item in candidates:
        if not isinstance(item, dict) or "id" not in item or "text" not in item:
            raise ValueError("each candidate needs id and text")
        priority = item.get("priority", 0)
        if not isinstance(priority, (int, float)):
            raise ValueError("candidate priority must be numeric")
        tokens = count_tokens(item["text"], encoding)
        row = dict(item)
        row["token_count"] = tokens
        normalized.append(row)

    # Deterministic ordering: highest priority first, then stable string id.
    normalized.sort(key=lambda x: (-x.get("priority", 0), str(x["id"])))
    selected = []
    skipped = []
    used = 0
    for item in normalized:
        if used + item["token_count"] <= budget:
            selected.append(item)
            used += item["token_count"]
        else:
            skipped.append(item)
    return {
        "budget_tokens": budget,
        "used_tokens": used,
        "remaining_tokens": budget - used,
        "selected": selected,
        "skipped": skipped,
        "encoding": getattr(encoding, "name", None),
        "tiktoken_version": getattr(tiktoken, "__version__", None) if tiktoken is not None else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p_count = sub.add_parser("count")
    p_count.add_argument("text")
    p_count.add_argument("--model")
    p_count.add_argument("--encoding")

    p_budget = sub.add_parser("budget")
    p_budget.add_argument("--context-limit", type=int, required=True)
    p_budget.add_argument("--reserved-output", type=int, required=True)
    p_budget.add_argument("--fixed-overhead", type=int, default=0)
    p_budget.add_argument("--safety-margin", type=int, default=0)

    args = ap.parse_args()
    try:
        if args.command == "count":
            enc = resolve_encoding(args.model, args.encoding)
            print(json.dumps({"tokens": count_tokens(args.text, enc), "encoding": getattr(enc, "name", None)}, indent=2))
            return 0
        print(calculate_input_budget(args.context_limit, args.reserved_output, args.fixed_overhead, args.safety_margin))
        return 0
    except Exception as exc:
        print("CONTEXT BUDGET: ERROR - %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
