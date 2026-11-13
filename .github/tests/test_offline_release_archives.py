"""Release archive controls against the exact accepted source; retain all fixtures."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]


class ReadOnlyConsumer(unittest.TestCase):
    def test_consumer_import_never_writes_bytecode_without_cli_B(self):
        import sys
        spec = importlib.util.spec_from_file_location('consumer_check_build', ROOT/'release/Build-Offline-First.py')
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
        root = Path(tempfile.mkdtemp(prefix='consumer-readonly-'))/'memory-integrity'
        module = root/'scripts/integrity_v2/release_content.py'
        module.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/'memory-integrity/scripts/integrity_v2/release_content.py', module)
        before = sorted(str(p.relative_to(root)) for p in root.rglob('*'))
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = False
            b.consumer(root)
        finally:
            sys.dont_write_bytecode = previous
        self.assertEqual(before, sorted(str(p.relative_to(root)) for p in root.rglob('*')))


class OfflineArchives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('archive_verifier', ROOT/'release/Verify-Offline-First.py')
        cls.v = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.v)
        cls.b = cls.v.b
        cls.base = Path(tempfile.mkdtemp(prefix='archive-controls-'))
        cls.source = cls.base/'source'
        cls.source.mkdir()
        for package in cls.b.PACKAGES:
            # Fixtures must not copy untracked runtime caches or private files.
            names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', '--', package])
            for raw in names.split(b'\0'):
                if raw:
                    rel = raw.decode('utf-8')
                    if rel == package + '/' + cls.b.ACTIVE:
                        continue  # Derived delivery manifest is tested separately below.
                    target = cls.source/rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT/rel, target)
        cls.blobs = {}
        for package in cls.b.PACKAGES:
            cls.blobs[package] = {}
            for rel in cls.b.inventory(cls.source/package):
                raw = (cls.source/package/rel).read_bytes()
                cls.blobs[package][rel] = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        # Replace only the external Git inventory; actual byte/source/ZIP validation runs.
        cls.git = patch.object(cls.b, 'git_packages', return_value=cls.blobs)
        cls.git.start()
        cls.addClassCleanup(cls.git.stop)
        cls.release = cls.base/'release'
        cls.manifest = cls.b.build(cls.source, 'a'*40, cls.release)

    def folder(self, label):
        return Path(tempfile.mkdtemp(prefix=label+'-', dir=self.base))

    def test_deterministic_success_and_fresh_extraction(self):
        second = self.folder('deterministic')/'new'
        result = self.b.build(self.source, 'a'*40, second)
        self.assertEqual(result, self.manifest)
        for name in self.b.PACKAGES:
            filename = result['packages'][name]['zip']
            self.assertEqual((self.release/filename).read_bytes(), (second/filename).read_bytes())
            with zipfile.ZipFile(second/filename) as z:
                self.assertTrue(all(i.date_time == (2026, 11, 13, 0, 0, 0) and
                                    i.external_attr >> 16 == 0o100644 for i in z.infolist()))
        report = self.v.verify(second, self.folder('verified')/'new', self.source)
        self.assertEqual(report['status'], 'PAIR_ARCHIVE_AND_EXTRACTION_VERIFIED')
        self.assertFalse(report['runtime_verified'])

    def test_build_and_verify_refuse_existing_output(self):
        with self.assertRaisesRegex(ValueError, 'OUTPUT_EXISTS'):
            self.b.build(self.source, 'a'*40, self.release)
        with self.assertRaisesRegex(ValueError, 'OUTPUT_EXISTS'):
            self.v.verify(self.release, self.folder('existing'), self.source)

    def active_source(self):
        source = self.folder('active-source')/'source'
        shutil.copytree(self.source, source)
        for name in self.b.PACKAGES:
            (source/name/self.b.ACTIVE).write_bytes(
                self.b.canonical(self.b.consumer(source/name).content_document(source/name)) + b'\n')
        return source

    def test_active_delivery_manifests_preserve_qualified_archive_bytes(self):
        source = self.active_source()
        out = self.folder('active-build')/'new'
        self.assertEqual(self.b.build(source, 'a'*40, out), self.manifest)
        for row in self.manifest['packages'].values():
            self.assertEqual((out/row['zip']).read_bytes(), (self.release/row['zip']).read_bytes())
        self.assertEqual(self.v.verify(out, self.folder('active-verify')/'new', source)['status'],
                         'PAIR_ARCHIVE_AND_EXTRACTION_VERIFIED')

    def test_active_manifest_tamper_noncanonical_and_unknown_extensions_refused(self):
        for mode in ('malformed', 'noncanonical', 'tamper', 'extra', 'case'):
            with self.subTest(mode=mode):
                source = self.active_source()
                path = source/'memory-integrity'/self.b.ACTIVE
                if mode == 'malformed':
                    path.write_bytes(b'{')
                elif mode == 'noncanonical':
                    path.write_bytes(path.read_bytes() + b' ')
                elif mode == 'tamper':
                    value = self.b.read(path.read_bytes());value['files']['SKILL.md'] = '0'*64
                    path.write_bytes(self.b.canonical(value) + b'\n')
                else:
                    (source/'memory-integrity'/('extra.txt' if mode == 'extra' else
                                               'tests_v2/offline1-content.json')).write_bytes(b'bad')
                with self.assertRaises(ValueError):
                    self.b.source_check(source, 'a'*40)

    def test_active_manifest_hardlink_refused_before_read(self):
        import os
        source = self.active_source()
        os.link(source/'memory-integrity'/self.b.ACTIVE, self.folder('active-alias')/'alias')
        with self.assertRaisesRegex(ValueError, 'NONORDINARY_FILE'):
            self.b.source_check(source, 'a'*40)

    def test_source_drift_rejected_by_git_blob_binding(self):
        altered = self.folder('source-drift')/'source'
        shutil.copytree(self.source, altered)
        with (altered/'memory-integrity/SKILL.md').open('ab') as f:
            f.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'SOURCE_BYTES'):
            self.b.source_check(altered, 'a'*40)

    def test_source_link_rejected(self):
        altered = self.folder('source-link')/'source'
        shutil.copytree(self.source, altered)
        import os
        os.link(altered/'memory-integrity/SKILL.md', altered/'memory-integrity/linked.md')
        with self.assertRaisesRegex(ValueError, 'NONORDINARY_FILE'):
            self.b.inventory(altered/'memory-integrity')

    def test_duplicate_json_and_nonfinite_json_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                self.b.read(raw)

    def test_windows_and_traversal_member_aliases_rejected(self):
        for name in ('../escape', '/absolute', 'p\\bad', 'p/C:bad', 'p/CON.txt',
                     'p/LPT1', 'p/NUL', 'p/trailing.', 'p/trailing ', 'p//empty'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.b.safe_name(name)
        self.assertEqual(self.b.safe_name('complete_read_v2/contracts.py'),
                         'complete_read_v2/contracts.py')

    def altered_release(self, mode):
        folder = self.folder('tampered')
        for path in self.release.iterdir():
            shutil.copyfile(path, folder/path.name)
        m = self.b.read((folder/'Offline-First-Release-Manifest.json').read_bytes())
        row = m['packages']['memory-integrity']
        archive = folder/row['zip']
        with zipfile.ZipFile(archive) as z:
            members = [(i, z.read(i)) for i in z.infolist()]
        if mode == 'missing':
            members.pop()
        elif mode in ('duplicate', 'case', 'traversal', 'device', 'symlink', 'extra'):
            old, data = members[0]
            names = {'duplicate': old.filename, 'case': old.filename.upper(),
                     'traversal': '../escape', 'device': 'memory-integrity/CON.txt',
                     'symlink': 'memory-integrity/link', 'extra': 'memory-integrity/extra'}
            i = zipfile.ZipInfo(names[mode]);i.external_attr = (0o120777 if mode == 'symlink' else 0o100644) << 16
            members.append((i, data))
        with zipfile.ZipFile(archive, 'w') as z:
            for i, data in members:
                z.writestr(i, data)
        row.update(sha256=self.b.sha(archive.read_bytes()), bytes=archive.stat().st_size,
                   entries=len(members))
        (folder/'Offline-First-Release-Manifest.json').write_bytes(self.b.canonical(m))
        return folder

    def test_unsafe_duplicate_and_case_members_rejected_even_with_updated_zip_hash(self):
        for mode in ('duplicate', 'case', 'traversal', 'device', 'symlink'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                folder = self.altered_release(mode)
                self.v.verify(folder, folder/'verification', self.source)

    def test_missing_extra_members_rejected_even_with_updated_zip_hash(self):
        for mode in ('missing', 'extra'):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'PACKAGE_SOURCE_CLOSURE'):
                folder = self.altered_release(mode)
                self.v.verify(folder, folder/'verification', self.source)

    def test_archive_hash_tamper_rejected(self):
        folder = self.folder('zip-hash')
        for p in self.release.iterdir():
            shutil.copyfile(p, folder/p.name)
        with (folder/'memory-integrity-offline-v1.zip').open('ab') as f:
            f.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'ARCHIVE_HASH'):
            self.v.verify(folder, folder/'verification', self.source)

    def test_wrong_companion_pin_rejected(self):
        source = self.folder('wrong-pair')/'source'
        shutil.copytree(self.source, source)
        path = source/'memory-integrity/scripts/memory_integrity_v2.py'
        raw = path.read_bytes().replace(self.manifest['pair_contract']['schema_digest'].encode(), b'0'*64)
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'COMPANION_PIN'):
            self.b.pair_contract(source)


if __name__ == '__main__':
    unittest.main()
