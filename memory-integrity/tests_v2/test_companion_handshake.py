#!/usr/bin/env python3
"""M0: companion handshake passes real engines, fails everything else."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

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
        with tempfile.TemporaryDirectory(prefix="tampered-engine-") as temp:
            fake = Path(temp) / "engine"
            shutil.copytree(ENGINE / "scripts", fake / "scripts")
            target = fake / "scripts" / "complete_read_v2" / "contracts.py"
            text = target.read_text(encoding="utf-8")
            patched = text.replace('"MANUAL_REPORTED",',
                                    '"MANUAL_REPORTED",\n    "FORGED_CLASS",', 1)
            self.assertNotEqual(patched, text)
            target.write_text(patched, encoding="utf-8")
            from memory_integrity_v2 import PINNED_ENGINE_DIGEST
            ok, payload = engine_client.handshake(str(fake), expect_digest=PINNED_ENGINE_DIGEST)
            self.assertFalse(ok)
            self.assertEqual(payload["error"]["code"], "E_DIGEST_MISMATCH")

    def test_garbage_stdout_fails_structured(self):
        with tempfile.TemporaryDirectory(prefix="garbage-engine-") as temp:
            entry = Path(temp) / "scripts"
            entry.mkdir(parents=True)
            (entry / "claude_mon_v2.py").write_text("print('not json {{')\n", encoding="utf-8")
            ok, payload = engine_client.handshake(temp)
            self.assertFalse(ok)
            self.assertEqual(payload["error"]["code"], "E_COMPANION_BAD_JSON")


if __name__ == "__main__":
    unittest.main(verbosity=2)
