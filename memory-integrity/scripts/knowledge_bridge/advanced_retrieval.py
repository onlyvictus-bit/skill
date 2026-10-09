"""Pinned Semantica community/global/DRIFT discovery over an authorized graph.

Only authored node/edge candidates leave this adapter. Generated executive
strings and upstream 'verified' terminology never confer source authority.
"""
from collections import deque
import math

from . import contracts as c


STRATEGIES = {'community', 'global', 'drift'}


def _bounds(direction, seeds, max_hops, max_visits, max_results):
    if direction not in {'outgoing', 'incoming', 'both'}:
        raise ValueError('E_QUERY_DIRECTION')
    c.integer(seeds, 1, 100, 'seeds')
    c.integer(max_hops, 0, 8, 'hops')
    c.integer(max_visits, 1, 10000, 'visits')
    c.integer(max_results, 1, 1000, 'results')


def traverse(seed_items, neighbors, max_hops, max_visits, max_results):
    """Same deterministic breadth-first limits used by ordinary bridge retrieval."""
    queue = deque((i, score, [i], []) for i, score in seed_items)
    seen, results, limits = set(), [], []
    while queue:
        ident, score, path, edge_ids = queue.popleft()
        if ident in seen:
            continue
        if len(seen) >= max_visits:
            limits.append('max_visits')
            break
        if len(results) >= max_results:
            limits.append('max_results')
            break
        seen.add(ident)
        results.append({'id': ident, 'score': score, 'path': path, 'edge_ids': edge_ids})
        if len(path) - 1 < max_hops:
            for target, edge in sorted(set(neighbors(ident))):
                if target not in seen:
                    queue.append((target, score * .9, path + [target], edge_ids + [edge]))
    return results, sorted(set(limits))


def retrieve(nodes, edges, query_text, strategy='community', embedding_mode='lexical',
             direction='outgoing', seeds=1, max_hops=2, max_visits=100,
             max_results=50, vectors=None, query_vector=None, embedding_metadata=None):
    if strategy not in STRATEGIES:
        raise ValueError('E_ADVANCED_STRATEGY')
    _bounds(direction, seeds, max_hops, max_visits, max_results)
    c.string(query_text, 'query text')
    if vectors is not None:
        try:
            if query_vector is None or not isinstance(embedding_metadata, dict) or len(vectors) != len(nodes):
                raise ValueError('missing prepared vector basis')
            dimension = c.integer(len(query_vector), 1, 4096, 'dimension')
            if embedding_metadata.get('dimension') != dimension:
                raise ValueError('metadata dimension')
            vectors = [c.vector(vector, dimension) for vector in vectors]
            query_vector = c.vector(query_vector, dimension)
        except (ValueError, TypeError) as exc:
            raise ValueError('E_ADVANCED_VECTOR_BASIS') from exc
    from .offline_engine import search_vectors, validate_types
    validate_types(nodes, edges)
    from semantica.kg.community_hierarchy import CommunityHierarchyBuilder
    from semantica.kg.community_summarizer import CommunitySummarizer
    from semantica.context.global_retriever import GlobalGraphRetriever
    from semantica.context.drift_search import DriftSearchEngine
    if vectors is None:
        vectors, query_vector, embedding_metadata = search_vectors(nodes, query_text, embedding_mode)
    table = {n['id']: n for n in nodes}
    graph = {'nodes': [dict(id=n['id'], name=n['id'], description=n['text']) for n in nodes],
             'edges': [dict(id=e['id'], source=e['subject'], target=e['object'],
                            type=e['predicate'], description=e['subject'] + ' ' + e['predicate'] + ' ' + e['object'])
                       for e in edges]}
    hierarchy = CommunityHierarchyBuilder(seed=42, max_levels=4, directed=True).build(graph)
    if len(hierarchy) > 512:
        raise ValueError('E_COMMUNITY_LIMIT')
    reports = CommunitySummarizer(llm=None, cache_enabled=False).summarize_hierarchy(
        hierarchy, graph=graph, use_cache=False)
    vector_table = dict(zip(table, vectors))
    scores = {ident: math.fsum(float(a) * float(b) for a, b in zip(vector, query_vector))
              for ident, vector in vector_table.items()}
    # Enrich the real Semantica topology reports with exact source-bound findings.
    # No model or free-text entailment is represented by these copied assertions.
    for report in reports.values():
        report.findings = [{'summary': table[i]['text'], 'explanation': 'Source node ' + i,
                            'node_id': i, 'source_units': table[i]['source_units']}
                           for i in sorted(report.member_entities)]
        report.embedding = [math.fsum(vector_table[i][j] for i in report.member_entities)
                            / len(report.member_entities) for j in range(len(query_vector))]
    report_payload = {i: r.to_dict() for i, r in sorted(reports.items())}
    used, admissible_edges = set(), {e['id'] for e in edges}
    selected_ids = set()
    extra = {}
    if strategy == 'community':
        ranked = sorted(reports.values(), key=lambda r: (
            -math.fsum(a * b for a, b in zip(r.embedding, query_vector)), r.community_id))
        for report in ranked:
            used.add(report.community_id)
            selected_ids.update(report.member_entities)
            if len(selected_ids) >= seeds:
                break
    elif strategy == 'global':
        result = GlobalGraphRetriever(reports=list(reports.values()), hierarchy=hierarchy,
                                      llm=None, max_workers=2, timeout=10,
                                      max_context_tokens=4000).search(query_text, query_embedding=query_vector)
        used.update(result.community_reports_used)
        for point in result.key_points:
            selected_ids.update(i for i in point.entities if i in table)
        extra['key_points_retained'] = len(result.key_points)
    else:
        result = DriftSearchEngine(knowledge_graph=graph, reports=list(reports.values()),
                                   hierarchy=hierarchy, llm=None, embedder=None,
                                   max_depth=max(1, max_hops), drift_threshold=.1).search(query_text)
        used.update(result.global_reports_used)
        selected_ids.update(i for f in result.facets_explored for i in f.target_entities if i in table)
        admissible_edges = {fact['edge_id'] for fact in result.verified_local_contexts
                            if fact.get('edge_id') in {e['id'] for e in edges}}
        extra.update(drift_alignment='LEXICAL_HEURISTIC', pruned_edges=result.pruned_fact_count,
                     upstream_depth=result.depth_reached)
    # No invented vector fallback: empty advanced discoveries remain empty.
    selected_seeds = sorted(((i, scores[i]) for i in selected_ids), key=lambda p: (-p[1], p[0]))[:seeds]
    def neighbors(ident):
        for edge in edges:
            if edge['id'] not in admissible_edges:
                continue
            if direction in {'outgoing', 'both'} and edge['subject'] == ident:
                yield edge['object'], edge['id']
            if direction in {'incoming', 'both'} and edge['object'] == ident:
                yield edge['subject'], edge['id']
    results, limits = traverse(selected_seeds, neighbors, max_hops, max_visits, max_results)
    diagnostics = {'strategy': strategy, 'report_kind': 'SOURCE_BOUND_EXTRACTIVE',
                   'semantic_truth': 'UNVERIFIED', 'provider_calls': 0,
                   'community_count': len(hierarchy), 'levels': hierarchy.levels,
                   'hierarchy_digest': c.digest(c.canonical(hierarchy.to_dict())),
                   'reports_digest': c.digest(c.canonical(report_payload)),
                   'communities_used': sorted(used),
                   'communities_excluded': sorted(set(reports) - used),
                   'synthesized_answer_discarded': strategy in {'global', 'drift'}, **extra}
    return {'results': results, 'limits_reached': limits,
            'embedding_metadata': embedding_metadata, 'diagnostics': diagnostics}

