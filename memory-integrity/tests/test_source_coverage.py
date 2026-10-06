import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "source_coverage.py"


class SourceCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("source_coverage", SCRIPT)
        cls.sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sc)

    def test_exact_roundtrip_and_complete_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "big.txt"
            src.write_text("alpha\nβeta\ngamma\n" * 100, encoding="utf-8")
            out = root / "coverage"
            manifest = self.sc.ingest_text(src, out, max_bytes=97)
            rebuilt = self.sc.reassemble(out / "manifest.json")
            self.assertEqual(src.read_bytes(), rebuilt)
            self.sc.mark_all_complete(out / "manifest.json", out / "receipts.jsonl")
            report = self.sc.verify(out / "manifest.json", out / "receipts.jsonl")
            self.assertEqual("COVERAGE_COMPLETE", report["coverage_status"])
            self.assertEqual([], report["missing_chunk_ids"])
            self.assertEqual([], report["duplicate_primary_chunk_ids"])
            self.assertFalse(report["stale"])
            self.assertEqual(manifest["source_sha256"], report["source_sha256"])

    def test_missing_receipt_is_reported_not_rounded_up(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"
            src.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            out = root / "coverage"
            self.sc.ingest_text(src, out, max_bytes=5)
            self.sc.mark_all_complete(out / "manifest.json", out / "receipts.jsonl")
            lines = (out / "receipts.jsonl").read_text().splitlines()
            (out / "receipts.jsonl").write_text("\n".join(lines[:-1]) + "\n")
            report = self.sc.verify(out / "manifest.json", out / "receipts.jsonl")
            self.assertEqual("PARTIAL", report["coverage_status"])
            self.assertEqual(1, len(report["missing_chunk_ids"]))

    def test_source_change_marks_manifest_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"
            src.write_text("stable\n", encoding="utf-8")
            out = root / "coverage"
            self.sc.ingest_text(src, out, max_bytes=4)
            self.sc.mark_all_complete(out / "manifest.json", out / "receipts.jsonl")
            src.write_text("changed\n", encoding="utf-8")
            report = self.sc.verify(out / "manifest.json", out / "receipts.jsonl")
            self.assertTrue(report["stale"])
            self.assertEqual("STALE", report["coverage_status"])

    def test_duplicate_primary_receipt_is_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"
            src.write_text("abcdef\n", encoding="utf-8")
            out = root / "coverage"
            self.sc.ingest_text(src, out, max_bytes=3)
            self.sc.mark_all_complete(out / "manifest.json", out / "receipts.jsonl")
            first = (out / "receipts.jsonl").read_text().splitlines()[0]
            with (out / "receipts.jsonl").open("a", encoding="utf-8") as f:
                f.write(first + "\n")
            report = self.sc.verify(out / "manifest.json", out / "receipts.jsonl")
            self.assertEqual("INVALID", report["coverage_status"])
            self.assertTrue(report["duplicate_primary_chunk_ids"])


if __name__ == "__main__":
    unittest.main()

class SourceCoverageExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("source_coverage_extra", SCRIPT)
        cls.sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sc)

    def test_document_extraction_status_is_separate_from_canonical_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = root / "scan.pdf"
            original.write_bytes(b"%PDF-fake-binary")
            canonical = root / "docling.json"
            canonical.write_text('{"text":"hello"}\n', encoding="utf-8")
            out = root / "coverage"
            self.sc.ingest_text(
                canonical,
                out,
                max_bytes=8,
                origin_path=original,
                extractor="docling:test",
                extraction_status="PARTIAL",
            )
            self.sc.mark_all_complete(out / "manifest.json", out / "receipts.jsonl")
            report = self.sc.verify(out / "manifest.json", out / "receipts.jsonl")
            self.assertEqual("COVERAGE_COMPLETE", report["coverage_status"])
            self.assertEqual("PARTIAL", report["extraction_status"])
            self.assertEqual("BLOCKED", report["overall_status"])

    def test_multiple_attempts_are_allowed_but_latest_attempt_controls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"
            src.write_text("abcdef\n", encoding="utf-8")
            out = root / "coverage"
            self.sc.ingest_text(src, out, max_bytes=32)
            manifest = out / "manifest.json"
            receipts = out / "receipts.jsonl"
            cid = json.loads(manifest.read_text())["chunks"][0]["chunk_id"]
            self.sc.record_receipt(manifest, receipts, cid, "ERROR", note="first attempt")
            r2 = self.sc.record_receipt(manifest, receipts, cid, "COMPLETE", note="retry")
            self.assertEqual(2, r2["attempt"])
            report = self.sc.verify(manifest, receipts)
            self.assertEqual("COVERAGE_COMPLETE", report["coverage_status"])
            self.assertEqual([], report["duplicate_primary_chunk_ids"])

class SourceCoverageSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("source_coverage_safety", SCRIPT)
        cls.sc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.sc)

    def test_invalid_utf8_is_rejected_not_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "bad.bin"
            src.write_bytes(b"abc\xffdef")
            with self.assertRaises(UnicodeDecodeError):
                self.sc.ingest_text(src, root / "out", max_bytes=4)
