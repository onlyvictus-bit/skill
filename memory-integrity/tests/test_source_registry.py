import json
import tempfile
import unittest
from pathlib import Path

from scripts import source_coverage
from scripts import source_registry


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.registry = self.root / 'sources.json'
        source_registry.init_registry(self.registry)

    def tearDown(self):
        self.tmp.cleanup()

    def _add_text(self, name, text, required=True):
        src = self.root / name
        src.write_text(text, encoding='utf-8')
        out = self.root / (name + '.coverage')
        manifest = source_coverage.ingest_text(src, out, max_bytes=16)
        receipts = out / 'receipts.jsonl'
        source_coverage.mark_all_complete(out / 'manifest.json', receipts)
        entry = source_registry.register_source(
            self.registry,
            source_id='SRC-' + name.replace('.', '-'),
            source_path=src,
            manifest_path=out / 'manifest.json',
            receipts_path=receipts,
            required=required,
            authority='AUTHORITATIVE',
            role='requirement-source',
        )
        return src, out, entry

    def test_registry_basis_is_deterministic(self):
        self._add_text('a.txt', 'alpha\n')
        self._add_text('b.txt', 'beta\n')
        first = source_registry.audit_registry(self.registry)
        second = source_registry.audit_registry(self.registry)
        self.assertEqual(first['source_basis_digest'], second['source_basis_digest'])
        self.assertEqual(first['overall'], 'READY')
        self.assertEqual(first['required_sources'], 2)
        self.assertEqual(first['ready_required_sources'], 2)

    def test_required_source_staleness_blocks_basis(self):
        src, _, _ = self._add_text('a.txt', 'alpha\n')
        ready = source_registry.audit_registry(self.registry)
        self.assertEqual(ready['overall'], 'READY')
        src.write_text('changed\n', encoding='utf-8')
        stale = source_registry.audit_registry(self.registry)
        self.assertEqual(stale['overall'], 'BLOCKED')
        self.assertIn('SRC-a-txt', stale['blocked_required_source_ids'])
        self.assertEqual(stale['sources'][0]['coverage'], 'STALE')

    def test_optional_source_does_not_block_required_basis(self):
        self._add_text('required.txt', 'r\n', required=True)
        src, _, _ = self._add_text('optional.txt', 'o\n', required=False)
        src.write_text('changed optional\n', encoding='utf-8')
        report = source_registry.audit_registry(self.registry)
        self.assertEqual(report['overall'], 'READY')
        self.assertEqual(report['blocked_required_source_ids'], [])
        optional = [s for s in report['sources'] if s['source_id'] == 'SRC-optional-txt'][0]
        self.assertEqual(optional['coverage'], 'STALE')

    def test_registry_rejects_duplicate_source_id(self):
        self._add_text('a.txt', 'alpha\n')
        with self.assertRaises(ValueError):
            source_registry.register_source(
                self.registry,
                source_id='SRC-a-txt',
                source_path=self.root / 'a.txt',
                required=True,
                authority='AUTHORITATIVE',
                role='duplicate',
            )


if __name__ == '__main__':
    unittest.main()
