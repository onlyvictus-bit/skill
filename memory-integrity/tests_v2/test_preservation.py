"""Portable preservation/content tests: no external workspace anchor."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

class Preservation(unittest.TestCase):
    def test_r1_prefix_preserved_byte_for_byte(self):
        baseline = json.loads((ROOT / "tests_v2" / "baseline-r1.json").read_text(encoding="utf-8"))
        row = next(r for r in baseline["files"] if r["path"] == "SKILL.md")
        current = (ROOT / "SKILL.md").read_bytes()
        self.assertGreaterEqual(len(current), row["bytes"])
        self.assertEqual(sha(current[:row["bytes"]]), row["sha256"])

    def test_release_exact_content_and_declared_changes(self):
        name = "R3-CONTENT.json" if (ROOT/"tests_v2/R3-CONTENT.json").is_file() else "R2-CONTENT.json"
        manifest = json.loads((ROOT / "tests_v2" / name).read_text(encoding="utf-8"))
        baseline = json.loads((ROOT / "tests_v2" / "baseline-r1.json").read_text(encoding="utf-8"))
        actual = {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in ROOT.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
                  and p.relative_to(ROOT).as_posix() != "tests_v2/"+name}
        self.assertEqual(actual, manifest["files"])
        original = {r["path"]:r["sha256"] for r in baseline["files"]}
        self.assertFalse(set(original) - set(actual), "original file deleted")
        changed = sorted(p for p in original if original[p] != actual[p])
        self.assertEqual(changed, manifest["changed_r1_files"])
        added = sorted(set(actual) - set(original))
        self.assertEqual(added, manifest["added_files"])

if __name__ == "__main__":
    unittest.main()
