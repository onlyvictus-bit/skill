"""Controller fault injection for owned profiles; no selected Store runtime."""
import os
from pathlib import Path
import site
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


@unittest.skipUnless(os.name == 'nt', 'Windows owned-root Job required')
class OwnedRootJobGate(unittest.TestCase):
    @staticmethod
    def native_api(failure=None):
        import ctypes
        events = []
        class Call:
            def __init__(self, name, action): self.name, self.action = name, action
            def __call__(self, *args):
                events.append((self.name, args))
                if self.name == failure or (failure == 'assign-and-close' and self.name in ('AssignProcessToJobObject', 'CloseHandle')):
                    ctypes.set_last_error(5)
                    return 0
                return self.action(*args)
        def membership(process, job, inside):
            inside._obj.value = 0 if failure == 'outside' else 1
            return 1
        actions = {'CreateJobObjectW': lambda *a: 123, 'GetCurrentProcess': lambda: -1,
            'AssignProcessToJobObject': lambda *a: 1, 'IsProcessInJob': membership,
            'CloseHandle': lambda *a: 1}
        return SimpleNamespace(**{name: Call(name, action) for name, action in actions.items()}), events

    def test_native_create_assign_and_membership_faults_fail_closed(self):
        from knowledge_bridge import recursive_bootstrap as b
        for failure in ('CreateJobObjectW', 'AssignProcessToJobObject', 'IsProcessInJob', 'outside'):
            api, events = self.native_api(failure)
            with self.subTest(failure=failure), patch.object(b.ctypes, 'WinDLL', return_value=api):
                with self.assertRaises((OSError, ValueError)):
                    b._enter_owned_root_job()
            closed = [args for name, args in events if name == 'CloseHandle']
            self.assertEqual(closed, [] if failure == 'CreateJobObjectW' else [(123,)])

    def test_native_job_verifies_current_membership_and_retains_exact_handle(self):
        from knowledge_bridge import recursive_bootstrap as b
        api, events = self.native_api()
        with patch.object(b.ctypes, 'WinDLL', return_value=api):
            job = b._enter_owned_root_job()
        self.assertEqual(job.handle, 123)
        self.assertEqual(events[0], ('CreateJobObjectW', (None, None)))
        self.assertIn(('AssignProcessToJobObject', (123, -1)), events)
        self.assertFalse(any(name == 'CloseHandle' for name, args in events))
        job.close()
        self.assertIsNone(job.handle)
        self.assertEqual(events[-1], ('CloseHandle', (123,)))

    def test_native_assign_error_remains_primary_when_close_also_fails(self):
        from knowledge_bridge import recursive_bootstrap as b
        api, events = self.native_api('assign-and-close')
        with patch.object(b.ctypes, 'WinDLL', return_value=api):
            with self.assertRaises(OSError) as caught:
                b._enter_owned_root_job()
        self.assertIn('E_RP_OWNED_ROOT_JOB_ASSIGN', str(caught.exception.__notes__))
        self.assertIn('E_RP_OWNED_ROOT_JOB_CLOSE', str(caught.exception.__notes__))
        self.assertEqual(caught.exception.owned_root_job_debt.handle, 123)

    def invoke(self, enter, install, variant='OWNED_RUNTIME'):
        from knowledge_bridge import recursive_bootstrap as b
        profile = {'variant': variant, 'paths': sys.path[:]}
        with ExitStack() as stack:
            for name, action in (('validate_profile', lambda p: p),
                    ('environment_profile', lambda p, e: p), ('attest', lambda *a, **k: None),
                    ('observed_profile', lambda p: p), ('policy', lambda p: None),
                    ('_publish_failure', lambda *a, **k: None), ('_check_startup_deadline', lambda d: None)):
                stack.enter_context(patch.object(b, name, side_effect=action))
            entry = stack.enter_context(patch.object(b, '_enter_owned_root_job', side_effect=enter, create=True))
            dispatch = stack.enter_context(patch.object(b, 'install', side_effect=install))
            self.entry, self.dispatch = entry, dispatch
            return b.install_root(profile, time.monotonic()+10)

    def test_owned_root_enters_job_before_guard_and_retains_handle(self):
        events = []
        job = SimpleNamespace(handle=123, close=lambda: events.append('close'))
        guard = SimpleNamespace()
        result = self.invoke(lambda: (events.append('job'), job)[1],
                             lambda p: (events.append('guard'), guard)[1])
        self.assertEqual(events, ['job', 'guard'])
        self.assertIs(result._rp_root_job, job)
        self.assertEqual(result._rp_root_job.handle, 123)

    def test_create_or_assignment_failure_blocks_dispatch(self):
        for name in ('CONTROL_CREATE_JOB', 'CONTROL_ASSIGN_JOB'):
            error = OSError(name)
            with self.subTest(name=name):
                def refuse(): raise error
                with self.assertRaises(OSError) as caught:
                    self.invoke(refuse, lambda p: SimpleNamespace())
                self.assertIs(caught.exception, error)
                self.dispatch.assert_not_called()

    def test_guard_failure_attempts_job_close_and_preserves_original(self):
        events = []
        original = OSError('CONTROL_INSTALL_GUARD')
        def close():
            events.append('close')
            raise OSError('CONTROL_JOB_CLOSE')
        job = SimpleNamespace(handle=123, close=close)
        def refuse(profile): raise original
        with self.assertRaises(OSError) as caught:
            self.invoke(lambda: job, refuse)
        self.assertIs(caught.exception, original)
        self.assertEqual(events, ['close'])
        self.assertIn('CONTROL_JOB_CLOSE', str(original.__notes__))
        self.assertIs(original.owned_root_job_debt, job)

    def test_controller_variant_does_not_change_its_job_membership(self):
        guard = SimpleNamespace()
        result = self.invoke(lambda: self.fail('controller must not enter Job'), lambda p: guard,
                             variant='CONTROLLER_ONLY')
        self.assertIs(result, guard)
        self.entry.assert_not_called()


@unittest.skipUnless(os.name == 'nt', 'Windows profile identity required')
class OwnedProfile(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge import recursive_bootstrap as bootstrap
        self.b = bootstrap
        directory = tempfile.TemporaryDirectory(prefix='rp2-owned-profile-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.requests = self.root / 'requests'
        self.requests.mkdir()
        self.bound = {'version': 1, 'deadline': time.monotonic()+120,
            'requests': str(self.requests),
            'bootstrap': self.b.record(self.b.__file__),
            'policy': self.b.record(Path(self.b.__file__).with_name('recursive_policy.py'))}
        self.paths = [str(Path(self.b.__file__).parent), str(Path(sys.base_prefix)/'Lib'),
                      str(Path(sys.base_prefix)/'DLLs')]
        self.alias = (self.root / 'normal/AppData/Local/Microsoft/WindowsApps' /
                      'PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/python.exe')
        self.store_base = (self.alias.parents[3] / 'Packages' / self.alias.parent.name /
                           'LocalCache/local-packages')

    def test_store_missing_userbase_cannot_reach_installer(self):
        for no_site in (None, '0', '1'):
            environment = {} if no_site is None else {'PYTHONNOUSERSITE': no_site}
            with self.subTest(no_site=no_site), patch.dict(os.environ, environment, clear=True), \
                    patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                    patch.object(self.b, '_owned_store_runtime', return_value=True), \
                    patch.object(self.b, 'install_root') as install:
                with self.assertRaisesRegex(ValueError, 'STORE'):
                    self.b.install_owned_root(self.bound, time.monotonic()+10)
                install.assert_not_called()
        failures = list(self.requests.glob('rp1-install-*.failure.json'))
        self.assertEqual(len(failures), 3)

    def test_store_missing_binding_cannot_reach_child_audit(self):
        with patch.dict(os.environ, {'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(self.b, '_owned_store_runtime', return_value=False):
            profile = self.b.owned_profile(self.bound)
        with patch.dict(os.environ, {'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', profile['paths']), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(self.b, '_owned_store_runtime', return_value=True), \
                patch.object(self.b, '_in_any_job'), patch.object(self.b, 'audit') as audit:
            with self.assertRaisesRegex(ValueError, 'STORE'):
                self.b.attest(profile)
            audit.assert_not_called()

    def test_store_value_requires_no_user_site_and_is_bound_without_rewriting(self):
        base = str(self.store_base)
        for no_site, enabled in ((None, False), ('0', False), ('1', True)):
            environment = {'PYTHONUSERBASE': base}
            if no_site is not None:
                environment['PYTHONNOUSERSITE'] = no_site
            with self.subTest(no_site=no_site, enabled=enabled), \
                    patch.dict(os.environ, environment, clear=True), patch.object(sys, 'path', self.paths), \
                    patch.object(site, 'ENABLE_USER_SITE', enabled), \
                    patch.object(self.b, '_owned_store_runtime', return_value=True):
                with self.assertRaisesRegex(ValueError, 'STORE'):
                    self.b.owned_profile(self.bound)
        with patch.dict(os.environ, {'PYTHONUSERBASE':base, 'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(sys, '_base_executable', str(self.alias)), \
                patch.object(self.b, '_owned_store_runtime', return_value=True):
            profile = self.b.owned_profile(self.bound)
        self.assertEqual(profile['store_userbase'], base)
        self.assertFalse(profile['user_site'])
        self.assertEqual(profile['deadline'], self.bound['deadline'])

    def test_non_store_profile_cannot_borrow_store_userbase_exception(self):
        with patch.dict(os.environ, {'PYTHONUSERBASE':str(self.root), 'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(self.b, '_owned_store_runtime', return_value=False):
            with self.assertRaisesRegex(ValueError, 'STORE'):
                self.b.owned_profile(self.bound)

    def test_store_cannot_bind_arbitrary_absolute_or_wrong_family_userbase(self):
        for base in (self.root/'arbitrary', self.alias.parents[3]/'Packages'/'WrongFamily'/'LocalCache/local-packages'):
            with self.subTest(base=str(base)), \
                    patch.dict(os.environ, {'PYTHONUSERBASE':str(base), 'PYTHONNOUSERSITE':'1'}, clear=True), \
                    patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                    patch.object(sys, '_base_executable', str(self.alias)), \
                    patch.object(self.b, '_owned_store_runtime', return_value=True):
                with self.assertRaisesRegex(ValueError, 'STORE'):
                    self.b.owned_profile(self.bound)

    def test_child_attestation_rejects_consistent_but_wrong_store_location(self):
        with patch.dict(os.environ, {'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', self.paths), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(sys, '_base_executable', str(self.alias)), \
                patch.object(self.b, '_owned_store_runtime', return_value=False):
            profile = self.b.owned_profile(self.bound)
        profile['store_userbase'] = str(self.root/'wrong-location')
        with patch.dict(os.environ, {'PYTHONUSERBASE':profile['store_userbase'], 'PYTHONNOUSERSITE':'1'}, clear=True), \
                patch.object(sys, 'path', profile['paths']), patch.object(site, 'ENABLE_USER_SITE', False), \
                patch.object(sys, '_base_executable', str(self.alias)), \
                patch.object(self.b, '_owned_store_runtime', return_value=True), \
                patch.object(self.b, '_in_any_job'), patch.object(self.b, 'audit') as audit:
            with self.assertRaisesRegex(ValueError, 'STORE'):
                self.b.attest(profile)
            audit.assert_not_called()
