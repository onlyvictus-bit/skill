#!/usr/bin/env python3
"""Native process-tree containment (audit P0-4): a grandchild that holds the
captured pipe open and ignores SIGTERM must still die on timeout, pipes must
reach EOF, and the result must record proven tree containment. Stdlib only."""
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hybrid_bridge import native_observation as obs  # noqa: E402

PARENT = (
    "import subprocess,signal,sys,time;"
    "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
    "subprocess.Popen([sys.executable,'-c',"
    "'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
    "time.sleep(120)']);"
    "time.sleep(120)"
)


class ContainmentTests(unittest.TestCase):
    def test_grandchild_pipe_holder_killed(self):
        result = obs._capture_process(
            [sys.executable, "-c", PARENT], cwd=str(Path.cwd()),
            env=dict(__import__("os").environ), timeout=5)
        self.assertTrue(result["timed_out"])
        self.assertTrue(result["kill_path_used"])
        self.assertTrue(result["tree_contained"], result.get("containment_note"))
        self.assertTrue(result["capture_complete"], result.get("capture_errors"))

    def test_clean_command_unaffected(self):
        result = obs._capture_process(
            [sys.executable, "-c", "print('ok')"], cwd=str(Path.cwd()),
            env=dict(__import__("os").environ), timeout=30)
        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(result["kill_path_used"])
        self.assertTrue(result["tree_contained"])
        self.assertTrue(result["capture_complete"])


    def test_clean_exit_descendant_accounted(self):
        import json as _json
        script = ("import subprocess,sys; p=subprocess.Popen([sys.executable,'-c',"
                  "'import time;time.sleep(6)'],stdin=subprocess.DEVNULL,"
                  "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                  "print(p.pid,flush=True)")
        capture = obs._capture_process(
            [sys.executable, "-B", "-c", script], cwd=str(Path.cwd()),
            env=dict(__import__("os").environ), timeout=2)
        for key in ("exit_code", "capture_complete", "kill_path_used",
                    "tree_contained", "containment_method", "containment_note"):
            self.assertIn(key, capture)
        self.assertFalse(capture["kill_path_used"])
        self.assertEqual(capture["containment_method"], "windows-job-kill-on-close")
        time.sleep(6.2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
