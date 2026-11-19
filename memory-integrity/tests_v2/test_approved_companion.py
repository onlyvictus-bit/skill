"""Approved-release boundary: altered code must not execute, even if resealed."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout

MI = Path(__file__).resolve().parents[1]
CM = MI.parent / 'claude-mon'
sys.path.insert(0, str(MI / 'scripts'))
from integrity_v2 import engine_client, release_content, source_audit


class ApprovedCompanion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='approved-companion-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.engine = self.root / 'claude-mon'
        shutil.copytree(CM, self.engine, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.marker = self.root / 'must-not-execute'

    def alter(self, name='scripts/claude_mon_v2.py'):
        target = self.engine / name
        target.write_bytes(('from pathlib import Path; Path(%r).write_text("executed")\n' % str(self.marker)).encode() + target.read_bytes())

    def refused(self):
        ok, value = engine_client.handshake(self.engine)
        self.assertFalse(ok, value)
        self.assertFalse(self.marker.exists(), 'unapproved companion executed before rejection')

    def test_unchanged_approved_copy_works(self):
        ok, value = engine_client.handshake(self.engine)
        self.assertTrue(ok, value)

    def test_relative_companion_alias_normalizes_to_same_root(self):
        import memory_integrity_workflow as core
        core.companion(CM)
        self.assertEqual(engine_client.approved_imports(CM / '..' / CM.name), CM.resolve())

    def test_changed_entry_refused_before_execution(self):
        self.alter(); self.refused()

    def test_self_resealed_changed_entry_is_still_refused(self):
        self.alter()
        (self.engine / release_content.ACTIVE).write_bytes((json.dumps(release_content.content_document(self.engine), sort_keys=True, separators=(',', ':')) + '\n').encode())
        release_content.verify_content(self.engine)
        self.refused()

    def test_wrong_runtime_release_refused(self):
        p = self.engine / 'scripts/complete_read_v2/__init__.py'
        p.write_bytes(p.read_bytes().replace(b'2.0.0-m12', b'0.0.0-audit'))
        self.refused()

    def test_unexpected_file_refused(self):
        (self.engine / 'unexpected.txt').write_bytes(b'not approved')
        self.refused()

    def test_untracked_bytecode_cache_is_refused(self):
        cache = self.engine / 'scripts/complete_read_v2/__pycache__'
        cache.mkdir()
        (cache / 'unapproved.pyc').write_bytes(b'unapproved executable cache')
        self.refused()

    def test_pythonpath_startup_hook_is_not_executed(self):
        hooks = self.root / 'hooks'; hooks.mkdir()
        (hooks / 'sitecustomize.py').write_text('from pathlib import Path; Path(%r).write_text("hook ran")\n' % str(self.marker))
        with patch.dict(os.environ, {'PYTHONPATH': str(hooks)}):
            ok, value = engine_client.handshake(self.engine)
        self.assertTrue(ok, value)
        self.assertFalse(self.marker.exists(), 'unapproved startup hook executed')

    def test_cached_foreign_module_refused(self):
        fake = SimpleNamespace(__file__=str(self.root / 'foreign.py'))
        with patch.dict(sys.modules, {'complete_read_v2.audit_foreign': fake}):
            with self.assertRaisesRegex(ValueError, 'E_COMPANION_IMPORT'):
                engine_client.approved_imports(CM)

    def test_cached_module_cannot_claim_another_approved_file(self):
        fake = SimpleNamespace(__file__=str(CM / 'scripts/complete_read_v2/ledger.py'))
        with patch.dict(sys.modules, {'complete_read_v2.providers': fake}):
            with self.assertRaisesRegex(ValueError, 'E_COMPANION_IMPORT'):
                engine_client.approved_imports(CM)

    def test_public_success_guard_rejects_late_drift(self):
        import memory_integrity_workflow as core
        def drift(args):
            with (self.engine / 'SKILL.md').open('ab') as stream:
                stream.write(b'\nlate change before success\n')
            return {'ok': True}
        argv = ['workflow', 'offline-run', '--claude-mon-root', str(self.engine), '--source', 'unused', '--task', 'fixture', '--responses-file', 'unused', '--run-dir', str(self.root/'unused')]
        output = io.StringIO()
        with patch.object(core, 'offline_run', side_effect=drift), patch.object(sys, 'argv', argv), redirect_stdout(output):
            code = core.main()
        self.assertNotEqual(code, 0)
        self.assertFalse(json.loads(output.getvalue())['ok'])

    def test_hardlinked_approved_bytes_refused(self):
        target = self.engine / 'SKILL.md'
        duplicate = self.root / 'same-bytes.txt'
        duplicate.write_bytes(target.read_bytes()); target.unlink()
        os.link(duplicate, target)
        self.refused()

    def test_missing_file_refused(self):
        (self.engine / 'references/INDEX.md').unlink()
        self.refused()

    def test_direct_engine_call_cannot_bypass_release_gate(self):
        self.alter()
        value, error = engine_client.run_engine(self.engine, ['capabilities'])
        self.assertIsNotNone(error, value)
        self.assertFalse(self.marker.exists())

    def test_direct_partition_probe_cannot_import_altered_code(self):
        self.alter('scripts/complete_read_v2/partition.py')
        errors = source_audit.validate_with_engine(self.engine, b'fixture\n', {})
        self.assertTrue(any('E_ENGINE_APPROVAL' in e for e in errors), errors)
        self.assertFalse(self.marker.exists())

    def test_direct_saved_proof_probe_cannot_import_altered_code(self):
        self.alter('scripts/complete_read_v2/proof.py')
        errors = source_audit.validate_saved_run_with_engine(self.engine, self.root)
        self.assertTrue(any('E_ENGINE_APPROVAL' in e for e in errors), errors)
        self.assertFalse(self.marker.exists())

    def test_change_during_engine_execution_refused(self):
        original = engine_client.subprocess.run
        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            with (self.engine / 'SKILL.md').open('ab') as stream:
                stream.write(b'\nconcurrent change\n')
            return result
        with patch.object(engine_client.subprocess, 'run', side_effect=mutate):
            ok, value = engine_client.handshake(self.engine)
        self.assertFalse(ok, value)

    def test_runtime_identity_is_checked_after_approved_preflight(self):
        ok, valid = engine_client.handshake(CM)
        self.assertTrue(ok, valid)
        for key in ('engine', 'engine_version'):
            with self.subTest(key=key), patch.object(engine_client, 'run_engine', return_value=({**valid, key: 'wrong'}, None)):
                self.assertFalse(engine_client.handshake(CM)[0])

    def test_public_workflow_rejects_before_ledger_creation(self):
        self.alter()
        source = self.root / 'source.txt'; source.write_bytes(b'No external effects.\n')
        reviews = self.root / 'reviews.json'
        reviews.write_text(json.dumps({'U000001': {'interpretation': 'No external effects are permitted.', 'findings': [], 'disposition': 'resolved', 'reviewer': 'fixture', 'unresolved': []}}))
        run = self.root / 'run'
        p = subprocess.run([sys.executable, '-B', str(MI / 'scripts/memory_integrity_workflow.py'), 'offline-run', '--claude-mon-root', str(self.engine), '--source', str(source), '--task', 'Read fixture', '--responses-file', str(reviews), '--run-dir', str(run)], capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=60)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertFalse(run.exists(), 'unapproved companion reached ledger creation')
        self.assertFalse(self.marker.exists())

    def test_normal_python_workflow_does_not_create_companion_cache(self):
        copied_mi = self.root / 'memory-integrity'
        shutil.copytree(MI, copied_mi, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        source = self.root / 'normal-source.txt'; source.write_bytes(b'No external effects.\n')
        reviews = self.root / 'normal-reviews.json'
        reviews.write_text(json.dumps({'U000001': {'interpretation': 'This fixture forbids external effects.', 'findings': [], 'disposition': 'resolved', 'reviewer': 'fixture', 'unresolved': []}}))
        env = dict(os.environ); env.pop('PYTHONDONTWRITEBYTECODE', None)
        p = subprocess.run([sys.executable, str(copied_mi/'scripts/memory_integrity_workflow.py'), 'offline-run', '--claude-mon-root', str(self.engine), '--source', str(source), '--task', 'Read fixture', '--responses-file', str(reviews), '--run-dir', str(self.root/'normal-run')], capture_output=True, env=env, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)
        self.assertFalse(list(self.engine.rglob('*.pyc')))


if __name__ == '__main__':
    unittest.main()
