"""M7 native journal/recovery contract.

These tests exercise the durable CM journal with a qualified adapter-shaped
fixture.  They prove orchestration semantics only; they do not claim that a
real Beads binary is qualified.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parent / "claude-mon" / "scripts"))

from complete_read_v2 import ledger
from hybrid_bridge import native


def good_guard():
    return {
        "ok": True,
        "coordinated": True,
        "phase": "dispatch",
        "blocked": [],
        "ready": [],
        "snapshot_digest": "6" * 64,
        "revision": "native-revision-1",
        "basis": {
            "policy_digest": "7" * 64,
            "snapshot_digest": "6" * 64,
            "prerequisites": {},
        },
    }


class QualifiedAdapterFixture:
    """Adapter-shaped fixture for journal semantics; never a native proof."""

    native_write_qualified = True
    evidence_class = "NATIVE_VERIFIED"
    selection_digest = "1" * 64
    qualification_id = "qual-fixture-1"
    qualification_evidence_refs = ("2" * 64,)

    def __init__(self):
        self.write_count = 0
        self.effects = {}
        self.crash_after_effect = False

    def execute(self, operation_id, command):
        self.write_count += 1
        self.effects[command["native_task_id"]] = dict(command)
        evidence = {
            "operation_id": operation_id,
            "exit_code": 0,
            "stdout_sha256": "3" * 64,
            "stderr_sha256": "4" * 64,
        }
        if self.crash_after_effect:
            self.crash_after_effect = False
            raise RuntimeError("simulated interruption after native effect")
        return evidence

    def readback(self, command):
        observed = self.effects.get(command["native_task_id"])
        return {
            "applied": observed == command,
            "native_task_id": command["native_task_id"],
            "snapshot_digest": "5" * 64,
            "observed_state": None if observed is None else {"command": observed},
        }


class NativeJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mi-m7-journal-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = ledger.connect(self.root / "ledger.sqlite")
        self.addCleanup(self._close)
        self.journal = native.CMCoordinationJournal(self.db, ledger)
        self.adapter = QualifiedAdapterFixture()
        self.command = {
            "kind": "claim",
            "native_task_id": "mip-a",
            "actor": "memory-integrity-pilot",
        }

    def _close(self):
        try:
            self.db.close()
        except Exception:
            pass

    def _events(self, operation_id):
        rows = self.db.execute(
            "SELECT kind, detail FROM events WHERE kind LIKE 'NATIVE_%' ORDER BY seq"
        ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(row["detail"])
            if payload.get("operation_id") == operation_id:
                result.append(row["kind"])
        return result

    def test_success_is_intent_then_one_outcome_and_repeat_is_idempotent(self):
        first = native.coordinate_native_operation(
            self.journal, self.adapter, "op-success", "work-A",
            self.command, good_guard())
        self.assertEqual(first["status"], "NATIVE_APPLIED")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(self._events("op-success"), ["NATIVE_INTENT", "NATIVE_OUTCOME"])

        again = native.coordinate_native_operation(
            self.journal, self.adapter, "op-success", "work-A",
            self.command, good_guard())
        self.assertEqual(again["status"], "IDEMPOTENT_NATIVE_APPLIED")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(self._events("op-success"), ["NATIVE_INTENT", "NATIVE_OUTCOME"])

    def test_interruption_after_effect_recovers_by_readback_without_second_write(self):
        self.adapter.crash_after_effect = True
        first = native.coordinate_native_operation(
            self.journal, self.adapter, "op-crash", "work-A",
            self.command, good_guard())
        self.assertEqual(first["status"], "UNKNOWN")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(self._events("op-crash"), ["NATIVE_INTENT", "NATIVE_UNKNOWN"])

        self.db.close()
        self.db = ledger.connect(self.root / "ledger.sqlite")
        self.journal = native.CMCoordinationJournal(self.db, ledger)

        repeated = native.coordinate_native_operation(
            self.journal, self.adapter, "op-crash", "work-A",
            self.command, good_guard())
        self.assertEqual(repeated["status"], "UNKNOWN")
        self.assertEqual(self.adapter.write_count, 1)

        recovered = native.reconcile_native_operation(
            self.journal, self.adapter, "op-crash", "work-A", self.command)
        self.assertEqual(recovered["status"], "RECONCILED_NATIVE_APPLIED")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(
            self._events("op-crash"),
            ["NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"],
        )

        again = native.reconcile_native_operation(
            self.journal, self.adapter, "op-crash", "work-A", self.command)
        self.assertEqual(again["status"], "IDEMPOTENT_RECONCILED")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(
            self._events("op-crash"),
            ["NATIVE_INTENT", "NATIVE_UNKNOWN", "NATIVE_RECONCILED"],
        )

    def test_absent_readback_stays_unknown_and_never_retries(self):
        self.journal.append("NATIVE_INTENT", "op-absent", {
            "work_item_id": "work-A",
            "command_digest": native._command_digest(self.command),
            "selection_digest": self.adapter.selection_digest,
            "qualification_id": self.adapter.qualification_id,
            "guard_digest": "8" * 64,
            "evidence_class": "NATIVE_VERIFIED",
            "evidence_refs": list(self.adapter.qualification_evidence_refs),
        })
        result = native.reconcile_native_operation(
            self.journal, self.adapter, "op-absent", "work-A", self.command)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(self.adapter.write_count, 0)
        self.assertEqual(self._events("op-absent"), ["NATIVE_INTENT"])

    def test_blocked_or_uncoordinated_guard_writes_nothing(self):
        for guard in (
            dict(good_guard(), ok=False, blocked=["A"]),
            dict(good_guard(), coordinated=False),
            dict(good_guard(), phase="report"),
        ):
            with self.subTest(guard=guard):
                before = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                with self.assertRaisesRegex(native.NativeContractError, "E_NATIVE_GUARD"):
                    native.coordinate_native_operation(
                        self.journal, self.adapter, "op-blocked", "work-A",
                        self.command, guard)
                after = self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                self.assertEqual(after, before)
                self.assertEqual(self.adapter.write_count, 0)

    def test_operation_identity_cannot_rebind_command_work_item_or_selection(self):
        native.coordinate_native_operation(
            self.journal, self.adapter, "op-bind", "work-A",
            self.command, good_guard())
        changed = dict(self.command, native_task_id="mip-b")
        with self.assertRaisesRegex(native.NativeContractError, "E_NATIVE_OPERATION_REBIND"):
            native.coordinate_native_operation(
                self.journal, self.adapter, "op-bind", "work-A",
                changed, good_guard())
        with self.assertRaisesRegex(native.NativeContractError, "E_NATIVE_OPERATION_REBIND"):
            native.coordinate_native_operation(
                self.journal, self.adapter, "op-bind", "work-B",
                self.command, good_guard())
        self.adapter.selection_digest = "9" * 64
        with self.assertRaisesRegex(native.NativeContractError, "E_NATIVE_OPERATION_REBIND"):
            native.reconcile_native_operation(
                self.journal, self.adapter, "op-bind", "work-A", self.command)
        self.assertEqual(self.adapter.write_count, 1)


class GuardDerivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mi-m7-guard-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = ledger.connect(self.root / "ledger.sqlite")
        self.addCleanup(lambda: self.db.close())
        self.journal = native.CMCoordinationJournal(self.db, ledger)
        self.adapter = QualifiedAdapterFixture()
        self.command = {
            "kind": "claim",
            "native_task_id": "mip-a",
            "actor": "memory-integrity-pilot",
        }

    def test_wrapper_derives_guard_from_coordination_module(self):
        calls = []
        class Coordination:
            @staticmethod
            def guard(db, work_item_id, artifacts_dir, current_context, phase):
                calls.append((db, work_item_id, artifacts_dir, current_context, phase))
                return good_guard()

        result = native.coordinate_guarded_native_operation(
            Coordination, self.db, self.journal, self.adapter,
            "op-guarded", "work-A", str(self.root / "artifacts"),
            {"contexts": {"work-A": {"observed": True}}}, self.command)
        self.assertEqual(result["status"], "NATIVE_APPLIED")
        self.assertEqual(self.adapter.write_count, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], "work-A")
        self.assertEqual(calls[0][-1], "dispatch")

    def test_blocked_real_guard_prevents_intent_and_native_call(self):
        class Coordination:
            @staticmethod
            def guard(*args, **kwargs):
                raise RuntimeError("E_COORD_BLOCKED: prerequisite A incomplete")

        with self.assertRaisesRegex(RuntimeError, "E_COORD_BLOCKED"):
            native.coordinate_guarded_native_operation(
                Coordination, self.db, self.journal, self.adapter,
                "op-blocked-real", "work-A", str(self.root / "artifacts"),
                {"contexts": {}}, self.command)
        self.assertEqual(self.adapter.write_count, 0)
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM events WHERE kind LIKE 'NATIVE_%'").fetchone()[0],
            0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
