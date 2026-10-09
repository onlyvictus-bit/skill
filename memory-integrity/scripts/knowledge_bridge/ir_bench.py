#!/usr/bin/env python3
"""Phase 4: honest IR measurement. Metrics are hand-checkable; losing
variants stay in the report with a named winner that may be the baseline.
No superiority claim without a measured win. Standard library only.
"""
import math
import time


def _unique(ranked):
    """Duplicate result IDs count once; ranking spam never inflates recall."""
    seen, out = set(), []
    for doc in ranked:
        if doc not in seen:
            seen.add(doc)
            out.append(doc)
    return out


def recall_at_k(ranked, relevant, k):
    relevant = set(relevant)
    if not relevant or k <= 0:
        return 0.0
    ranked = _unique(ranked)
    return len([d for d in ranked[:k] if d in relevant]) / len(relevant)


def mrr(ranked, relevant):
    relevant = set(relevant)
    for rank, doc in enumerate(_unique(ranked), start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(ranked, relevant, k):
    relevant = set(relevant)
    if not relevant or k <= 0:
        return 0.0
    gains = [1.0 if doc in relevant else 0.0 for doc in _unique(ranked)[:k]]
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return (dcg / ideal) if ideal else 0.0


def run_variant(name, rank_fn, queries, k=5):
    """rank_fn(query_id) -> ranked id list. Returns metrics + latency."""
    started = time.perf_counter()
    recalls, rrs, ndcgs, missing = [], [], [], 0
    for qid, relevant in queries.items():
        ranked = list(rank_fn(qid)) if callable(rank_fn) else list(rank_fn)
        recalls.append(recall_at_k(ranked, relevant, k))
        rrs.append(mrr(ranked, relevant))
        ndcgs.append(ndcg_at_k(ranked, relevant, k))
        missing += len([d for d in relevant if d not in ranked[:k]])
    count = max(len(queries), 1)
    return {"variant": name, "k": k,
            "recall@%d" % (k,): sum(recalls) / count,
            "mrr": sum(rrs) / count, "ndcg": sum(ndcgs) / count,
            "missing_required": missing,
            "seconds": time.perf_counter() - started}


def compare(rank_fns, queries, k=5):
    """Rank every variant, name the winner, keep losers visible."""
    variants = {name: run_variant(name, fn, queries, k)
                for name, fn in rank_fns.items()}
    winner = max(variants, key=lambda n: (variants[n]["recall@%d" % (k,)],
                                          variants[n]["mrr"],
                                          variants[n]["ndcg"], n))
    return {"variants": variants, "winner": winner, "k": k,
            "note": "winner is measured on this fixture, not a general claim"}
