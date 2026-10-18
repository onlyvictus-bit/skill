#!/usr/bin/env python3
"""Lease-v2 CM consumer integration tests for the isolated fence.

The v1 predecessor consumer is deliberately stopped (the gate test below
locks that refusal). These tests exercise the lease-v2 successor through
the concrete sealed backend with a TEST_ONLY process boundary, the same
pattern as the lease-backend tests: subprocess output is fabricated, so
they prove parsing, binding, refusal and journal semantics offline --
never native behavior, never qualification.
"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(SOURCE / "claude-mon" / "scripts"))

from complete_read_v2 import ledger  # noqa: E402
from hybrid_bridge import practical_backend, practical_consumer  # noqa: E402
from hybrid_bridge import practical_contract  # noqa: E402
from hybrid_bridge import practical_lease_backend  # noqa: E402
from hybrid_bridge.practical_lease_consumer import LeaseConsumerError, LeaseNativeConsumer  # noqa: E402
from tests_v2.test_practical_lease_contract import reassign_packet  # noqa: E402

# Deliberate tripwire: the literal must match the sealed backend DOLT_PIN.
# A pin change breaks these tests loudly instead of silently re-targeting.
PIN = 'ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2'


SELECTION = {
    "scratch_root": "C:/scratch/r5-fence", "dolt_executable": "C:/scratch/r5-fence/dolt.exe",
    "dolt_sha256": "a" * 64, "host": "127.0.0.1", "port": 3306,
    "database": "beads_scratch", "main_branch": "main",
    "incarnation": "scratch-incarnation-20261013",
    "native_node_id": "practical-scratch-node-1",
    "candidate_route": "APPROVED_SCRATCH_PRACTICAL_CONTRACT",
}


def lease_selection(**changes):
    value = dict(
        scratch_root='C:/Users/sakth/memory-integrity-practical-fence-20261013/pilot-1',
        dolt_executable='C:/pinned/dolt.exe', dolt_sha256=PIN,
        host='127.0.0.1', port=50001, database='mipx', main_branch='main',
        incarnation='store-1', native_node_id='practical-approved-scratch-only',
        candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT')
    value.update(changes)
    return value


def lease_packet(operation_id='op-lease-1', **changes):
    value = dict(
        schema_version=2, work_item_id='cm-work-17', operation_id=operation_id,
        action='guarded_title_lease', task_id='mip-42', actor='alice',
        title='fenced lease title', expected_status='in_progress',
        grant_id='grant-7', expected_row_lock=731,
        lease_holder='alice', lease_granted_node='practical-approved-scratch-only',
        lease_granted_at_utc='2026-10-14 10:00:00.000000',
        lease_expires_at_utc='2026-10-14 10:05:00.000000',
        lease_heartbeat_at_utc='2026-10-14 10:00:00.000000')
    value.update(changes)
    payload = {key: item for key, item in value.items() if key != 'command_digest'}
    value['command_digest'] = practical_contract.canonical_command_digest(payload)
    return value


def authority_row(selection_digest, **changes):
    # Native DATETIME renders without a suffix; UTC_TIMESTAMP(6) keeps one.
    row = dict(
        issue_id='mip-42', issue_title='before', issue_status='in_progress',
        assignee='alice', issue_row_lock=731, ephemeral=0,
        holder='alice', granted_node='practical-approved-scratch-only',
        granted_at='2026-10-14 10:00:00', lease_expires_at='2026-10-14 10:05:00',
        heartbeat_at='2026-10-14 10:00:00',
        grant_id='grant-7', grant_actor='alice', grant_status='CURRENT',
        fixed_deadline_utc='2026-10-14 10:05:00', issue_revision=731,
        tombstoned=0, lease_node='practical-approved-scratch-only',
        lease_granted_at='2026-10-14 10:00:00', lease_expiry='2026-10-14 10:05:00',
        lease_heartbeat='2026-10-14 10:00:00', current_revision=731,
        selection_digest=selection_digest,
        native_node_id='practical-approved-scratch-only',
        selected_database='mipx', selected_main_branch='main',
        observed_utc='2026-10-14 10:00:01.000000')
    row.update(changes)
    return row


def persisted_row(selection, request, **changes):
    binding = request.as_dict()
    binding.update(selection_digest=selection.digest, store_incarnation=selection.incarnation,
                   database=selection.database, branch='main', native_node_id=selection.native_node_id)
    receipt = dict(binding, status='WORKING_SET_APPLIED',
                   evidence_class='NATIVE_OBSERVED_UNQUALIFIED', native_write_qualified=False,
                   head_committed=False, backend_operation_id=request.operation_id,
                   native_task_id=request.task_id, original_row_lock=request.expected_row_lock,
                   fixed_deadline_utc=request.fixed_deadline_utc,
                   authorization_time_utc='2026-10-14 10:00:01.000000', resulting_row_lock=812)
    receipt.update(changes)
    return dict(binding_json=json.dumps(binding), receipt_json=json.dumps(receipt),
                command_digest=request.command_digest,
                authorization_time=receipt['authorization_time_utc'], resulting_row_lock=812)


def process_result(row):
    return SimpleNamespace(returncode=0, stdout=json.dumps({'rows': [row]}).encode(), stderr=b'')


class LeaseConsumerTests(unittest.TestCase):
    def setUp(self):
        # Keep unique local evidence after a run; this test never deletes it.
        self.temp = Path(tempfile.mkdtemp(prefix="practical-consumer-"))
        self.db = ledger.connect(self.temp / "cm.sqlite")
        ledger.create_work_item(self.db, "cm-work-17", "task", "source")
        ledger.coordination_put(self.db, "cm-work-17", {"registered": True})
        self.backend = practical_backend.PracticalBackend(
            SELECTION, runner=lambda *_args: (_ for _ in ()).throw(AssertionError("no CLI")))
        self.lease_backend = practical_lease_backend.LeaseScratchBackend(lease_selection())
        self.consumer = LeaseNativeConsumer(self.db, self.lease_backend)
        self.calls = []

    def tearDown(self):
        self.db.close()

    def run_backend(self, authority, dispatch=None, readback=None):
        # TEST_ONLY process boundary: fabricated subprocess output proves
        # parsing/binding/refusal logic, never native behavior.
        def run(argv, **kwargs):
            sql = argv[-1]
            self.calls.append(sql)
            if sql.lstrip().upper().startswith('SELECT') and 'observed_utc' in sql:
                payload = {'rows': [authority]}
            elif sql.lstrip().upper().startswith('SELECT'):
                payload = {'rows': [readback] if readback is not None else []}
            else:
                payload = {'rows': [dispatch]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode(), stderr=b'')
        return run

    def patched(self, authority, dispatch=None, readback=None):
        return (patch.object(practical_lease_backend, '_native_boundary'),
                patch.object(practical_lease_backend.subprocess, 'run',
                             side_effect=self.run_backend(authority, dispatch, readback)))

    def kinds(self):
        return [row[0] for row in self.db.execute(
            "SELECT kind FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq")]

    def test_stopped_v1_consumer_constructor_stays_stopped(self):
        # The v1 consumer is deliberately stopped pending the real lease-v2
        # replacement (practical-resume-20261014.md:30): construction refuses
        # before any reader registration, so no injected predecessor runner
        # can register a fabricated native proof path. The gate precedes the
        # concrete-type check, which the refusal below documents.
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError,
                                    "E_PRACTICAL_REVISION_STOPPED"):
            practical_consumer.PracticalNativeConsumer(self.db, self.backend)
        with self.assertRaisesRegex(practical_consumer.PracticalConsumerError,
                                    "E_PRACTICAL_REVISION_STOPPED"):
            practical_consumer.PracticalNativeConsumer(self.db, object())

    def test_dispatch_uses_winner_reservation_then_real_operation_readback(self):
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            result = self.consumer.dispatch_lease_title(lease_packet())
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertTrue(result["inserted"])
        # Authority read, one dispatch batch, one independent readback: three
        # subprocess calls. History shows the backend's honest UNKNOWN marker
        # (effect observed, readback pending) between dispatch consumption and
        # the consumer's APPLIED completion: exactly one dispatch, one APPLIED.
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.kinds(),
                         ["PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_DISPATCHED",
                          "PRACTICAL_NATIVE_UNKNOWN", "PRACTICAL_NATIVE_APPLIED"])
        applied = self.db.execute(
            "SELECT detail FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0]
        self.assertEqual(json.loads(applied)["receipt"]["observed_state"], "WORKING_SET_APPLIED")

    def test_loser_and_recovery_do_readback_only_never_replay_mutation(self):
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            first = self.consumer.dispatch_lease_title(lease_packet())
            calls_after_winner = len(self.calls)
            second = self.consumer.dispatch_lease_title(lease_packet())
            recovered = self.consumer.reconcile_lease_title(lease_packet())
        self.assertTrue(first["inserted"])
        # The loser re-validates currency first (one authority SELECT, the
        # same fail-closed ordering as a winner), then completes the stored
        # readback without dispatch; recovery adds no call at all.
        self.assertFalse(second["inserted"])
        self.assertFalse(recovered["inserted"])
        self.assertEqual(second["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(len(self.calls), calls_after_winner + 1)
        new_sql = self.calls[calls_after_winner:]
        self.assertEqual(len(new_sql), 1)
        self.assertIn("observed_utc", new_sql[0])
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_DISPATCHED"), 1)
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_APPLIED"), 1)

    def test_backend_error_marks_unknown_and_never_retries_dispatch(self):
        auth = authority_row(self.lease_backend.selection.digest)
        def failing(argv, **kwargs):
            sql = argv[-1]
            self.calls.append(sql)
            if sql.lstrip().upper().startswith('SELECT') and 'observed_utc' in sql:
                return SimpleNamespace(returncode=0,
                                        stdout=json.dumps({'rows': [auth]}).encode(), stderr=b'')
            if sql.lstrip().upper().startswith('SELECT'):
                return SimpleNamespace(returncode=0,
                                        stdout=json.dumps({'rows': []}).encode(), stderr=b'')
            return SimpleNamespace(returncode=1, stdout=b'', stderr=b'backend lost')
        boundary = patch.object(practical_lease_backend, '_native_boundary')
        process = patch.object(practical_lease_backend.subprocess, 'run', side_effect=failing)
        with boundary, process:
            result = self.consumer.dispatch_lease_title(lease_packet())
            again = self.consumer.dispatch_lease_title(lease_packet())
        # The backend records the uncertainty itself before the consumer's
        # completion call, so the consumer observes (not inserts) UNKNOWN.
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_UNKNOWN")
        self.assertFalse(result["inserted"])
        self.assertEqual(again["kind"], "PRACTICAL_NATIVE_UNKNOWN")
        self.assertFalse(again["inserted"])
        self.assertEqual(self.kinds(),
                         ["PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_DISPATCHED",
                          "PRACTICAL_NATIVE_UNKNOWN"])
        # Exactly one dispatch batch across both attempts: the uncertain write
        # is never resent; the retry only re-reads.
        dispatch_calls = [sql for sql in self.calls
                          if not sql.lstrip().upper().startswith('SELECT')]
        self.assertEqual(len(dispatch_calls), 1)
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_DISPATCHED"), 1)
        self.assertNotIn("PRACTICAL_NATIVE_APPLIED", self.kinds())

    def test_current_backend_prerequisite_refuses_stale_grant_before_dispatch(self):
        auth = authority_row(self.lease_backend.selection.digest, issue_row_lock=999)
        boundary, process = self.patched(auth)
        with boundary, process:
            with self.assertRaisesRegex(LeaseConsumerError, "E_PRACTICAL_CURRENT_AUTHORITY"):
                self.consumer.dispatch_lease_title(lease_packet())
        # Refusal happens before any intent is reserved: no CM event and only
        # the single authority read reached a subprocess.
        self.assertEqual(self.kinds(), [])
        self.assertEqual(len(self.calls), 1)

    def test_historical_applied_event_cannot_authorize_later_changed_grant(self):
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            first = self.consumer.dispatch_lease_title(lease_packet())
            self.assertTrue(first["inserted"])
            calls_after_winner = len(self.calls)
            # Replaying the identical request completes the same durable
            # readback: no new events, one currency re-validation read.
            same = self.consumer.dispatch_lease_title(lease_packet())
            self.assertEqual(same["kind"], "PRACTICAL_NATIVE_APPLIED")
            self.assertFalse(same["inserted"])
            # Reusing the operation id with a different title rebinds the
            # digest: the reservation boundary refuses before any new SQL
            # beyond the already-passed currency precheck.
            with self.assertRaisesRegex(Exception, "E_PRACTICAL_BINDING"):
                self.consumer.dispatch_lease_title(lease_packet(title="reworded title"))
            recovered = self.consumer.reconcile_lease_title(lease_packet())
        self.assertFalse(recovered["inserted"])
        self.assertEqual(recovered["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_APPLIED"), 1)
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_DISPATCHED"), 1)

    def test_foreign_or_compact_readback_cannot_seal_success(self):
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        forged = persisted_row(self.lease_backend.selection, request, native_task_id='other')
        compact = {'binding_json': '{}'}
        for row in (forged, compact):
            with self.subTest(row=sorted(row)):
                consumer = LeaseNativeConsumer(self.db, practical_lease_backend.LeaseScratchBackend(
                    lease_selection()))
                calls = []
                def run(argv, **kwargs):
                    sql = argv[-1]
                    calls.append(sql)
                    if sql.lstrip().upper().startswith('SELECT') and 'observed_utc' in sql:
                        payload = {'rows': [auth]}
                    elif sql.lstrip().upper().startswith('SELECT'):
                        payload = {'rows': [row]}
                    else:
                        payload = {'rows': [persisted_row(
                            consumer._backend.selection, request)]}
                    return SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode(),
                                            stderr=b'')
                boundary = patch.object(practical_lease_backend, '_native_boundary')
                process = patch.object(practical_lease_backend.subprocess, 'run', side_effect=run)
                operation = 'op-foreign-%d' % len(calls)
                with boundary, process:
                    result = consumer.dispatch_lease_title(lease_packet(operation_id=operation))
                self.assertEqual(result["kind"], "PRACTICAL_NATIVE_UNKNOWN")
                self.assertNotIn("PRACTICAL_NATIVE_APPLIED", self.kinds())

    def test_consumer_subclass_and_method_replacement_cannot_forge_readback(self):
        # The ledger registers the consumer object itself as the protected
        # reader. A subclass overriding the readback callback would turn that
        # registration into fabricated APPLIED proof with zero native calls,
        # so subclass construction must refuse; instance-level replacement
        # must be structurally impossible.
        class ForgedConsumer(LeaseNativeConsumer):
            def read_practical_native_operation(self, binding):
                return dict(binding, observed_state='WORKING_SET_APPLIED')

        with self.assertRaisesRegex(LeaseConsumerError, 'E_PRACTICAL_CONSUMER'):
            ForgedConsumer(self.db, self.lease_backend)
        with self.assertRaises(AttributeError):
            self.consumer.read_practical_native_operation = lambda binding: {}

    def test_grant_lifecycle_status_accepts_only_producer_values(self):
        # Producers write CURRENT (initial claim) or GRANTED (reassign mint).
        # A task status such as in_progress, or any retired lifecycle value,
        # must refuse before any intent is reserved.
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        for status, allowed in (('CURRENT', True), ('GRANTED', True),
                                ('in_progress', False), ('RELEASED', False)):
            with self.subTest(status=status):
                auth = authority_row(self.lease_backend.selection.digest, grant_status=status)
                boundary, process = self.patched(auth)
                with boundary, process:
                    if allowed:
                        self.consumer._current_prerequisite(request)
                    else:
                        with self.assertRaisesRegex(LeaseConsumerError,
                                                    'E_PRACTICAL_CURRENT_AUTHORITY'):
                            self.consumer._current_prerequisite(request)
                self.assertEqual(self.kinds(), [])

    def test_changed_grant_after_applied_refuses_before_new_dispatch(self):
        # The original changed-authority guarantee: after a recorded success,
        # the authority moves on (competing grant) and the same original
        # request must refuse at the prerequisite — no new intent, no mutation.
        request = practical_contract.LeaseGuardedTitleRequest.from_value(lease_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            first = self.consumer.dispatch_lease_title(lease_packet())
            self.assertTrue(first["inserted"])
            calls_after_winner = len(self.calls)
            moved = authority_row(self.lease_backend.selection.digest, issue_row_lock=999,
                                  issue_revision=999, current_revision=999)
            moved_boundary, moved_process = self.patched(moved)
            with moved_boundary, moved_process:
                with self.assertRaisesRegex(LeaseConsumerError,
                                            'E_PRACTICAL_CURRENT_AUTHORITY'):
                    self.consumer.dispatch_lease_title(lease_packet())
        self.assertEqual(len(self.calls), calls_after_winner + 1)
        self.assertIn("observed_utc", self.calls[-1])
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_APPLIED"), 1)
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_DISPATCHED"), 1)

    def test_non_concrete_backend_and_direct_success_payload_fail_closed(self):
        with self.assertRaisesRegex(LeaseConsumerError, "E_PRACTICAL_BACKEND"):
            LeaseNativeConsumer(self.db, object())

        class ShadowedBackend(practical_lease_backend.LeaseScratchBackend):
            pass

        with self.assertRaisesRegex(LeaseConsumerError, "E_PRACTICAL_BACKEND"):
            LeaseNativeConsumer(self.db, ShadowedBackend(lease_selection()))
        with self.assertRaises(LeaseConsumerError):
            self.consumer.dispatch_lease_title({"success": True})


def reassign_persisted_row(selection, request, **changes):
    binding = request.as_dict()
    binding.update(selection_digest=selection.digest, store_incarnation=selection.incarnation,
                   database=selection.database, branch='main', native_node_id=selection.native_node_id)
    receipt = dict(binding, status='WORKING_SET_APPLIED',
                   evidence_class='NATIVE_OBSERVED_UNQUALIFIED', native_write_qualified=False,
                   head_committed=False, backend_operation_id=request.operation_id,
                   native_task_id=request.task_id, original_row_lock=request.expected_row_lock,
                   fixed_deadline_utc=request.fixed_deadline_utc,
                   prior_grant_id=request.grant_id, new_grant_id=request.new_grant_id,
                   target_actor=request.target_actor,
                   authorization_time_utc='2026-10-14 10:00:01.000000', resulting_row_lock=812,
                   resulting_lease_heartbeat_at_utc='2026-10-14 10:00:01.000000')
    receipt.update(changes)
    return dict(binding_json=json.dumps(binding), receipt_json=json.dumps(receipt),
                command_digest=request.command_digest,
                authorization_time=receipt['authorization_time_utc'], resulting_row_lock=812)


def xfer_packet(operation_id='op-xfer-1', **changes):
    # Reassign request aligned with authority_row (mip-42 / row_lock 731 /
    # grant-7): the transferor currency fixtures above. Digest recomputed.
    return reassign_packet(task_id='mip-42', expected_row_lock=731, grant_id='grant-7',
                           work_item_id='cm-work-17', operation_id=operation_id, **changes)


class LeaseReassignConsumerTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="practical-reassign-"))
        self.db = ledger.connect(self.temp / "cm.sqlite")
        ledger.create_work_item(self.db, "cm-work-17", "task", "source")
        ledger.coordination_put(self.db, "cm-work-17", {"registered": True})
        self.lease_backend = practical_lease_backend.LeaseScratchBackend(lease_selection())
        self.consumer = LeaseNativeConsumer(self.db, self.lease_backend)
        self.calls = []

    def tearDown(self):
        self.db.close()

    def patched(self, authority, dispatch=None, readback=None):
        def run(argv, **kwargs):
            sql = argv[-1]
            self.calls.append(sql)
            if sql.lstrip().upper().startswith('SELECT') and 'observed_utc' in sql:
                payload = {'rows': [authority]}
            elif sql.lstrip().upper().startswith('SELECT'):
                payload = {'rows': [readback] if readback is not None else []}
            else:
                payload = {'rows': [dispatch]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload).encode(), stderr=b'')
        return (patch.object(practical_lease_backend, '_native_boundary'),
                patch.object(practical_lease_backend.subprocess, 'run', side_effect=run))

    def kinds(self):
        return [row[0] for row in self.db.execute(
            "SELECT kind FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%' ORDER BY seq")]

    def test_reassign_winner_dispatch_then_real_readback_applies(self):
        request = practical_contract.LeaseReassignRequest.from_value(xfer_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = reassign_persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            result = self.consumer.dispatch_reassign_title(xfer_packet())
        self.assertEqual(result["kind"], "PRACTICAL_NATIVE_APPLIED")
        self.assertTrue(result["inserted"])
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.kinds(),
                         ["PRACTICAL_NATIVE_INTENT", "PRACTICAL_NATIVE_DISPATCHED",
                          "PRACTICAL_NATIVE_UNKNOWN", "PRACTICAL_NATIVE_APPLIED"])
        applied = self.db.execute(
            "SELECT detail FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0]
        detail = json.loads(applied)
        self.assertEqual(detail["binding"]["new_grant_id"], 'grant-2')
        self.assertEqual(detail["binding"]["target_actor"], 'bob')

    def test_reassign_stale_transferor_refuses_before_reservation(self):
        auth = authority_row(self.lease_backend.selection.digest, issue_row_lock=999)
        boundary, process = self.patched(auth)
        with boundary, process:
            with self.assertRaisesRegex(LeaseConsumerError, "E_PRACTICAL_CURRENT_AUTHORITY"):
                self.consumer.dispatch_reassign_title(xfer_packet())
        self.assertEqual(self.kinds(), [])
        self.assertEqual(len(self.calls), 1)

    def test_reassign_wrong_resulting_heartbeat_refuses_despite_bounds(self):
        # Reported probe: authorization 10:00:01 with resulting heartbeat
        # 10:00:00 sits inside granted<=heartbeat<=auth, yet it is not the
        # transfer-time value the builder writes. It must yield UNKNOWN with
        # zero APPLIED. Companion cases: invalid precision, missing heartbeat.
        # Each row is built from its own dispatch packet so only the heartbeat
        # under test differs; anything else refusing would hide the defect.
        auth = authority_row(self.lease_backend.selection.digest)
        cases = {
            'one-second-wrong': '2026-10-14 10:00:00.000000',
            'nonzero-microsecond': '2026-10-14 10:00:01.000001',
            'suffix-less': '2026-10-14 10:00:01',
        }
        for name, heartbeat in cases.items():
            with self.subTest(case=name):
                operation = 'op-heartbeat-' + name
                request = practical_contract.LeaseReassignRequest.from_value(
                    xfer_packet(operation_id=operation))
                row = reassign_persisted_row(self.lease_backend.selection, request)
                receipt = json.loads(row['receipt_json'])
                receipt['resulting_lease_heartbeat_at_utc'] = heartbeat
                row['receipt_json'] = json.dumps(receipt)
                consumer = LeaseNativeConsumer(self.db, practical_lease_backend.LeaseScratchBackend(
                    lease_selection()))
                boundary, process = self.patched(auth, dispatch=row, readback=row)
                with boundary, process:
                    result = consumer.dispatch_reassign_title(xfer_packet(operation_id=operation))
                self.assertEqual(result['kind'], 'PRACTICAL_NATIVE_UNKNOWN')
        operation = 'op-heartbeat-missing'
        request = practical_contract.LeaseReassignRequest.from_value(
            xfer_packet(operation_id=operation))
        missing = reassign_persisted_row(self.lease_backend.selection, request)
        receipt = json.loads(missing['receipt_json'])
        del receipt['resulting_lease_heartbeat_at_utc']
        missing['receipt_json'] = json.dumps(receipt)
        consumer = LeaseNativeConsumer(self.db, practical_lease_backend.LeaseScratchBackend(
            lease_selection()))
        boundary, process = self.patched(auth, dispatch=missing, readback=missing)
        with boundary, process:
            result = consumer.dispatch_reassign_title(xfer_packet(operation_id=operation))
        self.assertEqual(result['kind'], 'PRACTICAL_NATIVE_UNKNOWN')
        self.assertNotIn('PRACTICAL_NATIVE_APPLIED', self.kinds())

    def test_bounds_only_check_would_accept_the_probe(self):
        # Non-vacuity proof for the regression above: the previous
        # bounds-only rule accepts the exact probe row, so that test
        # distinguishes the old check from the repaired validator.
        from datetime import datetime as _dt
        granted = _dt(2026, 10, 14, 10, 0, 0)
        auth = _dt(2026, 10, 14, 10, 0, 1)
        transferred = _dt(2026, 10, 14, 10, 0, 0)
        self.assertTrue(granted <= transferred <= auth)
        self.assertNotEqual(transferred, auth.replace(microsecond=0))

    def test_reassign_expired_lease_and_exact_deadline_refuse_before_reservation(self):
        # DB clock at or past the original expiry refuses even with an
        # otherwise current transferor snapshot; nothing is reserved.
        for observed in ('2026-10-14 10:05:00.000000', '2026-10-14 10:06:00.000000'):
            with self.subTest(observed=observed):
                auth = authority_row(self.lease_backend.selection.digest, observed_utc=observed)
                boundary, process = self.patched(auth)
                with boundary, process:
                    with self.assertRaisesRegex(LeaseConsumerError,
                                                'E_PRACTICAL_CURRENT_AUTHORITY'):
                        self.consumer.dispatch_reassign_title(xfer_packet())
        self.assertEqual(self.kinds(), [])

    def test_reassign_recovery_reads_only_and_rebind_refuses(self):
        request = practical_contract.LeaseReassignRequest.from_value(xfer_packet())
        auth = authority_row(self.lease_backend.selection.digest)
        receipt = reassign_persisted_row(self.lease_backend.selection, request)
        boundary, process = self.patched(auth, dispatch=receipt, readback=receipt)
        with boundary, process:
            first = self.consumer.dispatch_reassign_title(xfer_packet())
            self.assertTrue(first["inserted"])
            recovered = self.consumer.reconcile_lease_title(xfer_packet())
            self.assertEqual(recovered["kind"], "PRACTICAL_NATIVE_APPLIED")
            self.assertFalse(recovered["inserted"])
            with self.assertRaisesRegex(Exception, "E_PRACTICAL_BINDING"):
                self.consumer.dispatch_reassign_title(xfer_packet(title="renamed twice"))
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_DISPATCHED"), 1)
        self.assertEqual(self.kinds().count("PRACTICAL_NATIVE_APPLIED"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
