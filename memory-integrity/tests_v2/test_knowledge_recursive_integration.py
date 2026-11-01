"""Real owned-root integration controls; retained logs distinguish startup failure."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


@unittest.skipUnless(os.name == 'nt', 'Windows owned-process proof required')
class RecursiveOwnedIntegration(unittest.TestCase):
    def run_owned(self, root, script, *, environment=None, **limits):
        from knowledge_bridge.windows_owned_process import launch_current
        owner = None
        with (root/'stdout.log').open('wb') as output, (root/'stderr.log').open('wb') as errors:
            try:
                owner = launch_current(subprocess.Popen, sys.executable, script,
                    stdin=subprocess.PIPE, stdout=output, stderr=errors,
                    env=(dict(os.environ, PYTHONNOUSERSITE='1') if environment is None else environment),
                    cwd=root, **limits)
                owner.wait(time.monotonic()+5)
                owner.release()
            finally:
                if owner is not None:
                    if not owner.proof.get('released'):
                        owner.stop(time.monotonic()+5)
                        owner.release()
                    if owner.process.stdin is not None:
                        owner.process.stdin.close()
        return owner

    def test_actual_owned_root_runs_bound_readonly_git_with_native_exit_proof(self):
        repo = ROOT.parent
        with tempfile.TemporaryDirectory(prefix='rp2-owned-git-') as name:
            root = Path(name)
            script = root/'root.py'
            script.write_text('import json,subprocess\n'
                'subprocess.Popen._rp_bind_runtime_git(' + repr(str(repo)) + ')\n'
                'head=subprocess.check_output(["git","-C",' + repr(str(repo)) +
                ',"rev-parse","HEAD"],text=True).strip()\n'
                'print(json.dumps({"head":head,"guard":subprocess.Popen._rp1_guard}))\n', encoding='utf-8')
            env = {k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
            env['PYTHONNOUSERSITE'] = '1'
            owner = self.run_owned(root, script, deadline=time.monotonic()+10, environment=env)
            self.assertEqual(owner.process.returncode, 0, (root/'stderr.log').read_text())
            actual = json.loads((root/'stdout.log').read_text())
            expected = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'], text=True).strip()
            self.assertEqual(actual, {'head':expected, 'guard':True})
            self.assertTrue(owner.proof['termination']['native_exit_proved'])
            self.assertGreaterEqual(owner.proof['termination']['records'], 2)

    def test_default_recursive_budget_is_independent_of_startup_deadline(self):
        with tempfile.TemporaryDirectory(prefix='rp2-independent-deadlines-') as name:
            root = Path(name)
            script = root/'root.py'
            script.write_text('pass\n', encoding='utf-8')
            before = time.monotonic()
            startup = before+10
            owner = self.run_owned(root, script, deadline=startup)
            after = time.monotonic()
            self.assertEqual(owner.process.returncode, 0, (root/'stderr.log').read_text())
            contract = json.loads(owner._paths['contract'].read_text(encoding='utf-8'))
            self.assertEqual(contract['deadline'], startup)
            self.assertGreaterEqual(contract['recursive']['deadline'], before+120)
            self.assertLessEqual(contract['recursive']['deadline'], after+120)
            self.assertGreater(contract['recursive']['deadline'], startup)

    def test_both_sessions_propagate_the_same_recursive_request_deadline(self):
        from knowledge_bridge import distributed_retrieval as distributed
        from knowledge_bridge import windows_owned_process as owned
        deadline = time.monotonic()+30
        seen = []
        def capture(*args, **kwargs):
            seen.append((kwargs.get('deadline'), kwargs.get('recursive_deadline')))
            raise OSError('CONTROL_STOP_BEFORE_PROCESS')
        with patch.object(owned, 'launch_current', side_effect=capture):
            for lane in (0, 1):
                with self.assertRaisesRegex(OSError, 'CONTROL_STOP_BEFORE_PROCESS'):
                    distributed._Session(sys.executable, lane, 'a'*64, deadline)
        self.assertEqual(seen, [(deadline, deadline), (deadline, deadline)])

    def test_changed_policy_seal_blocks_authored_code_and_retains_profile_failure(self):
        from knowledge_bridge import windows_owned_process as owned
        real_record = owned._source_record
        def corrupt_policy(path):
            row = real_record(path)
            if Path(path).name == 'recursive_policy.py':
                row['sha256'] = '0'*64
            return row
        with tempfile.TemporaryDirectory(prefix='rp2-policy-seal-') as name:
            root = Path(name)
            marker = root/'must-not-run'
            script = root/'root.py'
            script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) +
                              ').write_text("bad")\n', encoding='utf-8')
            with patch.object(owned, '_source_record', side_effect=corrupt_policy):
                owner = self.run_owned(root, script, deadline=time.monotonic()+10)
            self.assertNotEqual(owner.process.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertIn('E_RP_OWNED_PROFILE_SOURCE', (root/'stderr.log').read_text())
            rows = [json.loads(p.read_text()) for p in root.rglob('rp1-install-*.failure.json')]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['stage'], 'profile')
            self.assertIn('E_RP_OWNED_PROFILE_SOURCE', rows[0]['error'])
            self.assertTrue(owner.proof['termination']['native_exit_proved'])

    def test_owned_root_refuses_unsupported_recursive_python_before_child_starts(self):
        from knowledge_bridge.windows_owned_process import launch_current
        original_popen = subprocess.Popen
        with tempfile.TemporaryDirectory(prefix='rp2-recursive-guard-') as name:
            root = Path(name)
            marker = root / 'unsupported-child-started'
            child_code = 'from pathlib import Path; Path(' + repr(str(marker)) + ').write_text("started")'
            script = root / 'root.py'
            script.write_text(
                'import json,subprocess,sys\n'
                'try:\n'
                ' child=subprocess.Popen([sys.executable,"-S","-c",' + repr(child_code) + '])\n'
                ' code=child.wait(timeout=5)\n'
                ' print(json.dumps({"refused":False,"child_exit":code}))\n'
                'except ValueError as error:\n'
                ' print(json.dumps({"refused":True,"error":str(error)}))\n', encoding='utf-8')
            owner = None
            with (root/'stdout.log').open('wb') as output, (root/'stderr.log').open('wb') as errors:
                try:
                    owner = launch_current(subprocess.Popen, sys.executable, script,
                        deadline=time.monotonic()+10, stdin=subprocess.PIPE,
                        stdout=output, stderr=errors, env=os.environ.copy(), cwd=root)
                    self.assertIs(subprocess.Popen, original_popen, 'parent Popen was changed')
                    owner.wait(time.monotonic()+5)
                    owner.release()
                finally:
                    if owner is not None:
                        if not owner.proof.get('released'):
                            owner.stop(time.monotonic()+5)
                            owner.release()
                        if owner.process.stdin is not None:
                            owner.process.stdin.close()
            stderr = (root/'stderr.log').read_text(encoding='utf-8')
            self.assertEqual(owner.process.returncode, 0, stderr)
            frame = json.loads((root/'stdout.log').read_text(encoding='utf-8'))
            self.assertTrue(frame['refused'], 'unsupported recursive Python child was allowed to execute')
            self.assertIn('E_RP1_ARGV_STARTUP', frame['error'])
            self.assertFalse(marker.exists())
            self.assertTrue(owner.proof['termination']['native_exit_proved'])

    def test_post_go_startup_refusal_retains_cause_before_authored_worker(self):
        from knowledge_bridge.windows_owned_process import launch_current
        with tempfile.TemporaryDirectory(prefix='rp2-recursive-install-failure-') as name:
            root = Path(name)
            marker = root / 'authored-worker-started'
            (root/'forbidden.dll').write_bytes(b'inert startup-audit control')
            script = root / 'root.py'
            script.write_text('from pathlib import Path\nPath(' + repr(str(marker)) +
                              ').write_text("started")\n', encoding='utf-8')
            owner = None
            with (root/'stdout.log').open('wb') as output, (root/'stderr.log').open('wb') as errors:
                try:
                    owner = launch_current(subprocess.Popen, sys.executable, script,
                        deadline=time.monotonic()+10, stdin=subprocess.PIPE,
                        stdout=output, stderr=errors, env=os.environ.copy(), cwd=root)
                    owner.wait(time.monotonic()+5)
                    owner.release()
                finally:
                    if owner is not None:
                        if not owner.proof.get('released'):
                            owner.stop(time.monotonic()+5)
                            owner.release()
                        if owner.process.stdin is not None:
                            owner.process.stdin.close()
            self.assertNotEqual(owner.process.returncode, 0, 'startup refusal was returned as success')
            self.assertFalse(marker.exists(), 'authored worker ran despite failed startup audit')
            stderr = (root/'stderr.log').read_text(encoding='utf-8')
            self.assertIn('E_RP_STARTUP_CWD_DLL', stderr)
            records = [json.loads(p.read_text(encoding='utf-8')) for p in root.rglob('*.failure.json')]
            failures = [row for row in records if row.get('stage') == 'audit-cwd']
            self.assertTrue(failures, 'failure segment is absent from retained diagnostics')
            self.assertIn('E_RP_STARTUP_CWD_DLL', json.dumps(failures))
            self.assertTrue(owner.proof['termination']['native_exit_proved'])
