"""Static contract for the isolated native M7 GitHub Actions pilot."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "m7-native-pilot.yml"


class NativePilotWorkflowContract(unittest.TestCase):
    def test_workflow_is_pinned_disposable_and_retains_receipt(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = [
            "windows-latest",
            "development/m7-completion",
            "beads_1.3.1_windows_amd64.zip",
            "48cd82e1d3e311c9bf9a5d6d67ad1a8542ae13d4e20c5bfb527656c5e666af76",
            "memory-integrity/scripts/m7_native_pilot.py",
            "--expected-executable-sha256",
            "M7_DISPOSABLE_PILOT_VERIFIED",
            "claim_invocations",
            "NATIVE_INTENT,NATIVE_UNKNOWN,NATIVE_RECONCILED",
            "actions/upload-artifact@v4",
            "contents: read",
        ]
        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, text)
        self.assertNotIn("secrets.", text.lower())
        self.assertNotIn("development/r4-native", text)

    def test_workflow_does_not_run_on_main(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        branch_block = text.split("branches:", 1)[1].split("paths:", 1)[0]
        self.assertNotIn("main", branch_block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
