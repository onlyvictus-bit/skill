"""TEST_ONLY transport diagnostics; real CM history, no native DB or cleanup.

Only the physical-host and subprocess boundaries are mocked. Diagnostics are
observations, not authorization, success receipts or native fence proof.
"""
import base64
import copy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT.parent/'claude-mon/scripts'))
from complete_read_v2 import ledger
from hybrid_bridge import practical_lease_backend as backend_module
from hybrid_bridge import practical_lease_sql
from hybrid_bridge.practical_contract import LeaseGuardedTitleRequest, strict_canonical_json
from tests_v2.test_practical_lease_backend import selected
from tests_v2.test_practical_lease_contract import packet


class ExecutionDiagnostics(unittest.TestCase):
    def setUp(self):
        self.db=ledger.connect(':memory:')
        self.request=LeaseGuardedTitleRequest.from_value(packet())
        self.backend=backend_module.LeaseScratchBackend(selected())
        self.binding=self.backend.intent_binding(self.request)
        ledger.create_work_item(self.db,self.request.work_item_id,'task','source')
        ledger.coordination_put(self.db,self.request.work_item_id,{'registered':True})
        self.cap=ledger.reserve_practical_native_intent(self.db,self.binding)['reservation']
        self.sql=practical_lease_sql.guarded_title_sql(selected(),self.request)

    def tearDown(self):
        self.db.close()

    def module(self):
        self.assertTrue((ROOT/'scripts/hybrid_bridge/practical_execution.py').is_file(),
                        'operation-bound execution diagnostics reader is missing')
        return importlib.import_module('hybrid_bridge.practical_execution')

    def fail_process(self, result=None, error=None):
        result=result or SimpleNamespace(returncode=17,stdout=b'\x00\xffnative-output',
            stderr=b'ERROR: E_MI2_AUTH mentioned by an unrelated failure\x80')
        with patch.object(backend_module,'_native_boundary'),patch.object(
                backend_module.subprocess,'run',return_value=result,side_effect=error) as process:
            with self.assertRaises(backend_module.LeaseDeliveryUnknown):
                self.backend.execute_guarded_title(self.request,cm_db=self.db,reservation=self.cap)
        self.assertEqual(process.call_count,1)
        row=self.db.execute("SELECT * FROM events WHERE kind='PRACTICAL_NATIVE_UNKNOWN'").fetchone()
        reason=json.loads(row['detail'])['reason']
        self.assertTrue(reason.startswith('{'),
                        'durable UNKNOWN discarded original execution diagnostics: '+reason)
        return json.loads(reason)

    def read(self):
        return self.module().read_execution_diagnostics(self.db,self.binding,
            expected_sql_sha256=sha256(self.sql.encode()).hexdigest())

    def test_raw_non_utf8_failure_survives_in_original_unknown_event(self):
        observed=self.fail_process()
        self.assertEqual(observed['binding'],self.binding)
        capture=observed['transport']
        self.assertEqual(capture['outcome'],'PROCESS_RESULT')
        self.assertEqual(capture['returncode'],17)
        self.assertEqual(base64.b64decode(capture['stdout']['base64']),b'\x00\xffnative-output')
        self.assertEqual(capture['sql_sha256'],sha256(self.sql.encode()).hexdigest())
        self.assertEqual(capture['selection_digest'],selected().digest)
        self.assertNotIn('fence',observed.get('refusal',{}))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0],0)

    def test_partial_timeout_output_is_retained_not_engine_rejection(self):
        observed=self.fail_process(error=subprocess.TimeoutExpired('not-retained-command',15,
            output=b'partial-before-timeout',stderr=b'partial-error'))
        capture=observed['transport']
        self.assertEqual(capture['outcome'],'TIMEOUT')
        self.assertIsNone(capture['returncode'])
        self.assertEqual(base64.b64decode(capture['stdout']['base64']),b'partial-before-timeout')
        self.assertEqual(capture['exception_type'],'TimeoutExpired')
        self.assertNotIn('not-retained-command',json.dumps(observed))

    def test_spawn_error_has_explicitly_missing_output_without_exception_message(self):
        observed=self.fail_process(error=OSError('SECRET_SENTINEL_NOT_A_REAL_KEY'))
        self.assertEqual(observed['transport']['outcome'],'SPAWN_ERROR')
        self.assertFalse(observed['transport']['stdout']['available'])
        self.assertNotIn('SECRET_SENTINEL',json.dumps(observed))

    def test_reader_is_read_only_exact_and_never_classifies_as_fence_proof(self):
        self.fail_process()
        before=self.db.total_changes
        out=self.read()
        self.assertTrue(out['available'],out)
        self.assertEqual(out['causal_status'],'UNVERIFIED')
        self.assertEqual(out['evidence_class'],'TRANSPORT_DIAGNOSTICS_ONLY')
        self.assertEqual(self.db.total_changes,before)
        self.assertEqual(out['observation']['transport']['returncode'],17)
        self.assertEqual(ledger.verify_history(self.db)['internal_chain'],'VERIFIED')

    def test_capture_truncation_is_explicit_and_cannot_claim_complete_bytes(self):
        mod=self.module()
        raw=b'x'*(mod.MAX_CHANNEL_BYTES+19)
        self.fail_process(result=SimpleNamespace(returncode=2,stdout=raw,stderr=b'error'))
        out=self.read()
        capture=out['observation']['transport']['stdout']
        self.assertTrue(capture['truncated'])
        self.assertEqual(capture['observed_bytes'],len(raw))
        self.assertEqual(len(base64.b64decode(capture['base64'])),mod.MAX_CHANNEL_BYTES)
        self.assertEqual(capture['sha256'],sha256(raw).hexdigest())
        self.assertFalse(out['capture_complete'])
        self.assertEqual(out['causal_status'],'UNVERIFIED')

    def test_foreign_binding_and_wrong_sql_hash_are_unavailable_not_success(self):
        self.fail_process()
        mod=self.module()
        for binding,sql_hash in ((dict(self.binding,grant_id='foreign'),sha256(self.sql.encode()).hexdigest()),
                                 (self.binding,'a'*64)):
            out=mod.read_execution_diagnostics(self.db,binding,expected_sql_sha256=sql_hash)
            self.assertFalse(out['available'],out)
            self.assertEqual(out['causal_status'],'UNVERIFIED')

    def test_payload_corruption_and_caller_created_cause_cannot_be_diagnostics_proof(self):
        observed=self.fail_process()
        mod=self.module()
        for change in ('bytes','hash','bool','cause'):
            candidate=copy.deepcopy(observed)
            if change=='bytes': candidate['transport']['stdout']['base64']='!invalid!'
            elif change=='hash': candidate['transport_sha256']='0'*64
            elif change=='bool': candidate['transport']['returncode']=True
            else: candidate['refusal']={'by':'fence','code':'CALLER_CREATED_CAUSE'}
            if change in ('bytes','bool'):
                candidate['transport_sha256']=sha256(strict_canonical_json(candidate['transport'])).hexdigest()
            with self.subTest(change=change),self.assertRaises(ValueError):
                mod.validate_observation(candidate,self.binding,
                    expected_sql_sha256=sha256(self.sql.encode()).hexdigest())

    def test_consumed_operation_never_replays_to_improve_diagnostics(self):
        self.fail_process()
        before=self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        with patch.object(backend_module,'_native_boundary'),patch.object(backend_module.subprocess,'run') as process:
            with self.assertRaisesRegex(ValueError,'READBACK_ONLY'):
                self.backend.execute_guarded_title(self.request,cm_db=self.db,reservation=self.cap)
        process.assert_not_called()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],before)

    def test_missing_exit_status_is_not_complete_capture(self):
        self.fail_process(result=SimpleNamespace(returncode=True,stdout=b'',stderr=b'failed'))
        self.assertFalse(self.read()['capture_complete'])

    def test_valid_json_but_foreign_receipt_retains_original_bytes(self):
        self.fail_process(result=SimpleNamespace(returncode=0,stdout=b'{"rows":[{"foreign":true}]}',stderr=b''))
        out=self.read()
        self.assertTrue(out['available'],out)
        self.assertEqual(base64.b64decode(out['observation']['transport']['stdout']['base64']),
                         b'{"rows":[{"foreign":true}]}')

    def test_controller_reads_journal_not_worker_supplied_execution_cause(self):
        self.fail_process()
        from hybrid_bridge import practical_race_controller as controller
        driver=object.__new__(controller._LiveDriver)
        driver._cm_db=self.db
        driver.alice_request=self.request
        driver.schedule={'requests':{'selection':dict(selected().__dict__)},'pause_seconds':20}
        driver.schedule['phases']={'alice_arm':{'batch':self.sql}}
        method=getattr(driver,'execution_diagnostics',None)
        self.assertTrue(callable(method),'controller has no independent CM diagnostics reader')
        out=method()
        self.assertTrue(out['available'],out)
        self.assertEqual(out['causal_status'],'UNVERIFIED')

    def test_source_manifest_binds_diagnostic_module(self):
        from hybrid_bridge import practical_race_controller as controller
        manifest,_=controller._source_manifest()
        self.assertIn('practical_execution.py',manifest)
        self.assertEqual(manifest['practical_execution.py'],sha256(
            (ROOT/'scripts/hybrid_bridge/practical_execution.py').read_bytes()).hexdigest())

    def test_consumer_unknown_keeps_diagnostics_despite_swallowed_exception(self):
        from hybrid_bridge.practical_lease_consumer import LeaseNativeConsumer
        from tests_v2.test_practical_consumer import authority_row
        self.request=LeaseGuardedTitleRequest.from_value(packet(operation_id='op-consumer'))
        self.binding=self.backend.intent_binding(self.request)
        self.sql=practical_lease_sql.guarded_title_sql(selected(),self.request)
        authority=authority_row(selected().digest,issue_id=self.request.task_id,
            issue_row_lock=-7,issue_revision=-7,current_revision=-7,grant_id=self.request.grant_id)
        def process(argv,**kwargs):
            if argv[-1].startswith('SELECT'):
                rows=[authority] if 'observed_utc' in argv[-1] else []
                return SimpleNamespace(returncode=0,stdout=json.dumps({'rows':rows}).encode(),stderr=b'')
            return SimpleNamespace(returncode=9,stdout=b'original-output',stderr=b'original-error')
        consumer=LeaseNativeConsumer(self.db,self.backend)
        with patch.object(backend_module,'_native_boundary'),patch.object(backend_module.subprocess,'run',side_effect=process):
            result=consumer.dispatch_lease_title(self.request)
        self.assertEqual(result['kind'],'PRACTICAL_NATIVE_UNKNOWN')
        out=self.read()
        self.assertTrue(out['available'],out)
        self.assertEqual(base64.b64decode(out['observation']['transport']['stderr']['base64']),b'original-error')

    def test_reopened_read_only_connection_preserves_exact_event_without_replay(self):
        self.fail_process()
        retained=ROOT.parent.parent/'build-validation/retained-temp'
        root=Path(tempfile.mkdtemp(prefix='execution-reopen-',dir=retained))
        path=root/'cm.sqlite'
        copy_db=sqlite3.connect(path)
        try:
            self.db.backup(copy_db)
        finally:
            copy_db.close()
        reopened=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
        reopened.row_factory=sqlite3.Row
        try:
            before=reopened.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            out=self.module().read_execution_diagnostics(reopened,self.binding,
                expected_sql_sha256=sha256(self.sql.encode()).hexdigest())
            self.assertTrue(out['available'],out)
            self.assertEqual(reopened.execute('SELECT COUNT(*) FROM events').fetchone()[0],before)
            self.assertEqual(reopened.total_changes,0)
        finally:
            reopened.close()

    def test_real_worker_and_controller_keep_diagnostics_but_no_false_causation(self):
        from tests_v2.test_practical_race_offline_sequence import FullSequenceOfflineTests
        probe=FullSequenceOfflineTests('test_missing_execution_cause_remains_inconclusive_at_canonical_verifier')
        self.addCleanup(probe.doCleanups)
        result,evidence,model,driver=probe._run('unrelated_transport_failure')
        observed=evidence['alice']['execution_diagnostics']
        self.assertTrue(observed['available'],observed)
        self.assertEqual(observed['observation']['binding']['operation_id'],driver.alice_request.operation_id)
        # The existing stateful model returns exit=1 plus stderr; it does not
        # raise a spawn exception. Preserve that exact boundary observation.
        self.assertEqual(observed['observation']['transport']['outcome'],'PROCESS_RESULT')
        self.assertEqual(observed['observation']['transport']['returncode'],1)
        self.assertEqual(base64.b64decode(observed['observation']['transport']['stderr']['base64']),
                         b'E_UNRELATED_TRANSPORT_FAILURE')
        self.assertEqual(observed['causal_status'],'UNVERIFIED')
        self.assertEqual(evidence['refusal'],{'by':None,'code':'E_HARNESS_EXECUTION_CAUSE_UNPROVEN'})
        self.assertEqual(result['verdict'],'INCONCLUSIVE')
        self.assertEqual({row['code'] for row in result['reasons']},{'REFUSAL_UNKNOWN'})

    def test_closed_journal_is_unavailable_not_success_or_reader_crash(self):
        self.fail_process()
        mod=self.module()
        self.db.close()
        try:
            out=mod.read_execution_diagnostics(self.db,self.binding,
                expected_sql_sha256=sha256(self.sql.encode()).hexdigest())
        except sqlite3.Error as exc:
            self.fail('unreadable diagnostics must stay unavailable: '+type(exc).__name__)
        self.assertFalse(out['available'])
        self.assertEqual(out['causal_status'],'UNVERIFIED')

    def caller_packet(self, *, legacy=False, changed_identity=False):
        """Supported CM APIs only; no native process or backend invocation."""
        mod=self.module()
        capture=mod.capture_transport(selected(),self.sql,['caller-chosen-argv'],15,
            result=SimpleNamespace(returncode=23,stdout=b'caller-output',stderr=b'caller-error'))
        if legacy:
            capture['source']='SEALED_DOLT_CLIENT'
        if changed_identity:
            capture.update(port=65535,executable='C:/caller/dolt.exe',timeout_seconds=44,
                           command_sha256='a'*64)
        reason=mod.diagnostic_reason(self.binding,selected(),self.sql,
            backend_module.LeaseDeliveryUnknown('caller',transport_observation=capture))
        ledger.consume_practical_native_dispatch(self.db,self.binding,self.cap)
        ledger.mark_practical_native_unknown(self.db,self.cap,reason)
        return self.read()

    def assert_unauthenticated(self,out):
        self.assertEqual(out.get('provenance_status'),'UNAUTHENTICATED')
        self.assertIs(out.get('producer_authenticated'),False)
        self.assertIs(out.get('invocation_identity_verified'),False)
        self.assertEqual(out['causal_status'],'UNVERIFIED')
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM events WHERE kind='PRACTICAL_NATIVE_APPLIED'").fetchone()[0],0)

    def test_valid_public_api_forgery_is_explicitly_unauthenticated_not_sealed_proof(self):
        out=self.caller_packet()
        self.assertTrue(out['available'])
        self.assertTrue(out['capture_complete'])
        self.assertEqual(base64.b64decode(out['observation']['transport']['stdout']['base64']),b'caller-output')
        self.assert_unauthenticated(out)

    def test_rehashed_claimed_invocation_is_never_independently_verified(self):
        out=self.caller_packet(changed_identity=True)
        self.assertTrue(out['available'])
        self.assertEqual(out['observation']['transport']['command_sha256'],'a'*64)
        self.assert_unauthenticated(out)

    def test_legacy_sealed_label_is_retained_but_never_authenticates_producer(self):
        out=self.caller_packet(legacy=True)
        self.assertTrue(out['available'])
        self.assertEqual(out['observation']['transport']['source'],'SEALED_DOLT_CLIENT')
        before=self.db.total_changes
        self.assert_unauthenticated(out)
        self.assertEqual(self.db.total_changes,before)

    def test_current_capture_uses_declared_source_and_never_implies_authentication(self):
        self.fail_process()
        out=self.read()
        self.assertEqual(out['observation']['transport']['source'],'DECLARED_DOLT_CLIENT')
        self.assert_unauthenticated(out)

    def test_controller_missing_journal_still_reports_unverified_provenance(self):
        from hybrid_bridge import practical_race_controller as controller
        driver=object.__new__(controller._LiveDriver)
        out=driver.execution_diagnostics()
        self.assertFalse(out['available'])
        self.assert_unauthenticated(out)


if __name__=='__main__':
    unittest.main(verbosity=2)
