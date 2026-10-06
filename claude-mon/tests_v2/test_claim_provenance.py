#!/usr/bin/env python3
"""M5: synthesis claims map to units; required units are all claimed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import results  # noqa: E402


class ClaimProvenanceTests(unittest.TestCase):
    def test_full_mapping_passes(self):
        errors = results.validate_synthesis(
            [{"id": "CL1", "unit_ids": ["U1", "U2"]}], ["U1", "U2"])
        self.assertEqual(errors, [])

    def test_unmapped_claim_fails(self):
        errors = results.validate_synthesis([{"id": "CL1", "unit_ids": []}], ["U1"])
        self.assertTrue(any("UNMAPPED" in e for e in errors))

    def test_foreign_citation_fails(self):
        errors = results.validate_synthesis([{"id": "CL1", "unit_ids": ["U9"]}], ["U1"])
        self.assertTrue(any("FOREIGN" in e for e in errors))

    def test_unclaimed_unit_fails(self):
        errors = results.validate_synthesis([{"id": "CL1", "unit_ids": ["U1"]}],
                                            ["U1", "U2"])
        self.assertTrue(any("GAP" in e for e in errors))

    def test_partial_mode_allows_gap(self):
        errors = results.validate_synthesis([{"id": "CL1", "unit_ids": ["U1"]}],
                                            ["U1", "U2"], require_full=False)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
