#!/usr/bin/env python3
"""M7: a fresh process reopens runs from disk; changed sources invalidate."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
sys.path.insert(0, SCRIPTS)

from integrity_v2 import recall  # noqa: E402

REOPEN = ("import json,sys; sys.path.insert(0, %r);"
          "from integrity_v2 import recall;"
          "out = recall.load_run_map(%r, {over});"
          "print(json.dumps(out))")


class FreshSessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fresh-")
        self.root = Path(self.temp.name)
        self.run_map = {"run_dir": str(self.root), "source_digests": {"a.txt": "d1"},
                        "artifact_digests": {"r1": "d2"}, "generation": "g1"}
        recall.save_run_map(str(self.root / "run-map.json"), self.run_map)

    def tearDown(self):
        self.temp.cleanup()

    def reopen(self, current):
        code = REOPEN % (SCRIPTS, str(self.root / "run-map.json"))
        code = code.replace("{over}", json.dumps(current))
        proc = subprocess.run([sys.executable, "-c", code], text=True,
                              capture_output=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        return json.loads(proc.stdout)

    def test_fresh_process_reopens_current(self):
        out = self.reopen({"a.txt": "d1"})
        # R2: v2 maps have no artifact/path binding and are historical
        # only; a fresh authoritative read needs the v3 layout.
        self.assertFalse(out["current"])
        self.assertTrue(out["historical_unverified"])
        self.assertEqual(out["stale_sources"], [])
        self.assertEqual(out["run_map"]["generation"], "g1")

    def test_changed_source_invalidates(self):
        out = self.reopen({"a.txt": "d2"})
        self.assertFalse(out["current"])
        self.assertEqual(out["stale_sources"], ["a.txt"])

    def test_missing_map_is_an_error(self):
        with self.assertRaises(recall.RecallError):
            recall.load_run_map(str(self.root / "nope.json"), {})

    def test_run_map_requires_fields(self):
        with self.assertRaises(recall.RecallError):
            recall.save_run_map(str(self.root / "bad.json"), {"run_dir": "x"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
