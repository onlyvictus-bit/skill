"""R4 shared claim protocol pilot smoke contract."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hybrid_bridge import shared_native_pilot
import r4_shared_claim_pilot


class SharedClaimPilotContract(unittest.TestCase):
    def test_public_pilot_surface_exists(self):
        self.assertTrue(callable(shared_native_pilot.run_shared_claim_protocol_pilot))
        self.assertTrue(callable(r4_shared_claim_pilot.main))

    def test_pilot_is_claim_only_and_never_globally_qualifies_native(self):
        source = (ROOT / "scripts" / "hybrid_bridge" / "shared_native_pilot.py").read_text(encoding="utf-8")
        self.assertIn("SharedNativeClaimAdapter", source)
        self.assertIn("coordinate_guarded_native_operation", source)
        self.assertIn('"native_shared_claim_protocol_qualified": True', source)
        self.assertIn('"native_beads_qualified": False', source)
        self.assertIn('"native_merge_qualified": False', source)
        self.assertNotIn('"kind": "close"', source)
        self.assertNotIn('"kind": "merge"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
