#!/usr/bin/env python3
"""H2a: derived compact work/evidence cards over existing Fable+v2 records.

Read-only display layer. Never edits engines, ledgers, sources, or Fable
state. Never invents evidence: every card resolves to exact basis digests,
proof locators, and an explicit freshness/conflict note. Standard library only.

Card dimensions stay separate (no single done boolean):
  approval | execution | evidence | acceptance | projection_freshness
"""
import hashlib
import json

CARD_REQUIRED = ("work_id", "kind", "need", "basis", "state", "proof",
                 "gap", "next", "recheck", "freshness")
STATE_KEYS = ("approval", "execution", "evidence", "acceptance",
              "projection_freshness")
BASIS_KEYS = ("requirement_ref", "source_digest", "manifest_digest",
              "worktree_id", "check_digest")


class CardError(ValueError):
    pass


def card_id(*parts):
    """Deterministic operation/card identity from exact basis parts."""
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8") + b"\x00")
    return h.hexdigest()[:16]


def validate_gap(gap):
    """A gap is actionable only with exact references. Raise CardError."""
    if not isinstance(gap, dict):
        raise CardError("E_GAP_TYPE: gap must be an object")
    for key in ("id", "need", "basis", "state", "proof_ref", "gap",
                "next", "recheck", "blocking"):
        if key not in gap:
            raise CardError("E_GAP_REQUIRED: missing %s in %r"
                            % (key, gap.get("id", "?")))
    if not isinstance(gap["basis"], dict):
        raise CardError("E_GAP_BASIS: basis must be an object")
    missing = sorted(set(BASIS_KEYS) - set(gap["basis"]))
    if missing:
        raise CardError("E_GAP_BASIS: %s missing basis fields %s"
                        % (gap["id"], ",".join(missing)))
    if any(not isinstance(gap["basis"][key], str) or not gap["basis"][key].strip()
           for key in BASIS_KEYS):
        raise CardError("E_GAP_BASIS: empty or non-text basis")
    if not isinstance(gap["state"], dict) or set(gap["state"]) != set(STATE_KEYS):
        raise CardError("E_GAP_STATE: all five dimensions required")
    if any(not isinstance(v, str) or not v.strip() for v in gap["state"].values()):
        raise CardError("E_GAP_STATE: empty dimension")
    for key in ("id", "proof_ref", "gap", "next"):
        if not isinstance(gap[key], str) or not gap[key].strip():
            raise CardError("E_GAP_VALUE: %s must be nonempty text" % key)
    if not isinstance(gap["blocking"], bool):
        raise CardError("E_GAP_BLOCKING: bool required")
    if not isinstance(gap["recheck"], list) or not gap["recheck"] or any(
            not isinstance(v, str) or not v.strip() for v in gap["recheck"]):
        raise CardError("E_GAP_RECHECK: nonempty text list required")
    unknown_state = sorted(set(gap["state"]) - set(STATE_KEYS))
    if unknown_state:
        raise CardError("E_GAP_STATE: %s unknown dimensions %s"
                        % (gap["id"], ",".join(unknown_state)))
    if not str(gap["need"]).strip():
        raise CardError("E_GAP_NEED: %s has empty need" % (gap["id"],))
    return gap


def derive_cards(gaps, generated_from, limit=50, token=0):
    """Build a paginated derived view. Never claims completeness of a page.

    gaps: list of gap dicts (validated). Blocking gaps sort first and are
    always counted in total/remaining even when a page omits them.
    generated_from: {manifest_tree_digests, receipt_ref, at} freshness basis.
    Returns dict with total/shown/remaining/next_token/cards/mandatory_blockers.
    """
    if not isinstance(gaps, list):
        raise CardError("E_INPUT_TYPE: gaps must be a list")
    if not isinstance(generated_from, dict) or not generated_from:
        raise CardError("E_INPUT_FRESHNESS: generation basis required")
    if not isinstance(limit, int) or limit <= 0:
        raise CardError("E_INPUT_LIMIT: limit must be a positive int")
    if not isinstance(token, int) or token < 0:
        raise CardError("E_INPUT_TOKEN: token must be a non-negative int")
    valid = [validate_gap(g) for g in gaps]
    if len({g['id'] for g in valid}) != len(valid):
        raise CardError("E_INPUT_DUPLICATE: duplicate work IDs")
    blocking = [g["id"] for g in valid if g["blocking"]]
    ordered = sorted(valid, key=lambda g: (not g["blocking"], g["id"]))
    total = len(ordered)
    page = ordered[token:token + limit]
    cards = []
    for g in page:
        cards.append({
            "work_id": g["id"],
            "kind": g.get("kind", "repair"),
            "need": g["need"],
            "basis": dict(g["basis"]),
            "state": dict(g["state"]),
            "proof": g["proof_ref"],
            "gap": g["gap"],
            "next": g["next"],
            "recheck": list(g["recheck"]),
            "freshness": {
                "generated_from": dict(generated_from),
                "card_digest": card_id(json.dumps(g, sort_keys=True, ensure_ascii=False),
                                       json.dumps(generated_from, sort_keys=True, ensure_ascii=False)),
            },
        })
    remaining = max(0, total - (token + len(page)))
    return {
        "total": total,
        "shown": len(page),
        "remaining": remaining,
        "next_token": token + len(page) if remaining > 0 else None,
        "mandatory_blockers": sorted(blocking),
        "cards": cards,
    }


def render_text(report):
    """Short human view. Always prints totals; never presents a page as whole."""
    lines = ["CARDS: %d total, %d shown, %d remaining"
             % (report["total"], report["shown"], report["remaining"])]
    if report["mandatory_blockers"]:
        lines.append("BLOCKERS: %s" % (", ".join(report["mandatory_blockers"]),))
    for c in report["cards"]:
        lines.append("- %s | %s | next: %s"
                     % (c["work_id"], c["need"][:80], c["next"][:80]))
    if report["next_token"] is not None:
        lines.append("CONTINUE token=%s (more items remain)" % (report["next_token"],))
    return "\n".join(lines)

