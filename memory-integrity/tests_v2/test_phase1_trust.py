#!/usr/bin/env python3
"""Phase 1 RED: execution trust, oracle tiers, supply-chain pins.

Each test names its requirement. They must FAIL before the Phase 1
implementation and pass after, without weakening any existing suite.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from knowledge_bridge import trusted_runner  # noqa: E402
from knowledge_bridge import admission  # noqa: E402
from knowledge_bridge import supply_chain  # noqa: E402


class TrustRunnerTests(unittest.TestCase):
    def test_untrusted_execution_refused_without_sandbox(self):
        policy = trusted_runner.sandbox_available()
        self.assertFalse(policy["untrusted_allowed"])
        with self.assertRaises(trusted_runner.TrustError):
            trusted_runner.run({"trust": "UNTRUSTED", "test_paths": ["x"],
                                "root": ".", "output": "o.json",
                                "execution_id": "e1"})

    def test_socket_connect_denied_and_recorded(self):
        receipt = trusted_runner.run_fixture("socket-connect")
        self.assertFalse(receipt["ok"])
        self.assertIn("E_TEST_NETWORK_FORBIDDEN", receipt["detail"])

    def test_subprocess_network_denied(self):
        receipt = trusted_runner.run_fixture("subprocess-network")
        self.assertFalse(receipt["ok"])

    def test_path_outside_workspace_refused(self):
        with self.assertRaises(trusted_runner.TrustError):
            trusted_runner.check_path("/etc/passwd", Path(".").resolve())

    def test_symlink_escape_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            link = Path(temp) / "link"
            try:
                link.symlink_to(Path(temp) / "..", target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation unavailable")
            with self.assertRaises(trusted_runner.TrustError):
                trusted_runner.check_path(link / "x", Path(temp))

    def test_env_secrets_scrubbed(self):
        env = trusted_runner.scrub_env({"PATH": "x", "NVIDIA_API_KEY": "nvapi-SECRET"})
        self.assertNotIn("nvapi-SECRET", repr(env))

    def test_timeout_enforced(self):
        receipt = trusted_runner.run_fixture("infinite-loop", timeout=2)
        self.assertFalse(receipt["ok"])
        self.assertIn("timeout", receipt["detail"].lower())

    def test_duplicate_execution_id_no_rerun(self):
        first = trusted_runner.run_fixture("ok-case", execution_id="dup-1")
        second = trusted_runner.run_fixture("ok-case", execution_id="dup-1")
        self.assertEqual(first["receipt_digest"], second["receipt_digest"])
        self.assertEqual(second["reruns"], 2)


class OracleTierTests(unittest.TestCase):
    def test_manual_tier_compat(self):
        review = {"reviewer": "human", "oracle_digest": "a" * 64}
        self.assertEqual(admission.review_tier(review), "MANUAL_REPORTED_REVIEW")

    def test_same_actor_independent_refused(self):
        review = {"reviewer": "agent-1", "oracle_digest": "a" * 64,
                  "tier": "INDEPENDENT_VERIFIED",
                  "reviewer_identity": {"id": "agent-1", "kind": "agent"}}
        with self.assertRaises(ValueError):
            admission.check_reviewer_independence(review, producer_id="agent-1")

    def test_tampered_oracle_digest_refused(self):
        review = {"reviewer": "agent-2", "oracle_digest": "b" * 64,
                  "tier": "INDEPENDENT_VERIFIED",
                  "reviewer_identity": {"id": "agent-2", "kind": "agent"}}
        with self.assertRaises(ValueError):
            admission.check_reviewer_independence(
                review, producer_id="agent-1",
                expected_digest="a" * 64)

    def test_independent_without_witness_refused(self):
        review = {"reviewer": "agent-2", "oracle_digest": "a" * 64,
                  "tier": "INDEPENDENT_VERIFIED",
                  "reviewer_identity": {"id": "agent-2", "kind": "agent"}}
        with self.assertRaises(ValueError) as ctx:
            admission.check_reviewer_independence(review, producer_id="agent-1")
        self.assertIn("WITNESS", str(ctx.exception))

    def test_independent_with_witness_passes(self):
        review = {"reviewer": "agent-2", "oracle_digest": "a" * 64,
                  "tier": "INDEPENDENT_VERIFIED",
                  "reviewer_identity": {"id": "agent-2", "kind": "agent",
                                        "witness": {"run_id": "run-9",
                                                    "artifact_digest": "c" * 64}}}
        self.assertEqual(admission.check_reviewer_independence(
            review, producer_id="agent-1"), "INDEPENDENT_VERIFIED")


class SupplyChainTests(unittest.TestCase):
    def test_tampered_pin_detected(self):
        import copy
        pins = copy.deepcopy(supply_chain.controlled_pins())
        pins["pins"][0]["version"] = "9.9.9-evil"
        with self.assertRaises(supply_chain.SupplyChainError):
            supply_chain.verify_pins(pins)

    def test_missing_package_never_green(self):
        verdict = supply_chain.provenance_status("semantica-nonexistent-xyz")
        self.assertNotEqual(verdict, "VERIFIED")

    def test_record_hash_mismatch_refused(self):
        import json
        import tempfile
        from unittest import mock
        from pathlib import Path as _Path
        with tempfile.TemporaryDirectory() as temp:
            lock = _Path(temp) / "pins.json"
            lock.write_text(json.dumps({"pins": [
                {"name": "fakepkg", "version": "1.0",
                 "revision": "r1", "source": "test",
                 "record_sha256": {"f.py": "0" * 64}}]}))
            fake_dist = mock.Mock()
            fake_dist.read_text.return_value = "f.py,sha256=ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,1\n"
            with mock.patch.object(supply_chain, "LOCK", lock), \
                 mock.patch("importlib.util.find_spec", return_value=object()), \
                 mock.patch("importlib.metadata.version", return_value="1.0"), \
                 mock.patch("importlib.metadata.distribution", return_value=fake_dist):
                with self.assertRaises(supply_chain.SupplyChainError):
                    supply_chain.provenance_status("fakepkg")


if __name__ == "__main__":
    unittest.main(verbosity=1)
