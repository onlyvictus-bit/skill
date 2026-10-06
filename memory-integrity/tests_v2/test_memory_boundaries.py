#!/usr/bin/env python3
"""M7: persistence boundaries need observed generation change + identity."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import recall, watchdog  # noqa: E402


class MemoryBoundaryTests(unittest.TestCase):
    def test_fresh_client_proves_client_only(self):
        self.assertEqual(watchdog.boundary_verdict("same_session", {"generation": "g2"}),
                         "BOUNDARY_UNVERIFIED")

    def test_generation_change_without_identity_insufficient(self):
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": "g1", "generation_after": "g2",
                                "same_data_identity": False}), "BOUNDARY_UNVERIFIED")

    def test_full_restart_evidence(self):
        self.assertEqual(watchdog.boundary_verdict(
            "service_restart", {"generation_before": "g1", "generation_after": "g2",
                                "same_data_identity": True}), "BOUNDARY_UNVERIFIED")

    def test_run_map_generation_tracks_boundary(self):
        import tempfile
        with tempfile.TemporaryDirectory(prefix="gen-") as temp:
            path = str(Path(temp) / "run-map.json")
            recall.save_run_map(path, {"run_dir": temp, "source_digests": {"a": "d1"},
                                       "artifact_digests": {}, "generation": "g1"})
            out = recall.load_run_map(path, {"a": "d1"})
            self.assertEqual(out["run_map"]["generation"], "g1")
            # A generation change without re-verified digests proves nothing alone.
            out2 = recall.load_run_map(path, {"a": "CHANGED"})
            self.assertFalse(out2["current"])

    def test_coverage_basis_carries_digest(self):
        # Every exhaustive answer names the source version it was computed
        # from; a caller comparing digests detects drift without re-reading.
        index = recall.build_index({"U1": "alpha"}, "digest-A")
        out = recall.exhaustive(index, lambda _i, _t: True)
        self.assertEqual(out["coverage_basis"]["source_digest"], "digest-A")
        self.assertNotEqual(out["coverage_basis"]["source_digest"], "digest-B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
