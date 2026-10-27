"""Current-source successor boundaries; only new scratch fixtures are mutated."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).absolute().parents[2]
SCRIPT = ROOT/'.github/scripts/gate1_current_preflight.py'


def subject():
    if not SCRIPT.exists():
        raise AssertionError('Current-source preflight is not implemented')
    spec = importlib.util.spec_from_file_location('current_preflight_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def archive(items):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as stream:
        for name, raw in items:
            stream.writestr(name, raw)
    return output.getvalue()


def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


class CurrentPreflight(unittest.TestCase):
    def setUp(self):
        self.g = subject()

    def test_read_checks_path_and_handle_without_equating_windows_ctime_roles(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'retained'; path.write_bytes(b'original')
            os.utime(path, (1000000000, 1000000000))
            self.assertEqual(self.g.read_file(path), b'original')

    def test_pinned_system_executable_uses_type_identity_not_filename_execute_bits(self):
        git = Path(r'C:\Program Files\Git\cmd\git.exe')
        self.assertEqual(hashlib.sha256(self.g.read_file(git, 2)).hexdigest(),
                         'da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f')
        with self.assertRaises(ValueError): self.g.read_file(git)

    def test_clean_extract_matches_exact_git_blobs_and_preserves_archive(self):
        raw = archive([('memory-integrity/a.py', b'print(120)\n'), ('claude-mon/b.txt', b'pair')])
        tree = {'memory-integrity/a.py': blob(b'print(120)\n'), 'claude-mon/b.txt': blob(b'pair')}
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            self.g.extract_source(raw, tree, dest)
            self.assertEqual((dest/'memory-integrity/a.py').read_bytes(), b'print(120)\n')
            self.assertEqual((dest/'claude-mon/b.txt').stat().st_nlink, 1)
            self.assertEqual(set(self.g.source_manifest(dest)), set(tree))

    def test_real_current_commit_extracts_without_old_caches_or_overlay(self):
        raw, tree, expected = self.g.committed_source()
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            self.g.extract_source(raw, tree, dest)
            self.assertEqual(len(tree), 627)
            self.g.verify_source(dest, expected)
            self.assertEqual(set(self.g.source_manifest(dest)), set(tree))
            self.assertFalse((dest/'.git').exists())
            self.assertFalse((dest/'memory-integrity/%SystemDrive%').exists())

    def test_wrong_blob_missing_file_or_extra_member_refuses_before_creation(self):
        cases = [({'a': blob(b'right')}, [('a', b'wrong')]),
                 ({'a': blob(b'right')}, []),
                 ({'a': blob(b'right')}, [('a', b'right'), ('b', b'extra')])]
        with tempfile.TemporaryDirectory() as folder:
            for index, (tree, rows) in enumerate(cases):
                dest = Path(folder)/str(index)
                with self.subTest(index=index), self.assertRaises(ValueError):
                    self.g.extract_source(archive(rows), tree, dest)
                self.assertFalse(dest.exists())

    def test_traversal_windows_alias_or_case_collision_refuses_before_creation(self):
        for names in (('../escape',), ('C:/escape',), ('a\\b',), ('A', 'a'), ('NUL.txt',), ('a.',)):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as folder:
                rows = [(name, b'x') for name in names]
                dest = Path(folder)/'source'
                with self.assertRaises(ValueError):
                    self.g.extract_source(archive(rows), {name: blob(b'x') for name in names}, dest)
                self.assertFalse(dest.exists())

    def test_case_colliding_directory_prefix_refuses_before_any_write(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            rows = [('A/b', b'b'), ('a/c', b'c')]
            with self.assertRaises(ValueError):
                self.g.extract_source(archive(rows), {name: blob(raw) for name, raw in rows}, dest)
            self.assertFalse(dest.exists())

    def test_untracked_empty_archive_directory_refuses_before_any_write(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            raw = archive([('a', b'kept'), ('unexpected/', b'')])
            with self.assertRaises(ValueError):
                self.g.extract_source(raw, {'a': blob(b'kept')}, dest)
            self.assertFalse(dest.exists())

    def test_extra_empty_directory_in_clean_copy_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            self.g.extract_source(archive([('a', b'abc')]), {'a': blob(b'abc')}, dest)
            (dest/'unexpected').mkdir()
            with self.assertRaises(ValueError):
                self.g.verify_source(dest, {'a': hashlib.sha256(b'abc').hexdigest()})

    def test_interrupted_copy_leaves_partial_output_and_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'; rows = [('first', b'one'), ('second', b'two')]
            raw = archive(rows); tree = {name: blob(data) for name, data in rows}
            original_open = Path.open
            def fail_second(path, mode='r', *args, **kwargs):
                if path == dest/'second' and mode == 'xb': raise OSError('controlled interrupted copy')
                return original_open(path, mode, *args, **kwargs)
            with patch.object(Path, 'open', fail_second), self.assertRaises(OSError):
                self.g.extract_source(raw, tree, dest)
            self.assertEqual((dest/'first').read_bytes(), b'one')
            self.assertFalse((dest/'Prepared.json').exists())
            with self.assertRaises(ValueError): self.g.extract_source(raw, tree, dest)
            self.assertEqual((dest/'first').read_bytes(), b'one')

    def test_final_preservation_failure_cannot_publish_prepared_success(self):
        self.assertTrue(hasattr(self.g, 'finalize_result'), 'No guarded final success publication yet')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            receipt = {'status': 'PARTIAL_OR_FAILED_NO_RETRY', 'failure': None}
            def changed(): raise ValueError('controlled final preservation mismatch')
            self.g.finalize_result(output, receipt, {'candidate': 'unaccepted'}, changed)
            self.assertFalse((output/'Prepared.json').exists())
            self.assertNotIn('prepared', receipt)
            retained = json.loads((output/'Receipt.json').read_bytes())
            self.assertEqual(retained['status'], 'PARTIAL_OR_FAILED_NO_RETRY')
            self.assertIn('controlled final preservation mismatch', retained['preservation_failure'])

    def test_success_requires_final_check_and_matching_prepared_receipt(self):
        self.assertTrue(hasattr(self.g, 'finalize_result'), 'No guarded final success publication yet')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder); receipt = {'status': 'PARTIAL_OR_FAILED_NO_RETRY', 'failure': None}
            checks = []
            self.g.finalize_result(output, receipt, {'candidate': 'verified'}, lambda: checks.append('checked'))
            self.assertEqual(checks, ['checked'])
            raw = (output/'Prepared.json').read_bytes()
            retained = json.loads((output/'Receipt.json').read_bytes())
            self.assertEqual(retained['prepared']['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(retained['status'], 'STEP1_SOURCE_AND_ENVIRONMENT_VERIFIED_NOT_GATE1')

    def test_pre_copy_failure_retained_once_without_source_or_prepared(self):
        self.assertTrue(hasattr(self.g, 'retain_preflight_failure'), 'No retained pre-copy failure yet')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); destination = root/'Preflight-Failure.json'
            self.g.retain_preflight_failure(destination, 'controlled input failure')
            raw = destination.read_bytes(); value = json.loads(raw)
            self.assertEqual(value['status'], 'C1_PREFLIGHT_FAILED_NO_SOURCE_OR_RETRIEVAL')
            self.assertFalse(value['gate1_complete'])
            self.assertEqual(value['failure'], 'controlled input failure')
            self.assertFalse((root/'source').exists())
            self.assertFalse((root/'Prepared.json').exists())
            with self.assertRaises(FileExistsError):
                self.g.retain_preflight_failure(destination, 'second invocation')
            self.assertEqual(destination.read_bytes(), raw)

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'; dest.mkdir()
            (dest/'keep').write_bytes(b'original')
            with self.assertRaises(ValueError):
                self.g.extract_source(archive([('new', b'x')]), {'new': blob(b'x')}, dest)
            self.assertEqual((dest/'keep').read_bytes(), b'original')
            self.assertFalse((dest/'new').exists())

    def test_changed_added_missing_copy_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder)/'source'
            self.g.extract_source(archive([('a', b'abc')]), {'a': blob(b'abc')}, dest)
            expected = {'a': hashlib.sha256(b'abc').hexdigest()}
            self.g.verify_source(dest, expected)
            (dest/'a').write_bytes(b'changed')
            with self.assertRaises(ValueError): self.g.verify_source(dest, expected)
            (dest/'a').write_bytes(b'abc'); (dest/'extra').write_bytes(b'x')
            with self.assertRaises(ValueError): self.g.verify_source(dest, expected)
            with self.assertRaises(ValueError): self.g.verify_source(dest, {'missing': expected['a']})

    def test_authoritative_hardlink_is_rejected_without_changing_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'a').write_bytes(b'keep')
            os.link(root/'a', root/'alias')
            with self.assertRaises(ValueError): self.g.source_manifest(root)
            self.assertEqual((root/'a').read_bytes(), b'keep')
            self.assertEqual((root/'a').stat().st_nlink, 2)

    def test_failed_child_exposes_stderr_not_secondary_json_error(self):
        with self.assertRaisesRegex(ValueError, 'CHILD_FAILED.*ownership refused'):
            self.g.parse_child({'exit_code': 128, 'complete': True}, b'', b'ownership refused')

    def test_incomplete_capture_and_non_json_are_not_success(self):
        for meta, raw in [({'exit_code': 0, 'complete': False}, b'{}'),
                          ({'exit_code': 0, 'complete': True}, b'')]:
            with self.subTest(meta=meta, raw=raw), self.assertRaises(ValueError):
                self.g.parse_child(meta, raw, b'')

    def test_dependency_version_extra_missing_and_revision_mismatch_refuse(self):
        expected = {'numpy': '2.5.3', 'semantica': '0.7.0'}
        good = {'versions': expected, 'revision': self.g.REVISION, 'user_site': False}
        self.g.validate_dependencies(good, expected)
        for field, value in [('versions', {'numpy': '1.0', 'semantica': '0.7.0'}),
                             ('versions', {'numpy': '2.5.3'}), ('revision', 'wrong'), ('user_site', True)]:
            wrong = copy.deepcopy(good); wrong[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.g.validate_dependencies(wrong, expected)

    def test_runtime_uses_observed_store_image_and_case_insensitive_environment(self):
        image = self.g.load_support('gate1_image_successor')
        env = {'USERPROFILE': r'C:\Users\sakth', 'SYSTEMDRIVE': 'C:', 'PATH': 'existing'}
        expected = image.runtime_expectation(env, Path(r'C:\scratch'))
        self.g.validate_runtime(expected, env, Path(r'C:\scratch'))
        wrong = copy.deepcopy(expected); wrong['image_path'] = str(image.g.BASE)
        with self.assertRaises(ValueError): self.g.validate_runtime(wrong, env, Path(r'C:\scratch'))


if __name__ == '__main__':
    unittest.main()
