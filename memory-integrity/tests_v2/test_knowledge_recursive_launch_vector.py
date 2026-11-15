"""Direct-image launch preserves older CPython's base identity and authored argv."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from knowledge_bridge import recursive_bootstrap as b


class RecursiveLaunchVector(unittest.TestCase):
    def test_direct_image_argv0_keeps_selected_venv_only_in_bound_launcher(self):
        for mode, tail in (('script', ['child.py', 'argument with spaces']),
                           ('c', ['-c', 'print(7)', 'tail']),
                           ('m', ['-m', 'authored.module', 'tail'])):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='recursive-vector-') as name:
                root = Path(name)
                selected, image = str(root/'venv/Scripts/python.exe'), str(root/'base/python.exe')
                requests = root/'requests'; requests.mkdir()
                profile = {'selected': selected, 'image': image, 'paths': [], 'requests': str(requests),
                           'store_userbase': None, 'variant': 'OWNED_RUNTIME', 'user_site': False,
                           'bootstrap': {'path': str(root/'bootstrap.py'), 'sha256': 'a'*64},
                           'policy': {'path': str(root/'policy.py'), 'sha256': 'b'*64}}
                from knowledge_bridge import recursive_policy as policy
                real_policy = SimpleNamespace(parse_argv=policy.parse_argv, clean_env=policy.clean_env,
                                              read_checked=lambda *args: b'bound source')
                authored = [selected, '-B', *tail]
                options = {'env': {'PYTHONNOUSERSITE': '1'}, 'cwd': str(root)}
                with patch.object(b, 'validate_profile'), patch.object(b, 'audit'), \
                     patch.object(b, 'policy', return_value=real_policy):
                    argv, actual = b.prepare_launch(authored, profile, options)
                self.assertEqual(argv[0], image, 'CPython 3.11/3.12 derives base_executable from argv[0]')
                self.assertEqual(actual['executable'], image)
                self.assertEqual(actual['env']['__PYVENV_LAUNCHER__'], selected)
                self.assertEqual(argv[1:3], ['-B', '-c'])
                request, = requests.glob('*.json')
                raw = request.read_bytes(); doc = json.loads(raw)
                self.assertEqual(doc['command']['argv'], authored)
                self.assertEqual(doc['command']['mode'], mode)
                self.assertEqual(doc['profile'], profile)
                self.assertIn(hashlib.sha256(raw).hexdigest(), argv[-1])
                self.assertEqual(authored, [selected, '-B', *tail], 'caller command mutated')


class NativeRecursiveIdentity(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows direct-image recursive identity proof required')
    def test_child_and_grandchild_preserve_real_base_and_selected_venv(self):
        from knowledge_bridge.windows_owned_process import launch_current
        with tempfile.TemporaryDirectory(prefix='recursive-native-identity-') as name:
            root = Path(name)
            frame = "{'executable':sys.executable,'base_executable':sys._base_executable,'prefix':sys.prefix,'guard':subprocess.Popen._rp1_guard}"
            leaf = ('import json,sys,subprocess,time\nfrom pathlib import Path\n'
                    'Path("leaf-ready").write_text("ready")\n'
                    'until=time.monotonic()+10\n'
                    'while not Path("release").exists():\n'
                    ' if time.monotonic()>=until: raise TimeoutError("fixture release not received")\n'
                    ' time.sleep(.005)\nprint(json.dumps(['+frame+']))')
            child = 'import json,sys,subprocess;rows=json.loads(subprocess.check_output([sys.executable,"-B","-c",'+repr(leaf)+'],text=True));print(json.dumps(['+frame+']+rows))'
            code = 'import json,sys,subprocess;rows=json.loads(subprocess.check_output([sys.executable,"-B","-c",'+repr(child)+'],text=True));print(json.dumps(['+frame+']+rows))'
            script = root/'root.py'; script.write_text(code, encoding='utf-8')
            owner = None
            with (root/'stdout.log').open('wb') as out, (root/'stderr.log').open('wb') as err:
                try:
                    owner = launch_current(subprocess.Popen, sys.executable, script,
                        deadline=time.monotonic()+10, stdin=subprocess.PIPE, stdout=out, stderr=err,
                        env=dict(os.environ, PYTHONNOUSERSITE='1'), cwd=root)
                    until = time.monotonic()+10
                    while not (root/'leaf-ready').exists():
                        if time.monotonic() >= until or owner.process.poll() is not None:
                            self.fail('recursive leaf readiness failed: '+(root/'stderr.log').read_text())
                        time.sleep(.005)
                    owner._observe(until)  # Pin every live native handle before fixture release.
                    (root/'release').write_text('release', encoding='utf-8')
                    owner.wait(time.monotonic()+5)
                    owner.release()
                finally:
                    if owner is not None:
                        if not owner.proof.get('released'):
                            owner.stop(time.monotonic()+5); owner.release()
                        if owner.process.stdin is not None: owner.process.stdin.close()
            self.assertEqual(owner.process.returncode, 0, (root/'stderr.log').read_text())
            rows = json.loads((root/'stdout.log').read_text())
            self.assertEqual(len(rows), 3)
            expected = {'executable': sys.executable, 'base_executable': sys._base_executable, 'prefix': sys.prefix}
            for row in rows:
                self.assertIs(row['guard'], True)
                for key, value in expected.items():
                    self.assertEqual(os.path.normcase(os.path.abspath(row[key])), os.path.normcase(os.path.abspath(value)))
            self.assertTrue(owner.proof['termination']['native_exit_proved'])


if __name__ == '__main__':
    unittest.main()
