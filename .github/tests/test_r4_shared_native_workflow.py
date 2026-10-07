"""Static R4 shared-native qualification workflow contract."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "r4-shared-claim-pilot.yml"


class SharedNativeWorkflowContract(unittest.TestCase):
    def test_workflow_is_pinned_scoped_and_retains_evidence(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for item in (
            "windows-latest",
            "release/r4-successor",
            "beads_1.3.1_windows_amd64.zip",
            "48cd82e1d3e311c9bf9a5d6d67ad1a8542ae13d4e20c5bfb527656c5e666af76",
            "r4_shared_claim_pilot.py",
            "R4_SHARED_CLAIM_PROTOCOL_VERIFIED",
            "native_shared_claim_protocol_qualified",
            "native_merge_qualified",
            "claim_invocations",
            "NATIVE_INTENT,NATIVE_OUTCOME",
            "actions/upload-artifact@v4",
            "contents: read",
        ):
            with self.subTest(item=item):
                self.assertIn(item, text)
        self.assertNotIn("secrets.", text.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
