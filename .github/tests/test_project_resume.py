"""Project entry must reject stale or substituted continuity evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/verify_project_resume.py'


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


if __name__=='__main__': unittest.main()
