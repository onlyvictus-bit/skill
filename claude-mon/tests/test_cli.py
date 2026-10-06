import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
CLI = SKILL / "scripts" / "claude_mon.py"


class CliTests(unittest.TestCase):
    def run_cli(self, *args, expect=0):
        proc = subprocess.run([sys.executable, str(CLI), *args], text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, expect, proc.stderr or proc.stdout)
        return proc

    def test_end_to_end_cli_materializes_chunk_and_status_hides_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "fable").mkdir(parents=True)
            secret = "PRIVATE_PAYLOAD_123\nsecond line\n"
            src = root / "source.txt"
            src.write_text(secret, encoding="utf-8")
            reg = json.loads(self.run_cli("register", "--project", td, "--source", str(src)).stdout)
            sid = reg["source_id"]
            self.run_cli("unitize", "--project", td, "--source-id", sid, "--max-unit-bytes", "12")
            chunk = json.loads(self.run_cli("chunk", "--project", td, "--source-id", sid, "--max-primary-bytes", "20").stdout)
            chunks_path = root / chunk["chunks_path"]
            first_chunk = json.loads(chunks_path.read_text(encoding="utf-8").splitlines()[0])
            payload = json.loads(self.run_cli("payload", "--project", td, "--source-id", sid, "--chunk-id", first_chunk["chunk_id"]).stdout)
            self.assertIn("text", payload)
            self.assertTrue(payload["text"])
            self.assertEqual(payload["payload_sha256"], first_chunk["payload_sha256"])
            status = self.run_cli("status", "--project", td).stdout
            self.assertNotIn("PRIVATE_PAYLOAD_123", status)

    def test_register_preserves_provenance_when_cli_option_is_omitted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "fable").mkdir(parents=True)
            src = root / "source.txt"
            src.write_text("one\n", encoding="utf-8")
            first = json.loads(self.run_cli(
                "register", "--project", td, "--source", str(src),
                "--provenance", "user-request",
            ).stdout)
            second = json.loads(self.run_cli("register", "--project", td, "--source", str(src)).stdout)
            self.assertEqual(first["provenance"], ["user-request"])
            self.assertEqual(second["provenance"], ["user-request"])

    def test_verify_returns_nonzero_on_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "fable").mkdir(parents=True)
            src = root / "source.txt"
            src.write_text("one\n", encoding="utf-8")
            sid = json.loads(self.run_cli("register", "--project", td, "--source", str(src)).stdout)["source_id"]
            self.run_cli("unitize", "--project", td, "--source-id", sid)
            self.run_cli("chunk", "--project", td, "--source-id", sid)
            src.write_text("two\n", encoding="utf-8")
            proc = self.run_cli("verify", "--project", td, "--source-id", sid, expect=2)
            out = json.loads(proc.stdout)
            self.assertEqual(out["unit_manifest"]["status"], "STALE")


if __name__ == "__main__":
    unittest.main()
