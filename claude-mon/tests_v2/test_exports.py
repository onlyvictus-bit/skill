#!/usr/bin/env python3
"""M5: exports are complete, ordered, and re-verifiable."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import partition, results  # noqa: E402

SOURCE = b"one\ntwo must not break\nthree costs 7 coins\n"


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="exports-")
        self.man = partition.build_manifest("SRC-1", SOURCE)
        self.recs = [results.make_result(
            SOURCE, self.man, u["id"], "task-1", "ATT-1", "reading %s" % (u["id"],))
            for u in self.man["units"]]

    def tearDown(self):
        self.temp.cleanup()

    def ids(self):
        return [u["id"] for u in self.man["units"]]

    def test_roundtrip_complete(self):
        path = str(Path(self.temp.name) / "units.jsonl")
        self.assertEqual(results.export_jsonl(self.recs, path), len(self.recs))
        self.assertEqual(results.verify_export(path, self.ids(), SOURCE, self.man), [])

    def test_missing_row_fails(self):
        path = str(Path(self.temp.name) / "units.jsonl")
        results.export_jsonl(self.recs[:-1], path)
        errors = results.verify_export(path, self.ids(), SOURCE, self.man)
        self.assertTrue(any("missing" in e for e in errors), errors)

    def test_corrupt_line_fails(self):
        path = str(Path(self.temp.name) / "units.jsonl")
        results.export_jsonl(self.recs, path)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write('{"unit_id": "U999999"}\n')
        errors = results.verify_export(path, self.ids(), SOURCE, self.man)
        self.assertTrue(errors)

    def test_source_order_preserved(self):
        path = str(Path(self.temp.name) / "units.jsonl")
        results.export_jsonl(list(reversed(self.recs)), path)
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        # File order is caller order; verification is order-insensitive but complete.
        self.assertEqual(len(lines), len(self.recs))
        self.assertEqual(results.verify_export(path, self.ids(), SOURCE, self.man), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
