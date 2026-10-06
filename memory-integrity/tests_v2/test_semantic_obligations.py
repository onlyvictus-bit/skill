#!/usr/bin/env python3
"""M5: strict challenges catch seeded traps; unresolved blocks readiness."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import semantic  # noqa: E402


class SemanticObligationTests(unittest.TestCase):
    def test_negation_trap(self):
        rep = semantic.challenge_unit("U1", "Refunds must not exceed 30 days.",
                                      "Refunds are allowed any time.")
        self.assertIn("negation", rep["unresolved"])
        ready, blockers = semantic.strict_ready([rep])
        self.assertFalse(ready)
        self.assertTrue(blockers)

    def test_number_trap(self):
        rep = semantic.challenge_unit("U2", "The fee is 42 USD per quarter.",
                                      "There is a fee.")
        self.assertTrue(any("42" in u for u in rep["unresolved"]))
        ready, _ = semantic.strict_ready([rep])
        self.assertFalse(ready)

    def test_clean_unit_passes(self):
        rep = semantic.challenge_unit("U3", "The fee is 42 USD, never waived.",
                                      "Fee 42 USD, must not waive.")
        self.assertEqual(rep["unresolved"], [])
        ready, _ = semantic.strict_ready([rep])
        self.assertTrue(ready)

    def test_empty_interpretation_unresolved(self):
        rep = semantic.challenge_unit("U4", "Some rule.", "  ")
        self.assertIn("nonempty", rep["unresolved"])

    def test_missing_original_rejected(self):
        with self.assertRaises(semantic.SemanticError):
            semantic.challenge_unit("U5", "  ", "text")

    def test_dependency_reconciliation(self):
        by_id = {"A": {"disposition": "resolved"}, "B": {"disposition": "unresolved"}}
        findings = semantic.reconcile_dependencies(
            by_id, [{"id": "A", "requires": ["B"], "conflicts_with": []}])
        self.assertTrue(any("unresolved unit B" in f["detail"] for f in findings))
        both = {"A": {"disposition": "resolved"}, "C": {"disposition": "resolved"}}
        findings = semantic.reconcile_dependencies(
            both, [{"id": "A", "requires": [], "conflicts_with": ["C"]}])
        self.assertTrue(any("conflict" in f["detail"] for f in findings))
        ok = semantic.reconcile_dependencies(
            {"A": {"disposition": "resolved"}}, [{"id": "A", "requires": [], "conflicts_with": []}])
        self.assertEqual(ok, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
