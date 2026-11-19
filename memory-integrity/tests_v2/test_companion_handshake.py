#!/usr/bin/env python3
"""M0: companion handshake passes real engines, fails everything else."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import engine_client  # noqa: E402

STAGE = Path(__file__).resolve().parents[1]
ENGINE = STAGE.parents[0] / "claude-mon"


class HandshakeTests(unittest.TestCase):
    def test_real_engine_passes_with_pin(self):
        from memory_integrity_v2 import PINNED_ENGINE_DIGEST
        self.assertFalse(PINNED_ENGINE_DIGEST.startswith("REPLACE_"))
        ok, payload = engine_client.handshake(str(ENGINE), expect_digest=PINNED_ENGINE_DIGEST)
        self.assertTrue(ok, payload)
        self.assertEqual(payload["engine"], "claude-mon")

    def test_missing_companion_fails_structured(self):
        ok, payload = engine_client.handshake(str(STAGE / "no-such-engine"))
        self.assertFalse(ok)
        self.assertEqual(payload["error"]["code"], "E_COMPANION_MISSING")

    def test_wrong_schema_version_fails(self):
        ok, payload = engine_client.handshake(str(ENGINE), expect_schema_version=99)
        self.assertFalse(ok)
        self.assertEqual(payload["error"]["code"], "E_SCHEMA_MISMATCH")

    def test_tampered_engine_digest_fails(self):
        # Unapproved code is now refused BEFORE it can print an envelope.
        # Inject only the response here to retain the independent protocol check.
        from memory_integrity_v2 import PINNED_ENGINE_DIGEST
        ok, approved = engine_client.handshake(ENGINE)
        self.assertTrue(ok, approved)
        with patch.object(engine_client, 'run_engine', return_value=({**approved, 'schema_digest': '0'*64}, None)):
            ok, payload = engine_client.handshake(ENGINE, expect_digest=PINNED_ENGINE_DIGEST)
            self.assertFalse(ok)
            self.assertEqual(payload["error"]["code"], "E_DIGEST_MISMATCH")

    def test_garbage_stdout_fails_structured(self):
        with tempfile.TemporaryDirectory(prefix="garbage-engine-") as temp:
            entry = Path(temp) / "scripts"
            entry.mkdir(parents=True)
            (entry / "claude_mon_v2.py").write_text("print('not json {{')\n", encoding="utf-8")
            ok, payload = engine_client.handshake(temp)
            self.assertFalse(ok)
            self.assertEqual(payload["error"]["code"], "E_COMPANION_RELEASE")

    def test_bad_json_from_approved_process_fails_structured(self):
        from types import SimpleNamespace
        with patch.object(engine_client.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='not json {', stderr='')):
            value, error = engine_client.run_engine(ENGINE, ['capabilities'])
        self.assertIsNone(value)
        self.assertEqual(error['code'], 'E_COMPANION_BAD_JSON')


if __name__ == "__main__":
    unittest.main(verbosity=2)
