"""Current text retrieval with explicit edge direction and private exclusions.

The source-bound outer pack remains v1. Its v2 retrieval receipt identifies the
authorized text fit separately from extraction's fixed lexical vector identity.
"""
from collections import deque
from datetime import datetime, timezone
import math

from . import contracts as c
from . import indexing
from . import retrieval as legacy


DIRECTIONS = {'outgoing', 'incoming', 'both'}
MODES = {'lexical', 'lsa', 'hybrid'}
REASONS = {'expired', 'notyetvalid', 'premise_unavailable', 'stale',
           'not_selected', 'limit', 'outside_budget'}
BINDING_FIELDS = {'schema_version', 'query_text', 'embedding_mode', 'direction',
                  'seeds', 'max_hops', 'max_visits', 'max_results',
                  'authorized_projection_digest'}
COMMON_FIELDS = {'schema_version', 'ok', 'backend', 'results', 'limits_reached',
                 'lineage', 'shacl', 'query_binding', 'exclusions',
                 'embedding_metadata', 'direction'}
RUNTIME_FIELDS = {'score_scale', 'bridge_version', 'semantica_version', 'revision',
                  'network_policy', 'answer_generation'}
METADATA_FIELDS = {'model', 'dimension', 'evidence_class', 'mode', 'algorithm',
                   'semantic_quality', 'fit_scope_digest', 'sklearn_version',
                   'feature_count', 'document_count', 'lsa_components',
                   'feature_limit', 'lexical_weight', 'query_nonzero_features'}
PACK_FIELDS = {'schema_version', 'kind', 'workspace_id', 'task_id', 'generation',
               'source_basis_digest', 'policy_digest', 'task_obligations_digest',
               'embedding', 'required_units', 'units', 'assertions', 'premises',
               'retrieval', 'coverage', 'semantic_audit', 'pack_digest'}


def _query_binding(binding):
    c.keys(binding, BINDING_FIELDS, 'text query binding')
    if type(binding['schema_version']) is not int or binding['schema_version'] != 2:
        raise ValueError('E_TEXT_QUERY_VERSION')
    c.string(binding['query_text'], 'query text')
    if len(binding['query_text'].encode('utf-8')) > c.MAX_MESSAGE:
        raise ValueError('E_MESSAGE_LIMIT')
    if binding['embedding_mode'] not in MODES:
        raise ValueError('E_EMBEDDING_MODE')
    if binding['direction'] not in DIRECTIONS:
        raise ValueError('E_RETRIEVAL_DIRECTION')
    c.integer(binding['seeds'], 1, 100, 'seeds')
    c.integer(binding['max_hops'], 0, 8, 'hops')
    c.integer(binding['max_visits'], 1, 10000, 'visits')
    c.integer(binding['max_results'], 1, 1000, 'results')
    c.sha(binding['authorized_projection_digest'])
    return binding


def _metadata(metadata, backend, mode):
    c.keys(metadata, METADATA_FIELDS, 'text embedding metadata')
    for key in ('model', 'algorithm', 'sklearn_version'):
        c.string(metadata[key], key)
    if metadata['mode'] != mode or mode not in MODES:
        raise ValueError('E_TEXT_EMBEDDING_MODE')
    expected_class = 'HOST_OBSERVED' if backend == 'SEMANTICA_OBSERVED' else 'TEST_ONLY'
    if metadata['evidence_class'] != expected_class or metadata['semantic_quality'] != 'UNVERIFIED':
        raise ValueError('E_TEXT_EMBEDDING_QUALIFICATION')
    c.sha(metadata['fit_scope_digest'])
    c.integer(metadata['dimension'], 1, 4096, 'text dimension')
    c.integer(metadata['feature_count'], 1, 2048, 'features')
    c.integer(metadata['document_count'], 1, 10000, 'documents')
    c.integer(metadata['lsa_components'], 0, 64, 'latent components')
    if type(metadata['feature_limit']) is not int or metadata['feature_limit'] != 2048:
        raise ValueError('E_TEXT_FEATURE_LIMIT')
    c.integer(metadata['query_nonzero_features'], 1, metadata['feature_count'], 'query features')
    weight = metadata['lexical_weight']
    if type(weight) not in (int, float) or not math.isfinite(weight) or weight != {
            'lexical': 1.0, 'lsa': 0.0, 'hybrid': 0.8}[mode]:
        raise ValueError('E_TEXT_LEXICAL_WEIGHT')
    return metadata


def _source_refs(refs):
    if not isinstance(refs, list) or not refs:
        raise ValueError('E_RETRIEVAL_LINEAGE_REFS')
    seen = set()
    for ref in refs:
        c.keys(ref, {'source_id', 'unit_id'}, 'lineage source')
        pair = (c.identity(ref['source_id'], 'source'), c.identity(ref['unit_id'], 'unit'))
        if pair in seen:
            raise ValueError('E_RETRIEVAL_LINEAGE_REFS')
        seen.add(pair)


def validate_receipt(receipt, execution=False):
    if not isinstance(receipt, dict) or not COMMON_FIELDS <= set(receipt) or set(receipt) - COMMON_FIELDS - RUNTIME_FIELDS:
        raise ValueError('E_RETRIEVAL_RECEIPT_SCHEMA')
    if type(receipt['schema_version']) is not int or receipt['schema_version'] != 2:
        raise ValueError('E_RETRIEVAL_RECEIPT_VERSION')
    backend = receipt['backend']
    if receipt['ok'] is not True or backend not in {'DIRECT_INSPECTION_DEGRADED', 'SEMANTICA_OBSERVED', 'TEST_ONLY'}:
        raise ValueError('E_RETRIEVAL_BACKEND')
    binding = _query_binding(receipt['query_binding'])
    if receipt['direction'] != binding['direction']:
        raise ValueError('E_RETRIEVAL_DIRECTION')
    c.strings(receipt['limits_reached'], 'retrieval limits')
    if not set(receipt['limits_reached']) <= {'max_visits', 'max_results'}:
        raise ValueError('E_RETRIEVAL_LIMIT_KIND')
    if not isinstance(receipt['results'], list) or not isinstance(receipt['lineage'], dict):
        raise ValueError('E_RETRIEVAL_RECEIPT_TYPE')
    if len(receipt['results']) > min(binding['max_visits'], binding['max_results']):
        raise ValueError('E_RETRIEVAL_LIMIT')
    result_ids, roots = set(), set()
    for result in receipt['results']:
        c.keys(result, {'id', 'score', 'path', 'edge_ids'}, 'candidate')
        ident = c.identity(result['id'], 'candidate')
        path, edge_ids, score = result['path'], result['edge_ids'], result['score']
        if not isinstance(path, list) or not path or not isinstance(edge_ids, list):
            raise ValueError('E_RETRIEVAL_FOREIGN_OR_PATH')
        for step in path:
            c.identity(step, 'path node')
        for edge_id in edge_ids:
            c.identity(edge_id, 'path edge')
        if ident in result_ids or path[-1] != ident or len(set(path)) != len(path) or len(edge_ids) != len(path) - 1 or len(path) - 1 > binding['max_hops']:
            raise ValueError('E_RETRIEVAL_FOREIGN_OR_PATH')
        if type(score) not in (int, float) or not math.isfinite(score) or not -1.00001 <= score <= 1.00001:
            raise ValueError('E_SCORE')
        result_ids.add(ident)
        roots.add(path[0])
    if len(roots) > binding['seeds']:
        raise ValueError('E_RETRIEVAL_SEED_LIMIT')
    excluded = c.keys(receipt['exclusions'], {'outside_current_access', 'candidates'}, 'retrieval exclusions')
    c.integer(excluded['outside_current_access'], 0, 10000, 'excluded private nodes')
    if not isinstance(excluded['candidates'], list) or len(excluded['candidates']) > 10000:
        raise ValueError('E_RETRIEVAL_EXCLUSIONS')
    seen = set()
    for item in excluded['candidates']:
        c.keys(item, {'id', 'reason'}, 'candidate exclusion')
        c.identity(item['id'], 'excluded candidate')
        if item['id'] in seen or item['reason'] not in REASONS:
            raise ValueError('E_RETRIEVAL_EXCLUSIONS')
        seen.add(item['id'])
    if backend == 'DIRECT_INSPECTION_DEGRADED':
        c.keys(receipt, COMMON_FIELDS, 'direct text retrieval receipt')
        if receipt['embedding_metadata'] is not None or receipt['results'] or receipt['limits_reached'] or receipt['lineage'] or receipt['shacl'] != 'UNVERIFIED':
            raise ValueError('E_RETRIEVAL_FALSE_QUALIFICATION')
    elif backend == 'TEST_ONLY':
        c.keys(receipt, COMMON_FIELDS, 'test text retrieval receipt')
        _metadata(receipt['embedding_metadata'], backend, binding['embedding_mode'])
        if receipt['lineage'] or receipt['shacl'] != 'UNVERIFIED':
            raise ValueError('E_RETRIEVAL_FALSE_QUALIFICATION')
        if execution:
            raise ValueError('E_RETRIEVAL_UNQUALIFIED')
    else:
        from . import BRIDGE_VERSION, SEMANTICA_VERSION, SEMANTICA_REVISION
        c.keys(receipt, COMMON_FIELDS | RUNTIME_FIELDS, 'observed text retrieval receipt')
        _metadata(receipt['embedding_metadata'], backend, binding['embedding_mode'])
        if receipt['shacl'] not in {'CONFORMS', 'UNAVAILABLE'}:
            raise ValueError('E_RETRIEVAL_SHACL_STATE')
        if receipt['bridge_version'] != BRIDGE_VERSION or receipt['semantica_version'] != SEMANTICA_VERSION or receipt['revision'] != SEMANTICA_REVISION or receipt['answer_generation'] is not False:
            raise ValueError('E_RETRIEVAL_RUNTIME_IDENTITY')
        c.string(receipt['network_policy'], 'network policy')
        c.string(receipt['score_scale'], 'score scale')
        for ident, lineage in receipt['lineage'].items():
            c.identity(ident, 'lineage node')
            c.keys(lineage, {'integrity_verified', 'source_units', 'derivation', 'lineage_entity_ids'}, 'lineage')
            if lineage['integrity_verified'] is not True:
                raise ValueError('E_RETRIEVAL_LINEAGE')
            _source_refs(lineage['source_units'])
            c.strings(lineage['lineage_entity_ids'], 'lineage entities')
            if lineage['derivation'] is not None:
                derivation = c.keys(lineage['derivation'], {'rule', 'premises'}, 'lineage derivation')
                c.string(derivation['rule'], 'lineage rule')
                c.strings(derivation['premises'], 'lineage premises')
                if not derivation['premises']:
                    raise ValueError('E_RETRIEVAL_LINEAGE')
                for premise in derivation['premises']:
                    c.identity(premise, 'lineage premise')
    return receipt


def _visible(doc, policy):
    allowed = set(policy['allowed_source_ids'])
    stale = set(doc.get('stale_sources', []))
    invalidated = set(doc.get('invalidated_nodes', []))
    now = datetime.now(timezone.utc)
    table = {}
    reasons = {}
    outside = 0
    for node in doc['projection']['nodes']:
        if any(ref['source_id'] not in allowed for ref in node['source_units']):
            outside += 1
            continue
        ident = node['id']
        if ident in invalidated or any(ref['source_id'] in stale for ref in node['source_units']):
            reasons[ident] = 'stale'
            continue
        start, end = c.timestamp(node['valid_from']), c.timestamp(node['valid_until'])
        c.active(node, now)
        if start and now < start:
            reasons[ident] = 'notyetvalid'
        elif end and now > end:
            reasons[ident] = 'expired'
        else:
            table[ident] = node
    while True:
        unavailable = {ident for ident, node in table.items()
                       if node['derivation'] and not set(node['derivation']['premises']) <= set(table)}
        if not unavailable:
            break
        for ident in unavailable:
            reasons[ident] = 'premise_unavailable'
            del table[ident]
    nodes = [node for node in doc['projection']['nodes'] if node['id'] in table]
    edges = [edge for edge in doc['projection']['edges']
             if edge['subject'] in table and edge['object'] in table
             and all(ref['source_id'] in allowed and ref['source_id'] not in stale
                     for ref in edge['source_units']) and c.active(edge, now)]
    return nodes, edges, table, outside, reasons


def _binding(nodes, edges, text, mode, direction, seeds, hops, visits, results):
    return _query_binding({'schema_version': 2, 'query_text': text, 'embedding_mode': mode,
                           'direction': direction, 'seeds': seeds, 'max_hops': hops,
                           'max_visits': visits, 'max_results': results,
                           'authorized_projection_digest': c.digest(c.canonical({'nodes': nodes, 'edges': edges}))})


def _step(edge, left, right, direction):
    outgoing = edge['subject'] == left and edge['object'] == right
    incoming = edge['object'] == left and edge['subject'] == right
    return outgoing if direction == 'outgoing' else incoming if direction == 'incoming' else outgoing or incoming


def _candidates(receipt, table, edges, binding):
    if receipt.get('ok') is not True or not isinstance(receipt.get('results'), list):
        raise ValueError('E_RETRIEVAL_FAILED')
    if len(receipt['results']) > min(binding['max_visits'], binding['max_results']):
        raise ValueError('E_RETRIEVAL_LIMIT')
    edge_table = {edge['id']: edge for edge in edges}
    refs, selected, roots = [], [], set()
    seen = set()
    for result in receipt['results']:
        c.keys(result, {'id', 'score', 'path', 'edge_ids'}, 'candidate')
        ident, path, edge_ids = result['id'], result['path'], result['edge_ids']
        c.identity(ident, 'candidate')
        if not isinstance(path, list) or not path or not isinstance(edge_ids, list):
            raise ValueError('E_RETRIEVAL_FOREIGN_OR_PATH')
        for step in path:
            c.identity(step, 'path node')
        for edge_id in edge_ids:
            c.identity(edge_id, 'path edge')
        if ident not in table or ident in seen or path[-1] != ident or len(set(path)) != len(path) or not set(path) <= set(table) or len(path) - 1 > binding['max_hops'] or len(edge_ids) != len(path) - 1:
            raise ValueError('E_RETRIEVAL_FOREIGN_OR_PATH')
        score = result['score']
        if type(score) not in (int, float) or not math.isfinite(score) or not -1.00001 <= score <= 1.00001:
            raise ValueError('E_SCORE')
        for position, edge_id in enumerate(edge_ids):
            edge = edge_table.get(edge_id)
            if edge is None or not _step(edge, path[position], path[position + 1], binding['direction']):
                raise ValueError('E_PATH_EDGE')
            refs.extend(edge['source_units'])
        seen.add(ident)
        selected.append(table[ident])
        roots.update(path)
    closure = {}
    pending = sorted(roots, reverse=True)
    while pending:
        ident = pending.pop()
        if ident in closure:
            continue
        closure[ident] = table[ident]
        refs.extend(table[ident]['source_units'])
        if table[ident]['derivation']:
            pending.extend(table[ident]['derivation']['premises'])
    return selected, [closure[ident] for ident in sorted(set(closure) - seen)], refs


def _exclusions(outside, reasons, table, edges, receipt, binding):
    selected = {item['id'] for item in receipt['results']}
    reachable = set()
    if receipt['limits_reached']:
        adjacency = {ident: set() for ident in table}
        for edge in edges:
            if binding['direction'] in {'outgoing', 'both'}:
                adjacency[edge['subject']].add(edge['object'])
            if binding['direction'] in {'incoming', 'both'}:
                adjacency[edge['object']].add(edge['subject'])
        queue = deque((item['path'][0], 0) for item in receipt['results'])
        while queue:
            ident, depth = queue.popleft()
            if ident in reachable:
                continue
            reachable.add(ident)
            if depth < binding['max_hops']:
                queue.extend((other, depth + 1) for other in sorted(adjacency[ident]) if other not in reachable)
    reported = dict(reasons)
    for ident in set(table) - selected:
        reported[ident] = 'limit' if ident in reachable else 'not_selected'
    return {'outside_current_access': outside,
            'candidates': [{'id': ident, 'reason': reported[ident]} for ident in sorted(reported)]}


def _check_embedding_scope(receipt, nodes):
    if receipt['embedding_metadata'] is None:
        return
    corpus = sorted([{'id': node['id'], 'text': node['text']} for node in nodes], key=lambda row: row['id'])
    metadata = receipt['embedding_metadata']
    if metadata['fit_scope_digest'] != c.digest(c.canonical(corpus)) or metadata['document_count'] != len(nodes):
        raise ValueError('E_TEXT_EMBEDDING_CURRENT_SCOPE')


def _required_units(doc, root, task):
    stale = set(doc.get('stale_sources', []))
    invalidated = set(doc.get('invalidated_nodes', []))
    invalidated_refs = {(ref['source_id'], ref['unit_id'])
                        for node in doc['projection']['nodes'] if node['id'] in invalidated
                        for ref in node['source_units']}
    if any(ref['source_id'] in stale or (ref['source_id'], ref['unit_id']) in invalidated_refs
           for ref in task['required_units']):
        raise ValueError('E_REQUIRED_STALE')
    try:
        return [indexing.reopen(doc, root, ref) for ref in task['required_units']]
    except ValueError as exc:
        if 'E_STALE_SOURCE' in str(exc):
            raise ValueError('E_REQUIRED_STALE') from exc
        raise


def _validate_pack(pack):
    c.keys(pack, PACK_FIELDS, 'evidence pack')
    if type(pack['schema_version']) is not int or pack['schema_version'] != 1 or pack['kind'] != 'knowledge-evidence-v1':
        raise ValueError('E_PACK_VERSION')
    c.identity(pack['workspace_id'], 'workspace')
    c.identity(pack['task_id'], 'task')
    for key in ('generation', 'source_basis_digest', 'policy_digest', 'task_obligations_digest', 'pack_digest'):
        c.sha(pack[key])
    if pack['pack_digest'] != c.digest(c.canonical({key: value for key, value in pack.items() if key != 'pack_digest'})):
        raise ValueError('E_PACK_DIGEST')
    if any(not isinstance(pack[key], list) for key in ('units', 'assertions', 'premises', 'required_units')):
        raise ValueError('E_PACK_LIST')
    pairs = set()
    for unit in pack['units']:
        c.keys(unit, {'source_id', 'unit_id', 'path', 'source_sha256', 'unit_sha256', 'range', 'text', 'authority'}, 'pack unit')
        pair = (c.identity(unit['source_id'], 'source'), c.identity(unit['unit_id'], 'unit'))
        if pair in pairs:
            raise ValueError('E_PACK_DUPLICATE_UNIT')
        pairs.add(pair)
        c.sha(unit['source_sha256'])
        c.sha(unit['unit_sha256'])
        if not isinstance(unit['text'], str) or c.digest(unit['text'].encode('utf-8')) != unit['unit_sha256']:
            raise ValueError('E_PACK_UNIT_HASH')
    for ref in pack['required_units']:
        c.keys(ref, {'source_id', 'unit_id'}, 'required pack unit')
        if (ref['source_id'], ref['unit_id']) not in pairs:
            raise ValueError('E_PACK_REQUIRED_OMITTED')
    if pack['coverage'] != 'UNVERIFIED' or pack['semantic_audit'] != 'UNVERIFIED':
        raise ValueError('E_PACK_FALSE_QUALIFICATION')
    validate_receipt(pack['retrieval'])
    return pack


def retrieve(doc, root, policy, task, query_text, worker, max_hops=2, seeds=1,
             max_visits=100, max_results=50, direction='outgoing', embedding_mode='lexical'):
    legacy.validate_policy(policy, doc, task)
    if doc['projection']['ontology'] != 'project-2':
        raise ValueError('E_TEXT_PROJECTION_VERSION')
    units = _required_units(doc, root, task)
    nodes, edges, table, outside, reasons = _visible(doc, policy)
    binding = _binding(nodes, edges, query_text, embedding_mode, direction, seeds, max_hops, max_visits, max_results)
    if worker is None:
        if task['require_graph']:
            raise ValueError('E_GRAPH_RUNTIME_UNAVAILABLE')
        receipt = {'schema_version': 2, 'ok': True, 'backend': 'DIRECT_INSPECTION_DEGRADED',
                   'results': [], 'limits_reached': [], 'lineage': {}, 'shacl': 'UNVERIFIED',
                   'embedding_metadata': None, 'direction': direction}
    else:
        receipt = worker({'op': 'retrieve_text', 'ontology': 'project-2', 'nodes': nodes, 'edges': edges,
                          'query_text': query_text, 'embedding_mode': embedding_mode, 'direction': direction,
                          'seeds': seeds, 'max_hops': max_hops, 'max_visits': max_visits, 'max_results': max_results})
        if not isinstance(receipt, dict):
            raise ValueError('E_RETRIEVAL_FAILED')
    selected, premises, refs = _candidates(receipt, table, edges, binding)
    receipt = dict(receipt)
    receipt['query_binding'] = binding
    receipt['exclusions'] = _exclusions(outside, reasons, table, edges, receipt, binding)
    validate_receipt(receipt)
    _check_embedding_scope(receipt, nodes)
    seen = {(unit['source_id'], unit['unit_id']) for unit in units}
    for ref in refs:
        pair = (ref['source_id'], ref['unit_id'])
        if pair not in seen:
            seen.add(pair)
            units.append(indexing.reopen(doc, root, ref))
    pack = {'schema_version': 1, 'kind': 'knowledge-evidence-v1', 'workspace_id': doc['workspace_id'],
            'task_id': task['task_id'], 'generation': doc['generation'],
            'source_basis_digest': doc['source_basis_digest'], 'policy_digest': c.digest(c.canonical(policy)),
            'task_obligations_digest': c.digest(c.canonical(task)), 'embedding': doc['projection']['embedding'],
            'required_units': task['required_units'], 'units': units, 'assertions': selected,
            'premises': premises, 'retrieval': receipt, 'coverage': 'UNVERIFIED', 'semantic_audit': 'UNVERIFIED'}
    pack['pack_digest'] = c.digest(c.canonical(pack))
    if len(c.canonical(pack)) > task['max_bytes']:
        raise ValueError('E_PACK_BUDGET: mandatory units retained; reduce optional candidates or increase authorized budget')
    return _validate_pack(pack)


def verify_pack(pack, doc, root, policy, task, worker=None):
    _validate_pack(pack)
    legacy.validate_policy(policy, doc, task)
    _required_units(doc, root, task)
    if pack['embedding'] != doc['projection']['embedding']:
        raise ValueError('E_PACK_EMBEDDING_PROVENANCE')
    if pack['generation'] != doc['generation'] or pack['task_id'] != task['task_id'] or pack['workspace_id'] != policy['workspace_id'] or pack['source_basis_digest'] != doc['source_basis_digest'] or pack['policy_digest'] != c.digest(c.canonical(policy)) or pack['task_obligations_digest'] != c.digest(c.canonical(task)):
        raise ValueError('E_PACK_CURRENT_BASIS')
    if pack['required_units'] != task['required_units']:
        raise ValueError('E_REQUIRED_SCOPE')
    nodes, edges, table, outside, reasons = _visible(doc, policy)
    receipt = pack['retrieval']
    binding = receipt['query_binding']
    actual = _binding(nodes, edges, binding['query_text'], binding['embedding_mode'], binding['direction'],
                      binding['seeds'], binding['max_hops'], binding['max_visits'], binding['max_results'])
    if actual != binding:
        raise ValueError('E_QUERY_CURRENT_SCOPE')
    selected, premises, refs = _candidates(receipt, table, edges, binding)
    if selected != pack['assertions'] or premises != pack['premises']:
        raise ValueError('E_PACK_ASSERTION_OR_DERIVATION')
    if receipt['exclusions'] != _exclusions(outside, reasons, table, edges, receipt, binding):
        raise ValueError('E_RETRIEVAL_CURRENT_EXCLUSIONS')
    _check_embedding_scope(receipt, nodes)
    validate_receipt(receipt, execution=True)
    expected = {(ref['source_id'], ref['unit_id']) for ref in refs + task['required_units']}
    if expected != {(unit['source_id'], unit['unit_id']) for unit in pack['units']}:
        raise ValueError('E_PACK_SOURCE_CLOSURE')
    for unit in pack['units']:
        if unit['source_id'] not in policy['allowed_source_ids']:
            raise ValueError('E_PACK_ACCESS')
        if indexing.reopen(doc, root, {'source_id': unit['source_id'], 'unit_id': unit['unit_id']}) != unit:
            raise ValueError('E_PACK_SOURCE')
    if len(c.canonical(pack)) > task['max_bytes']:
        raise ValueError('E_PACK_BUDGET')
    if task['require_graph'] or receipt['backend'] == 'SEMANTICA_OBSERVED':
        from .worker_client import WorkerClient
        if not isinstance(worker, WorkerClient):
            raise ValueError('E_GRAPH_REQUIRED_FRESH_WORKER')
        fresh = retrieve(doc, root, policy, task, binding['query_text'], worker,
                         binding['max_hops'], binding['seeds'], binding['max_visits'], binding['max_results'],
                         binding['direction'], binding['embedding_mode'])
        if fresh != pack:
            raise ValueError('E_GRAPH_REPLAY_MISMATCH')
    return pack
