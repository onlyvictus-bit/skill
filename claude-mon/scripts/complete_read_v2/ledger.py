#!/usr/bin/env python3
"""Central, append-only companion audit ledger (schema 4)."""
import hashlib
import json
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone

LEDGER_SCHEMA = "4"
FORWARD = {
    "QUEUED": ("PREPARED", "CANCELLED"), "PREPARED": ("AWAITING_APPROVAL", "CANCELLED"),
    "AWAITING_APPROVAL": ("DISPATCHING", "CANCELLED"),
    "DISPATCHING": ("RESPONSE_SAVED", "DELIVERY_UNKNOWN", "RETRYABLE_ERROR", "CANCELLED"),
    "RESPONSE_SAVED": ("VALIDATED", "INVALID_RESULT", "TRUNCATED", "REFUSED", "CANCELLED"),
    "VALIDATED": ("ACCEPTED", "INVALID_RESULT", "CANCELLED"),
}
TERMINAL = {"ACCEPTED", "REFUSED", "TRUNCATED", "RETRYABLE_ERROR", "INVALID_RESULT", "DELIVERY_UNKNOWN", "CANCELLED", "STALE"}

SCHEMA = """
PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS work_items (id TEXT PRIMARY KEY, task_digest TEXT NOT NULL, source_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'PENDING', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, work_item_id TEXT NOT NULL REFERENCES work_items(id), attempt_no INTEGER NOT NULL, state TEXT NOT NULL, request_digest TEXT, response_digest TEXT, approval_ref TEXT, approval_id TEXT, error TEXT, updated_at TEXT NOT NULL, UNIQUE(work_item_id,attempt_no));
CREATE TABLE IF NOT EXISTS accepted (work_item_id TEXT PRIMARY KEY REFERENCES work_items(id), attempt_id TEXT NOT NULL REFERENCES attempts(id), revoked INTEGER NOT NULL DEFAULT 0, revoke_reason TEXT, accepted_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL, work_item_id TEXT, detail TEXT NOT NULL, actor TEXT NOT NULL, op_id TEXT NOT NULL, object_version INTEGER NOT NULL, identity_json TEXT NOT NULL, evidence_refs_json TEXT NOT NULL, prev_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, attempt_id TEXT NOT NULL REFERENCES attempts(id), request_digest TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, endpoint TEXT NOT NULL, purpose TEXT NOT NULL, max_output_tokens INTEGER NOT NULL, limits_json TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
"""
TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'E_EVENT_IMMUTABLE: corrections append a new event'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'E_EVENT_IMMUTABLE: history cannot be deleted'); END;
CREATE TRIGGER IF NOT EXISTS events_require_canonical BEFORE INSERT ON events BEGIN
 SELECT CASE WHEN trim(NEW.actor)='' OR trim(NEW.op_id)='' OR NEW.object_version<0 OR json_valid(NEW.identity_json)=0 OR json_valid(NEW.evidence_refs_json)=0 THEN RAISE(ABORT,'E_EVENT_INVALID: canonical identity required') END;
 SELECT CASE WHEN NEW.seq!=COALESCE((SELECT MAX(seq)+1 FROM events),1) THEN RAISE(ABORT,'E_EVENT_SEQUENCE: central chain must be contiguous') END;
 SELECT CASE WHEN NEW.prev_hash!=COALESCE((SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1),'') THEN RAISE(ABORT,'E_EVENT_PREDECESSOR: predecessor mismatch') END;
 SELECT CASE WHEN NEW.event_hash!=ledger_event_hash(NEW.seq,NEW.at,NEW.kind,NEW.work_item_id,NEW.detail,NEW.actor,NEW.op_id,NEW.object_version,NEW.identity_json,NEW.evidence_refs_json,NEW.prev_hash) THEN RAISE(ABORT,'E_EVENT_HASH: invalid canonical hash') END;
END;
"""

class LedgerError(ValueError): pass
def _now(): return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def _canon(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def _event_hash(seq,at,kind,wid,detail,actor,op_id,version,identity,evidence,previous):
    return hashlib.sha256(_canon({"seq":seq,"at":at,"kind":kind,"work_item_id":wid,"detail":detail,"actor":actor,"op_id":op_id,"object_version":version,"identity_json":identity,"evidence_refs_json":evidence,"prev_hash":previous}).encode()).hexdigest()
def _sql_hash(*args): return _event_hash(*args)
def _tables(): return {"meta","work_items","attempts","accepted","events","approvals","sqlite_sequence"}

def _projection(db):
    """Complete security-bearing projections retained inside canonical events.

    Full snapshots trade size for deterministic replay without a second store.
    Schema marker is infrastructure, not mutable task/evidence state.
    """
    out = {}
    for table, order in (("work_items", "id"), ("attempts", "id"),
                         ("accepted", "work_item_id"), ("approvals", "id")):
        out[table] = [dict(row) for row in db.execute("SELECT * FROM %s ORDER BY %s" % (table, order))]
    out["meta"] = [dict(row) for row in db.execute("SELECT key,value FROM meta WHERE key!='schema_version' ORDER BY key")]
    return out

def _begin(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        checked = verify_history(db)
        if checked["internal_chain"] != "VERIFIED" or checked["projection_replay"] == "FAILED":
            raise LedgerError("E_HISTORY_CORRUPT: cannot append over altered history/projections")
    except Exception:
        db.execute("ROLLBACK")
        raise

def connect(path,timeout=10.0):
    db=sqlite3.connect(str(path),timeout=timeout,isolation_level=None); db.row_factory=sqlite3.Row
    db.create_function("ledger_event_hash",11,_sql_hash,deterministic=True)
    exists=db.execute("SELECT name FROM sqlite_master WHERE name='meta'").fetchone()
    if not exists:
        foreign=[r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        if foreign: raise LedgerError("E_LEDGER_FOREIGN: store holds non-ledger tables %s; refusing to adopt" % sorted(foreign))
        db.executescript(SCHEMA); db.execute("INSERT INTO meta VALUES('schema_version',?)",(LEDGER_SCHEMA,)); db.executescript(TRIGGERS); return db
    row=db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    known={r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if row is None: raise LedgerError("E_LEDGER_FOREIGN: meta lacks a ledger schema marker; refusing to adopt")
    if not known.issubset(_tables()): raise LedgerError("E_LEDGER_FOREIGN: store holds non-ledger tables %s; refusing to adopt" % sorted(known-_tables()))
    version=row["value"]
    if version=="2":
        db.executescript(SCHEMA); _migrate_2_to_3(db); version="3"
    if version=="3": _migrate_3_to_4(db)
    elif version!=LEDGER_SCHEMA: raise LedgerError("E_LEDGER_VERSION: schema %s unsupported" % version)
    db.executescript(SCHEMA); db.executescript(TRIGGERS); return db

def _migrate_2_to_3(db):
    if "approval_id" not in {r["name"] for r in db.execute("PRAGMA table_info(attempts)")}: db.execute("ALTER TABLE attempts ADD COLUMN approval_id TEXT")
    db.execute("UPDATE meta SET value='3' WHERE key='schema_version'")
def _migrate_3_to_4(db):
    db.execute("BEGIN IMMEDIATE")
    try:
        existing={r["name"] for r in db.execute("PRAGMA table_info(events)")}
        for name,kind in {"actor":"TEXT","op_id":"TEXT","object_version":"INTEGER","identity_json":"TEXT","evidence_refs_json":"TEXT","prev_hash":"TEXT","event_hash":"TEXT"}.items():
            if name not in existing: db.execute("ALTER TABLE events ADD COLUMN %s %s" % (name,kind))
        previous=""
        for r in db.execute("SELECT seq,at,kind,work_item_id,detail FROM events ORDER BY seq"):
            identity=_canon({"provenance":"legacy_unverified"}); evidence="[]"; op="legacy:%s" % r["seq"]
            digest=_event_hash(r["seq"],r["at"],r["kind"],r["work_item_id"],r["detail"],"LEGACY_UNVERIFIED",op,0,identity,evidence,previous)
            db.execute("UPDATE events SET actor=?,op_id=?,object_version=?,identity_json=?,evidence_refs_json=?,prev_hash=?,event_hash=? WHERE seq=?",("LEGACY_UNVERIFIED",op,0,identity,evidence,previous,digest,r["seq"])); previous=digest
        db.execute("UPDATE meta SET value=? WHERE key='schema_version'",(LEDGER_SCHEMA,))
        _append(db,"LEGACY_STATE_IMPORTED",detail=_canon({"provenance":"legacy_unverified"}),
                actor="LEGACY_UNVERIFIED",object_version=0,identity={"provenance":"legacy_unverified"})
        db.execute("COMMIT")
    except Exception: db.execute("ROLLBACK"); raise

def _append(db,kind,wid=None,detail="",actor="unknown",op_id=None,object_version=1,identity=None,evidence_refs=None):
    if not isinstance(actor,str) or not actor.strip(): raise LedgerError("E_EVENT_ACTOR: explicit actor or unknown required")
    identity = dict(identity or {})
    identity["projection"] = _projection(db)
    identity=_canon(identity); evidence=_canon(evidence_refs or []); last=db.execute("SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone(); seq=(last["seq"]+1) if last else 1; previous=last["event_hash"] if last else ""; at=_now(); op_id=op_id or "OP-"+uuid.uuid4().hex
    digest=_event_hash(seq,at,kind,wid,detail,actor,op_id,object_version,identity,evidence,previous)
    db.execute("INSERT INTO events(seq,at,kind,work_item_id,detail,actor,op_id,object_version,identity_json,evidence_refs_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(seq,at,kind,wid,detail,actor,op_id,object_version,identity,evidence,previous,digest)); return digest
def event(db,kind,work_item_id=None,detail="",**kwargs):
    # Generic events never own projection mutations. In particular a caller
    # must not edit rows inside BEGIN and then ask us to seal that new state.
    if isinstance(kind,str) and kind.startswith("PRACTICAL_NATIVE_"):
        raise LedgerError("E_PRACTICAL_EVENT: practical native journal events require its protected API")
    if isinstance(kind,str) and kind.startswith("NATIVE_") and \
            (kwargs.get('identity') or {}).get('native_evidence_class') != 'TEST_ONLY':
        from .release_profile import require_native_execution_enabled
        require_native_execution_enabled()
    if db.in_transaction:
        raise LedgerError("E_EVENT_TRANSACTION: generic events require their own verified transaction")
    _begin(db)
    try:
        out=_append(db,kind,work_item_id,detail,**kwargs)
        db.execute("COMMIT")
        return out
    except Exception:
        if db.in_transaction: db.execute("ROLLBACK")
        raise

def coordination_get(db,work_item_id):
    row=db.execute("SELECT value FROM meta WHERE key=?",("coordination:"+work_item_id,)).fetchone(); return json.loads(row["value"]) if row else None
def coordination_put(db,work_item_id,policy):
    if not isinstance(policy,dict): raise LedgerError("E_COORDINATION_POLICY: policy must be object")
    _begin(db)
    try:
        raw=_canon(policy); key="coordination:"+work_item_id
        existing=db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone()
        if existing is not None:
            if existing["value"] != raw:
                raise LedgerError("E_COORD_REPLACE: registered task policy/snapshot is immutable")
            db.execute("COMMIT"); return False
        db.execute("INSERT INTO meta(key,value) VALUES(?,?)",(key,raw))
        _append(db,"COORDINATION_POLICY_FROZEN",work_item_id,raw,identity={"work_item_id":work_item_id})
        db.execute("COMMIT"); return True
    except Exception: db.execute("ROLLBACK"); raise
def coordination_record_event(db,kind,work_item_id,detail,**kwargs): return event(db,kind,work_item_id,detail,**kwargs)


# R5 practical native journal -------------------------------------------------
#
# This is deliberately event-only: schema 4 remains unchanged and the canonical
# CM event chain remains the sole history owner.  The opaque objects below are
# normal Python API capabilities.  They stop accidental/public-API forgery but
# are not a claim of security against Python introspection, a private-module
# caller, or an administrator with direct SQLite access.
_PRACTICAL_BINDING_FIELDS = (
    "work_item_id", "operation_id", "selection_digest", "store_incarnation",
    "database", "branch", "native_task_id", "actor", "grant_id",
    "original_row_lock", "fixed_deadline", "command_digest",
    "backend_operation_id",
)
_PRACTICAL_LEASE_FIELDS = (
    "lease_holder", "lease_granted_node", "lease_granted_at_utc",
    "lease_expires_at_utc", "lease_heartbeat_at_utc",
)
_PRACTICAL_BINDING_V2_FIELDS = _PRACTICAL_BINDING_FIELDS + _PRACTICAL_LEASE_FIELDS
_PRACTICAL_REASSIGN_FIELDS = _PRACTICAL_BINDING_V2_FIELDS + ("target_actor", "new_grant_id")
_PRACTICAL_DIGEST_FIELDS = ("selection_digest", "command_digest")
_PRACTICAL_KINDS = (
    "PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_DISPATCHED",
    "PRACTICAL_NATIVE_APPLIED", "PRACTICAL_NATIVE_UNKNOWN",
)
_PRACTICAL_OWNER_SEAL = object()
_PRACTICAL_READER_SEAL = object()


def _practical_sha(value):
    return (isinstance(value,str) and len(value)==64 and
            all(char in "0123456789abcdef" for char in value))


def _practical_binding(value):
    """Validate and canonicalize the complete immutable practical basis."""
    if not isinstance(value,dict) or set(value) not in (
            set(_PRACTICAL_BINDING_FIELDS), set(_PRACTICAL_BINDING_V2_FIELDS),
            set(_PRACTICAL_REASSIGN_FIELDS)):
        raise LedgerError("E_PRACTICAL_BINDING: exact immutable binding fields required")
    out=dict(value)
    if set(out) == set(_PRACTICAL_REASSIGN_FIELDS):
        fields = _PRACTICAL_REASSIGN_FIELDS
    elif set(out) == set(_PRACTICAL_BINDING_V2_FIELDS):
        fields = _PRACTICAL_BINDING_V2_FIELDS
    else:
        fields = _PRACTICAL_BINDING_FIELDS
    for field in fields:
        if field == "original_row_lock":
            continue
        if not isinstance(out[field],str) or not out[field].strip():
            raise LedgerError("E_PRACTICAL_BINDING: %s must be a non-empty string" % field)
    for field in _PRACTICAL_DIGEST_FIELDS:
        if not _practical_sha(out[field]):
            raise LedgerError("E_PRACTICAL_BINDING: %s must be lower SHA-256" % field)
    if out["branch"] != "main":
        raise LedgerError("E_PRACTICAL_BINDING: branch must be the approved main candidate")
    lock=out["original_row_lock"]
    if isinstance(lock,bool) or not isinstance(lock,int) or lock==0 or not -(2**63)<=lock<=2**63-1:
        raise LedgerError("E_PRACTICAL_BINDING: original_row_lock must be a nonzero signed int64")
    deadline=out["fixed_deadline"]
    try:
        if deadline.endswith("Z"):
            parsed=datetime.fromisoformat(deadline[:-1] + "+00:00")
            if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed):
                raise ValueError("not UTC")
        else:
            # The protected local backend samples its database-side UTC clock
            # and retains the exact SQL timestamp (without a client offset).
            # CM binds those original bytes rather than rewriting the evidence.
            parsed=datetime.strptime(deadline,"%Y-%m-%d %H:%M:%S.%f")
    except ValueError as exc:
        raise LedgerError("E_PRACTICAL_BINDING: fixed_deadline must be a recognized UTC timestamp") from exc
    if fields in (_PRACTICAL_BINDING_V2_FIELDS, _PRACTICAL_REASSIGN_FIELDS):
        lease_times={}
        for field in ("lease_granted_at_utc", "lease_expires_at_utc", "lease_heartbeat_at_utc"):
            value=out[field]
            # The protected backend records database UTC DATETIME bytes, not a
            # converted client/RFC3339 representation.  Bind those original
            # bytes exactly, while requiring a whole-second native lease.
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}",value):
                raise LedgerError("E_PRACTICAL_BINDING: %s must be a pinned-second native UTC timestamp" % field)
            try:
                lease_times[field]=datetime.strptime(value,"%Y-%m-%d %H:%M:%S.%f")
            except ValueError as exc:
                raise LedgerError("E_PRACTICAL_BINDING: %s must be a valid UTC calendar time" % field) from exc
            if lease_times[field].microsecond != 0:
                raise LedgerError("E_PRACTICAL_BINDING: %s must be pinned to a whole second" % field)
        if out["actor"] != out["lease_holder"]:
            raise LedgerError("E_PRACTICAL_BINDING: actor must equal the lease holder")
        if out["fixed_deadline"] != out["lease_expires_at_utc"]:
            raise LedgerError("E_PRACTICAL_BINDING: fixed deadline must equal lease expiry")
        if not (lease_times["lease_granted_at_utc"] <= lease_times["lease_heartbeat_at_utc"] < lease_times["lease_expires_at_utc"]):
            raise LedgerError("E_PRACTICAL_BINDING: lease times must satisfy granted <= heartbeat < expiry")
    if fields == _PRACTICAL_REASSIGN_FIELDS:
        if out["target_actor"] == out["actor"]:
            raise LedgerError("E_PRACTICAL_BINDING: successor must differ from transferor")
        if out["new_grant_id"] == out["grant_id"]:
            raise LedgerError("E_PRACTICAL_BINDING: successor grant must differ from prior grant")
    return out


def _practical_detail(row):
    try:
        value=json.loads(row["detail"])
    except (KeyError,TypeError,ValueError) as exc:
        raise LedgerError("E_PRACTICAL_HISTORY: practical event detail is invalid") from exc
    if not isinstance(value,dict):
        raise LedgerError("E_PRACTICAL_HISTORY: practical event detail must be an object")
    return value


def _practical_validate_receipt(binding, receipt):
    if not isinstance(receipt,dict) or set(receipt) != set(binding) | {"observed_state"}:
        raise LedgerError("E_PRACTICAL_RECEIPT: exact readback receipt fields required")
    observed=receipt.get("observed_state")
    if observed not in ("WORKING_SET_APPLIED", "UNKNOWN", "MISSING", "HEAD"):
        raise LedgerError("E_PRACTICAL_RECEIPT: unsupported observed state")
    receipt_binding={field:receipt[field] for field in binding}
    if _canon(_practical_binding(receipt_binding)) != _canon(binding):
        raise LedgerError("E_PRACTICAL_RECEIPT: readback result is foreign to the durable intent")
    return dict(receipt)


def _practical_events_locked(db, operation_id=None):
    rows=db.execute("SELECT * FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq").fetchall()
    return [row for row in rows if operation_id is None or
            _practical_detail(row).get("binding",{}).get("operation_id")==operation_id]


def _validate_practical_history(rows):
    """Reject a syntactically chained practical history with invalid semantics."""
    operations={}
    backend_operations={}
    for row in rows:
        if not row["kind"].startswith("PRACTICAL_NATIVE_"):
            continue
        if row["kind"] not in _PRACTICAL_KINDS:
            raise LedgerError("E_PRACTICAL_HISTORY: unsupported practical event kind")
        detail=_practical_detail(row)
        binding=_practical_binding(detail.get("binding"))
        if row["work_item_id"] != binding["work_item_id"]:
            raise LedgerError("E_PRACTICAL_HISTORY: event work item differs from immutable binding")
        if row["kind"] == "PRACTICAL_NATIVE_INTENT":
            if set(detail)!={"binding"}:
                raise LedgerError("E_PRACTICAL_HISTORY: intent detail changed")
            existing=backend_operations.get(binding["backend_operation_id"])
            if existing and existing != binding["operation_id"]:
                raise LedgerError("E_PRACTICAL_HISTORY: backend operation identity is reused")
            backend_operations[binding["backend_operation_id"]]=binding["operation_id"]
        elif row["kind"] == "PRACTICAL_NATIVE_DISPATCHED":
            if set(detail)!={"binding"}:
                raise LedgerError("E_PRACTICAL_HISTORY: dispatched detail changed")
        elif row["kind"] == "PRACTICAL_NATIVE_APPLIED":
            if set(detail)!={"binding","receipt"}:
                raise LedgerError("E_PRACTICAL_HISTORY: applied detail changed")
            receipt=_practical_validate_receipt(binding,detail["receipt"])
            if receipt["observed_state"] != "WORKING_SET_APPLIED":
                raise LedgerError("E_PRACTICAL_HISTORY: applied event lacks working-set proof")
        else:
            if set(detail) not in ({"binding","reason"},{"binding","reason","receipt"}) or \
                    not isinstance(detail.get("reason"),str) or not detail["reason"].strip():
                raise LedgerError("E_PRACTICAL_HISTORY: unknown detail changed")
            if "receipt" in detail:
                receipt=_practical_validate_receipt(binding,detail["receipt"])
                if receipt["observed_state"] == "WORKING_SET_APPLIED":
                    raise LedgerError("E_PRACTICAL_HISTORY: working-set proof cannot be unknown")
        operations.setdefault(binding["operation_id"],[]).append((row,binding))
    for events in operations.values():
        first,binding=events[0]
        if first["kind"] != "PRACTICAL_NATIVE_INTENT":
            raise LedgerError("E_PRACTICAL_HISTORY: operation has no leading intent")
        durable=_canon(binding)
        if len(events)>4:
            raise LedgerError("E_PRACTICAL_HISTORY: operation has extra transitions")
        for index,(row,current) in enumerate(events):
            if _canon(current)!=durable:
                raise LedgerError("E_PRACTICAL_HISTORY: immutable binding changed")
        kinds=[row["kind"] for row,_ in events]
        if "PRACTICAL_NATIVE_DISPATCHED" in kinds:
            if len(kinds)<2 or kinds[1] != "PRACTICAL_NATIVE_DISPATCHED" or \
                    kinds.count("PRACTICAL_NATIVE_DISPATCHED") != 1:
                raise LedgerError("E_PRACTICAL_HISTORY: dispatch must occur exactly once after intent")
            terminals=kinds[2:]
        else:
            terminals=kinds[1:]
        if any(kind not in ("PRACTICAL_NATIVE_APPLIED","PRACTICAL_NATIVE_UNKNOWN") for kind in terminals):
            raise LedgerError("E_PRACTICAL_HISTORY: invalid practical transition")
        if len(terminals)>2 or (len(terminals)==2 and terminals != ["PRACTICAL_NATIVE_UNKNOWN","PRACTICAL_NATIVE_APPLIED"]):
            raise LedgerError("E_PRACTICAL_HISTORY: only UNKNOWN may reconcile to APPLIED")


def _practical_current_work_item(db, binding):
    row=db.execute("SELECT id FROM work_items WHERE id=?",(binding["work_item_id"],)).fetchone()
    policy=coordination_get(db,binding["work_item_id"])
    if row is None or not isinstance(policy,dict) or policy.get("registered") is not True:
        raise LedgerError("E_PRACTICAL_WORK_ITEM: a current registered CM work item is required")


class _PracticalNativeReservation:
    __slots__=("_seal","_db","_binding")
    def __init__(self, seal, db, binding):
        if seal is not _PRACTICAL_OWNER_SEAL:
            raise LedgerError("E_PRACTICAL_OWNER: internal reservation capability required")
        self._seal, self._db, self._binding=seal,db,_canon(binding)


class _PracticalNativeReaderRegistration:
    __slots__=("_seal","_db","_reader")
    def __init__(self, seal, db, reader):
        if seal is not _PRACTICAL_READER_SEAL:
            raise LedgerError("E_PRACTICAL_READER: internal reader registration required")
        self._seal, self._db, self._reader=seal,db,reader


def _register_practical_native_readback_consumer(db, reader):
    """Private integration seam for the protected concrete backend consumer.

    It is intentionally private: public callers cannot register an arbitrary
    lambda then pass a caller-created success dictionary to completion.  The
    registered consumer must perform its own real local backend op-id readback.
    """
    method=getattr(reader,"read_practical_native_operation",None)
    if db.in_transaction or not callable(method):
        raise LedgerError("E_PRACTICAL_READER: a concrete private readback consumer is required")
    return _PracticalNativeReaderRegistration(_PRACTICAL_READER_SEAL,db,reader)


def _practical_owner(reservation, db, binding):
    if not isinstance(reservation,_PracticalNativeReservation) or \
            reservation._seal is not _PRACTICAL_OWNER_SEAL or reservation._db is not db or \
            reservation._binding != _canon(binding):
        raise LedgerError("E_PRACTICAL_OWNER: winning reservation capability required")


def _practical_reader(registration, db):
    if not isinstance(registration,_PracticalNativeReaderRegistration) or \
            registration._seal is not _PRACTICAL_READER_SEAL or registration._db is not db or \
            not callable(getattr(registration._reader,"read_practical_native_operation",None)):
        raise LedgerError("E_PRACTICAL_READER: registered protected reader capability required")
    return registration._reader


def reserve_practical_native_intent(db, binding):
    """Atomically reserve one durable native operation; only the winner can dispatch."""
    from .release_profile import require_native_execution_enabled
    require_native_execution_enabled()
    binding=_practical_binding(binding)
    if db.in_transaction:
        raise LedgerError("E_PRACTICAL_TRANSACTION: reservation requires its own transaction")
    _begin(db)
    try:
        _practical_current_work_item(db,binding)
        all_events=_practical_events_locked(db)
        _validate_practical_history(all_events)
        existing=[(row,_practical_detail(row)) for row in all_events
                  if _practical_detail(row).get("binding",{}).get("operation_id")==binding["operation_id"]]
        if existing:
            prior=_practical_binding(existing[0][1].get("binding"))
            if _canon(prior)!=_canon(binding):
                raise LedgerError("E_PRACTICAL_BINDING: operation id is already bound to different immutable facts")
            db.execute("COMMIT")
            return {"winner":False,"reservation":None,"kind":existing[-1][0]["kind"],"binding":dict(prior)}
        for row in all_events:
            if row["kind"]=="PRACTICAL_NATIVE_INTENT":
                prior=_practical_binding(_practical_detail(row)["binding"])
                if prior["backend_operation_id"]==binding["backend_operation_id"]:
                    raise LedgerError("E_PRACTICAL_BINDING: backend operation identity is already bound")
        _append(db,"PRACTICAL_NATIVE_INTENT",binding["work_item_id"],_canon({"binding":binding}),
                actor=binding["actor"],op_id="PRACTICAL:"+binding["operation_id"],
                identity={"work_item_id":binding["work_item_id"],"operation_id":binding["operation_id"]},
                evidence_refs=[binding["selection_digest"],binding["command_digest"]])
        db.execute("COMMIT")
        return {"winner":True,"reservation":_PracticalNativeReservation(_PRACTICAL_OWNER_SEAL,db,binding),
                "kind":"PRACTICAL_NATIVE_INTENT","binding":dict(binding)}
    except Exception:
        if db.in_transaction: db.execute("ROLLBACK")
        raise


def consume_practical_native_dispatch(db, binding, reservation):
    """Durably consume the winner-only dispatch capability before native work.

    This only records the CM-side claim.  It does not run a subprocess, infer a
    backend effect, or turn a v1 intent into native proof.  The database-bound
    opaque reservation and the persisted event together prevent a reopened or
    second backend object from issuing another dispatch for the same intent.
    """
    from .release_profile import require_native_execution_enabled
    require_native_execution_enabled()
    binding=_practical_binding(binding)
    if db.in_transaction:
        raise LedgerError("E_PRACTICAL_TRANSACTION: dispatch consumption requires its own transaction")
    _begin(db)
    try:
        _practical_current_work_item(db,binding); _practical_owner(reservation,db,binding)
        rows,durable=_practical_intent_locked(db,binding)
        if rows[-1]["kind"] != "PRACTICAL_NATIVE_INTENT":
            db.execute("COMMIT")
            return {"dispatch":False,"kind":rows[-1]["kind"],"binding":dict(durable)}
        _append(db,"PRACTICAL_NATIVE_DISPATCHED",durable["work_item_id"],
                _canon({"binding":durable}),actor=durable["actor"],
                op_id="PRACTICAL:"+durable["operation_id"],
                identity={"work_item_id":durable["work_item_id"],"operation_id":durable["operation_id"]},
                evidence_refs=[durable["selection_digest"],durable["command_digest"]])
        db.execute("COMMIT")
        return {"dispatch":True,"kind":"PRACTICAL_NATIVE_DISPATCHED","binding":dict(durable)}
    except Exception:
        if db.in_transaction: db.execute("ROLLBACK")
        raise


def _practical_intent_locked(db, binding):
    rows=_practical_events_locked(db,binding["operation_id"])
    _validate_practical_history(_practical_events_locked(db))
    if not rows or rows[0]["kind"]!="PRACTICAL_NATIVE_INTENT":
        raise LedgerError("E_PRACTICAL_ORDER: durable practical intent is required")
    durable=_practical_binding(_practical_detail(rows[0])["binding"])
    if _canon(durable)!=_canon(binding):
        raise LedgerError("E_PRACTICAL_BINDING: supplied facts differ from durable intent")
    return rows,durable


def mark_practical_native_unknown(db, reservation, error):
    """Record a winner-only uncertain external dispatch; it never asserts success."""
    if not isinstance(error,str) or not error.strip():
        raise LedgerError("E_PRACTICAL_UNKNOWN: non-empty uncertainty reason required")
    if not isinstance(reservation,_PracticalNativeReservation):
        raise LedgerError("E_PRACTICAL_OWNER: winning reservation capability required")
    binding=_practical_binding(json.loads(reservation._binding))
    if db.in_transaction:
        raise LedgerError("E_PRACTICAL_TRANSACTION: transition requires its own transaction")
    _begin(db)
    try:
        _practical_current_work_item(db,binding); _practical_owner(reservation,db,binding)
        rows,durable=_practical_intent_locked(db,binding)
        if rows[-1]["kind"] in ("PRACTICAL_NATIVE_APPLIED","PRACTICAL_NATIVE_UNKNOWN"):
            db.execute("COMMIT")
            return {"inserted":False,"kind":rows[-1]["kind"],"binding":dict(durable)}
        _append(db,"PRACTICAL_NATIVE_UNKNOWN",binding["work_item_id"],
                _canon({"binding":binding,"reason":error}),actor=binding["actor"],
                op_id="PRACTICAL:"+binding["operation_id"],
                identity={"work_item_id":binding["work_item_id"],"operation_id":binding["operation_id"]},
                evidence_refs=[binding["selection_digest"],binding["command_digest"]])
        db.execute("COMMIT")
        return {"inserted":True,"kind":"PRACTICAL_NATIVE_UNKNOWN","binding":dict(binding)}
    except Exception:
        if db.in_transaction: db.execute("ROLLBACK")
        raise


def complete_practical_native_readback(db, binding, reader_registration, reservation=None):
    """Invoke protected fresh readback and append APPLIED only for exact evidence.

    ``reservation=None`` is recovery-only: a newly opened protected consumer
    may read the already-stored intent, but no new dispatch capability is made.
    """
    from .release_profile import require_native_execution_enabled
    require_native_execution_enabled()
    binding=_practical_binding(binding); reader=_practical_reader(reader_registration,db)
    if reservation is not None: _practical_owner(reservation,db,binding)
    if db.in_transaction:
        raise LedgerError("E_PRACTICAL_TRANSACTION: completion requires its own transaction")
    _begin(db)
    try:
        _practical_current_work_item(db,binding)
        rows,durable=_practical_intent_locked(db,binding)
        if rows[-1]["kind"] == "PRACTICAL_NATIVE_APPLIED":
            db.execute("COMMIT")
            return {"inserted":False,"kind":rows[-1]["kind"],"binding":dict(durable)}
        # The registered protected consumer maps unavailable/missing backend
        # observation to None.  A malformed or foreign receipt deliberately
        # propagates: it must not be rewritten into a caller-friendly UNKNOWN.
        observed=reader.read_practical_native_operation(dict(durable))
        reason="readback missing or uncertain"
        if observed is None:
            if rows[-1]["kind"] == "PRACTICAL_NATIVE_UNKNOWN":
                db.execute("COMMIT")
                return {"inserted":False,"kind":"PRACTICAL_NATIVE_UNKNOWN","binding":dict(durable)}
            detail={"binding":durable,"reason":reason}; kind="PRACTICAL_NATIVE_UNKNOWN"
        else:
            receipt=_practical_validate_receipt(durable,observed)
            if receipt["observed_state"]=="WORKING_SET_APPLIED":
                detail={"binding":durable,"receipt":receipt}; kind="PRACTICAL_NATIVE_APPLIED"
            else:
                if rows[-1]["kind"] == "PRACTICAL_NATIVE_UNKNOWN":
                    db.execute("COMMIT")
                    return {"inserted":False,"kind":"PRACTICAL_NATIVE_UNKNOWN","binding":dict(durable)}
                detail={"binding":durable,"reason":"readback state "+receipt["observed_state"],"receipt":receipt}
                kind="PRACTICAL_NATIVE_UNKNOWN"
        _append(db,kind,durable["work_item_id"],_canon(detail),actor=durable["actor"],
                op_id="PRACTICAL:"+durable["operation_id"],
                identity={"work_item_id":durable["work_item_id"],"operation_id":durable["operation_id"]},
                evidence_refs=[durable["selection_digest"],durable["command_digest"]])
        db.execute("COMMIT")
        return {"inserted":True,"kind":kind,"binding":dict(durable)}
    except Exception:
        if db.in_transaction: db.execute("ROLLBACK")
        raise

def bind_request_measurement(db,attempt_id,request_digest,measurement_digest):
    for name,value in (("request_digest",request_digest),("measurement_digest",measurement_digest)):
        if not isinstance(value,str) or len(value)!=64: raise LedgerError("E_MEASUREMENT_VALUE: %s must be a sha256" % name)
    row=db.execute("SELECT work_item_id,state,request_digest FROM attempts WHERE id=?",(attempt_id,)).fetchone()
    if row is None or row["state"]!="PREPARED" or row["request_digest"]!=request_digest: raise LedgerError("E_MEASUREMENT_STATE: bind only exact prepared request")
    event(db,"REQUEST_MEASUREMENT_BOUND",row["work_item_id"],_canon({"attempt_id":attempt_id,"request_digest":request_digest,"measurement_digest":measurement_digest}),identity={"attempt_id":attempt_id,"work_item_id":row["work_item_id"]},evidence_refs=[measurement_digest])
def request_measurement_binding(db,attempt_id,request_digest):
    for r in db.execute("SELECT detail FROM events WHERE kind='REQUEST_MEASUREMENT_BOUND' ORDER BY seq DESC"):
        try: value=json.loads(r["detail"])
        except (TypeError,ValueError): continue
        if value.get("attempt_id")==attempt_id and value.get("request_digest")==request_digest: return value.get("measurement_digest")
    return None

def create_work_item(db,work_item_id,task_digest,source_id):
    _begin(db)
    try:
        db.execute("INSERT INTO work_items(id,task_digest,source_id,status,created_at) VALUES(?,?,?,?,?)",(work_item_id,task_digest,source_id,"PENDING",_now())); _append(db,"WORK_ITEM_CREATED",work_item_id,_canon({"task_digest":task_digest,"source_id":source_id}),identity={"work_item_id":work_item_id,"task_digest":task_digest,"source_id":source_id}); db.execute("COMMIT")
    except sqlite3.IntegrityError as exc:
        db.execute("ROLLBACK")
        if "UNIQUE constraint failed: work_items.id" in str(exc):
            raise LedgerError("E_WORK_ITEM_DUPLICATE: %s" % work_item_id) from exc
        raise
    except Exception: db.execute("ROLLBACK"); raise
def _latest_attempt(db,work_item_id): return db.execute("SELECT * FROM attempts WHERE work_item_id=? ORDER BY attempt_no DESC LIMIT 1",(work_item_id,)).fetchone()
def unresolved_delivery(db,work_item_id):
    """Return retained uncertain delivery; a generic retry note cannot resolve it."""
    return db.execute("SELECT id FROM attempts WHERE work_item_id=? AND state='DELIVERY_UNKNOWN' ORDER BY attempt_no DESC LIMIT 1",(work_item_id,)).fetchone()
def begin_attempt(db,work_item_id):
    _begin(db)
    try:
        if coordination_get(db,work_item_id) is not None:
            if unresolved_delivery(db,work_item_id) is not None:
                raise LedgerError("E_COORD_DELIVERY_UNKNOWN: reconcile delivery or approve a distinct run/basis; no replacement attempt")
            latest = _latest_attempt(db,work_item_id)
            if latest is not None and (latest["state"] not in TERMINAL or accepted_attempt(db,work_item_id)):
                raise LedgerError("E_COORD_ACTIVE_ATTEMPT: serialized coordinated claim already has work; resume or revoke")
        n=db.execute("SELECT COALESCE(MAX(attempt_no),0) m FROM attempts WHERE work_item_id=?",(work_item_id,)).fetchone()["m"]+1; aid="ATT-"+uuid.uuid4().hex[:12]; db.execute("INSERT INTO attempts(id,work_item_id,attempt_no,state,updated_at) VALUES(?,?,?,?,?)",(aid,work_item_id,n,"QUEUED",_now())); _append(db,"ATTEMPT_QUEUED",work_item_id,_canon({"attempt_id":aid,"state":"QUEUED"}),identity={"attempt_id":aid,"work_item_id":work_item_id}); db.execute("COMMIT"); return aid
    except Exception: db.execute("ROLLBACK"); raise

def transition(db,attempt_id,to_state,request_digest=None,response_digest=None,approval_ref=None,error=None,coordination_context=None):
    _begin(db)
    try:
        row=db.execute("SELECT * FROM attempts WHERE id=?",(attempt_id,)).fetchone()
        if row is None: raise LedgerError("E_ATTEMPT_UNKNOWN: %s" % attempt_id)
        current=row["state"]
        if current in TERMINAL: raise LedgerError("E_ATTEMPT_TERMINAL: %s already %s" % (attempt_id,current))
        if to_state not in FORWARD.get(current,()): raise LedgerError("E_TRANSITION: %s -> %s illegal" % (current,to_state))
        if to_state in ("CANCELLED", "RETRYABLE_ERROR") and row["response_digest"] is None and coordination_get(db,row["work_item_id"]) is not None:
            spent=row["approval_id"] is not None and db.execute("SELECT id FROM approvals WHERE id=? AND consumed=1",(row["approval_id"],)).fetchone() is not None
            if spent:
                raise LedgerError("E_COORD_DELIVERY_UNKNOWN: spent approval without a saved response requires uncertain-delivery reconciliation, not cancellation/retry")
        if to_state in ("PREPARED", "DISPATCHING", "ACCEPTED") and coordination_get(db,row["work_item_id"]) is not None:
            try:
                from . import coordination
                coordination.require_transition_guard(db,attempt_id,coordination_context,to_state=to_state)
                if to_state == "DISPATCHING":
                    raise LedgerError("E_COORD_DISPATCH_START: use atomic guarded approval consumption and dispatch start")
            except ImportError:
                if coordination_get(db,row["work_item_id"]) is not None: raise LedgerError("E_COORDINATION_GUARD: coordinated acceptance requires verified runner")
        db.execute("UPDATE attempts SET state=?,request_digest=COALESCE(?,request_digest),response_digest=COALESCE(?,response_digest),approval_ref=COALESCE(?,approval_ref),error=?,updated_at=? WHERE id=?",(to_state,request_digest,response_digest,approval_ref,error,_now(),attempt_id))
        if to_state=="ACCEPTED":
            old=db.execute("SELECT * FROM accepted WHERE work_item_id=?",(row["work_item_id"],)).fetchone()
            if old is not None and not old["revoked"]: raise LedgerError("E_DOUBLE_ACCEPT: %s already accepted; revoke first" % row["work_item_id"])
            if old: db.execute("UPDATE accepted SET attempt_id=?,revoked=0,revoke_reason=NULL,accepted_at=? WHERE work_item_id=?",(attempt_id,_now(),row["work_item_id"]))
            else: db.execute("INSERT INTO accepted(work_item_id,attempt_id,accepted_at) VALUES(?,?,?)",(row["work_item_id"],attempt_id,_now()))
            db.execute("UPDATE work_items SET status='ACCEPTED' WHERE id=?",(row["work_item_id"],))
        detail=_canon({"attempt_id":attempt_id,"from_state":current,"to_state":to_state,"request_digest":request_digest or row["request_digest"],"response_digest":response_digest or row["response_digest"],"error":error}); _append(db,"ATTEMPT_"+to_state,row["work_item_id"],detail,identity={"attempt_id":attempt_id,"work_item_id":row["work_item_id"]},evidence_refs=[x for x in (request_digest or row["request_digest"],response_digest or row["response_digest"]) if x]); db.execute("COMMIT")
    except Exception: db.execute("ROLLBACK"); raise
def revoke(db,work_item_id,reason):
    if not (reason or "").strip(): raise LedgerError("E_REVOKE_REASON: revocation needs a reason")
    _begin(db)
    try:
        row=db.execute("SELECT * FROM accepted WHERE work_item_id=? AND revoked=0",(work_item_id,)).fetchone()
        if row is None: raise LedgerError("E_REVOKE_NOTHING: %s has no current accepted result" % work_item_id)
        db.execute("UPDATE accepted SET revoked=1,revoke_reason=? WHERE work_item_id=?",(reason,work_item_id)); db.execute("UPDATE work_items SET status='PENDING' WHERE id=?",(work_item_id,)); _append(db,"ACCEPTED_REVOKED",work_item_id,_canon({"attempt_id":row["attempt_id"],"reason":reason}),identity={"work_item_id":work_item_id,"attempt_id":row["attempt_id"]}); db.execute("COMMIT")
    except Exception: db.execute("ROLLBACK"); raise

def issue_approval(db,attempt_id,request_digest,provider,model,endpoint,purpose,max_output_tokens,limits=None):
    for name,value in (("request_digest",request_digest),("provider",provider),("model",model),("endpoint",endpoint),("purpose",purpose)):
        if not isinstance(value,str) or not value.strip(): raise LedgerError("E_APPROVAL_VALUE: %s must be non-empty" % name)
    if isinstance(max_output_tokens,bool) or not isinstance(max_output_tokens,int) or max_output_tokens<=0: raise LedgerError("E_APPROVAL_VALUE: max_output_tokens must be a positive int")
    approval="APR-"+uuid.uuid4().hex[:12]; _begin(db)
    try:
        if db.execute("SELECT id FROM attempts WHERE id=?",(attempt_id,)).fetchone() is None: raise LedgerError("E_APPROVAL_ATTEMPT: unknown attempt %s" % attempt_id)
        db.execute("INSERT INTO approvals(id,attempt_id,request_digest,provider,model,endpoint,purpose,max_output_tokens,limits_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(approval,attempt_id,request_digest,provider,model,endpoint,purpose,max_output_tokens,_canon(limits or {}),_now())); _append(db,"APPROVAL_ISSUED",None,_canon({"approval_id":approval,"attempt_id":attempt_id}),identity={"attempt_id":attempt_id},evidence_refs=[request_digest]); db.execute("COMMIT"); return approval
    except Exception: db.execute("ROLLBACK"); raise
def _consume_approval_locked(db,approval_id,attempt_id,request_digest):
    row=db.execute("SELECT approval_id FROM attempts WHERE id=?",(attempt_id,)).fetchone()
    if row is None or row["approval_id"] is not None:
        raise LedgerError("E_APPROVAL_SPENT: attempt already consumed an approval or is unknown")
    if db.execute("UPDATE approvals SET consumed=1 WHERE id=? AND consumed=0 AND attempt_id=? AND request_digest=?",(approval_id,attempt_id,request_digest)).rowcount!=1:
        raise LedgerError("E_APPROVAL_SPENT: approval missing, consumed, or mismatched")
    db.execute("UPDATE attempts SET approval_id=? WHERE id=?",(approval_id,attempt_id))
    _append(db,"APPROVAL_CONSUMED",None,_canon({"approval_id":approval_id,"attempt_id":attempt_id}),identity={"attempt_id":attempt_id},evidence_refs=[request_digest])

def consume_approval(db,approval_id,attempt_id,request_digest):
    _begin(db)
    try:
        _consume_approval_locked(db,approval_id,attempt_id,request_digest)
        db.execute("COMMIT"); return db.execute("SELECT * FROM approvals WHERE id=?",(approval_id,)).fetchone()
    except Exception: db.execute("ROLLBACK"); raise

def start_approved_dispatch(db,approval_id,attempt_id,request_digest,coordination_context):
    """Recheck prerequisites, spend approval and enter dispatch atomically.

    This serializes CM state only, not filesystem changes or native/API writes.
    If interrupted after commit, recovery retains DELIVERY_UNKNOWN.
    """
    _begin(db)
    try:
        row=db.execute("SELECT * FROM attempts WHERE id=?",(attempt_id,)).fetchone()
        if row is None or row["state"]!="AWAITING_APPROVAL" or row["request_digest"]!=request_digest:
            raise LedgerError("E_DISPATCH_STATE: exact approved attempt required")
        if coordination_get(db,row["work_item_id"]) is not None:
            from . import coordination
            coordination.require_transition_guard(db,attempt_id,coordination_context,to_state="DISPATCHING")
        _consume_approval_locked(db,approval_id,attempt_id,request_digest)
        db.execute("UPDATE attempts SET state='DISPATCHING',error=NULL,updated_at=? WHERE id=?",(_now(),attempt_id))
        _append(db,"ATTEMPT_DISPATCHING",row["work_item_id"],
                _canon({"attempt_id":attempt_id,"from_state":row["state"],"to_state":"DISPATCHING",
                        "request_digest":request_digest,"response_digest":row["response_digest"],"error":None}),
                identity={"attempt_id":attempt_id,"work_item_id":row["work_item_id"]},
                evidence_refs=[value for value in (request_digest,row["response_digest"]) if value])
        db.execute("COMMIT")
    except Exception: db.execute("ROLLBACK"); raise

def reconcile_uncertain_attempt(db,attempt_id):
    """Retain an interrupted dispatched/spent attempt as DELIVERY_UNKNOWN.

    No queued retry and no new approval are created. A response saved before
    interruption instead resumes validation/acceptance through the runner.
    """
    _begin(db)
    try:
        row=db.execute("SELECT * FROM attempts WHERE id=?",(attempt_id,)).fetchone()
        if row is None: raise LedgerError("E_ATTEMPT_UNKNOWN")
        if row["state"]=="DELIVERY_UNKNOWN":
            db.execute("COMMIT"); return False
        spent=row["approval_id"] is not None and db.execute("SELECT id FROM approvals WHERE id=? AND consumed=1",(row["approval_id"],)).fetchone() is not None
        if row["state"]!="DISPATCHING" and not (row["state"]=="AWAITING_APPROVAL" and spent):
            raise LedgerError("E_RECONCILE_STATE: only interrupted dispatch/spent approval is uncertain")
        db.execute("UPDATE attempts SET state='DELIVERY_UNKNOWN',error='reconciled after reopen',updated_at=? WHERE id=?",(_now(),attempt_id))
        _append(db,"RECONCILED_DELIVERY_UNKNOWN",row["work_item_id"],
                _canon({"attempt_id":attempt_id,"from_state":row["state"],"to_state":"DELIVERY_UNKNOWN"}),
                identity={"attempt_id":attempt_id,"work_item_id":row["work_item_id"]})
        db.execute("COMMIT"); return True
    except Exception: db.execute("ROLLBACK"); raise
def reconcile_on_open(db):
    moved=[]; _begin(db)
    try:
        for row in db.execute("SELECT id,work_item_id,state,approval_id FROM attempts WHERE state IN ('PREPARED','AWAITING_APPROVAL','DISPATCHING')").fetchall():
            spent=row["approval_id"] is not None and db.execute("SELECT id FROM approvals WHERE id=? AND consumed=1",(row["approval_id"],)).fetchone() is not None
            target="DELIVERY_UNKNOWN" if row["state"]=="DISPATCHING" or (row["state"]=="AWAITING_APPROVAL" and spent) else "QUEUED"
            db.execute("UPDATE attempts SET state=?,error=?,updated_at=? WHERE id=?",(target,"reconciled after reopen",_now(),row["id"])); _append(db,"RECONCILED_"+target,row["work_item_id"],_canon({"attempt_id":row["id"],"from_state":row["state"],"to_state":target}),identity={"attempt_id":row["id"],"work_item_id":row["work_item_id"]}); moved.append((row["id"],row["state"],target))
        db.execute("COMMIT")
    except Exception: db.execute("ROLLBACK"); raise
    return moved

def make_checkpoint(db,owner,checkpoint_id=None):
    if not isinstance(owner,str) or not owner.strip(): raise LedgerError("E_CHECKPOINT_OWNER: owner is required")
    row=db.execute("SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone(); return {"schema":"cm-history-checkpoint-v1","checkpoint_id":checkpoint_id or "CHK-"+uuid.uuid4().hex,"owner":owner,"seq":row["seq"] if row else 0,"event_hash":row["event_hash"] if row else ""}
_PROJECTION_KEYS = {"work_items":"id", "attempts":"id", "accepted":"work_item_id",
                    "approvals":"id", "meta":"key"}

def _snapshot_map(snapshot):
    if not isinstance(snapshot,dict) or set(snapshot)!=set(_PROJECTION_KEYS):
        raise ValueError("projection fields")
    out={}
    for table,key in _PROJECTION_KEYS.items():
        if not isinstance(snapshot[table],list): raise ValueError("projection rows")
        out[table]={}
        for item in snapshot[table]:
            if not isinstance(item,dict) or not isinstance(item.get(key),str) or item[key] in out[table]:
                raise ValueError("projection identity")
            out[table][item[key]]=item
    return out

def _replay_change(before,after,row):
    """Validate the typed projection delta, not merely the final snapshot.

    Generic audit/merge/measurement events change no ledger projection. Task
    identity and registered coordination metadata cannot be changed or removed
    by any later event. Every mutator has an explicit, limited delta below.
    """
    expected=json.loads(_canon(before))
    kind=row["kind"]; wid=row["work_item_id"]
    try: detail=json.loads(row["detail"])
    except (TypeError,ValueError): detail={}

    def change(table,key,fields=None,new=False):
        candidate=after[table][key]
        if new:
            if key in before[table]: raise ValueError("projection duplicate")
        else:
            original=before[table][key]
            if set(candidate)!=set(original) or any(candidate[name]!=value for name,value in original.items() if name not in fields):
                raise ValueError("projection changed immutable fields")
        expected[table][key]=candidate
        return candidate

    if kind=="WORK_ITEM_CREATED":
        work=change("work_items",wid,new=True)
        if work["status"]!="PENDING" or work["task_digest"]!=detail["task_digest"] or work["source_id"]!=detail["source_id"]:
            raise ValueError("work identity")
    elif kind=="COORDINATION_POLICY_FROZEN":
        policy=change("meta","coordination:"+wid,new=True)
        if policy["value"]!=row["detail"] or wid not in before["work_items"]:
            raise ValueError("coordination identity")
    elif kind=="ATTEMPT_QUEUED":
        aid=detail["attempt_id"]; attempt=change("attempts",aid,new=True)
        number=1+max((a["attempt_no"] for a in before["attempts"].values() if a["work_item_id"]==wid),default=0)
        if wid not in before["work_items"] or attempt["work_item_id"]!=wid or attempt["state"]!="QUEUED" or attempt["attempt_no"]!=number or any(attempt[k] is not None for k in ("request_digest","response_digest","approval_ref","approval_id","error")):
            raise ValueError("attempt claim")
    elif kind.startswith("ATTEMPT_"):
        aid=detail["attempt_id"]; original=before["attempts"][aid]
        attempt=change("attempts",aid,{"state","request_digest","response_digest","approval_ref","error","updated_at"})
        state=detail["to_state"]
        if kind!="ATTEMPT_"+state or original["work_item_id"]!=wid or detail["from_state"]!=original["state"] or state not in FORWARD.get(original["state"],()) or attempt["state"]!=state or attempt["request_digest"]!=detail["request_digest"] or attempt["response_digest"]!=detail["response_digest"] or attempt["error"]!=detail["error"]:
            raise ValueError("attempt transition")
        if state=="ACCEPTED":
            old=before["accepted"].get(wid)
            if old is not None and old["revoked"]!=1: raise ValueError("double acceptance")
            accepted=change("accepted",wid,{"attempt_id","revoked","revoke_reason","accepted_at"},new=old is None)
            work=change("work_items",wid,{"status"})
            if accepted["attempt_id"]!=aid or accepted["revoked"]!=0 or accepted["revoke_reason"] is not None or work["status"]!="ACCEPTED":
                raise ValueError("accepted projection")
    elif kind=="ACCEPTED_REVOKED":
        accepted=change("accepted",wid,{"revoked","revoke_reason"})
        work=change("work_items",wid,{"status"})
        if before["accepted"][wid]["revoked"]!=0 or accepted["attempt_id"]!=detail["attempt_id"] or accepted["revoked"]!=1 or accepted["revoke_reason"]!=detail["reason"] or not detail["reason"].strip() or work["status"]!="PENDING":
            raise ValueError("revocation projection")
    elif kind=="APPROVAL_ISSUED":
        approval=change("approvals",detail["approval_id"],new=True)
        if approval["attempt_id"]!=detail["attempt_id"] or approval["attempt_id"] not in before["attempts"] or approval["consumed"]!=0 or type(approval["max_output_tokens"]) is not int or approval["max_output_tokens"]<=0 or any(not isinstance(approval[k],str) or not approval[k].strip() for k in ("request_digest","provider","model","endpoint","purpose")):
            raise ValueError("approval projection")
        json.loads(approval["limits_json"])
    elif kind=="APPROVAL_CONSUMED":
        pid=detail["approval_id"]; aid=detail["attempt_id"]
        approval=change("approvals",pid,{"consumed"}); attempt=change("attempts",aid,{"approval_id"})
        if before["approvals"][pid]["consumed"]!=0 or before["attempts"][aid]["approval_id"] is not None or approval["consumed"]!=1 or approval["attempt_id"]!=aid or attempt["approval_id"]!=pid:
            raise ValueError("approval consumption")
    elif kind.startswith("RECONCILED_"):
        aid=detail["attempt_id"]; original=before["attempts"][aid]
        attempt=change("attempts",aid,{"state","error","updated_at"})
        spent=original["approval_id"] is not None and before["approvals"].get(original["approval_id"],{}).get("consumed")==1
        state="DELIVERY_UNKNOWN" if original["state"]=="DISPATCHING" or (original["state"]=="AWAITING_APPROVAL" and spent) else "QUEUED"
        if original["state"] not in ("PREPARED","AWAITING_APPROVAL","DISPATCHING") or original["work_item_id"]!=wid or detail["from_state"]!=original["state"] or detail["to_state"]!=state or kind!="RECONCILED_"+state or attempt["state"]!=state or attempt["error"]!="reconciled after reopen":
            raise ValueError("reconciliation projection")
    if expected!=after: raise ValueError("unexplained projection delta")

def _replay_projections(rows):
    replayed={key:{} for key in _PROJECTION_KEYS}
    legacy=False; imported=False; modern=False
    for row in rows:
        identity=json.loads(row["identity_json"])
        if row["actor"]=="LEGACY_UNVERIFIED":
            if modern or imported or identity.get("provenance")!="legacy_unverified" or row["object_version"]!=0:
                raise ValueError("invalid legacy provenance")
            legacy=True
            if row["kind"]=="LEGACY_STATE_IMPORTED":
                replayed=_snapshot_map(identity["projection"]); imported=True
            elif "projection" in identity or row["op_id"]!="legacy:%s" % row["seq"]:
                raise ValueError("invalid legacy event")
            continue
        if legacy and not imported: raise ValueError("missing legacy baseline")
        modern=True
        snapshot=_snapshot_map(identity["projection"])
        _replay_change(replayed,snapshot,row)
        replayed=snapshot
    if legacy and not imported: raise ValueError("missing legacy import")
    return replayed,legacy
def verify_history(db,checkpoint=None):
    rows=db.execute("SELECT * FROM events ORDER BY seq").fetchall(); previous=""; good=True
    for seq,row in enumerate(rows,1):
        good=good and row["seq"]==seq and row["prev_hash"]==previous and row["event_hash"]==_event_hash(row["seq"],row["at"],row["kind"],row["work_item_id"],row["detail"],row["actor"],row["op_id"],row["object_version"],row["identity_json"],row["evidence_refs_json"],row["prev_hash"])
        if not good: break
        previous=row["event_hash"]
    internal="VERIFIED" if good else "FAILED"
    if checkpoint is None: anchored="UNVERIFIED"
    elif not isinstance(checkpoint,dict) or set(checkpoint)!={"schema","checkpoint_id","owner","seq","event_hash"} or checkpoint.get("schema")!="cm-history-checkpoint-v1" or type(checkpoint.get("seq")) is not int or not 0<=checkpoint["seq"]<=len(rows) or any(not isinstance(checkpoint.get(k),str) or not checkpoint[k].strip() for k in ("owner","checkpoint_id")): anchored="FAILED"
    elif checkpoint["seq"]==0: anchored="VERIFIED" if good and checkpoint["event_hash"]=="" else "FAILED"
    else:
        anchor=next((r for r in rows if r["seq"]==checkpoint.get("seq")),None); anchored="VERIFIED" if good and anchor and anchor["event_hash"]==checkpoint.get("event_hash") else "FAILED"
    anchored_through = checkpoint["seq"] if anchored=="VERIFIED" else None
    current_head_anchored = anchored=="VERIFIED" and checkpoint["seq"]==len(rows)
    if anchored=="VERIFIED" and not current_head_anchored:
        anchored="UNVERIFIED"
    # Every typed delta is checked; a generic event may not bless arbitrary
    # projection edits even when its canonical chain hash is valid.
    try:
        _validate_practical_history(rows)
        replayed,legacy = _replay_projections(rows)
        projection = "UNVERIFIED" if legacy else "VERIFIED"
        if not good or replayed!=_snapshot_map(_projection(db)): projection="FAILED"
    except (ValueError,KeyError,TypeError,AttributeError):
        projection="FAILED"
    triggers={r["name"] for r in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    return {"normal_append_only_enforced":"VERIFIED" if {"events_no_update","events_no_delete","events_require_canonical"}.issubset(triggers) else "UNVERIFIED","internal_chain":internal,"anchored_completeness":anchored,"anchored_through_seq":anchored_through,"current_head_anchored":current_head_anchored,"projection_replay":projection,"event_count":len(rows),"head_hash":previous}
def pending_work(db): return [r["id"] for r in db.execute("SELECT id FROM work_items WHERE status!='ACCEPTED' ORDER BY id")]
def accepted_attempt(db,work_item_id):
    row=db.execute("SELECT attempt_id FROM accepted WHERE work_item_id=? AND revoked=0",(work_item_id,)).fetchone(); return row["attempt_id"] if row else None
def history(db,work_item_id): return [dict(r) for r in db.execute("SELECT attempt_no,state,error FROM attempts WHERE work_item_id=? ORDER BY attempt_no",(work_item_id,))]
