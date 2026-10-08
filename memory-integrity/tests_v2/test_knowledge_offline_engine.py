"""Independent expectations for offline lexical/latent search and prose facts."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
ENGINE = SCRIPTS / 'knowledge_bridge' / 'offline_engine.py'
sys.path.insert(0, str(SCRIPTS))


class TypesAndIsolation(unittest.TestCase):
    def setUp(self):
        self.assertTrue(ENGINE.is_file(), 'offline engine implementation is missing')
        self.engine = importlib.import_module('knowledge_bridge.offline_engine')

    def test_import_does_not_load_optional_runtime(self):
        code = "import sys;sys.path.insert(0," + repr(str(SCRIPTS)) + ");import knowledge_bridge.offline_engine;print([x for x in ('sklearn','numpy','semantica') if x in sys.modules])"
        out = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True, timeout=15)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), '[]')

    def test_coding_and_test_evidence_type_rules(self):
        nodes = [{'id': 'module', 'type': 'Component'}, {'id': 'symbol', 'type': 'Symbol'},
                 {'id': 'other', 'type': 'Symbol'}, {'id': 'test', 'type': 'TestCase'},
                 {'id': 'run', 'type': 'TestRun'}]
        edges = [{'id': 'definition', 'subject': 'symbol', 'predicate': 'DEFINED_IN', 'object': 'module'},
                 {'id': 'reference', 'subject': 'symbol', 'predicate': 'REFERENCES', 'object': 'other'},
                 {'id': 'tests', 'subject': 'test', 'predicate': 'TESTS', 'object': 'symbol'},
                 {'id': 'evidence', 'subject': 'test', 'predicate': 'SUPPORTED_BY', 'object': 'run'}]
        result = self.engine.validate_types(nodes, edges)
        self.assertEqual(result['ontology'], 'project-2')
        self.assertEqual(result['shacl'], 'UNVERIFIED')

    def test_wrong_domain_range_and_foreign_predicate_rejected(self):
        nodes = [{'id': 'decision', 'type': 'Decision'}, {'id': 'symbol', 'type': 'Symbol'},
                 {'id': 'test', 'type': 'TestCase'}, {'id': 'run', 'type': 'TestRun'}]
        for subject, predicate, object_ in [('decision', 'TESTS', 'symbol'), ('test', 'TESTS', 'run'),
                                             ('symbol', 'DOES_EVERYTHING', 'decision')]:
            with self.subTest(subject=subject, predicate=predicate, object=object_):
                with self.assertRaisesRegex(ValueError, 'E_ONTOLOGY'):
                    self.engine.validate_types(nodes, [{'id': 'E', 'subject': subject, 'predicate': predicate, 'object': object_}])

    def test_malformed_type_records_are_explicit_value_errors(self):
        for nodes, edges in [([{'id': 'a', 'type': []}], []),
                             ([{'id': 'a', 'type': 'Symbol'}], [{'id': 'E', 'subject': 'a', 'predicate': [], 'object': 'a'}]),
                             ([{'id': 'a', 'type': 'Symbol'}], [{'id': 'E', 'subject': [], 'predicate': 'REFERENCES', 'object': 'a'}])]:
            with self.subTest(nodes=nodes, edges=edges):
                try:
                    self.engine.validate_types(nodes, edges)
                except Exception as exc:
                    self.assertIsInstance(exc, ValueError)
                else:
                    self.fail('malformed ontology record was accepted')


@unittest.skipUnless(os.environ.get('KNOWLEDGE_WORKER_PYTHON'), 'explicit pinned Semantica runtime not selected')
class ActualOfflineRuntime(unittest.TestCase):
    def setUp(self):
        self.assertTrue(ENGINE.is_file(), 'offline engine implementation is missing')

    def observe(self, body):
        prefix = "import sys,json,socket;sys.path.insert(0," + repr(str(SCRIPTS)) + ")\n"
        prefix += "def deny(*a,**kw): raise RuntimeError('E_UNEXPECTED_NETWORK')\n"
        prefix += "socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.create_connection=deny\n"
        prefix += "from knowledge_bridge import offline_engine as engine\n"
        out = subprocess.run([os.environ['KNOWLEDGE_WORKER_PYTHON'], '-B', '-c', prefix + body],
                             capture_output=True, text=True, encoding='utf-8',
                             env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=45)
        self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
        return json.loads(out.stdout)

    def test_automatically_generated_vectors_rank_identifiers_with_real_semantica(self):
        result = self.observe("""
nodes=[{'id':'retry','text':'client retry budget and maximum attempts'},
       {'id':'render','text':'renderer glyph texture and drawing'},
       {'id':'upload','text':'image uploader upload receipts'}]
vectors,query,metadata=engine.search_vectors(nodes,'retry budget')
from semantica.vector_store.vector_store import VectorRetriever
found=VectorRetriever(backend='inmemory').search_similar(query,vectors,[n['id'] for n in nodes],k=3)
print(json.dumps({'best':max(found,key=lambda x:x['score'])['id'],'metadata':metadata,'dimensions':[len(x) for x in vectors]},allow_nan=False))
""")
        self.assertEqual(result['best'], 'retry')
        self.assertEqual(result['metadata']['mode'], 'lexical')
        self.assertEqual(result['metadata']['evidence_class'], 'HOST_OBSERVED')
        self.assertEqual(result['metadata']['semantic_quality'], 'UNVERIFIED')
        self.assertEqual(result['dimensions'], [result['metadata']['dimension']] * 3)

    def test_latent_and_hybrid_modes_are_deterministic_without_model_downloads(self):
        result = self.observe("""
nodes=[{'id':'a','text':'client retries worker requests'}, {'id':'b','text':'worker applies policy retry rules'},
       {'id':'c','text':'policy denies invalid credentials'}, {'id':'d','text':'renderer draws glyph textures'}]
results=[]
for mode in ('lsa','hybrid'):
 a=engine.search_vectors(nodes,'worker policy',mode=mode)
 b=engine.search_vectors(nodes,'worker policy',mode=mode)
 results.append({'mode':mode,'same':a==b,'dimension':a[2]['dimension'],'algorithm':a[2]['algorithm']})
print(json.dumps(results,allow_nan=False))
""")
        self.assertTrue(all(r['same'] for r in result))
        self.assertTrue(all(r['dimension'] > 0 for r in result))
        self.assertTrue(all('LSA' in r['algorithm'] for r in result))

    def test_oov_empty_input_and_unknown_mode_do_not_invent_vectors(self):
        result = self.observe("""
nodes=[{'id':'a','text':'worker retry'}, {'id':'b','text':'renderer glyph'}]
errors=[]
for scope,query,mode in [(nodes,'qzzzzvxx','lexical'),([], 'worker','lexical'),(nodes,' ','lexical'),(nodes,'worker','unknown')]:
 try: engine.search_vectors(scope,query,mode=mode)
 except ValueError as exc: errors.append(str(exc))
print(json.dumps(errors))
""")
        self.assertEqual(len(result), 4)
        self.assertIn('E_QUERY_NO_LEXICAL_SUPPORT', result[0])

    def test_only_passed_authorized_corpus_changes_fitted_identity(self):
        result = self.observe("""
nodes=[{'id':'a','text':'worker retry'}, {'id':'b','text':'renderer glyph'}]
first=engine.search_vectors(nodes,'worker')[2]
second=engine.search_vectors(nodes+[{'id':'c','text':'uploader receipts'}],'worker')[2]
print(json.dumps({'first':first,'second':second}))
""")
        self.assertNotEqual(result['first']['model'], result['second']['model'])
        self.assertNotEqual(result['first']['fit_scope_digest'], result['second']['fit_scope_digest'])

    def test_document_with_no_tokens_cannot_be_randomly_represented(self):
        result = self.observe("""
try: engine.search_vectors([{'id':'valid','text':'worker retry'},{'id':'empty','text':'...'}],'worker')
except ValueError as exc: print(json.dumps(str(exc)))
""")
        self.assertIn('E_OFFLINE_DOCUMENT_NO_LEXICAL_SUPPORT', result)

    def test_affirmative_prose_calls_actual_semantica_with_precise_utf8_ranges(self):
        result = self.observe(r"""
text='\u00a0\nClient depends on Worker.\nClient references Policy.\n'
relations=engine.extract_prose(text)
print(json.dumps({'relations':relations,'text':text},ensure_ascii=False))
""")
        relations = result['relations']
        self.assertEqual([r['predicate'] for r in relations], ['DEPENDS_ON', 'REFERENCES'])
        first = relations[0]
        self.assertEqual((first['subject'], first['object']), ('Client', 'Worker'))
        raw = result['text'].encode('utf-8')
        self.assertEqual(raw[slice(*first['subject_span'])].decode('utf-8'), 'Client')
        self.assertEqual(raw[slice(*first['object_span'])].decode('utf-8'), 'Worker')
        self.assertEqual(raw[slice(*first['span'])].decode('utf-8'), first['text'])
        self.assertEqual(first['subject_span'][0], 3)
        self.assertEqual(first['polarity'], 'positive')
        self.assertEqual(first['conditions'], [])
        self.assertEqual(first['confidence_source'], 'HEURISTIC_UNCALIBRATED')
        self.assertIn('semantica', first['method'])

    def test_crlf_preserves_proposition_text_and_original_byte_spans(self):
        result = self.observe(r"""
lf='Client depends on Worker.\nClient references Policy.\n'
crlf=lf.replace('\n','\r\n')
print(json.dumps({'lf':engine.extract_prose(lf),'crlf':engine.extract_prose(crlf),'text':crlf}))
""")
        self.assertEqual(len(result['crlf']), 2)
        self.assertEqual([r['text'] for r in result['lf']], [r['text'] for r in result['crlf']])
        raw = result['text'].encode('utf-8')
        for row in result['crlf']:
            self.assertEqual(raw[slice(*row['span'])].decode('utf-8'), row['text'])
            self.assertNotIn('\r', row['text'])
            self.assertEqual(raw[slice(*row['subject_span'])].decode('utf-8'), row['subject'])
        self.assertEqual(result['crlf'][1]['span'][0], result['lf'][1]['span'][0] + 1)

    def test_conditional_negative_and_unrelated_prose_stays_unasserted(self):
        result = self.observe(r"""
text='If enabled, Client depends on Worker.\nClient does not depend on Worker.\nClient depends on Worker if enabled.\nClient appears near Worker.\n'
print(json.dumps(engine.extract_prose(text)))
""")
        self.assertEqual(result, [])

    def test_repeated_names_keep_each_actual_statement_span(self):
        result = self.observe(r"""
text='Client depends on Worker.\nClient depends on Storage.\n'
print(json.dumps({'relations':engine.extract_prose(text),'text':text}))
""")
        self.assertEqual([r['object'] for r in result['relations']], ['Worker', 'Storage'])
        raw = result['text'].encode('utf-8')
        for row in result['relations']:
            self.assertEqual(raw[slice(*row['subject_span'])].decode('utf-8'), row['subject'])
            self.assertEqual(raw[slice(*row['span'])].decode('utf-8'), row['text'])

    def test_scoped_conditional_and_example_context_is_not_flattened(self):
        result = self.observe(r"""
cases=['If enabled:\nClient depends on Worker.\n',
       'If enabled.\nClient depends on Worker.\n',
       'Example:\nClient depends on Worker.\n',
       '```text\nClient depends on Worker.\n```\n',
       'Nothing depends on Worker.\n']
print(json.dumps([engine.extract_prose(text) for text in cases]))
""")
        self.assertEqual(result, [[]] * 5)

    def test_document_context_cannot_turn_quoted_or_denied_claims_into_facts(self):
        result = self.observe(r"""
cases=['Never assume the following.\nClient depends on Worker.\n',
       'The claim is false.\nClient depends on Worker.\n',
       'Example:\n\nClient depends on Worker.\n',
       '```\nSample code\n~~~\nClient depends on Worker.\n```\n',
       'Résumé.\nClient depends on Worker.\n',
       'Client depends on Worker.\nUnqualified trailing context.\n',
       'Client depends on Worker.\n\nUnless disabled.\n']
print(json.dumps([engine.extract_prose(text) for text in cases]))
""")
        self.assertEqual(result, [[]] * 7)

    def test_real_shacl_applies_predicate_domain_and_range(self):
        result = self.observe("""
nodes=[{'id':'test','type':'TestCase'},{'id':'symbol','type':'Symbol'}]
print(json.dumps(engine.validate_types(nodes,[{'id':'E','subject':'test','predicate':'TESTS','object':'symbol'}],shacl=True)))
""")
        self.assertEqual(result['shacl'], 'CONFORMS')


if __name__ == '__main__':
    unittest.main()
