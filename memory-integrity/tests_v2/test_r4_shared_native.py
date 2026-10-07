"""R4 shared-native claim qualification contract.

RED first: the release must expose a granular shared-project claim path rather
than promoting the disposable pilot or enabling an unrestricted native adapter.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hybrid_bridge import native


class SharedNativeSurfaceTests(unittest.TestCase):
    def test_granular_shared_claim_surface_exists(self):
        self.assertTrue(callable(getattr(native, "validate_shared_claim_authorization", None)))
        self.assertTrue(callable(getattr(native, "SharedNativeClaimAdapter", None)))
        self.assertTrue(callable(getattr(native, "shared_claim_qualification", None)))

    def test_native_selection_digest_is_public_and_deterministic(self):
        selection = native.NativeSelection(
            executable="C:/runtime/bd.exe",
            database="C:/project",
            expected_version="1.3.1",
            executable_sha256="a" * 64,
            expected_project_id="project-1",
            expected_database_name="project_db",
            expected_prefix="proj",
        )
        fn = getattr(native, "selection_digest", None)
        self.assertTrue(callable(fn))
        first = fn(selection)
        second = fn(selection)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
