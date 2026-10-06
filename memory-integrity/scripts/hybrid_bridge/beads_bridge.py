#!/usr/bin/env python3
"""H2b/H3: optional Beads coordination bridge — OFF/SHADOW/ACTIVE.

OFF (default): no Beads import, call, or write. Core-only behavior.
SHADOW: dry-run projection from derived cards. Writes nothing, spawns
  nothing, needs no bd binary. Output is a plan, not coordination state.
ACTIVE: refused unless ALL hold: pinned bd binary present with matching
  version+checksum, disposable database path outside synced trees, explicit
  per-run authorization record. Otherwise BLOCKED with exact reason.

No atomic transaction across SQLite and Dolt is assumed. Single writer per
workspace. Deterministic operation IDs; read-back verification; explicit
UNKNOWN on uncertain synchronization; reconcile before retry. Task text is
untrusted data, never executed. A closed/projected task never creates or
upgrades an ACCEPTED receipt or READY_FOR_DECLARED_TASK.
Standard library only.
"""
import hashlib
import json
import shutil

MODES = ("OFF", "SHADOW", "ACTIVE")
PINNED_BD_VERSION = None  # set only after a tested release is qualified
PINNED_BD_SHA256 = None


class BridgeError(ValueError):
    pass


def operation_id(workspace, work_id, card_digest, bridge_version="h3-1"):
    """Deterministic id for one projected operation. Same input → same id."""
    h = hashlib.sha256()
    for part in (workspace, work_id, card_digest, bridge_version):
        h.update(str(part).encode("utf-8") + b"\x00")
    return "op-" + h.hexdigest()[:16]


def project_shadow(cards_report, workspace, evidence_digest):
    """SHADOW: plan projections from a cards report. Pure function, no I/O."""
    if not isinstance(cards_report, dict) or "cards" not in cards_report:
        raise BridgeError("E_INPUT_CARDS: need a derive_cards report")
    if not str(workspace).strip():
        raise BridgeError("E_INPUT_WORKSPACE: workspace required")
    if not isinstance(evidence_digest, str) or len(evidence_digest) != 64:
        raise BridgeError("E_INPUT_EVIDENCE: SHA256 basis required")
    projections = []
    for card in cards_report["cards"]:
        op = operation_id(workspace, card["work_id"],
                          card["freshness"]["card_digest"], evidence_digest)
        projections.append({
            "op_id": op,
            "workspace": workspace,
            "work_id": card["work_id"],
            "title": card["need"][:120],
            "evidence_digest": evidence_digest,
            "card_digest": card["freshness"]["card_digest"],
            "next": card["next"],
            "mode": "SHADOW",
            "writes": 0,
        })
    return {"mode": "SHADOW", "workspace": workspace,
            "projections": projections,
            "note": "dry-run plan only; no task created, no database touched"}


class MemoryStore:
    """Disposable in-memory claim store (TEST harness stand-in, not a DB).

    Models the single-writer + read-back + UNKNOWN-reconcile contract so the
    coordination logic is tested without creating any database file.
    """

    def __init__(self):
        self._claims = {}
        self._pending = {}

    def create(self, op_id, owner):
        """Idempotent create: same op_id twice → same record, no duplicate."""
        if op_id in self._claims:
            return dict(self._claims[op_id], duplicate_suppressed=True)
        if op_id in self._pending:
            return {"op_id": op_id, "status": "UNKNOWN",
                    "reason": "previous create uncertain; reconcile first"}
        record = {"op_id": op_id, "owner": owner, "status": "open"}
        self._claims[op_id] = record
        read_back = self._claims.get(op_id)
        if read_back != record:
            raise BridgeError("E_READBACK: store read-back mismatch for %s" % (op_id,))
        return dict(record, duplicate_suppressed=False)

    def begin_uncertain(self, op_id):
        """Mark an op whose commit state is unknown (e.g. crash mid-write)."""
        self._pending[op_id] = True

    def reconcile(self, op_id):
        """Resolve UNKNOWN before any retry. Never blindly re-creates."""
        if op_id in self._claims:
            return {"op_id": op_id, "status": "known-open",
                    "action": "resume existing; do not duplicate"}
        if op_id in self._pending:
            return {"op_id": op_id, "status": "UNKNOWN",
                    "action": "verify backend before retry; no blind duplicate"}
        return {"op_id": op_id, "status": "absent",
                "action": "safe to create once"}

    def close(self, op_id):
        """Close is task state only. Caller must still pass v2/Fable gates."""
        record = self._claims.get(op_id)
        if record is None:
            raise BridgeError("E_CLOSE_UNKNOWN: no such op %s" % (op_id,))
        record["status"] = "closed-task-state-only"
        return dict(record)


def gate_active(workspace, bd_path=None, authorization=None):
    """ACTIVE entry gate. Returns BLOCKED dict unless fully qualified."""
    if not str(workspace).strip():
        return {"active": False, "reason": "workspace required"}
    binary = bd_path or shutil.which("bd")
    if not binary:
        return {"active": False,
                "reason": "BLOCKED: no bd executable found; "
                          "SHADOW/OFF only. Installing bd needs separate "
                          "authorization + pinned release + checksum."}
    if PINNED_BD_VERSION is None:
        return {"active": False,
                "reason": "BLOCKED: no pinned bd release qualified "
                          "(found %s); refusing unpinned binary" % (binary,)}
    if not isinstance(authorization, dict) or not authorization.get("approved"):
        return {"active": False,
                "reason": "BLOCKED: ACTIVE needs an explicit per-run "
                          "authorization record"}
    # R2 intentionally ships no native executor. A declaration of a pin is
    # not qualification: binary, checksum, version and disposable DB tests
    # remain a separately approved native pilot. Never claim ACTIVE here.
    return {"active": False,
            "reason": "BLOCKED: native executor/pin/checksum/disposable DB pilot not qualified"}

