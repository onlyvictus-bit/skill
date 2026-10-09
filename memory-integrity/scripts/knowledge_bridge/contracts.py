"""Strict bridge-v1 contracts, independent of historical companion schemas."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import re

MAX_MESSAGE = 8 * 1024 * 1024
NODE_TYPES = {'Requirement','SourceVersion','SourceUnit','Component','Symbol','Interface','TestCase','TestRun','Decision','Assertion','AuditFinding'}
PREDICATES = {'DEFINED_IN','REFERENCES','DEPENDS_ON','IMPLEMENTS','TESTS','SUPPORTED_BY','CONTRADICTS','SUPERSEDES','DERIVED_FROM'}

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def digest(value): return hashlib.sha256(value).hexdigest()

def _pairs(pairs):
    obj={}
    for key,value in pairs:
        if key in obj: raise ValueError('E_DUP_KEY: '+key)
        obj[key]=value
    return obj

def loads(raw):
    if len(raw.encode('utf-8') if isinstance(raw,str) else raw)>MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
    def invalid(value): raise ValueError('E_NONFINITE_JSON: '+value)
    return json.loads(raw,object_pairs_hook=_pairs,parse_constant=invalid)

def read(path): return loads(Path(path).read_bytes())

def keys(obj,names,where,allow_extra=frozenset()):
    if not isinstance(obj,dict) or set(obj)-set(names)-set(allow_extra) or set(names)-set(obj): raise ValueError('E_SCHEMA: '+where)
    return obj

def string(value,where):
    if not isinstance(value,str) or not value.strip(): raise ValueError('E_STRING: '+where)
    return value

def identity(value,where):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',value): raise ValueError('E_ID: '+where)
    return value

def sha(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value): raise ValueError('E_DIGEST')
    return value

def integer(value,low,high,where):
    if type(value)!=int or not low<=value<=high: raise ValueError('E_LIMIT: '+where)
    return value

def strings(value,where):
    if not isinstance(value,list) or len(value)!=len(set(string(x,where) for x in value)): raise ValueError('E_STRING_LIST: '+where)
    return value

def timestamp(value):
    if value is None: return None
    string(value,'timestamp')
    try: dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc: raise ValueError('E_TIME') from exc
    if dt.tzinfo is None: raise ValueError('E_TIME_ZONE')
    return dt.astimezone(timezone.utc)

def active(row,now):
    start,end=timestamp(row['valid_from']),timestamp(row['valid_until'])
    if start and end and start>end: raise ValueError('E_TIME_RANGE')
    return not ((start and now<start) or (end and now>end))

def vector(value,dimension):
    if not isinstance(value,list) or len(value)!=dimension: raise ValueError('E_VECTOR_DIMENSION')
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in value): raise ValueError('E_VECTOR_FINITE')
    norm=math.hypot(*value)
    if not math.isfinite(norm) or norm==0: raise ValueError('E_VECTOR_NORM')
    return [float(x)/norm for x in value]

def ordinary(path,directory=False):
    p=Path(path).absolute()
    for part in [p,*p.parents]:
        if part.is_symlink(): raise ValueError('E_SYMLINK')
    if p.exists() and not (p.is_dir() if directory else p.is_file()): raise ValueError('E_PATH_KIND')
    return p

def within(root,relative):
    string(relative,'path')
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative or ':' in relative: raise ValueError('E_PATH_ESCAPE')
    root=ordinary(root,True).resolve(); path=ordinary(root/p)
    if not path.resolve().is_relative_to(root): raise ValueError('E_PATH_ESCAPE')
    return path

def refs(value,sources):
    if not isinstance(value,list) or not value: raise ValueError('E_SOURCE_REFS')
    seen=set()
    for row in value:
        keys(row,{'source_id','unit_id'},'source reference')
        pair=(identity(row['source_id'],'source'),identity(row['unit_id'],'unit'))
        if pair in seen or pair[0] not in sources: raise ValueError('E_SOURCE_REF')
        seen.add(pair)
        if pair[1] not in {u['id'] for u in sources[pair[0]]['manifest']['units']}: raise ValueError('E_UNIT_REF')
    return value

def validate_projection(doc,sources):
    keys(doc,{'schema_version','ontology','embedding','nodes','edges'},'projection')
    if (doc['schema_version'],doc['ontology']) not in ((1,'project-1'),(2,'project-2')): raise ValueError('E_VERSION')
    e=keys(doc['embedding'],{'model','dimension','evidence_class'},'embedding')
    string(e['model'],'embedding model'); integer(e['dimension'],1,4096,'dimension')
    if e['evidence_class'] not in ('TEST_ONLY','HOST_OBSERVED','MANUAL_REPORTED'): raise ValueError('E_EMBEDDING_EVIDENCE')
    if not isinstance(doc['nodes'],list) or not doc['nodes'] or len(doc['nodes'])>10000: raise ValueError('E_NODE_SCOPE')
    if not isinstance(doc['edges'],list) or len(doc['edges'])>40000: raise ValueError('E_EDGE_SCOPE')
    ids=set()
    for n in doc['nodes']:
        keys(n,{'id','type','text','source_units','polarity','conditions','derivation','valid_from','valid_until','review_status','vector'},'node')
        identity(n['id'],'node'); string(n['text'],'text'); refs(n['source_units'],sources)
        if n['id'] in ids or n['type'] not in NODE_TYPES: raise ValueError('E_NODE_ID_TYPE')
        ids.add(n['id'])
        if n['polarity'] not in ('positive','negative','unknown') or n['review_status'] not in ('unreviewed','reviewed'): raise ValueError('E_ASSERTION_STATE')
        strings(n['conditions'],'conditions'); active(n,datetime.now(timezone.utc)); vector(n['vector'],e['dimension'])
    for n in doc['nodes']:
        if n['derivation'] is not None:
            d=keys(n['derivation'],{'rule','premises'},'derivation'); string(d['rule'],'rule'); strings(d['premises'],'premises')
            if not d['premises'] or not set(d['premises'])<=ids or n['id'] in d['premises']: raise ValueError('E_DERIVATION')
    # A circular explanation is not a source-grounded inference chain.
    from collections import deque
    dependencies={n['id']:set(n['derivation']['premises']) if n['derivation'] else set() for n in doc['nodes']}
    children={ident:[] for ident in ids}
    for ident,premises in dependencies.items():
        for premise in premises: children[premise].append(ident)
    queue=deque(i for i,premises in dependencies.items() if not premises);count=0
    while queue:
        ident=queue.popleft();count+=1
        for child in children[ident]:
            dependencies[child].remove(ident)
            if not dependencies[child]: queue.append(child)
    if count!=len(ids): raise ValueError('E_DERIVATION_CYCLE')
    edges=set()
    for row in doc['edges']:
        keys(row,{'id','subject','predicate','object','source_units','conditions','valid_from','valid_until'},'edge')
        identity(row['id'],'edge'); refs(row['source_units'],sources); strings(row['conditions'],'conditions'); active(row,datetime.now(timezone.utc))
        if row['id'] in edges or row['subject'] not in ids or row['object'] not in ids or row['predicate'] not in PREDICATES: raise ValueError('E_EDGE_ENDPOINT_OR_TYPE')
        edges.add(row['id'])
    if doc['ontology']=='project-2':
        from .offline_engine import validate_types
        validate_types(doc['nodes'],doc['edges'])
    if len(canonical(doc))>MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
    return doc
