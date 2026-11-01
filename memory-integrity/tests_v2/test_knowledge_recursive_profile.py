"""Controller fault injection for owned profiles; no selected Store runtime."""
import os
from pathlib import Path
import site
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


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
