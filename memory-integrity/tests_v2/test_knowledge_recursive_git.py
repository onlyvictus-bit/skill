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

from _knowledge_git_fixture import create_git_fixture, fixture_snapshot

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
        self.repo, self.head = create_git_fixture(self.root)
        # This newly owned fixture can live under long retained evidence paths.
        # Bind its local setting; no user/system/real-checkout config is changed.
        with (self.repo/'.git/config').open('a',encoding='ascii') as stream:
            stream.write('longpaths = true\n')
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
        self.guarded._rp_bind_runtime_git(self.repo)
        first = json.dumps(self.profile['native_commands'], sort_keys=True)
        self.guarded._rp_bind_runtime_git(self.repo)
        self.assertEqual(json.dumps(self.profile['native_commands'], sort_keys=True), first)
        with self.assertRaisesRegex(ValueError, 'GIT_REBIND'):
            self.guarded._rp_bind_runtime_git(self.root)
        with patch.object(self.b.shutil, 'which', return_value=str(self.root/'git.exe')):
            with self.assertRaisesRegex(ValueError, 'GIT_REBIND'):
                self.guarded._rp_bind_runtime_git(self.repo)
        with self.assertRaisesRegex(ValueError, 'GIT_VECTOR'):
            subprocess.Popen(['git', '--version'], env=self.env)
        with self.assertRaisesRegex(ValueError, 'GIT_ENV'):
            subprocess.Popen(['git','-C',str(self.repo),'rev-parse','HEAD'],
                             env=dict(self.env, GIT_CONFIG_COUNT='1'))

    def test_bound_git_preserves_existing_readonly_outputs(self):
        before = fixture_snapshot(self.repo)
        tails = (['rev-parse','HEAD'], ['status','--porcelain','--untracked-files=all'])
        script = self.root/'owned-git-outputs.py'
        script.write_text('import json,subprocess\n'
            'root=' + repr(str(self.repo)) + '\n'
            'subprocess.Popen._rp_bind_runtime_git(root)\n'
            'rows=[]\n'
            'for tail in ' + repr(tails) + ':\n'
            ' result=subprocess.run(["git","-C",root,*tail],capture_output=True,timeout=10)\n'
            ' rows.append({"returncode":result.returncode,"stdout":result.stdout.hex(),"stderr":result.stderr.hex()})\n'
            'print(json.dumps(rows))\n',encoding='utf-8')
        # The binding-only unit setup intentionally does not own the long-lived
        # test runner. Exercise real dispatch in a fresh, legitimately owned root.
        import test_knowledge_recursive_integration as integration
        from knowledge_bridge import windows_ready_copy as ready
        environment={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
        environment['PYTHONNOUSERSITE']='1'
        original=self.guarded.__bases__[0]
        with patch.object(subprocess,'Popen',original), \
                patch.object(ready,'default_root',return_value=self.root/'ready-copies-v1'):
            owner=integration.RecursiveOwnedIntegration.run_owned(self,self.root,script,
                deadline=time.monotonic()+10,environment=environment)
        self.assertEqual(owner.process.returncode,0,(self.root/'stderr.log').read_text())
        rows=json.loads((self.root/'stdout.log').read_text())
        self.assertEqual(len(rows),len(tails))
        self.assertTrue(owner.proof['termination']['native_exit_proved'])
        self.assertGreaterEqual(owner.proof['termination']['records'],3,json.dumps(owner.proof))
        for tail,row in zip(tails,rows):
            argv = ['git','-C',str(self.repo),*tail]
            spec = self.b.native_spec(self.b.shutil.which('git'),self.repo,
                bound_home=environment.get('HOME') or environment.get('USERPROFILE'))
            with original([spec['image']['path'],'--no-optional-locks',*argv[1:]], env=self.env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE) as direct:
                out, err = direct.communicate(timeout=10)
            actual=subprocess.CompletedProcess(argv,row['returncode'],bytes.fromhex(row['stdout']),bytes.fromhex(row['stderr']))
            self.assertEqual((actual.returncode,actual.stdout,actual.stderr), (direct.returncode,out,err))
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(actual.stdout.strip(), self.head.encode() if tail[0]=='rev-parse' else b'')
        self.assertEqual(fixture_snapshot(self.repo), before)

    def test_expired_binding_and_dispatch_cannot_start_git(self):
        self.profile['deadline'] = time.monotonic()-1
        with patch.object(self.b, 'native_spec', side_effect=AssertionError('must refuse before inspection')):
            with self.assertRaisesRegex(ValueError, 'DEADLINE'):
                self.guarded._rp_bind_runtime_git(self.repo)
        self.profile['deadline'] = time.monotonic()+10
        self.guarded._rp_bind_runtime_git(self.repo)
        self.profile['deadline'] = time.monotonic()-1
        with patch.object(self.b, 'route_native', side_effect=AssertionError('must refuse before routing')):
            with self.assertRaisesRegex(ValueError, 'DEADLINE'):
                subprocess.Popen(['git','-C',str(self.repo),'rev-parse','HEAD'], env=self.env)


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
