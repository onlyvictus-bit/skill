"""Failure-first contracts for the bounded extended timing recorder.

The recorder observes a diagnostic copy only.  These tests deliberately use
ordinary temporary files and never start the selected retrieval runtime.
"""
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
import uuid


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
RETAINED = SCRIPTS.parent / 'run-artifacts' / 'extended-timing-tests-20261023'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    import extended_timing_log as timing
except ModuleNotFoundError:
    timing = None


class ExtendedTimingLogContracts(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(timing, 'The extended per-file timing recorder has not been implemented')
        return importlib.reload(timing)

    @contextlib.contextmanager
    def configured(self, budget=120):
        recorder = self.api()
        RETAINED.mkdir(parents=True, exist_ok=True)
        base = RETAINED / ('case-' + uuid.uuid4().hex)
        base.mkdir()
        watched = base / 'watched'
        watched.mkdir()
        root = base / 'exclusive-events'
        root.mkdir()
        recorder.configure(root, [watched], budget=budget)
        yield recorder, base, watched, root

    def records(self, root):
        rows = []
        for path in sorted(root.glob('*.jsonl')):
            with path.open('rb') as stream:
                rows.extend(json.loads(line.decode('utf-8')) for line in stream if line.strip())
        return rows

    def test_span_records_exact_start_end_without_stdout_or_retained_handle(self):
        recorder = self.api()
        with self.configured() as (recorder, _base, _watched, root):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with recorder.span('community-search', mode='community'):
                    pass
            self.assertEqual((out.getvalue(), err.getvalue()), ('', ''))
            rows = self.records(root)
            self.assertEqual([(r['event'], r['action']) for r in rows],
                             [('START', 'community-search'), ('END', 'community-search')])
            start, end = rows
            self.assertEqual(start['span'], end['span'])
            self.assertEqual(start['pid'], os.getpid())
            self.assertEqual(end['status'], 'RETURNED')
            self.assertIsInstance(start['utc'], str)
            self.assertIsInstance(end['utc'], str)
            self.assertGreaterEqual(end['duration_ns'], 0)
            self.assertGreaterEqual(end['monotonic_ns'], start['monotonic_ns'])
            self.assertGreaterEqual(end['cpu_ns'], start['cpu_ns'])
            self.assertFalse(hasattr(recorder, '_open_log_handle'))
            self.assertEqual(len(list(root.glob('*.jsonl'))), 1)

    def test_span_propagates_original_exception_and_marks_it(self):
        with self.configured() as (recorder, _base, _watched, root):
            original = LookupError('original')
            with self.assertRaises(LookupError) as caught:
                with recorder.span('community-search'):
                    raise original
            self.assertIs(caught.exception, original)
            rows = self.records(root)
            self.assertEqual(rows[-1]['status'], 'EXCEPTION')
            self.assertEqual(rows[-1]['error_type'], 'LookupError')

    def test_read_and_exact_digest_association_are_per_byte_object_not_same_size_guess(self):
        with self.configured() as (recorder, _base, watched, root):
            first = watched / 'first.txt'
            second = watched / 'second.txt'
            first.write_bytes(b'abcd')
            second.write_bytes(b'wxyz')
            one = recorder.read_bytes(first)
            two = recorder.read_bytes(second)
            self.assertEqual(recorder.digest(hashlib.sha256, one).hexdigest(), hashlib.sha256(one).hexdigest())
            unrelated_same_size = bytes(bytearray(two))
            self.assertEqual(recorder.digest(hashlib.sha256, unrelated_same_size).hexdigest(), hashlib.sha256(two).hexdigest())
            digest_rows = [r for r in self.records(root) if r['action'] == 'digest' and r['event'] == 'END']
            self.assertEqual(digest_rows[0]['path'], str(first.resolve()))
            self.assertNotIn('path', digest_rows[1], 'A same-sized different bytes object must not be guessed')
            reads = [r for r in self.records(root) if r['action'] == 'file-read-bytes' and r['event'] == 'END']
            self.assertEqual([r['bytes'] for r in reads], [4, 4])

    def test_text_read_records_bytes_but_unwatched_read_is_not_noisily_logged(self):
        with self.configured() as (recorder, base, watched, root):
            text = watched / 'source.txt'
            text.write_text('hello\n', encoding='utf-8')
            outside = base / 'library.txt'
            outside.write_text('library', encoding='utf-8')
            self.assertEqual(recorder.read_text(text, encoding='utf-8'), 'hello\n')
            self.assertEqual(recorder.read_text(outside, encoding='utf-8'), 'library')
            rows = self.records(root)
            ends = [r for r in rows if r['action'] == 'file-read-text' and r['event'] == 'END']
            self.assertEqual(len(ends), 1)
            self.assertEqual(ends[0]['path'], str(text.resolve()))
            self.assertEqual(ends[0]['bytes'], text.stat().st_size)

    def test_table_retains_physical_bytes_digest_and_exception_type(self):
        with self.configured() as (recorder, _base, watched, root):
            target = watched/'data.txt'; target.write_bytes(b'abc')
            value = recorder.read_bytes(target)
            recorder.digest(lambda raw: hashlib.sha256(raw).hexdigest(), value)
            with self.assertRaises(LookupError):
                with recorder.span('deliberate-failure'):
                    raise LookupError('retained')
            rows = recorder.summarize(list(root.glob('*.jsonl')))
            by_action = {r['action']:r for r in rows}
            self.assertEqual(by_action['file-read-bytes'].get('bytes'), 3)
            self.assertEqual(by_action['digest'].get('sha256'), hashlib.sha256(b'abc').hexdigest())
            self.assertEqual(by_action['deliberate-failure'].get('error_type'), 'LookupError')

    def test_append_refuses_replaced_log_without_touching_the_replacement(self):
        with self.configured() as (recorder, _base, _watched, root):
            with recorder.span('first'):
                pass
            target = root/(str(os.getpid())+'.jsonl')
            target.rename(root/'retained-original.jsonl')
            target.write_bytes(b'replacement-must-stay-unchanged\n')
            with self.assertRaisesRegex(recorder.TimingLogError, 'IDENTITY|LOG_WRITE'):
                with recorder.span('must-refuse'):
                    pass
            self.assertEqual(target.read_bytes(), b'replacement-must-stay-unchanged\n')

    def test_invalid_completion_status_is_not_a_valid_timing_row(self):
        with self.configured() as (recorder, _base, _watched, root):
            with recorder.span('first'):
                pass
            rows = self.records(root)
            rows[-1]['status'] = 'SUCCESS_WITHOUT_END'
            with self.assertRaisesRegex(ValueError, 'MALFORMED'):
                recorder.summarize(rows)

    def test_lookup_times_the_original_validator_without_claiming_global_search(self):
        with self.configured() as (recorder, _base, watched, root):
            target = watched / 'item.txt'
            target.write_text('ok', encoding='utf-8')
            def validate(root_arg, relative):
                self.assertEqual(root_arg, watched)
                return root_arg / relative
            self.assertEqual(recorder.locate(validate, watched, 'item.txt'), target)
            rows = [r for r in self.records(root) if r['action'] == 'path-validation']
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(r['details']['scope'] == 'validator-only' for r in rows))
            self.assertEqual(rows[-1]['path'], str(target.resolve()))

    def test_source_unit_reopen_decorator_derives_path_and_unit_id(self):
        with self.configured() as (recorder, _base, watched, root):
            source = watched / 'code.py'
            source.write_text('x=1\n', encoding='utf-8')
            doc = {'sources': {'s1': {'path': 'code.py'}}}
            ref = {'source_id': 's1', 'unit_id': 'u9'}
            @recorder.traced('source-unit-reopen')
            def reopen(document, project_root, source_ref):
                return {'ok': document is doc and project_root == watched and source_ref == ref}
            self.assertEqual(reopen(doc, watched, ref), {'ok': True})
            end = [r for r in self.records(root) if r['event'] == 'END'][-1]
            self.assertEqual(end['path'], str(source.resolve()))
            self.assertEqual(end['details']['unit_id'], 'u9')

    def test_summarize_preserves_unfinished_and_does_not_add_parallel_or_nested_times(self):
        recorder = self.api()
        rows = [
            {'schema': 1, 'event': 'START', 'pid': 1, 'thread': 1, 'span': 1, 'action': 'outer',
             'utc': '2026-10-23T00:00:00+00:00', 'monotonic_ns': 10, 'cpu_ns': 1, 'status': 'STARTED'},
            {'schema': 1, 'event': 'START', 'pid': 1, 'thread': 1, 'span': 2, 'action': 'inner',
             'utc': '2026-10-23T00:00:00+00:00', 'monotonic_ns': 20, 'cpu_ns': 2, 'status': 'STARTED'},
            {'schema': 1, 'event': 'END', 'pid': 1, 'thread': 1, 'span': 2, 'action': 'inner',
             'utc': '2026-10-23T00:00:00+00:00', 'monotonic_ns': 30, 'cpu_ns': 3, 'duration_ns': 10,
             'status': 'RETURNED'},
            {'schema': 1, 'event': 'START', 'pid': 2, 'thread': 2, 'span': 1, 'action': 'parallel',
             'utc': '2026-10-23T00:00:00+00:00', 'monotonic_ns': 15, 'cpu_ns': 1, 'status': 'STARTED'},
            {'schema': 1, 'event': 'END', 'pid': 2, 'thread': 2, 'span': 1, 'action': 'parallel',
             'utc': '2026-10-23T00:00:00+00:00', 'monotonic_ns': 25, 'cpu_ns': 2, 'duration_ns': 10,
             'status': 'RETURNED'},
        ]
        table = recorder.summarize(rows)
        by_action = {r['action']: r for r in table}
        self.assertEqual(by_action['outer']['status'], 'UNFINISHED')
        self.assertIsNone(by_action['outer']['duration_ns'])
        self.assertEqual(by_action['inner']['duration_ns'], 10)
        self.assertEqual(by_action['inner']['duration_seconds'], 0.00000001)
        self.assertEqual(by_action['parallel']['duration_ns'], 10)
        self.assertNotIn('total_duration_ns', by_action['inner'])
        malformed = rows + [dict(rows[2])]
        with self.assertRaisesRegex(ValueError, 'DUPLICATE|PAIR|MALFORMED'):
            recorder.summarize(malformed)

    def test_configure_is_idempotent_only_for_same_context_and_never_overwrites_existing_log(self):
        recorder = self.api()
        RETAINED.mkdir(parents=True, exist_ok=True)
        base = RETAINED / ('config-' + uuid.uuid4().hex)
        base.mkdir(); watched = base / 'watched'; watched.mkdir()
        root = base / 'exclusive'; root.mkdir()
        recorder.configure(root, [watched], budget=120)
        recorder.configure(root, [watched], budget=120)
        with self.assertRaisesRegex(ValueError, 'CONFIG'):
            recorder.configure(root, [watched], budget=121)
        target = root / (str(os.getpid()) + '.jsonl')
        target.write_bytes(b'already-present\n')
        with self.assertRaisesRegex(recorder.TimingLogError, 'LOG_WRITE:FileExistsError'):
            with recorder.span('must-not-overwrite'):
                pass
        self.assertEqual(target.read_bytes(), b'already-present\n')


if __name__ == '__main__':
    unittest.main()
