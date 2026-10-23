"""Failure-first contract tests for the isolated Gate1 cleanup diagnostic."""
import importlib.util
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
SUBJECT = ROOT / '.github/scripts/gate1_cleanup_diagnostic.py'
WORKER = ROOT / 'memory-integrity/scripts/knowledge_bridge/worker.py'


def load_subject():
    if not SUBJECT.exists():
        # The RED probe must execute the existing worker formatter through the
        # real client, rather than treating a missing module as a useful test.
        return SimpleNamespace(diagnostic_worker_bytes=lambda raw: raw)
    spec = importlib.util.spec_from_file_location('gate1_cleanup_diagnostic_test_subject', SUBJECT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CleanupDiagnosticWorkerContract(unittest.TestCase):
    def setUp(self):
        self.subject = load_subject()

    def synthetic_worker_tree(self, body=None, overlay=True):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / 'scripts'
        bridge = root / 'knowledge_bridge'
        shutil.copytree(WORKER.parent, bridge)
        original = (bridge / 'worker.py').read_bytes()
        worker_bytes = self.subject.diagnostic_worker_bytes(original) if overlay else original
        # The handler is real. Only runtime/retrieval are replaced to induce a
        # deterministic OS-shaped error without calling Semantica.
        marker = b"def runtime_identity():"
        start = worker_bytes.index(marker)
        end = worker_bytes.index(b"\ndef shacl(", start)
        identity = b"""def runtime_identity():\n    return {'bridge_version':'1.2.0','semantica_version':'0.7.0','revision':'320761de5d040a54a3220acc563223b4a7ffdc51','answer_generation':False}\n"""
        worker_bytes = worker_bytes[:start] + identity + worker_bytes[end + 1:]
        body = body or b"""    cause=OSError(13, 'synthetic denied', 'fixture-cache.db')\n    cause.add_note('synthetic cleanup note')\n    raise ValueError('E_DISTRIBUTED_CLEANUP') from cause\n"""
        injected = b'def retrieve(payload):\n' + body
        self.assertEqual(worker_bytes.count(b'def retrieve(payload):'), 1)
        worker_bytes = worker_bytes.replace(b'def retrieve(payload):\n', injected, 1)
        (bridge / 'worker.py').write_bytes(worker_bytes)
        return root

    def public_workflow(self, root, body, overlay=True):
        """Use the unchanged public main error wrapper around a real child."""
        root = self.synthetic_worker_tree(body, overlay=overlay)
        worker_temp = root.parent / 'worker-temp'; worker_temp.mkdir()
        workflow_root = ROOT / 'memory-integrity/scripts'
        program = r'''
import os,sys
os.environ['TEMP']=sys.argv[3];os.environ['TMP']=sys.argv[3]
sys.path.insert(0,sys.argv[1]);sys.path.insert(1,sys.argv[2])
from knowledge_bridge import workflow as knowledge
from knowledge_bridge.worker_client import WorkerClient
def dispatch(args):
    return WorkerClient(sys.executable, timeout=15)({'op':'retrieve'})
knowledge.dispatch=dispatch
import memory_integrity_workflow
sys.argv=['memory_integrity_workflow.py','knowledge-status','--claude-mon-root','unused']
raise SystemExit(memory_integrity_workflow.main())
'''
        return subprocess.run([sys.executable, '-B', '-c', program, str(root), str(workflow_root), str(worker_temp)],
                              capture_output=True, text=True, timeout=30)

    def test_success_reply_path_is_unchanged_through_the_public_workflow(self):
        body = b"    return {'ok':True,'result':'synthetic-success'}\n"
        original = self.public_workflow(None, body, overlay=False)
        diagnostic = self.public_workflow(None, body, overlay=True)
        self.assertEqual(original.returncode, 0, original.stdout + original.stderr)
        self.assertEqual(diagnostic.returncode, 0, diagnostic.stdout + diagnostic.stderr)
        self.assertEqual(json.loads(original.stdout), json.loads(diagnostic.stdout))
        self.assertNotIn('GATE1_CLEANUP_DIAGNOSTIC=', diagnostic.stdout)

    def test_actual_worker_client_preserves_details_through_public_error_wrapper(self):
        root = self.synthetic_worker_tree()
        worker_temp = root.parent / 'worker-temp'
        worker_temp.mkdir()
        program = r'''
import os,sys
os.environ['TEMP']=sys.argv[2]
os.environ['TMP']=sys.argv[2]
sys.path.insert(0, sys.argv[1])
from knowledge_bridge.worker_client import WorkerClient
try:
    WorkerClient(sys.executable, timeout=15)({'op':'retrieve'})
except ValueError as error:
    print(str(error))
    raise SystemExit(0)
raise SystemExit(9)
'''
        result = subprocess.run([sys.executable, '-B', '-c', program, str(root), str(worker_temp)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = result.stdout
        self.assertIn('E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP', text)
        marker = 'GATE1_CLEANUP_DIAGNOSTIC='
        self.assertIn(marker, text)
        detail = json.loads(text.split(marker, 1)[1].strip())
        self.assertFalse(detail['truncated'])
        self.assertEqual(detail['exception']['type'], 'ValueError')
        self.assertEqual(detail['chain'][1]['type'], 'PermissionError')
        self.assertEqual(detail['chain'][1]['errno'], 13)
        self.assertEqual(detail['chain'][1]['filename'], 'fixture-cache.db')

        self.assertEqual(detail['chain'][1]['notes'], ['synthetic cleanup note'])

    def test_actual_public_workflow_blocker_retains_the_worker_diagnostic(self):
        body = b"""    try:
        raise OSError(13, 'synthetic denied', 'fixture-cache.db')
    except OSError as cause:
        cause.add_note('synthetic cleanup note')
        raise ValueError('E_DISTRIBUTED_CLEANUP') from cause
"""
        result = self.public_workflow(None, body)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        reply = json.loads(result.stdout)
        self.assertFalse(reply['ok'])
        self.assertEqual(reply['overall'], 'BLOCKED')
        self.assertEqual(reply['adapter_calls'], 0)
        self.assertEqual(reply['approvals_consumed'], 0)
        blocker = reply['blockers'][0]
        self.assertIn('E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP', blocker)
        self.assertIn('GATE1_CLEANUP_DIAGNOSTIC=', blocker)
        detail = json.loads(blocker.split('GATE1_CLEANUP_DIAGNOSTIC=', 1)[1].strip())
        self.assertFalse(detail['truncated'])
        self.assertEqual(detail['chain'][0]['relation'], 'root')
        self.assertEqual(detail['chain'][1]['relation'], 'cause')
        self.assertTrue(detail['chain'][1]['frames'])
        self.assertEqual(detail['chain'][1]['errno'], 13)
        self.assertEqual(detail['chain'][1]['filename'], 'fixture-cache.db')

        state, observed = self.subject.classify_public_reply(2, reply, Path('unused-pack.json'))
        self.assertEqual(state, 'CAUSE_OBSERVED_PENDING_REVIEW')
        self.assertEqual(observed, detail)

    def test_details_bound_cycles_depth_and_frames_without_environment_or_payload(self):
        result = self.public_workflow(None, b"""    cycle=ValueError('E_DISTRIBUTED_CLEANUP')
    inner=OSError(5, 'locked', 'cache.db')
    cycle.__cause__=inner
    inner.__context__=cycle
    inner.add_note('n'*20000)
    raise cycle
""")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        blocker = json.loads(result.stdout)['blockers'][0]
        self.assertIn(self.subject.MARKER, blocker)
        detail = json.loads(blocker.split(self.subject.MARKER, 1)[1])
        encoded = json.dumps(detail, ensure_ascii=True).encode('utf-8')
        self.assertLessEqual(len(encoded), 49152)
        self.assertTrue(detail['truncated'])
        self.assertLessEqual(len(detail['chain']), 12)
        self.assertIn('frames', detail)
        self.assertNotIn('environ', json.dumps(detail))
        self.assertNotIn('payload', json.dumps(detail))

    def test_actual_overlay_marks_truncation_for_a_shortened_exception_field(self):
        root = self.synthetic_worker_tree(b"    raise ValueError('x'*10000)\n")
        worker_temp = root.parent / 'worker-temp'; worker_temp.mkdir()
        program = r'''
import os,sys
os.environ['TEMP']=sys.argv[2];os.environ['TMP']=sys.argv[2]
sys.path.insert(0,sys.argv[1])
from knowledge_bridge.worker_client import WorkerClient
try: WorkerClient(sys.executable, timeout=15)({'op':'retrieve'})
except ValueError as error: print(str(error));raise SystemExit(0)
raise SystemExit(9)
'''
        result = subprocess.run([sys.executable, '-B', '-c', program, str(root), str(worker_temp)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        detail = json.loads(result.stdout.split('GATE1_CLEANUP_DIAGNOSTIC=', 1)[1].strip())
        self.assertTrue(detail['truncated'], 'shortened exception fields must not masquerade as complete evidence')

    def test_changed_original_or_unexpected_overlay_pattern_is_refused(self):
        original = WORKER.read_bytes()
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_WORKER_ORIGINAL_CHANGED'):
            self.subject.diagnostic_worker_bytes(original + b'changed')
        # Byte identity is checked before structure, so a modified source must
        # fail at the stronger first gate.
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_WORKER_ORIGINAL_CHANGED'):
            self.subject.diagnostic_worker_bytes(original.replace(
                b"except Exception as exc:", b"except RuntimeError as exc:"))


class CleanupDiagnosticGuards(unittest.TestCase):
    def setUp(self):
        self.subject = load_subject()

    def test_no_output_is_created_when_external_seal_is_wrong(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'Contract.json'
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_EXTERNAL_SEAL'):
                self.subject.preflight(path, '0' * 64)
            self.assertFalse((Path(temporary) / 'public-cleanup-diagnostic-20261021').exists())

    def test_parser_checks_exit_and_stderr_before_attempting_json(self):
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_CHILD_EXIT'):
            self.subject.parse_public_reply(3, b'', b'underlying child stderr')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_JSON'):
            self.subject.parse_public_reply(0, b'', b'')
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_REPLY_SHAPE'):
            self.subject.parse_public_reply(2, b'[]', b'')

    def test_failed_child_without_json_reports_its_retained_error_not_json_decode(self):
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_CHILD_EXIT.*original child refusal'):
            self.subject.parse_public_reply(2, b'', b'original child refusal')

    def success_reply(self):
        return {'ok':True,'overall':'SOURCE_REOPENED','generation':'a'*64,
                'pack_digest':'b'*64,'units':1,'coverage':'UNVERIFIED',
                'semantic_truth':'UNVERIFIED','evidence_pack':str(Path('expected-pack.json').absolute()),
                'retrieval_backend':'SEMANTICA_OBSERVED','limits_reached':[]}

    def failure_reply(self):
        root = {'relation':'root','type':'ValueError','message':'E_DISTRIBUTED_CLEANUP','frames':[]}
        detail = {'schema_version':1,'truncated':False,'exception':root,'frames':[],
                  'chain':[root,{'relation':'cause','type':'PermissionError','message':'locked',
                                 'frames':[],'errno':13,'filename':'cache.db'}]}
        return {'ok':False,'overall':'BLOCKED','evidence_class':'TEST_ONLY',
                'adapter_calls':0,'approvals_consumed':0,'blockers':[
                    'ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP\n'+
                    self.subject.MARKER+json.dumps(detail)]}

    def test_classifier_requires_a_complete_nonvacuous_expected_success(self):
        expected = Path('expected-pack.json').absolute()
        reply = self.success_reply()
        state, detail = self.subject.classify_public_reply(0, reply, expected)
        self.assertEqual(state, 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')
        self.assertIsNone(detail)
        for key, bad in [('overall','READY'),('units',0),('units',True),('generation',''),
                         ('pack_digest','not-a-hash'),('coverage','COMPLETE'),
                         ('semantic_truth','VERIFIED'),('evidence_pack','wrong-pack.json'),
                         ('retrieval_backend','DIRECT_INSPECTION_DEGRADED'),('limits_reached',['unknown'])]:
            with self.subTest(field=key, value=bad):
                changed = copy.deepcopy(reply); changed[key] = bad
                with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PUBLIC_CONTRACT'):
                    self.subject.classify_public_reply(0, changed, expected)
        for bad in ({'ok':True}, dict(reply, adapter_calls=1), dict(reply, blockers=['contradiction'])):
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PUBLIC_CONTRACT'):
                self.subject.classify_public_reply(0, bad, expected)

    def test_classifier_rejects_wrong_path_authority_and_contradictory_failure(self):
        expected = Path('expected-pack.json').absolute()
        reply = self.failure_reply()
        state, detail = self.subject.classify_public_reply(2, reply, expected)
        self.assertEqual(state, 'CAUSE_OBSERVED_PENDING_REVIEW')
        self.assertEqual(detail['chain'][1]['errno'], 13)
        for key, bad in [('overall','SOURCE_REOPENED'),('evidence_class','READY'),
                         ('adapter_calls',1),('approvals_consumed',1),('adapter_calls',False),
                         ('blockers',reply['blockers']+['another blocker']),
                         ('blockers',['unrelated wrapper\n'+reply['blockers'][0]]),
                         ('blockers',[]),('ok',True)]:
            with self.subTest(field=key, value=bad):
                changed = copy.deepcopy(reply); changed[key] = bad
                with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PUBLIC_CONTRACT'):
                    self.subject.classify_public_reply(2, changed, expected)
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PUBLIC_CONTRACT'):
            self.subject.classify_public_reply(0, reply, expected)
        with self.assertRaisesRegex(ValueError, 'E_CLEANUP_PUBLIC_CONTRACT'):
            self.subject.classify_public_reply(2, self.success_reply(), expected)

    def test_classifier_keeps_missing_cleanup_detail_inconclusive(self):
        reply = self.failure_reply()
        reply['blockers'] = ['ValueError: E_WORKER_FAILED: ValueError: E_DISTRIBUTED_CLEANUP']
        state, detail = self.subject.classify_public_reply(2, reply, Path('expected-pack.json'))
        self.assertEqual(state, 'DIAGNOSTIC_MISSING_OR_TRUNCATED_INCONCLUSIVE')
        self.assertIsNone(detail)

    def test_fixture_matches_the_actual_completion_bytes_and_build_order(self):
        # Invoke the authoritative Completion.setUp, not a copied expected string.
        spec = importlib.util.spec_from_file_location('actual_completion_fixture',
            ROOT/'memory-integrity/tests_v2/test_knowledge_completion.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        actual = module.Completion(); actual.setUp(); self.addCleanup(actual.doCleanups)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); expected, files, mapping = self.subject._fixture_values(output)
            task, store = self.subject._fixture(output, expected)
            self.assertEqual({p.name for p in task.iterdir()}, {'client.py','worker.py','test_sample.py'})
            for name in ('client.py','worker.py','test_sample.py'):
                self.assertEqual((task/name).read_bytes(), (actual.root/name).read_bytes())
            self.assertEqual(store, task/'index')
            self.assertEqual(json.loads((output/'Build-Mapping.json').read_bytes()), actual.map)
            self.assertEqual(self.subject.g.sha((output/'Build-Mapping.json').read_bytes()), expected['mapping_sha256'])
            self.assertEqual(expected['timeout_seconds'], 90)
            self.assertEqual(expected['stages'], ['sources','index','policy-task','public-vector-distributed'])
            source_text = (ROOT/'memory-integrity/tests_v2/test_knowledge_completion.py').read_text(encoding='utf-8')
            self.assertIn('capture_output=True,text=True,timeout='+str(expected['timeout_seconds']), source_text)
            store.mkdir()  # Test-owned stand-in: no numerical runtime in this guard.
            self.subject._fixture_request_files(output, expected)
            self.assertEqual({p.name for p in task.iterdir()},
                             {'client.py','worker.py','test_sample.py','index','policy.json','task.json'})
            self.assertIn(str(task/'vector-distributed-local.json'), expected['argv'])

    def test_authored_fixture_bytes_are_rechecked_after_build_and_public_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); expected = self.subject._fixture_values(output)[0]
            task, store = self.subject._fixture(output, expected)
            self.subject._check_fixture(output, expected, requests_written=False)
            mapping = output/'Build-Mapping.json'; saved = mapping.read_bytes()
            mapping.write_bytes(saved+b' ')
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_FIXTURE_MAPPING_CHANGED'):
                self.subject._check_fixture(output, expected, requests_written=False)
            mapping.write_bytes(saved)  # Only a new test-owned fixture is restored.
            source = task/'worker.py'; original = source.read_bytes()
            source.write_bytes(original+b'# drift')
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_FIXTURE_CHANGED'):
                self.subject._check_fixture(output, expected, requests_written=False)
            source.write_bytes(original)
            store.mkdir(); self.subject._fixture_request_files(output, expected)
            self.subject._check_fixture(output, expected, requests_written=True)
            (task/'policy.json').write_bytes(b'{"forged":true}')
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_FIXTURE_CHANGED'):
                self.subject._check_fixture(output, expected, requests_written=True)

    def test_fixture_refuses_early_request_files_and_unbuilt_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); expected = self.subject._fixture_values(output)[0]
            task, _ = self.subject._fixture(output, expected)
            (task/'policy.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_FIXTURE_STAGE'):
                self.subject._check_fixture(output, expected, requests_written=False)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary); expected = self.subject._fixture_values(output)[0]
            self.subject._fixture(output, expected)
            with self.assertRaisesRegex(ValueError, 'E_CLEANUP_FIXTURE_STAGE'):
                self.subject._check_fixture(output, expected, requests_written=False, index_built=True)

    def test_incomplete_diagnostic_cannot_be_promoted_to_observed_cause(self):
        incomplete = {'truncated': False, 'chain': [{'errno': 13, 'filename': 'cache.db'}]}
        self.assertIsNone(self.subject.diagnostic_from_blockers([
            'E_DISTRIBUTED_CLEANUP\n' + self.subject.MARKER + json.dumps(incomplete)]))

    def test_only_one_complete_marker_with_a_low_level_cause_is_usable(self):
        marker = self.subject.MARKER
        root = {'relation':'root','type':'ValueError','message':'E_DISTRIBUTED_CLEANUP','frames':[]}
        concrete = {'schema_version':1,'truncated':False,'exception':root,'frames':[], 'chain':[
            root, {'relation':'cause','type':'PermissionError','message':'locked',
                   'frames':[],'errno':13,'filename':'cache.db'}]}
        self.assertEqual(self.subject.diagnostic_from_blockers(['E_DISTRIBUTED_CLEANUP\n' + marker + json.dumps(concrete)]), concrete)
        self.assertIsNone(self.subject.diagnostic_from_blockers(['E_DISTRIBUTED_CLEANUP']))
        self.assertIsNone(self.subject.diagnostic_from_blockers([marker + '{broken']))
        self.assertIsNone(self.subject.diagnostic_from_blockers([marker + json.dumps({'truncated': True, 'chain': []})]))
        self.assertIsNone(self.subject.diagnostic_from_blockers([marker + json.dumps({'truncated': False, 'chain': [{'type': 'ValueError'}]})]))
        self.assertIsNone(self.subject.diagnostic_from_blockers([marker + json.dumps(concrete) + '\n' + marker + json.dumps(concrete)]))


if __name__ == '__main__':
    unittest.main()
