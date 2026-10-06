#!/usr/bin/env python3
"""M1: scope audits catch missing/changed/misbound sources; engine deep-checks."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from integrity_v2 import source_audit  # noqa: E402

STAGE = Path(__file__).resolve().parents[1]
ENGINE = STAGE.parents[0] / "claude-mon"

sys.path.insert(0, str(ENGINE / "scripts"))
from complete_read_v2 import inventory, partition  # noqa: E402


def project(files):
    temp = tempfile.TemporaryDirectory(prefix="audit-")
    root = Path(temp.name)
    for rel, data in files.items():
        (root / rel).write_bytes(data)
    return temp, root


def freeze(root, rels):
    return inventory.freeze_scope(root, rels)


def read_all(root, rels):
    return {rel: (root / rel).read_bytes() for rel in rels}


class BindingTests(unittest.TestCase):
    def test_ready_when_unchanged(self):
        temp, root = project({"a.txt": b"hello\n"})
        try:
            scope = freeze(root, ["a.txt"])
            man = partition.build_manifest("SRC-A", b"hello\n")
            verdict, findings = source_audit.audit_scope(
                scope, read_all(root, ["a.txt"]), {"a.txt": man}, engine_root=str(ENGINE))
            self.assertEqual(verdict, "READY", findings)
        finally:
            temp.cleanup()

    def test_missing_source_blocked(self):
        temp, root = project({"a.txt": b"hello\n"})
        try:
            scope = freeze(root, ["a.txt"])
            (root / "a.txt").unlink()
            verdict, findings = source_audit.audit_scope(scope, {}, {})
            self.assertEqual(verdict, "BLOCKED", findings)
        finally:
            temp.cleanup()

    def test_changed_source_stale(self):
        temp, root = project({"a.txt": b"v1"})
        try:
            scope = freeze(root, ["a.txt"])
            (root / "a.txt").write_bytes(b"v2")
            verdict, findings = source_audit.audit_scope(
                scope, read_all(root, ["a.txt"]), {})
            self.assertEqual(verdict, "STALE", findings)
            self.assertTrue(any("E_SOURCE_STALE" in f for f in findings))
        finally:
            temp.cleanup()

    def test_swapped_manifest_binding_mismatch(self):
        temp, root = project({"a.txt": b"aaa\n", "b.txt": b"bbb\n"})
        try:
            scope = freeze(root, ["a.txt"])
            man_b = partition.build_manifest("SRC-B", b"bbb\n")
            verdict, findings = source_audit.audit_scope(
                scope, read_all(root, ["a.txt"]), {"a.txt": man_b})
            self.assertEqual(verdict, "STALE", findings)
            self.assertTrue(any("BINDING_MISMATCH" in f for f in findings), findings)
        finally:
            temp.cleanup()

    def test_empty_scope_blocked(self):
        verdict, findings = source_audit.audit_scope(
            {"schema_version": 2, "verdict": "NOT_APPLICABLE", "sources": [],
             "scope_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
            {}, {})
        self.assertEqual(verdict, "BLOCKED", findings)

    def test_engine_catches_deep_manifest_defect(self):
        temp, root = project({"a.txt": b"one\ntwo\n"})
        try:
            scope = freeze(root, ["a.txt"])
            man = partition.build_manifest("SRC-A", b"one\ntwo\n")
            broken = copy.deepcopy(man)
            broken["chunks"].append(dict(broken["chunks"][0]))
            verdict, findings = source_audit.audit_scope(
                scope, read_all(root, ["a.txt"]), {"a.txt": broken},
                engine_root=str(ENGINE))
            self.assertNotEqual(verdict, "READY", findings)
            self.assertTrue(any("E_MANIFEST_INVALID" in f for f in findings), findings)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
