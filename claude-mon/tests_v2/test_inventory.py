#!/usr/bin/env python3
"""M1: frozen scopes are explicit, bounded, and change-sensitive."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from complete_read_v2 import inventory  # noqa: E402


def make_project(files):
    temp = tempfile.TemporaryDirectory(prefix="inv-")
    root = Path(temp.name)
    for rel, data in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    temp.root = root
    return temp


class InventoryTests(unittest.TestCase):
    def test_freeze_explicit_set(self):
        temp = make_project({"a.txt": b"hello\n", "sub/b.txt": "héllo wörld\n".encode("utf-8")})
        try:
            scope = inventory.freeze_scope(temp.root, ["a.txt", "sub/b.txt"])
            self.assertEqual(scope["verdict"], "FROZEN")
            self.assertEqual(len(scope["sources"]), 2)
            self.assertEqual(len(scope["scope_digest"]), 64)
        finally:
            temp.cleanup()

    def test_empty_scope_refused(self):
        temp = make_project({"a.txt": b"x"})
        try:
            with self.assertRaises(inventory.EmptyScopeError):
                inventory.freeze_scope(temp.root, [])
            scope = inventory.freeze_scope(temp.root, [], allow_empty=True)
            self.assertEqual(scope["verdict"], "NOT_APPLICABLE")
        finally:
            temp.cleanup()

    def test_missing_source_blocked(self):
        temp = make_project({"a.txt": b"x"})
        try:
            with self.assertRaises(inventory.ContractError):
                inventory.freeze_scope(temp.root, ["nope.txt"])
        finally:
            temp.cleanup()

    def test_escape_refused(self):
        temp = make_project({"a.txt": b"x"})
        try:
            with self.assertRaises(inventory.PathEscapeError):
                inventory.freeze_scope(temp.root, ["../escape.txt"])
        finally:
            temp.cleanup()

    def test_change_after_freeze_changes_digest(self):
        temp = make_project({"a.txt": b"v1"})
        try:
            first = inventory.freeze_scope(temp.root, ["a.txt"])
            (temp.root / "a.txt").write_bytes(b"v2")
            second = inventory.freeze_scope(temp.root, ["a.txt"])
            self.assertNotEqual(first["scope_digest"], second["scope_digest"])
        finally:
            temp.cleanup()

    def test_snapshot_bytes_equal_source(self):
        temp = make_project({"a.txt": b"exact bytes\n"})
        try:
            scope = inventory.freeze_scope(temp.root, ["a.txt"])
            digest = scope["sources"][0]["sha256"]
            snap = temp.root / ".snapshot" / digest
            self.assertTrue(snap.is_file())
            self.assertEqual(snap.read_bytes(), b"exact bytes\n")
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
