"""M7 disposable native pilot helper contracts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hybrid_bridge import native
from hybrid_bridge import native_pilot


class PilotHelpers(unittest.TestCase):
    def test_init_is_git_free_and_environment_is_explicit(self):
        env = native_pilot.build_env(
            Path("/tmp/work/.beads"),
            {"BEADS_DB":"foreign","BD_JSON_ENVELOPE":"1","DOLT_DB":"foreign","KEEP":"yes"})
        self.assertEqual(env["BEADS_DIR"], str(Path("/tmp/work/.beads")))
        self.assertEqual(env["BD_JSON_ENVELOPE"], "0")
        self.assertEqual(env["BD_DISABLE_METRICS"], "1")
        self.assertEqual(env["KEEP"], "yes")
        self.assertNotIn("BEADS_DB", env)
        self.assertNotIn("DOLT_DB", env)
        argv = native_pilot.init_argv("bd")
        self.assertIn("init", argv)
        self.assertIn("--quiet", argv)
        self.assertIn("--stealth", argv)
        self.assertNotIn("--readonly", argv)

    def test_issue_parser_requires_exactly_one_issue_identity(self):
        self.assertEqual(native_pilot.issue_id('{"id":"mip-a"}'), "mip-a")
        self.assertEqual(native_pilot.issue_id('[{"id":"mip-a"}]'), "mip-a")
        for raw in ("{}", "[]", '[{"id":"a"},{"id":"b"}]', '{"id":1}', "not-json"):
            with self.subTest(raw=raw):
                with self.assertRaises(native.NativeContractError):
                    native_pilot.issue_id(raw)


class PilotAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mi-pilot-test-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        exe = root / "bd.exe"
        exe.write_bytes(b"pilot-binary")
        beads = root / "workspace" / ".beads"
        (beads / "embeddeddolt" / "mip" / ".dolt").mkdir(parents=True)
        (beads / "metadata.json").write_text(json.dumps({
            "database":"dolt","backend":"dolt","dolt_mode":"embedded",
            "dolt_database":"mip","project_id":"pilot-project"}), encoding="utf-8")
        self.selection = native.NativeSelection(
            str(exe), str(root / "workspace"), "1.3.1",
            hashlib.sha256(exe.read_bytes()).hexdigest(),
            expected_project_id="pilot-project",
            expected_database_name="mip", expected_prefix="mip")
        self.calls = []
        self.state = {"id":"mip-a","status":"open","assignee":None}

        def run(argv, cwd, env):
            self.calls.append(list(argv))
            if "update" in argv:
                self.state = {"id":"mip-a","status":"in_progress",
                              "assignee":"memory-integrity-pilot"}
                return {"exit_code":0,"stdout":b'{"id":"mip-a"}',"stderr":b"",
                        "capture_complete":True,"timed_out":False,
                        "output_limit_exceeded":False,"capture_errors":[],
                        "process_id":1,"kill_path_used":False,
                        "tree_contained":False,"containment_method":"test",
                        "containment_note":"test"}
            if "show" in argv:
                return {"exit_code":0,"stdout":json.dumps([self.state]).encode(),
                        "stderr":b"","capture_complete":True,"timed_out":False,
                        "output_limit_exceeded":False,"capture_errors":[],
                        "process_id":2,"kill_path_used":False,
                        "tree_contained":False,"containment_method":"test",
                        "containment_note":"test"}
            raise AssertionError(argv)

        self.adapter = native_pilot.PilotNativeAdapter(
            self.selection, "qual-1", ["a"*64], runner=run)

    def test_claim_executes_once_and_readback_proves_actor_and_state(self):
        evidence = self.adapter.execute("op-1", {
            "kind":"claim","native_task_id":"mip-a",
            "actor":"memory-integrity-pilot"})
        self.assertEqual(evidence["exit_code"], 0)
        observed = self.adapter.readback({
            "kind":"claim","native_task_id":"mip-a",
            "actor":"memory-integrity-pilot"})
        self.assertTrue(observed["applied"])
        self.assertEqual(observed["native_task_id"], "mip-a")
        self.assertIn("update", self.calls[0])
        self.assertIn("--claim", self.calls[0])
        self.assertIn("show", self.calls[1])
        self.assertIn("--readonly", self.calls[1])

    def test_adapter_is_explicitly_disposable_pilot_scoped(self):
        self.assertTrue(self.adapter.native_write_qualified)
        self.assertEqual(self.adapter.evidence_class, "NATIVE_VERIFIED")
        self.assertEqual(self.adapter.qualification_scope, "DISPOSABLE_PILOT")
        self.assertEqual(len(self.adapter.selection_digest), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
