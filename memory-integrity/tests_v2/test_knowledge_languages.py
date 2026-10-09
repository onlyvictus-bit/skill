"""Behavioral syntax and quoted-proposal contracts; optional parser runtime."""
import importlib.util
import os
import subprocess
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from knowledge_bridge import contracts as c
PARSER_AVAILABLE=bool(importlib.util.find_spec('tree_sitter') or os.environ.get('MODEL_PYTHON'))

def selected_parse(raw,path):
    if importlib.util.find_spec('tree_sitter'):
        from knowledge_bridge.language_extraction import parse
        return parse(raw,path)
    script=Path(__file__).resolve().parents[1]/'scripts/knowledge_bridge/language_extraction.py'
    observed=subprocess.run([os.environ['MODEL_PYTHON'],'-B',str(script)],
             input=c.canonical({'text':raw.decode('utf-8'),'path':path}),capture_output=True,timeout=30)
    if observed.returncode:raise AssertionError(observed.stdout.decode()+observed.stderr.decode())
    return c.loads(observed.stdout)


class LanguageContract(unittest.TestCase):
    def test_real_syntax_parser_contract_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.language_extraction'),
                             'JavaScript/TypeScript parser is missing')

    @unittest.skipUnless(PARSER_AVAILABLE, 'isolated parser runtime required')
    def test_typescript_exports_imports_calls_and_exact_utf8_ranges(self):
        parse=selected_parse
        raw = '// café\nimport {send} from "./worker";\nexport function run(x: string) { return send(x); }\n'.encode()
        result = parse(raw, 'client.ts')
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual([x['name'] for x in result['symbols']], ['run'])
        self.assertEqual(result['imports'][0]['module'], './worker')
        self.assertEqual(result['calls'][0]['callee'], 'send')
        for row in result['symbols'] + result['imports'] + result['calls']:
            start, end = row['range']
            self.assertEqual(row['span_sha256'], c.digest(raw[start:end]))
        self.assertEqual(result['runtime_call_truth'], 'UNVERIFIED')

    @unittest.skipUnless(PARSER_AVAILABLE, 'isolated parser runtime required')
    def test_malformed_syntax_is_failed_not_partial_success(self):
        parse=selected_parse
        result = parse(b'export function broken( {', 'bad.js')
        self.assertEqual(result['status'], 'FAILED')
        self.assertFalse(result['symbols'])

    @unittest.skipUnless(PARSER_AVAILABLE, 'isolated parser runtime required')
    def test_dynamic_calls_have_no_invented_target(self):
        parse=selected_parse
        result = parse(b'const x = () => handlers[name]();', 'dynamic.js')
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertIn('UNRESOLVED_CALL', [x['kind'] for x in result['diagnostics']])

    @unittest.skipUnless(PARSER_AVAILABLE, 'isolated parser runtime required')
    def test_parsed_symbols_enter_source_bound_project_projection(self):
        import tempfile
        from knowledge_bridge import extraction
        import inspect
        self.assertIn('language_parser',inspect.signature(extraction.extract).parameters)
        parse=selected_parse
        class SelectedParser:
            executable_digest = 'a' * 64
            def syntax(self,text,path): return parse(text.encode(),path)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=b'export function run() { return 3; }\n';(root/'client.ts').write_bytes(raw)
            source={'path':'client.ts','authority':'AUTHORITATIVE','source_sha256':c.digest(raw),
                    'manifest':{'units':[{'id':'U000001','range':[0,len(raw)],'sha256':c.digest(raw)}]}}
            result=extraction.extract({'client':source},'fixture',root=root,language_parser=SelectedParser())
            self.assertTrue(any(n['type']=='Symbol' and 'run' in n['text'] for n in result['projection']['nodes']))
            self.assertTrue(extraction._sealed_previous(result['manifest'],'fixture'))


if __name__ == '__main__':
    unittest.main()
