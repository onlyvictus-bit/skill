"""Bounded diagnostics in the existing CM UNKNOWN event, never fence proof.

Packet hashes detect damage, not a malicious database administrator or Python
module patch. These observations cannot authorize success, replay or native
qualification. No native process or database migration is performed here.
"""
import base64
from hashlib import sha256
import json
import sqlite3
import subprocess

from .practical_contract import strict_canonical_json

MAX_CHANNEL_BYTES = 64 * 1024
MAX_REASON_BYTES = 256 * 1024
KIND = 'PRACTICAL_EXECUTION_DIAGNOSTICS'
_PIN = 'ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2'
_TRANSPORT_FIELDS = frozenset(('source','selection_digest','dolt_sha256','executable',
    'host','port','database','branch','sql_sha256','command_sha256','timeout_seconds',
    'outcome','returncode','exception_type','stdout','stderr'))
_CHANNEL_FIELDS = frozenset(('available','base64','captured_bytes','observed_bytes',
    'sha256','captured_sha256','truncated'))


class ObservedRows(list):
    """Private transport-result carrier, diagnostic only; never receipt authority."""
    def __init__(self, rows, observation):
        super().__init__(rows)
        self.transport_observation=observation


def _hash(value):
    return sha256(strict_canonical_json(value)).hexdigest()


def _channel(raw):
    available = isinstance(raw,bytes)
    prefix = raw[:MAX_CHANNEL_BYTES] if available else b''
    return dict(available=available,base64=base64.b64encode(prefix).decode('ascii'),
        captured_bytes=len(prefix),observed_bytes=len(raw) if available else None,
        sha256=sha256(raw).hexdigest() if available else None,
        captured_sha256=sha256(prefix).hexdigest(),
        truncated=available and len(raw)>len(prefix))


def capture_transport(selection, sql, argv, timeout, *, result=None, error=None):
    """Capture bytes/status and fixed identity, never env or exception text."""
    if error is None:
        outcome='PROCESS_RESULT'
        stdout,stderr=getattr(result,'stdout',None),getattr(result,'stderr',None)
        returncode=getattr(result,'returncode',None)
    else:
        outcome='TIMEOUT' if isinstance(error,subprocess.TimeoutExpired) else 'SPAWN_ERROR'
        stdout,stderr=getattr(error,'stdout',None),getattr(error,'stderr',None)
        returncode=None
    if type(returncode) is not int:
        returncode=None
    return dict(source='SEALED_DOLT_CLIENT',selection_digest=selection.digest,
        dolt_sha256=selection.dolt_sha256,executable=selection.dolt_executable,
        host=selection.host,port=selection.port,database=selection.database,branch='main',
        sql_sha256=sha256(sql.encode('utf-8')).hexdigest(),command_sha256=_hash(argv),
        timeout_seconds=timeout,outcome=outcome,returncode=returncode,
        exception_type=type(error).__name__ if error is not None else None,
        stdout=_channel(stdout),stderr=_channel(stderr))


def _sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def _check_channel(value):
    if not isinstance(value,dict) or set(value)!=_CHANNEL_FIELDS or \
            type(value['available']) is not bool or type(value['truncated']) is not bool:
        raise ValueError('E_EXECUTION_CHANNEL')
    try:
        raw=base64.b64decode(value['base64'],validate=True)
    except (ValueError,TypeError) as exc:
        raise ValueError('E_EXECUTION_BASE64') from exc
    if type(value['captured_bytes']) is not int or not 0<=len(raw)<=MAX_CHANNEL_BYTES or \
            len(raw)!=value['captured_bytes'] or value['captured_sha256']!=sha256(raw).hexdigest():
        raise ValueError('E_EXECUTION_CAPTURE_HASH')
    if value['available']:
        size=value['observed_bytes']
        if type(size) is not int or size<len(raw) or not _sha(value['sha256']) or \
                value['truncated'] is not (size>len(raw)) or \
                (not value['truncated'] and value['sha256']!=sha256(raw).hexdigest()):
            raise ValueError('E_EXECUTION_OUTPUT_LENGTH')
    elif raw or value['observed_bytes'] is not None or value['sha256'] is not None or value['truncated']:
        raise ValueError('E_EXECUTION_MISSING_BYTES')


def validate_observation(value, binding, *, expected_sql_sha256):
    """Validate damage/identity; never interpret a database rejection."""
    from complete_read_v2 import ledger
    if not isinstance(value,dict) or set(value)!={'schema_version','kind','binding','transport','transport_sha256'} or \
            type(value['schema_version']) is not int or value['schema_version']!=1 or value['kind']!=KIND:
        raise ValueError('E_EXECUTION_PACKET')
    basis=ledger._practical_binding(binding)
    if strict_canonical_json(value['binding'])!=strict_canonical_json(basis):
        raise ValueError('E_EXECUTION_BINDING')
    data=value['transport']
    if not isinstance(data,dict) or set(data)!=_TRANSPORT_FIELDS or value['transport_sha256']!=_hash(data):
        raise ValueError('E_EXECUTION_TRANSPORT_HASH')
    if not _sha(expected_sql_sha256) or data['sql_sha256']!=expected_sql_sha256 or \
            data['selection_digest']!=basis['selection_digest'] or data['database']!=basis['database'] or \
            data['branch']!='main' or data['host']!='127.0.0.1' or data['dolt_sha256']!=_PIN or \
            data['source']!='SEALED_DOLT_CLIENT' or not _sha(data['command_sha256']):
        raise ValueError('E_EXECUTION_COMMAND_IDENTITY')
    if not isinstance(data['executable'],str) or data['executable'].replace('\\','/').split('/')[-1].lower()!='dolt.exe' or \
            type(data['port']) is not int or not 1<=data['port']<=65535 or \
            type(data['timeout_seconds']) is not int or not 1<=data['timeout_seconds']<=45 or \
            data['outcome'] not in ('PROCESS_RESULT','TIMEOUT','SPAWN_ERROR') or \
            (data['returncode'] is not None and type(data['returncode']) is not int) or \
            (data['exception_type'] is not None and not isinstance(data['exception_type'],str)) or \
            (data['outcome']!='PROCESS_RESULT' and data['returncode'] is not None):
        raise ValueError('E_EXECUTION_STATUS')
    for channel in ('stdout','stderr'):
        _check_channel(data[channel])
    return json.loads(strict_canonical_json(value))


def diagnostic_reason(binding, selection, sql, error, rows=None):
    """Bind a capture before the consumer swallows delivery exceptions."""
    capture=getattr(error,'transport_observation',None)
    if capture is None and type(rows) is ObservedRows:
        capture=rows.transport_observation
    fallback='lease dispatch uncertain: '+type(error).__name__
    if not isinstance(capture,dict):
        return fallback
    try:
        packet=dict(schema_version=1,kind=KIND,binding=binding,transport=capture,
                    transport_sha256=_hash(capture))
        validate_observation(packet,binding,expected_sql_sha256=sha256(sql.encode()).hexdigest())
        if capture['selection_digest']!=selection.digest:
            return fallback
        encoded=strict_canonical_json(packet)
        return encoded.decode('utf-8') if len(encoded)<=MAX_REASON_BYTES else fallback
    except (ValueError,TypeError):
        return fallback


def _pairs(items):
    value={}
    for key,item in items:
        if key in value:
            raise ValueError('E_EXECUTION_DUPLICATE_KEY')
        value[key]=item
    return value


def read_execution_diagnostics(db, binding, *, expected_sql_sha256):
    """Read protected history only; no reserve, complete, migrate or retry."""
    from complete_read_v2 import ledger
    unavailable=dict(available=False,causal_status='UNVERIFIED',
        evidence_class='TRANSPORT_DIAGNOSTICS_ONLY',capture_complete=False)
    try:
        binding=ledger._practical_binding(binding)
        history=ledger.verify_history(db)
        if history['internal_chain']!='VERIFIED' or history['projection_replay']!='VERIFIED':
            return dict(unavailable,code='E_EXECUTION_HISTORY')
        rows=[]
        for row in db.execute("SELECT * FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq"):
            detail=json.loads(row['detail'],object_pairs_hook=_pairs)
            if detail.get('binding',{}).get('operation_id')==binding['operation_id']:
                if strict_canonical_json(detail['binding'])!=strict_canonical_json(binding):
                    return dict(unavailable,code='E_EXECUTION_BINDING')
                rows.append((row,detail))
        kinds=[row['kind'] for row,_ in rows]
        candidates=[(row,detail) for row,detail in rows if row['kind']=='PRACTICAL_NATIVE_UNKNOWN']
        if kinds.count('PRACTICAL_NATIVE_INTENT')!=1 or kinds.count('PRACTICAL_NATIVE_DISPATCHED')!=1 or len(candidates)!=1:
            return dict(unavailable,code='E_EXECUTION_UNAVAILABLE')
        row,detail=candidates[0]
        reason=detail.get('reason')
        if not isinstance(reason,str) or len(reason.encode('utf-8'))>MAX_REASON_BYTES:
            return dict(unavailable,code='E_EXECUTION_UNAVAILABLE')
        observed=validate_observation(json.loads(reason,object_pairs_hook=_pairs),binding,
                                     expected_sql_sha256=expected_sql_sha256)
        complete=all(observed['transport'][x]['available'] and not observed['transport'][x]['truncated']
                     for x in ('stdout','stderr'))
        complete=complete and observed['transport']['outcome']=='PROCESS_RESULT' and \
            type(observed['transport']['returncode']) is int
        return dict(unavailable,available=True,capture_complete=complete,
                    event_seq=row['seq'],event_hash=row['event_hash'],observation=observed)
    except (ValueError,TypeError,KeyError,sqlite3.Error):
        return dict(unavailable,code='E_EXECUTION_INVALID')
