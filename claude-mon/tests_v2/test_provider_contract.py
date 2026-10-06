#!/usr/bin/env python3
"""M4b: adapter protocol, TEST_ONLY labeling, response validation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import providers  # noqa: E402

MODEL = {"schema_version": 2, "provider": "test", "model": "m-1",
         "encoding": "o200k_base", "encoding_version": "t", "context_limit": 1000,
         "output_limit": 200, "counting_method": "tiktoken"}


class ProviderContractTests(unittest.TestCase):
    def test_prepared_request_canonical(self):
        raw1, digest1 = providers.prepared_request("W1", "task", ["U1", "U2"], "spec", MODEL)
        raw2, digest2 = providers.prepared_request("W1", "task", ["U1", "U2"], "spec", MODEL)
        self.assertEqual((raw1, digest1), (raw2, digest2))
        self.assertEqual(len(digest1), 64)

    def test_prepared_rejects_duplicates_and_empties(self):
        with self.assertRaises(providers.AdapterError):
            providers.prepared_request("W1", "task", ["U1", "U1"], "spec", MODEL)
        with self.assertRaises(providers.AdapterError):
            providers.prepared_request("W1", "task", [], "spec", MODEL)
        with self.assertRaises(providers.AdapterError):
            providers.prepared_request("W1", "task", ["U1"], "spec",
                                       {"provider": "x"})

    def test_testonly_ok_validated(self):
        adapter = providers.TestOnlyAdapter([("ok", {"U1": "r"})])
        raw, _ = providers.prepared_request("W1", "task", ["U1"], "spec", MODEL)
        resp = adapter.dispatch(raw)
        self.assertEqual(resp["evidence_class"], "TEST_ONLY")
        self.assertFalse(resp["live"])
        self.assertNotIn("raw_digest", resp)
        ok, reason = providers.validate_response(resp, ["U1"], "a" * 64)
        self.assertTrue(ok, reason)

    def test_testonly_never_live(self):
        adapter = providers.TestOnlyAdapter([("ok", {"U1": "r"})])
        raw, _ = providers.prepared_request("W1", "task", ["U1"], "spec", MODEL)
        with self.assertRaises(providers.AdapterError):
            adapter.dispatch(raw, live=True)

    def test_non_ok_terminal_rejected(self):
        for kind, payload in (("truncate", None), ("refuse", "no"), ("error", "boom")):
            adapter = providers.TestOnlyAdapter([(kind, payload)])
            raw, _ = providers.prepared_request("W1", "task", ["U1"], "spec", MODEL)
            resp = adapter.dispatch(raw)
            ok, reason = providers.validate_response(resp, ["U1"])
            self.assertFalse(ok, kind)
            self.assertIn("non-ok", reason)

    def test_unit_set_mismatch_rejected(self):
        adapter = providers.TestOnlyAdapter([("ok", {"U1": "r", "U2": "x"})])
        raw, _ = providers.prepared_request("W1", "task", ["U1"], "spec", MODEL)
        with self.assertRaises(providers.AdapterError):
            adapter.dispatch(raw)

    def test_unknown_state_rejected(self):
        ok, reason = providers.validate_response({"terminal_state": "maybe",
                                                  "evidence_class": "TEST_ONLY",
                                                  "unit_ids": [], "raw_digest": "a" * 64}, [])
        self.assertFalse(ok)
        self.assertIn("unknown terminal", reason)

    def test_base_adapter_dispatches_nothing(self):
        with self.assertRaises(providers.AdapterError):
            providers.ProviderAdapter().dispatch(b"{}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
