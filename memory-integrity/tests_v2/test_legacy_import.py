#!/usr/bin/env python3
"""M8: legacy v1 artifacts are history, never v2 proof."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import extraction, report, watchdog  # noqa: E402


class LegacyImportTests(unittest.TestCase):
    def test_legacy_complete_mark_rejected(self):
        # A v1-style hand-written COMPLETE has no v2 standing.
        with self.assertRaises(Exception):
            extraction.validate_event({"state": "COMPLETE-ISH", "schema_version": 2,
                                       "source_digest": "s", "canonical_digest": "c",
                                       "extractor": "x", "extractor_version": "1",
                                       "config_digest": "c", "expected_inventory": {},
                                       "produced_elements": {}, "diagnostics": {}})

    def test_legacy_memory_reply_rejected(self):
        out = watchdog.strict_roundtrip(_LegacyBackend(), "s", "canary")
        self.assertNotEqual(out["verdict"], "HEALTHY")

    def test_legacy_layer_values_rejected(self):
        with self.assertRaises(report.ReportError):
            report.compose({"scope": "COMPLETE", "extraction": "READY", "coverage": "READY",
                            "execution": "READY", "results": "READY", "semantic": "READY",
                            "persistence": "READY"})

    def test_legacy_counts_cannot_pass(self):
        out = report.compose(
            {"scope": "READY", "extraction": "READY", "coverage": "PARTIAL",
             "execution": "READY", "results": "READY", "semantic": "READY",
             "persistence": "READY"},
            counts={"units_done": 100, "units_total": 50})
        self.assertEqual(out["overall"], "PARTIAL")


class _LegacyBackend:
    """Mimics a v1-shaped loose memory reply: bare strings, no ids."""

    def remember(self, text):
        return "stored-ok"

    def search(self, query):
        return ["canary text here"]

    def fetch(self, record_id):
        return "canary text here"

    def delete(self, record_id):
        return True


if __name__ == "__main__":
    unittest.main(verbosity=2)
