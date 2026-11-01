"""Closed editable-runtime Git binding; controller and read-only Git only."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT/'scripts'))


@unittest.skipUnless(os.name == 'nt', 'Windows owned profile')
class RecursiveGit(unittest.TestCase):
    def setUp(self):
        from knowledge_bridge import recursive_bootstrap as bootstrap
        self.b = bootstrap
        directory = tempfile.TemporaryDirectory(prefix='rp2-git-binding-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.env = {k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','GIT_'))}
        self.env['PYTHONNOUSERSITE'] = '1'
        requests = self.root/'requests'
        requests.mkdir()
        self.profile = self.b.owned_profile({'version':1, 'deadline':time.monotonic()+120,
            'requests':str(requests), 'bootstrap':self.b.record(self.b.__file__),
            'policy':self.b.record(Path(self.b.__file__).with_name('recursive_policy.py'))})
        original = subprocess.Popen
        self.guarded = self.b.install(self.profile)
        self.addCleanup(setattr, subprocess, 'Popen', original)

    def test_binding_is_idempotent_but_rejects_other_root_image_and_vectors(self):
        self.guarded._rp_bind_runtime_git(REPO)
        first = json.dumps(self.profile['native_commands'], sort_keys=True)
        self.guarded._rp_bind_runtime_git(REPO)
        self.assertEqual(json.dumps(self.profile['native_commands'], sort_keys=True), first)
        with self.assertRaisesRegex(ValueError, 'GIT_REBIND'):
            self.guarded._rp_bind_runtime_git(self.root)
        with patch.object(self.b.shutil, 'which', return_value=str(self.root/'git.exe')):
            with self.assertRaisesRegex(ValueError, 'GIT_REBIND'):
                self.guarded._rp_bind_runtime_git(REPO)
        with self.assertRaisesRegex(ValueError, 'GIT_VECTOR'):
            subprocess.Popen(['git', '--version'], env=self.env)
        with self.assertRaisesRegex(ValueError, 'GIT_ENV'):
            subprocess.Popen(['git','-C',str(REPO),'rev-parse','HEAD'],
                             env=dict(self.env, GIT_CONFIG_COUNT='1'))

    def test_bound_git_preserves_existing_readonly_outputs(self):
        self.guarded._rp_bind_runtime_git(REPO)
        for tail in (['rev-parse','HEAD'], ['status','--porcelain','--untracked-files=all']):
            argv = ['git','-C',str(REPO),*tail]
            spec = self.profile['native_commands']['git']
            original = self.guarded.__bases__[0]
            with original([spec['image']['path'],*argv[1:]], env=self.env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as direct:
                out, err = direct.communicate(timeout=10)
            actual = subprocess.run(argv, env=self.env, capture_output=True, timeout=10)
            self.assertEqual((actual.returncode,actual.stdout,actual.stderr), (direct.returncode,out,err))

    def test_expired_binding_and_dispatch_cannot_start_git(self):
        self.profile['deadline'] = time.monotonic()-1
        with patch.object(self.b, 'native_spec', side_effect=AssertionError('must refuse before inspection')):
            with self.assertRaisesRegex(ValueError, 'DEADLINE'):
                self.guarded._rp_bind_runtime_git(REPO)
        self.profile['deadline'] = time.monotonic()+10
        self.guarded._rp_bind_runtime_git(REPO)
        self.profile['deadline'] = time.monotonic()-1
        with patch.object(self.b, 'route_native', side_effect=AssertionError('must refuse before routing')):
            with self.assertRaisesRegex(ValueError, 'DEADLINE'):
                subprocess.Popen(['git','-C',str(REPO),'rev-parse','HEAD'], env=self.env)


class EditableRuntimeHook(unittest.TestCase):
    def exercise(self, guarded):
        # Execute the real function body with explicit metadata/source controls;
        # no vendor import or selected interpreter is claimed by this test.
        path = ROOT/'scripts/knowledge_bridge/worker.py'
        node = next(n for n in ast.parse(path.read_bytes()).body
                    if isinstance(n,ast.FunctionDef) and n.name=='runtime_identity')
        events = []
        class Popen:
            pass
        if guarded:
            Popen._rp_bind_runtime_git = staticmethod(lambda root: events.append(('bind',str(root))))
        revision = 'a'*40
        def run(argv, **options):
            events.append(('run',argv[3:]))
            return types.SimpleNamespace(returncode=0, stdout=revision if argv[3]=='rev-parse' else '')
        metadata = types.SimpleNamespace(version=lambda name:'1.0', distribution=lambda name:
            types.SimpleNamespace(read_text=lambda name:'{"dir_info":{"editable":true}}'))
        namespace = {'sys':types.SimpleNamespace(version_info=(3,12)), 'Path':Path,
            'importlib':types.SimpleNamespace(metadata=metadata), 'c':types.SimpleNamespace(loads=json.loads),
            'subprocess':types.SimpleNamespace(Popen=Popen,run=run),
            'SEMANTICA_VERSION':'1.0','SEMANTICA_REVISION':revision,'BRIDGE_VERSION':'test'}
        fake = types.ModuleType('semantica')
        fake.__file__ = str(REPO/'semantica/__init__.py')
        with patch.dict(sys.modules, {'semantica':fake}):
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
            result = namespace['runtime_identity']()
        self.assertEqual(result['revision'], revision)
        return events

    def test_editable_owned_runtime_binds_before_existing_git_queries(self):
        events = self.exercise(True)
        self.assertEqual(events, [('bind',str(REPO)), ('run',['rev-parse','HEAD']),
                                  ('run',['status','--porcelain','--untracked-files=all'])])

    def test_non_owned_runtime_keeps_existing_git_path(self):
        self.assertEqual(self.exercise(False), [('run',['rev-parse','HEAD']),
                                                ('run',['status','--porcelain','--untracked-files=all'])])
