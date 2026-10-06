#!/usr/bin/env python3
"""M3/M4 coordination contracts and execution guards.

These tests use the public runner and durable ledger.  A Beads-shaped graph
fixture is deliberately labelled native-unqualified: it establishes policy
behaviour only and never invokes a native executable.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import artifacts, coordination, ledger, partition, providers, results, runner  # noqa: E402

PROFILE = {"schema_version": 2, "provider": "fixture", "model": "fixture-1",
           "encoding": "test-char", "encoding_version": "test-v1",
           "context_limit": 4000, "output_limit": 100, "counting_method": "test",
           "endpoint": "test-only-transport", "purpose": "coordination",
           "max_spend": 0}


def graph(nodes, edges, revision="fixture-r1"):
    return {"schema_version": 1, "workspace_id": "WS-1", "requirement_digest": "a" * 64,
            "revision": revision, "native_observation": "FIXTURE_NATIVE_UNQUALIFIED",
            "nodes": nodes, "edges": edges, "complete": True, "page_complete": True}


def policy(task_id, source="SRC-1"):
    source_digest = hashlib.sha256(b"alpha").hexdigest()
    profile_digest = hashlib.sha256(json.dumps(PROFILE, sort_keys=True, separators=(",", ":"),
                                               ensure_ascii=False).encode("utf-8")).hexdigest()
    return {"schema_version": 1, "coordination_required": True, "workspace_id": "WS-1",
            "task_id": task_id, "run_id": "RUN-1", "source_id": source,
            "source_digest": source_digest, "profile_digest": profile_digest,
            "requirement_digest": "a" * 64, "fence": "F-1"}


class SpyAdapter(providers.ProviderAdapter):
    adapter_name = "coordination-spy"
    adapter_version = "1"
    evidence_class = "TEST_ONLY"

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def dispatch(self, _request):
        self.calls += 1
        response = dict(self.capabilities())
        response.update({"terminal_state": "ok", "results": self.response})
        return response


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r3-coord-")
        self.db = ledger.connect(Path(self.temp.name) / "ledger.sqlite")
        self.artifacts = str(Path(self.temp.name) / "artifacts")
        ledger.create_work_item(self.db, "A", "task-A", "SRC-1")
        ledger.create_work_item(self.db, "B", "task-B", "SRC-1")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def _register(self):
        self.snapshot = graph(["A", "B"], [{"from": "A", "to": "B", "kind": "hard"}])
        self.policies = {ident: policy(ident) for ident in ("A", "B")}
        self.contexts = {ident: coordination.observed_context(self.policies[ident], self.snapshot)
                         for ident in ("A", "B")}
        self.envelope = coordination.context_envelope(self.contexts)
        coordination.register_task(self.db, "A", self.policies["A"], self.snapshot, self.artifacts)
        coordination.register_task(self.db, "B", self.policies["B"], self.snapshot, self.artifacts)

    def _prepare(self, work_id, task_digest, source=b"alpha", context=None):
        manifest = partition.build_manifest("SRC-1", source)
        return runner.prepare(self.db, self.artifacts, work_id, task_digest,
                              {"U000001": source.decode("utf-8")}, "audit",
                              {"type": "object"}, {}, "spec-1", PROFILE,
                              counter=lambda value: value, manifest=manifest,
                              source_bytes=source, coordination_context=context), manifest

    def _accept_a(self):
        (attempt, digest), manifest = self._prepare("A", "task-A", context=self.contexts["A"])
        runner.approve(self.db, attempt, "human-ref")
        approval = ledger.issue_approval(self.db, attempt, digest, "fixture", "fixture-1",
                                         "test-only-transport", "coordination", 100,
                                         {"max_spend": 0})
        record = results.make_result(b"alpha", manifest, "U000001", "task-A", attempt, "ok")
        adapter = SpyAdapter({"U000001": record})
        runner.dispatch_via_adapter(self.db, self.artifacts, adapter, attempt, approval,
                                    coordination_context=self.contexts["A"])
        runner.accept(self.db, self.artifacts, attempt, "task-A", manifest, b"alpha",
                      {"provider": "fixture", "model": "fixture-1",
                       "endpoint": "test-only-transport", "purpose": "coordination",
                       "max_output_tokens": 100}, coordination_context=self.contexts["A"])
        return attempt

    def test_missing_prerequisite_blocks_prepare_without_attempt(self):
        self._register()
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_BLOCKED"):
            self._prepare("B", "task-B", context=self.envelope)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM attempts WHERE work_item_id='B'").fetchone()[0], 0)

    def test_verified_prerequisite_allows_b_then_revoke_blocks_current_applicability(self):
        self._register()
        self._accept_a()
        decision = coordination.evaluate(self.db, "B", self.artifacts, self.envelope, "prepare")
        self.assertTrue(decision["ok"], decision)
        ledger.revoke(self.db, "A", "upstream source stale")
        decision = coordination.evaluate(self.db, "B", self.artifacts, self.envelope, "report")
        self.assertFalse(decision["ok"])
        self.assertTrue(any(reason.startswith("A:") for reason in decision["blocked"]), decision)

    def test_caller_off_mode_or_new_id_cannot_downgrade_registered_task(self):
        self._register()
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_CONTEXT"):
            coordination.guard(self.db, "B", self.artifacts, {"mode": "OFF"}, "prepare")
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_CONTEXT"):
            coordination.guard(self.db, "B", self.artifacts, policy("OTHER"), "prepare")

    def test_deleted_policy_cannot_be_reclassified_as_standalone_off(self):
        self._register()
        self.db.execute("DELETE FROM meta WHERE key='coordination:A'")
        self.assertFalse(coordination.evaluate(self.db,"A",self.artifacts,None,"prepare")["ok"])
        with self.assertRaises(ledger.LedgerError):
            self._prepare("A","task-A")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],0)

    def test_revocation_between_guard_and_dispatch_is_checked_before_approval_spend(self):
        self._register()
        self._accept_a()
        (attempt,digest),_=self._prepare("B","task-B",context=self.envelope)
        runner.approve(self.db,attempt,"fixture-human")
        approval=ledger.issue_approval(self.db,attempt,digest,"fixture","fixture-1","test-only-transport","coordination",100,{"max_spend":0})
        original=coordination.guard
        revoked=False
        def revoke_after_first_guard(*args,**kwargs):
            nonlocal revoked
            out=original(*args,**kwargs)
            if not revoked:
                revoked=True
                ledger.revoke(self.db,"A","changed before serialized approval consumption")
            return out
        adapter=SpyAdapter({})
        with mock.patch.object(coordination,"guard",side_effect=revoke_after_first_guard):
            with self.assertRaises(ledger.LedgerError):
                runner.dispatch_via_adapter(self.db,self.artifacts,adapter,attempt,approval,coordination_context=self.envelope)
        self.assertEqual(adapter.calls,0)
        self.assertEqual(self.db.execute("SELECT consumed FROM approvals WHERE id=?",(approval,)).fetchone()[0],0)

    def test_uncertain_coordinated_delivery_blocks_low_level_replacement_attempt(self):
        self._register()
        (attempt,digest),_=self._prepare("A","task-A",context=self.envelope)
        runner.approve(self.db,attempt,"fixture-human")
        approval=ledger.issue_approval(self.db,attempt,digest,"fixture","fixture-1","test-only-transport","coordination",100,{"max_spend":0})
        class UnknownAdapter(SpyAdapter):
            def dispatch(self,_request):
                self.calls+=1
                raise RuntimeError("delivery unknown")
        first=UnknownAdapter({})
        runner.dispatch_via_adapter(self.db,self.artifacts,first,attempt,approval,coordination_context=self.envelope)
        self.assertEqual(first.calls,1)
        self.assertEqual(self.db.execute("SELECT state FROM attempts WHERE id=?",(attempt,)).fetchone()[0],"DELIVERY_UNKNOWN")
        count=self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        with self.assertRaises(ledger.LedgerError):
            ledger.begin_attempt(self.db,"A")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],count)
        self.assertFalse(coordination.evaluate(self.db,"A",self.artifacts,self.envelope,"prepare")["ok"])
        # A generic reason string is not an approved new coordinated basis.
        runner.record_retry_decision(self.db,"A",attempt,"caller-declared retry")
        with self.assertRaises(ledger.LedgerError):
            self._prepare("A","task-A",context=self.envelope)

    def test_graph_rejects_cycle_missing_and_unsupported_relation(self):
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_GRAPH_CYCLE"):
            coordination.register_task(self.db, "A", policy("A"),
                                       graph(["A", "B"], [{"from": "A", "to": "B", "kind": "hard"},
                                                          {"from": "B", "to": "A", "kind": "hard"}]),
                                       self.artifacts)
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_GRAPH_NODE"):
            coordination.register_task(self.db, "A", policy("A"),
                                       graph(["A"], [{"from": "Z", "to": "A", "kind": "hard"}]),
                                       self.artifacts)
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_GRAPH_KIND"):
            coordination.register_task(self.db, "A", policy("A"),
                                       graph(["A", "B"], [{"from": "A", "to": "B", "kind": "soft"}]),
                                       self.artifacts)

    def test_blocked_dispatch_spends_no_approval_and_calls_no_adapter(self):
        self._register()
        self._accept_a()
        (attempt, digest), _manifest = self._prepare("B", "task-B", context=self.envelope)
        runner.approve(self.db, attempt, "human-ref")
        approval = ledger.issue_approval(self.db, attempt, digest, "fixture", "fixture-1",
                                         "test-only-transport", "coordination", 100,
                                         {"max_spend": 0})
        ledger.revoke(self.db,"A","upstream review withdrawn after preparation")
        adapter = SpyAdapter({})
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_BLOCKED"):
            runner.dispatch_via_adapter(self.db, self.artifacts, adapter, attempt, approval,
                                        coordination_context=self.envelope)
        self.assertEqual(adapter.calls, 0)
        self.assertEqual(self.db.execute("SELECT consumed FROM approvals WHERE id=?", (approval,)).fetchone()[0], 0)

    def test_raw_protected_transitions_and_legacy_path_refuse_missing_context(self):
        self._register()
        attempt = ledger.begin_attempt(self.db,"A")
        with self.assertRaisesRegex(ledger.LedgerError,"E_COORD_CONTEXT"):
            ledger.transition(self.db,attempt,"PREPARED",request_digest="a"*64)
        ledger.transition(self.db,attempt,"CANCELLED")
        (attempt,digest), _ = self._prepare("A","task-A",context=self.envelope)
        runner.approve(self.db,attempt,"fixture-approval")
        spy = runner.FakeProvider([("ok",b"never")])
        with self.assertRaisesRegex(ledger.LedgerError,"E_COORD_LEGACY"):
            runner.dispatch(self.db,self.artifacts,spy,attempt,coordination_context=self.envelope)
        self.assertEqual(len(spy.script),1)
        with self.assertRaisesRegex(ledger.LedgerError,"E_COORD_CONTEXT"):
            ledger.transition(self.db,attempt,"DISPATCHING")

    def test_generic_dispatch_transition_cannot_replace_atomic_approval_start(self):
        self._register()
        (attempt, _digest), _ = self._prepare("A", "task-A", context=self.envelope)
        runner.approve(self.db, attempt, "fixture-approval")
        before = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_DISPATCH_START"):
            ledger.transition(self.db, attempt, "DISPATCHING",
                              coordination_context={"context": self.envelope,
                                                    "artifacts_dir": self.artifacts})
        self.assertEqual(self.db.execute("SELECT state FROM attempts WHERE id=?", (attempt,)).fetchone()[0],
                         "AWAITING_APPROVAL")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM approvals").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], before)
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"], "VERIFIED")

    def test_spent_dispatch_cannot_be_cancelled_or_retried_as_definite_nondelivery(self):
        self._register()
        (attempt, digest), _ = self._prepare("A", "task-A", context=self.envelope)
        runner.approve(self.db, attempt, "fixture-approval")
        approval = ledger.issue_approval(self.db, attempt, digest, "fixture", "fixture-1",
                                         "test-only-transport", "coordination", 100, {"max_spend": 0})
        ledger.start_approved_dispatch(self.db, approval, attempt, digest,
                                       {"context": self.envelope, "artifacts_dir": self.artifacts})
        for target in ("CANCELLED", "RETRYABLE_ERROR"):
            with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_DELIVERY_UNKNOWN"):
                ledger.transition(self.db, attempt, target)
            self.assertEqual(self.db.execute("SELECT state FROM attempts WHERE id=?", (attempt,)).fetchone()[0],
                             "DISPATCHING")
        ledger.reconcile_uncertain_attempt(self.db, attempt)
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_DELIVERY_UNKNOWN"):
            ledger.begin_attempt(self.db, "A")
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"], "VERIFIED")

    def test_spent_awaiting_approval_cannot_cancel_uncertainty(self):
        self._register()
        (attempt, digest), _ = self._prepare("A", "task-A", context=self.envelope)
        runner.approve(self.db, attempt, "fixture-approval")
        approval = ledger.issue_approval(self.db, attempt, digest, "fixture", "fixture-1",
                                         "test-only-transport", "coordination", 100, {"max_spend": 0})
        ledger.consume_approval(self.db, approval, attempt, digest)
        with self.assertRaisesRegex(ledger.LedgerError, "E_COORD_DELIVERY_UNKNOWN"):
            ledger.transition(self.db, attempt, "CANCELLED")
        ledger.reconcile_on_open(self.db)
        self.assertEqual(self.db.execute("SELECT state FROM attempts WHERE id=?", (attempt,)).fetchone()[0],
                         "DELIVERY_UNKNOWN")
        self.assertFalse(coordination.evaluate(self.db, "A", self.artifacts, self.envelope, "prepare")["ok"])

    def test_self_partial_foreign_and_missing_prerequisite_context_refuse(self):
        for snapshot in (graph(["A"],[{"from":"A","to":"A","kind":"hard"}]),
                         dict(graph(["A"],[]),page_complete=False)):
            with self.assertRaises(ledger.LedgerError):
                coordination.validate_snapshot(snapshot)
        self._register()
        self._accept_a()
        self.assertFalse(coordination.evaluate(self.db,"B",self.artifacts,self.contexts["B"],"prepare")["ok"])

    def test_partial_task_results_and_changed_source_cannot_satisfy_prerequisite(self):
        self._register()
        self._accept_a()
        changed = dict(self.contexts["A"],source_digest="f"*64)
        current = coordination.context_envelope(dict(self.contexts,A=changed))
        self.assertFalse(coordination.evaluate(self.db,"B",self.artifacts,current,"prepare")["ok"])

    def test_revocation_after_dispatch_blocks_acceptance_and_changed_fence_blocks_dispatch(self):
        self._register()
        self._accept_a()
        (attempt,digest),manifest = self._prepare("B","task-B",context=self.envelope)
        runner.approve(self.db,attempt,"fixture-human")
        approval = ledger.issue_approval(self.db,attempt,digest,"fixture","fixture-1","test-only-transport","coordination",100,{"max_spend":0})
        record = results.make_result(b"alpha",manifest,"U000001","task-B",attempt,"resolved")
        adapter = SpyAdapter({"U000001":record})
        moved = coordination.context_envelope(dict(self.contexts,B=dict(self.contexts["B"],fence="reassigned")))
        with self.assertRaises(ledger.LedgerError):
            runner.dispatch_via_adapter(self.db,self.artifacts,adapter,attempt,approval,coordination_context=moved)
        self.assertEqual(adapter.calls,0)
        self.assertEqual(self.db.execute("SELECT consumed FROM approvals WHERE id=?",(approval,)).fetchone()[0],0)
        runner.dispatch_via_adapter(self.db,self.artifacts,adapter,attempt,approval,coordination_context=self.envelope)
        ledger.revoke(self.db,"A","late revocation")
        with self.assertRaises(ledger.LedgerError):
            runner.accept(self.db,self.artifacts,attempt,"task-B",manifest,b"alpha",
                {"provider":"fixture","model":"fixture-1","endpoint":"test-only-transport","purpose":"coordination","max_output_tokens":100},coordination_context=self.envelope)
        self.assertIsNone(ledger.accepted_attempt(self.db,"B"))

    def test_serialized_same_task_claim_and_full_ready_blocked_query(self):
        self._register()
        claim = ledger.begin_attempt(self.db,"A")
        with self.assertRaisesRegex(ledger.LedgerError,"E_COORD_ACTIVE_ATTEMPT"):
            ledger.begin_attempt(self.db,"A")
        ledger.transition(self.db,claim,"CANCELLED")
        out = coordination.ready_blocked(self.db,self.artifacts,self.envelope)
        self.assertEqual(out["ready"],["A"])
        self.assertIn("B",out["blocked"])

    def test_missing_or_corrupt_graph_cas_blocks_prepare_dispatch_and_accept(self):
        self._register()
        graph_path = Path(self.artifacts)/coordination.snapshot_digest(self.snapshot)
        graph_bytes = graph_path.read_bytes()
        for changed in (None,b"corrupt graph"):
            if changed is None:
                graph_path.unlink()
            else:
                graph_path.write_bytes(changed)
            self.assertFalse(coordination.evaluate(self.db,"A",self.artifacts,self.envelope,"prepare")["ok"])
            with self.assertRaises(ledger.LedgerError):
                self._prepare("A","task-A",context=self.envelope)
            self.assertEqual(self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],0)
            graph_path.write_bytes(graph_bytes)
        (attempt,digest),manifest = self._prepare("A","task-A",context=self.envelope)
        runner.approve(self.db,attempt,"fixture-human")
        approval = ledger.issue_approval(self.db,attempt,digest,"fixture","fixture-1","test-only-transport","coordination",100,{"max_spend":0})
        rich = results.make_result(b"alpha",manifest,"U000001","task-A",attempt,"resolved")
        adapter = SpyAdapter({"U000001":rich})
        graph_path.unlink()
        with self.assertRaises(ledger.LedgerError):
            runner.dispatch_via_adapter(self.db,self.artifacts,adapter,attempt,approval,coordination_context=self.envelope)
        self.assertEqual(adapter.calls,0)
        self.assertEqual(self.db.execute("SELECT consumed FROM approvals WHERE id=?",(approval,)).fetchone()[0],0)
        graph_path.write_bytes(graph_bytes)
        runner.dispatch_via_adapter(self.db,self.artifacts,adapter,attempt,approval,coordination_context=self.envelope)
        graph_path.write_bytes(b"corrupt graph")
        with self.assertRaises(ledger.LedgerError):
            runner.accept(self.db,self.artifacts,attempt,"task-A",manifest,b"alpha",
                {"provider":"fixture","model":"fixture-1","endpoint":"test-only-transport","purpose":"coordination","max_output_tokens":100},coordination_context=self.envelope)
        self.assertIsNone(ledger.accepted_attempt(self.db,"A"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
