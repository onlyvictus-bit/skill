"""Offline profile refuses native effects before transport or authority use."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hybrid_bridge import native, native_observation, native_pilot, shared_native_pilot
from hybrid_bridge.practical_lease_backend import LeaseScratchBackend


class OfflineReleaseProfile(unittest.TestCase):
    def profile(self):
        self.assertIsNotNone(importlib.util.find_spec('hybrid_bridge.release_profile'),
                             'offline release enforcement not implemented')
        from hybrid_bridge import release_profile
        return release_profile

    def test_active_profile_refuses_native_authority(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            self.profile().require_native_execution_enabled()

    def test_missing_profile_cannot_use_historical_qualification(self):
        profile = self.profile()
        with patch.object(Path, 'read_text', return_value=json.dumps({
                'native_shared_claim_protocol_qualified': True})):
            with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_INVALID'):
                profile.require_native_execution_enabled()

    def test_flag_edit_cannot_enable_native_operations(self):
        profile = self.profile()
        doc = {'active_release_profile': {'id': 'offline-first-v1',
               'native_subprocesses_enabled': True, 'native_mutations_enabled': False,
               'live_provider_enabled': False}}
        with patch.object(Path, 'read_text', return_value=json.dumps(doc)):
            with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_INVALID'):
                profile.require_native_execution_enabled()

    def test_duplicate_profile_json_refused(self):
        profile = self.profile()
        with patch.object(Path, 'read_text', return_value='{"active_release_profile":{},"active_release_profile":{}}'):
            with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_INVALID'):
                profile.require_native_execution_enabled()

    def test_shared_claim_and_readback_never_call_transport(self):
        adapter = object.__new__(native.SharedNativeClaimAdapter)
        adapter.operation_id, adapter.native_task_id, adapter.actor = 'op', 'task', 'owner'
        calls = []
        def forbidden(*args, **kwargs):
            calls.append(True)
            raise ValueError('TEST_TRANSPORT_REACHED')
        command = {'kind': 'claim', 'native_task_id': 'task', 'actor': 'owner'}
        with patch.object(adapter, '_run', side_effect=forbidden):
            for action in (lambda: adapter.execute('op', command), lambda: adapter.readback(command)):
                with self.subTest(action=action):
                    with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                        action()
        self.assertEqual(calls, [])

    def test_observation_refuses_before_selection(self):
        calls = []
        def forbidden(*args, **kwargs):
            calls.append(True)
            raise ValueError('TEST_SELECTION_REACHED')
        with patch.object(native_observation, '_selection', side_effect=forbidden):
            with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                native_observation.observe(object())
        self.assertEqual(calls, [])

    def test_lease_transport_refuses_before_boundary(self):
        backend = object.__new__(LeaseScratchBackend)
        # Deliberately no selection: correct profile refusal precedes its access.
        try:
            backend._invoke('SELECT 1')
        except ValueError as exc:
            self.assertRegex(str(exc), 'E_RELEASE_PROFILE_NATIVE_DISABLED')
        except AttributeError as exc:
            self.fail('native boundary reached before profile refusal: ' + str(exc))
        else:
            self.fail('native transport was allowed')

    def test_pilots_refuse_before_initialization(self):
        for fn, extra in ((native_pilot.run_disposable_pilot, {}),
                          (shared_native_pilot.run_shared_claim_protocol_pilot,
                           {'coordination_module': None, 'artifacts_module': None})):
            with self.subTest(pilot=fn.__name__):
                with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                    fn(bd_path=ROOT/'absent.exe', expected_executable_sha256='a'*64,
                       workspace=ROOT/'DO-NOT-CREATE', receipt=ROOT/'DO-NOT-WRITE.json',
                       ledger_module=None, **extra)
        self.assertFalse((ROOT/'DO-NOT-CREATE').exists())
        self.assertFalse((ROOT/'DO-NOT-WRITE.json').exists())

    def test_fixture_remains_test_only(self):
        adapter = native.FixtureBeadsAdapter({'branch': 'main', 'head': 'fixture-head'})
        snapshot = adapter.read_snapshot()
        self.assertFalse(snapshot['native'])
        self.assertEqual(snapshot['evidence_class'], 'TEST_ONLY')

    def test_race_confirmation_cannot_construct_live_driver(self):
        from hybrid_bridge import practical_race_controller as race
        with patch.object(race, '_LiveDriver', side_effect=AssertionError('live driver reached')) as driver:
            with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                race.run_schedule({}, confirm_native_execution=True)
        driver.assert_not_called()

    def test_direct_race_transport_refuses_before_resources(self):
        from hybrid_bridge import practical_race_controller as race
        driver = object.__new__(race._LiveDriver)
        for name, args in [('preflight', ()), ('start_server', ()),
                           ('start_alice', ('unused SQL',)), ('_invoke', ([],))]:
            with self.subTest(method=name):
                with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                    getattr(driver, name)(*args)

    def test_native_event_acceptance_refuses_before_journal_access(self):
        journal = object.__new__(native.CMCoordinationJournal)
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            journal.append('NATIVE_OUTCOME', 'op', {'evidence_class':'NATIVE_VERIFIED'})

    def test_direct_read_command_refuses_before_executable_selection(self):
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            native_observation._command(None, None, None, 'info', [], 'a'*64)

    def test_predecessor_cli_refuses_before_path_validation(self):
        from hybrid_bridge.practical_backend import PracticalBackend
        backend = object.__new__(PracticalBackend)
        with self.assertRaisesRegex(ValueError, 'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            backend._run_cli([], b'', 1, 'unused')

    def test_direct_disposable_adapter_refuses_all_native_entrypoints(self):
        adapter = object.__new__(native_pilot.PilotNativeAdapter)
        command = {'kind':'claim','native_task_id':'mip-a','actor':native_pilot.ACTOR}
        for action in (lambda:adapter.execute('op',command),lambda:adapter.readback(command),
                       lambda:adapter._run([],True),lambda:adapter._default_runner([],None,{})):
            with self.subTest(action=action):
                with self.assertRaisesRegex(ValueError,'E_RELEASE_PROFILE_NATIVE_DISABLED'):
                    action()

    def test_direct_race_worker_refuses_before_reading_spec_or_journal(self):
        from hybrid_bridge import practical_race_alice
        with self.assertRaisesRegex(ValueError,'E_RELEASE_PROFILE_NATIVE_DISABLED'):
            practical_race_alice.run(ROOT/'absent-spec.json')
