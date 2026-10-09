"""Opt-in actual JavaScript/TypeScript syntax, never source execution.

Names are navigation observations. Calls remain unresolved until a separate
binding analysis establishes their target; syntax alone never proves runtime.
"""
from pathlib import PurePosixPath
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from knowledge_bridge import contracts as c
else:
    from . import contracts as c


def parse(raw, path):
    if not isinstance(raw, bytes) or not raw or len(raw) > c.MAX_MESSAGE:
        raise ValueError('E_LANGUAGE_SOURCE_SIZE')
    raw.decode('utf-8')
    suffix = PurePosixPath(path).suffix
    if suffix not in {'.js', '.jsx', '.ts', '.tsx'}:
        raise ValueError('E_LANGUAGE_UNSUPPORTED')
    try:
        from tree_sitter import Language, Parser
        if suffix in {'.ts', '.tsx'}:
            import tree_sitter_typescript as grammar
            capsule = grammar.language_tsx() if suffix == '.tsx' else grammar.language_typescript()
        else:
            import tree_sitter_javascript as grammar
            capsule = grammar.language()
    except ImportError as exc:
        raise ValueError('E_LANGUAGE_RUNTIME_UNAVAILABLE') from exc
    import importlib.metadata
    versions = {'tree-sitter': importlib.metadata.version('tree-sitter'),
                'grammar': importlib.metadata.version('tree-sitter-typescript' if suffix in {'.ts', '.tsx'} else 'tree-sitter-javascript')}
    tree = Parser(Language(capsule)).parse(raw)
    result = {'status': 'FAILED' if tree.root_node.has_error else 'OBSERVED',
              'language': 'typescript' if suffix in {'.ts', '.tsx'} else 'javascript',
              'parser': versions, 'source_sha256': c.digest(raw), 'symbols': [],
              'imports': [], 'calls': [], 'diagnostics': [], 'runtime_call_truth': 'UNVERIFIED'}
    if tree.root_node.has_error:
        result['diagnostics'].append({'kind': 'PARSE_FAILED', 'range': [0, len(raw)]})
        return result

    def text(node):
        return raw[node.start_byte:node.end_byte].decode('utf-8')

    def row(node, **values):
        return dict(values, range=[node.start_byte, node.end_byte],
                    span_sha256=c.digest(raw[node.start_byte:node.end_byte]))

    stack = [tree.root_node]; count = 0
    while stack:
        node = stack.pop(); count += 1
        if count > 50000:
            raise ValueError('E_LANGUAGE_NODE_LIMIT')
        if node.type in {'function_declaration', 'generator_function_declaration',
                         'class_declaration', 'interface_declaration', 'type_alias_declaration'}:
            name = node.child_by_field_name('name')
            if name:
                result['symbols'].append(row(node, name=text(name), kind=node.type))
        elif node.type == 'import_statement':
            source = node.child_by_field_name('source')
            if source:
                result['imports'].append(row(node, module=text(source)[1:-1],
                                             bindings=[text(n) for n in node.named_children if n != source]))
        elif node.type == 'call_expression':
            callee = node.child_by_field_name('function')
            result['calls'].append(row(node, callee=text(callee) if callee else None,
                                       target=None, qualification='SYNTAX_ONLY'))
            result['diagnostics'].append(row(node, kind='UNRESOLVED_CALL'))
        stack.extend(reversed(node.named_children))
    return result


def main():
    try:
        request=c.loads(sys.stdin.buffer.read(c.MAX_MESSAGE+1))
        c.keys(request,{'text','path'},'syntax request')
        c.string(request['text'],'syntax text');c.string(request['path'],'syntax path')
        result=dict(parse(request['text'].encode('utf-8'),request['path']),ok=True)
        status=0
    except Exception as exc:
        result={'ok':False,'error':str(exc)};status=1
    sys.stdout.buffer.write(c.canonical(result));return status


if __name__=='__main__':raise SystemExit(main())
