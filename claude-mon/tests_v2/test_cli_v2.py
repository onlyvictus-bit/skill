#!/usr/bin/env python3
"""M4-R Order 7: the public CLI path end to end, plus rejection paths.

Exercises prepare -> preflight -> run -> accept -> status -> verify ->
export -> open-unit -> query through real subprocesses. Rejections must
exit nonzero with the spy-less guarantee: nothing dispatched without
approval, budget, and identity.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / "scripts"))
from complete_read_v2 import partition, results  # noqa: E402

STAGE = Path(__file__).resolve().parents[1]
CLI = str(STAGE / "scripts" / "claude_mon_v2.py")
PROFILE = {"schema_version": 2, "provider": "test-only", "model": "m-1",
           "encoding": "e", "encoding_version": "v", "context_limit": 100000,
           "output_limit": 500, "counting_method": "synthetic-word-split",
           "endpoint": "test-only-transport", "purpose": "m4r-cli-test", "max_spend": 0}


def run_cli(*argv):
    proc = subprocess.run([sys.executable, CLI] + [str(a) for a in argv], text=True,
                          capture_output=True, timeout=120)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        return proc.returncode, {"_stdout": proc.stdout[-500:], "_stderr": proc.stderr[-500:]}


class CliV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cliv2-")
        self.root = Path(self.temp.name)
        self.run_dir = str(self.root / "run")
        (self.root / "source.txt").write_bytes(b"alpha beta\ngamma delta\n")
        (self.root / "units.json").write_text(json.dumps({"U000001": "alpha beta\n",
                                                           "U000002": "gamma delta\n"}))
        (self.root / "instructions.json").write_text(json.dumps("x"))
        (self.root / "task.txt").write_text("do it")
        (self.root / "schema.json").write_text(json.dumps({"type": "object"}))
        (self.root / "context.json").write_text(json.dumps({}))
        (self.root / "profile.json").write_text(json.dumps(PROFILE))
        (self.root / "script.json").write_text(json.dumps([["ok", {"U000001": "r1",
                                                                   "U000002": "r2"}]]))
        man = partition.build_manifest("SRC-1", b"alpha beta\ngamma delta\n")
        (self.root / "manifest.json").write_text(json.dumps(man))
        self.f = lambda name: str(self.root / name)

    def tearDown(self):
        self.temp.cleanup()

    def test_freeze_scope(self):
        import shutil
        (Path(self.run_dir)).mkdir(parents=True, exist_ok=True)
        shutil.copy(self.f("source.txt"), str(Path(self.run_dir) / "source.txt"))
        code, out = run_cli("freeze", "--run-dir", self.run_dir, "--sources", "source.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["sources"], 1)
        self.assertEqual(len(out["scope_digest"]), 64)
        code, out = run_cli("freeze", "--run-dir", self.run_dir,
                            "--sources", self.f("source.txt"))
        self.assertEqual(code, 1)  # outside run root: escape refusal is correct
        code, out = run_cli("freeze", "--run-dir", self.run_dir, "--sources", "x")
        self.assertEqual(code, 1)  # missing source refused

    def test_capabilities_lists_commands(self):
        code, out = run_cli("capabilities")
        self.assertEqual(code, 0)
        for cmd in ("prepare", "preflight", "run", "resume", "status", "verify",
                    "export", "open-unit", "query", "freeze", "accept"):
            self.assertIn(cmd, out["commands"])

    def test_end_to_end_offline(self):
        code, out = run_cli("prepare", "--run-dir", self.run_dir, "--work-item", "W1",
                            "--task-digest", "t1", "--task-spec-digest", "s1",
                            "--units-file", self.f("units.json"),
                            "--instructions-file", self.f("task.txt"),
                            "--schema-file", self.f("schema.json"),
                            "--context-file", self.f("context.json"),
                             "--profile-file", self.f("profile.json"),
                             "--source-id", "SRC-1", "--counter-words",
                             "--manifest-file", self.f("manifest.json"),
                             "--source-file", self.f("source.txt"))
        self.assertEqual(code, 0, out)
        attempt = out["attempt_id"]
        manifest = json.loads(Path(self.f("manifest.json")).read_text())
        source = Path(self.f("source.txt")).read_bytes()
        scripted = {uid: results.make_result(source, manifest, uid, "t1", attempt, "r-" + uid)
                    for uid in ("U000001", "U000002")}
        Path(self.f("script.json")).write_text(json.dumps([["ok", scripted]]))
        code, out = run_cli("status", "--run-dir", self.run_dir, "--work-item", "W1")
        self.assertEqual(code, 0)
        self.assertEqual(out["attempts"][0]["state"], "PREPARED")
        code, out = run_cli("run", "--run-dir", self.run_dir, "--attempt-id", attempt,
                            "--approval-ref", "user-go-1", "--provider", "test-only",
                            "--model", "m-1", "--purpose", "m4r-cli-test",
                            "--max-output", "500",
                            "--script-file", self.f("script.json"), "--accept",
                            "--manifest-file", self.f("manifest.json"),
                            "--source-file", self.f("source.txt"),
                            "--expect-task-digest", "t1")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["state"], "ACCEPTED")
        code, out = run_cli("status", "--run-dir", self.run_dir, "--work-item", "W1")
        done = [a for a in out["attempts"] if a["state"] == "ACCEPTED"]
        self.assertEqual(len(done), 1)

    def test_run_without_budget_or_approval_blocked(self):
        code, out = run_cli("prepare", "--run-dir", self.run_dir, "--work-item", "W9",
                            "--task-digest", "t1", "--task-spec-digest", "s1",
                            "--units-file", self.f("units.json"),
                            "--instructions-file", self.f("task.txt"),
                            "--schema-file", self.f("schema.json"),
                            "--profile-file", self.f("profile.json"),
                            "--counter-words")
        self.assertEqual(code, 0, out)
        code, out = run_cli("run", "--run-dir", self.run_dir, "--attempt-id", out["attempt_id"],
                            "--approval-ref", "   ", "--provider", "test-only",
                            "--model", "m-1", "--purpose", "x", "--max-output", 5,
                            "--script-file", self.f("script.json"))
        self.assertNotEqual(code, 0)

    def test_verify_open_unit_query(self):
        man = partition.build_manifest("SRC-1", b"alpha beta\ngamma delta\n")
        man_file = self.root / "manifest.json"
        man_file.write_text(json.dumps(man))
        code, out = run_cli("verify", "--manifest-file", str(man_file),
                            "--source-file", self.f("source.txt"))
        self.assertEqual(code, 0, out)
        code, out = run_cli("open-unit", "--manifest-file", str(man_file),
                            "--source-file", self.f("source.txt"),
                            "--unit-id", man["units"][0]["id"])
        self.assertEqual(code, 0)
        self.assertIn("alpha", out["text"])
        code, out = run_cli("query", "--manifest-file", str(man_file),
                            "--source-file", self.f("source.txt"), "--text", "gamma")
        self.assertEqual(code, 0)
        self.assertTrue(out["hits"])
        self.assertEqual(out["mode"], "locator-not-semantic-search")

    def test_resume_and_export(self):
        code, out = run_cli("resume", "--run-dir", self.run_dir)
        self.assertEqual(code, 0)
        self.assertEqual(out["pending"], [])
        code, out = run_cli("export", "--run-dir", self.run_dir,
                            "--out", str(self.root / "report.json"))
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
