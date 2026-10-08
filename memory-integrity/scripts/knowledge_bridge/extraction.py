"""Deterministic local Python syntax projection, never source execution.

AST names are conservative navigation relationships, not runtime call proof.
Prose interpretation is left unqualified for the isolated semantic extractor.
Cached fragments contain only per-file syntax; every cross-file lookup is fresh.
"""
import ast
import copy
import hashlib
import math
from pathlib import PurePosixPath
import re
import sys

from . import contracts as c

DIMENSION = 256
EXTRACTOR = {'name': 'local-python-ast', 'version': '1.0.3',
             'python_grammar': '%d.%d' % sys.version_info[:2]}
MAX_AST_NODES = 50000


def vectorize(text):
    """Signed hashed word/subword features; lexical, not semantic embeddings."""
    if not isinstance(text, str): raise ValueError('E_VECTOR_TEXT')
    features = [0.0] * DIMENSION
    tokens = re.findall(r'\w+', text.casefold(), flags=re.UNICODE)
    for token in tokens or ['<empty>']:
        parts = re.findall(r'[a-z]+|\d+|[^\x00-\x7f]+', token) or [token]
        for value in [token, *parts]:
            hashed = hashlib.sha256(value.encode('utf-8')).digest()
            features[int.from_bytes(hashed[:4], 'big') % DIMENSION] += 1 if hashed[4] & 1 else -1
    norm = math.hypot(*features)
    if not norm: features[0] = 1.0; norm = 1.0
    return [value / norm for value in features]


def _id(kind, *parts):
    return kind + ':' + c.digest(c.canonical(list(parts)))[:40]


def _refs(source_id, source, span):
    rows = [{'source_id': source_id, 'unit_id': unit['id']}
            for unit in source['manifest']['units']
            if unit['range'][0] < span[1] and unit['range'][1] > span[0]]
    if not rows: raise ValueError('E_EXTRACTION_SOURCE_SPAN')
    return rows


def _node(ident, kind, text, refs):
    return {'id': ident, 'type': kind, 'text': text, 'source_units': refs,
            'polarity': 'positive', 'conditions': [], 'derivation': None,
            'valid_from': None, 'valid_until': None, 'review_status': 'unreviewed',
            'vector': vectorize(text)}


def _edge(subject, predicate, obj, refs, conditions, location):
    return {'id': _id('edge', subject, predicate, obj, location), 'subject': subject,
            'predicate': predicate, 'object': obj, 'source_units': refs,
            'conditions': conditions, 'valid_from': None, 'valid_until': None}


def _module(path):
    parts = list(PurePosixPath(path).with_suffix('').parts)
    if parts and parts[-1] == '__init__': parts.pop()
    return '.'.join(parts) or '__root__'


def _dotted(node):
    if isinstance(node, ast.Name): return [node.id]
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return parent + [node.attr] if parent else None
    return None


def _parameters(node):
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)): return []
    args = node.args
    return [a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs,
                           *([args.vararg] if args.vararg else []),
                           *([args.kwarg] if args.kwarg else [])]]


class _Fragment(ast.NodeVisitor):
    def __init__(self, source_id, source, raw, repository):
        self.source_id, self.source, self.raw = source_id, source, raw
        self.repository, self.module = repository, _module(source['path'])
        self.component = _id('component', repository, source['path'])
        self.nodes = [_node(self.component, 'Component', 'Python module ' + self.module,
                            _refs(source_id, source, [0, len(raw)]))]
        self.symbols, self.edges, self.imports, self.calls, self.diagnostics = [], [], [], [], []
        self.mutations = []
        self.scopes = {'': {'kind': 'module', 'parent': None, 'bindings': {}, 'star_import': False}}
        self.current = ''
        self.offsets = [0]
        for line in raw.splitlines(keepends=True): self.offsets.append(self.offsets[-1] + len(line))

    def span(self, node):
        start = self.offsets[node.lineno - 1] + node.col_offset
        end = self.offsets[node.end_lineno - 1] + node.end_col_offset
        if not 0 <= start < end <= len(self.raw): raise ValueError('E_EXTRACTION_AST_SPAN')
        return [start, end]

    def diag(self, kind, node, detail):
        self.diagnostics.append({'kind': kind, 'source_id': self.source_id,
                                 'range': self.span(node), 'detail': detail})

    def bind(self, name, value):
        entries = self.scopes[self.current]['bindings'].setdefault(name, [])
        if value not in entries: entries.append(value)

    def declaration(self, node, kind):
        parent = self.current
        scope = '.'.join(x for x in (parent, node.name) if x)
        qualified = self.module + '.' + scope
        span = self.span(node)
        ident = (_id('symbol', self.repository, self.source['path'], scope, span[0])
                 if scope in self.scopes else _id('symbol', self.repository, self.source['path'], scope))
        self.bind(node.name, {'kind': 'symbol', 'id': ident})
        refs = _refs(self.source_id, self.source, span)
        self.symbols.append({'id': ident, 'qualified_name': qualified, 'name': node.name,
                             'kind': kind, 'scope': scope, 'source_id': self.source_id,
                             'range': span, 'span_sha256': c.digest(self.raw[span[0]:span[1]])})
        text = 'Python ' + kind + ' ' + qualified
        doc = ast.get_docstring(node, clean=False)
        if doc: text += ': ' + doc[:1024]
        self.nodes.append(_node(ident, 'Symbol', text, refs))
        self.edges.append(_edge(ident, 'DEFINED_IN', self.component, refs,
                                ['python-declaration'], [self.source_id, *span]))
        # Decorators and defaults execute in the outer lexical scope.
        for decorator in node.decorator_list: self.visit(decorator)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in [*node.args.defaults, *[d for d in node.args.kw_defaults if d]]: self.visit(default)
        elif isinstance(node, ast.ClassDef):
            for base in node.bases: self.visit(base)
            for keyword in node.keywords: self.visit(keyword.value)
        # Duplicate definitions cannot establish an unambiguous target.
        if scope in self.scopes:
            self.diag('AMBIGUOUS_SYMBOL', node, qualified)
            self.bind(node.name, {'kind': 'shadowed'})
            scope += '@' + str(span[0])
        self.scopes[scope] = {'kind': 'class' if kind == 'class' else 'function',
                              'parent': parent, 'bindings': {}, 'star_import': False,
                              'symbol_id': ident}
        self.current = scope
        for name in _parameters(node): self.bind(name, {'kind': 'shadowed'})
        for child in node.body: self.visit(child)
        self.current = parent

    def visit_FunctionDef(self, node): self.declaration(node, 'function')
    def visit_AsyncFunctionDef(self, node): self.declaration(node, 'async-function')
    def visit_ClassDef(self, node): self.declaration(node, 'class')

    def visit_Import(self, node):
        for alias in node.names:
            spec = {'kind': 'import', 'module': alias.name, 'member': None,
                    'binding': alias.asname or alias.name.split('.')[0],
                    'bound_module': alias.name if alias.asname else alias.name.split('.')[0],
                    'scope': self.current, 'source_id': self.source_id,
                    'range': self.span(node), 'component': self.component}
            self.imports.append(spec); self.bind(spec['binding'], spec)

    def visit_ImportFrom(self, node):
        base = self.module.split('.') if self.source['path'].endswith('/__init__.py') else self.module.split('.')[:-1]
        if node.level:
            if node.level > len(base): module = None
            else: module = '.'.join(base[:len(base) - node.level + 1] + (node.module.split('.') if node.module else []))
        else: module = node.module
        for alias in node.names:
            if alias.name == '*':
                self.scopes[self.current]['star_import'] = True
                self.diag('UNRESOLVED_IMPORT', node, 'wildcard imports cannot establish named targets')
                continue
            spec = {'kind': 'import', 'module': module, 'member': alias.name,
                    'binding': alias.asname or alias.name, 'bound_module': module,
                    'scope': self.current, 'source_id': self.source_id,
                    'range': self.span(node), 'component': self.component}
            self.imports.append(spec); self.bind(spec['binding'], spec)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)): self.bind(node.id, {'kind': 'shadowed'})

    def mutation(self, node, receiver):
        if receiver:
            self.mutations.append({'scope': self.current, 'receiver': receiver})
            self.diag('DYNAMIC_BINDING', node, 'attribute mutation prevents static module-call qualification')

    def visit_Attribute(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)): self.mutation(node, _dotted(node))
        self.generic_visit(node)

    def visit_Subscript(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)): self.mutation(node, _dotted(node.value))
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name: self.bind(node.name, {'kind': 'shadowed'})
        self.generic_visit(node)

    def visit_Global(self, node):
        for name in node.names: self.bind(name, {'kind': 'shadowed'})
        self.diag('DYNAMIC_BINDING', node, 'global rebinding requires runtime analysis')

    def visit_Nonlocal(self, node):
        for name in node.names: self.bind(name, {'kind': 'shadowed'})
        self.diag('DYNAMIC_BINDING', node, 'nonlocal rebinding requires runtime analysis')

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in {'setattr', 'delattr'} and node.args:
            self.mutation(node, _dotted(node.args[0]))
        self.calls.append({'source_id': self.source_id, 'range': self.span(node),
                           'scope': self.current, 'callee': _dotted(node.func),
                           'subject': self.scopes[self.current].get('symbol_id', self.component)})
        self.generic_visit(node)

    def visit_Lambda(self, node):
        # Anonymous/closure scopes are intentionally not resolved.
        self.diag('DYNAMIC_BINDING', node, 'lambda calls require separate scope analysis')

    def visit_ListComp(self, node):
        # Assignment expressions in comprehensions bind the enclosing scope.
        # Other comprehension-local names and calls remain unobserved.
        for child in ast.walk(node):
            if isinstance(child, ast.NamedExpr) and isinstance(child.target, ast.Name):
                self.bind(child.target.id, {'kind': 'shadowed'})
        self.diag('DYNAMIC_BINDING', node, 'comprehension scope not resolved')
    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def result(self):
        return {'module': self.module, 'component': self.component, 'nodes': self.nodes,
                'symbols': self.symbols, 'edges': self.edges, 'imports': self.imports,
                'calls': self.calls, 'mutations': self.mutations, 'scopes': self.scopes, 'diagnostics': self.diagnostics}


def _fragment(source_id, source, raw, repository):
    if not source['path'].endswith('.py'):
        diagnostics = [{'kind': 'UNSUPPORTED_FORMAT', 'source_id': source_id,
                        'range': [0, len(raw)], 'detail': 'structural extraction supports Python only'}]
        text = raw.decode('utf-8')
        if re.search(r'\b(never|not|unless|except|cannot|forbidden)\b', text, re.I):
            diagnostics.append({'kind': 'SEMANTIC_REVIEW_REQUIRED', 'source_id': source_id,
                                'range': [0, len(raw)], 'detail': 'negated or conditional prose is not flattened into assertions'})
        navigation = []
        for unit in source['manifest']['units']:
            start, end = unit['range']
            if not raw[start:end].decode('utf-8').strip(): continue
            refs = [{'source_id': source_id, 'unit_id': unit['id']}]
            node = _node(_id('unit', repository, source['path'], unit['id']), 'SourceUnit',
                         raw[start:end].decode('utf-8'), refs)
            node['polarity'] = 'unknown'
            navigation.append(node)
        return {'status': 'UNSUPPORTED', 'module': None, 'component': None,
                'nodes': navigation, 'symbols': [], 'edges': [], 'imports': [], 'calls': [], 'mutations': [],
                'scopes': {}, 'diagnostics': diagnostics}
    try:
        tree = ast.parse(raw.decode('utf-8'), filename=source['path'])
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES: raise ValueError('AST node scope exceeded')
        parser = _Fragment(source_id, source, raw, repository); parser.visit(tree)
        return dict(parser.result(), status='OBSERVED')
    except (SyntaxError, RecursionError, ValueError) as exc:
        return {'status': 'FAILED', 'module': _module(source['path']), 'component': None,
                'nodes': [], 'symbols': [], 'edges': [], 'imports': [], 'calls': [], 'mutations': [], 'scopes': {},
                'diagnostics': [{'kind': 'PARSE_FAILED', 'source_id': source_id,
                                 'range': [0, len(raw)], 'detail': type(exc).__name__ + ': ' + str(exc)}]}


def _lookup(fragment, scope, name):
    while scope is not None:
        row = fragment['scopes'][scope]
        if row['star_import']: return None
        values = row['bindings'].get(name)
        if values: return values[0] if len(values) == 1 else None
        parent = row['parent']
        # Neither functions nor nested classes close over class-local names.
        while parent is not None and fragment['scopes'][parent]['kind'] == 'class':
            parent = fragment['scopes'][parent]['parent']
        scope = parent
    return None


def _combine(fragments, sources):
    nodes, edges, symbols, diagnostics = [], [], [], []
    modules, qualified = {}, {}
    for source_id, fragment in fragments.items():
        nodes.extend(fragment['nodes']); edges.extend(fragment['edges'])
        symbols.extend(fragment['symbols']); diagnostics.extend(fragment['diagnostics'])
        if fragment['component']:
            modules.setdefault(fragment['module'], []).append(fragment)
        for symbol in fragment['symbols']: qualified.setdefault(symbol['qualified_name'], []).append(symbol)
    for module, rows in modules.items():
        if len(rows) > 1:
            for row in rows:
                diagnostics.append({'kind': 'AMBIGUOUS_MODULE', 'source_id': row['nodes'][0]['source_units'][0]['source_id'],
                                    'range': None, 'detail': module})

    def member(module, names):
        if len(modules.get(module, [])) != 1: return None
        if not names: return modules[module][0]['component']
        matches = qualified.get(module + '.' + '.'.join(names), [])
        return matches[0]['id'] if len(matches) == 1 else None

    def imported(spec, tail=()):
        module = spec['module']
        if not module: return None
        if spec['member']:
            target = member(module, [spec['member'], *tail])
            submodule = module + '.' + spec['member']
            alternate = member(submodule, list(tail))
            return target if target and not alternate else alternate if alternate and not target else None
        full = [*spec['bound_module'].split('.'), *tail]
        # The longest declared module prefix is the only permissible owner.
        candidates = []
        for count in range(1, len(full) + 1):
            target = member('.'.join(full[:count]), full[count:])
            if target: candidates.append(target)
        return candidates[0] if len(set(candidates)) == 1 and candidates else None

    mutated_modules = set()
    for fragment in fragments.values():
        for mutation in fragment['mutations']:
            binding = _lookup(fragment, mutation['scope'], mutation['receiver'][0])
            if binding and binding['kind'] == 'import' and binding['module']:
                mutated_modules.add(binding['module'])
            elif binding and binding['kind'] == 'symbol':
                mutated_modules.add(fragment['module'])
    mutated_symbols = {symbol['id'] for symbol in symbols
                       if any(symbol['qualified_name'].startswith(module + '.') for module in mutated_modules)}

    for source_id, fragment in fragments.items():
        for spec in fragment['imports']:
            refs = _refs(source_id, sources[source_id], spec['range'])
            module = spec['module']
            target = imported(spec) if spec['member'] else member(module, [])
            if spec['member'] and target:
                target_module = module if len(modules.get(module, [])) == 1 else module + '.' + spec['member']
            else: target_module = module
            if not target or len(modules.get(target_module, [])) != 1:
                diagnostics.append({'kind': 'UNRESOLVED_IMPORT', 'source_id': source_id,
                                    'range': spec['range'], 'detail': '.'.join(x for x in (module, spec['member']) if x) or 'relative import outside declared package'})
                continue
            destination = modules[target_module][0]['component']
            edges.append(_edge(fragment['component'], 'DEPENDS_ON', destination, refs,
                               ['python-static-import'], [source_id, *spec['range'], spec['binding']]))
        for call in fragment['calls']:
            target = None; dotted = call['callee']
            binding = _lookup(fragment, call['scope'], dotted[0]) if dotted else None
            if binding and binding['kind'] == 'symbol' and len(dotted) == 1: target = binding['id']
            elif binding and binding['kind'] == 'import': target = imported(binding, dotted[1:])
            if target and target not in mutated_symbols and any(n['id'] == target and n['type'] == 'Symbol' for n in nodes):
                refs = _refs(source_id, sources[source_id], call['range'])
                edges.append(_edge(call['subject'], 'REFERENCES', target, refs,
                                   ['python-static-call'], [source_id, *call['range']]))
            else:
                diagnostics.append({'kind': 'UNRESOLVED_CALL', 'source_id': source_id,
                                    'range': call['range'], 'detail': '.'.join(dotted) if dotted else 'dynamic callable expression'})
    # Stable order and content, independent of caller source-map ordering.
    return sorted(nodes, key=lambda n: n['id']), sorted(edges, key=lambda e: e['id']), sorted(symbols, key=lambda s: (s['qualified_name'], s['source_id'])), diagnostics


def _projection(nodes, edges):
    return {'schema_version': 2, 'ontology': 'project-2',
            'embedding': {'model': 'local-text-v1', 'dimension': DIMENSION, 'evidence_class': 'HOST_OBSERVED'},
            'nodes': nodes, 'edges': edges}


def _sealed_previous(previous, repository):
    """Reject damaged cache seals and closure; these hashes are not authority."""
    if not isinstance(previous, dict) or previous.get('extractor') != EXTRACTOR or previous.get('repository') != repository:
        return False
    try:
        if previous.get('manifest_digest') != c.digest(c.canonical({k: v for k, v in previous.items() if k != 'manifest_digest'})):
            return False
        fragments, old_sources = {}, {}
        for ident, record in previous['sources'].items():
            c.identity(ident, 'cached source'); c.sha(record['source_sha256']); c.sha(record['unit_manifest_digest'])
            if record['fragment_digest'] != c.digest(c.canonical(record['fragment'])): return False
            units = record['unit_ranges']; seen = set()
            for unit in units:
                c.keys(unit, {'id', 'range'}, 'cached unit'); c.identity(unit['id'], 'cached unit')
                if unit['id'] in seen or not isinstance(unit['range'], list) or len(unit['range']) != 2: return False
                c.integer(unit['range'][0], 0, c.MAX_MESSAGE, 'cached start')
                c.integer(unit['range'][1], unit['range'][0] + 1, c.MAX_MESSAGE, 'cached end')
                seen.add(unit['id'])
            fragments[ident] = record['fragment']; old_sources[ident] = {'manifest': {'units': units}}
        nodes, edges, symbols, diagnostics = _combine(fragments, old_sources)
        return (previous['projection_digest'] == c.digest(c.canonical(_projection(nodes, edges)))
                and previous['symbols'] == symbols and previous['diagnostics'] == diagnostics)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def extract(sources, repository, previous=None, *, root):
    """Project frozen source records; root is explicit and sources never execute.

    ``previous`` is a prior manifest (or complete extract result). Cache reuse
    requires matching source, path, unit manifest, parser, repository and fragment
    hashes. Consumers still validate generations and admissions independently.
    """
    c.string(repository, 'repository'); root = c.ordinary(root, True)
    if not isinstance(sources, dict) or not sources or len(sources) > 1000: raise ValueError('E_SOURCE_SCOPE')
    if previous and 'manifest' in previous: previous = previous['manifest']
    compatible = _sealed_previous(previous, repository)
    fragments, records, reused, parsed = {}, {}, [], []; total = 0
    for source_id in sorted(sources):
        c.identity(source_id, 'source'); source = sources[source_id]
        c.keys(source, {'path', 'authority', 'source_sha256', 'manifest'}, 'extraction source')
        raw = c.within(root, source['path']).read_bytes(); total += len(raw)
        if not raw or total > c.MAX_MESSAGE: raise ValueError('E_SOURCE_SIZE')
        try: raw.decode('utf-8')
        except UnicodeError as exc: raise ValueError('E_EXTRACTION_UTF8') from exc
        if c.digest(raw) != source['source_sha256']: raise ValueError('E_STALE_SOURCE')
        for unit in source['manifest']['units']:
            start, end = unit['range']
            if not 0 <= start < end <= len(raw) or c.digest(raw[start:end]) != unit['sha256']: raise ValueError('E_MANIFEST_INVALID')
        unit_digest = c.digest(c.canonical(source['manifest']))
        prior = previous.get('sources', {}).get(source_id) if compatible else None
        cache_key = {'source_sha256': source['source_sha256'], 'path': source['path'], 'unit_manifest_digest': unit_digest}
        if isinstance(prior, dict) and all(prior.get(k) == v for k, v in cache_key.items()) and isinstance(prior.get('fragment'), dict) and prior.get('fragment_digest') == c.digest(c.canonical(prior['fragment'])):
            fragment = copy.deepcopy(prior['fragment']); reused.append(source_id)
        else:
            fragment = _fragment(source_id, source, raw, repository); parsed.append(source_id)
        fragments[source_id] = fragment
        records[source_id] = dict(cache_key, status=fragment['status'], fragment=fragment,
                                  unit_ranges=[{'id': unit['id'], 'range': list(unit['range'])}
                                               for unit in source['manifest']['units']],
                                  fragment_digest=c.digest(c.canonical(fragment)))
    nodes, edges, symbols, diagnostics = _combine(fragments, sources)
    if len(nodes) > 10000 or len(edges) > 40000: raise ValueError('E_EXTRACTION_GRAPH_SCOPE')
    projection = _projection(nodes, edges)
    manifest = {'schema_version': 1, 'kind': 'knowledge-extraction-v1', 'repository': repository,
                'extractor': copy.deepcopy(EXTRACTOR), 'sources': records, 'symbols': symbols,
                'diagnostics': diagnostics, 'cache': {'reused_source_ids': reused, 'parsed_source_ids': parsed},
                'coverage': 'OBSERVED_FOR_DECLARED_PYTHON_SYNTAX' if all(r['status'] == 'OBSERVED' for r in records.values()) else 'PARTIAL',
                'embedding_scope': 'deterministic lexical word/subword hashing; semantic quality UNVERIFIED',
                'runtime_call_truth': 'UNVERIFIED', 'semantic_truth': 'UNVERIFIED',
                'projection_digest': c.digest(c.canonical(projection))}
    manifest['manifest_digest'] = c.digest(c.canonical(manifest))
    if len(c.canonical({'projection': projection, 'manifest': manifest})) > c.MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
    return {'projection': projection, 'manifest': manifest}
