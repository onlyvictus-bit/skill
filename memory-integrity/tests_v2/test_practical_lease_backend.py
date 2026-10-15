"""Real request/journal/transport parsing with a TEST_ONLY process boundary.

These tests do not execute Dolt or prove its transactional/crash behavior.
No injected runner or receipt is accepted by the public backend constructor.
"""
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude-mon/scripts'))
from complete_read_v2 import ledger
from hybrid_bridge.practical_contract import LeasePracticalSelection, LeaseGuardedTitleRequest
from tests_v2.test_practical_lease_contract import packet

PIN = 'ca21a9d1dab233a694b99ad0be9e78590967a1cc2773eb202fa0dd2929239ba2'


def selected():
    return LeasePracticalSelection(
        scratch_root='C:/Users/sakth/memory-integrity-practical-fence-20261013/pilot-1',
        dolt_executable='C:/pinned/dolt.exe', dolt_sha256=PIN,
        host='127.0.0.1', port=50001, database='mipx', main_branch='main',
        incarnation='store-1', native_node_id='practical-approved-scratch-only',
        candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT')


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
    return SimpleNamespace(returncode=0, stdout=json.dumps({'rows':[row]}).encode(), stderr=b'')


class LeaseBackend(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT/'scripts/hybrid_bridge/practical_lease_backend.py').is_file(),
                        'sealed lease-bound successor backend is missing')
        self.mod = importlib.import_module('hybrid_bridge.practical_lease_backend')
        self.selection = selected()
        self.request = LeaseGuardedTitleRequest.from_value(packet())
        self.db = ledger.connect(':memory:')
        ledger.create_work_item(self.db, self.request.work_item_id, 'task', 'source')
        ledger.coordination_put(self.db, self.request.work_item_id, {'registered':True})
        self.backend = self.mod.LeaseScratchBackend(self.selection)

    def tearDown(self):
        if hasattr(self, 'db'):
            self.db.close()

    def winner(self):
        binding = self.backend.intent_binding(self.request)
        return binding, ledger.reserve_practical_native_intent(self.db, binding)['reservation']

    def test_public_constructor_rejects_injected_runner(self):
        with self.assertRaises(TypeError):
            self.mod.LeaseScratchBackend(self.selection, runner=lambda *_:None)

    def test_backend_cannot_be_shadowed_or_promoted(self):
        with self.assertRaises((AttributeError, TypeError)):
            self.backend.read_operation = lambda *_:{'status':'WORKING_SET_APPLIED'}
        self.assertFalse(self.backend.native_write_qualified)
        self.assertFalse(self.backend.activate(native_write_qualified=True))

    def test_unpinned_binary_or_beads_filename_refuses(self):
        value = dict(self.selection.__dict__, dolt_sha256='a'*64)
        with self.assertRaisesRegex(ValueError, 'PIN'):
            self.mod.LeaseScratchBackend(value)
        value = dict(self.selection.__dict__, dolt_executable='C:/pinned/bd.exe')
        with self.assertRaisesRegex(ValueError, 'DOLT'):
            self.mod.LeaseScratchBackend(value)

    def test_binding_records_every_original_real_lease_fact(self):
        binding = self.backend.intent_binding(self.request)
        for key in ('lease_holder','lease_granted_node','lease_granted_at_utc',
                    'lease_expires_at_utc','lease_heartbeat_at_utc'):
            self.assertEqual(binding[key], getattr(self.request,key))
        self.assertEqual(binding['fixed_deadline'], self.request.fixed_deadline_utc)

    def test_missing_reservation_causes_zero_native_calls(self):
        with patch.object(self.mod.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'OWNER'):
                self.backend.execute_guarded_title(self.request, cm_db=self.db, reservation=object())
        process.assert_not_called()

    def test_native_boundary_refusal_does_not_consume_dispatch(self):
        binding, cap = self.winner()
        before = self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        with patch.object(self.mod, '_native_boundary', side_effect=ValueError('E_PATH')):
            with self.assertRaisesRegex(ValueError, 'E_PATH'):
                self.backend.execute_guarded_title(self.request, cm_db=self.db, reservation=cap)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before)

    def test_exact_receipt_one_dispatch_is_not_native_qualification(self):
        binding, cap = self.winner()
        result = process_result(persisted_row(self.selection,self.request))
        with patch.object(self.mod, '_native_boundary'), patch.object(self.mod.subprocess,'run',return_value=result) as process:
            out = self.backend.execute_guarded_title(self.request, cm_db=self.db, reservation=cap)
        self.assertEqual(process.call_count,1)
        argv = process.call_args.args[0]
        self.assertEqual(argv[0],self.selection.dolt_executable)
        self.assertIn('COMMIT;',argv[-1])
        self.assertFalse(process.call_args.kwargs['shell'])
        self.assertFalse(out['native_write_qualified'])
        self.assertFalse(out['head_committed'])
        kinds=[r[0] for r in self.db.execute("SELECT kind FROM events WHERE kind LIKE 'PRACTICAL_NATIVE_%'")]
        self.assertEqual(kinds,['PRACTICAL_NATIVE_INTENT','PRACTICAL_NATIVE_DISPATCHED','PRACTICAL_NATIVE_UNKNOWN'])
        self.assertEqual(ledger.verify_history(self.db)['internal_chain'],'VERIFIED')

    def test_new_backend_and_reused_capability_cannot_repeat_mutation(self):
        binding, cap = self.winner()
        result = process_result(persisted_row(self.selection,self.request))
        with patch.object(self.mod, '_native_boundary'), patch.object(self.mod.subprocess,'run',return_value=result) as process:
            self.backend.execute_guarded_title(self.request, cm_db=self.db, reservation=cap)
            other=self.mod.LeaseScratchBackend(self.selection)
            with self.assertRaisesRegex(ValueError,'READBACK_ONLY'):
                other.execute_guarded_title(self.request,cm_db=self.db,reservation=cap)
        self.assertEqual(process.call_count,1)

    def test_foreign_receipt_becomes_unknown_never_applied(self):
        binding, cap = self.winner()
        forged=process_result(persisted_row(self.selection,self.request,native_task_id='other'))
        with patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=forged):
            with self.assertRaises(self.mod.LeaseDeliveryUnknown):
                self.backend.execute_guarded_title(self.request,cm_db=self.db,reservation=cap)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0],0)

    def test_duplicate_json_keys_and_stderr_refuse(self):
        for result in (SimpleNamespace(returncode=0,stdout=b'{"rows":[],"rows":[]}',stderr=b''),
                       SimpleNamespace(returncode=0,stdout=b'{"rows":[]}',stderr=b'warning')):
            with self.subTest(result=result),patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=result):
                with self.assertRaises(self.mod.LeaseDeliveryUnknown):
                    self.backend.read_operation(self.request)

    def test_readback_has_no_mutation_and_missing_is_unknown(self):
        result=SimpleNamespace(returncode=0,stdout=b'{"rows":[]}',stderr=b'')
        with patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=result) as process:
            self.assertIsNone(self.backend.read_operation(self.request))
        sql=process.call_args.args[0][-1]
        self.assertIn('mi_practical_v2_operations',sql)
        self.assertNotIn('UPDATE ',sql)
        self.assertNotIn('INSERT ',sql)

    def test_partial_or_late_authorization_receipt_is_not_success(self):
        for row in ({'receipt_json':'{}'},persisted_row(self.selection,self.request,
                       authorization_time_utc=self.request.fixed_deadline_utc)):
            with self.subTest(row=row),patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=process_result(row)):
                with self.assertRaises(self.mod.LeaseDeliveryUnknown):
                    self.backend.read_operation(self.request)

    def test_float_in_binding_is_not_integer_identity(self):
        row=persisted_row(self.selection,self.request)
        binding=json.loads(row['binding_json'])
        binding['expected_row_lock']=float(self.request.expected_row_lock)
        row['binding_json']=json.dumps(binding)
        with patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=process_result(row)):
            with self.assertRaises(self.mod.LeaseDeliveryUnknown):
                self.backend.read_operation(self.request)

    def test_boolean_binding_cannot_equal_numeric_revision(self):
        req=LeaseGuardedTitleRequest.from_value(packet(expected_row_lock=1))
        row=persisted_row(self.selection,req)
        binding=json.loads(row['binding_json'])
        binding['expected_row_lock']=True
        row['binding_json']=json.dumps(binding)
        with patch.object(self.mod,'_native_boundary'),patch.object(self.mod.subprocess,'run',return_value=process_result(row)):
            with self.assertRaises(self.mod.LeaseDeliveryUnknown):
                self.backend.read_operation(req)


    def test_current_authority_read_is_select_only_and_exact(self):
        row = dict(issue_id='mipx-1', issue_title='t', issue_status='in_progress',
                   assignee='alice', issue_row_lock=-7, ephemeral=0,
                   holder='alice', granted_node='practical-approved-scratch-only',
                   granted_at='2026-10-14 10:00:00', lease_expires_at='2026-10-14 10:05:00',
                   heartbeat_at='2026-10-14 10:00:00', grant_id='grant-1', grant_actor='alice',
                   grant_status='CURRENT', fixed_deadline_utc='2026-10-14 10:05:00',
                   issue_revision=-7, tombstoned=0, lease_node='practical-approved-scratch-only',
                   lease_granted_at='2026-10-14 10:00:00', lease_expiry='2026-10-14 10:05:00',
                   lease_heartbeat='2026-10-14 10:00:00', current_revision=-7,
                   selection_digest=self.selection.digest,
                   native_node_id='practical-approved-scratch-only',
                   selected_database='mipx', selected_main_branch='main',
                   observed_utc='2026-10-14 10:00:01.000000')
        result = process_result(row)
        with patch.object(self.mod, '_native_boundary'), patch.object(
                self.mod.subprocess, 'run', return_value=result) as process:
            self.assertEqual(self.backend.read_current_authority(self.request), row)
        sql = process.call_args.args[0][-1]
        self.assertTrue(sql.lstrip().upper().startswith('SELECT'))
        for forbidden in ('UPDATE ', 'INSERT ', 'DELETE ', 'COMMIT;', 'DOLT_'):
            self.assertNotIn(forbidden, sql)
        self.assertIn('observed_utc', sql)


if __name__=='__main__':
    unittest.main(verbosity=2)
