#!/usr/bin/env python3
"""M4-R: regression tests for the independent-review findings F1-F7.

Each test fails on the pre-correction code and passes after it. A spy
adapter proves non-dispatch on every rejection path: passing helper tests
alone never closes this gate.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import budget, ledger, partition, providers, results, runner  # noqa: E402

PROFILE = {"schema_version": 2, "provider": "t", "model": "m", "encoding": "e",
           "encoding_version": "v", "context_limit": 3000, "output_limit": 200,
           "counting_method": "tiktoken", "endpoint": "test-endpoint", "purpose": "m4r",
           "max_spend": 0}
WORDS = lambda text: text.split()  # noqa: E731


class SpyAdapter(providers.ProviderAdapter):
    adapter_name = "spy"
    adapter_version = "1"
    evidence_class = "TEST_ONLY"

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.response_values = None

    def dispatch(self, prepared_bytes):
        self.calls += 1
        kind, payload = self.script.pop(0)
        base = dict(self.capabilities())
        if kind == "ok":
            import json
            expected = json.loads(prepared_bytes.decode("utf-8"))["primary_unit_ids"]
            base.update({"terminal_state": "ok", "results":
                         self.response_values or {uid: "r-%s" % uid for uid in expected}})
            return base
        base.update({"terminal_state": "error", "error": str(payload)})
        return base


def database():
    temp = tempfile.TemporaryDirectory(prefix="m4r-")
    db = ledger.connect(Path(temp.name) / "ledger.db")
    return temp, db, str(Path(temp.name) / "artifacts")


def prepare_full(db, art, work="W1", units=None, task="t"):
    ledger.create_work_item(db, work, task, "SRC-1")
    texts = units or {"U000001": "alpha beta"}
    source = next(iter(texts.values())).encode("utf-8")
    manifest = partition.build_manifest("SRC-1", source)
    return runner.prepare(db, art, work, task, texts, "do it", {"type": "object"},
                          {}, "spec-1", PROFILE, counter=WORDS, manifest=manifest,
                          source_bytes=source)


def approve_for(db, attempt_id, request_digest, provider="t", model="m"):
    return ledger.issue_approval(db, attempt_id, request_digest, provider, model,
                                 "test-endpoint", "m4r", 200, {"max_spend": 0})


class M4RTests(unittest.TestCase):
    def setUp(self):
        self.temp, self.db, self.art = database()

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_f1_total_context_enforced(self):
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(PROFILE, [{"id": "U1", "input_tokens": 3000}],
                                per_unit_output=10)

    def test_f3_negatives_and_duplicates_rejected(self):
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(PROFILE, [{"id": "U1", "input_tokens": 10}],
                                per_unit_output=10, safety_reserve=-1)
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(PROFILE, [{"id": "U1", "input_tokens": -5}],
                                per_unit_output=10)
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(PROFILE, [{"id": "U1", "input_tokens": 1},
                                          {"id": "U1", "input_tokens": 1}], per_unit_output=1)
        with self.assertRaises(budget.BudgetError):
            budget.plan_batches(PROFILE, [{"id": "U1", "input_tokens": True}],
                                per_unit_output=1)

    def test_f3_synthetic_counts_cannot_go_live(self):
        measurement = budget.measure_request(PROFILE, {"a": "x y"}, counter=WORDS)
        ok, _ = budget.qualify_for_live(PROFILE, measurement["methods"])
        self.assertFalse(ok)

    def test_f2_request_contains_material(self):
        raw, digest, measurement = providers.build_complete_request(
            "W1", "t", {"U1": "alpha beta"}, "do it", {"type": "object"}, {},
            "spec-1", PROFILE, counter=WORDS)
        import json
        body = json.loads(raw.decode("utf-8"))
        self.assertIn("alpha beta", body["materials"]["source_U1"])
        self.assertEqual(body["materials"]["instructions"], "do it")
        self.assertEqual(measurement["methods"], ["injected-counter"])

    def test_f4_adapter_traverses_real_path(self):
        att, digest = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        approval = approve_for(self.db, att, digest)
        spy = SpyAdapter([("ok", None)])
        manifest = partition.build_manifest("SRC-1", b"alpha beta")
        spy.response_values = {"U000001": results.make_result(
            b"alpha beta", manifest, "U000001", "t", att, "r-U000001")}
        runner.dispatch_via_adapter(self.db, self.art, spy, att, approval)
        self.assertEqual(spy.calls, 1)
        row = self.db.execute("SELECT state FROM attempts WHERE id=?", (att,)).fetchone()
        self.assertEqual(row["state"], "VALIDATED")
        runner.accept(self.db, self.art, att, "t", manifest, b"alpha beta",
                      {"provider": "t", "model": "m", "endpoint": "test-endpoint",
                       "purpose": "m4r", "max_output_tokens": 200})
        self.assertEqual(ledger.accepted_attempt(self.db, "W1"), att)

    def test_f4_reused_approval_never_dispatches(self):
        att, digest = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        approval = approve_for(self.db, att, digest)
        spy = SpyAdapter([("ok", None), ("ok", None)])
        runner.dispatch_via_adapter(self.db, self.art, spy, att, approval)
        with self.assertRaises(ledger.LedgerError):
            runner.dispatch_via_adapter(self.db, self.art, spy, att, approval)
        self.assertEqual(spy.calls, 1)

    def test_f5_missing_and_mismatched_results_rejected(self):
        ok, _ = providers.validate_response(
            {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
             "unit_ids": ["U1"], "raw_digest": "z" * 64}, ["U1"])
        self.assertFalse(ok)
        ok, _ = providers.validate_response(
            {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
             "unit_ids": ["U1"], "raw_digest": "z" * 64, "results": {"X": "y"}},
            ["U1"])
        self.assertFalse(ok)

    def test_f5_spoofed_digest_rejected(self):
        att, digest = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        approval = approve_for(self.db, att, digest)
        spy = SpyAdapter([("ok", None)])
        runner.dispatch_via_adapter(self.db, self.art, spy, att, approval)
        row = self.db.execute("SELECT response_digest FROM attempts WHERE id=?",
                              (att,)).fetchone()
        self.assertEqual(len(row["response_digest"]), 64)
        ok, reason = providers.validate_response(
            {"terminal_state": "ok", "evidence_class": "TEST_ONLY",
             "results": {"U1": "r"}, "raw_digest": "f" * 64},
            ["U1"], row["response_digest"])
        self.assertFalse(ok)
        self.assertIn("SPOOF", reason)

    def test_f6_unknown_and_mismatched_work_blocked(self):
        man = partition.build_manifest("SRC-1", b"aaa\n")
        ok, notes = runner.preflight(self.db, "NOPE", man, b"aaa\n", PROFILE, 20,
                                     counter=WORDS)
        self.assertFalse(ok, notes)
        prepare_full(self.db, self.art, work="W9")
        other = partition.build_manifest("OTHER", b"aaa\n")
        ok, notes = runner.preflight(self.db, "W9", other, b"aaa\n", PROFILE, 20,
                                     counter=WORDS)
        self.assertFalse(ok, notes)
        self.assertTrue(any("source" in n for n in notes), notes)

    def test_f6_uncertain_delivery_needs_decision(self):
        att, _ = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        ledger.transition(self.db,att,"DISPATCHING")
        ledger.transition(self.db,att,"DELIVERY_UNKNOWN",error="test crash after dispatch")
        man = partition.build_manifest("SRC-1", b"aaa\n")
        ok, notes = runner.preflight(self.db, "W1", man, b"aaa\n", PROFILE, 20,
                                     counter=WORDS)
        self.assertFalse(ok, notes)
        runner.record_retry_decision(self.db, "W1", att, "provider dashboard shows no charge")
        ok, notes = runner.preflight(self.db, "W1", man, b"aaa\n", PROFILE, 20,
                                     counter=WORDS)
        self.assertTrue(ok, notes)

    def test_f6_saved_response_resumes_not_resends(self):
        att, _ = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        approval = approve_for(self.db, att,
                               self.db.execute("SELECT request_digest FROM attempts WHERE id=?",
                                               (att,)).fetchone()["request_digest"])
        spy = SpyAdapter([("ok", None)])
        runner.dispatch_via_adapter(self.db, self.art, spy, att, approval)
        man = partition.build_manifest("SRC-1", b"aaa\n")
        ok, notes = runner.preflight(self.db, "W1", man, b"aaa\n", PROFILE, 20,
                                     counter=WORDS)
        self.assertFalse(ok, notes)
        self.assertTrue(any("resume" in n for n in notes), notes)
        self.assertEqual(spy.calls, 1)

    def test_f7_approval_bound_to_exact_request(self):
        att, digest = prepare_full(self.db, self.art)
        runner.approve(self.db, att, "ref-1")
        approval = approve_for(self.db, att, digest)
        other_att, other_digest = prepare_full(self.db, self.art, work="W2",
                                               units={"U000001": "other"})
        runner.approve(self.db, other_att, "ref-2")
        spy = SpyAdapter([("ok", None)])
        with self.assertRaises(ledger.LedgerError):
            runner.dispatch_via_adapter(self.db, self.art, spy, other_att, approval)
        self.assertEqual(spy.calls, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
