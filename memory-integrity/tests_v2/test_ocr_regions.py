#!/usr/bin/env python3
"""M6: absent OCR/extraction backends stay UNSUPPORTED; nothing is faked."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2.adapters import docling_adapter as docling  # noqa: E402
from integrity_v2 import extraction  # noqa: E402


class OcrRegionTests(unittest.TestCase):
    def test_qualify_shape_always_valid(self):
        status = docling.qualify()
        self.assertIn(status["verdict"], ("QUALIFIED", "UNSUPPORTED"))
        self.assertIsInstance(status["available"], bool)

    def test_unavailable_refuses_convert(self):
        status = docling.qualify()
        if status["available"]:
            self.skipTest("docling present; unavailable-path not exercisable here")
        with self.assertRaises(docling.DoclingError):
            docling.convert("whatever.pdf")

    def test_unavailable_maps_to_unknown_state(self):
        status = docling.qualify()
        if status["available"]:
            self.skipTest("docling present")
        self.assertEqual(extraction.readiness_from_state("UNKNOWN"), "PARTIAL")
        event = {"schema_version": 2, "source_digest": "s", "canonical_digest": "c",
                 "extractor": "docling", "extractor_version": "?",
                 "config_digest": "?", "expected_inventory": {"pages": 3},
                 "produced_elements": {"pages": 1},
                 "diagnostics": {"missing": ["ocr"]}, "state": "PARTIAL"}
        self.assertEqual(extraction.validate_event(event)["state"], "PARTIAL")

    def test_no_silent_ocr_claim(self):
        # No OCR helper exists anywhere in the adapters package.
        import integrity_v2.adapters as adapters
        names = " ".join(dir(adapters))
        self.assertNotIn("ocr", names.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
