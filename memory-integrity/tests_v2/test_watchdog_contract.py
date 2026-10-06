#!/usr/bin/env python3
"""M2: strict round-trip against a controlled TEST_ONLY backend."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import watchdog  # noqa: E402


class TestBackend:
    """Controlled in-memory store. TEST_ONLY: never live evidence."""
    def __init__(self, corrupt=None):
        self.store, self.corrupt = {}, corrupt
        self.next_id = 0

    def remember(self, text):
        self.next_id += 1
        rec = {"id": "canon-%d" % self.next_id, "text": text}
        self.store[rec["id"]] = rec
        return dict(rec)

    def search(self, query):
        if self.corrupt == "malformed":
            return ["not-a-dict"]
        return {"hits": [dict(r) for r in self.store.values() if query in r["text"]]}

    def fetch(self, record_id):
        rec = self.store.get(record_id)
        if rec is None:
            return None
        if self.corrupt == "wrong-content":
            return {"id": record_id, "text": "DIFFERENT"}
        return dict(rec)

    def delete(self, record_id):
        if self.corrupt == "unconfirmed":
            return {"deleted": False}
        self.store.pop(record_id, None)
        return {"deleted": True}


class GhostBackend(TestBackend):
    def delete(self, record_id):
        return {"deleted": True}  # lies: keeps the record


class WatchdogContractTests(unittest.TestCase):
    def test_healthy_path(self):
        out = watchdog.strict_roundtrip(TestBackend(), "s", "canary-1")
        self.assertEqual(out["verdict"], "HEALTHY", out)
        self.assertEqual(out["boundary"], "BOUNDARY_UNVERIFIED")

    def test_wrong_content_fails(self):
        out = watchdog.strict_roundtrip(TestBackend(corrupt="wrong-content"), "s", "canary-2")
        self.assertEqual(out["verdict"], "FAILED", out)
        self.assertIn("CONTENT", out["reason"])

    def test_unconfirmed_delete_fails_with_id(self):
        out = watchdog.strict_roundtrip(TestBackend(corrupt="unconfirmed"), "s", "canary-3")
        self.assertEqual(out["verdict"], "FAILED", out)
        self.assertIn("canary_id", out)

    def test_ghost_after_delete_fails(self):
        out = watchdog.strict_roundtrip(GhostBackend(), "s", "canary-4")
        self.assertEqual(out["verdict"], "FAILED", out)
        self.assertIn("GHOST", out["reason"])

    def test_malformed_response_is_blind(self):
        out = watchdog.strict_roundtrip(TestBackend(corrupt="malformed"), "s", "canary-5")
        self.assertEqual(out["verdict"], "BLIND", out)

    def test_transport_error_is_blind(self):
        class Broken:
            def remember(self, text):
                raise ConnectionError("down")
        out = watchdog.strict_roundtrip(Broken(), "s", "canary-6")
        self.assertEqual(out["verdict"], "BLIND", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
