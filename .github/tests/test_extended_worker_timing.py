"""Diagnostic-only budget, source preservation and overlay wiring controls."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).absolute().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
try:
    timing = importlib.import_module('extended_worker_timing')
except ModuleNotFoundError:
    timing = None


class ExtendedTimingTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(timing, 'Extended-time diagnostic is not implemented')

    def test_search_command_selects_supported_budget_without_changing_source(self):
        args = timing.search_argv(Path(sys.executable), Path('copy'), Path('fixture'),
                                  Path('pack.json'), 'community', 'single', Path(sys.executable))
        self.assertEqual(args[args.index('--worker-timeout') + 1], '120')
        self.assertEqual(args[args.index('--strategy') + 1], 'community')
        self.assertEqual(args[args.index('--execution') + 1], 'single')

    def test_invalid_case_cannot_be_silently_run(self):
        with self.assertRaisesRegex(ValueError, 'CASE'):
            timing.search_argv(Path(sys.executable), Path('copy'), Path('fixture'),
                               Path('pack.json'), 'global', 'distributed-local', Path(sys.executable))

    def test_empty_worker_trace_is_not_an_observed_search(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'events').mkdir()
            with self.assertRaisesRegex(ValueError, 'MISSING_WORKER'):
                timing.observer_rows(root)

    def test_markdown_has_bytes_and_distinguishes_unknown_from_zero(self):
        self.assertTrue(callable(getattr(timing,'timing_markdown',None)), 'Timing table renderer missing')
        table = timing.timing_markdown([{'operation':'read','action':'file-read-bytes',
            'bytes':3,'duration_seconds':0.0,'status':'RETURNED'},
            {'operation':'worker','action':'community-search','duration_seconds':None,'status':'UNFINISHED'}])
        self.assertIn('| 0.000000 | 3 | RETURNED |', table)
        self.assertIn('| UNKNOWN |  | UNFINISHED |', table)

    def test_spawn_to_module_entry_and_worker_budget_are_not_silently_dropped(self):
        rows = [
            {'kind':'POINT','phase':'popen-entry','pid':1,'thread':1,'wall_ns':100},
            {'kind':'POINT','phase':'popen-return','pid':1,'thread':1,'wall_ns':200,
             'child_pid':2,'child_creation':'abc'},
            {'kind':'POINT','phase':'worker-deadline','pid':1,'thread':1,'wall_ns':210,
             'child_pid':2,'deadline_ns':120000000200,'budget_seconds':120},
            {'kind':'POINT','phase':'worker-entry','pid':2,'thread':1,'wall_ns':300,
             'creation':'abc','parent_pid':1},
        ]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/'events').mkdir()
            (root/'events'/'synthetic.json').write_text('{}',encoding='utf-8')
            # Only parsing is replaced: this control targets interval conversion,
            # not the separately tested observer parser or a real worker proof.
            with mock.patch.object(timing.observer,'parse_events',return_value={'errors':[],'events':rows}):
                result=timing.observer_rows(root)
        phases={r['action']:r for r in result}
        self.assertIn('process-creation',phases)
        self.assertEqual(phases['process-creation']['duration_seconds'],0.0000001)
        self.assertIn('spawn-to-python-module-entry',phases)
        self.assertEqual(phases['spawn-to-python-module-entry']['duration_seconds'],0.0000001)
        self.assertEqual(phases['spawn-to-python-module-entry']['worker_budget_seconds'],120)

    def test_real_observer_parser_accepts_120_and_refuses_30_in_extended_trace(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); events=root/'events'; events.mkdir()
            common={'schema':1,'arm':'events','thread':1,'cpu_ns':0,'kind':'POINT'}
            rows=[dict(common,pid=101,creation='parent',sequence=0,wall_ns=100,phase='popen-entry'),
                  dict(common,pid=101,creation='parent',sequence=1,wall_ns=200,phase='popen-return',
                       child_pid=102,child_creation='child'),
                  dict(common,pid=101,creation='parent',sequence=2,wall_ns=210,phase='worker-deadline',
                       child_pid=102,deadline_ns=120000000200,budget_seconds=120),
                  dict(common,pid=102,creation='child',sequence=0,wall_ns=300,phase='worker-entry')]
            for n,row in enumerate(rows):
                (events/(str(n)+'.json')).write_text(json.dumps(row),encoding='ascii')
            self.assertTrue(any(r['action']=='process-creation' for r in timing.observer_rows(root)))
            # New test-owned record mutation exercises rejection; no historical packet is changed.
            rows[2]['budget_seconds']=30
            (events/'2.json').write_text(json.dumps(rows[2]),encoding='ascii')
            with self.assertRaisesRegex(ValueError,'WRONG_BUDGET'):
                timing.observer_rows(root)

    def test_fixture_creation_times_every_created_file_and_total(self):
        self.assertTrue(callable(getattr(timing,'create_fixture',None)), 'Timed fixture creator missing')
        with tempfile.TemporaryDirectory() as folder:
            fixture=Path(folder)/'fixture'
            rows=timing.create_fixture(fixture)
            files={r['path']:r for r in rows if r['action']=='fixture-file-write'}
            self.assertEqual({Path(p).name for p in files},set(timing.FIXTURE)|{'sources.json','policy.json','task.json'})
            for path,row in files.items():
                self.assertEqual(row['bytes'],Path(path).stat().st_size)
                self.assertGreaterEqual(row['duration_seconds'],0)
                self.assertEqual(row['status'],'RETURNED')
            self.assertTrue(any(r['action']=='fixture-creation' and r['status']=='RETURNED' for r in rows))

    def test_missing_historical_cache_is_refused_not_rebaselined(self):
        self.assertTrue(callable(getattr(timing,'cache_inputs',None)), 'Exact cache set check missing')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'only-one.db').write_bytes(b'not-the-six-approved-cache-files')
            with self.assertRaisesRegex(ValueError,'CACHE_SET'):
                timing.cache_inputs(root)

    def test_real_parser_retains_thread_and_base_import_readiness_in_table(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); events=root/'events'; events.mkdir()
            common={'schema':1,'arm':'events','thread':27,'pid':102,'creation':'child',
                    'cpu_ns':0,'kind':'POINT'}
            rows=[dict(common,sequence=0,wall_ns=100,phase='worker-entry'),
                  dict(common,sequence=1,wall_ns=300,phase='base-imports-complete')]
            for n,row in enumerate(rows):
                (events/(str(n)+'.json')).write_text(json.dumps(row),encoding='ascii')
            result=timing.observer_rows(root)
            self.assertTrue(any(r['action']=='module-entry-to-base-imports-complete' for r in result))
            row=next(r for r in result if r['action']=='module-entry-to-base-imports-complete')
            self.assertEqual(row['thread'],27)
            self.assertEqual(row['duration_seconds'],0.0000002)
            table=timing.timing_markdown(result)
            self.assertIn('| Thread |',table)
            self.assertIn('| 102 | 27 |',table)

    def test_io_overlay_preserves_file_read_and_hash_result(self):
        raw = b"from pathlib import Path\nfrom knowledge_bridge import contracts as c\ndef sample(p):\n    return c.digest(Path(p).read_bytes())\n"
        transformed = timing.io_overlay(raw, 'sample.py', hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'unicode.txt'; data.write_bytes('alpha\u0ba4'.encode('utf-8'))
            # Use the real diagnostic logger, not a mock observer.
            import extended_timing_log as log
            log = importlib.reload(log)
            events = root / 'logs'; events.mkdir()
            log.configure(events, [root], budget=120)
            scope = {'__name__': 'overlay_control', '_et': log}
            sys.path.insert(0, str(SCRIPTS.parents[1] / 'memory-integrity/scripts'))
            from knowledge_bridge import contracts
            exec(compile(transformed, 'overlay_control.py', 'exec'), scope)
            self.assertEqual(scope['sample'](data), hashlib.sha256(data.read_bytes()).hexdigest())
            self.assertTrue(list(events.glob('*.jsonl')))

    def test_source_hash_mismatch_is_refused_before_transform(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_PIN'):
            timing.io_overlay(b'def f(): return 1\n', 'sample.py', '0' * 64)

    def test_real_copied_public_index_logs_each_declared_source_without_worker(self):
        self.assertTrue(callable(getattr(timing,'make_source_copy',None)), 'Sealed source-copy builder missing')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'source'; source.mkdir()
            timing.make_source_copy(source)
            fixture = root/'fixture'; fixture.mkdir()
            for name, text in timing.FIXTURE.items():
                (fixture/name).write_text(text, encoding='utf-8')
            rows = [{'id':i, 'path':p, 'authority':'AUTHORITATIVE'} for i,p in
                    [('client','client.py'),('worker','worker.py'),('test','test_sample.py')]]
            (fixture/'sources.json').write_text(json.dumps({'schema_version':1,'workspace_id':'w',
                'repository':'example','sources':rows}), encoding='utf-8')
            target = root/'build'; target.mkdir(); (target/'events').mkdir(); (target/'io').mkdir()
            (root/'temp').mkdir()
            (target/'Config.json').write_text(json.dumps({'watched_roots':[str(fixture),str(source)]}),encoding='utf-8')
            env = dict(os.environ, MEMORY_INTEGRITY_WORKER_DIAGNOSTICS=str(target/'events'),
                       PYTHONDONTWRITEBYTECODE='1', TEMP=str(root/'temp'), TMP=str(root/'temp'))
            run = subprocess.run([sys.executable,'-B',str(SCRIPTS/'extended_worker_timing.py'),
                '--step','build','--source',str(source),'--fixture',str(fixture),'--target',str(target)],
                cwd=target,env=env,capture_output=True,timeout=30)
            self.assertEqual(run.returncode,0,(run.stdout+run.stderr).decode(errors='replace'))
            self.assertTrue((target/'Step-Result.json').is_file())
            records=[json.loads(line) for p in (target/'io').glob('*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
            for name in timing.FIXTURE:
                self.assertTrue(any(r.get('path')==str(fixture/name) and r['event']=='END' for r in records),name)

    def test_mutated_protected_input_is_not_rebaselined(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'source.py'; file.write_bytes(b'original')
            rows = {str(file): timing.file_record(file)}
            timing.check_records(rows)
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'INPUT_CHANGED'):
                timing.check_records(rows)

    def test_probe_failure_does_not_consume_workload_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            attempt = Path(folder) / 'Attempt'
            def refused():
                raise ValueError('E_RUNTIME_UNAVAILABLE')
            with self.assertRaisesRegex(ValueError, 'RUNTIME_UNAVAILABLE'):
                timing.claim_after_probe(attempt, refused)
            self.assertFalse(attempt.exists())

    def test_existing_attempt_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            attempt = Path(folder) / 'Attempt'; attempt.mkdir()
            marker = attempt / 'retain'; marker.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):
                timing.claim_after_probe(attempt, lambda: None)
            self.assertEqual(marker.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
