#!/usr/bin/env python3
"""M3/M6 graph and branch-policy behavior through real in-process data."""
import sys
import tempfile
import subprocess
import hashlib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hybrid_bridge import branch, graph  # noqa: E402


def snapshot(branch_name, head, task_state=None, edges=None, evidence=None):
    return {
        "database": "fixture:db", "branch": branch_name, "head": head,
        "tasks": task_state if task_state is not None else {"A": "open", "B": "open"},
        "edges": edges if edges is not None else [{"from": "A", "to": "B", "relation": "hard"}],
        "evidence": evidence if evidence is not None else {"A": "basis-a", "B": "basis-b"},
        "cas_digest": hashlib.sha256(branch_name.encode()).hexdigest(), "evidence_class": "TEST_ONLY",
    }


class GraphPolicyTests(unittest.TestCase):
    def test_completeness_must_be_explicit_true_and_fixture_class_explicit(self):
        raw = {"workspace":"ws","revision":"r1","tasks":["A"],"edges":[]}
        for additions in ({},{"complete_read":1},{"complete_read":"false"},
                          {"complete_read":False},{"complete_read":True},
                          {"complete_read":True,"evidence_class":"NATIVE_VERIFIED"}):
            with self.assertRaises(graph.GraphContractError):
                graph.freeze_snapshot(dict(raw,**additions))
    def test_hard_prerequisite_must_have_current_core_evidence_not_native_closed_state(self):
        frozen = graph.freeze_snapshot({
            "workspace": "ws", "revision": "r1", "tasks": ["A", "B"],
            "edges": [{"from": "A", "to": "B", "relation": "hard"}],
            "complete_read":True,"evidence_class":"TEST_ONLY",
        })
        blocked = graph.eligibility(frozen, "B", {"A": {"eligible": False, "native_state": "closed"}})
        self.assertFalse(blocked["eligible"])
        self.assertEqual(blocked["blockers"], ["A"])
        ready = graph.eligibility(frozen, "B", {"A": {"eligible": True, "native_state": "open"}})
        self.assertTrue(ready["eligible"])

    def test_cycle_missing_and_unsupported_relation_refuse_snapshot(self):
        for bad in (
            {"workspace": "ws", "revision": "r", "tasks": ["A"], "edges": [{"from": "A", "to": "A", "relation": "hard"}]},
            {"workspace": "ws", "revision": "r", "tasks": ["A"], "edges": [{"from": "A", "to": "MISSING", "relation": "hard"}]},
            {"workspace": "ws", "revision": "r", "tasks": ["A", "B"], "edges": [{"from": "A", "to": "B", "relation": "mystery"}]},
        ):
            with self.assertRaises(graph.GraphContractError):
                graph.freeze_snapshot(bad)


class BranchPolicyTests(unittest.TestCase):
    def test_changed_dirty_bytes_change_observed_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git","init",tmp],check=True,capture_output=True)
            path = Path(tmp)/"dirty.txt"
            path.write_text("before",encoding="utf-8")
            before = branch.observe_git_workspace(tmp)
            path.write_text("after",encoding="utf-8")
            after = branch.observe_git_workspace(tmp)
            self.assertEqual(before["workspace"],str(Path(tmp)))
            self.assertEqual(after["workspace"],str(Path(tmp)))
            self.assertNotEqual(before["dirty_source_digest"],after["dirty_source_digest"])

    def test_modified_preview_missing_label_unknown_ancestry_cycle_refuse(self):
        base,source,target = snapshot("main","h0"),snapshot("feature","h1"),snapshot("main","h2")
        preview = branch.preview_merge(base,source,target,"h0")
        preview["merged_tasks"]["A"] = "closed"
        with self.assertRaises(branch.MergeRefused):
            branch.apply_fixture_preview(preview,"h1","h2")
        del source["evidence_class"]
        with self.assertRaises(branch.MergeRefused):
            branch.preview_merge(base,source,target,"h0")
        with self.assertRaises(branch.MergeRefused):
            branch.preview_merge(base,snapshot("feature","h1"),target,None)
        cycle_source = snapshot("feature","h1",edges=[{"from":"A","to":"B","relation":"hard"},{"from":"B","to":"A","relation":"hard"}])
        cycle = branch.preview_merge(base,cycle_source,target,"h0")
        self.assertFalse(cycle["mergeable"])
    def test_compatible_three_way_preview_preserves_both_origins_and_requires_fresh_evidence(self):
        base = snapshot("main", "h0")
        source = snapshot("feature/a", "h1", {"A": "closed", "B": "open"})
        target = snapshot("main", "h2", {"A": "open", "B": "closed"})
        preview = branch.preview_merge(base, source, target, common_ancestor="h0")
        self.assertTrue(preview["mergeable"], preview)
        self.assertEqual(preview["base_origin"]["head"],"h0")
        self.assertEqual([r["id"] for r in preview["changed_tasks"]["source"]],["A"])
        self.assertEqual([r["id"] for r in preview["changed_tasks"]["target"]],["B"])
        self.assertEqual(preview["changed_edges"],{"source":[],"target":[]})
        self.assertTrue(preview["evidence_applicability"]["fresh_evidence_required"])
        self.assertFalse(preview["evidence_applicability"]["accepted_evidence_imported"])
        result = branch.apply_fixture_preview(preview, current_source_head="h1", current_target_head="h2")
        self.assertEqual(result["status"], "TEST_ONLY_MERGED")
        self.assertFalse(result["approval_reused"])
        self.assertTrue(result["fresh_evidence_required"])
        self.assertEqual(result["event_payload"]["source_origin"]["head"], "h1")
        self.assertEqual(result["event_payload"]["target_origin"]["head"], "h2")

    def test_competing_edge_change_and_moved_head_refuse_without_mutating_target(self):
        base = snapshot("main", "h0")
        source = snapshot("feature/a", "h1", edges=[{"from": "A", "to": "B", "relation": "informational"}])
        target = snapshot("main", "h2", edges=[])
        preview = branch.preview_merge(base, source, target, common_ancestor="h0")
        self.assertFalse(preview["mergeable"])
        self.assertTrue(preview["conflicts"])

        clean = branch.preview_merge(base, snapshot("feature/a", "h1", {"A": "closed", "B": "open"}),
                                     snapshot("main", "h2", {"A": "open", "B": "closed"}), common_ancestor="h0")
        with self.assertRaises(branch.MergeRefused):
            branch.apply_fixture_preview(clean, current_source_head="h9", current_target_head="h2")

    def test_non_git_is_an_explicit_boundary(self):
        observed = branch.observe_git_workspace(Path(self.id()).parent / "not-a-repository")
        self.assertEqual(observed["kind"], "NON_GIT")
        self.assertFalse(observed["git_observed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
