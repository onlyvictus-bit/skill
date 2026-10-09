#!/usr/bin/env python3
"""Phase 2 RED: truth maintenance, bitemporal replay, entity canonicalization.

Each test names its requirement. Must FAIL before implementation, pass after,
without weakening any existing suite.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import truth  # noqa: E402


def assertion(aid, text, sources=("S1",), kind="OBSERVED"):
    return {"id": aid, "source_units": list(sources), "claim": {"type": kind, "text": text},
            "provenance": {"source_digest": "d" * 64, "generation": "g1", "producer": "p1"}}


class RetractionTests(unittest.TestCase):
    def test_correction_retracts_derived_keeps_history(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "base fact"), op_id="op-1")
        store = truth.assert_claim(store, assertion("A2", "derived", kind="DERIVED"), op_id="op-2",
                                   premises=["A1"])
        store, affected = truth.retract(store, "A1", "source corrected", op_id="op-3")
        self.assertIn("A1", affected)
        self.assertIn("A2", affected)
        self.assertEqual(truth.status(store, "A1"), "RETRACTED")
        self.assertEqual(truth.status(store, "A2"), "RETRACTED")
        self.assertTrue(truth.history(store, "A1"))

    def test_retract_idempotent(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "x"), op_id="op-1")
        store, _ = truth.retract(store, "A1", "why", op_id="op-2")
        store2, affected2 = truth.retract(store, "A1", "why", op_id="op-2")
        self.assertEqual(affected2, [])
        self.assertEqual(truth.event_count(store2), truth.event_count(store))

    def test_conflicting_supports_flagged_not_chosen(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "up"), op_id="op-1")
        store = truth.assert_claim(store, assertion("A2", "down"), op_id="op-2")
        store = truth.contradicts(store, "A1", "A2", op_id="op-3")
        self.assertEqual(truth.status(store, "A1"), "CONFLICTED")
        self.assertEqual(truth.status(store, "A2"), "CONFLICTED")


class BitemporalTests(unittest.TestCase):
    def test_as_of_excludes_future_known(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "old"), op_id="op-1",
                                   known_from="2026-01-01T00:00:00Z")
        store = truth.assert_claim(store, assertion("A2", "new"), op_id="op-2",
                                   known_from="2026-06-01T00:00:00Z")
        visible = truth.known_as_of(store, "2026-03-01T00:00:00Z")
        self.assertIn("A1", visible)
        self.assertNotIn("A2", visible)

    def test_out_of_order_correction_no_lookahead(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "v1"), op_id="op-1",
                                   known_from="2026-06-01T00:00:00Z",
                                   valid_from="2026-01-01T00:00:00Z")
        store = truth.correct(store, "A1", "v0-was-wrong", "2026-01-01T00:00:00Z",
                              "2026-03-01T00:00:00Z", op_id="op-2")
        self.assertIn("A1", truth.as_valid_at(store, "2026-02-01T00:00:00Z"))
        self.assertTrue(truth.history(store, "A1"))


class EntityTests(unittest.TestCase):
    def test_possible_match_never_auto_merges(self):
        store = truth.new_store()
        store = truth.register_entity(store, "E1", ["Alpha"], op_id="op-1")
        store = truth.register_entity(store, "E2", ["Alpha Inc"], op_id="op-2")
        store = truth.possible_match(store, "E1", "E2", 0.97, op_id="op-3")
        self.assertNotEqual(truth.canonical_of(store, "E2"), "E1")

    def test_explicit_merge_and_rollback(self):
        store = truth.new_store()
        store = truth.register_entity(store, "E1", ["Alpha"], op_id="op-1")
        store = truth.register_entity(store, "E2", ["Alpha Inc"], op_id="op-2")
        store = truth.merge_entities(store, "E1", "E2", "same-as", op_id="op-3")
        self.assertEqual(truth.canonical_of(store, "E2"), "E1")
        store = truth.unmerge_entities(store, "E1", "E2", op_id="op-4")
        self.assertEqual(truth.canonical_of(store, "E2"), "E2")


class ReplayTests(unittest.TestCase):
    def test_duplicate_mutation_single_effect(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "x"), op_id="op-1")
        store = truth.assert_claim(store, assertion("A1", "x"), op_id="op-1")
        self.assertEqual(truth.event_count(store), 1)

    def test_replay_twice_same_state(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "x"), op_id="op-1")
        store, _ = truth.retract(store, "A1", "why", op_id="op-2")
        replayed = truth.replay(truth.events(store))
        self.assertEqual(truth.status(replayed, "A1"), "RETRACTED")
        self.assertEqual(truth.event_count(replayed), truth.event_count(store))


class AuthorityTests(unittest.TestCase):
    def test_fable_projection_read_only(self):
        store = truth.new_store()
        decisions = [{"id": "D1", "rationale": "r", "evidence": ["e"],
                      "time": "2026-01-01T00:00:00Z", "superseded_by": None}]
        projected, writes = truth.project_fable_decisions(store, decisions)
        self.assertEqual(writes, [])
        self.assertIn("D1", [n["id"] for n in projected["nodes"]])

    def test_contradiction_triggers_review_not_override(self):
        store = truth.new_store()
        store = truth.assert_claim(store, assertion("A1", "graph says down"), op_id="op-1")
        out, writes = truth.project_fable_decisions(store, [{"id": "D1", "rationale": "up",
                                                             "evidence": [], "time": "t",
                                                             "superseded_by": None}])
        self.assertEqual(writes, [])
        self.assertIn("D1", [f["id"] for f in out.get("review_flags", [])])


if __name__ == "__main__":
    unittest.main(verbosity=1)
