#!/usr/bin/env python3
"""One offline JSON operation in the pinned isolated Semantica interpreter."""
import contextlib
from collections import deque
import importlib.metadata
import io
import json
from pathlib import Path
import socket
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from knowledge_bridge import BRIDGE_VERSION,SEMANTICA_VERSION,SEMANTICA_REVISION
from knowledge_bridge import contracts as c

def _no_network(*args,**kwargs): raise RuntimeError('E_WORKER_NETWORK_FORBIDDEN')
socket.socket.connect=_no_network
socket.socket.connect_ex=_no_network
socket.create_connection=_no_network

def runtime_identity():
    if not (3,10)<=sys.version_info[:2]<(3,14): raise ValueError('E_PYTHON_RANGE')
    if importlib.metadata.version('semantica')!=SEMANTICA_VERSION: raise ValueError('E_SEMANTICA_VERSION')
    dist=importlib.metadata.distribution('semantica');url=c.loads(dist.read_text('direct_url.json') or '{}')
    vcs=url.get('vcs_info',{})
    if vcs.get('commit_id')==SEMANTICA_REVISION: revision=vcs['commit_id']
    elif url.get('dir_info',{}).get('editable'):
        import semantica
        root=Path(semantica.__file__).resolve().parent.parent
        def git(*args):
            p=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,timeout=10)
            if p.returncode!=0: raise ValueError('E_RUNTIME_SOURCE')
            return p.stdout.strip()
        revision=git('rev-parse','HEAD')
        if git('status','--porcelain','--untracked-files=all'): raise ValueError('E_RUNTIME_DIRTY')
    else: raise ValueError('E_RUNTIME_PIN_PROVENANCE: install exact VCS revision')
    if revision!=SEMANTICA_REVISION: raise ValueError('E_RUNTIME_REVISION')
    return {'bridge_version':BRIDGE_VERSION,'semantica_version':SEMANTICA_VERSION,'revision':revision,'network_policy':'no provider operations; Python sockets blocked; not an OS sandbox','answer_generation':False}

def shacl(nodes,edges):
    from rdflib import Graph,Namespace,URIRef,Literal,RDF
    from semantica.ontology.ontology_validator import run_shacl_validation
    ns=Namespace('urn:memory-integrity:'); graph=Graph()
    for n in nodes:
        uri=URIRef('urn:node:'+n['id']);graph.add((uri,RDF.type,ns.KnowledgeNode));graph.add((uri,ns.nodeType,Literal(n['type'])))
        for r in n['source_units']: graph.add((uri,ns.sourceUnit,Literal(r['source_id']+'/'+r['unit_id'])))
    for e in edges:
        uri=URIRef('urn:edge:'+e['id']);graph.add((uri,RDF.type,ns.KnowledgeEdge))
        graph.add((uri,ns.subject,URIRef('urn:node:'+e['subject'])))
        graph.add((uri,ns.object,URIRef('urn:node:'+e['object'])))
        graph.add((uri,ns.predicate,Literal(e['predicate'])))
        for r in e['source_units']: graph.add((uri,ns.sourceUnit,Literal(r['source_id']+'/'+r['unit_id'])))
    shape='''@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix mi: <urn:memory-integrity:> .
mi:Shape a sh:NodeShape; sh:targetClass mi:KnowledgeNode;
 sh:property [ sh:path mi:sourceUnit; sh:minCount 1 ];
 sh:property [ sh:path mi:nodeType; sh:minCount 1; sh:maxCount 1 ] .
mi:EdgeShape a sh:NodeShape; sh:targetClass mi:KnowledgeEdge;
 sh:property [ sh:path mi:sourceUnit; sh:minCount 1 ];
 sh:property [ sh:path mi:subject; sh:minCount 1; sh:maxCount 1; sh:class mi:KnowledgeNode ];
 sh:property [ sh:path mi:object; sh:minCount 1; sh:maxCount 1; sh:class mi:KnowledgeNode ];
 sh:property [ sh:path mi:predicate; sh:minCount 1; sh:maxCount 1 ] .'''
    try: result=run_shacl_validation(graph.serialize(format='turtle'),shape,data_graph_format='turtle',shacl_format='turtle')
    except ImportError: return 'UNAVAILABLE'
    if not result.conforms: raise ValueError('E_SHACL_NONCONFORMING')
    return 'CONFORMS'

def retrieve(payload):
    text_mode=payload.get('op')=='retrieve_text'
    fields={'op','nodes','edges','seeds','max_hops','max_visits','max_results'}
    c.keys(payload,fields|({'query_text','embedding_mode','direction','ontology'} if text_mode else {'query_vector','dimension'}),'worker query')
    from semantica.context.context_graph import ContextGraph
    from semantica.vector_store.vector_store import VectorRetriever
    from semantica.provenance import ProvenanceManager,InMemoryStorage
    nodes=payload['nodes'];edges=payload['edges']
    if not isinstance(nodes,list) or len(nodes)>10000 or not isinstance(edges,list) or len(edges)>40000: raise ValueError('E_GRAPH_SIZE')
    direction=payload['direction'] if text_mode else 'outgoing'
    if direction not in ('outgoing','incoming','both'):raise ValueError('E_QUERY_DIRECTION')
    if text_mode:
        from knowledge_bridge.offline_engine import search_vectors,validate_types
        if payload['ontology']!='project-2':raise ValueError('E_ONTOLOGY_VERSION')
        validate_types(nodes,edges)
        vectors,query,metadata=search_vectors(nodes,payload['query_text'],payload['embedding_mode'])
        dimension=metadata['dimension']
    else:
        dimension=c.integer(payload['dimension'],1,4096,'dimension');query=c.vector(payload['query_vector'],dimension)
        vectors=[c.vector(n['vector'],dimension) for n in nodes]
    seeds=c.integer(payload['seeds'],1,100,'seeds');hops=c.integer(payload['max_hops'],0,8,'hops');visits=c.integer(payload['max_visits'],1,10000,'visits');count=c.integer(payload['max_results'],1,1000,'results')
    ids=[n['id'] for n in nodes]
    if len(ids)!=len(set(ids)): raise ValueError('E_DUPLICATE_NODE')
    graph=ContextGraph(extract_entities=False,extract_relationships=False,advanced_analytics=False)
    for n in nodes:
        if not graph.add_node(n['id'],n['type'],n['text'],source_units=n['source_units']): raise ValueError('E_GRAPH_NODE')
    endpoints={}
    for e in edges:
        if e['subject'] not in ids or e['object'] not in ids or e['predicate'] not in c.PREDICATES: raise ValueError('E_GRAPH_ENDPOINT')
        if not graph.add_edge(e['subject'],e['object'],e['predicate'],id=e['id'],source_units=e['source_units']): raise ValueError('E_GRAPH_EDGE')
        endpoints.setdefault((e['subject'],e['object'],e['predicate']),[]).append(e['id'])
    found=VectorRetriever(backend='inmemory').search_similar(query,vectors,ids,k=min(seeds,len(ids)))
    queue=deque();seen=set();results=[];limits=[]
    for item in sorted(found,key=lambda x:(-x['score'],x['id'])):
        queue.append((item['id'],float(item['score']),[item['id']],[]))
    while queue:
        ident,score,path,edge_ids=queue.popleft()
        if ident in seen: continue
        if len(seen)>=visits:
            limits.append('max_visits');break
        if len(results)>=count:
            limits.append('max_results');break
        seen.add(ident);results.append({'id':ident,'score':score,'path':path,'edge_ids':edge_ids})
        if len(path)-1>=hops: continue
        neighbors=[]
        if direction in ('outgoing','both'):
            for n in graph.get_neighbors(ident,hops=1):neighbors.append((n['id'],endpoints[(ident,n['id'],n['relationship'])][0]))
        if direction in ('incoming','both'):
            neighbors.extend((e['subject'],e['id']) for e in edges if e['object']==ident)
        for target,edge in sorted(set(neighbors)):
            if target not in seen:queue.append((target,score*.9,path+[target],edge_ids+[edge]))
    prov=ProvenanceManager(storage=InMemoryStorage());lineage={};table={n['id']:n for n in nodes}
    closure=set();pending=[item['id'] for item in results]
    while pending:
        ident=pending.pop()
        if ident in closure: continue
        if ident not in table: raise ValueError('E_PROVENANCE_PREMISE')
        closure.add(ident)
        if table[ident]['derivation']: pending.extend(table[ident]['derivation']['premises'])
    tracked=set();sources=set();pending=set(closure)
    while pending:
        ready=sorted(i for i in pending if not table[i]['derivation'] or set(table[i]['derivation']['premises'])<=tracked)
        if not ready: raise ValueError('E_PROVENANCE_CYCLE')
        for ident in ready:
            n=table[ident];parents=[]
            for ref in n['source_units']:
                uri='source:'+ref['source_id']+':'+ref['unit_id']
                if uri not in sources:
                    if prov.track_entity(uri,ref['source_id'],source_location=ref['unit_id']) is None: raise ValueError('E_PROVENANCE_SOURCE')
                    sources.add(uri)
                parents.append(uri)
            if n['derivation']: parents.extend('node:'+i for i in n['derivation']['premises'])
            if prov.track_entity('node:'+ident,parents[0],parent_entity_id=parents[0],used_entities=parents,entity_type='assertion') is None: raise ValueError('E_PROVENANCE_NODE')
            tracked.add(ident);pending.remove(ident)
    for item in results:
        n=table[item['id']]
        actual=prov.get_lineage('node:'+n['id'])
        if not actual.get('integrity_verified'): raise ValueError('E_PROVENANCE_INTEGRITY')
        ancestry=set();todo=[n['id']]
        while todo:
            ident=todo.pop()
            if ident in ancestry: continue
            ancestry.add(ident)
            if table[ident]['derivation']: todo.extend(table[ident]['derivation']['premises'])
        expected={'node:'+i for i in ancestry}
        for ident in ancestry:
            for ref in table[ident]['source_units']: expected.add('source:'+ref['source_id']+':'+ref['unit_id'])
        entity_ids={entry['entity_id'] for entry in actual['lineage_chain']}
        if not expected<=entity_ids: raise ValueError('E_PROVENANCE_PREMISE_LINEAGE')
        lineage[n['id']]={'integrity_verified':True,'source_units':n['source_units'],'derivation':n['derivation'],'lineage_entity_ids':sorted(entity_ids)}
    conform=validate_types(nodes,edges,shacl=True)['shacl'] if text_mode else shacl(nodes,edges)
    if text_mode and shacl(nodes,edges)!='CONFORMS':raise ValueError('E_SHACL_SOURCE_STRUCTURE')
    result={'ok':True,'backend':'SEMANTICA_OBSERVED','results':results,'limits_reached':sorted(set(limits)),'lineage':lineage,'shacl':conform,'score_scale':'cosine [-1,1]; graph hop decay 0.9'}
    if text_mode:result.update(schema_version=2,direction=direction,embedding_metadata=metadata)
    return result

def main():
    try:
        raw=sys.stdin.buffer.read(c.MAX_MESSAGE+1);payload=c.loads(raw)
        # Dependency progress output belongs to stderr, never the protocol.
        with contextlib.redirect_stdout(sys.stderr):
            identity=runtime_identity()
            if payload=={'op':'handshake'}:
                import importlib.util
                result={'ok':True,'backend':'SEMANTICA_OBSERVED','shacl_available':importlib.util.find_spec('pyshacl') is not None}
            elif payload.get('op') in ('retrieve','retrieve_text'): result=retrieve(payload)
            elif payload.get('op')=='extract_prose':
                c.keys(payload,{'op','text'},'prose extraction')
                from knowledge_bridge.offline_engine import extract_prose
                result={'ok':True,'relationships':extract_prose(payload['text']),'extraction_status':'NARROW_RELATION_DSL','semantic_truth':'UNVERIFIED'}
            else: raise ValueError('E_WORKER_OPERATION')
        result.update(identity);response=c.canonical(result)
        if len(response)>c.MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
        sys.stdout.buffer.write(response);return 0
    except Exception as exc:
        sys.stdout.buffer.write(c.canonical({'ok':False,'error':type(exc).__name__+': '+str(exc)}));return 2
if __name__=='__main__': raise SystemExit(main())
