#!/usr/bin/env python3
"""One pinned local shard session. No socket transport or provider operations."""
import contextlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from knowledge_bridge import contracts as c
from knowledge_bridge.worker import runtime_identity


def main():
    lane, lease, sequence = None, None, 0
    owned, adjacency, vectors, query = {}, {}, {}, None
    identity = runtime_identity()
    while True:
        raw = sys.stdin.buffer.readline(c.MAX_MESSAGE + 2)
        if not raw:
            return 0
        try:
            if not raw.endswith(b'\n') or len(raw) > c.MAX_MESSAGE:
                raise ValueError('E_DISTRIBUTED_MESSAGE_LIMIT')
            request = c.loads(raw)
            c.keys(request, {'schema_version', 'lane', 'sequence', 'lease', 'op', 'payload'}, 'shard request')
            if request['schema_version'] != 1:
                raise ValueError('E_DISTRIBUTED_PROTOCOL')
            c.integer(request['lane'], 0, 1, 'lane'); c.sha(request['lease'])
            if lane is None:
                lane, lease = request['lane'], request['lease']
            if request['lane'] != lane or request['lease'] != lease or request['sequence'] != sequence:
                raise ValueError('E_DISTRIBUTED_REQUEST_BINDING')
            sequence += 1
            payload, op = request['payload'], request['op']
            with contextlib.redirect_stdout(sys.stderr):
                if op == 'fit':
                    fields = {'nodes', 'edges', 'query_text', 'embedding_mode'}
                    if 'vector_override' in payload:
                        fields.add('vector_override')
                    c.keys(payload, fields, 'fit')
                    from knowledge_bridge.offline_engine import search_vectors, validate_types
                    validate_types(payload['nodes'], payload['edges'], shacl=True)
                    if 'vector_override' in payload:
                        override = c.keys(payload['vector_override'], {'vectors', 'query', 'metadata'}, 'vector override')
                        dimension = c.integer(len(override['query']), 1, 4096, 'dimension')
                        if len(override['vectors']) != len(payload['nodes']):
                            raise ValueError('E_DISTRIBUTED_VECTOR_BASIS')
                        vec = [c.vector(v, dimension) for v in override['vectors']]
                        q, metadata = c.vector(override['query'], dimension), override['metadata']
                        if not isinstance(metadata, dict) or metadata.get('dimension') != dimension:
                            raise ValueError('E_DISTRIBUTED_VECTOR_BASIS')
                    else:
                        vec, q, metadata = search_vectors(payload['nodes'], payload['query_text'], payload['embedding_mode'])
                    result = {'vectors': vec, 'query': q, 'metadata': metadata}
                elif op == 'initialize':
                    c.keys(payload, {'nodes', 'edges', 'vectors', 'query', 'direction', 'fit_digest'}, 'shard initialize')
                    c.sha(payload['fit_digest'])
                    if payload['direction'] not in {'outgoing', 'incoming', 'both'}:
                        raise ValueError('E_QUERY_DIRECTION')
                    c.vector(payload['query'], len(payload['query']))
                    query = payload['query']
                    owned = {n['id']: n for n in payload['nodes']}
                    if len(owned) != len(payload['nodes']) or len(owned) != len(payload['vectors']):
                        raise ValueError('E_DISTRIBUTED_OWNERSHIP')
                    if any(int(c.digest(i.encode()), 16) % 2 != lane for i in owned):
                        raise ValueError('E_DISTRIBUTED_OWNERSHIP')
                    for vector in payload['vectors']:
                        c.vector(vector, len(query))
                    vectors = {n['id']: v for n, v in zip(payload['nodes'], payload['vectors'])}
                    adjacency = {i: [] for i in owned}
                    for edge in payload['edges']:
                        if payload['direction'] in {'outgoing', 'both'} and edge['subject'] in owned:
                            adjacency[edge['subject']].append((edge['object'], edge['id']))
                        if payload['direction'] in {'incoming', 'both'} and edge['object'] in owned:
                            adjacency[edge['object']].append((edge['subject'], edge['id']))
                    result = {'shard_digest': c.digest(c.canonical(payload)), 'node_count': len(owned)}
                elif op == 'seed':
                    c.keys(payload, {'seeds'}, 'shard seed')
                    k = c.integer(payload['seeds'], 1, 100, 'seeds')
                    if query is None:
                        raise ValueError('E_DISTRIBUTED_NOT_INITIALIZED')
                    from semantica.vector_store.vector_store import VectorRetriever
                    # Fetch every owned score before cutting ties; upstream
                    # numpy argsort otherwise chooses an arbitrary tied subset.
                    found = VectorRetriever(backend='inmemory').search_similar(query, list(vectors.values()), list(vectors), k=len(vectors)) if vectors else []
                    result = {'seeds': [{'id': item['id'], 'score': float(item['score'])}
                                        for item in sorted(found, key=lambda x: (-x['score'], x['id']))[:k]]}
                elif op == 'neighbors':
                    c.keys(payload, {'id'}, 'shard neighbors')
                    if payload['id'] not in owned:
                        raise ValueError('E_DISTRIBUTED_FOREIGN_OWNER')
                    result = {'neighbors': [list(pair) for pair in sorted(set(adjacency[payload['id']]))]}
                else:
                    raise ValueError('E_DISTRIBUTED_OPERATION')
            reply = {'schema_version': 1, 'lane': lane, 'sequence': request['sequence'],
                     'lease': lease, 'request_digest': c.digest(c.canonical(request)),
                     'ok': True, 'result': result, 'identity': identity}
        except Exception as exc:
            sys.stdout.buffer.write(c.canonical({'ok': False, 'error': type(exc).__name__ + ': ' + str(exc)}) + b'\n')
            sys.stdout.buffer.flush()
            return 2
        response = c.canonical(reply) + b'\n'
        if len(response) > c.MAX_MESSAGE:
            return 2
        sys.stdout.buffer.write(response); sys.stdout.buffer.flush()


if __name__ == '__main__':
    raise SystemExit(main())

