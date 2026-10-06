#!/usr/bin/env python3
"""M2: persistence boundaries are proven separately, never assumed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import report, watchdog  # noqa: E402


class BoundaryTests(unittest.TestCase):
    def test_same_session_never_proves_restart(self):
        self.assertEqual(watchdog.boundary_verdict("same_session", {"anything": 1}),
                         "BOUNDARY_UNVERIFIED")

    def test_restart_needs_generation_change(self):
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": "g1", "generation_after": "g1",
                                "same_data_identity": True}), "BOUNDARY_UNVERIFIED")
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": "g1", "generation_after": "g2",
                                "same_data_identity": True}), "BOUNDARY_UNVERIFIED")

    def test_restore_needs_identity(self):
        self.assertEqual(watchdog.boundary_verdict(
            "datastore_restore", {"generation_before": "g1", "generation_after": "g2",
                                  "same_data_identity": False}), "BOUNDARY_UNVERIFIED")
        self.assertEqual(watchdog.boundary_verdict(
            "datastore_restore", {"generation_before": "g1", "generation_after": "g2",
                                  "same_data_identity": True}), "BOUNDARY_UNVERIFIED")

    def test_unknown_boundary_rejected(self):
        with self.assertRaises(watchdog.WatchdogError):
            watchdog.boundary_verdict("teleport", {})


class ReportTests(unittest.TestCase):
    def layers(self, **over):
        base = {n: "READY" for n in report.LAYERS}
        base.update(over)
        return base

    def test_all_ready_is_ready(self):
        out = report.compose(self.layers())
        self.assertEqual(out["overall"], "READY_FOR_DECLARED_TASK")

    def test_one_blocked_blocks(self):
        out = report.compose(self.layers(coverage="BLOCKED"))
        self.assertEqual(out["overall"], "BLOCKED")

    def test_failed_dominates(self):
        out = report.compose(self.layers(coverage="BLOCKED", semantic="FAILED"))
        self.assertEqual(out["overall"], "FAILED")

    def test_counts_cannot_override(self):
        out = report.compose(self.layers(semantic="PARTIAL"),
                             counts={"units_done": 50000, "units_total": 50000})
        self.assertEqual(out["overall"], "PARTIAL")

    def test_not_required_needs_reason(self):
        with self.assertRaises(report.ReportError):
            report.compose(self.layers(persistence="NOT_REQUIRED"))
        out = report.compose(self.layers(persistence="NOT_REQUIRED"),
                             reasons={"persistence": "task needs no restart proof"})
        self.assertEqual(out["overall"], "READY_FOR_DECLARED_TASK")

    def test_unknown_layer_rejected(self):
        bad = self.layers()
        bad["vibes"] = "READY"
        with self.assertRaises(report.ReportError):
            report.compose(bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
