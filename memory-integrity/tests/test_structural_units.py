import tempfile
import unittest
from pathlib import Path

from scripts import source_coverage
from scripts import structural_units


class StructuralUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_line_inventory_covers_source_exactly(self):
        src = self.root / 'code.py'
        src.write_text('a = 1\nβ = 2\nlast', encoding='utf-8')
        out = self.root / 'units.json'
        inv = structural_units.build_inventory(src, out, mode='lines')
        self.assertEqual(['L000001', 'L000002', 'L000003'], [u['unit_id'] for u in inv['units']])
        report = structural_units.verify_inventory(out)
        self.assertEqual('READY', report['overall'])
        self.assertEqual(src.read_bytes(), structural_units.reassemble_units(out))

    def test_paragraph_inventory_covers_separators_without_loss(self):
        src = self.root / 'doc.md'
        src.write_text('First para.\n\nSecond line 1.\nSecond line 2.\n\nThird.', encoding='utf-8')
        out = self.root / 'units.json'
        inv = structural_units.build_inventory(src, out, mode='paragraphs')
        self.assertEqual(3, len(inv['units']))
        self.assertEqual(src.read_bytes(), structural_units.reassemble_units(out))
        self.assertEqual('READY', structural_units.verify_inventory(out)['overall'])

    def test_inventory_maps_units_to_coverage_chunks_and_becomes_stale(self):
        src = self.root / 'x.txt'
        src.write_text('one\ntwo\nthree\n', encoding='utf-8')
        cov = self.root / 'cov'
        source_coverage.ingest_text(src, cov, max_bytes=5)
        out = self.root / 'units.json'
        inv = structural_units.build_inventory(src, out, mode='lines', coverage_manifest=cov / 'manifest.json')
        self.assertTrue(all(u['chunk_ids'] for u in inv['units']))
        src.write_text('changed\n', encoding='utf-8')
        report = structural_units.verify_inventory(out)
        self.assertEqual('STALE', report['overall'])


if __name__ == '__main__':
    unittest.main()
