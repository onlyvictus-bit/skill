"""Fresh-process coordinated workflow controls using real SQLite/CAS policy.

Provider results are supplied fixtures, not live AI proof. No native install.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CM = ROOT.parent / "claude-mon"
ENTRY = ROOT / "scripts/memory_integrity_workflow.py"


class PublicCoordination(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mi-r3-public-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.run = self.base / "workspace"
        rows = []
        for ident, prereq in (("A", []), ("B", ["A"]), ("C", ["B"])):
            source = self.base / (ident + ".txt")
            source.write_text(ident + " has one requirement\n", encoding="utf-8")
            review = self.base / (ident + "-reviews.json")
            review.write_text(json.dumps({"U000001": {"interpretation": ident+" requirement inspected",
                "findings": [], "disposition": "resolved", "reviewer": "offline-fixture", "unresolved": []}}), encoding="utf-8")
            rows.append({"id": ident, "source": str(source), "task": "Inspect " + ident,
                         "responses_file": str(review), "requires": prereq})
        self.plan = self.base / "plan.json"
        self.plan.write_text(json.dumps({"schema_version": 1, "workspace_id": "example-workspace",
            "run_id": "approved-run-1", "requirement_digest": hashlib.sha256(b"approved requirements").hexdigest(),
            "tasks": rows}), encoding="utf-8")

    def call(self, command, *args):
        proc = subprocess.run([sys.executable, "-B", str(ENTRY), command,
                "--claude-mon-root", str(CM), "--workspace-dir", str(self.run), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8", timeout=50,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8"))
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc.returncode, json.loads(proc.stdout)

    def initialize(self):
        code, out = self.call("coordinate-init", "--plan-file", self.plan)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["ready"], ["A"])
        return out

    def run_task(self, ident):
        code, out = self.call("coordinate-run", "--task-id", ident)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["evidence_class"], "TEST_ONLY")
        return out

    def test_graph_blocks_before_approval_and_execution_then_allows_in_order(self):
        self.initialize()
        before = (self.run / "ledger.sqlite").read_bytes()
        code, blocked = self.call("coordinate-run", "--task-id", "B")
        self.assertNotEqual(code, 0, blocked)
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["adapter_calls"], 0)
        self.assertEqual(blocked["approvals_consumed"], 0)
        self.assertEqual((self.run / "ledger.sqlite").read_bytes(), before)
        self.run_task("A")
        code, status = self.call("coordinate-ready")
        self.assertEqual(code, 0, status)
        self.assertEqual(status["ready"], ["B"])
        self.run_task("B")
        self.run_task("C")
        code, out = self.call("coordinate-verify", "--query", "every")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["overall"], "VERIFIED_COORDINATED_OFFLINE")
        self.assertEqual(len(out["recall"]["records"]), 3)
        self.assertFalse(out["native_beads_qualified"])
        self.assertEqual(out["history"]["anchored_completeness"], "UNVERIFIED")

    def test_revoked_prerequisite_keeps_history_but_blocks_report_recall_and_resume(self):
        self.initialize()
        for ident in ("A", "B", "C"):
            self.run_task(ident)
        code, out = self.call("coordinate-revoke", "--task-id", "A", "--reason", "source review withdrawn")
        self.assertEqual(code, 0, out)
        code, stale = self.call("coordinate-verify", "--query", "every")
        self.assertNotEqual(code, 0, stale)
        self.assertFalse(stale["ok"])
        self.assertEqual(stale["historical_accepted"], ["B", "C"])
        self.assertNotIn("recall", stale)
        before = (self.run / "ledger.sqlite").read_bytes()
        code, resumed = self.call("coordinate-run", "--task-id", "B")
        self.assertNotEqual(code, 0, resumed)
        self.assertEqual(resumed["adapter_calls"], 0)
        self.assertEqual((self.run / "ledger.sqlite").read_bytes(), before)

    def test_changed_upstream_source_and_graph_refuse_current_completion(self):
        self.initialize()
        self.run_task("A")
        self.run_task("B")
        (self.base / "A.txt").write_text("source changed\n", encoding="utf-8")
        code, blocked = self.call("coordinate-run", "--task-id", "C")
        self.assertNotEqual(code, 0, blocked)
        self.assertEqual(blocked["adapter_calls"], 0)
        code, out = self.call("coordinate-verify")
        self.assertNotEqual(code, 0, out)
        self.assertFalse(out["ok"])

    def test_native_close_without_evidence_and_foreign_task_do_not_unlock(self):
        self.initialize()
        db = sqlite3.connect(self.run / "ledger.sqlite")
        try:
            db.execute("UPDATE work_items SET status='ACCEPTED' WHERE id LIKE '%::A'")
            db.commit()
        finally:
            db.close()
        code, blocked = self.call("coordinate-run", "--task-id", "B")
        self.assertNotEqual(code, 0, blocked)
        self.assertEqual(blocked["adapter_calls"], 0)
        code, foreign = self.call("coordinate-run", "--task-id", "invented")
        self.assertNotEqual(code, 0, foreign)
        self.assertEqual(foreign["adapter_calls"], 0)

    def test_no_duplicate_on_current_resume_and_r2_skill_prefix_preserved(self):
        self.initialize()
        self.run_task("A")
        before = (self.run / "ledger.sqlite").read_bytes()
        out = self.run_task("A")
        self.assertTrue(out["resumed"])
        self.assertEqual(out["adapter_calls"], 0)
        self.assertEqual((self.run / "ledger.sqlite").read_bytes(), before)
        for root in (ROOT, CM):
            baseline = json.loads((root / "tests_v2/baseline-r2.json").read_text(encoding="utf-8"))
            old = next(row for row in baseline["files"] if row["path"] == "SKILL.md")
            self.assertEqual(hashlib.sha256((root / "SKILL.md").read_bytes()[:old["bytes"]]).hexdigest(), old["sha256"])

    def test_checkpoint_and_merge_public_routing_do_not_import_completion(self):
        self.initialize()
        self.run_task("A")
        seal = self.base/"verifier-owned-checkpoint.json"
        code,out = self.call("history-seal","--owner","independent-verifier","--seal-path",seal)
        self.assertEqual(code,0,out)
        code,out = self.call("coordinate-ready","--checkpoint-file",seal)
        self.assertEqual(code,0,out)
        self.assertEqual(out["history"]["anchored_completeness"],"VERIFIED")
        tasks = {"A":"open","B":"open","C":"open"}
        def origin(name,head,task_state):
            return {"database":"fixture:example-workspace","branch":name,"head":head,
                    "tasks":task_state,"edges":[],"evidence":{},"evidence_class":"TEST_ONLY"}
        fixture = self.base/"branches.json"
        fixture.write_text(json.dumps({"base":origin("main","h0",tasks),
            "source":origin("feature","h1",dict(tasks,A="closed")),
            "target":origin("main","h2",dict(tasks,B="closed")),"common_ancestor":"h0"}),encoding="utf-8")
        code,out = self.call("branch-merge-fixture","--fixture-file",fixture,"--operation-id","merge-1")
        self.assertEqual(code,0,out)
        self.assertTrue(out["fresh_evidence_required"])
        code,out = self.call("coordinate-run","--task-id","B")
        self.assertNotEqual(code,0,out)
        self.assertEqual(out["adapter_calls"],0)

    def test_sources_are_reobserved_after_preparation_and_after_dispatch(self):
        sys.path.insert(0,str(ROOT/"scripts"))
        import coordination_workflow as workflow
        workflow._engines(CM)
        from complete_read_v2 import runner
        original_source = (self.base/"A.txt").read_bytes()
        for boundary in ("prepare","dispatch_via_adapter"):
            with self.subTest(boundary=boundary):
                (self.base/"A.txt").write_bytes(original_source)
                args = SimpleNamespace(claude_mon_root=str(CM),
                    workspace_dir=str(self.base/("boundary-"+boundary)),
                    plan_file=str(self.plan),task_id="A",checkpoint_file=None)
                workflow.initialize(args)
                original = getattr(runner,boundary)
                def changed_source(*call_args,**kwargs):
                    out = original(*call_args,**kwargs)
                    (self.base/"A.txt").write_text("Changed during execution",encoding="utf-8")
                    return out
                with mock.patch.object(runner,boundary,side_effect=changed_source):
                    out = workflow.run_task(args)
                self.assertFalse(out["ok"],out)
                self.assertEqual(out["adapter_calls"],0 if boundary=="prepare" else 1)
                self.assertEqual(out["approvals_consumed"],0 if boundary=="prepare" else 1)
                db=sqlite3.connect(Path(args.workspace_dir)/"ledger.sqlite")
                try:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM accepted").fetchone()[0],0)
                finally:
                    db.close()

    def test_recall_reobserves_sources_after_report_view(self):
        sys.path.insert(0,str(ROOT/"scripts"))
        import coordination_workflow as workflow
        args=SimpleNamespace(claude_mon_root=str(CM),workspace_dir=str(self.run),
            plan_file=str(self.plan),task_id="A",checkpoint_file=None,query="every")
        workflow.initialize(args)
        for ident in ("A","B","C"):
            args.task_id=ident
            self.assertTrue(workflow.run_task(args)["ok"])
        original=workflow._view
        def changed_after_view(*call_args,**kwargs):
            out=original(*call_args,**kwargs)
            (self.base/"A.txt").write_text("Changed before recall",encoding="utf-8")
            return out
        with mock.patch.object(workflow,"_view",side_effect=changed_after_view):
            with self.assertRaises(ValueError):
                workflow.verify(args)
        code,out=self.call("coordinate-verify","--query","every")
        self.assertNotEqual(code,0,out)
        self.assertNotIn("recall",out)

    def test_public_resume_uses_same_attempt_and_never_resends_saved_or_unknown_delivery(self):
        sys.path.insert(0,str(ROOT/"scripts"))
        import coordination_workflow as workflow
        workflow._engines(CM)
        from complete_read_v2 import ledger,runner
        for boundary in ("prepare","approve","response_saved","validated","dispatching"):
            with self.subTest(boundary=boundary):
                self.run=self.base/("resume-"+boundary)
                args=SimpleNamespace(claude_mon_root=str(CM),workspace_dir=str(self.run),
                    plan_file=str(self.plan),task_id="A",checkpoint_file=None)
                workflow.initialize(args)
                if boundary in ("prepare","approve","validated"):
                    method="dispatch_via_adapter" if boundary=="validated" else boundary
                    original=getattr(runner,method)
                    def interrupted(*call_args,**kwargs):
                        original(*call_args,**kwargs)
                        raise RuntimeError("fixture process interruption after "+boundary)
                    patch=mock.patch.object(runner,method,side_effect=interrupted)
                else:
                    original=ledger.transition
                    def interrupted(db,attempt,state,*call_args,**kwargs):
                        if state==("VALIDATED" if boundary=="response_saved" else "RESPONSE_SAVED"):
                            raise RuntimeError("fixture process interruption before "+state)
                        return original(db,attempt,state,*call_args,**kwargs)
                    patch=mock.patch.object(ledger,"transition",side_effect=interrupted)
                with patch:
                    self.assertFalse(workflow.run_task(args)["ok"])
                db=sqlite3.connect(self.run/"ledger.sqlite")
                before=db.execute("SELECT id FROM attempts").fetchone()[0]
                db.close()
                code,out=self.call("coordinate-resume","--task-id","A")
                if boundary=="dispatching":
                    self.assertNotEqual(code,0,out)
                    self.assertEqual(out["adapter_calls"],0)
                    self.assertEqual(out["approvals_consumed"],0)
                else:
                    self.assertEqual(code,0,out)
                    self.assertTrue(out["resumed"])
                    self.assertEqual(out["adapter_calls"],1 if boundary in ("prepare","approve") else 0)
                db=sqlite3.connect(self.run/"ledger.sqlite")
                try:
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],1)
                    self.assertEqual(db.execute("SELECT id FROM attempts").fetchone()[0],before)
                    if boundary=="dispatching":
                        self.assertEqual(db.execute("SELECT state FROM attempts").fetchone()[0],"DELIVERY_UNKNOWN")
                finally:
                    db.close()


if __name__ == "__main__":
    unittest.main()
