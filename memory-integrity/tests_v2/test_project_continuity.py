"""Project entry must reject stale or substituted continuity evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/project_continuity.py'


class ProjectResume(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root/'docs/fable/continuity'
        self.folder.mkdir(parents=True)
        self.source = self.root/'decision.txt'
        self.source.write_bytes(b'live persistence is unverified')
        spec = importlib.util.spec_from_file_location('resume', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.basis = {'schema_version':1, 'project_id':'r5',
            'files':{'decision.txt':hashlib.sha256(self.source.read_bytes()).hexdigest()}}
        self.write()

    def write(self):
        (self.folder/'Basis.json').write_text(json.dumps(self.basis))

    def test_valid_basis_checks_original_bytes(self):
        self.assertEqual(self.module.check_basis(self.root)['project_id'],'r5')

    def test_changed_original_blocks(self):
        self.source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'STALE'): self.module.check_basis(self.root)

    def test_missing_original_blocks(self):
        self.basis['files']['missing.txt']='a'*64;self.write()
        with self.assertRaisesRegex(ValueError,'MISSING'): self.module.check_basis(self.root)

    def test_empty_scope_cannot_be_ready(self):
        self.basis['files']={};self.write()
        with self.assertRaisesRegex(ValueError,'SCOPE'): self.module.check_basis(self.root)

    def test_parent_escape_and_absolute_path_refused(self):
        for name in ('../outside.txt',str(self.source),'C:/outside.txt'):
            self.basis['files']={name:'a'*64};self.write()
            with self.assertRaisesRegex(ValueError,'PATH'): self.module.check_basis(self.root)

    def test_duplicate_keys_refused(self):
        (self.folder/'Basis.json').write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError,'DUPLICATE'): self.module.check_basis(self.root)

    def test_fresh_process_observes_saved_files(self):
        result=subprocess.run([sys.executable,'-B',str(SCRIPT),'--project-root',str(self.root),'--basis-only'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'SOURCE_BASIS_VERIFIED')

    def test_stale_basis_does_not_invoke_protected_workflow(self):
        self.source.write_bytes(b'changed')
        with patch.object(self.module.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'STALE'): self.module.resume(self.root)
        run.assert_not_called()

    def resume_fixture(self):
        self.basis.update(source='decision.txt',run_map='decision.txt',expected_units=1)
        self.memory=self.root/'mi';self.companion=self.root/'cm'
        self.basis['skills']={}
        for name,root in (('memory-integrity',self.memory),('claude-mon',self.companion)):
            root.mkdir();(root/'tool.py').write_bytes(b'fixture tool')
            self.basis['skills'][name]={'root':str(root),'files':{'tool.py':hashlib.sha256(b'fixture tool').hexdigest()}}
        self.write()
        return {'ok':True,'overall':'VERIFIED_OFFLINE','evidence_class':'TEST_ONLY',
            'counts':{'units':1,'accepted_results':1},
            'recall':{'mode':'exhaustive','records':[{}],
                'coverage_basis':{'units':1,'source_digest':self.basis['files']['decision.txt']}}}

    def test_generic_ok_without_protected_evidence_refused(self):
        self.resume_fixture()
        with patch.object(self.module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"ok":true}',stderr='')):
            with self.assertRaises(ValueError): self.module.resume(self.root,self.memory,self.companion)

    def test_substituted_skill_root_refused_before_dispatch(self):
        self.resume_fixture()
        with patch.object(self.module.subprocess,'run') as run:
            with self.assertRaises(ValueError): self.module.resume(self.root,self.root/'other',self.companion)
        run.assert_not_called()

    def test_change_during_verification_blocks(self):
        result=self.resume_fixture()
        def mutate(*args,**kwargs):
            self.source.write_bytes(b'concurrent change')
            return SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr='')
        with patch.object(self.module.subprocess,'run',side_effect=mutate):
            with self.assertRaisesRegex(ValueError,'STALE'): self.module.resume(self.root,self.memory,self.companion)

    def test_bound_success_remains_file_recovery_only(self):
        result=self.resume_fixture()
        with patch.object(self.module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr='')):
            value=self.module.resume(self.root,self.memory,self.companion)
        self.assertEqual(value['memory_service_persistence'],'UNVERIFIED')

    def test_readonly_process_guard_rejects_writes_and_network(self):
        for event,args in [('open',('x','w',0)),('os.mkdir',('x',0)),
                           ('os.remove',('x',0)),('socket.connect',('host',0))]:
            with self.subTest(event=event),self.assertRaises(PermissionError):
                self.module.readonly_audit(event,args)
        self.module.readonly_audit('open',('x','r',0))

    def seal_fixture(self):
        self.resume_fixture()
        run=self.root/'run';run.mkdir()
        (run/'manifest.json').write_text('{"units":[{}]}')
        (run/'run-map.json').write_text(json.dumps({'run_dir':str(run),
            'artifact_digests':{'manifest.json':hashlib.sha256((run/'manifest.json').read_bytes()).hexdigest()}}))
        request=self.folder/'Seal-Request.json'
        request.write_text(json.dumps({'schema_version':1,'project_id':'real-project',
            'source':'decision.txt','run_map':'run/run-map.json','files':['decision.txt']}))
        return request.relative_to(self.root).as_posix()

    def test_refresh_requires_exact_previous_basis(self):
        request=self.seal_fixture();before=(self.folder/'Basis.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'LEASE'):
            self.module.seal(self.root,request,self.memory,self.companion)
        self.assertEqual((self.folder/'Basis.json').read_bytes(),before)

    def test_failed_candidate_verification_preserves_current_basis(self):
        request=self.seal_fixture();before=(self.folder/'Basis.json').read_bytes()
        with patch.object(self.module,'resume',side_effect=ValueError('REFUSED')):
            with self.assertRaisesRegex(ValueError,'REFUSED'):
                self.module.seal(self.root,request,self.memory,self.companion,hashlib.sha256(before).hexdigest())
        self.assertEqual((self.folder/'Basis.json').read_bytes(),before)

    def test_refresh_retains_old_basis_and_publishes_verified_one(self):
        request=self.seal_fixture();before=(self.folder/'Basis.json').read_bytes();old=hashlib.sha256(before).hexdigest()
        with patch.object(self.module,'resume',return_value={'status':'VERIFIED_PROJECT_FILE_RECOVERY'}):
            result=self.module.seal(self.root,request,self.memory,self.companion,old)
        self.assertEqual(result['status'],'PROJECT_CHECKPOINT_SEALED')
        self.assertEqual((self.folder/'history'/('Basis-'+old+'.json')).read_bytes(),before)
        self.assertEqual(self.module.check_basis(self.root)['project_id'],'real-project')

    def test_initial_seal_without_previous_basis(self):
        request=self.seal_fixture();(self.folder/'Basis.json').unlink()
        with patch.object(self.module,'resume',return_value={'status':'VERIFIED_PROJECT_FILE_RECOVERY'}):
            self.module.seal(self.root,request,self.memory,self.companion)
        self.assertEqual(self.module.check_basis(self.root)['expected_units'],1)

    def test_existing_publication_lock_is_never_removed(self):
        request=self.seal_fixture();before=(self.folder/'Basis.json').read_bytes()
        lock=self.folder/'Basis.publish.lock';lock.write_bytes(b'other publisher')
        with patch.object(self.module,'resume',return_value={'status':'VERIFIED_PROJECT_FILE_RECOVERY'}):
            with self.assertRaisesRegex(ValueError,'PUBLICATION_LOCKED'):
                self.module.seal(self.root,request,self.memory,self.companion,hashlib.sha256(before).hexdigest())
        self.assertEqual(lock.read_bytes(),b'other publisher')
        self.assertEqual((self.folder/'Basis.json').read_bytes(),before)

    def test_concurrent_basis_change_is_not_overwritten(self):
        request=self.seal_fixture();before=(self.folder/'Basis.json').read_bytes()
        def competing_change(*args):
            (self.folder/'Basis.json').write_bytes(b'concurrent checkpoint')
            return {'status':'VERIFIED_PROJECT_FILE_RECOVERY'}
        with patch.object(self.module,'resume',side_effect=competing_change):
            with self.assertRaisesRegex(ValueError,'BASIS_LEASE'):
                self.module.seal(self.root,request,self.memory,self.companion,hashlib.sha256(before).hexdigest())
        self.assertEqual((self.folder/'Basis.json').read_bytes(),b'concurrent checkpoint')


if __name__=='__main__': unittest.main()
