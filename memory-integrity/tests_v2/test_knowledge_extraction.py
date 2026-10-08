"""Observed byte-linked extraction, conservative static calls and exact cache reuse."""
import copy
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
CM = ROOT.parent / 'claude-mon'


class Extraction(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('knowledge_bridge.extraction'),
                             'source-linked local extraction is missing')
        from knowledge_bridge import extraction, indexing, contracts
        self.e, self.i, self.c = extraction, indexing, contracts
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = {}

    def put(self, ident, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode('utf-8') if isinstance(text, str) else text)
        self.paths[ident] = path

    def sources(self):
        return self.i.freeze(self.root, {'schema_version': 1, 'workspace_id': 'extract-test',
            'repository': 'owner/project', 'sources': [
                {'id': ident, 'path': path, 'authority': 'AUTHORITATIVE'}
                for ident, path in self.paths.items()]}, CM)

    def extract(self, previous=None):
        return self.e.extract(self.sources(), 'owner/project', previous=previous, root=self.root)

    def symbol(self, result, name):
        return next(row for row in result['manifest']['symbols'] if row['qualified_name'] == name)

    def test_modules_symbols_and_source_refs_are_generated_without_execution(self):
        self.put('client', 'pkg/client.py', "raise RuntimeError('must never execute')\nclass Client:\n    def send(self):\n        return 7\n")
        result = self.extract()
        self.assertEqual(result['projection']['schema_version'], 2)
        self.assertEqual(result['projection']['ontology'], 'project-2')
        self.assertEqual(result['projection']['embedding']['model'], 'local-text-v1')
        self.assertEqual(result['projection']['embedding']['dimension'], 256)
        sym = self.symbol(result, 'pkg.client.Client.send')
        node = next(n for n in result['projection']['nodes'] if n['id'] == sym['id'])
        self.assertEqual(node['type'], 'Symbol')
        self.assertEqual(node['source_units'], [
            {'source_id': 'client', 'unit_id': 'U000003'},
            {'source_id': 'client', 'unit_id': 'U000004'}])
        self.assertTrue(any(e['subject'] == sym['id'] and e['predicate'] == 'DEFINED_IN'
                            for e in result['projection']['edges']))

    def test_unicode_crlf_byte_spans_reopen_exact_source(self):
        raw = '# é漢\r\ndef café():\r\n    return "é"\r\n'.encode('utf-8')
        self.put('unicode', 'unicode_mod.py', raw)
        result = self.extract()
        row = self.symbol(result, 'unicode_mod.café')
        start, end = row['range']
        self.assertEqual(raw[start:end], 'def café():\r\n    return "é"'.encode('utf-8'))
        self.assertEqual(row['span_sha256'], self.c.digest(raw[start:end]))
        self.assertEqual(result['manifest']['sources']['unicode']['source_sha256'], self.c.digest(raw))

    def test_relative_import_alias_and_static_call_have_authored_direction(self):
        self.put('client', 'pkg/client.py', 'from .worker import run as work\ndef send():\n    return work()\n')
        self.put('worker', 'pkg/worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        send, run = (self.symbol(result, n)['id'] for n in ('pkg.client.send', 'pkg.worker.run'))
        self.assertTrue(any(e['subject'] == send and e['object'] == run and e['predicate'] == 'REFERENCES'
                            and 'python-static-call' in e['conditions'] for e in result['projection']['edges']))
        modules = {n['text']: n['id'] for n in result['projection']['nodes'] if n['type'] == 'Component'}
        self.assertTrue(any(e['subject'] == modules['Python module pkg.client']
                            and e['object'] == modules['Python module pkg.worker']
                            and e['predicate'] == 'DEPENDS_ON' for e in result['projection']['edges']))

    def test_argument_shadowing_does_not_invent_imported_call(self):
        self.put('client', 'pkg/client.py', 'from .worker import run\ndef send(run):\n    return run()\n')
        self.put('worker', 'pkg/worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        send, run = (self.symbol(result, n)['id'] for n in ('pkg.client.send', 'pkg.worker.run'))
        self.assertFalse(any(e['subject'] == send and e['object'] == run and e['predicate'] == 'REFERENCES'
                             for e in result['projection']['edges']))
        self.assertTrue(any(d['kind'] == 'UNRESOLVED_CALL' for d in result['manifest']['diagnostics']))

    def test_assignment_shadowing_and_dynamic_receiver_remain_unknown(self):
        self.put('client', 'pkg/client.py', 'from .worker import run\ndef send(obj):\n    run = obj\n    run()\n    obj.run()\n')
        self.put('worker', 'pkg/worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))
        self.assertEqual(sum(d['kind'] == 'UNRESOLVED_CALL' for d in result['manifest']['diagnostics']), 2)

    def test_unresolved_external_import_never_imports_source_or_invents_endpoint(self):
        self.put('client', 'client.py', 'from nonexistent_secret_service import action\ndef send():\n    return action()\n')
        result = self.extract()
        kinds = {d['kind'] for d in result['manifest']['diagnostics']}
        self.assertTrue({'UNRESOLVED_IMPORT', 'UNRESOLVED_CALL'} <= kinds)
        self.assertFalse(any(e['predicate'] == 'DEPENDS_ON' for e in result['projection']['edges']))

    def test_unchanged_fragments_are_reused_but_cross_file_resolution_is_fresh(self):
        self.put('client', 'pkg/client.py', 'from .worker import run\ndef send():\n    return run()\n')
        self.put('worker', 'pkg/worker.py', 'def run():\n    return 1\n')
        first = self.extract()
        self.put('worker', 'pkg/worker.py', 'def renamed():\n    return 2\n')
        second = self.extract(first['manifest'])
        self.assertEqual(second['manifest']['cache']['reused_source_ids'], ['client'])
        self.assertEqual(second['manifest']['cache']['parsed_source_ids'], ['worker'])
        self.assertEqual(self.symbol(first, 'pkg.client.send')['id'], self.symbol(second, 'pkg.client.send')['id'])
        self.assertFalse(any('python-static-call' in e['conditions'] for e in second['projection']['edges']))
        self.assertTrue(any(d['kind'] == 'UNRESOLVED_IMPORT' for d in second['manifest']['diagnostics']))

    def test_parser_identity_and_corrupt_fragment_prevent_cache_reuse(self):
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        first = self.extract()
        for mutate in ('identity', 'fragment'):
            prior = copy.deepcopy(first['manifest'])
            if mutate == 'identity': prior['extractor']['version'] = 'foreign'
            else: prior['sources']['worker']['fragment_digest'] = '0' * 64
            result = self.extract(prior)
            self.assertEqual(result['manifest']['cache']['reused_source_ids'], [])
            self.assertEqual(result['manifest']['cache']['parsed_source_ids'], ['worker'])

    def test_modified_fragment_with_stale_manifest_seal_cannot_fabricate_calls(self):
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        first = self.extract()
        prior = copy.deepcopy(first['manifest'])
        fragment = prior['sources']['worker']['fragment']
        fake_symbol = copy.deepcopy(fragment['symbols'][0])
        fake_symbol.update(id='symbol:forged', name='fabricated', qualified_name='worker.fabricated', scope='fabricated')
        fragment['symbols'].append(fake_symbol)
        fake_node = copy.deepcopy(next(n for n in fragment['nodes'] if n['type'] == 'Symbol'))
        fake_node.update(id='symbol:forged', text='Python function worker.fabricated')
        fragment['nodes'].append(fake_node)
        prior['sources']['worker']['fragment_digest'] = self.c.digest(self.c.canonical(fragment))
        self.put('client', 'client.py', 'from worker import fabricated\ndef send():\n    return fabricated()\n')
        result = self.extract(prior)
        self.assertEqual(result['manifest']['cache']['reused_source_ids'], [])
        self.assertFalse(any(n['id'] == 'symbol:forged' for n in result['projection']['nodes']))
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))

    def test_sealed_manifest_with_wrong_recombined_projection_is_not_reused(self):
        self.put('client', 'client.py', 'from worker import run\ndef send():\n    return run()\n')
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        first = self.extract()
        prior = copy.deepcopy(first['manifest'])
        prior['projection_digest'] = '0' * 64
        prior['manifest_digest'] = self.c.digest(self.c.canonical({k: v for k, v in prior.items() if k != 'manifest_digest'}))
        result = self.extract(prior)
        self.assertEqual(result['manifest']['cache']['reused_source_ids'], [])

    def test_duplicate_module_mapping_is_ambiguous_not_merged(self):
        self.put('first', 'worker.py', 'def run():\n    return 1\n')
        self.put('second', 'worker/__init__.py', 'def run():\n    return 2\n')
        self.put('client', 'client.py', 'from worker import run\ndef send():\n    return run()\n')
        result = self.extract()
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))
        self.assertTrue(any(d['kind'] == 'AMBIGUOUS_MODULE' for d in result['manifest']['diagnostics']))

    def test_redefined_symbols_keep_distinct_occurrences_and_calls_unknown(self):
        self.put('worker', 'worker.py', 'def run():\n    return 1\ndef run():\n    return 2\ndef use():\n    return run()\n')
        result = self.extract()
        ids = [n['id'] for n in result['projection']['nodes']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))
        self.assertTrue(any(d['kind'] == 'AMBIGUOUS_SYMBOL' for d in result['manifest']['diagnostics']))

    def test_namespace_package_dotted_import_resolves_without_importing_package(self):
        self.put('client', 'client.py', 'import pkg.worker\ndef send():\n    return pkg.worker.run()\n')
        self.put('worker', 'pkg/worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        self.assertEqual(sum(e['predicate'] == 'DEPENDS_ON' for e in result['projection']['edges']), 1)
        self.assertEqual(sum('python-static-call' in e['conditions'] for e in result['projection']['edges']), 1)

    def test_wildcard_import_blocks_potentially_rebound_names(self):
        self.put('client', 'client.py', 'def run():\n    return 1\nfrom other import *\ndef use():\n    return run()\n')
        result = self.extract()
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))

    def test_imported_module_attribute_replacement_does_not_prove_original_call(self):
        self.put('client', 'client.py', 'import worker\nworker.run = lambda: 2\ndef send():\n    return worker.run()\n')
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))

    def test_comprehension_walrus_binding_shadows_imported_name_in_outer_scope(self):
        self.put('client', 'client.py', 'from worker import run\ndef send():\n    [(run := item) for item in [lambda: 2]]\n    return run()\n')
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        self.assertFalse(any('python-static-call' in e['conditions'] for e in result['projection']['edges']))

    def test_nested_class_does_not_lexically_close_over_outer_class_names(self):
        self.put('client', 'client.py', 'from worker import run\nclass Outer:\n    def run():\n        return 2\n    class Inner:\n        run()\n')
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        inner = self.symbol(result, 'client.Outer.Inner')['id']
        worker = self.symbol(result, 'worker.run')['id']
        edges = [e for e in result['projection']['edges'] if 'python-static-call' in e['conditions']]
        self.assertEqual([(e['subject'], e['object']) for e in edges], [(inner, worker)])

    def test_blank_prose_units_do_not_make_projection_structurally_invalid(self):
        self.put('policy', 'policy.md', '\r\n\r\nClient depends on Worker.\r\n')
        sources = self.sources()
        result = self.e.extract(sources, 'owner/project', root=self.root)
        self.c.validate_projection(result['projection'], sources)
        self.assertTrue(all(n['text'].strip() for n in result['projection']['nodes']))
        self.assertEqual(result['projection']['nodes'][0]['source_units'],
                         [{'source_id': 'policy', 'unit_id': 'U000003'}])

    def test_parse_failure_is_observed_and_cannot_be_claimed_complete(self):
        self.put('bad', 'bad.py', 'def broken(:\n    pass\n')
        result = self.extract()
        self.assertEqual(result['manifest']['sources']['bad']['status'], 'FAILED')
        self.assertEqual(result['manifest']['coverage'], 'PARTIAL')
        self.assertTrue(any(d['kind'] == 'PARSE_FAILED' for d in result['manifest']['diagnostics']))

    def test_nonpython_and_negated_prose_are_explicit_diagnostics(self):
        self.put('policy', 'policy.md', 'Never retry writes unless policy permits it.\n')
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        result = self.extract()
        kinds = {d['kind'] for d in result['manifest']['diagnostics']}
        self.assertTrue({'UNSUPPORTED_FORMAT', 'SEMANTIC_REVIEW_REQUIRED'} <= kinds)
        self.assertFalse(any(n['type'] == 'Assertion' for n in result['projection']['nodes']))

    def test_prose_only_source_retains_exact_unit_navigation_without_assertion(self):
        text = 'Never retry writes unless policy permits it.\r\n'
        self.put('policy', 'policy.md', text)
        result = self.extract()
        nodes = result['projection']['nodes']
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]['type'], 'SourceUnit')
        self.assertEqual(nodes[0]['text'], text)
        self.assertEqual(nodes[0]['source_units'], [{'source_id': 'policy', 'unit_id': 'U000001'}])
        self.assertEqual(nodes[0]['polarity'], 'unknown')
        self.assertEqual(result['manifest']['coverage'], 'PARTIAL')

    def test_invalid_utf8_and_changed_frozen_bytes_are_refused(self):
        self.put('worker', 'worker.py', 'def run():\n    return 1\n')
        sources = self.sources()
        (self.root / 'worker.py').write_bytes(b'\xff')
        with self.assertRaises(ValueError): self.e.extract(sources, 'owner/project', root=self.root)
        (self.root / 'worker.py').write_text('def changed():\n    pass\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'STALE'): self.e.extract(sources, 'owner/project', root=self.root)

    def test_local_vectors_are_deterministic_nonzero_and_explicitly_lexical(self):
        a = self.e.vectorize('retry client worker')
        self.assertEqual(a, self.e.vectorize('retry client worker'))
        self.assertEqual(len(a), 256)
        self.assertAlmostEqual(math.hypot(*a), 1.0)
        self.assertNotEqual(a, self.e.vectorize('unrelated geometry triangles'))
        self.assertEqual(len(self.e.vectorize('')), 256)


if __name__ == '__main__': unittest.main()
