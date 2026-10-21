"""A diagnostic must preserve source and avoid claiming unobserved causation."""
import copy
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import time

ROOT = Path(__file__).resolve().parents[2]


class CacheCauseProbe(unittest.TestCase):
    def setUp(self):
        path = ROOT/'.github/scripts/cache_cause_probe.py'
        self.assertTrue(path.is_file(),'controlled scratch diagnostic missing')
        spec = importlib.util.spec_from_file_location('cache_probe_test',path)
        self.p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.p)

    def test_filtered_context_carries_no_credentials_or_new_os_variables(self):
        source = {'Path':'tools','SystemRoot':'windows','WINDIR':'windows','TMP':'tmp',
                  'SystemDrive':'C:','ProgramData':'shared','TOKEN':'secret-value'}
        env = self.p.filtered_context(source,Path('owned-scratch'))
        self.assertEqual(env['Path'],'tools')
        self.assertNotIn('TOKEN',env)
        self.assertNotIn('SystemDrive',env)
        self.assertNotIn('ProgramData',env)
        self.assertEqual(env['TMP'],str(Path('owned-scratch')))
        self.assertEqual(env['HF_HUB_OFFLINE'],'1')

    def test_source_filter_inventory_covers_both_actual_boundaries(self):
        rows = self.p.source_filter_inventory()
        self.assertEqual(set(rows),{'single','shard'})
        for row in rows.values():
            self.assertEqual(set(row['keys']),{'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','LANG','LC_ALL'})
            self.assertIs(type(row['explicit_cwd']),bool)

    def test_incomplete_or_changed_protection_is_not_accepted(self):
        value = self.p.basis(sys.executable)
        self.p.verify_basis(value)
        omitted = copy.deepcopy(value)
        omitted['protected_packages'].pop('memory-integrity')
        with self.assertRaisesRegex(ValueError,'E_PROBE_SCHEMA'):
            self.p.verify_basis(omitted)
        wrong = copy.deepcopy(value)
        wrong['protected_packages']['memory-integrity']['SKILL.md']='0'*64
        with self.assertRaisesRegex(ValueError,'E_PROBE_PROTECTED_CHANGED'):
            self.p.verify_basis(wrong)

    def test_existing_or_inside_package_output_never_written(self):
        inside=ROOT/'memory-integrity/probe-must-not-exist'
        with self.assertRaisesRegex(ValueError,'E_OUTPUT_PHYSICAL_PACKAGE'):
            self.p.new_probe_output(inside)
        self.assertFalse(inside.exists())
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'keep').write_bytes(b'old evidence')
            with self.assertRaisesRegex(ValueError,'E_OUTPUT_EXISTS'):
                self.p.new_probe_output(root)
            self.assertEqual((root/'keep').read_bytes(),b'old evidence')

    def test_external_seal_rejects_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            prepared=root/'Prepared.json'
            prepared.write_bytes(b'{}')
            target=root/'unconsumed'
            with self.assertRaisesRegex(ValueError,'E_PROBE_EXTERNAL_HASH'):
                self.p.execute(prepared,'0'*64,target)
            self.assertFalse(target.exists())

    def test_helper_drift_is_not_rebaselined(self):
        value=self.p.basis(sys.executable)
        value['scripts']['cache_cause_probe.py']='0'*64
        with self.assertRaisesRegex(ValueError,'E_PROBE_HELPER_CHANGED'):
            self.p.verify_basis(value)

    def _scratch_venv(self,root):
        folder=root/'venv'
        (folder/'Scripts').mkdir(parents=True)
        base=root/'base'
        base.mkdir()
        (base/'python.exe').write_bytes(b'owned-base-fixture-not-executed')
        worker=folder/'Scripts/python.exe'
        worker.write_bytes(b'owned-launcher-fixture-not-executed')
        cfg=folder/'pyvenv.cfg'
        cfg.write_text('home = '+str(base)+'\ninclude-system-site-packages = false\n'
                       'version = 3.12.10\nexecutable = '+str(base/'python.exe')+'\n',encoding='utf-8')
        return worker,cfg,base/'python.exe'

    def test_venv_configuration_and_base_binary_drift_are_refused(self):
        self.assertTrue(callable(getattr(self.p,'runtime_binding',None)),'runtime configuration binding absent')
        with tempfile.TemporaryDirectory() as temp:
            worker,cfg,base=self._scratch_venv(Path(temp))
            binding=self.p.runtime_binding(worker)
            self.assertEqual(binding['version'],[3,12,10])
            self.p.verify_runtime_binding(worker,binding)
            original=cfg.read_bytes()
            cfg.write_bytes(original+b'# modified owned fixture\n')
            with self.assertRaisesRegex(ValueError,'E_PROBE_RUNTIME_CHANGED'):
                self.p.verify_runtime_binding(worker,binding)
            cfg.write_bytes(original)
            base.write_bytes(b'changed-owned-base')
            with self.assertRaisesRegex(ValueError,'E_PROBE_RUNTIME_CHANGED'):
                self.p.verify_runtime_binding(worker,binding)

    def test_startup_validates_reported_version_and_cwd(self):
        self.assertTrue(callable(getattr(self.p,'startup_identity',None)),'startup identity validator absent')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            worker,_,base=self._scratch_venv(root)
            binding=self.p.runtime_binding(worker)
            identity={'version':[3,12,10],'executable':str(worker),'base_executable':str(base),
                      'prefix':str(worker.parent.parent),'base_prefix':str(base.parent),'cwd':str(root)}
            def completed(value):
                return subprocess.CompletedProcess([],0,json.dumps(value).encode('utf-8'),b'')
            checked=self.p.startup_identity(completed(identity),worker,binding,root)
            self.assertEqual(checked['version'],[3,12,10])
            wrong=dict(identity,version=[3,13,0])
            with self.assertRaisesRegex(ValueError,'E_PROBE_STARTUP_IDENTITY'):
                self.p.startup_identity(completed(wrong),worker,binding,root)
            with self.assertRaisesRegex(ValueError,'E_PROBE_STARTUP_IDENTITY'):
                self.p.startup_identity(completed(dict(identity,cwd=str(base.parent))),worker,binding,root)
            with self.assertRaisesRegex(ValueError,'E_PROBE_STARTUP_IDENTITY'):
                self.p.startup_identity(completed({}),worker,binding,root)
            with self.assertRaisesRegex(ValueError,'E_PROBE_STARTUP_IDENTITY'):
                self.p.startup_identity(subprocess.CompletedProcess([],0,b'not-json',b''),worker,binding,root)

    def test_unreadable_base_is_explicitly_unverified_not_authenticated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            worker,cfg,_=self._scratch_venv(root)
            absent=root/'not-created/python.exe'
            cfg.write_text('home = '+str(absent.parent)+'\ninclude-system-site-packages = false\n'
                           'version = 3.12.10\nexecutable = '+str(absent)+'\n',encoding='utf-8')
            binding=self.p.runtime_binding(worker)
            self.assertIsNone(binding['base_file'])
            self.assertEqual(binding['base_binary_authentication'],'UNVERIFIED_CACHE_CAUSE_ONLY')
            self.p.verify_runtime_binding(worker,binding)
            binding['base_binary_authentication']='HASH_BOUND'
            with self.assertRaisesRegex(ValueError,'E_PROBE_RUNTIME_CHANGED'):
                self.p.verify_runtime_binding(worker,binding)

    def test_prior_artifact_drift_is_not_accepted_as_preserved(self):
        self.assertTrue(callable(getattr(self.p,'verify_artifacts',None)),'prior artifact binding absent')
        with tempfile.TemporaryDirectory() as temp:
            prior=Path(temp)/'Prior-Receipt.json'
            prior.write_bytes(b'{"historical":true}')
            binding={str(prior):self.p.stream_record(prior)}
            self.p.verify_artifacts(binding)
            prior.write_bytes(b'{"historical":false}')
            with self.assertRaisesRegex(ValueError,'E_PROBE_PRIOR_CHANGED'):
                self.p.verify_artifacts(binding)

    def test_hashed_but_omitted_prior_set_refuses_before_output(self):
        value=self.p.basis(sys.executable)
        value['historical_artifacts']={}
        with tempfile.TemporaryDirectory() as temp:
            prepared=Path(temp)/'Prepared.json'
            self.p.save(prepared,value)
            target=Path(temp)/'unconsumed'
            with self.assertRaisesRegex(ValueError,'E_PROBE_HISTORICAL_SET'):
                self.p.execute(prepared,self.p.sha(prepared.read_bytes()),target)
            self.assertFalse(target.exists())

    def test_one_new_cache_does_not_become_exact_cache_reproduction(self):
        row={'%SystemDrive%/ProgramData/Microsoft/Windows/Caches/cversions.2.db':{'sha256':'0'*64,'bytes':1}}
        control={'version':[3,14,3],'executable':'control','base_executable':'control','prefix':'control','base_prefix':'control'}
        worker={'version':[3,12,10],'executable':'venv','base_executable':'base','prefix':'venv','base_prefix':'base'}
        self.assertEqual(self.p.cache_paths(row),list(row))
        self.assertEqual(self.p.classify([{'arm':'startup-control','created':{},'cwd':'control','exit_code':0},
                                         {'arm':'startup-a','created':row,'cwd':'a','exit_code':0}]),
                         'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING')
        self.assertEqual(self.p.classify([{'arm':'startup-control','created':{},'cwd':'control','exit_code':0,'runtime_identity':control},
                                         {'arm':'startup-a','created':row,'cwd':'a','exit_code':0,'runtime_identity':worker},
                                         {'arm':'startup-b','created':row,'cwd':'b','exit_code':0,'runtime_identity':worker}]),
                         'RELATIVE_CACHE_WRITE_REPEATED_IN_DISTINCT_STARTUP_CWDS')

    def test_mismatched_startup_identities_cannot_establish_cause(self):
        row={'%SystemDrive%/ProgramData/Microsoft/Windows/Caches/cversions.2.db':'a'*64}
        control={'version':[3,14,3],'executable':'control','base_executable':'control','prefix':'control','base_prefix':'control'}
        worker={'version':[3,12,10],'executable':'venv','base_executable':'base','prefix':'venv','base_prefix':'base'}
        rows=[{'arm':'startup-control','created':{},'cwd':'control','exit_code':0,'runtime_identity':control},
              {'arm':'startup-a','created':row,'cwd':'a','exit_code':0,'runtime_identity':worker},
              {'arm':'startup-b','created':row,'cwd':'b','exit_code':0,'runtime_identity':dict(worker,version=[3,13,0])}]
        self.assertEqual(self.p.classify(rows),'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING')
        rows[2]['runtime_identity']=dict(worker,base_executable='different-base')
        self.assertEqual(self.p.classify(rows),'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING')

    def test_file_change_is_reported_not_omitted_as_cache(self):
        before={'source':{'sha256':'a'*64,'bytes':1}}
        after={'source':{'sha256':'b'*64,'bytes':1},'new':{'sha256':'c'*64,'bytes':2}}
        self.assertEqual(self.p.changes(before,after),{
            'added':{'new':after['new']},'missing':{},
            'modified':{'source':{'before':before['source'],'after':after['source']}}})

    def test_failed_or_same_cwd_startups_are_not_causal_proof(self):
        row={'%SystemDrive%/ProgramData/Microsoft/Windows/Caches/example.db':'a'*64}
        rows=[{'arm':'startup-control','cwd':'control','exit_code':0,'created':{}},
              {'arm':'startup-a','cwd':'same','exit_code':0,'created':row},
              {'arm':'startup-b','cwd':'same','exit_code':0,'created':row}]
        self.assertEqual(self.p.classify(rows),'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING')
        rows[2].update(cwd='different',exit_code=1)
        self.assertEqual(self.p.classify(rows),'DIAGNOSTIC_PARTIAL_OR_NONREPRODUCING')

    @patch.dict(os.environ,{'TOKEN_FOR_PROBE':'never-print-this-value','SystemDrive':'C:'})
    def test_source_boundaries_keep_filtered_context_and_isolate_relative_writes(self):
        """Real subprocesses + authored echo, NOT numerical/runtime/cache-cause proof."""
        sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
        from knowledge_bridge.worker_client import _process
        from knowledge_bridge import distributed_retrieval as shard
        with tempfile.TemporaryDirectory() as temp:
            scratch=Path(temp)
            script=scratch/'distributed_worker.py'
            script.write_text('import json,os\nfrom pathlib import Path\n'
                              'Path("authored-relative-output").write_bytes(b"scratch-only")\n'
                              'print(json.dumps({"ok":True,"cwd":os.getcwd(),"keys":sorted(os.environ)}))\n',
                              encoding='utf-8')
            parent=Path.cwd()
            os.chdir(scratch)
            try:
                digest=self.p.sha(Path(sys.executable).read_bytes())
                first=_process(sys.executable,script,{},5,digest)
                self.assertNotEqual(Path(first['cwd']).resolve(),scratch.resolve())
                self.assertNotIn('TOKEN_FOR_PROBE',first['keys'])
                self.assertNotIn('SYSTEMDRIVE',{key.upper() for key in first['keys']})
                self.assertFalse((scratch/'authored-relative-output').exists())
                with patch.object(shard,'__file__',str(scratch/'distributed_retrieval.py')):
                    session=shard._Session(sys.executable,'probe','not-a-real-lease',time.monotonic()+5)
                    try:
                        self.assertEqual(session.process.wait(timeout=5),0)
                        session.reader.seek(0)
                        second=json.loads(session.reader.read())
                        self.assertEqual(Path(second['cwd']).resolve(),Path(session.directory.name).resolve())
                        self.assertNotEqual(Path(second['cwd']).resolve(),scratch.resolve())
                        self.assertEqual((Path(session.directory.name)/'authored-relative-output').read_bytes(),b'scratch-only')
                        self.assertNotIn('TOKEN_FOR_PROBE',second['keys'])
                        self.assertNotIn('SYSTEMDRIVE',{key.upper() for key in second['keys']})
                    finally:
                        session.close()
            finally:
                os.chdir(parent)


if __name__=='__main__':
    unittest.main()
