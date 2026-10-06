#!/usr/bin/env python3
"""M8: Fable guard runs first; either side can block; verdicts agree."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE / "scripts"))
sys.path.insert(0, str(STAGE.parents[0] / "memory-integrity" / "scripts"))

from fable_bridge_v2 import check, compose_overall  # noqa: E402
from integrity_v2 import report  # noqa: E402

LAYERS = ("scope", "extraction", "coverage", "execution", "results",
          "semantic", "persistence")


def ready_layers(**over):
    base = {name: "READY" for name in LAYERS}
    base.update(over)
    return base


def fake_guard(exit_code, root):
    path = Path(root) / ("guard-%d.py" % exit_code)
    path.write_text("import sys; print('fake guard'); sys.exit(%d)\n" % (exit_code,),
                    encoding="utf-8")
    return str(path)


class ComposedGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="composed-")

    def tearDown(self):
        self.temp.cleanup()

    def test_guard_failure_blocks_despite_ready_layers(self):
        overall, detail = check(self.temp.name, ready_layers(),
                                fable_guard=fake_guard(1, self.temp.name))
        self.assertEqual(overall, "BLOCKED")
        self.assertEqual(detail["fable_guard"], "failed")

    def test_guard_pass_plus_ready_is_ready(self):
        overall, _detail = check(self.temp.name, ready_layers(),
                                 fable_guard=fake_guard(0, self.temp.name))
        self.assertEqual(overall, "READY_FOR_DECLARED_TASK")

    def test_blocked_layer_blocks_despite_guard(self):
        overall, _detail = check(self.temp.name, ready_layers(coverage="BLOCKED"),
                                 fable_guard=fake_guard(0, self.temp.name))
        self.assertEqual(overall, "BLOCKED")

    def test_no_layers_is_blocked(self):
        overall, _detail = check(self.temp.name, None, fable_guard=fake_guard(0, self.temp.name))
        self.assertEqual(overall, "BLOCKED")

    def test_conformance_with_mi_report(self):
        cases = [ready_layers(), ready_layers(semantic="PARTIAL"),
                 ready_layers(results="STALE", coverage="BLOCKED"),
                 ready_layers(persistence="FAILED"),
                 ready_layers(persistence="NOT_REQUIRED")]
        reasons = {} if cases[-1].get("persistence") != "NOT_REQUIRED" else {
            "persistence": "no restart proof required"}
        for layers in cases:
            mine = compose_overall(layers, reasons if "NOT_REQUIRED" in layers.values() else None)
            theirs = report.compose(layers, reasons if "NOT_REQUIRED" in layers.values() else None)
            self.assertEqual(mine["overall"], theirs["overall"], layers)

    def test_cli_end_to_end(self):
        bridge = str(STAGE / "scripts" / "fable_bridge_v2.py")
        layers = Path(self.temp.name) / "layers.json"
        layers.write_text(json.dumps(ready_layers()))
        proc = subprocess.run(
            [sys.executable, bridge, "--project-root", self.temp.name,
             "--fable-guard", fake_guard(0, self.temp.name),
             "--layers-file", str(layers)],
            text=True, capture_output=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr[-500:])
        self.assertEqual(json.loads(proc.stdout)["overall"], "READY_FOR_DECLARED_TASK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
