"""Delivery CI keeps the qualified pair and historical authority fail closed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('ci_release_check', ROOT/'release/Check-Offline-First-CI.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class HistoricalAuthority(unittest.TestCase):
    def fixture(self):
        root = Path(tempfile.mkdtemp(prefix='offline-history-'))
        (root/'release').mkdir()
        authority = c.b.read((ROOT/'release/Offline-First-Historical-Hashes.json').read_bytes())
        for name in (*authority['files'], 'release/Offline-First-Historical-Hashes.json'):
            shutil.copyfile(ROOT/name, root/name)
        return root, authority

    def test_complete_real_authority_matches_pinned_git_objects(self):
        root, authority = self.fixture()
        self.assertEqual(c.historical(root, ROOT), authority['files'])

    def test_rebaselining_authority_cannot_hide_old_release_mutation(self):
        root, authority = self.fixture()
        name = next(iter(authority['files']))
        raw = (root/name).read_bytes() + b'changed'
        (root/name).write_bytes(raw)
        authority['files'][name] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
        (root/'release/Offline-First-Historical-Hashes.json').write_bytes(c.b.canonical(authority))
        with self.assertRaisesRegex(ValueError, 'HISTORICAL_DRIFT'):
            c.historical(root, ROOT)

    def test_missing_file_and_extra_authority_are_refused(self):
        root, authority = self.fixture()
        authority['files']['release/unknown.zip'] = {'bytes': 0, 'sha256': '0'*64}
        (root/'release/Offline-First-Historical-Hashes.json').write_bytes(c.b.canonical(authority))
        with self.assertRaisesRegex(ValueError, 'HISTORICAL_SET'):
            c.historical(root, ROOT)
        authority['source_commit'] = '0'*40
        (root/'release/Offline-First-Historical-Hashes.json').write_bytes(c.b.canonical(authority))
        with self.assertRaisesRegex(ValueError, 'HISTORICAL_AUTHORITY'):
            c.historical(root, ROOT)


class WorkflowMigration(unittest.TestCase):
    def test_both_workflows_bind_exact_source_and_fresh_extraction(self):
        for filename in ('ci.yml', 'knowledge-runtime.yml'):
            with self.subTest(filename=filename):
                text = (ROOT/'.github/workflows'/filename).read_text()
                self.assertIn('fetch-depth: 0', text)
                self.assertIn('Check-Offline-First-CI.py', text)
                self.assertIn('offline_ci_suite.py', text)
                self.assertIn('verified/extracted', text)
                self.assertIn('PYTHONNOUSERSITE: "1"', text)
                self.assertIn('if: always()', text)
                self.assertIn('github.sha', text)
                for obsolete in ('Verify-Knowledge-Bridge.py', 'Verify-Memory-Integrity-R3.py',
                                 'Verify-Memory-Integrity-R4.py'):
                    self.assertNotIn(obsolete, text)
        text = (ROOT/'.github/workflows/knowledge-runtime.yml').read_text()
        self.assertIn('offline_release_acceptance.py', text)
        self.assertIn('Source runtime', text)
        self.assertIn('Fresh extracted runtime', text)
        self.assertEqual(text.count("subprocess.run([str(worker), '-B', '.github/scripts/offline_ci_suite.py'"), 2)
        self.assertIn("subprocess.run([str(worker), '-B', '.github/scripts/offline_release_acceptance.py'", text)

    def test_release_manifest_and_zip_pins_are_qualified_values(self):
        self.assertEqual(c.ACCEPTED, 'a2a28bf547a9c3e187c89eb6aee9f0b6bd822956')
        self.assertEqual(len(c.QUALIFIED), 3)
        for name, digest in c.QUALIFIED.items():
            self.assertEqual(hashlib.sha256((ROOT/'release'/name).read_bytes()).hexdigest(), digest)

    def test_compatibility_successor_has_separate_source_and_exact_pair_pins(self):
        self.assertEqual(c.DELIVERY_BASE, '1076e02c36e59ada0f455bd2c2612bf0ef811e94')
        self.assertEqual(c.DELIVERY_DIRECTORY, 'release/offline-compat-20261115')
        self.assertEqual(set(c.DELIVERY), set(c.QUALIFIED))
        for name, digest in c.DELIVERY.items():
            self.assertEqual(hashlib.sha256((ROOT/c.DELIVERY_DIRECTORY/name).read_bytes()).hexdigest(), digest)
        doc=c.b.read((ROOT/c.DELIVERY_DIRECTORY/'Offline-First-Release-Manifest.json').read_bytes())
        self.assertEqual(doc['source_commit'],c.DELIVERY_BASE)
        self.assertNotEqual(c.DELIVERY['memory-integrity-offline-v1.zip'], c.QUALIFIED['memory-integrity-offline-v1.zip'])
        self.assertEqual(c.DELIVERY['claude-mon-offline-v1.zip'], c.QUALIFIED['claude-mon-offline-v1.zip'])

    def test_byte_rebuild_is_mandatory_on_qualified_windows_toolchain(self):
        text = (ROOT/'.github/workflows/ci.yml').read_text()
        self.assertIn('  reproducible-pair:', text)
        self.assertIn('runs-on: windows-latest', text)
        self.assertIn('python-version: "3.14.10"', text)
        self.assertIn('Check-Offline-First-CI.py --rebuild-exact', text)
        self.assertIn('REPRODUCIBLE_HASH:', (ROOT/'release/Check-Offline-First-CI.py').read_text())

    def test_core_uses_clean_nonredirected_stdlib_interpreter_without_install(self):
        text=(ROOT/'.github/workflows/ci.yml').read_text()
        self.assertIn("'-m', 'venv', '--copies', '--without-pip'",text)
        self.assertIn("os.environ['GITHUB_PATH']",text)


if __name__ == '__main__':
    unittest.main()
