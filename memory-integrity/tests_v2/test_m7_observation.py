"""Native observation contracts; supplied subprocess replies are TEST_ONLY.

These checks exercise refusal and normalization, never native qualification.
Actual pinned-binary observation is a separate public command receipt.
"""
import copy
import base64
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
from hybrid_bridge import native


class NativeObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mi-m7-observe-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.exe = self.base / "bd.exe"
        self.exe.write_bytes(b"TEST_ONLY executable identity; never executed")
        self.pilot = self.base / "pilot"
        beads = self.pilot / ".beads"
        (beads / "embeddeddolt" / "mip" / ".dolt").mkdir(parents=True)
        self.metadata = {"database":"dolt", "backend":"dolt", "dolt_mode":"embedded",
                         "dolt_database":"mip", "project_id":"pilot-project"}
        (beads / "metadata.json").write_text(json.dumps(self.metadata), encoding="utf-8")
        self.selection = native.NativeSelection(str(self.exe), str(self.pilot), "1.3.1",
            hashlib.sha256(self.exe.read_bytes()).hexdigest(), expected_project_id="pilot-project",
            expected_database_name="mip", expected_prefix="mip")
        self.a = {"_type":"issue", "id":"mip-a", "status":"open", "dependency_count":0}
        self.b = {"_type":"issue", "id":"mip-b", "status":"in_progress", "assignee":"pilot",
            "lease_expires_at":"2000-01-01T00:00:00Z", "dependency_count":1,
            "dependencies":[{"issue_id":"mip-b", "depends_on_id":"mip-a", "type":"blocks"}]}
        self.export = "\n".join(json.dumps(x) for x in (self.a, self.b)) + "\n"
        self.info = {"database_path":str(beads / "embeddeddolt"), "mode":"direct",
                     "issue_count":2, "schema_version":1, "config":{"issue_prefix":"mip"}}
        self.head = {"branch":"main", "commit":"h1", "schema_version":1}
        self.version = {"version":"1.3.1", "commit":"c1c4b642ac1c08d8c828007a1c2f96e47e43ef7c",
                        "schema_version":1}

    def replies(self, changes=None):
        replies = [self.version, self.info, self.head, self.export, self.export, self.head, self.info]
        changes = changes or {}
        result = []
        for i, reply in enumerate(replies):
            reply = changes.get(i, reply)
            if isinstance(reply, Exception):
                result.append(reply)
            elif isinstance(reply, subprocess.CompletedProcess):
                result.append(reply)
            else:
                raw = reply if isinstance(reply, str) else json.dumps(reply)
                result.append(subprocess.CompletedProcess([], 0, raw.encode(), b""))
        for i, reply in enumerate(result):
            if isinstance(reply,subprocess.CompletedProcess):
                result[i] = {"exit_code":reply.returncode,"stdout":reply.stdout,"stderr":reply.stderr,
                             "capture_complete":True,"timed_out":False,"output_limit_exceeded":False,
                             "capture_errors":[],"process_id":0}
        return result

    def observe(self, changes=None):
        with mock.patch("hybrid_bridge.native_observation._capture_process", side_effect=self.replies(changes)) as calls:
            out = native.NativeBeadsAdapter(self.selection).observe()
        return out, calls

    def test_complete_observation_preserves_native_dependencies_but_cannot_activate(self):
        out, calls = self.observe()
        self.assertTrue(out["ok"], out)
        self.assertFalse(out["native_beads_qualified"])
        self.assertFalse(out["active"])
        self.assertEqual(out["snapshot"]["edges"], [{"from":"mip-a","to":"mip-b","relation":"hard"}])
        self.assertEqual(out["snapshot"]["claims"]["mip-b"]["effective"], False)
        self.assertEqual(out["snapshot"]["claims"]["mip-b"]["reason"], "EXPIRED")
        self.assertEqual(out["evidence_class"], "NATIVE_OBSERVED_UNQUALIFIED")
        for call in calls.call_args_list:
            argv = call.args[0]
            self.assertIn("--readonly", argv)
            self.assertFalse(call.kwargs["shell"])
            self.assertEqual(call.kwargs["env"]["BEADS_DIR"], str(self.pilot / ".beads"))
            self.assertEqual(call.kwargs["env"]["BD_JSON_ENVELOPE"], "0")
        self.assertEqual(calls.call_count, 7)

    def test_gate_warning_stops_before_export_and_retains_raw_diagnostics(self):
        reply = subprocess.CompletedProcess([], 0, json.dumps(self.info).encode(),
            b"warning: workspace gate unavailable, continuing ungated: Access is denied.\n")
        out, calls = self.observe({1:reply})
        self.assertFalse(out["ok"])
        self.assertIn("E_NATIVE_DIAGNOSTIC", out["blockers"][0])
        self.assertIn("Access is denied", out["observations"][-1]["stderr"])
        self.assertEqual(calls.call_count, 2)

    def test_exact_migration_note_allowed_but_unknown_warning_refused(self):
        from hybrid_bridge import native_observation as observation
        allowed = subprocess.CompletedProcess([], 0, json.dumps(self.info).encode(),
            (observation.JSON_MIGRATION_NOTE + "\n").encode())
        self.assertTrue(self.observe({1:allowed})[0]["ok"])
        denied = subprocess.CompletedProcess([], 0, json.dumps(self.info).encode(), b"warning: new warning\n")
        self.assertFalse(self.observe({1:denied})[0]["ok"])

    def test_hash_and_metadata_drift_refuse_before_subprocess(self):
        self.exe.write_bytes(b"changed executable")
        out, calls = self.observe()
        self.assertFalse(out["ok"])
        self.assertIn("E_NATIVE_EXE_HASH", out["blockers"][0])
        calls.assert_not_called()

    def test_executable_change_between_commands_refuses_before_second_launch(self):
        replies = iter(self.replies())
        def first(*args,**kwargs):
            self.exe.write_bytes(b"replaced after version was captured")
            return next(replies)
        with mock.patch("hybrid_bridge.native_observation._capture_process",side_effect=first) as calls:
            out = native.NativeBeadsAdapter(self.selection).observe()
        self.assertFalse(out["ok"])
        self.assertIn("E_NATIVE_EXE_HASH",out["blockers"][0])
        self.assertEqual(calls.call_count,1)
        self.assertEqual(len(out["observations"]),1)

    def test_metadata_replacement_after_export_preserves_prior_observations_and_refuses(self):
        replies = iter(self.replies())
        calls_seen = 0
        def changed(*args,**kwargs):
            nonlocal calls_seen
            calls_seen += 1
            if calls_seen==4:
                path = self.pilot / ".beads/metadata.json"
                path.write_text(json.dumps(self.metadata,indent=2),encoding="utf-8")
            return next(replies)
        with mock.patch("hybrid_bridge.native_observation._capture_process",side_effect=changed):
            out = native.NativeBeadsAdapter(self.selection).observe()
        self.assertFalse(out["ok"])
        self.assertIn("E_NATIVE_METADATA_CHANGED",out["blockers"][0])
        self.assertEqual(len(out["observations"]),7)

    def test_hostile_inherited_routing_does_not_select_another_database(self):
        hostile = {"BEADS_DIR":"foreign","BEADS_DB":"foreign","BD_JSON_ENVELOPE":"1",
                   "BD_OTHER":"foreign","DOLT_DB":"foreign"}
        with mock.patch.dict(os.environ,hostile):
            out,calls = self.observe()
        self.assertTrue(out["ok"],out)
        for call in calls.call_args_list:
            env = call.kwargs["env"]
            self.assertEqual(env["BEADS_DIR"],str(self.pilot / ".beads"))
            self.assertEqual(env["BD_JSON_ENVELOPE"],"0")
            self.assertNotIn("BEADS_DB",env)
            self.assertNotIn("BD_OTHER",env)
            self.assertNotIn("DOLT_DB",env)

    def test_foreign_database_and_invalid_count_refuse(self):
        for field, value in (("database_path",str(self.base / "foreign")),("issue_count",True)):
            with self.subTest(field=field):
                bad = dict(self.info, **{field:value})
                out, _ = self.observe({1:bad})
                self.assertFalse(out["ok"], out)

    def test_partial_duplicate_and_error_exports_refuse(self):
        for raw in (json.dumps(self.a)+"\n", json.dumps(self.a)+"\n"+json.dumps(self.a)+"\n",
                    self.export[:-4], '{"error":"read failed"}\n'):
            with self.subTest(raw=raw):
                out, _ = self.observe({3:raw,4:raw})
                self.assertFalse(out["ok"], out)

    def test_dependency_omission_unknown_semantics_and_missing_target_refuse(self):
        for change in (None, "parent-child", "foreign-a"):
            b = copy.deepcopy(self.b)
            if change is None:
                del b["dependencies"]
            elif change == "parent-child":
                b["dependencies"][0]["type"] = change
            else:
                b["dependencies"][0]["depends_on_id"] = change
            raw = json.dumps(self.a)+"\n"+json.dumps(b)+"\n"
            out, _ = self.observe({3:raw,4:raw})
            self.assertFalse(out["ok"], out)

    def test_cycles_and_same_head_working_changes_refuse(self):
        a = dict(self.a,dependency_count=1,
            dependencies=[{"issue_id":"mip-a","depends_on_id":"mip-b","type":"blocks"}])
        raw = json.dumps(a)+"\n"+json.dumps(self.b)+"\n"
        self.assertFalse(self.observe({3:raw,4:raw})[0]["ok"])
        b = dict(self.b,status="closed")
        changed = json.dumps(self.a)+"\n"+json.dumps(b)+"\n"
        self.assertFalse(self.observe({4:changed})[0]["ok"])
        self.assertFalse(self.observe({5:dict(self.head,commit="h2")})[0]["ok"])

    def test_foreign_prefix_with_matching_count_refuses_complete_graph(self):
        for relation in (None,"blocks","related"):
            with self.subTest(relation=relation):
                foreign = dict(self.a,id="foreign-a")
                local = copy.deepcopy(self.b)
                if relation is None:
                    local["dependencies"] = []
                    local["dependency_count"] = 0
                else:
                    local["dependencies"][0].update(depends_on_id="foreign-a",type=relation)
                raw = json.dumps(foreign)+"\n"+json.dumps(local)+"\n"
                out, _ = self.observe({3:raw,4:raw})
                self.assertFalse(out["ok"],out)
                self.assertIn("E_NATIVE_FOREIGN_PREFIX",out["blockers"][0])
                self.assertNotIn("snapshot",out)

    def test_invalid_utf8_keeps_exact_captured_pipe_bytes(self):
        for name in ("stdout","stderr"):
            with self.subTest(name=name):
                raw = b"bad\xffdiagnostic"
                reply = subprocess.CompletedProcess([],0,json.dumps(self.info).encode(),b"")
                setattr(reply,name,raw)
                out, _ = self.observe({1:reply})
                self.assertFalse(out["ok"])
                record = out["observations"][-1]
                self.assertEqual(base64.b64decode(record[name+"_base64"]),raw)
                self.assertEqual(record[name+"_sha256"],hashlib.sha256(raw).hexdigest())
                self.assertEqual(record[name+"_captured_bytes"],len(raw))

    def test_timeout_retains_partial_capture_and_never_calls_success(self):
        timeout = subprocess.TimeoutExpired(["bd"], 15, output=b'{"partial":', stderr=b"waiting")
        out, calls = self.observe({1:timeout})
        self.assertFalse(out["ok"])
        self.assertTrue(out["observations"][-1]["timed_out"])
        self.assertFalse(out["observations"][-1]["capture_complete"])
        self.assertEqual(calls.call_count, 2)

    def test_native_read_never_enables_write_or_claim_acceptance(self):
        adapter = native.NativeBeadsAdapter(self.selection)
        with mock.patch("hybrid_bridge.native_observation._capture_process",side_effect=self.replies()):
            self.assertTrue(adapter.observe()["ok"])
        with mock.patch("hybrid_bridge.native_observation._capture_process") as calls:
            with self.assertRaises(native.NativeQualificationError):
                adapter.execute("op-claim",{"kind":"claim","id":"mip-b"})
            calls.assert_not_called()

    def test_public_command_retains_blocked_receipt_without_overwriting(self):
        selection_file = self.base / "selection.json"
        from dataclasses import asdict
        selection_file.write_text(json.dumps(asdict(self.selection)),encoding="utf-8")
        self.exe.write_bytes(b"changed; command must refuse before running this file")
        receipt = self.base / "receipt.json"
        cmd = [sys.executable,"-B",str(ROOT / "scripts/memory_integrity_workflow.py"),
               "native-observe","--claude-mon-root",str(ROOT.parent / "claude-mon"),
               "--selection-file",str(selection_file),"--receipt",str(receipt)]
        first = subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(first.returncode,2,first.stderr)
        out = json.loads(first.stdout)
        self.assertIn("E_NATIVE_EXE_HASH",out["blockers"][0])
        saved = receipt.read_bytes()
        self.assertEqual(json.loads(saved),out)
        second = subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",timeout=30)
        self.assertEqual(second.returncode,2,second.stderr)
        self.assertIn("E_NATIVE_RECEIPT_EXISTS",json.loads(second.stdout)["blockers"][0])
        self.assertEqual(receipt.read_bytes(),saved)


class RealPipeCaptureTests(unittest.TestCase):
    """Real child/pipe controls using Python, without executing Beads writes."""

    def test_both_pipes_complete_and_exit_captured(self):
        from hybrid_bridge.native_observation import _capture_process
        result = _capture_process([sys.executable,"-B","-c",
            "import sys; print('output'); print('warning',file=sys.stderr); sys.exit(3)"],
            cwd=ROOT,env=os.environ.copy(),timeout=5)
        self.assertEqual(result["exit_code"],3)
        self.assertTrue(result["capture_complete"])
        self.assertIn(b"output",result["stdout"])
        self.assertIn(b"warning",result["stderr"])

    def test_running_output_limit_kills_exact_child_and_keeps_bounded_capture(self):
        from hybrid_bridge import native_observation as observation
        with mock.patch.object(observation,"MAX_OUTPUT_BYTES",1024):
            result = observation._capture_process([sys.executable,"-B","-c",
                "import sys; sys.stdout.buffer.write(b'x'*1000000); sys.stdout.flush()"],
                cwd=ROOT,env=os.environ.copy(),timeout=5)
        self.assertTrue(result["output_limit_exceeded"])
        self.assertEqual(len(result["stdout"]),1024)
        self.assertFalse(result["capture_complete"])
        self.assertIsNotNone(result["exit_code"])

    def test_timeout_kills_child_and_marks_uncertain_observation(self):
        from hybrid_bridge.native_observation import _capture_process
        result = _capture_process([sys.executable,"-B","-c","import time; time.sleep(10)"],
            cwd=ROOT,env=os.environ.copy(),timeout=0.2)
        self.assertTrue(result["timed_out"])
        self.assertIsNotNone(result["exit_code"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
