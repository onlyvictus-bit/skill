"""Real observer contracts; no selected numerical worker or historical retry."""
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
REPO = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))
try:
    import worker_diagnostic_events as events
except ModuleNotFoundError:
    events = None
try:
    import worker_lock_probe as locks
except ModuleNotFoundError:
    locks = None
try:
    import worker_timing_lifetime_diagnostic as controller
except ModuleNotFoundError:
    controller = None


class WorkerObserverContracts(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(events, 'The bounded event observer has not been implemented')
        return events

    @contextlib.contextmanager
    def configured(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name) / 'observed-events'
            root.mkdir()
            old = os.environ.get('MEMORY_INTEGRITY_WORKER_DIAGNOSTICS')
            os.environ['MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'] = str(root)
            try:
                yield root
            finally:
                if old is None:
                    os.environ.pop('MEMORY_INTEGRITY_WORKER_DIAGNOSTICS', None)
                else:
                    os.environ['MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'] = old

    def raw(self, root):
        return [p.read_bytes() for p in sorted(root.glob('*.json'))]

    def test_phase_preserves_success_exception_and_protocol_streams(self):
        # Removing the finally END or swallowing the original exception must fail.
        e = self.api()
        with self.configured() as root:
            out, err = io.StringIO(), io.StringIO()
            calls = []
            failure = RuntimeError('original')
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with e.phase('success'):
                    calls.append('once')
                with self.assertRaises(RuntimeError) as raised:
                    with e.phase('failure'):
                        raise failure
            self.assertIs(raised.exception, failure)
            self.assertEqual(calls, ['once'])
            self.assertEqual((out.getvalue(), err.getvalue()), ('', ''))
            rows = [json.loads(raw) for raw in self.raw(root)]
            self.assertEqual([(r['kind'], r['phase']) for r in rows],
                             [('START', 'success'), ('END', 'success'),
                              ('START', 'failure'), ('END', 'failure')])
            self.assertEqual(rows[-1]['outcome'], 'EXCEPTION')
            self.assertEqual(rows[-1]['error_type'], 'RuntimeError')
            self.assertTrue(all(r['pid'] == os.getpid() for r in rows))
            self.assertTrue(all(r['creation'] for r in rows))
            self.assertTrue(all(type(r['wall_ns']) is int and type(r['cpu_ns']) is int for r in rows))
            self.assertEqual(e.parse_events(self.raw(root), {'arm': root.name})['status'], 'FRAGMENT_OBSERVED_NOT_COMPLETE')

    def test_observer_failure_does_not_replace_original_exception(self):
        e = self.api()
        with self.configured() as root:
            # Existing sequence filename causes exclusive creation to refuse.
            e.emit({'kind': 'POINT', 'phase': 'first'})
            next_name = e.next_path()
            with next_name.open('xb') as stream:
                stream.write(b'occupied')
            original = LookupError('original')
            with self.assertRaises(LookupError) as raised:
                with e.phase('failed-observer'):
                    raise original
            self.assertIs(raised.exception, original)
            self.assertTrue(e.failures())
            self.assertEqual(next_name.read_bytes(), b'occupied')

    def test_missing_end_is_active_not_completed(self):
        e = self.api()
        with self.configured() as root:
            with e.phase('imports'):
                pass
            records = self.raw(root)[:1]
            report = e.parse_events(records, {'arm': root.name})
            self.assertEqual(report['status'], 'INCOMPLETE')
            self.assertEqual(report['active'][0]['phase'], 'imports')
            self.assertFalse(report['cause_proven'])

    def test_wrong_arm_duplicate_and_bad_json_cannot_be_observations(self):
        e = self.api()
        with self.configured() as root:
            with e.phase('valid'):
                pass
            raw = self.raw(root)
            for records, expected in [(raw, {'arm': 'wrong'}),
                                      (raw + raw, {'arm': root.name}),
                                      ([b'not-json'], {'arm': root.name})]:
                with self.subTest(expected=expected, size=len(records)):
                    self.assertEqual(e.parse_events(records, expected)['status'], 'INCOMPLETE')

    def test_event_limit_refuses_growth_without_hiding_failure(self):
        e = self.api()
        with self.configured() as root:
            for unused in range(129):
                e.emit({'kind': 'POINT', 'phase': 'bounded'})
            self.assertLessEqual(len(self.raw(root)), 128)
            self.assertLessEqual(sum(map(len, self.raw(root))), 16384)
            self.assertTrue(e.failures())

    def test_forbidden_payload_is_not_written(self):
        e = self.api()
        with self.configured() as root:
            e.emit({'kind': 'POINT', 'phase': 'bad', 'query_text': 'private-sentinel'})
            self.assertTrue(e.failures())
            self.assertNotIn(b'private-sentinel', b''.join(self.raw(root)))

    def test_unknown_source_hash_refuses_overlay(self):
        e = self.api()
        raw = b'print("untouched")\n'
        with self.assertRaisesRegex(ValueError, 'SOURCE'):
            e.diagnostic_source(raw, '0' * 64, 'worker.py')
        self.assertEqual(raw, b'print("untouched")\n')

    def test_overlay_removes_only_observation_nodes_to_original_ast(self):
        e = self.api()
        for role in e.SOURCE_PINS:
            source = REPO / 'memory-integrity/scripts/knowledge_bridge' / role
            raw = source.read_bytes()
            with self.subTest(role=role):
                observed = e.diagnostic_source(raw, hashlib.sha256(raw).hexdigest(), role)
                compile(observed, role, 'exec')
                self.assertEqual(e.original_ast(observed), e.original_ast(raw))
                self.assertNotEqual(observed, raw)

    def test_snapshots_do_not_open_or_seek_observed_stream(self):
        e = self.api()
        with tempfile.TemporaryFile() as stream:
            stream.write(b'unchanged'); stream.seek(3)
            before = stream.tell()
            snap = e.stream_snapshot(stream)
            self.assertFalse(snap['closed'])
            self.assertEqual(stream.tell(), before)
            self.assertFalse(os.get_inheritable(stream.fileno()))
        self.assertTrue(e.stream_snapshot(stream)['closed'])

    def test_bad_observer_path_cannot_replace_original_exception(self):
        e = self.api()
        with self.configured():
            old = os.environ['MEMORY_INTEGRITY_WORKER_DIAGNOSTICS']
            os.environ['MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'] = 'relative-unsafe-path'
            error = RuntimeError('work-failure')
            try:
                with self.assertRaises(RuntimeError) as caught:
                    with e.phase('invalid-observer'):
                        raise error
                self.assertIs(caught.exception, error)
            finally:
                os.environ['MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'] = old

    def test_actual_process_success_and_error_survive_overlay(self):
        # Real _process/Popen; retained runner suppresses directory cleanup here.
        # The separate two-session fixture below exercises actual owned cleanup.
        e = self.api()
        import types
        from unittest import mock
        scripts = REPO / 'memory-integrity/scripts'
        sys.path.insert(0, str(scripts))
        import knowledge_bridge
        raw = (scripts / 'knowledge_bridge/worker_client.py').read_bytes()
        observed = e.diagnostic_source(raw, hashlib.sha256(raw).hexdigest(), 'worker_client.py')
        package = types.ModuleType('knowledge_bridge._observed_worker_client')
        package.__package__ = 'knowledge_bridge'
        package.__file__ = str(scripts / 'knowledge_bridge/worker_client.py')
        with mock.patch.dict(sys.modules, {'knowledge_bridge._worker_diag_v1': e}), \
                mock.patch.object(knowledge_bridge, '_worker_diag_v1', e, create=True):
            exec(compile(observed, package.__file__, 'exec'), package.__dict__)
            with self.configured() as root:
                script = root.parent / 'echo.py'
                with script.open('x', encoding='utf-8') as stream:
                    stream.write('import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n')
                digest = hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
                self.assertEqual(package._process(sys.executable, script, {'ok': True}, 5, digest), {'ok': True})
                with self.assertRaisesRegex(ValueError, 'E_WORKER_FAILED: original'):
                    package._process(sys.executable, script, {'ok': False, 'error': 'original'}, 5, digest)
                rows = [json.loads(x) for x in self.raw(root)]
                self.assertEqual(sum(r['phase'] == 'popen-return' for r in rows), 2)
                self.assertEqual(sum(r['phase'] == 'worker-deadline' for r in rows), 2)
                self.assertFalse(e.failures())
                self.assertEqual(e.parse_events(self.raw(root), {'arm': root.name})['status'], 'FRAGMENT_OBSERVED_NOT_COMPLETE')


class WorkerLockProbeContracts(unittest.TestCase):
    def test_refuses_old_or_redirected_or_directory_targets_before_api(self):
        self.assertIsNotNone(locks, 'The query-only probe has not been implemented')
        with tempfile.TemporaryDirectory() as name:
            owned = Path(name) / 'new'; owned.mkdir()
            outside = Path(name) / 'old'; outside.mkdir()
            path = outside / 'output'
            with path.open('xb') as stream:
                stream.write(b'old')
            with self.assertRaisesRegex(ValueError, 'TARGET'):
                locks.validate_target(path, owned)
            with self.assertRaisesRegex(ValueError, 'TARGET'):
                locks.validate_target(owned, owned)
            self.assertEqual(path.read_bytes(), b'old')

    def test_empty_query_does_not_claim_no_holder_or_repair(self):
        self.assertIsNotNone(locks, 'The query-only probe has not been implemented')
        value = locks.result([], api_status=0)
        self.assertEqual(value['status'], 'UNKNOWN')
        self.assertFalse(value['cause_proven'])
        self.assertFalse(value['fix_validated'])
        self.assertFalse(value['gate1_complete'])


class WorkerDiagnosticControllerContracts(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(controller, 'The isolated controller has not been implemented')
        return controller

    def test_history_failure_creates_no_claim(self):
        ctl = self.api()
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / 'attempt'
            def denied():
                raise PermissionError('historical-input')
            with self.assertRaisesRegex(PermissionError, 'historical-input'):
                ctl.guarded_claim(denied, target)
            self.assertFalse(target.exists())

    def test_existing_attempt_is_preserved(self):
        ctl = self.api()
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / 'attempt'; target.mkdir()
            with self.assertRaises((ValueError, FileExistsError)):
                ctl.guarded_claim(lambda: None, target)
            self.assertTrue(target.is_dir())

    def test_pass_does_not_set_worker_fix_or_gate_qualification(self):
        ctl = self.api()
        result = ctl.diagnosis_result([], observer_complete=True)
        self.assertEqual(result['status'], 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        for flag in ('cause_proven', 'fix_validated', 'gate1_complete', 'release_ready', 'installed'):
            self.assertIs(result[flag], False)

    def test_incomplete_telemetry_cannot_be_success(self):
        ctl = self.api()
        self.assertEqual(ctl.diagnosis_result([], observer_complete=False)['status'], 'DIAGNOSTIC_INCOMPLETE')

    def test_wrong_external_seal_refuses_before_reading_json(self):
        ctl = self.api()
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'Prepared.json'
            with path.open('xb') as stream:
                stream.write(b'{not-json')
            with self.assertRaisesRegex(ValueError, 'SEAL'):
                ctl.read_sealed(path, '0' * 64)

    def test_live_overlay_uses_exact_original_test_and_worker_source(self):
        ctl = self.api()
        from unittest import mock
        originals = {role: (REPO / 'memory-integrity/scripts/knowledge_bridge' / role).read_bytes()
                     for role in events.SOURCE_PINS}
        with tempfile.TemporaryDirectory() as name:
            dest = Path(name) / 'observed'; dest.mkdir()
            folder = dest / 'memory-integrity/scripts/knowledge_bridge'
            folder.mkdir(parents=True)
            for role in events.SOURCE_PINS:
                original = REPO / 'memory-integrity/scripts/knowledge_bridge' / role
                with (folder / role).open('xb') as stream:
                    stream.write(original.read_bytes())
            with mock.patch.object(ctl, 'SOURCES', [Path(name) / 'baseline', dest]):
                manifest = ctl.overlay_copy(dest)
            self.assertEqual(len(manifest), 7)
            self.assertEqual((folder / '_worker_diag_v1.py').read_bytes(), (SCRIPTS / 'worker_diagnostic_events.py').read_bytes())
            for role, before in originals.items():
                self.assertEqual((REPO / 'memory-integrity/scripts/knowledge_bridge' / role).read_bytes(), before)

    def test_overlay_refuses_unapproved_root_before_file_read_or_write(self):
        ctl = self.api()
        with tempfile.TemporaryDirectory() as name:
            old = Path(name)
            with self.assertRaisesRegex(ValueError, 'COPY_SCOPE'):
                ctl.overlay_copy(old)
            self.assertEqual(list(old.iterdir()), [])

    def test_method_record_is_not_replaced_by_concurrent_holder_capture(self):
        ctl = self.api()
        self.assertTrue(callable(getattr(ctl, 'method_record', None)), 'Missing capture-role correlation')
        method = {'label': 'observed-method', 'exit_code': 1}
        query = {'label': 'holder-0', 'exit_code': 0}
        self.assertIs(ctl.method_record([method, query], 'observed-method'), method)
        with self.assertRaisesRegex(ValueError, 'CAPTURE_ROLE'):
            ctl.method_record([method, method], 'observed-method')

    def test_real_history_handshake_is_readonly_and_environment_restored(self):
        ctl = self.api()
        self.assertTrue(callable(getattr(ctl, 'readonly_python', None)), 'Missing inherited history guard')
        from integrity_v2 import engine_client
        before_env = {key: os.environ.get(key) for key in ('PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE')}
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); scripts = root / 'scripts'; scripts.mkdir()
            (scripts / 'capfixture.py').write_text('value = 17\n', encoding='utf-8')
            (scripts / 'claude_mon_v2.py').write_text(
                'import capfixture, json\nprint(json.dumps({"ok":True,"schema_version":2,"schema_digest":"' + 'a'*64 + '"}))\n', encoding='utf-8')
            def inventory():
                return {p.relative_to(root).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns,
                        None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest()) for p in root.rglob('*')}
            baseline = inventory()
            with ctl.readonly_python():
                self.assertEqual(os.environ['PYTHONDONTWRITEBYTECODE'], '1')
                self.assertEqual(os.environ['PYTHONNOUSERSITE'], '1')
                ok, reply = engine_client.handshake(root)
                self.assertTrue(ok, reply)
            self.assertEqual(inventory(), baseline)
            self.assertEqual({k: os.environ.get(k) for k in before_env}, before_env)
            with self.assertRaisesRegex(RuntimeError, 'same-error'):
                with ctl.readonly_python():
                    raise RuntimeError('same-error')
            self.assertEqual({k: os.environ.get(k) for k in before_env}, before_env)

    def test_seal_and_prepared_require_exact_roles_and_state(self):
        ctl = self.api()
        self.assertTrue(callable(getattr(ctl, 'validate_seal', None)), 'Missing exact seal schema')
        self.assertTrue(callable(getattr(ctl, 'validate_prepared', None)), 'Missing exact Prepared schema')
        with self.assertRaisesRegex(ValueError, 'SCHEMA'):
            ctl.validate_seal({'files': {}})
        sample = ctl.seal_template()
        ctl.validate_seal(sample)
        import copy
        first = next(iter(sample['files']))
        for case in ('empty', 'missing', 'extra', 'wrong-path'):
            bad = copy.deepcopy(sample)
            if case == 'empty': bad['files'] = {}
            elif case == 'missing': del bad['files'][first]
            elif case == 'extra': bad['files']['unknown'] = bad['files'][first]
            else: bad['files'][first]['path'] = str(ctl.OUT / 'wrong-role.py')
            with self.subTest(case=case), self.assertRaisesRegex(ValueError, 'SCHEMA'):
                ctl.validate_seal(bad)
        with self.assertRaisesRegex(ValueError, 'SCHEMA'):
            ctl.validate_prepared({'scope': 'wrong', 'worker_started': True})


class ReviewBlockerRegressions(unittest.TestCase):
    configured = WorkerObserverContracts.configured
    raw = WorkerObserverContracts.raw

    def trace_fixture(self):
        rows = []
        counters = {}
        def add(pid, kind, phase, role, **detail):
            seq = counters.get(pid, 0); counters[pid] = seq+1
            row = dict(schema=1, arm='observed-events', pid=pid, creation=str(pid*10),
                       parent_pid=11 if pid == 22 else 1, parent_creation='110' if pid == 22 else '10',
                       thread=pid, sequence=seq, wall_ns=seq+1, cpu_ns=seq+1,
                       kind=kind, phase=phase, role=role, **detail)
            rows.append({'name':str(pid)+'-'+str(seq).zfill(3)+'.json', 'raw':json.dumps(row).encode('ascii')})
        def pair(pid, phase, role):
            add(pid,'START',phase,role,span=counters.get(pid,0))
            first = json.loads(rows[-1]['raw'])
            add(pid,'END',phase,role,span=first['span'],outcome='RETURNED',duration_ns=1)
        add(11,'POINT','worker-client-entry','client')
        add(11,'START','worker-client-process','client',span=0)
        add(11,'POINT','popen-return','client',child_pid=22,child_creation='220',child_role='worker')
        add(11,'POINT','worker-deadline','client',child_pid=22,budget_seconds=30,deadline_ns=1000)
        add(11,'END','worker-client-process','client',span=0,outcome='RETURNED',duration_ns=3)
        add(22,'POINT','worker-entry','worker')
        add(22,'POINT','base-imports-complete','worker')
        add(22,'POINT','input-size','worker')
        for phase in ('worker-main','worker-runtime_identity','worker-retrieve','serialization'):
            pair(22,phase,'worker')
        return rows, {'arm':'observed-events','root_pid':11,'public_count':0}
    def test_single_balanced_point_is_not_complete_without_role_grammar(self):
        with self.configured() as root:
            events.emit({'kind': 'POINT', 'phase': 'alone'})
            self.assertNotEqual(events.parse_events(self.raw(root), {'arm': root.name})['status'], 'OBSERVED')

    def test_snapshot_error_is_persisted_and_cannot_complete_trace(self):
        with self.configured() as root:
            events.emit({'kind':'POINT','phase':'establish-root'})
            class BrokenMetadata:
                @property
                def closed(self): raise RuntimeError('diagnostic-property')
            detail = events.safe_snapshot(BrokenMetadata())
            self.assertEqual(detail, {'observation_error':'RuntimeError'})
            self.assertTrue(list(root.glob('*.error')), 'Observation failure must survive process exit')
            rows, expected = self.trace_fixture()
            row = json.loads(rows[0]['raw']); row['snapshot'] = detail
            rows[0]['raw'] = json.dumps(row).encode('ascii')
            self.assertEqual(events.validate_trace(rows,expected)['status'], 'INCOMPLETE')

    def test_full_parser_refuses_missing_foreign_reused_and_wrong_named_events(self):
        self.assertTrue(callable(getattr(events, 'validate_trace', None)), 'Missing process/role trace closure')
        rows, expected = self.trace_fixture()
        self.assertEqual(events.validate_trace(rows, expected)['status'], 'OBSERVED')
        import copy
        for mutation in ('missing-phase', 'missing-process', 'generation', 'foreign', 'foreign-whole-process', 'filename', 'duplicate', 'role', 'clock'):
            changed = copy.deepcopy(rows)
            if mutation == 'missing-phase':
                changed = [x for x in changed if json.loads(x['raw'])['phase'] != 'worker-main']
                counts = {}
                for item in changed:
                    row = json.loads(item['raw']); pid = row['pid']; seq = counts.get(pid,0); counts[pid]=seq+1
                    row['sequence']=seq;item.update(name=str(pid)+'-'+str(seq).zfill(3)+'.json',raw=json.dumps(row).encode('ascii'))
            elif mutation == 'missing-process': changed = [x for x in changed if json.loads(x['raw'])['pid'] != 22]
            elif mutation == 'foreign-whole-process':
                for item in rows:
                    row=json.loads(item['raw'])
                    if row['pid'] != 22: continue
                    row.update(pid=33, creation='330')
                    changed.append({'name':'33-'+str(row['sequence']).zfill(3)+'.json','raw':json.dumps(row).encode('ascii')})
            elif mutation == 'duplicate': changed.append(copy.deepcopy(changed[0]))
            elif mutation == 'filename': changed[0]['name'] = 'other.json'
            else:
                target = changed[-1]; data = json.loads(target['raw'])
                if mutation == 'generation': data['creation'] = '9999'
                elif mutation == 'foreign': data['pid'] = 33
                elif mutation == 'role': data['role'] = 'unknown'
                else: data['wall_ns'] = 0
                target['raw'] = json.dumps(data).encode('ascii')
            with self.subTest(mutation=mutation):
                result = events.validate_trace(changed, expected)
                self.assertEqual(result['status'], 'INCOMPLETE', result)

    def test_transformed_two_session_lifecycle_is_transparent_and_within_quota(self):
        import types
        from unittest import mock
        import shutil
        scripts = REPO / 'memory-integrity/scripts'
        sys.path.insert(0, str(scripts))
        import knowledge_bridge
        raw = (scripts / 'knowledge_bridge/distributed_retrieval.py').read_bytes()
        observed = events.diagnostic_source(raw, hashlib.sha256(raw).hexdigest(), 'distributed_retrieval.py')
        package = types.ModuleType('knowledge_bridge._observed_distributed')
        package.__package__ = 'knowledge_bridge'
        fixture = '''import hashlib,json,sys
from pathlib import Path
sys.path.insert(0, SCRIPTS)
from knowledge_bridge import BRIDGE_VERSION,SEMANTICA_VERSION,SEMANTICA_REVISION
canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
owned={}
for raw in sys.stdin.buffer:
 r=json.loads(raw)
 p=r['payload']; op=r['op']
 if op=='fit': result={'vectors':[[1.0] for n in p['nodes']],'query':[1.0],'metadata':{'dimension':1}}
 elif op=='initialize':
  owned={n['id']:n for n in p['nodes']};result={'shard_digest':hashlib.sha256(canonical(p)).hexdigest(),'node_count':len(owned)}
 elif op=='seed': result={'seeds':[{'id':i,'score':1.0} for i in sorted(owned)[:p['seeds']]]}
 elif op=='neighbors': result={'neighbors':[]}
 else: raise ValueError('unknown fixture operation')
 response={'schema_version':1,'lane':r['lane'],'sequence':r['sequence'],'lease':r['lease'],'request_digest':hashlib.sha256(canonical(r)).hexdigest(),'ok':True,'result':result,'identity':{'bridge_version':BRIDGE_VERSION,'semantica_version':SEMANTICA_VERSION,'revision':SEMANTICA_REVISION,'answer_generation':False}}
 sys.stdout.buffer.write(canonical(response)+b'\\n');sys.stdout.buffer.flush()
'''.replace('SCRIPTS', repr(str(scripts)))
        with self.configured() as root:
            (root.parent / 'distributed_worker.py').write_text(fixture, encoding='utf-8')
            package.__file__ = str(root.parent / 'distributed_retrieval.py')
            with mock.patch.dict(sys.modules, {'knowledge_bridge._worker_diag_v1': events}), \
                    mock.patch.object(knowledge_bridge, '_worker_diag_v1', events, create=True):
                exec(compile(observed, package.__file__, 'exec'), package.__dict__)
                calls = []
                class OwnedDirectory:
                    def __init__(self): self.name = tempfile.mkdtemp()
                    def cleanup(self):
                        calls.append(('cleanup', self.name)); shutil.rmtree(self.name)
                sessions = []
                real_session = package._Session
                def create_session(*args, **kwargs):
                    session = real_session(*args, **kwargs); sessions.append(session); return session
                with mock.patch.object(package.tempfile, 'TemporaryDirectory', OwnedDirectory):
                    from knowledge_bridge import distributed_retrieval as original
                    client = package.DistributedClient(sys.executable, timeout=10)
                    payload = {'nodes':[{'id':'a'}, {'id':'b'}, {'id':'c'}], 'edges':[], 'query_text':'fixture',
                               'embedding_mode':'lexical', 'direction':'outgoing','seeds':1,'max_hops':2,
                               'max_visits':100,'max_results':10,'generation_lease':'a'*64}
                    try:
                        with mock.patch.object(package, '_Session', create_session):
                            result = client(payload)
                        self.assertEqual([r['id'] for r in result['results']], ['a'])
                        self.assertTrue(all(row['alive'] is False for row in client.execution_proof['workers_after_close']))
                    finally:
                        # Real fixture children/handles are released even on RED.
                        for session in sessions:
                            if not session._closed: original._Session.close(session)
                self.assertEqual(len(calls), 2)
                for session in sessions:
                    self.assertIsNotNone(session.process.returncode)
                    self.assertTrue(all(s.closed for s in (session.reader, session.output, session.errors, session.process.stdin)))
                    self.assertFalse(Path(session.directory.name).exists())
                self.assertFalse(events.failures(), events.failures())
                self.assertLessEqual(len(self.raw(root)), events.COORDINATOR_EVENTS)
                self.assertLessEqual(sum(map(len, self.raw(root))), events.COORDINATOR_BYTES)
                rows = [json.loads(raw) for raw in self.raw(root)]
                stop_starts = [r['sequence'] for r in rows if r['phase'] == 'distributed-retrieval-stop' and r['kind'] == 'START']
                first_close = min(r['sequence'] for r in rows if r['phase'] == 'distributed-retrieval-close' and r['kind'] == 'START')
                self.assertGreaterEqual(sum(seq < first_close for seq in stop_starts), 2)
                (root.parent / 'Lifecycle-Volume.json').write_text(json.dumps({'events':len(rows),
                    'bytes':sum(map(len,self.raw(root))),'child_count':len(sessions),
                    'real_cleanup_calls':len(calls),'numerical_runtime':False}),encoding='utf-8')
                # The original close error must survive an observer failure too.
                failure = RuntimeError('owned-close-error')
                class BadSession:
                    process = None; writer = None
                    def close(self): raise failure
                with self.assertRaises(RuntimeError) as caught:
                    events.call('lifetime-close', BadSession(), 'close')
                self.assertIs(caught.exception, failure)


if __name__ == '__main__':
    unittest.main()
