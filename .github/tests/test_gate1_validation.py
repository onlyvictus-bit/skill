"""Gate1 guards must reject missing evidence, not manufacture a runtime pass."""
import copy
import importlib.util
import json
import io
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]


class Gate1Contracts(unittest.TestCase):
    def setUp(self):
        path=ROOT/'.github/scripts/gate1_validation.py'
        self.assertTrue(path.is_file(),'Gate1 successor is not implemented')
        spec=importlib.util.spec_from_file_location('gate1_tests',path)
        self.g=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.g)

    def prepared_basis(self):
        # A portable synthetic contract, not the private Windows snapshot or a
        # claimed executable runtime. Production constants are never modified.
        # Only this freshly imported test module receives fixture identities.
        g=self.g;root=ROOT
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        workspace=Path(temporary.name)/'gate1'
        worker=Path(temporary.name)/'venv/Scripts/python.exe';worker.parent.mkdir(parents=True)
        worker.write_bytes(b'non-executable contract fixture')
        config=worker.parent.parent/'pyvenv.cfg';config.write_bytes(b'fixture only')
        g.REPO=root;g.WORKSPACE=workspace;g.WORKER=worker;g.CONTROLLER=Path(sys.executable);g.BASE=Path(sys.executable)
        g.CONTROLLER_SHA=g.BASE_SHA=g.sha(Path(sys.executable).read_bytes())
        g.WORKER_SHA=g.sha(worker.read_bytes());g.CONFIG_SHA=g.sha(config.read_bytes())
        manifest={'fixture-'+str(i):g.sha(str(i).encode()) for i in range(566)}
        manifest[g.OVERLAY]=g.OVERLAY_NEW
        protected={str(root/n):{'retained':g.sha(n.encode())} for n in ('memory-integrity','claude-mon','%SystemDrive%')}
        historical={str(Path(temporary.name)/'old.json'):g.sha(b'old')}
        ids={str(n):['required_case_'+str(n)] for n in range(len(g.PATTERNS))}
        g.SOURCE_MAP_SHA=g.map_digest(manifest);g.PROTECTED_MAP_SHA=g.map_digest(protected)
        g.HISTORY_MAP_SHA=g.map_digest(historical);g.TEST_IDS_SHA=g.map_digest(ids)
        basis=dict(schema_version=1,scope=g.SCOPE,head=g.HEAD,repo=str(root),
            workspace=str(workspace),source=str(workspace/'source'),source_manifest=manifest,
            overlay=dict(path=g.OVERLAY,old_sha256=g.OVERLAY_OLD,new_sha256=g.OVERLAY_NEW),
            protected=protected,historical=historical,runtime={key:g.file_record(path) for key,path in (
                ('controller',Path(sys.executable)),('worker',worker),('config',config),('base',g.BASE))},
            helpers={},patterns=[list(pair) for pair in g.PATTERNS],test_ids=ids,
            release_ready=False,native_execution=False,installed=False)
        basis['helpers']={n:self.g.file_record(ROOT/'.github/scripts'/n) for n in (
            'gate1_validation.py','gate1_runner.py','gate1_worker_checks.py')}
        if 'source_manifest_record' in self.g.PREPARED_KEYS:
            raw=(json.dumps(basis['source_manifest'],sort_keys=True,ensure_ascii=True)+'\n').encode()
            basis['source_manifest_record']=dict(path=str(Path(basis['workspace'])/'Source-Manifest.json'),size=len(raw),sha256=self.g.sha(raw))
        return basis

    def test_nested_paths_and_helper_substitution_refuse_before_claim(self):
        basis=self.prepared_basis();self.g.validate_prepared(basis)
        for field in ('repo','workspace','source'):
            wrong=copy.deepcopy(basis);wrong[field]=str(ROOT/'unexpected')
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):
                self.g.validate_prepared(wrong)
        wrong=copy.deepcopy(basis);wrong['helpers']['gate1_runner.py']['path']=str(ROOT/'other.py')
        with self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):self.g.validate_prepared(wrong)

    def test_nested_runtime_and_overlay_drift_cannot_be_sealed_as_approved(self):
        basis=self.prepared_basis();self.g.validate_prepared(basis)
        for role in ('controller','worker','config','base'):
            wrong=copy.deepcopy(basis);wrong['runtime'][role]['sha256']='0'*64
            with self.subTest(role=role),self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):
                self.g.validate_prepared(wrong)
        wrong=copy.deepcopy(basis);wrong['overlay']['new_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):self.g.validate_prepared(wrong)

    def test_missing_protection_history_source_or_test_ids_refuse_before_claim(self):
        basis=self.prepared_basis();self.g.validate_prepared(basis)
        for field in ('protected','historical','source_manifest','test_ids'):
            wrong=copy.deepcopy(basis);wrong[field]={}
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):
                self.g.validate_prepared(wrong)
        wrong=copy.deepcopy(basis);wrong['test_ids']['3']=['caller_declared_success']
        with self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):self.g.validate_prepared(wrong)

    def test_source_change_and_new_cache_are_not_hidden(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'source.py').write_bytes(b'original')
            manifest=self.g.inventory(root)
            self.g.verify_manifest(root,manifest)
            (root/'cache.db').write_bytes(b'new relative output')
            with self.assertRaisesRegex(ValueError,'E_G1_CONTENT_CHANGED'):
                self.g.verify_manifest(root,manifest)

    def test_source_hash_change_and_missing_file_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            file=root/'keep.txt';file.write_bytes(b'old')
            manifest=self.g.inventory(root)
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'E_G1_CONTENT_CHANGED'):
                self.g.verify_manifest(root,manifest)
            with self.assertRaisesRegex(ValueError,'E_G1_CONTENT_CHANGED'):
                self.g.verify_manifest(root,dict(manifest,missing='0'*64))

    def test_external_pins_fail_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);file=root/'Prepared.json';file.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'E_G1_EXTERNAL_SEAL'):
                self.g.load_sealed(file,'0'*64)
            self.assertEqual(sorted(p.name for p in root.iterdir()),['Prepared.json'])

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'keep').write_bytes(b'evidence')
            with self.assertRaises(ValueError):self.g.new_workspace(root,[])
            self.assertEqual((root/'keep').read_bytes(),b'evidence')

    def test_destination_in_protected_root_is_refused_before_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);target=root/'forbidden'
            with self.assertRaisesRegex(ValueError,'E_G1_OUTPUT_PROTECTED'):
                self.g.new_workspace(target,[root])
            self.assertFalse(target.exists())

    def outcome(self):
        return {'started':['test_a','test_b'],
                'finished':[{'id':'test_a','outcome':'PASS','reason':''},
                            {'id':'test_b','outcome':'PASS','reason':''}]}

    def test_complete_real_case_set_required_not_positive_count_alone(self):
        row=self.outcome();self.g.validate_outcomes(row,['test_a','test_b'],{})
        for field in ('started','finished'):
            wrong=copy.deepcopy(row);wrong[field].pop()
            with self.assertRaisesRegex(ValueError,'E_G1_CASE_SET'):
                self.g.validate_outcomes(wrong,['test_a','test_b'],{})

    def test_duplicate_foreign_or_failure_outcome_never_passes(self):
        for kind in ('duplicate','foreign','failure'):
            wrong=self.outcome()
            if kind=='duplicate':wrong['started']=['test_a','test_a']
            elif kind=='foreign':wrong['finished'][1]['id']='invented'
            else:wrong['finished'][1]['outcome']='FAIL'
            with self.assertRaises(ValueError):self.g.validate_outcomes(wrong,['test_a','test_b'],{})

    def test_unapproved_skip_and_mismatched_skip_reason_fail(self):
        wrong=self.outcome();wrong['finished'][1].update(outcome='SKIP',reason='runtime missing')
        with self.assertRaisesRegex(ValueError,'E_G1_SKIP'):
            self.g.validate_outcomes(wrong,['test_a','test_b'],{})
        with self.assertRaisesRegex(ValueError,'E_G1_SKIP'):
            self.g.validate_outcomes(wrong,['test_a','test_b'],{'test_b':'POSIX'})
        wrong['finished'][1]['reason']='POSIX-only test'
        self.g.validate_outcomes(wrong,['test_a','test_b'],{'test_b':'POSIX'})

    def test_unknown_prepared_fields_and_qualification_claim_refused(self):
        for value in ({},{'release_ready':True},{'scope':'old-host-a1'}):
            with self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):self.g.validate_prepared(value)

    def test_empty_or_caller_declared_acceptance_not_sufficient(self):
        for value in ({},{'status':'PASS_BOUNDED_RUNTIME','measurements':[]},
                      {'whole_skill_ready':True,'measurements':[{}]*24}):
            with self.assertRaises(ValueError):self.g.validate_acceptance(value)

    def test_actual_unittest_subtest_failure_is_not_counted_as_pass(self):
        runner=self.g.sibling_module('gate1_runner',ROOT/'.github/scripts')
        class Fails(unittest.TestCase):
            def test_work(self):
                with self.subTest(case='bad'):self.assertEqual(1,2)
        records={'started':[],'finished':[]}
        runner.RecordingResult.records=records
        result=unittest.TextTestRunner(stream=io.StringIO(),resultclass=runner.RecordingResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Fails))
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(records['finished'][0]['outcome'],'FAIL')
        with self.assertRaises(ValueError):
            self.g.validate_outcomes(records,records['started'],{})

    def test_actual_unittest_skip_needs_named_optional_contract(self):
        runner=self.g.sibling_module('gate1_runner',ROOT/'.github/scripts')
        class Optional(unittest.TestCase):
            @unittest.skip('runtime missing')
            def test_work(self):pass
        records={'started':[],'finished':[]};runner.RecordingResult.records=records
        unittest.TextTestRunner(stream=io.StringIO(),resultclass=runner.RecordingResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Optional))
        with self.assertRaisesRegex(ValueError,'E_G1_SKIP'):
            self.g.validate_outcomes(records,records['started'],runner.allowed_skips())

    def test_started_without_completed_test_never_passes(self):
        runner=self.g.sibling_module('gate1_runner',ROOT/'.github/scripts')
        records={'started':['test_a'],'finished':[]}
        with self.assertRaisesRegex(ValueError,'E_G1_CASE_SET'):
            self.g.validate_outcomes(records,['test_a'],runner.allowed_skips())

    def test_single_link_replaced_evidence_is_not_trusted_by_size(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'receipt.json';file.write_bytes(b'{"ok":0}')
            digest=self.g.file_record(file)['sha256']
            file.write_bytes(b'{"ok":1}')
            with self.assertRaisesRegex(ValueError,'E_G1_EXTERNAL_SEAL'):
                self.g.load_sealed(file,digest)

    def test_real_recording_runner_keeps_caller_relative_output_after_chdir(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'recorded'
            result=subprocess.run([sys.executable,'-B',str(ROOT/'.github/scripts/gate1_runner.py'),
                '--package-root',str(ROOT/'memory-integrity'),'--pattern','test_knowledge_worker_cwd.py',
                '--output-dir','recorded'],cwd=temp,capture_output=True,timeout=40)
            (Path(temp)/'stdout.log').write_bytes(result.stdout)
            (Path(temp)/'stderr.log').write_bytes(result.stderr)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            report=json.loads((output/'Case-Outcomes.json').read_text(encoding='utf-8'))
            self.g.validate_outcomes(report['outcomes'],report['expected_ids'],{})
            self.assertEqual(len(report['expected_ids']),7)

    def test_read_access_time_change_is_not_content_or_identity_change(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'kept';file.write_bytes(b'unchanged')
            before=file.stat()
            values={name:getattr(before,name) for name in dir(before) if name.startswith('st_')}
            values['st_atime']=before.st_atime+60
            after=SimpleNamespace(**values)
            with patch.object(Path,'stat',side_effect=[before,after,after]):
                record=self.g.file_record(file)
            self.assertEqual(record['sha256'],self.g.sha(b'unchanged'))

    def runtime_frame(self,cwd,env):
        return dict(version=[3,12,10],executable=str(self.g.WORKER),base_executable=str(self.g.ALIAS),
            prefix=str(self.g.WORKER.parent.parent),base_prefix=str(self.g.BASE.parent),
            image_path=str(self.g.BASE),image_sha256=self.g.BASE_SHA,cwd=str(cwd),
            environment={name:env.get(name) for name in ('USERPROFILE','TEMP','TMP','SYSTEMROOT','SystemDrive','PYTHONNOUSERSITE')},
            path_sha256=self.g.sha(env.get('PATH','').encode()),model_selected=False)

    def test_preclaim_runtime_requires_actual_image_cwd_and_context(self):
        env=dict(USERPROFILE=r'C:\Users\sakth',TEMP='owned',TMP='owned',PATH='inherited',PYTHONNOUSERSITE='1')
        frame=self.runtime_frame(ROOT,env)
        self.assertTrue(hasattr(self.g,'validate_runtime_observation'),'preclaim image/context validator missing')
        self.g.validate_runtime_observation(frame,env,ROOT)
        for field in ('base_executable','image_path','image_sha256','cwd','environment','path_sha256'):
            wrong=copy.deepcopy(frame);wrong[field]={} if field=='environment' else 'substituted'
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'E_G1_RUNTIME_OBSERVATION'):
                self.g.validate_runtime_observation(wrong,env,ROOT)

    def test_real_cleanup_is_first_postclaim_operation_not_after_suites(self):
        basis=self.prepared_basis();labels=[]
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'normal';output.mkdir()
            def capture(argv,target,cwd,env,timeout):
                labels.append(target.name)
                if target.name=='preclaim-runtime':
                    (target/'stdout.log').write_text(json.dumps(self.runtime_frame(cwd,env)),encoding='utf-8')
                code=0 if target.name.startswith('preclaim-') else 1
                return subprocess.CompletedProcess(argv,code,b'',b''),{}
            with patch.object(self.g,'load_sealed',return_value=basis),patch.object(self.g,'check_preserved'),\
                 patch.object(self.g,'new_workspace',return_value=output),\
                 patch.object(self.g,'sibling_module',return_value=SimpleNamespace(capture_owned=capture)),\
                 patch.dict(os.environ,USERPROFILE=r'C:\Users\sakth'):
                self.g.run(SimpleNamespace(prepared=__file__,sha256='0'*64))
            self.assertEqual(labels,['preclaim-git','preclaim-runtime','real-worker-cleanup'])

    def test_standalone_source_manifest_record_is_not_optional(self):
        basis=self.prepared_basis()
        self.assertIn('source_manifest_record',basis)
        basis['source_manifest_record']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'E_G1_SCHEMA'):self.g.validate_prepared(basis)

    @unittest.skipUnless(os.name=='nt','Win32 process-image handle check is Windows-only')
    def test_real_process_image_handle_probe_uses_current_controller_only(self):
        with tempfile.TemporaryDirectory() as temp:
            result=subprocess.run([sys.executable,'-B','-c',self.g.runtime_probe()],cwd=temp,
                capture_output=True,timeout=20)
            (Path(temp)/'stdout.log').write_bytes(result.stdout);(Path(temp)/'stderr.log').write_bytes(result.stderr)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            frame=json.loads(result.stdout)
            self.assertEqual(Path(frame['image_path']),Path(sys.executable).resolve(strict=True))
            self.assertEqual(frame['image_sha256'],self.g.sha(Path(sys.executable).read_bytes()))
            self.assertEqual(Path(frame['cwd']),Path(temp))


if __name__=='__main__':unittest.main()
