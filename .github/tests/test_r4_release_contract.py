"""Repository-level R4 formal release contract.

This file deliberately lives outside either skill package. Packaged skill
tests must not depend on repository-only workflows.
"""
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"


class R4ReleaseContractTests(unittest.TestCase):
    def test_formal_successor_pair_exists(self):
        for name in (
            "memory-integrity-r4.zip",
            "claude-mon-r4.zip",
            "Memory-Integrity-R4-Release-Manifest.json",
            "Verify-Memory-Integrity-R4.py",
        ):
            with self.subTest(name=name):
                self.assertTrue((RELEASE / name).is_file(), name)

    def test_release_identity_is_m12_and_pair_is_matching(self):
        manifest = json.loads(
            (RELEASE / "Memory-Integrity-R4-Release-Manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["release"], "2.0.0-m12-r4")
        self.assertEqual(set(manifest["packages"]), {"memory-integrity", "claude-mon"})
        self.assertTrue(manifest["native_shared_claim_qualified"])
        self.assertFalse(manifest["native_merge_qualified"])

    def test_each_release_zip_is_single_safe_skill(self):
        for package in ("memory-integrity", "claude-mon"):
            archive = RELEASE / (package + "-r4.zip")
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
            self.assertEqual(sum(name.endswith("/SKILL.md") for name in names), 1)
            self.assertTrue(all(name.startswith(package + "/") for name in names))
            self.assertFalse(any(".." in Path(name).parts or "\\" in name for name in names))

    def test_repo_only_ci_test_is_not_inside_memory_integrity_package(self):
        archive = RELEASE / "memory-integrity-r4.zip"
        with zipfile.ZipFile(archive) as z:
            names = set(z.namelist())
        self.assertNotIn(
            "memory-integrity/tests_v2/test_m7_native_ci_workflow.py", names
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
