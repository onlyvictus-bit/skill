#!/usr/bin/env python3
"""R1 hardening: every m8 audit probe must now fail closed (F01, F02, F07,
F14-F18). Isolated repair copy only. Each test names its finding ID.
"""
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import (extraction, recall, report, semantic, source_audit,  # noqa: E402
                          watchdog)
from integrity_v2.adapters import ooxml_inventory, pdf_inventory  # noqa: E402

STAGE = Path(__file__).resolve().parents[1]
ENGINE = STAGE.parents[0] / "claude-mon"


class TestF01Extraction(unittest.TestCase):
    def test_100_expected_zero_produced_rejected(self):
        event = {"schema_version": 2, "source_digest": "s", "canonical_digest": "c",
                 "extractor": "fixture", "extractor_version": "1", "config_digest": "cfg",
                 "expected_inventory": {"pages": 100}, "produced_elements": {"pages": 0},
                 "diagnostics": ["ERROR: required pages missing"], "state": "INVENTORY_CHECKED"}
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event)

    def test_exact_text_wrong_digests_rejected(self):
        event = {"schema_version": 2, "source_digest": "s", "canonical_digest": "c",
                 "extractor": "f", "extractor_version": "1", "config_digest": "cfg",
                 "expected_inventory": {}, "produced_elements": {},
                 "diagnostics": [], "state": "EXACT_TEXT"}
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event)

    def test_exact_text_missing_digests_unknown(self):
        self.assertEqual(extraction.direct_text_event(None, None)["state"], "UNKNOWN")


class TestF02Semantic(unittest.TestCase):
    def test_empty_review_not_ready(self):
        ready, _ = semantic.strict_ready([])
        self.assertFalse(ready)

    def test_malformed_review_not_ready(self):
        ready, _ = semantic.strict_ready([{}])
        self.assertFalse(ready)

    def test_reversed_rule_flagged(self):
        rep = semantic.challenge_unit("U1", "The fee is 42 USD, never waived.",
                                      "The fee is 42 USD and always waived, not delayed.")
        self.assertTrue(rep["unresolved"])


class TestF07RunMap(unittest.TestCase):
    def test_empty_map_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            path = str(Path(temp) / "m.json")
            Path(path).write_text("{}", encoding="utf-8")
            with self.assertRaises(recall.RecallError):
                recall.load_run_map(path, {})

    def test_missing_dir_rejected(self):
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            path = str(Path(temp) / "m.json")
            Path(path).write_text(
                '{"run_dir": "nonexistent", "source_digests": {"S": "d"}, '
                '"artifact_digests": {"result": "missing"}, "generation": "g"}',
                encoding="utf-8")
            with self.assertRaises(recall.RecallError):
                recall.load_run_map(path, {"S": "d"})


class TestF14Watchdog(unittest.TestCase):
    class BadBackend:
        def __init__(self, malformed=False):
            self.deleted, self.malformed = False, malformed
            self.text = None

        def remember(self, text):
            self.text = text
            return {"id": "stored-id", "text": text}

        def search(self, query):
            hits = [] if self.deleted else [{"id": "stored-id", "text": self.text}]
            return {"hits": hits + ([123] if self.malformed else [])}

        def fetch(self, ident):
            return None if self.deleted else {"id": "WRONG-ID", "text": self.text}

        def delete(self, ident):
            self.deleted = True
            return {"deleted": True}

    def test_wrong_identity_fails(self):
        out = watchdog.strict_roundtrip(self.BadBackend(), "fixture", "canary")
        self.assertEqual(out["verdict"], "FAILED")
        self.assertIn("IDENTITY", out["reason"])

    def test_malformed_hits_blind(self):
        out = watchdog.strict_roundtrip(self.BadBackend(True), "fixture", "canary")
        self.assertEqual(out["verdict"], "BLIND")

    def test_dict_generations_unverified(self):
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": {"arbitrary": 1},
                                "generation_after": {"arbitrary": 2},
                                "same_data_identity": True}), "BOUNDARY_UNVERIFIED")


class TestF15Inventories(unittest.TestCase):
    def test_truncated_pdf_partial(self):
        inv = pdf_inventory.inventory_pdf(
            b"%PDF-1.7\n1 0 obj << /Type /Pages /Count 1 >> endobj\n"
            b"2 0 obj << /Type /Page >> endobj\n")
        self.assertTrue(inv["truncated"])
        self.assertEqual(pdf_inventory.readiness(inv), "PARTIAL")

    def test_hidden_sheet_detected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("xl/workbook.xml", '<workbook><sheets>'
                        '<sheet name="Hidden" state="hidden" sheetId="1"/>'
                        "</sheets></workbook>")
            zf.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")
        buf.seek(0)
        inv = ooxml_inventory.inventory_ooxml(buf)
        self.assertTrue([u for u in inv["unsupported"] if "hidden" in u["reason"]])
        self.assertEqual(ooxml_inventory.readiness(inv), "PARTIAL")


class TestF16Scope(unittest.TestCase):
    def test_unfrozen_dict_blocked(self):
        import hashlib
        digest = hashlib.sha256(b"A\n").hexdigest()
        verdict, _ = source_audit.audit_scope(
            {"sources": [{"path": "a.txt", "sha256": digest}]},
            {"a.txt": b"A\n"}, {})
        self.assertEqual(verdict, "BLOCKED")

    def test_missing_source_structured(self):
        from unittest.mock import patch
        sys.path.insert(0, str(ENGINE / "scripts"))
        from complete_read_v2 import inventory, partition
        with tempfile.TemporaryDirectory(prefix="r1-") as temp:
            root = Path(temp)
            (root / "a.txt").write_bytes(b"A\n")
            scope = inventory.freeze_scope(root, ["a.txt"])
            man = partition.build_manifest("S", b"A\n")
            verdict, findings = source_audit.audit_scope(
                scope, {}, {"missing.txt": man}, engine_root=str(ENGINE))
            self.assertEqual(verdict, "BLOCKED")
            self.assertTrue(findings)


class TestF17ReportGate(unittest.TestCase):
    def test_all_exempt_verified_blocked(self):
        out = report.compose_verified({n: "NOT_REQUIRED" for n in report.LAYERS},
                                      {n: "skip" for n in report.LAYERS}, {})
        self.assertEqual(out["overall"], "BLOCKED")

    def test_evidenced_ready_passes(self):
        layers = {n: "READY" for n in report.LAYERS}
        # R2: concrete, bounded, hash-verified proof files replace R1's
        # invented digest strings.  This remains a formatter gate only; the
        # full run verifier is tested separately.
        with tempfile.TemporaryDirectory(prefix="proof-") as temp:
            root = Path(temp)
            evidence = {}
            for i, name in enumerate(report.LAYERS):
                path = root / (name + ".txt")
                path.write_text("proof-%d" % i, encoding="utf-8")
                import hashlib
                evidence[name] = [{"path": path.name,
                                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]
            out = report.compose_verified(layers, {}, evidence, evidence_root=root)
        self.assertEqual(out["overall"], "BLOCKED")

    def test_ready_without_evidence_blocked(self):
        out = report.compose_verified({n: "READY" for n in report.LAYERS}, {}, {})
        self.assertEqual(out["overall"], "BLOCKED")


class TestF18Handshake(unittest.TestCase):
    def test_missing_engine_blocked(self):
        import hashlib
        h = hashlib.sha256()
        h.update(b"a.txt\x00" + b"d" * 64 + b"\x00")
        verdict, findings = source_audit.audit_scope(
            {"schema_version": 2, "frozen": True, "verdict": "FROZEN",
             "sources": [{"path": "a.txt", "sha256": "d" * 64}],
             "scope_digest": h.hexdigest()},
            {"a.txt": b"A\n"}, {},
            engine_root=str(Path(tempfile.gettempdir()) / "no-engine-here"))
        self.assertEqual(verdict, "BLOCKED")
        self.assertTrue(any("HANDSHAKE" in f for f in findings))


if __name__ == "__main__":
    unittest.main(verbosity=1)
