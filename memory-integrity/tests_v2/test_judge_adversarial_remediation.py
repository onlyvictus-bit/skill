"""Adversarial regressions for the independent Fable Judge findings.

Do not weaken these tests to obtain a green build; each checks a real trust boundary.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from knowledge_bridge import sparql, graphrag, admission, supply_chain, truth, ir_bench, hybrid


class HiddenAuthorizationTests(unittest.TestCase):
    GRAPH = {"nodes": [{"id": "private", "hidden": True}, {"id": "public"}],
             "edges": [{"subject": "private", "predicate": "LINK", "object": "public"}]}

    def test_arbitrary_hidden_justification_fails_closed(self):
        with self.assertRaises(sparql.SparqlError):
            sparql.query(self.GRAPH, "SELECT ?s WHERE { ?s LINK public }",
                         include_hidden="approved")

    def test_hidden_edge_does_not_leak_through_predicate_or_object(self):
        self.assertEqual(sparql.query(
            self.GRAPH, "SELECT ?p WHERE { private ?p public }"), [])


class GraphApprovalTests(unittest.TestCase):
    GRAPH = {"project_id": "project-A",
             "nodes": [{"id": "A"}, {"id": "B"}],
             "edges": [{"subject": "A", "predicate": "EDGE", "object": "B"}]}

    def test_self_declared_approval_rejected(self):
        with self.assertRaises(graphrag.GraphragError):
            graphrag.enable({"approver": "anyone", "scope": "project-A"})

    def test_wrong_scope_never_accepted_for_graph(self):
        with self.assertRaises(graphrag.GraphragError):
            handle = graphrag.enable({"approver": "anyone", "scope": "project-B"})
            graphrag.query(self.GRAPH, "A", handle=handle)


class ReviewerIdentityTests(unittest.TestCase):
    def test_self_signed_witness_not_independent(self):
        review = {"tier": "INDEPENDENT_VERIFIED", "oracle_digest": "a" * 64,
                  "reviewer_identity": {"id": "someone-else", "kind": "agent",
                                        "witness": {"run_id": "invented",
                                                    "artifact_digest": "b" * 64}}}
        with self.assertRaises(ValueError):
            admission.check_reviewer_independence(review, producer_id="producer")


class WheelHashTests(unittest.TestCase):
    def test_record_digest_uses_second_field_and_rejects_bad_sha(self):
        import json
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / "lock.json"
            lock.write_text(json.dumps({"pins": [{
                "name": "example_pkg", "version": "1.0", "revision": "r", "source": "fixture",
                "record_sha256": {"lib.py": "a" * 43}}]}))
            class Dist:
                def read_text(self, name):
                    self_name = name
                    return "lib.py,sha256=" + "b" * 43 + ",10\n"
            with mock.patch.object(supply_chain, "LOCK", lock), \
                 mock.patch("importlib.util.find_spec", return_value=object()), \
                 mock.patch("importlib.metadata.version", return_value="1.0"), \
                 mock.patch("importlib.metadata.distribution", return_value=Dist()):
                with self.assertRaises(supply_chain.SupplyChainError):
                    supply_chain.provenance_status("example_pkg")

    def test_missing_active_record_pins_are_not_verified(self):
        from unittest import mock
        class Dist:
            def read_text(self, name):
                return "example_pkg/__init__.py,sha256=" + "a" * 43 + ",10\n"
        with mock.patch("importlib.util.find_spec", return_value=object()), \
             mock.patch("importlib.metadata.version", return_value="0.7.0"), \
             mock.patch("importlib.metadata.distribution", return_value=Dist()):
            self.assertNotEqual(supply_chain.provenance_status("semantica"), "VERIFIED")


class BitemporalTests(unittest.TestCase):
    def claim(self):
        return {"id": "A", "claim": {"type": "OBSERVED", "text": "A"},
                "provenance": {"source_digest": "abc", "generation": "g", "producer": "p"}}

    def test_retraction_without_known_at_is_rejected(self):
        store = truth.assert_claim(truth.new_store(), self.claim(), "op1",
                                   known_from="2026-01-01T00:00:00Z")
        with self.assertRaises(truth.TruthError):
            truth.retract(store, "A", "correction", "op2")

    def test_correction_requires_discovery_time(self):
        store = truth.assert_claim(truth.new_store(), self.claim(), "op1",
                                   known_from="2026-01-01T00:00:00Z")
        with self.assertRaises(truth.TruthError):
            truth.correct(store, "A", "correction", "2025-12-01T00:00:00Z",
                          "2025-12-31T00:00:00Z", "op2")


class MetricsTests(unittest.TestCase):
    def test_deduplicated_cutoff_consistent_with_recall(self):
        result = ir_bench.run_variant("duplicate", ["A", "A", "B"],
                                      {"q": {"A", "B"}}, k=2)
        self.assertEqual(result["recall@2"], 1.0)
        self.assertEqual(result["missing_required"], 0)

    def test_missing_freshness_excluded(self):
        ranked, dropped = hybrid.rerank([{"id": "unknown", "authorized": True,
                                         "score": 0.9}])
        self.assertEqual(ranked, [])
        self.assertIn("unknown", dropped)


if __name__ == "__main__":
    unittest.main()
