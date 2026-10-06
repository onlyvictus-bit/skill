"""Actual CM central history/CAS integration for TEST_ONLY branch policies."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT.parent/"claude-mon/scripts"))
from hybrid_bridge import branch,native
from complete_read_v2 import artifacts,ledger


class CentralMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = ledger.connect(self.root/"ledger.sqlite")
        self.addCleanup(lambda:self.db.close())
        self.cas = self.root/"artifacts"
        self.journal = native.CMCoordinationJournal(self.db,ledger)

    def origin(self,name,head,tasks,edges=()):
        return branch.freeze_origin({"database":"fixture:db","branch":name,"head":head,
            "tasks":tasks,"edges":list(edges),"evidence":{},"evidence_class":"TEST_ONLY"},artifacts,self.cas)

    def test_durable_operation_identity_must_be_a_nonempty_string(self):
        for operation_id in (""," ",None,0):
            with self.assertRaises(native.NativeContractError):
                self.journal.append("NATIVE_MERGE_INTENT",operation_id,{"evidence_class":"TEST_ONLY"})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],0)

    def test_both_origins_are_retained_in_real_chain_and_no_acceptance_is_imported(self):
        base = self.origin("main","h0",{"A":"open","B":"open"})
        source = self.origin("feature","h1",{"A":"closed","B":"open"})
        target = self.origin("main","h2",{"A":"open","B":"closed"})
        out = branch.apply_central_fixture_merge(base,source,target,"h0","h1","h2",self.journal,artifacts,self.cas,"merge-1")
        self.assertEqual(out["merged_tasks"],{"A":"closed","B":"closed"})
        self.assertTrue(out["fresh_evidence_required"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM accepted").fetchone()[0],0)
        events = self.db.execute("SELECT detail FROM events WHERE kind='NATIVE_MERGE_OUTCOME'").fetchall()
        payload = json.loads(events[0]["detail"])
        for ref in ("source_cas_digest","target_cas_digest","base_cas_digest"):
            self.assertTrue(json.loads(artifacts.open_verified(self.cas,payload[ref])))
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"],"VERIFIED")
        count = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        again = branch.apply_central_fixture_merge(base,source,target,"h0","h1","h2",self.journal,artifacts,self.cas,"merge-1")
        self.assertEqual(again["status"],"IDEMPOTENT_TEST_ONLY_MERGED")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],count)

    def test_reopen_unknown_operation_reconciles_without_reissuing_and_rebinding_refuses(self):
        adapter = native.FixtureBeadsAdapter({"branch":"main","head":"h0"})
        adapter.interrupt_next("claim-1")
        out = native.coordinate_fixture_operation(self.journal,adapter,"claim-1",{"kind":"claim"})
        self.assertEqual(out["status"],"UNKNOWN")
        self.db.close()
        self.db = ledger.connect(self.root/"ledger.sqlite")
        journal = native.CMCoordinationJournal(self.db,ledger)
        with self.assertRaises(native.NativeContractError):
            native.coordinate_fixture_operation(journal,adapter,"claim-1",{"kind":"close"})
        self.assertEqual(native.coordinate_fixture_operation(journal,adapter,"claim-1",{"kind":"claim"})["status"],"UNKNOWN")
        self.assertEqual(native.reconcile_fixture_operation(journal,adapter,"claim-1")["status"],"RECONCILED_APPLIED")
        self.assertEqual(adapter.write_count,1)
        self.assertEqual(ledger.verify_history(self.db)["internal_chain"],"VERIFIED")

    def test_conflict_and_missing_cas_leave_dirty_origin_and_ledger_unchanged(self):
        base = self.origin("main","h0",{"A":"open"})
        source = self.origin("feature","h1",{"A":"closed"})
        target = self.origin("main","h2",{"A":"reopened"})
        source_before,target_before = dict(source),dict(target)
        with self.assertRaises(branch.MergeRefused):
            branch.apply_central_fixture_merge(base,source,target,"h0","h1","h2",self.journal,artifacts,self.cas,"conflict")
        self.assertEqual(source,source_before)
        self.assertEqual(target,target_before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],0)
        compatible_target=self.origin("main","h2",{"A":"open"})
        (self.cas/base["cas_digest"]).unlink()
        with self.assertRaises(artifacts.ArtifactError):
            branch.apply_central_fixture_merge(base,source,compatible_target,"h0","h1","h2",self.journal,artifacts,self.cas,"missing-cas")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],0)

    def test_retained_merge_reopens_all_origins_and_reconciles_interrupted_intent(self):
        base=self.origin("main","h0",{"A":"open","B":"open"})
        source=self.origin("feature","h1",{"A":"closed","B":"open"})
        target=self.origin("main","h2",{"A":"open","B":"closed"})
        original=self.journal.append
        def interrupted(kind,*args,**kwargs):
            if kind=="NATIVE_MERGE_OUTCOME": raise RuntimeError("fixture interruption")
            return original(kind,*args,**kwargs)
        self.journal.append=interrupted
        with self.assertRaises(RuntimeError):
            branch.apply_central_fixture_merge(base,source,target,"h0","h1","h2",self.journal,artifacts,self.cas,"merge-interrupted")
        self.journal.append=original
        self.db.close()
        self.db=ledger.connect(self.root/"ledger.sqlite")
        self.journal=native.CMCoordinationJournal(self.db,ledger)
        out=branch.reconcile_central_fixture_merge(self.journal,artifacts,self.cas,"merge-interrupted")
        self.assertEqual(out["status"],"TEST_ONLY_RECONCILED_MERGE")
        payload=self.journal.last("merge-interrupted")["payload"]
        self.assertTrue(branch.verify_retained_merge(payload,artifacts,self.cas))
        for key in ("base_cas_digest","source_cas_digest","target_cas_digest","merged_result_digest"):
            path=self.cas/payload[key]
            before=path.read_bytes()
            path.unlink()
            with self.assertRaises(artifacts.ArtifactError):
                branch.verify_retained_merge(payload,artifacts,self.cas)
            path.write_bytes(b"corrupt retained artifact")
            with self.assertRaises(artifacts.ArtifactError):
                branch.verify_retained_merge(payload,artifacts,self.cas)
            path.write_bytes(before)
        self.assertEqual(ledger.verify_history(self.db)["projection_replay"],"VERIFIED")
