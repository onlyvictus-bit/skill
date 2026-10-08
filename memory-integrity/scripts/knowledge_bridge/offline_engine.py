"""Bounded local ranking, affirmed prose grammar, and project-2 type checks.

Only the caller's already-authorized corpus is fitted. Lexical vectors are not
semantic embeddings; LSA is a corpus-trained latent representation with no
claim of entailment or generally better retrieval. Optional dependencies are
loaded inside the requested operation, never when this module is imported.
"""
import math
import re

from . import contracts as c


def _types(*names):
    return frozenset(names)


_ALL = frozenset(c.NODE_TYPES)
_FACTS = _types('Requirement', 'Decision', 'Assertion', 'AuditFinding')
_CODE = _types('Component', 'Symbol', 'Interface')

# One matrix is consumed by host checks and rendered into worker SHACL shapes.
# project-1 imports retain their original structural semantics elsewhere.
TYPE_RULES = {
    'DEFINED_IN': (_ALL - _types('SourceVersion'), _types('SourceVersion', 'SourceUnit', 'Component', 'Symbol')),
    'REFERENCES': (_ALL, _ALL),
    'DEPENDS_ON': (_CODE | _FACTS | _types('TestCase'), _CODE | _FACTS | _types('SourceUnit', 'TestCase')),
    'IMPLEMENTS': (_CODE, _types('Requirement', 'Interface', 'Component')),
    'TESTS': (_types('TestCase', 'TestRun'), _CODE | _types('Requirement', 'Assertion')),
    'SUPPORTED_BY': (_CODE | _FACTS | _types('TestCase', 'TestRun'), _ALL),
    'CONTRADICTS': (_FACTS, _FACTS),
    'SUPERSEDES': (_FACTS | _types('SourceVersion'), _FACTS | _types('SourceVersion')),
    'DERIVED_FROM': (_ALL, _ALL),
}


def validate_types(nodes, edges, shacl=False):
    """Check project-2 endpoints/types; optionally require genuine SHACL success."""
    if type(shacl) is not bool or not isinstance(nodes, list) or not 1 <= len(nodes) <= 10000:
        raise ValueError('E_ONTOLOGY_NODE_SCOPE')
    if not isinstance(edges, list) or len(edges) > 40000:
        raise ValueError('E_ONTOLOGY_EDGE_SCOPE')
    table = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get('type'), str) or node['type'] not in _ALL:
            raise ValueError('E_ONTOLOGY_NODE_TYPE')
        ident = c.identity(node.get('id'), 'ontology node')
        if ident in table:
            raise ValueError('E_ONTOLOGY_DUPLICATE_NODE')
        table[ident] = node['type']
    edge_ids = set()
    for edge in edges:
        if not isinstance(edge, dict) or not isinstance(edge.get('predicate'), str) or edge['predicate'] not in TYPE_RULES:
            raise ValueError('E_ONTOLOGY_PREDICATE')
        ident = c.identity(edge.get('id'), 'ontology edge')
        if ident in edge_ids:
            raise ValueError('E_ONTOLOGY_DUPLICATE_EDGE')
        edge_ids.add(ident)
        subject = c.identity(edge.get('subject'), 'ontology subject')
        object_ = c.identity(edge.get('object'), 'ontology object')
        if subject not in table or object_ not in table:
            raise ValueError('E_ONTOLOGY_ENDPOINT')
        domains, ranges = TYPE_RULES[edge['predicate']]
        if table[subject] not in domains:
            raise ValueError('E_ONTOLOGY_DOMAIN: ' + edge['predicate'])
        if table[object_] not in ranges:
            raise ValueError('E_ONTOLOGY_RANGE: ' + edge['predicate'])
    result = {'ontology': 'project-2', 'type_constraints': 'HOST_VALIDATED', 'shacl': 'UNVERIFIED'}
    if shacl:
        _require_shacl(nodes, edges)
        result['shacl'] = 'CONFORMS'
    return result


def _require_shacl(nodes, edges):
    try:
        from rdflib import Graph, Namespace, URIRef, Literal, RDF
        from semantica.ontology.ontology_validator import run_shacl_validation
    except ImportError as exc:
        raise ValueError('E_SHACL_UNAVAILABLE') from exc
    ns = Namespace('urn:memory-integrity:')
    graph = Graph()
    for node in nodes:
        uri = URIRef('urn:node:' + node['id'])
        graph.add((uri, RDF.type, ns.KnowledgeNode))
        graph.add((uri, ns.nodeType, Literal(node['type'])))
    for edge in edges:
        uri = URIRef('urn:edge:' + edge['id'])
        graph.add((uri, RDF.type, ns.KnowledgeEdge))
        graph.add((uri, RDF.type, ns['Edge' + edge['predicate']]))
        graph.add((uri, ns.subject, URIRef('urn:node:' + edge['subject'])))
        graph.add((uri, ns.object, URIRef('urn:node:' + edge['object'])))
        graph.add((uri, ns.predicate, Literal(edge['predicate'])))
    shapes = ['@prefix sh: <http://www.w3.org/ns/shacl#> .', '@prefix mi: <urn:memory-integrity:> .']
    predicates = ' '.join('"' + name + '"' for name in sorted(TYPE_RULES))
    shapes.append('mi:EdgeShape a sh:NodeShape; sh:targetClass mi:KnowledgeEdge; '
                  'sh:property [ sh:path mi:predicate; sh:minCount 1; sh:maxCount 1; sh:in (' + predicates + ') ]; '
                  'sh:property [ sh:path mi:subject; sh:minCount 1; sh:maxCount 1; sh:class mi:KnowledgeNode ]; '
                  'sh:property [ sh:path mi:object; sh:minCount 1; sh:maxCount 1; sh:class mi:KnowledgeNode ] .')
    for predicate, (domains, ranges) in sorted(TYPE_RULES.items()):
        domain_values = ' '.join('"' + value + '"' for value in sorted(domains))
        range_values = ' '.join('"' + value + '"' for value in sorted(ranges))
        shapes.append('mi:' + predicate + 'Shape a sh:NodeShape; sh:targetClass mi:Edge' + predicate + '; '
                      'sh:property [ sh:path (mi:subject mi:nodeType); sh:minCount 1; sh:maxCount 1; sh:in (' + domain_values + ') ]; '
                      'sh:property [ sh:path (mi:object mi:nodeType); sh:minCount 1; sh:maxCount 1; sh:in (' + range_values + ') ] .')
    try:
        result = run_shacl_validation(graph.serialize(format='turtle'), '\n'.join(shapes),
                                      data_graph_format='turtle', shacl_format='turtle')
    except ImportError as exc:
        raise ValueError('E_SHACL_UNAVAILABLE') from exc
    if not result.conforms:
        raise ValueError('E_SHACL_NONCONFORMING')


def _words(text):
    # Preserve exact source text elsewhere; this normalization is ranking only.
    return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text).replace('_', ' ')


def search_vectors(nodes, query_text, mode='lexical'):
    """Fit authorized text and produce vectors consumable by VectorRetriever.

    Returns (vectors in input order, query vector, fixed-key metadata). Corpus
    identity, fit parameters and actual sklearn version bind model identity.
    No model weights, provider APIs, or supplied vectors are consulted.
    """
    if mode not in ('lexical', 'lsa', 'hybrid'):
        raise ValueError('E_OFFLINE_SEARCH_MODE')
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 10000:
        raise ValueError('E_OFFLINE_CORPUS_SCOPE')
    c.string(query_text, 'query text')
    table = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError('E_OFFLINE_CORPUS_NODE')
        ident = c.identity(node.get('id'), 'search node')
        text = c.string(node.get('text'), 'search text')
        if ident in table:
            raise ValueError('E_OFFLINE_DUPLICATE_NODE')
        table[ident] = text
    corpus = [{'id': ident, 'text': table[ident]} for ident in sorted(table)]
    if len(c.canonical(corpus)) + len(query_text.encode('utf-8')) > c.MAX_MESSAGE:
        raise ValueError('E_MESSAGE_LIMIT')
    try:
        import numpy as np
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.preprocessing import normalize
    except ImportError as exc:
        raise ValueError('E_OFFLINE_SEARCH_UNAVAILABLE') from exc
    feature_limit = 2048
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                               token_pattern=r'(?u)\b\w+\b', max_features=feature_limit)
    try:
        lexical = vectorizer.fit_transform([_words(row['text']) for row in corpus])
    except ValueError as exc:
        raise ValueError('E_OFFLINE_EMPTY_FEATURES') from exc
    if any(count == 0 for count in lexical.getnnz(axis=1)):
        raise ValueError('E_OFFLINE_DOCUMENT_NO_LEXICAL_SUPPORT')
    query_lexical = vectorizer.transform([_words(query_text)])
    if query_lexical.nnz == 0:
        raise ValueError('E_QUERY_NO_LEXICAL_SUPPORT')
    feature_count = lexical.shape[1]
    components = 0
    lexical_weight = 1.0
    dimension = feature_count
    if mode != 'lexical':
        components = min(64, len(corpus) - 1, feature_count - 1)
        if components < 1:
            raise ValueError('E_LATENT_CORPUS_SCOPE')
        dimension = components if mode == 'lsa' else feature_count + components
        lexical_weight = 0.0 if mode == 'lsa' else 0.8
    if len(corpus) * dimension > 500000:
        raise ValueError('E_OFFLINE_VECTOR_SCOPE')
    if mode == 'lexical':
        fitted = lexical.toarray()
        query = query_lexical.toarray()[0]
        algorithm = 'TF-IDF lexical cosine'
    else:
        latent = TruncatedSVD(n_components=components, random_state=0, n_iter=7)
        fitted_latent = normalize(latent.fit_transform(lexical))
        query_latent = normalize(latent.transform(query_lexical))[0]
        if mode == 'lsa':
            if any(np.linalg.norm(row) < 1e-12 for row in fitted_latent) or np.linalg.norm(query_latent) < 1e-12:
                raise ValueError('E_LATENT_NO_SUPPORT')
            fitted, query = fitted_latent, query_latent
            algorithm = 'TF-IDF + truncated SVD LSA cosine'
        else:
            fitted = np.concatenate((math.sqrt(lexical_weight) * lexical.toarray(),
                                     math.sqrt(1 - lexical_weight) * fitted_latent), axis=1)
            query = np.concatenate((math.sqrt(lexical_weight) * query_lexical.toarray()[0],
                                    math.sqrt(1 - lexical_weight) * query_latent))
            algorithm = 'Weighted lexical cosine + corpus LSA cosine'
    try:
        vectors = [c.vector(row.tolist(), dimension) for row in fitted]
        query_vector = c.vector(query.tolist(), dimension)
    except ValueError as exc:
        raise ValueError('E_LATENT_ZERO_OR_NONFINITE_VECTOR') from exc
    by_id = dict(zip((row['id'] for row in corpus), vectors))
    vectors = [by_id[node['id']] for node in nodes]
    fit_scope_digest = c.digest(c.canonical(corpus))
    configuration = {'mode': mode, 'feature_limit': feature_limit, 'ngram_range': [1, 2],
                     'sublinear_tf': True, 'normalization': 'split underscores/camelcase; L2',
                     'token_pattern': r'(?u)\b\w+\b', 'lsa_components': components,
                     'random_state': 0, 'n_iter': 7, 'lexical_weight': lexical_weight,
                     'fit_scope_digest': fit_scope_digest, 'sklearn_version': sklearn.__version__}
    metadata = {'model': 'offline-' + mode + '-v1:' + c.digest(c.canonical(configuration)),
                'dimension': dimension, 'evidence_class': 'HOST_OBSERVED', 'mode': mode,
                'algorithm': algorithm, 'semantic_quality': 'UNVERIFIED',
                'fit_scope_digest': fit_scope_digest, 'sklearn_version': sklearn.__version__,
                'feature_count': feature_count, 'document_count': len(corpus),
                'lsa_components': components, 'feature_limit': feature_limit,
                'lexical_weight': lexical_weight, 'query_nonzero_features': query_lexical.nnz}
    if len(c.canonical({'vectors': vectors, 'query': query_vector, 'metadata': metadata})) > c.MAX_MESSAGE:
        raise ValueError('E_MESSAGE_LIMIT')
    return vectors, query_vector, metadata


_VERBS = {
    'depends on': 'DEPENDS_ON', 'references': 'REFERENCES', 'implements': 'IMPLEMENTS',
    'tests': 'TESTS', 'is supported by': 'SUPPORTED_BY', 'contradicts': 'CONTRADICTS',
    'supersedes': 'SUPERSEDES', 'is derived from': 'DERIVED_FROM', 'is defined in': 'DEFINED_IN',
}
_IDENTIFIER = r'[A-Za-z][A-Za-z0-9_:-]*(?:\.[A-Za-z][A-Za-z0-9_:-]*)*'
_AFFIRMED = re.compile(r'^[ \t]*(?P<subject>' + _IDENTIFIER + r')[ \t]+'
                       r'(?P<verb>' + '|'.join(re.escape(verb) for verb in _VERBS) + r')[ \t]+'
                       r'(?P<object>' + _IDENTIFIER + r')\.?[ \t]*(?=\r?$)', re.MULTILINE | re.IGNORECASE)

_NEGATIVE_SUBJECTS = frozenset(('nothing', 'nobody', 'none', 'never', 'neither'))


def _relation_line_starts(text):
    """Accept only a whole relation DSL document, without context inference."""
    eligible = set()
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.strip():
            # Never select a sentence from surrounding context. A header,
            # disclaimer, example, fence, clause or unsupported line rejects
            # the entire submitted document, even across blank boundaries.
            match = _AFFIRMED.fullmatch(line.rstrip('\r\n'))
            if line.startswith((' ', '\t')) or match is None or match.group('subject').lower() in _NEGATIVE_SUBJECTS:
                return None
            eligible.add(offset)
        offset += len(line)
    return eligible


def extract_prose(text):
    """Observe a complete document in a narrow affirmative relationship DSL.

    Every nonblank line must be a standalone unindented identifier relationship.
    Mixed document context, conditional, negative, quoted, example, indented or
    unsupported text refuses all extraction. No natural-language document is
    partially interpreted; the original sources remain navigation evidence.
    This is not free-text entailment. Confidence is upstream fixed heuristic.
    Returned spans are independently checked UTF-8 byte ranges in original text.
    """
    if not isinstance(text, str):
        raise ValueError('E_PROSE_TEXT')
    if len(text.encode('utf-8')) > c.MAX_MESSAGE:
        raise ValueError('E_MESSAGE_LIMIT')
    eligible = _relation_line_starts(text)
    if eligible is None:
        return []
    matches = [match for match in _AFFIRMED.finditer(text) if match.start() in eligible]
    if len(matches) > 10000:
        raise ValueError('E_PROSE_SCOPE')
    if not matches:
        return []
    try:
        from semantica.semantic_extract.methods import extract_entities_regex, extract_relations_regex
    except ImportError as exc:
        raise ValueError('E_PROSE_EXTRACTOR_UNAVAILABLE') from exc
    positions = sorted({position for match in matches for position in
                        (match.start(), match.end(), match.start('subject'), match.end('subject'),
                         match.start('object'), match.end('object'))})
    byte_positions = {}
    previous = byte_count = 0
    for position in positions:
        byte_count += len(text[previous:position].encode('utf-8'))
        byte_positions[position] = byte_count
        previous = position
    out = []
    for match in matches:
        subject, object_ = match.group('subject'), match.group('object')
        c.identity(subject, 'prose subject')
        c.identity(object_, 'prose object')
        statement = match.group(0)
        predicate = _VERBS[match.group('verb').lower()]
        literal_entities = '(?:' + '|'.join(re.escape(name) for name in sorted({subject, object_}, key=len, reverse=True)) + ')'
        entities = extract_entities_regex(statement, patterns={'IDENTIFIER': literal_entities})
        for entity in entities:
            if statement[entity.start_char:entity.end_char] != entity.text:
                raise ValueError('E_PROSE_ENTITY_SPAN')
        actual = extract_relations_regex(statement, entities, patterns={predicate: [_AFFIRMED.pattern]})
        if len(actual) != 1 or actual[0].subject.text != subject or actual[0].object.text != object_ or actual[0].predicate != predicate:
            raise ValueError('E_PROSE_BACKEND_DISAGREEMENT')
        relation = actual[0]
        out.append({'subject': subject, 'predicate': predicate, 'object': object_,
                    'span': [byte_positions[match.start()], byte_positions[match.end()]],
                    'subject_span': [byte_positions[match.start('subject')], byte_positions[match.end('subject')]],
                    'object_span': [byte_positions[match.start('object')], byte_positions[match.end('object')]],
                    'text': statement, 'polarity': 'positive', 'conditions': [],
                    'method': 'semantica-relation-dsl-verified-v1', 'confidence': relation.confidence,
                    'confidence_source': 'HEURISTIC_UNCALIBRATED'})
    return out
