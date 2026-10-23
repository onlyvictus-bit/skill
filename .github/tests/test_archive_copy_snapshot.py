"""Copy-based preservation; OS visibility doubles are not cross-account proof."""
import contextlib
import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
try:
    import archive_copy_snapshot as snapshot
except ModuleNotFoundError:
    snapshot = None


def digest(value):
    return hashlib.sha256((json.dumps(value, sort_keys=True, ensure_ascii=True)+'\n').encode()).hexdigest()


class ArchiveCopyTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix='copy-test-'))
        self.source = self.folder / 'archive'; self.source.mkdir()
        (self.source / 'public.txt').write_bytes(b'public')
        secret = self.source / 'restricted'; secret.mkdir()
        (secret / 'data.bin').write_bytes(b'abc')
        (secret / 'empty').mkdir()
        self.session = '7b7f219af07a425185a7ae4adb72a1bc'

    def api(self):
        self.assertIsNotNone(snapshot, 'Fresh-copy preservation has not been implemented')
        return snapshot

    @contextlib.contextmanager
    def normal_visibility(self):
        actual = os.scandir
        def visible(path):
            if Path(path) == self.source / 'restricted':
                raise PermissionError(13, 'controlled normal-account visibility', str(path))
            return actual(path)
        with mock.patch('os.scandir', side_effect=visible):
            yield

    def request(self, phase='BEFORE', binding=None):
        with self.normal_visibility():
            return self.api().scan(self.source, self.session, phase, binding)

    def copied(self, request, name='copy'):
        output = self.folder / name
        self.api().copy_denied(request, output)
        raw = (output / 'Copies.json').read_bytes()
        return output, hashlib.sha256(raw).hexdigest()

    def merged(self, request, output, sha):
        with self.normal_visibility():
            return self.api().merge(request, output, sha)

    def pair(self, mutation=None):
        req = self.request(); copies, sha = self.copied(req)
        before = self.merged(req, copies, sha)
        if mutation: mutation()
        req2 = self.request('AFTER', {'before_sha256': digest(before), 'workload_sha256': 'e'*64})
        copies2, sha2 = self.copied(req2, 'after')
        return before, self.merged(req2, copies2, sha2)

    def test_fresh_copy_resolves_denied_subtree_without_ignoring_it(self):
        req = self.request()
        self.assertEqual(req['unresolved'], {'restricted': 'directory'})
        copies, sha = self.copied(req)
        result = self.merged(req, copies, sha)
        self.assertEqual(result['objects']['restricted/data.bin']['sha256'],
                         'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        self.assertEqual(result['objects']['restricted/empty'], {'kind': 'directory'})
        self.assertFalse(result['producer_authentication'])
        self.assertEqual((copies/'data/restricted/data.bin').read_bytes(), b'abc')
        self.assertEqual((self.source/'restricted/data.bin').read_bytes(), b'abc')

    def test_unchanged_complete_before_after_is_content_preservation_only(self):
        before, after = self.pair()
        result = self.api().compare(before, after)
        self.assertEqual(result['status'], 'CONTENT_MATCH_AT_BEFORE_AFTER_SAMPLES')
        self.assertFalse(result['whole_skill_ready'])
        self.assertFalse(result['producer_authentication'])

    def test_changed_original_is_detected_despite_intact_old_copy(self):
        before, after = self.pair(lambda: (self.source/'restricted/data.bin').write_bytes(b'new'))
        with self.assertRaisesRegex(ValueError, 'CONTENT_CHANGED'):
            self.api().compare(before, after)

    def test_added_original_is_not_hidden_by_snapshot(self):
        before, after = self.pair(lambda: (self.source/'restricted/new.bin').write_bytes(b'new'))
        with self.assertRaisesRegex(ValueError, 'CONTENT_CHANGED'):
            self.api().compare(before, after)

    def test_removed_new_test_original_is_detected(self):
        before, after = self.pair(lambda: (self.source/'restricted/data.bin').unlink())
        with self.assertRaisesRegex(ValueError, 'CONTENT_CHANGED'):
            self.api().compare(before, after)

    def test_original_changed_during_copy_is_not_accepted(self):
        req = self.request()
        real = self.api().read_file
        count = 0
        def moving(path, *args, **kwargs):
            nonlocal count
            row = real(path, *args, **kwargs)
            if Path(path) == self.source/'restricted/data.bin':
                count += 1
                if count == 1: Path(path).write_bytes(b'changed')
            return row
        with mock.patch.object(snapshot, 'read_file', side_effect=moving):
            with self.assertRaisesRegex(ValueError, 'CHANGED'):
                self.api().copy_denied(req, self.folder/'moving')

    def test_both_accounts_denied_remains_blocked(self):
        req = self.request()
        with self.normal_visibility():
            with self.assertRaises(PermissionError):
                self.api().copy_denied(req, self.folder/'failed')
        self.assertFalse((self.folder/'failed/Copies.json').exists())

    def test_tampered_copy_is_rejected(self):
        req = self.request(); copies, sha = self.copied(req)
        (copies/'data/restricted/data.bin').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'COPY_CONTENT'):
            self.merged(req, copies, sha)

    def test_missing_copy_is_rejected(self):
        req = self.request(); copies, sha = self.copied(req)
        (copies/'data/restricted/data.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'COPY_CONTENT'):
            self.merged(req, copies, sha)

    def test_extra_copy_is_rejected(self):
        req = self.request(); copies, sha = self.copied(req)
        (copies/'data/unexpected.bin').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'COPY_CONTENT'):
            self.merged(req, copies, sha)

    def test_before_copy_cannot_be_reused_for_after(self):
        req = self.request(); copies, sha = self.copied(req)
        before = self.merged(req, copies, sha)
        after = self.request('AFTER', {'before_sha256': digest(before), 'workload_sha256': 'e'*64})
        with self.assertRaisesRegex(ValueError, 'COPY_BINDING'):
            self.merged(after, copies, sha)

    def test_wrong_external_copy_hash_is_rejected(self):
        req = self.request(); copies, sha = self.copied(req)
        with self.assertRaisesRegex(ValueError, 'EXTERNAL_HASH'):
            self.merged(req, copies, '0'*64)

    def test_overlapping_unresolved_paths_are_rejected(self):
        req = self.request(); req['unresolved']['restricted/data.bin'] = 'file'
        with self.assertRaisesRegex(ValueError, 'COVERAGE'):
            self.api().copy_denied(req, self.folder/'bad')
        self.assertFalse((self.folder/'bad').exists())

    def test_outside_original_path_is_rejected_before_output(self):
        req = self.request(); req['unresolved']['../outside'] = 'file'
        with self.assertRaisesRegex(ValueError, 'PATH'):
            self.api().copy_denied(req, self.folder/'bad')
        self.assertFalse((self.folder/'bad').exists())

    def test_source_hardlink_is_refused(self):
        self.api()
        os.link(self.source/'public.txt', self.source/'alias.txt')
        with self.assertRaisesRegex(ValueError, 'LINK'):
            snapshot.scan(self.source, self.session, 'BEFORE', None)

    def test_existing_copy_folder_is_never_overwritten(self):
        req = self.request(); copies, sha = self.copied(req)
        old = (copies/'Copies.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.api().copy_denied(req, copies)
        self.assertEqual((copies/'Copies.json').read_bytes(), old)

    def test_snapshot_inside_original_archive_is_refused(self):
        req = self.request()
        with self.assertRaisesRegex(ValueError, 'OUTPUT_SCOPE'):
            self.api().copy_denied(req, self.source/'copies')

    def test_visibility_change_requires_investigation(self):
        req = self.request(); copies, sha = self.copied(req)
        with self.assertRaisesRegex(ValueError, 'VISIBILITY_CHANGED'):
            self.api().merge(req, copies, sha)

    def test_ordinary_io_failure_is_not_treated_as_permission_denial(self):
        self.api()
        with mock.patch('os.scandir', side_effect=OSError('controlled IO failure')):
            with self.assertRaises(OSError):
                snapshot.scan(self.source, self.session, 'BEFORE', None)

    def test_after_requires_before_and_workload_binding(self):
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            self.request('AFTER', None)

    def test_changed_readable_original_during_copy_is_rejected(self):
        req = self.request(); copies, sha = self.copied(req)
        (self.source/'public.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'READABLE_CHANGED'):
            self.merged(req, copies, sha)

    def test_wrong_before_binding_cannot_finalize(self):
        before, after = self.pair()
        after['binding']['before_sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            self.api().compare(before, after)

    def test_same_phase_cannot_finalize(self):
        req = self.request(); copies, sha = self.copied(req)
        before = self.merged(req, copies, sha)
        with self.assertRaisesRegex(ValueError, 'PHASE'):
            self.api().compare(before, before)

    def test_case_aliases_cannot_create_ambiguous_coverage(self):
        req = self.request(); req['unresolved']['RESTRICTED'] = 'directory'
        with self.assertRaisesRegex(ValueError, 'COVERAGE'):
            self.api().copy_denied(req, self.folder/'bad')

    def test_rewritten_file_checks_path_and_handle_times_separately(self):
        self.api()
        path = self.source/'public.txt'
        path.write_bytes(b'updated')
        row = snapshot.read_file(path)
        self.assertEqual(row['size'], 7)
        self.assertEqual(row['sha256'], hashlib.sha256(b'updated').hexdigest())

    def test_redirected_copy_parent_cannot_create_a_directory_outside_workspace(self):
        self.api()
        leaf = self.source/'nest/deep/file.bin'; leaf.parent.mkdir(parents=True)
        leaf.write_bytes(b'payload')
        actual_read = snapshot.read_file
        def denied(path, *args, **kwargs):
            if Path(path) == leaf: raise PermissionError('controlled leaf read denial')
            return actual_read(path,*args,**kwargs)
        with mock.patch.object(snapshot,'read_file',side_effect=denied):
            req = snapshot.scan(self.source,self.session,'BEFORE')
        out = self.folder/'redirected-copy'
        elsewhere = self.folder/'outside'; elsewhere.mkdir()
        actual_collect = snapshot.collect
        planted = False
        def planted_parent(root,*args,**kwargs):
            nonlocal planted
            result = actual_collect(root,*args,**kwargs)
            if Path(root) == leaf and not planted:
                planted = True
                link = out/'data/nest'
                if os.name == 'nt':
                    subprocess.run([r'C:\Windows\System32\cmd.exe','/c','mklink','/J',
                                    str(link),str(elsewhere)],check=True,capture_output=True)
                else: os.symlink(elsewhere,link,target_is_directory=True)
            return result
        with mock.patch.object(snapshot,'collect',side_effect=planted_parent):
            with self.assertRaisesRegex(ValueError,'REDIRECT'):
                snapshot.copy_denied(req,out)
        self.assertFalse((elsewhere/'deep').exists(), 'A rejected redirect still received a write')


if __name__ == '__main__':
    unittest.main()
