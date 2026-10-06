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
        self.assertTrue(result["capture_complete"])
        if result["containment_method"] == "windows-job-kill-on-close":
            self.assertTrue(result["tree_contained"])
        else:
            self.assertFalse(result["tree_contained"])
            self.assertIn("unverified", result["containment_note"])


def _process_dead(pid):
    import os as _os
    if _os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE,
                                                ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return True
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value != 259
        finally:
            kernel32.CloseHandle(handle)
    try:
        _os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return True
    return False


class CleanExitDescendantTests(unittest.TestCase):
    def test_clean_exit_descendant_accounted(self):
        script = ("import subprocess,sys; p=subprocess.Popen([sys.executable,'-c',"
                  "'import time;time.sleep(30)'],stdin=subprocess.DEVNULL,"
                  "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                  "print(p.pid,flush=True)")
        capture = obs._capture_process(
            [sys.executable, "-B", "-c", script], cwd=str(Path.cwd()),
            env=dict(__import__("os").environ), timeout=30)
        for key in ("exit_code", "capture_complete", "kill_path_used",
                    "tree_contained", "containment_method", "containment_note"):
            self.assertIn(key, capture)
        self.assertEqual(capture["exit_code"], 0)
        self.assertFalse(capture["kill_path_used"])
        pid = int(capture["stdout"].strip().split()[-1])
        if capture["containment_method"] == "windows-job-kill-on-close":
            # Job close on return must have terminated the descendant long
            # before its 30s natural expiry: poll briefly, then require death.
            deadline = time.time() + 10
            while time.time() < deadline and not _process_dead(pid):
                time.sleep(0.2)
            self.assertTrue(_process_dead(pid),
                            "descendant outlived the closed job")
            self.assertTrue(capture["tree_contained"])
        else:
            # No proven cleanup on this path: the receipt must say so.
            self.assertFalse(capture["tree_contained"])
            self.assertIn("unverified", capture["containment_note"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
