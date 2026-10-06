#!/usr/bin/env python3
"""M6: original/canonical digest binding is recomputed, never trusted."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "claude-mon" / "scripts"))

from integrity_v2 import extraction  # noqa: E402
from complete_read_v2 import partition  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ProvenanceTests(unittest.TestCase):
    def test_matching_binding_verifies(self):
        original = b"page one text\n"
        canonical = original  # direct-text route
        man = partition.build_manifest("SRC-1", canonical)
        event = {"schema_version": 2, "source_digest": sha(original),
                 "canonical_digest": man["source_digest"],
                 "extractor": "direct-text", "extractor_version": "1",
                 "config_digest": "c", "expected_inventory": {}, "produced_elements": {},
                 "diagnostics": {}, "state": "EXACT_TEXT"}
        self.assertEqual(extraction.validate_event(event)["state"], "EXACT_TEXT")
        self.assertEqual(man["source_digest"], sha(canonical))

    def test_swapped_canonical_detected(self):
        man_a = partition.build_manifest("SRC-A", b"aaa\n")
        man_b = partition.build_manifest("SRC-B", b"bbb\n")
        event = {"schema_version": 2, "source_digest": man_a["source_digest"],
                 "canonical_digest": man_b["source_digest"],
                 "extractor": "direct-text", "extractor_version": "1",
                 "config_digest": "c", "expected_inventory": {}, "produced_elements": {},
                 "diagnostics": {}, "state": "EXACT_TEXT"}
        # R1 (F01): a swapped EXACT_TEXT claim is rejected, not returned.
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event)
        self.assertNotEqual(man_a["source_digest"], man_b["source_digest"])
        self.assertNotEqual(
            extraction.direct_text_event(man_a["source_digest"],
                                         man_b["source_digest"])["state"], "EXACT_TEXT")

    def test_event_with_wrong_state_rejected(self):
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event({"schema_version": 2})


if __name__ == "__main__":
    unittest.main(verbosity=2)
