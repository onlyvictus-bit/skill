"""Rebuildable source-bound generations; one writer and atomic publication."""
from datetime import datetime,timezone
import os
from pathlib import Path
import subprocess
import uuid
from . import contracts as c

COMPANION_DIGEST='bf3c6314a1b0e8503230f483ef0be19cbf2ace1d4cab96eb4d7a2599b0270c9f'

def partition_engine(root):
    from integrity_v2 import engine_client
    import sys
    ok,env=engine_client.handshake(root,expect_digest=COMPANION_DIGEST)
    if not ok: raise ValueError('E_COMPANION: '+str(env))
    scripts=(Path(root)/'scripts').resolve(); sys.path.insert(0,str(scripts))
    from complete_read_v2 import partition
    if Path(partition.__file__).resolve().parent.parent!=scripts: raise ValueError('E_COMPANION_IMPORT')
    return partition

def repository_identity(root):
    def git(*args):
        p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=10)
        return p.stdout.strip() if p.returncode==0 else None
    return {'commit':git('rev-parse','HEAD'),'branch':git('symbolic-ref','--short','HEAD')}

def freeze(root,source_map,companion):
    c.keys(source_map,{'schema_version','workspace_id','repository','sources'},'source map')
    if source_map['schema_version']!=1: raise ValueError('E_VERSION')
    c.identity(source_map['workspace_id'],'workspace');c.string(source_map['repository'],'repository')
    if not isinstance(source_map['sources'],list) or not source_map['sources'] or len(source_map['sources'])>1000: raise ValueError('E_SOURCE_SCOPE')
    engine=partition_engine(companion);out={};total=0
    for row in source_map['sources']:
        c.keys(row,{'id','path','authority'},'source'); c.identity(row['id'],'source')
        if row['id'] in out or row['authority'] not in ('AUTHORITATIVE','SUPPORTING','DERIVED','EPHEMERAL'): raise ValueError('E_SOURCE_ID_AUTHORITY')
        path=c.within(root,row['path']);raw=path.read_bytes();raw.decode('utf-8');total+=len(raw)
        if not raw or total>c.MAX_MESSAGE: raise ValueError('E_SOURCE_SIZE')
        manifest=engine.build_manifest(row['id'],raw,max_unit_bytes=4096,max_primary_bytes=16384,context_units=1)
        errors=engine.validate_manifest(raw,manifest)
        if errors: raise ValueError('E_MANIFEST: '+errors[0])
        out[row['id']]={'path':row['path'],'authority':row['authority'],'source_sha256':c.digest(raw),'manifest':manifest}
    return out

def _write(path,raw):
    with Path(path).open('xb') as f:
        f.write(raw);f.flush();os.fsync(f.fileno())

def build(root,source_map,projection,store,companion,construction=None,expected_sources=None):
    root=c.ordinary(root,True);store=c.ordinary(store,True);store.mkdir(parents=True,exist_ok=True)
    lock=store/'writer.lock'
    try: handle=lock.open('x',encoding='utf-8')
    except FileExistsError as exc: raise ValueError('E_WRITER_BUSY: reconcile retained writer lock') from exc
    try:
        with handle:
            handle.write(str(os.getpid()));handle.flush();os.fsync(handle.fileno())
        sources=freeze(root,source_map,companion)
        if expected_sources is not None and sources!=expected_sources:raise ValueError('E_STALE_CONSTRUCTION_SOURCE')
        if construction is not None and expected_sources is None:raise ValueError('E_CONSTRUCTION_SOURCE_BINDING')
        c.validate_projection(projection,sources)
        now=datetime.now(timezone.utc).isoformat()
        body={'schema_version':1,'workspace_id':source_map['workspace_id'],'repository':source_map['repository'],'repository_identity':repository_identity(root),'source_basis_digest':c.digest(c.canonical(sources)),'sources':sources,'projection':projection,'observed_at':now,'built_at':now,'publication_state':'STRUCTURE_VALIDATED','semantic_truth':'UNVERIFIED'}
        if construction is not None:
            body.update(schema_version=2,construction=construction)
        raw=c.canonical(body)
        if len(raw)>c.MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
        generation=c.digest(raw);folder=c.ordinary(store/'generations',True);folder.mkdir(exist_ok=True)
        target=c.ordinary(folder/generation,True)
        if not target.exists():
            target.mkdir();_write(target/'generation.json',raw)
        elif (target/'generation.json').read_bytes()!=raw: raise ValueError('E_GENERATION_COLLISION')
        pointer=store/('CURRENT.'+uuid.uuid4().hex)
        _write(pointer,(generation+'\n').encode('ascii'))
        # Recheck inputs immediately before exposing a new generation.
        if freeze(root,source_map,companion)!=sources or repository_identity(root)!=body['repository_identity']: raise ValueError('E_STALE_BUILD')
        os.replace(pointer,store/'CURRENT')
        return {'ok':True,'generation':generation,'publication_state':'STRUCTURE_VALIDATED','source_basis_digest':body['source_basis_digest'],'semantic_truth':'UNVERIFIED'}
    finally:
        lock.unlink(missing_ok=True)

def load(store,root,companion,generation=None,allowed_sources=None):
    store=c.ordinary(store,True)
    generation=c.sha(generation or c.ordinary(store/'CURRENT').read_text(encoding='ascii').strip())
    path=c.ordinary(store/'generations'/generation/'generation.json');raw=path.read_bytes()
    if c.digest(raw)!=generation: raise ValueError('E_GENERATION_CORRUPT')
    doc=c.loads(raw)
    fields={'schema_version','workspace_id','repository','repository_identity','source_basis_digest','sources','projection','observed_at','built_at','publication_state','semantic_truth'}
    if doc.get('schema_version')==2: fields.add('construction')
    c.keys(doc,fields,'generation')
    if doc['schema_version'] not in (1,2) or doc['publication_state']!='STRUCTURE_VALIDATED': raise ValueError('E_VERSION')
    engine=partition_engine(companion)
    if allowed_sources is not None and not set(allowed_sources)<=set(doc['sources']): raise ValueError('E_POLICY_SOURCE')
    stale=[]
    for ident,source in doc['sources'].items():
        c.keys(source,{'path','authority','source_sha256','manifest'},'frozen source')
        if allowed_sources is not None and ident not in allowed_sources: continue
        path=c.within(root,source['path'])
        actual=path.read_bytes() if path.is_file() else b''
        if c.digest(actual)!=source['source_sha256']:
            if doc['schema_version']==1: raise ValueError('E_STALE_SOURCE: rebuild affected generation')
            stale.append(ident);continue
        errors=engine.validate_manifest(actual,source['manifest'])
        if errors or source['manifest']['source_id']!=ident: raise ValueError('E_MANIFEST_INVALID')
    current=repository_identity(root)
    if doc['schema_version']==1 and current!=doc['repository_identity']: raise ValueError('E_STALE_REPOSITORY_SCOPE')
    if doc['schema_version']==2 and current['branch']!=doc['repository_identity']['branch']: raise ValueError('E_STALE_BRANCH_SCOPE')
    if c.digest(c.canonical(doc['sources']))!=doc['source_basis_digest']: raise ValueError('E_SOURCE_BASIS')
    c.validate_projection(doc['projection'],doc['sources']);doc['generation']=generation
    if doc['schema_version']==2:
        from .impact import invalidation,validate_construction
        validate_construction(doc)
        doc.update(stale_sources=sorted(stale),invalidated_nodes=invalidation(doc,stale),current_repository_identity=current)
    return doc

def reopen(doc,root,ref):
    source=doc['sources'][ref['source_id']];raw=c.within(root,source['path']).read_bytes()
    if c.digest(raw)!=source['source_sha256']: raise ValueError('E_STALE_SOURCE')
    unit=next((u for u in source['manifest']['units'] if u['id']==ref['unit_id']),None)
    if unit is None: raise ValueError('E_UNIT_REF')
    part=raw[unit['range'][0]:unit['range'][1]]
    if c.digest(part)!=unit['sha256']: raise ValueError('E_UNIT_HASH')
    return {**ref,'path':source['path'],'source_sha256':source['source_sha256'],'unit_sha256':unit['sha256'],'range':unit['range'],'text':part.decode('utf-8'),'authority':source['authority']}
