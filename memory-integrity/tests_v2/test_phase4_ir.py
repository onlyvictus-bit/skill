#!/usr/bin/env python3
"""Phase 4 RED: embedding providers, provenance-first hybrid retrieval,
honest IR measurement. Must FAIL before implementation, pass after.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import embeddings, hybrid, ir_bench  # noqa: E402


class ProviderTests(unittest.TestCase):
    def test_hashed_provider_deterministic(self):
        a = embeddings.embed(["hello world"], provider="hashed")
        b = embeddings.embed(["hello world"], provider="hashed")
        self.assertEqual(a["vectors"], b["vectors"])
        self.assertTrue(a["meta"]["deterministic"])
        self.assertIn("artifact_hash", a["meta"])

    def test_learned_provider_refuses_without_approval(self):
        with self.assertRaises(embeddings.ProviderError):
            embeddings.embed(["x"], provider="learned-open-model")

    def test_unknown_provider_refused(self):
        with self.assertRaises(embeddings.ProviderError):
            embeddings.embed(["x"], provider="nope")


class HybridTests(unittest.TestCase):
    CANDIDATES = [
        {"id": "d1", "score": 0.9, "authorized": True, "stale": False},
        {"id": "d2", "score": 0.99, "authorized": False, "stale": False},
        {"id": "d3", "score": 0.8, "authorized": True, "stale": True},
        {"id": "d4", "score": 0.8, "authorized": True, "stale": False},
    ]

    def test_prefilter_removes_unauthorized_before_rank(self):
        ranked, dropped = hybrid.rerank(self.CANDIDATES, top_k=10)
        ids = [c["id"] for c in ranked]
        self.assertNotIn("d2", ids)
        self.assertNotIn("d3", ids)
        self.assertTrue({"d2", "d3"} <= set(dropped))

    def test_stable_tiebreak_by_id(self):
        ranked, _ = hybrid.rerank(self.CANDIDATES, top_k=10)
        self.assertEqual([c["id"] for c in ranked if c["score"] == 0.8],
                         ["d4"])

    def test_postfilter_rerun_after_rerank(self):
        ranked, _ = hybrid.rerank(self.CANDIDATES, top_k=10,
                                  rescore=lambda c: 0.0 if c["id"] == "d4" else c["score"])
        self.assertNotIn("d4", [c["id"] for c in ranked])

    def test_nonfinite_scores_rejected(self):
        bad = [dict(c, score=float("nan")) for c in self.CANDIDATES[:1]]
        ranked, dropped = hybrid.rerank(bad, top_k=10)
        self.assertEqual(ranked, [])
        self.assertIn("d1", dropped)
        with self.assertRaises(ValueError):
            hybrid.rerank(self.CANDIDATES, top_k=10,
                          rescore=lambda c: float("inf"))


class MetricTests(unittest.TestCase):
    JUDGMENTS = {"q1": {"d1", "d3"}}

    def test_recall_mrr_ndcg_hand_computed(self):
        ranked = ["d2", "d1", "d4", "d3"]
        self.assertAlmostEqual(ir_bench.recall_at_k(ranked, {"d1", "d3"}, 2), 0.5)
        self.assertAlmostEqual(ir_bench.recall_at_k(ranked, {"d1", "d3"}, 4), 1.0)
        self.assertAlmostEqual(ir_bench.mrr(ranked, {"d1", "d3"}), 0.5)
        self.assertTrue(0.0 < ir_bench.ndcg_at_k(ranked, {"d1", "d3"}, 4) < 1.0)
        self.assertEqual(ir_bench.ndcg_at_k(["d1", "d3"], {"d1", "d3"}, 2), 1.0)

    def test_empty_ranking_zero_not_error(self):
        self.assertEqual(ir_bench.recall_at_k([], {"d1"}, 5), 0.0)
        self.assertEqual(ir_bench.mrr([], {"d1"}), 0.0)

    def test_duplicate_ids_count_once(self):
        self.assertEqual(ir_bench.recall_at_k(["d1", "d1"], {"d1"}, 2), 1.0)
        self.assertEqual(ir_bench.mrr(["d9", "d1", "d1"], {"d1"}), 0.5)
        self.assertLessEqual(ir_bench.ndcg_at_k(["d1", "d1"], {"d1"}, 2), 1.0)


class HonestyTests(unittest.TestCase):
    def test_losing_variant_reported_not_hidden(self):
        report = ir_bench.compare(
            {"direct": ["d1"], "hybrid": ["d2"]}, {"d1": {"d1"}}, k=1)
        self.assertIn("hybrid", report["variants"])
        self.assertLess(report["variants"]["hybrid"]["recall@1"],
                        report["variants"]["direct"]["recall@1"])
        self.assertIn("winner", report)
        self.assertEqual(report["winner"], "direct")


if __name__ == "__main__":
    unittest.main(verbosity=1)
