#!/usr/bin/env python3
"""M2: extraction states are explicit; unknown never becomes complete."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import extraction  # noqa: E402


def profile(**over):
    base = {"schema_version": 2, "extractor": "direct-text", "version": "1",
            "config_digest": "c", "supported_features": ["text"]}
    base.update(over)
    return base


def event(**over):
    base = {"schema_version": 2, "source_digest": "s", "canonical_digest": "c",
            "extractor": "direct-text", "extractor_version": "1", "config_digest": "c",
            "expected_inventory": {"pages": 2}, "produced_elements": {"pages": 2},
            "diagnostics": {}, "state": "INVENTORY_CHECKED"}
    base.update(over)
    return base


class ExtractionGateTests(unittest.TestCase):
    def test_direct_text_exact_on_identical(self):
        got = extraction.direct_text_event("ab" * 32, "ab" * 32)
        self.assertEqual(got["state"], "EXACT_TEXT")

    def test_direct_text_unknown_on_differing(self):
        got = extraction.direct_text_event("ab" * 32, "cd" * 32)
        self.assertEqual(got["state"], "UNKNOWN")

    def test_gap_in_claimed_inventory_rejected(self):
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event(produced_elements={}))

    def test_unknown_field_rejected(self):
        bad = event()
        bad["forged"] = 1
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(bad)

    def test_bad_state_rejected(self):
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_event(event(state="COMPLETE-ISH"))

    def test_profile_requires_identity(self):
        with self.assertRaises(extraction.ExtractionError):
            extraction.validate_profile(profile(extractor=""))
        self.assertEqual(extraction.validate_profile(profile())["extractor"], "direct-text")

    def test_readiness_mapping(self):
        self.assertEqual(extraction.readiness_from_state("EXACT_TEXT"), "READY")
        self.assertEqual(extraction.readiness_from_state("UNKNOWN"), "PARTIAL")
        self.assertEqual(extraction.readiness_from_state("ERROR"), "BLOCKED")

    def test_vocabulary_matches_engine(self):
        from integrity_v2 import engine_client
        engine = Path(__file__).resolve().parents[2] / "claude-mon"
        ok, env = engine_client.handshake(str(engine))
        self.assertTrue(ok, env)
        self.assertEqual(sorted(env["extraction_states"]), sorted(extraction.EXTRACTION_STATES))


if __name__ == "__main__":
    unittest.main(verbosity=2)
