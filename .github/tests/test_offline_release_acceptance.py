"""Non-vacuous acceptance-harness contract, independent of retrieval ranking."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/offline_release_acceptance.py'


class AcceptanceHarness(unittest.TestCase):
    def module(self):
        self.assertTrue(SCRIPT.is_file(), 'portable acceptance harness is not implemented')
        spec = importlib.util.spec_from_file_location('offline_acceptance', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_failed_child_reports_original_stderr_before_json(self):
        m = self.module()
        with self.assertRaisesRegex(ValueError, 'E_CHILD_EXIT.*ownership refused'):
            m.child_json(subprocess.CompletedProcess([], 128, b'', b'ownership refused'))

    def test_successful_but_empty_child_is_not_accepted(self):
        m = self.module()
        with self.assertRaisesRegex(ValueError, 'E_CHILD_JSON'):
            m.child_json(subprocess.CompletedProcess([], 0, b'', b''))

    def test_existing_output_is_rejected_without_a_write(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'existing'
            path.mkdir()
            (path/'important.txt').write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError, 'E_OUTPUT_EXISTS'):
                m.new_output(path)
            self.assertEqual(list(path.iterdir()), [path/'important.txt'])
            self.assertEqual((path/'important.txt').read_bytes(), b'keep')

    def test_redirected_parent_is_rejected_before_mkdir(self):
        m = self.module()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            output = Path(root)/'new'
            with patch.object(Path, 'is_symlink', return_value=True):
                with self.assertRaisesRegex(ValueError, 'E_OUTPUT_REDIRECT'):
                    m.new_output(output)
            self.assertFalse(output.exists())

    def basis(self, m):
        raw = 'one\nதமிழ்\n'.encode('utf-8')
        sizes = [len(b'one\n'), len(raw)]
        units, start = [], 0
        for number, end in enumerate(sizes, 1):
            units.append({'id':'U%06d'%number,'range':[start,end],
                          'sha256':hashlib.sha256(raw[start:end]).hexdigest()})
            start = end
        sources = {'code':{'path':'code.py','source_sha256':m.sha(raw),
                           'manifest':{'units':units},'authority':'AUTHORITATIVE'}}
        pack = {'coverage':'UNVERIFIED','semantic_audit':'UNVERIFIED',
                'required_units':[{'source_id':'code','unit_id':'U000001'}],
                'units':[{'source_id':'code','unit_id':'U000001','range':units[0]['range'],
                          'text':'one\n','source_sha256':m.sha(raw),'unit_sha256':units[0]['sha256'],
                          'path':'code.py','authority':'AUTHORITATIVE'}]}
        return raw, sources, pack

    def test_source_accounting_rejects_gap_and_reordered_units(self):
        m = self.module()
        raw, sources, _ = self.basis(m)
        units = sources['code']['manifest']['units']
        m.check_manifest(raw, {'units':units})
        for broken in (list(reversed(units)), [units[0]],
                       [dict(units[0], range=[1,4]), units[1]]):
            with self.assertRaisesRegex(ValueError, 'E_SOURCE_ACCOUNTING'):
                m.check_manifest(raw, {'units':broken})

    def test_oversized_line_child_span_ids_are_valid_without_renumbering(self):
        m = self.module()
        raw = b'abcdef'
        units = [{'id':'U000001.1','range':[0,3],'sha256':m.sha(b'abc'),
                  'ordinal':0,'parent':'U000001'},
                 {'id':'U000001.2','range':[3,6],'sha256':m.sha(b'def'),
                  'ordinal':1,'parent':'U000001'}]
        m.check_manifest(raw, {'units':units})
        with self.assertRaisesRegex(ValueError, 'E_SOURCE_ACCOUNTING'):
            m.check_manifest(raw, {'units':[units[0],dict(units[1],id='U000001.1')]})

    def test_required_delivery_cannot_be_omitted(self):
        m = self.module()
        raw, sources, pack = self.basis(m)
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'code.py').write_bytes(raw)
            pack['units'] = []
            with self.assertRaisesRegex(ValueError, 'E_REQUIRED_DELIVERY'):
                m.check_pack(pack, sources, Path(root), pack['required_units'])

    def test_rehashed_foreign_unit_and_false_coverage_refused(self):
        m = self.module()
        raw, sources, pack = self.basis(m)
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'code.py').write_bytes(raw)
            m.check_pack(pack, sources, Path(root), pack['required_units'])
            forged = json.loads(json.dumps(pack))
            forged['units'][0].update(text='lie\n',unit_sha256=m.sha(b'lie\n'))
            with self.assertRaisesRegex(ValueError, 'E_SOURCE_REOPEN'):
                m.check_pack(forged, sources, Path(root), pack['required_units'])
            pack['coverage'] = 'COMPLETE'
            with self.assertRaisesRegex(ValueError, 'E_FALSE_QUALIFICATION'):
                m.check_pack(pack, sources, Path(root), pack['required_units'])

    def test_receipt_cannot_promote_empty_or_incomplete_runtime_measurements(self):
        m = self.module()
        with self.assertRaisesRegex(ValueError, 'E_ACCEPTANCE_INCOMPLETE'):
            m.validate_receipt({'checks':[], 'measurements':[], 'scope':'RANKED_RUNTIME'})
        with self.assertRaisesRegex(ValueError, 'E_ACCEPTANCE_INCOMPLETE'):
            m.validate_receipt({'checks':[{'name':'coding-tests','passed':True}],
                                'measurements':[{'case':'freshness','mode':'lexical'}],
                                'scope':'RANKED_RUNTIME'})

    def test_changed_retained_stream_is_not_validated_by_its_claimed_hash(self):
        m = self.module()
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'stdout.log'
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'E_STREAM_BINDING'):
                m.check_stream({'path':str(path),'size':2,'sha256':m.sha(b'{}')})

    def test_command_logs_cannot_collide_with_project_data(self):
        m = self.module()
        self.assertTrue(hasattr(m, 'command_directory'), 'separate command namespace missing')
        with tempfile.TemporaryDirectory() as root:
            (Path(root)/'project').mkdir()
            path = m.command_directory(Path(root), 'project')
            self.assertEqual(path, Path(root)/'commands/project')
            self.assertTrue(path.is_dir())

    def test_output_inside_package_is_refused_before_creation(self):
        m = self.module()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            package, companion = Path(root)/'mi', Path(root)/'cm'
            package.mkdir()
            companion.mkdir()
            output = package/'DO-NOT-CREATE'
            with patch.object(sys, 'argv', [str(SCRIPT),'--package-root',str(package),
                       '--claude-mon-root',str(companion),'--output-dir',str(output)]):
                with self.assertRaisesRegex(ValueError, 'E_OUTPUT_INSIDE_PACKAGE'):
                    m.main()
            self.assertFalse(output.exists(), 'output was created before package containment refusal')

    def test_safety_refusal_requires_structured_exact_cause_not_stderr_token(self):
        m = self.module()
        self.assertTrue(hasattr(m, 'expected_refusal'), 'strict refusal parser missing')
        good = {'ok':False,'overall':'BLOCKED','evidence_class':'TEST_ONLY',
                'adapter_calls':0,'approvals_consumed':0,'blockers':['ValueError: E_REQUIRED_STALE']}
        m.expected_refusal(subprocess.CompletedProcess([],2,json.dumps(good).encode(),b''),'E_REQUIRED_STALE')
        for item in (subprocess.CompletedProcess([],1,b'',b'Traceback: E_REQUIRED_STALE'),
                     subprocess.CompletedProcess([],2,b'not JSON E_REQUIRED_STALE',b''),
                     subprocess.CompletedProcess([],2,json.dumps(dict(good,blockers=['RuntimeError: E_REQUIRED_STALE'])).encode(),b''),
                     subprocess.CompletedProcess([],2,json.dumps(dict(good,adapter_calls=1)).encode(),b'')):
            with self.assertRaisesRegex(ValueError,'E_EXPECTED_REFUSAL'):
                m.expected_refusal(item,'E_REQUIRED_STALE')

    def test_timeout_keeps_partial_streams_and_command_record(self):
        m = self.module()
        self.assertTrue(hasattr(m, 'capture_command'), 'failure-retaining capture missing')
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            folder = m.command_directory(Path(root),'timeout')
            with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired(['python'],1,output=b'partial',stderr=b'detail')):
                completed, record = m.capture_command(['python'],folder,Path(root),{},1)
            self.assertIsNone(completed)
            self.assertEqual(record['execution'],'TIMEOUT')
            self.assertEqual((folder/'stdout.log').read_bytes(),b'partial')
            self.assertEqual((folder/'stderr.log').read_bytes(),b'detail')
            self.assertEqual(json.loads((folder/'Command.json').read_text(encoding='utf-8')), record)

    def test_spawn_failure_keeps_command_and_empty_streams(self):
        m = self.module()
        self.assertTrue(hasattr(m, 'capture_command'), 'failure-retaining capture missing')
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            folder = m.command_directory(Path(root),'start-error')
            with patch.object(m.subprocess,'run',side_effect=OSError('access denied')):
                completed, record = m.capture_command(['python'],folder,Path(root),{},1)
            self.assertIsNone(completed)
            self.assertEqual(record['execution'],'START_ERROR')
            self.assertIn('access denied',record['failure'])
            m.check_stream(record['stdout'])
            m.check_stream(record['stderr'])

    def test_changed_oracle_or_runtime_refuses_receipt_binding(self):
        m = self.module()
        self.assertTrue(hasattr(m, 'check_bindings'), 'source/oracle/runtime binding missing')
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            project = root/'project'
            project.mkdir()
            (project/'code.py').write_bytes(b'one')
            runtime = root/'python.exe'
            runtime.write_bytes(b'fixture identity only; never executed')
            frozen = root/'Frozen.json'
            frozen.write_bytes(m.canonical({'project':str(project),'source_sha256':m.inventory(project),
                                            'generator_sha256':m.sha(SCRIPT.read_bytes())}))
            receipt = {'fixture_binding':m.stream_record(frozen),
                       'runtime_identity':{'controller':m.stream_record(runtime),'worker':None}}
            m.check_bindings(receipt)
            runtime.write_bytes(b'wrong runtime')
            with self.assertRaisesRegex(ValueError,'E_RUNTIME_BINDING'):
                m.check_bindings(receipt)
            receipt['runtime_identity']['controller'] = m.stream_record(runtime)
            (project/'code.py').write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError,'E_FIXTURE_BINDING'):
                m.check_bindings(receipt)
            (project/'code.py').write_bytes(b'one')
            frozen.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'E_STREAM_BINDING'):
                m.check_bindings(receipt)
