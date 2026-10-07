"""M7 disposable native pilot helper contracts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parent / "claude-mon" / "scripts"))
from complete_read_v2 import ledger
from hybrid_bridge import native
from hybrid_bridge import native_pilot
import m7_native_pilot as pilot_cli


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


class DisposablePilotWorkflow(unittest.TestCase):
    def test_end_to_end_interruption_recovery_issues_claim_once(self):
        tmp = tempfile.TemporaryDirectory(prefix="mi-native-pilot-flow-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        exe = root / "bd.exe"
        exe.write_bytes(b"pilot-binary")
        workspace = root / "pilot"
        receipt = root / "pilot-receipt.json"
        state = {"issue": None}
        calls = []

        def result(stdout=b"", stderr=b""):
            return {
                "exit_code": 0, "stdout": stdout, "stderr": stderr,
                "capture_complete": True, "timed_out": False,
                "output_limit_exceeded": False, "capture_errors": [],
                "process_id": len(calls) + 1, "kill_path_used": False,
                "tree_contained": False, "containment_method": "test",
                "containment_note": "test",
            }

        def runner(argv, cwd, env):
            calls.append(list(argv))
            if "version" in argv:
                return result(json.dumps({
                    "version": "1.3.1",
                    "commit": "c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c",
                    "schema_version": 1,
                }).encode())
            if "init" in argv:
                beads = workspace / ".beads"
                try:
                    local_to_cwd = beads.resolve().is_relative_to(Path(cwd).resolve())
                except AttributeError:
                    local_to_cwd = str(beads.resolve()).startswith(str(Path(cwd).resolve()) + os.sep)
                if local_to_cwd:
                    return result(
                        b'{"ok":true}',
                        b"Warning: failed to update git exclude: not a git repository\n")
                (beads / "embeddeddolt" / "mip" / ".dolt").mkdir(parents=True)
                (beads / "metadata.json").write_text(json.dumps({
                    "database": "dolt", "backend": "dolt", "dolt_mode": "embedded",
                    "dolt_database": "mip", "project_id": "pilot-project",
                }), encoding="utf-8")
                return result(b'{"ok":true}')
            if "info" in argv:
                return result(json.dumps({
                    "database_path": str(workspace / ".beads" / "embeddeddolt"),
                    "mode": "direct", "issue_count": 0 if state["issue"] is None else 1,
                    "schema_version": 1, "config": {"issue_prefix": "mip"},
                }).encode())
            if "create" in argv:
                state["issue"] = {"id": "mip-a", "status": "open", "assignee": None}
                return result(b'{"id":"mip-a"}')
            if "update" in argv and "--claim" in argv:
                state["issue"] = {
                    "id": "mip-a", "status": "in_progress",
                    "assignee": native_pilot.ACTOR,
                }
                return result(b'{"id":"mip-a"}')
            if "show" in argv:
                return result(json.dumps([state["issue"]]).encode())
            raise AssertionError(argv)

        observed = {
            "ok": True,
            "evidence_class": "NATIVE_OBSERVED_UNQUALIFIED",
            "snapshot": {
                "snapshot_digest": "6" * 64,
                "head": "h1",
                "branch": "main",
            },
        }
        out = native_pilot.run_disposable_pilot(
            bd_path=exe,
            expected_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
            workspace=workspace,
            receipt=receipt,
            ledger_module=ledger,
            runner=runner,
            observer=lambda selection: observed,
        )
        self.assertTrue(out["ok"], out)
        self.assertEqual(out["overall"], "M7_DISPOSABLE_PILOT_VERIFIED")
        self.assertTrue(out["pilot_native_write_observed"])
        self.assertFalse(out["native_beads_qualified"])
        self.assertEqual(out["interrupted"]["status"], "UNKNOWN")
        self.assertEqual(out["recovered"]["status"], "RECONCILED_NATIVE_APPLIED")
        self.assertEqual(out["recovered_again"]["status"], "IDEMPOTENT_RECONCILED")
        claims = [argv for argv in calls if "update" in argv and "--claim" in argv]
        self.assertEqual(len(claims), 1)
        self.assertIn("version", calls[0])
        self.assertTrue(Path(out["launcher_cwd"]).is_dir())
        self.assertNotEqual(Path(out["launcher_cwd"]), workspace)
        self.assertFalse((workspace / ".beads").resolve().is_relative_to(
            Path(out["launcher_cwd"]).resolve()))
        self.assertLess(
            next(i for i, argv in enumerate(calls) if "version" in argv),
            next(i for i, argv in enumerate(calls) if "init" in argv))
        self.assertTrue(receipt.is_file())
        self.assertEqual(json.loads(receipt.read_text(encoding="utf-8")), out)
        self.assertEqual(out["journal_events"],
                         ["NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"])
        self.assertEqual(out["history_internal_chain"], "VERIFIED")

    def test_wrong_version_refuses_before_init_or_create(self):
        tmp = tempfile.TemporaryDirectory(prefix="mi-native-pilot-version-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        exe = root / "bd.exe"
        exe.write_bytes(b"pilot-binary")
        calls = []

        def runner(argv, cwd, env):
            calls.append(list(argv))
            return {
                "exit_code": 0,
                "stdout": json.dumps({
                    "version": "9.9.9", "commit": "wrong", "schema_version": 1
                }).encode(),
                "stderr": b"", "capture_complete": True, "timed_out": False,
                "output_limit_exceeded": False, "capture_errors": [],
                "process_id": 1, "kill_path_used": False,
                "tree_contained": False, "containment_method": "test",
                "containment_note": "test",
            }

        with self.assertRaisesRegex(native.NativeQualificationError, "E_PILOT_VERSION"):
            native_pilot.run_disposable_pilot(
                bd_path=exe,
                expected_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                workspace=root / "pilot",
                receipt=root / "receipt.json",
                ledger_module=ledger,
                runner=runner,
                observer=lambda selection: {},
            )
        self.assertEqual(len(calls), 1)
        self.assertIn("version", calls[0])
        self.assertFalse(any("init" in argv or "create" in argv for argv in calls))

    def test_existing_workspace_or_receipt_refuses_before_running_bd(self):
        tmp = tempfile.TemporaryDirectory(prefix="mi-native-pilot-refuse-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        exe = root / "bd.exe"
        exe.write_bytes(b"x")
        workspace = root / "pilot"
        workspace.mkdir()
        called = []
        with self.assertRaisesRegex(native.NativeContractError, "E_PILOT_WORKSPACE_EXISTS"):
            native_pilot.run_disposable_pilot(
                bd_path=exe,
                expected_executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                workspace=workspace,
                receipt=root / "receipt.json",
                ledger_module=ledger,
                runner=lambda *a, **k: called.append(a),
                observer=lambda selection: {},
            )
        self.assertEqual(called, [])


class PilotCliTests(unittest.TestCase):
    def test_cli_routes_explicit_paths_and_prints_receipt_summary(self):
        tmp = tempfile.TemporaryDirectory(prefix="mi-pilot-cli-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        bd = root / "bd.exe"
        bd.write_bytes(b"x")
        workspace = root / "workspace"
        receipt = root / "receipt.json"
        cm = ROOT.parent / "claude-mon"
        expected = hashlib.sha256(bd.read_bytes()).hexdigest()
        captured = {}

        def run_func(**kwargs):
            captured.update(kwargs)
            return {"ok": True, "overall": "M7_DISPOSABLE_PILOT_VERIFIED"}

        with mock.patch.object(pilot_cli, "_ledger_module", return_value=ledger):
            code = pilot_cli.main([
                "--bd", str(bd),
                "--expected-executable-sha256", expected,
                "--workspace", str(workspace),
                "--receipt", str(receipt),
                "--claude-mon-root", str(cm),
            ], run_func=run_func)
        self.assertEqual(code, 0)
        self.assertEqual(Path(captured["bd_path"]), bd)
        self.assertEqual(Path(captured["workspace"]), workspace)
        self.assertEqual(Path(captured["receipt"]), receipt)
        self.assertIs(captured["ledger_module"], ledger)

    def test_cli_failure_is_exit_two_not_false_success(self):
        with mock.patch.object(pilot_cli, "_ledger_module", side_effect=ValueError("bad companion")):
            code = pilot_cli.main([
                "--bd", "missing",
                "--expected-executable-sha256", "0" * 64,
                "--workspace", "w",
                "--receipt", "r",
                "--claude-mon-root", "cm",
            ])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
