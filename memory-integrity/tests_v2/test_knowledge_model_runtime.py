"""Local learned-model contracts and opt-in observations with real weights."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
MODULE = SCRIPTS / 'knowledge_bridge' / 'model_runtime.py'


class ManifestContracts(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), 'local learned-model runtime is missing')
        self.runtime = importlib.import_module('knowledge_bridge.model_runtime')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'minilm').mkdir()
        files = []
        for name in ('model.onnx', 'tokenizer.json'):
            raw = ('fixture-' + name).encode()
            (self.root / 'minilm' / name).write_bytes(raw)
            files.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest()})
        self.doc = {'schema_version': 1, 'models': {'embedding': {
            'model_id': 'sentence-transformers/all-MiniLM-L6-v2', 'revision': '1' * 40,
            'backend': 'onnx', 'directory': 'minilm', 'files': files,
            'model_file': 'model.onnx', 'tokenizer_file': 'tokenizer.json', 'max_input_tokens': 256}}}
        self.path = self.root / 'manifest.json'
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.doc), encoding='utf-8')

    def test_valid_manifest_binds_actual_bytes(self):
        result = self.runtime.load_manifest(self.path)
        self.assertEqual(result['manifest_digest'], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(result['models']['embedding']['revision'], '1' * 40)

    def test_changed_model_bytes_fail_before_model_import(self):
        (self.root / 'minilm' / 'model.onnx').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'E_MODEL_FILE_DIGEST'):
            self.runtime.load_manifest(self.path)

    def test_extra_unbound_file_is_rejected(self):
        (self.root / 'minilm' / 'remote_code.py').write_text('raise Exception()')
        with self.assertRaisesRegex(ValueError, 'E_MODEL_FILE_SET'):
            self.runtime.load_manifest(self.path)

    def test_path_escape_symlink_and_duplicate_manifest_file_are_rejected(self):
        for name in ('../outside', '/absolute', 'nested\\escape'):
            self.doc['models']['embedding']['directory'] = name
            self.save()
            with self.assertRaises(ValueError):
                self.runtime.load_manifest(self.path)
        self.doc['models']['embedding']['directory'] = 'minilm'
        self.doc['models']['embedding']['files'].append(dict(self.doc['models']['embedding']['files'][0]))
        self.save()
        with self.assertRaisesRegex(ValueError, 'E_MODEL_DUPLICATE_FILE'):
            self.runtime.load_manifest(self.path)
        self.doc['models']['embedding']['files'].pop()
        self.save()
        link = self.root / 'minilm' / 'link'
        try:
            link.symlink_to(self.root / 'minilm' / 'model.onnx')
        except OSError:
            return
        with self.assertRaisesRegex(ValueError, 'E_SYMLINK'):
            self.runtime.load_manifest(self.path)

    def test_unknown_backend_revision_and_boolean_token_limit_are_rejected(self):
        for field, value in [('backend', 'remote-api'), ('revision', 'main'), ('max_input_tokens', True)]:
            original = self.doc['models']['embedding'][field]
            self.doc['models']['embedding'][field] = value
            self.save()
            with self.assertRaises(ValueError):
                self.runtime.load_manifest(self.path)
            self.doc['models']['embedding'][field] = original

    def test_malformed_load_file_names_are_explicit_value_errors(self):
        for field, value in [('model_file', []), ('tokenizer_file', None)]:
            original = self.doc['models']['embedding'][field]
            self.doc['models']['embedding'][field] = value
            self.save()
            try:
                self.runtime.load_manifest(self.path)
            except Exception as error:
                self.assertIsInstance(error, ValueError)
            else:
                self.fail('malformed load filename was accepted')
            self.doc['models']['embedding'][field] = original

    def test_empty_or_over_scope_inputs_fail_without_loading_dependencies(self):
        for value in ([], [''], ['valid'] * 1001):
            with self.assertRaises(ValueError):
                self.runtime.embed_texts(self.path, value)
        with self.assertRaises(ValueError):
            self.runtime.generate_text(self.path, 'prompt', max_new_tokens=True)

    def test_optional_runtime_is_not_imported_by_import(self):
        code = 'import sys;sys.path.insert(0,' + repr(str(SCRIPTS)) + ');import knowledge_bridge.model_runtime;print([x for x in ("torch","transformers","onnxruntime","tokenizers") if x in sys.modules])'
        result = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '[]')

    def test_stdin_cli_rejects_unknown_operation_as_strict_json(self):
        result = subprocess.run([sys.executable, '-B', str(MODULE)],
            input=json.dumps({'op': 'remote', 'manifest': str(self.path)}),
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.strip(), 'model CLI JSON receipt is missing')
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt['ok'])
        self.assertIn('E_MODEL_OPERATION', receipt['error'])

    def test_stdin_cli_rejects_extra_fields_and_duplicate_json_keys(self):
        requests = [json.dumps({'op': 'embed', 'manifest': str(self.path), 'texts': ['valid'], 'provider': 'remote'}),
                    '{"op":"embed","op":"generate"}']
        for request in requests:
            result = subprocess.run([sys.executable, '-B', str(MODULE)], input=request,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertTrue(result.stdout.strip(), 'model CLI JSON receipt is missing')
            self.assertFalse(json.loads(result.stdout)['ok'])


@unittest.skipUnless(os.environ.get('KNOWLEDGE_MODEL_MANIFEST') and os.environ.get('MODEL_PYTHON'),
                     'explicit local model manifest and interpreter not selected')
class RealLocalModels(unittest.TestCase):
    def observe(self, body):
        code = 'import sys,json;sys.path.insert(0,' + repr(str(SCRIPTS)) + ')\n'
        code += 'from knowledge_bridge import model_runtime as runtime\nmanifest=' + repr(os.environ['KNOWLEDGE_MODEL_MANIFEST']) + '\n'
        result = subprocess.run([os.environ['MODEL_PYTHON'], '-B', '-c', code + body],
                                capture_output=True, text=True, timeout=240,
                                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_real_learned_embeddings_have_paraphrase_support_and_measured_tokens(self):
        result = self.observe("""
r=runtime.embed_texts(manifest,['A physician treats sick patients.','A doctor provides medical care.','The renderer draws polygon textures.'])
print(json.dumps(r,allow_nan=False))
""")
        vectors = result['vectors']
        self.assertEqual([len(v) for v in vectors], [384] * 3)
        cosine = lambda a, b: sum(x * y for x, y in zip(a, b))
        self.assertGreater(cosine(vectors[0], vectors[1]), cosine(vectors[0], vectors[2]))
        self.assertTrue(all(x > 0 for x in result['input_token_counts']))
        self.assertEqual(result['network_policy'], 'offline; Python sockets denied; not an OS sandbox')
        self.assertEqual(result['semantic_quality'], 'UNVERIFIED')

    def test_real_embedding_refuses_truncation(self):
        result = self.observe("""
try: runtime.embed_texts(manifest,['medicine '*1000])
except ValueError as e: print(json.dumps(str(e)))
""")
        self.assertIn('E_MODEL_INPUT_TOKEN_LIMIT', result)

    def test_real_generation_is_deterministic_and_receipts_account_for_raw_tokens(self):
        result = self.observe("""
a=runtime.generate_text(manifest,'Write a Python function add(a, b) that returns their sum.',max_new_tokens=48)
b=runtime.generate_text(manifest,'Write a Python function add(a, b) that returns their sum.',max_new_tokens=48)
print(json.dumps({'a':a,'b':b}))
""")
        a, b = result['a'], result['b']
        self.assertEqual(a['output_token_ids'], b['output_token_ids'])
        self.assertEqual(a['output_token_count'], len(a['output_token_ids']))
        self.assertEqual(a['input_token_count'], len(a['input_token_ids']))
        self.assertTrue(a['text'].strip())
        self.assertLessEqual(a['output_token_count'], 48)
        self.assertIn(a['finish_reason'], ('eos', 'output_limit'))
        self.assertFalse(a['settings']['do_sample'])
        self.assertEqual(a['settings'].get('temperature'), 1.0)
        self.assertEqual(a['settings'].get('top_p'), 1.0)
        self.assertEqual(a['settings'].get('top_k'), 50)

    def test_real_reranking_scores_every_candidate_with_bound_model(self):
        result = self.observe("""
print(json.dumps(runtime.rerank_texts(manifest,'Where is a network retry policy implemented?',[
 {'id':'retry','text':'The HTTP client implements retries with a bounded attempt policy.'},
 {'id':'glyph','text':'The renderer draws glyph textures on a canvas.'}]),allow_nan=False))
""")
        self.assertEqual({x['id'] for x in result['ranking']}, {'retry', 'glyph'})
        self.assertTrue(all(x['input_token_count'] > 0 and x['label_token_count'] > 0 for x in result['ranking']))
        self.assertEqual(result['algorithm'], 'causal cross-attention Yes/No label log-likelihood')
        self.assertEqual(result['semantic_quality'], 'UNVERIFIED')

    def test_real_generation_refuses_truncation(self):
        result = self.observe("""
try: runtime.generate_text(manifest,'print hello '*10000,max_new_tokens=1)
except ValueError as e: print(json.dumps(str(e)))
""")
        self.assertIn('E_MODEL_INPUT_TOKEN_LIMIT', result)


if __name__ == '__main__':
    unittest.main()
