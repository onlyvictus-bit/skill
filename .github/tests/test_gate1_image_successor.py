"""Regression inputs authored from the captured Store image, never BASE-derived."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT/'.github/scripts/gate1_image_successor.py'
OLD = ROOT/'.github/scripts/gate1_validation.py'
VENV = r'C:\Users\sakth\Documents\Codex\2026-10-02\ad\work\R5-practical-fence-20261013\build-validation\n3-retrieval-9ec6fb1db36444acba2945896e8b8d17\venv'
STORE = r'C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python.3.12_3.12.2800.0_x64__qbz5n2kfra8p0'
ALIAS = r'C:\Users\sakth\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe'
CWD = r'C:\Users\sakth\Documents\Codex\gate1-923de16-20261021\image-successor-20261021'
IMAGE_SHA = '5365b422ee178f691988eb937b7abca5f48910b148f76fcce6dbaf5585c948d0'


def load():
    # Before implementation, exercise the actual predecessor to retain RED.
    spec = importlib.util.spec_from_file_location('image_successor_test_subject',NEW if NEW.exists() else OLD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame_and_env():
    env = {'USERPROFILE':r'C:\Users\sakth','TEMP':CWD+r'\temp','TMP':CWD+r'\temp',
           'SYSTEMROOT':r'C:\windows','SYSTEMDRIVE':'C:','PYTHONNOUSERSITE':'1',
           'PATH':r'C:\retained-fixture-path'}
    frame = {'version':[3,12,10],'executable':VENV+r'\Scripts\python.exe',
             'base_executable':ALIAS,'prefix':VENV,'base_prefix':STORE,
             'image_path':STORE+r'\python3.12.exe','image_sha256':IMAGE_SHA,'cwd':CWD,
             'environment':{'USERPROFILE':r'C:\Users\sakth','TEMP':CWD+r'\temp','TMP':CWD+r'\temp',
                 'SYSTEMROOT':r'C:\windows','SystemDrive':'C:','PYTHONNOUSERSITE':'1'},
             'path_sha256':hashlib.sha256(env['PATH'].encode()).hexdigest(),'model_selected':False}
    return frame,env


class ImageSuccessor(unittest.TestCase):
    def setUp(self):
        self.subject=load()

    def test_recorded_store_filename_is_valid_with_uppercase_windows_env(self):
        frame,env=frame_and_env()
        try:self.subject.validate_runtime_observation(frame,env,Path(CWD))
        except ValueError as error:self.fail('Correct captured Store identity rejected: '+str(error))

    def test_windows_env_casing_alone_is_not_identity_drift(self):
        frame,env=frame_and_env()
        if not NEW.exists():frame['image_path']=STORE+r'\python.exe'
        try:self.subject.validate_runtime_observation(frame,env,Path(CWD))
        except ValueError as error:self.fail('SYSTEMDRIVE vs SystemDrive rejected: '+str(error))

    def test_mixedcase_environment_keys_have_same_windows_meaning(self):
        frame,env=frame_and_env();env={key.lower():value for key,value in env.items()}
        try:self.subject.validate_runtime_observation(frame,env,Path(CWD))
        except ValueError as error:self.fail('Unique case-insensitive environment rejected: '+str(error))

    def test_case_colliding_environment_keys_are_refused(self):
        frame,env=frame_and_env();env['SystemDrive']='D:'
        with self.assertRaises(ValueError):self.subject.validate_runtime_observation(frame,env,Path(CWD))

    def test_same_hash_other_image_or_old_launcher_is_not_loaded_image(self):
        frame,env=frame_and_env()
        for path in (STORE+r'\python.exe',STORE+r'\other.exe',r'C:\other\python3.12.exe'):
            wrong=copy.deepcopy(frame);wrong['image_path']=path
            with self.subTest(path=path),self.assertRaises(ValueError):
                self.subject.validate_runtime_observation(wrong,env,Path(CWD))

    def test_independent_wrong_runtime_fields_are_refused(self):
        frame,env=frame_and_env()
        for key in ('version','executable','base_executable','prefix','base_prefix','image_path',
                    'image_sha256','cwd','environment','path_sha256','model_selected'):
            wrong=copy.deepcopy(frame)
            wrong[key]=[0,0,0] if key=='version' else {} if key=='environment' else True if key=='model_selected' else 'CHANGED'
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.subject.validate_runtime_observation(wrong,env,Path(CWD))

    def test_error_names_the_mismatched_field(self):
        frame,env=frame_and_env();frame['image_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'image_sha256'):
            self.subject.validate_runtime_observation(frame,env,Path(CWD))

    def test_unknown_or_missing_probe_fields_refuse(self):
        frame,env=frame_and_env()
        for value in (dict(frame,unapproved=True),{k:v for k,v in frame.items() if k!='image_path'}):
            with self.subTest(value_keys=sorted(value)),self.assertRaises(ValueError):
                self.subject.validate_runtime_observation(value,env,Path(CWD))

    def contract_fixture(self):
        # Real isolated seal/manifest files, never the user's runtime or history.
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);s=self.subject
        s.g.REPO=root/'repo';s.g.REPO.mkdir()
        s.g.WORKSPACE=root/'workspace';s.g.WORKSPACE.mkdir()
        (s.g.WORKSPACE/'source').mkdir()
        s.HERE=s.g.REPO/'.github/scripts/gate1_image_successor.py'
        s.HERE.parent.mkdir(parents=True);s.HERE.write_bytes(b'non-executable helper fixture')
        s.PREPARED=s.g.WORKSPACE/'Prepared.json'
        s.PREPARED.write_text(json.dumps({'source':str(s.g.WORKSPACE/'source'),'repo':str(s.g.REPO),
            'runtime':{'worker':{'path':'NOT_EXECUTED_FIXTURE'}}}),encoding='utf-8')
        s.PREPARED_SHA=hashlib.sha256(s.PREPARED.read_bytes()).hexdigest()
        s.PRIOR=s.g.WORKSPACE/'old-attempt';s.PRIOR.mkdir()
        (s.PRIOR/'Receipt.json').write_bytes(b'retained predecessor receipt')
        (s.PRIOR/'stdout.log').write_bytes(b'retained predecessor output')
        s.PRIOR_RECEIPT_SHA=hashlib.sha256((s.PRIOR/'Receipt.json').read_bytes()).hexdigest()
        s.IMAGE=root/'image.exe';s.IMAGE.write_bytes(b'x'*172912)
        s.IMAGE_SHA=hashlib.sha256(s.IMAGE.read_bytes()).hexdigest()
        s.OUTPUT=s.g.WORKSPACE/'new-output'
        value=dict(schema_version=1,scope=s.SCOPE,head=s.g.HEAD,
            parent_prepared=s.g.file_record(s.PREPARED),parent_receipt=s.g.file_record(s.PRIOR/'Receipt.json'),
            prior_attempt=s.g.inventory(s.PRIOR),loaded_image=s.g.file_record(s.IMAGE),
            source=str(s.g.WORKSPACE/'source'),output=str(s.OUTPUT),successor_helper=s.g.file_record(s.HERE),
            producer_authentication=False,release_ready=False,installed=False,native_execution=False)
        return root,value

    def test_contract_cannot_substitute_roles_flags_or_helper(self):
        _,value=self.contract_fixture();s=self.subject
        with patch.object(s.g,'validate_prepared'):
            s.validate_contract(value)
            for key in ('source','output','head','release_ready','producer_authentication'):
                wrong=copy.deepcopy(value);wrong[key]=True if isinstance(value[key],bool) else 'SUBSTITUTED'
                with self.subTest(key=key),self.assertRaises(ValueError):s.validate_contract(wrong)
            for key in ('parent_prepared','parent_receipt','loaded_image','successor_helper'):
                wrong=copy.deepcopy(value);wrong[key]['sha256']='0'*64
                with self.subTest(key=key),self.assertRaises(ValueError):s.validate_contract(wrong)

    def test_external_seal_failure_happens_before_output_or_runtime(self):
        root,value=self.contract_fixture();s=self.subject
        contract=root/'Contract.json';s.g.save(contract,value)
        with self.assertRaisesRegex(ValueError,'E_G1_EXTERNAL_SEAL'):
            s.run(contract,'0'*64)
        self.assertFalse(s.OUTPUT.exists())
        self.assertEqual((s.PRIOR/'stdout.log').read_bytes(),b'retained predecessor output')

    def test_old_attempt_extra_or_changed_file_is_not_hidden(self):
        root,value=self.contract_fixture();s=self.subject
        (s.PRIOR/'unexpected.log').write_bytes(b'new unexpected prior output')
        contract=root/'Contract.json';s.g.save(contract,value)
        digest=hashlib.sha256(contract.read_bytes()).hexdigest()
        # Only the older full-source validator is outside this isolated fixture.
        # The new prior-attempt manifest comparison remains real.
        with patch.object(s.g,'validate_prepared'),patch.object(s.g,'check_preserved'):
            with self.assertRaisesRegex(ValueError,'E_G1_CONTENT_CHANGED'):
                s.preflight(contract,digest)
        self.assertFalse(s.OUTPUT.exists())
        self.assertEqual((s.PRIOR/'unexpected.log').read_bytes(),b'new unexpected prior output')

    def test_existing_successor_output_is_retained_and_not_reused(self):
        root,value=self.contract_fixture();s=self.subject
        s.OUTPUT.mkdir();(s.OUTPUT/'keep').write_bytes(b'keep all data')
        contract=root/'Contract.json';s.g.save(contract,value)
        digest=hashlib.sha256(contract.read_bytes()).hexdigest()
        with patch.object(s.g,'validate_prepared'),patch.object(s.g,'check_preserved'):
            with self.assertRaisesRegex(ValueError,'E_IMAGE_EXISTING_ATTEMPT_PRESERVED'):
                s.preflight(contract,digest)
        self.assertEqual((s.OUTPUT/'keep').read_bytes(),b'keep all data')

    def test_malformed_contract_schema_refuses_without_output(self):
        _,value=self.contract_fixture();s=self.subject
        with self.assertRaisesRegex(ValueError,'E_IMAGE_CONTRACT'):
            s.validate_contract(dict(value,caller_says_ready=True))
        self.assertFalse(s.OUTPUT.exists())

    def test_postcreate_import_failure_retains_failed_receipt(self):
        root,value=self.contract_fixture();s=self.subject
        contract=root/'Contract.json';s.g.save(contract,value)
        digest=hashlib.sha256(contract.read_bytes()).hexdigest()
        with patch.object(s.g,'validate_prepared'),patch.object(s.g,'check_preserved'),\
             patch.object(s.g,'sibling_module',side_effect=RuntimeError('injected import failure')),\
             patch.dict(s.os.environ,USERPROFILE=r'C:\Users\sakth'):
            try:s.run(contract,digest)
            except RuntimeError:pass
        self.assertTrue((s.OUTPUT/'Receipt.json').exists(),'postcreate failure lost its outcome receipt')
        receipt=json.loads((s.OUTPUT/'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['status'],'PARTIAL_OR_FAILED_NO_RETRY')
        self.assertIn('injected import failure',receipt['failure'])
        self.assertEqual(receipt['contract']['sha256'],digest)
        self.assertFalse((s.OUTPUT/'evaluation-claim.json').exists())

    def test_postcreate_temp_failure_retains_failed_receipt(self):
        root,value=self.contract_fixture();s=self.subject
        contract=root/'Contract.json';s.g.save(contract,value)
        digest=hashlib.sha256(contract.read_bytes()).hexdigest()
        original=Path.mkdir
        def create(path,*args,**kwargs):
            if path==s.OUTPUT/'temp':raise OSError('injected temp creation failure')
            return original(path,*args,**kwargs)
        with patch.object(s.g,'validate_prepared'),patch.object(s.g,'check_preserved'),\
             patch.object(Path,'mkdir',new=create),patch.dict(s.os.environ,USERPROFILE=r'C:\Users\sakth'):
            try:s.run(contract,digest)
            except OSError:pass
        self.assertTrue((s.OUTPUT/'Receipt.json').exists(),'temp failure lost its outcome receipt')
        receipt=json.loads((s.OUTPUT/'Receipt.json').read_text(encoding='utf-8'))
        self.assertIn('injected temp creation failure',receipt['failure'])
        self.assertEqual(receipt['commands'],[])

    def test_contract_drift_cannot_replace_initial_sealed_binding(self):
        root,value=self.contract_fixture();s=self.subject
        contract=root/'Contract.json';s.g.save(contract,value)
        digest=hashlib.sha256(contract.read_bytes()).hexdigest()
        def drift(*args,**kwargs):
            contract.write_bytes(b'changed after output creation')
            raise RuntimeError('injected load failure after contract drift')
        with patch.object(s.g,'validate_prepared'),patch.object(s.g,'check_preserved'),\
             patch.object(s.g,'sibling_module',side_effect=drift),\
             patch.dict(s.os.environ,USERPROFILE=r'C:\Users\sakth'):
            try:s.run(contract,digest)
            except RuntimeError:pass
        self.assertTrue((s.OUTPUT/'Receipt.json').exists(),'contract-drift failure lost its receipt')
        receipt=json.loads((s.OUTPUT/'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(receipt['contract']['sha256'],digest)
        self.assertFalse(receipt['preservation'])
        self.assertIn('E_IMAGE_CONTRACT_CHANGED',receipt['preservation_failure'])


if __name__=='__main__':unittest.main()
