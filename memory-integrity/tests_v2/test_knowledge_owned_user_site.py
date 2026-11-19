"""The owned launch excludes user-site startup only in its child process."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).absolute().parents[1] / 'scripts'))


@unittest.skipUnless(os.name == 'nt', 'Windows native owned-launch proof required')
class OwnedUserSiteTests(unittest.TestCase):
    def test_disabled_child_profile_does_not_mutate_callers_environment(self):
        from knowledge_bridge.windows_owned_process import launch_current
        parent = dict(os.environ)
        for key in ('PYTHONNOUSERSITE', 'pythonNOUSERsite'):
            with self.subTest(key=key), tempfile.TemporaryDirectory(prefix='owned-user-site-') as name:
                root = Path(name)
                script = root / 'root.py'
                script.write_text('import json,os,site,sys\n'
                    'print(json.dumps({"enabled":site.ENABLE_USER_SITE, '
                    '"flag":sys.flags.no_user_site,"env":'
                    '[(k,v) for k,v in os.environ.items() if k.upper()=="PYTHONNOUSERSITE"]}))\n',
                    encoding='utf-8')
                env = {k:v for k,v in parent.items() if k.upper() != 'PYTHONNOUSERSITE'}
                env[key] = '0'
                before = dict(env)
                owner = None
                with (root/'stdout.log').open('wb') as output, (root/'stderr.log').open('wb') as errors:
                    try:
                        owner = launch_current(subprocess.Popen, sys.executable, script,
                            deadline=time.monotonic()+10, stdin=subprocess.PIPE,
                            stdout=output, stderr=errors, env=env, cwd=root)
                        owner.wait(time.monotonic()+5)
                        owner.release()
                    finally:
                        if owner is not None:
                            if not owner.proof.get('released'):
                                owner.stop(time.monotonic()+5)
                                owner.release()
                            owner.process.stdin.close()
                            (root/'Owned-Proof.json').write_text(json.dumps(owner.proof), encoding='utf-8')
                self.assertEqual(owner.process.returncode, 0, (root/'stderr.log').read_text())
                frame = json.loads((root/'stdout.log').read_text())
                self.assertIs(frame['enabled'], False)
                self.assertEqual(frame['flag'], 1)
                self.assertEqual([(k.upper(), v) for k,v in frame['env']], [('PYTHONNOUSERSITE', '1')])
                self.assertTrue(owner.proof['termination']['native_exit_proved'])
                self.assertEqual(env, before)
        self.assertEqual(dict(os.environ), parent)


if __name__ == '__main__':
    unittest.main()
