#!/usr/bin/env python3
"""M8: named hosts route to v2 explicitly; anything else fails closed."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / "scripts"))

from complete_read_v2 import contracts  # noqa: E402

CLI = str(STAGE / "scripts" / "claude_mon_v2.py")


def run_cli(*argv):
    proc = subprocess.run([sys.executable, CLI] + [str(a) for a in argv], text=True,
                          capture_output=True, timeout=120)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        return proc.returncode, {"_out": proc.stdout[-300:]}


class HostRoutingTests(unittest.TestCase):
    def test_explicit_entrypoint_reports_v2(self):
        code, out = run_cli("capabilities")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["engine"], "claude-mon")
        self.assertEqual(out["schema_digest"], contracts.schema_digest())

    def test_unknown_command_is_usage_error(self):
        code, _out = run_cli("frobnicate")
        self.assertEqual(code, 2)

    def test_capabilities_file_matches_runtime(self):
        declared = json.loads((STAGE / "capabilities-v2.json").read_text(encoding="utf-8"))
        code, out = run_cli("capabilities")
        self.assertEqual(code, 0)
        self.assertEqual(declared["schema_version"], out["schema_version"])
        for command in declared["commands"]:
            self.assertIn(command, out["commands"])
        self.assertFalse(declared["live_dispatch"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
