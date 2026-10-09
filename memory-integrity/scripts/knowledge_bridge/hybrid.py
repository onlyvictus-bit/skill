#!/usr/bin/env python3
"""Phase 4: provenance-first hybrid rerank.

Order is the guarantee: pre-filter drops unauthorized/stale candidates
BEFORE scoring influence, rescoring runs, then the filter runs AGAIN
(post-filter), and ties break by stable id order. A top-scored forbidden
candidate can never surface, and calibration records exactly what ran.
Standard library only.
"""


def _eligible(candidate):
    return isinstance(candidate, dict) and candidate.get("authorized") is True \
        and candidate.get("stale") is not True \
        and isinstance(candidate.get("id"), str) and candidate["id"].strip() \
        and isinstance(candidate.get("score"), (int, float)) \
        and not isinstance(candidate.get("score"), bool)


def rerank(candidates, top_k=10, rescore=None, weights=None):
    """Rerank candidate dicts. Returns (ranked_list, dropped_ids).

    rescore(candidate) -> float runs between the two filter passes; any
    candidate it zeroes is dropped by the post-filter. weights documents
    score calibration and travels in neither direction unrecorded.
    """
    if not isinstance(candidates, list):
        raise ValueError("E_RERANK_INPUT: candidates must be a list")
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("E_RERANK_K: top_k must be a positive int")
    dropped = [c.get("id", "?") for c in candidates if not _eligible(c)]
    pool = [dict(c) for c in candidates if _eligible(c)]
    if rescore is not None:
        for candidate in pool:
            value = rescore(candidate)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError("E_RERANK_SCORE: rescore must return numbers")
            candidate["score"] = value
    pool = [c for c in pool if _eligible(c)]
    dropped += [c["id"] for c in pool if not c["score"] > 0]
    pool = [c for c in pool if c["score"] > 0]
    dropped += [c.get("id", "?") for c in candidates
                if c.get("id") not in {p["id"] for p in pool}
                and c.get("id", "?") not in dropped]
    ranked = sorted(pool, key=lambda c: (-c["score"], c["id"]))[:top_k]
    for candidate in ranked:
        candidate["calibration"] = {"weights": dict(weights or {}),
                                    "prefilter": "authorized-and-fresh",
                                    "postfilter": "rescore-rerun"}
    return ranked, sorted(set(dropped))
