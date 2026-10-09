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

    def test_incomplete_active_wheel_pin_remains_unverified(self):
        from unittest import mock
        class Dist:
            def read_text(self, name):
                return ("semantica/__init__.py,sha256=OqNPLbod4yFG-5xWfKr4rKq4PYe7ZqYl9s1hkPne7PA,10\n"
                        "semantica/extra.py,sha256=" + "b" * 43 + ",10\n")
        with (mock.patch("importlib.util.find_spec", return_value=object()),
              mock.patch("importlib.metadata.version", return_value="0.7.0"),
              mock.patch("importlib.metadata.distribution", return_value=Dist())):
            self.assertEqual(supply_chain.provenance_status("semantica"), "UNVERIFIED")


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

class SignedAuthorizationTests(unittest.TestCase):
    def test_sparql_signed_capability_is_graph_bound(self):
        import hashlib, hmac, json, os
        from unittest import mock
        graph = HiddenAuthorizationTests.GRAPH
        digest = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        token = {"graph_sha256": digest,
                 "signature": hmac.new(b"synthetic-private-key",
                                      ("sparql-hidden:" + digest).encode(), hashlib.sha256).hexdigest()}
        with mock.patch.dict(os.environ, {"SPARQL_HIDDEN_APPROVAL_KEY": "synthetic-private-key"}):
            self.assertEqual(sparql.query(graph, "SELECT ?s WHERE { ?s LINK public }",
                                          include_hidden=token), [{"s": "private"}])
            altered = {**graph, "project_id": "other"}
            with self.assertRaises(sparql.SparqlError):
                sparql.query(altered, "SELECT ?s WHERE { ?s LINK public }",
                             include_hidden=token)

    def test_graphrag_signed_scope_and_graph_digest_required(self):
        import hashlib, hmac, json, os
        from unittest import mock
        graph = GraphApprovalTests.GRAPH
        digest = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        message = ("graphrag:trusted-owner:project-A:" + digest).encode()
        approval = {"approver": "trusted-owner", "scope": "project-A", "graph_sha256": digest,
                    "signature": hmac.new(b"trusted-key", message, hashlib.sha256).hexdigest()}
        with mock.patch.dict(os.environ, {"GRAPHRAG_APPROVAL_KEY": "trusted-key"}):
            handle = graphrag.enable(approval)
            self.assertIn("B", graphrag.query(graph, "A", handle=handle)["visited"])
            self.assertIn(["A", "B"], graphrag.communities(graph, handle=handle))
            for changed in ({**graph, "project_id": "project-B"},
                            {**graph, "nodes": [{"id": "A"}, {"id": "B"}, {"id": "new"}]}):
                with self.assertRaises(graphrag.GraphragError):
                    graphrag.query(changed, "A", handle=handle)
            with self.assertRaises(graphrag.GraphragError):
                graphrag.communities(graph)

    def test_reviewer_witness_signed_by_trusted_issuer(self):
        import hashlib, hmac, os
        from unittest import mock
        witness = {"run_id": "trusted-run", "artifact_digest": "a" * 64}
        digest = "b" * 64
        payload = ("review:reviewer:producer:trusted-run:" + "a" * 64 + ":" + digest).encode()
        witness["signature"] = hmac.new(b"review-key", payload, hashlib.sha256).hexdigest()
        review = {"tier": "INDEPENDENT_VERIFIED", "oracle_digest": digest,
                  "reviewer_identity": {"id": "reviewer", "kind": "institution",
                                        "witness": witness}}
        with mock.patch.dict(os.environ, {"INDEPENDENT_REVIEW_WITNESS_KEY": "review-key"}):
            self.assertEqual(admission.check_reviewer_independence(
                review, producer_id="producer", expected_digest=digest), "INDEPENDENT_VERIFIED")
            with self.assertRaises(ValueError):
                admission.check_reviewer_independence(
                    review, producer_id="different-producer", expected_digest=digest)


class TimestampGuards(unittest.TestCase):
    def test_retraction_rejects_malformed_timestamp(self):
        row = BitemporalTests().claim()
        for invalid in ("~", "tomorrow", "2026-02-31T00:00:00Z", "2026-01-01"):
            store = truth.assert_claim(truth.new_store(), row, "op0")
            with self.assertRaises(truth.TruthError):
                truth.retract(store, "A", "source changed", "op1", known_at=invalid)


if __name__ == "__main__":
    unittest.main()
