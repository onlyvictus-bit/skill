#!/usr/bin/env python3
"""M3 native-adapter contract tests: fixtures exercise policy, never bd."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from hybrid_bridge import native  # noqa: E402


class NativeAdapterContractTests(unittest.TestCase):
    def test_unqualified_binary_is_never_active_even_with_matching_metadata(self):
        config = native.NativeSelection(
            executable="C:/candidate/bd.exe", database="C:/scratch/tasks",
            expected_version="1.3.1", executable_sha256="a" * 64,
        )
        status = native.native_status(config)
        self.assertFalse(status["active"])
        self.assertEqual(status["qualification"], "UNQUALIFIED_M7")
        self.assertTrue(any("executable" in item for item in status["missing"]))

    def test_real_adapter_refuses_any_write_before_native_qualification(self):
        adapter = native.NativeBeadsAdapter(native.NativeSelection(
            executable="C:/candidate/bd.exe", database="C:/scratch/tasks",
            expected_version="1.3.1", executable_sha256="a" * 64,
        ))
        with self.assertRaises(native.NativeQualificationError):
            adapter.execute("op-a", {"kind": "claim"})

    def test_fixture_operation_records_unknown_and_reconcile_never_repeats_write(self):
        adapter = native.FixtureBeadsAdapter({"branch": "feature/a", "head": "h1"})
        journal = native.MemoryCoordinationJournal()
        adapter.interrupt_next("op-a")
        first = native.coordinate_fixture_operation(journal, adapter, "op-a", {"kind": "claim"})
        self.assertEqual(first["status"], "UNKNOWN")
        self.assertEqual(adapter.write_count, 1)
        second = native.coordinate_fixture_operation(journal, adapter, "op-a", {"kind": "claim"})
        self.assertEqual(second["status"], "UNKNOWN")
        self.assertEqual(adapter.write_count, 1, "unknown operations must reconcile, not retry")
        self.assertEqual([e["kind"] for e in journal.events], ["NATIVE_INTENT", "NATIVE_UNKNOWN"])
        reconciled = native.reconcile_fixture_operation(journal, adapter, "op-a")
        self.assertEqual(reconciled["status"], "RECONCILED_APPLIED")
        self.assertEqual(adapter.write_count, 1)
        self.assertEqual(journal.events[-1]["kind"], "NATIVE_RECONCILED")

    def test_fixture_snapshot_and_journal_gap_are_explicit_test_only_evidence(self):
        adapter = native.FixtureBeadsAdapter({"branch": "feature/a", "head": "h1"})
        snapshot = adapter.read_snapshot()
        self.assertEqual(snapshot["evidence_class"], "TEST_ONLY")
        cursor = native.JournalCursor("replica-a", "feature/a", 4)
        gap = native.observe_journal(cursor, [{"seq": 6, "op": "close"}])
        self.assertEqual(gap["status"], "GAP_REBASELINE_REQUIRED")
        self.assertEqual(gap["expected_next_seq"], 5)
        self.assertEqual(native.observe_journal(cursor,[{"seq":5,"op":"merge"}])["status"],"GAP_REBASELINE_REQUIRED")
        self.assertEqual(native.observe_journal(cursor,[],{"replica":"replica-a","branch":"foreign"})["status"],"GAP_REBASELINE_REQUIRED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
