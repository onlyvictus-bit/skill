#!/usr/bin/env python3
"""M0: v2 contracts reject invalid inputs; handshake fails closed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import contracts  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_schema_digest_stable_and_hex(self):
        first = contracts.schema_digest()
        self.assertEqual(len(first), 64)
        int(first, 16)
        self.assertEqual(first, contracts.schema_digest())

    def test_reject_unknown_enum(self):
        with self.assertRaises(contracts.ContractError):
            contracts.require_enum("COMPLETE-ISH", contracts.RECEIPT_STATES, "receipt")

    def test_reject_bad_digest(self):
        with self.assertRaises(contracts.ContractError):
            contracts.require_sha256("abc", "manifest")
        with self.assertRaises(contracts.ContractError):
            contracts.require_sha256("z" * 64, "manifest")

    def test_reject_duplicate_json_keys(self):
        with self.assertRaises(contracts.ContractError):
            contracts.loads_strict('{"a": 1, "a": 2}')

    def test_reject_missing_and_unknown_fields(self):
        with self.assertRaises(contracts.ContractError):
            contracts.require_keys({"a": 1}, {"a", "b"}, {"a", "b"}, "doc")
        with self.assertRaises(contracts.ContractError):
            contracts.require_keys({"a": 1, "zzz": 2}, {"a"}, {"a"}, "doc")

    def test_reject_duplicate_ids(self):
        with self.assertRaises(contracts.ContractError):
            contracts.require_unique_ids([{"id": "A"}, {"id": "A"}], "rows")

    def test_reject_wrong_schema_version(self):
        ok, err = contracts.check_capabilities(
            {"ok": True, "schema_version": 1, "schema_digest": "a" * 64},
            expect_schema_version=2)
        self.assertFalse(ok)
        self.assertEqual(err["code"], "E_SCHEMA_MISMATCH")

    def test_reject_digest_mismatch(self):
        env = contracts.capabilities_envelope()
        ok, err = contracts.check_capabilities(env, expect_digest="0" * 64)
        self.assertFalse(ok)
        self.assertEqual(err["code"], "E_DIGEST_MISMATCH")

    def test_accept_valid_envelope(self):
        env = contracts.capabilities_envelope()
        ok, err = contracts.check_capabilities(env, expect_digest=env["schema_digest"])
        self.assertTrue(ok)
        self.assertIsNone(err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
