"""Scoped current-source invalidation and reusable automatic projection builds."""
from pathlib import Path
from . import contracts as c,indexing

def invalidation(doc,stale):
    changed=set(stale);nodes=doc['projection']['nodes'];edges=doc['projection']['edges']
    invalid={n['id'] for n in nodes if any(r['source_id'] in changed for r in n['source_units'])}
    while True:
        more={n['id'] for n in nodes if n['derivation'] and set(n['derivation']['premises'])&invalid}
        more|={e['subject'] for e in edges if e['predicate'] in {'DEPENDS_ON','REFERENCES','DEFINED_IN','SUPPORTED_BY','DERIVED_FROM','TESTS'} and (e['object'] in invalid or any(r['source_id'] in changed for r in e['source_units']))}
        if more<=invalid:break
        invalid|=more
    return sorted(invalid)

def previous(store):
    store=c.ordinary(store,True)
    if not (store/'CURRENT').exists():return None
    generation=c.sha((store/'CURRENT').read_text(encoding='ascii').strip());raw=c.ordinary(store/'generations'/generation/'generation.json').read_bytes()
    if c.digest(raw)!=generation:raise ValueError('E_GENERATION_CORRUPT')
    return c.loads(raw)

def validate_construction(doc):
    construction=c.keys(doc['construction'],{'schema_version','kind','extraction','prose','prose_status','tests','scope'},'construction manifest')
    if construction['schema_version']!=1 or construction['kind']!='automatic-project-2':raise ValueError('E_CONSTRUCTION_VERSION')
    manifest=construction['extraction']
    from .extraction import _sealed_previous
    if not _sealed_previous(manifest,doc['repository']):raise ValueError('E_CONSTRUCTION_EXTRACTION_SEAL')
    if set(manifest['sources'])!=set(doc['sources']):raise ValueError('E_CONSTRUCTION_SCOPE')
    for ident,source in doc['sources'].items():
        observed=manifest['sources'][ident]
        if observed['source_sha256']!=source['source_sha256'] or observed['path']!=source['path'] or observed['unit_manifest_digest']!=c.digest(c.canonical(source['manifest'])):raise ValueError('E_CONSTRUCTION_SOURCE_BINDING')
        if observed['unit_ranges']!=[{'id':u['id'],'range':list(u['range'])} for u in source['manifest']['units']]:raise ValueError('E_CONSTRUCTION_UNIT_BINDING')
    return construction

def build(root,source_map,store,companion,worker=None,test_receipt=None,language_parser=None):
    from . import extraction
    old=previous(store);sources=indexing.freeze(root,source_map,companion)
    result=extraction.extract(sources,source_map['repository'],previous=old.get('construction',{}).get('extraction') if old else None,root=root,language_parser=language_parser)
    projection=result['projection'];manifest=result['manifest']
    prose=[]
    if worker:
        for ident,source in sources.items():
            if Path(source['path']).suffix.lower() not in {'.md','.txt','.rst'}:continue
            text=c.within(root,source['path']).read_bytes().decode('utf-8')
            receipt=worker({'op':'extract_prose','text':text})
            if receipt.get('ok') is not True or not isinstance(receipt.get('relationships'),list):raise ValueError('E_EXTRACTION_WORKER')
            # Relations are navigation candidates; endpoint identity stays source scoped.
            for rel in receipt['relationships']:
                span=rel['span'];refs=[{'source_id':ident,'unit_id':u['id']} for u in source['manifest']['units'] if u['range'][0]<span[1] and u['range'][1]>span[0]]
                if not refs or source['source_sha256']!=c.digest(c.within(root,source['path']).read_bytes()):raise ValueError('E_STALE_EXTRACTION')
                endpoints=[]
                for name in (rel['subject'],rel['object']):
                    nid='prose:'+c.digest((ident+'\0'+name).encode())[:32];endpoints.append(nid)
                    if not any(n['id']==nid for n in projection['nodes']):
                        projection['nodes'].append({'id':nid,'type':'Component','text':name+' '+rel['text'],'source_units':refs,'polarity':'positive','conditions':[],'derivation':None,'valid_from':None,'valid_until':None,'review_status':'unreviewed','vector':extraction.vectorize(name+' '+rel['text'])})
                edge={'id':'prose-edge:'+c.digest(c.canonical([ident,rel]))[:32],'subject':endpoints[0],'predicate':rel['predicate'],'object':endpoints[1],'source_units':refs,'conditions':[],'valid_from':None,'valid_until':None}
                # Only Component-compatible types enter this small prose projection.
                from .offline_engine import validate_types
                try:validate_types(projection['nodes'],[edge])
                except ValueError:continue
                projection['edges'].append(edge);prose.append({'source_id':ident,**rel})
    if test_receipt:
        from . import test_evidence
        test_evidence.verify(test_receipt,root,{'sources':sources})
        test_evidence.add_projection(projection,test_receipt,sources)
    construction={'schema_version':1,'kind':'automatic-project-2','extraction':manifest,'prose':prose,'prose_status':'OBSERVED_RELATION_DSL' if worker else 'NOT_REQUESTED','tests':test_receipt,'scope':'declared source map; external and dynamic dependencies unresolved'}
    answer=indexing.build(root,source_map,projection,store,companion,construction=construction,expected_sources=sources)
    answer['reused_sources']=len(manifest['cache']['reused_source_ids'])
    return answer
