#!/usr/bin/env python3
"""M4-R Order 7: memory-integrity CLI through real subprocesses."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
CLI = str(STAGE / "scripts" / "memory_integrity_v2.py")
ENGINE = str(STAGE.parents[0] / "claude-mon")
LAYERS = {"scope": "READY", "extraction": "READY", "coverage": "READY",
          "execution": "READY", "results": "READY", "semantic": "READY",
          "persistence": "READY"}


def run_cli(*argv):
    proc = subprocess.run([sys.executable, CLI] + [str(a) for a in argv], text=True,
                          capture_output=True, timeout=120)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        return proc.returncode, {"_out": proc.stdout[-300:], "_err": proc.stderr[-300:]}


class MiCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="micli-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_audit_ready_and_stale(self):
        src = self.root / "src"
        src.mkdir()
        (src / "a.txt").write_bytes(b"hello\n")
        man_dir = self.root / "mans"
        man_dir.mkdir()
        sys.path.insert(0, str(Path(ENGINE) / "scripts"))
        try:
            from complete_read_v2 import inventory, partition
            man = partition.build_manifest("SRC-1", b"hello\n")
        finally:
            sys.path.remove(str(Path(ENGINE) / "scripts"))
        (man_dir / "a.txt.json").write_text(json.dumps(man))
        scope = inventory.freeze_scope(src, ["a.txt"])
        scope_file = self.root / "scope.json"
        scope_file.write_text(json.dumps(scope))
        code, out = run_cli("audit", "--claude-mon-root", ENGINE, "--scope-file", str(scope_file),
                            "--source-dir", str(src), "--manifest-dir", str(man_dir))
        self.assertEqual(code, 0, out)
        self.assertEqual(out["verdict"], "READY")
        (src / "a.txt").write_bytes(b"changed\n")
        code, out = run_cli("audit", "--claude-mon-root", ENGINE, "--scope-file", str(scope_file),
                            "--source-dir", str(src), "--manifest-dir", str(man_dir))
        self.assertNotEqual(code, 0)
        self.assertIn(out["verdict"], ("STALE", "BLOCKED"))

    def test_report_compose_and_reject(self):
        layers = self.root / "layers.json"
        layers.write_text(json.dumps(LAYERS))
        # R1 (F17): formatter-only composition warns and stays honest about
        # exit status; the authoritative gate needs --evidence-file.
        code, out = run_cli("report", "--layers-file", str(layers))
        self.assertEqual(code, 1, out)
        self.assertEqual(out["overall"], "READY_FOR_DECLARED_TASK")
        self.assertIn("warning", out)
        ev = self.root / "evidence.json"
        ev.write_text(json.dumps({n: ["d%d" % i] for i, n in enumerate(LAYERS)}))
        code, out = run_cli("report", "--layers-file", str(layers),
                            "--evidence-file", str(ev))
        self.assertEqual(code, 1, out)
        self.assertNotIn("warning", out)
        bad = self.root / "bad.json"
        bad.write_text(json.dumps(dict(LAYERS, coverage="BLOCKED")))
        code, out = run_cli("report", "--layers-file", str(bad))
        self.assertEqual(code, 1, out)
        self.assertEqual(out["overall"], "BLOCKED")

    def test_watchdog_testonly_roundtrip(self):
        code, out = run_cli("watchdog", "--canary", "cli-canary-1")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["evidence_class"], "TEST_ONLY")
        self.assertEqual(out["boundary"], "BOUNDARY_UNVERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
