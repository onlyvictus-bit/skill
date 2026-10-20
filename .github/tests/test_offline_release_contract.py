"""Successor content selection and preservation, without generating a release."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = {'id':'offline-first-v1','native_subprocesses_enabled':False,
           'native_mutations_enabled':False,'live_provider_enabled':False}


class ReleaseContent(unittest.TestCase):
    def setUp(self):
        path = ROOT/'memory-integrity/scripts/integrity_v2/release_content.py'
        self.assertTrue(path.is_file(), 'missing successor content consumer')
        spec = importlib.util.spec_from_file_location('offline_content',path)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'tests_v2').mkdir()
        (self.root/'SKILL.md').write_bytes(b'original skill\n')
        self.caps = {'engine':'fixture','engine_version':'2.0.0-m13',
                     'active_release_profile':PROFILE,
                     'active_content_manifest':'tests_v2/OFFLINE1-CONTENT.json'}
        self.write_caps()
        self.save('tests_v2/baseline-r1.json',{'files':[{'path':'SKILL.md',
                  'bytes':len(b'original skill\n'),
                  'sha256':hashlib.sha256(b'original skill\n').hexdigest()}]})
        self.save('tests_v2/R4-CONTENT.json',{'historical':'unchanged'})

    def save(self,name,value):
        (self.root/name).write_text(json.dumps(value),encoding='utf-8')

    def write_caps(self):
        self.save('capabilities-v2.json',self.caps)

    def test_active_selection_never_falls_back_when_missing_or_corrupt(self):
        with self.assertRaisesRegex(ValueError,'E_CONTENT_MISSING'):
            self.mod.verify_content(self.root)
        self.save('tests_v2/OFFLINE1-CONTENT.json',{'files':{}})
        with self.assertRaisesRegex(ValueError,'E_CONTENT_DRIFT'):
            self.mod.verify_content(self.root)

    def test_wrong_profile_pointer_and_duplicate_json_refuse(self):
        for pointer in ('tests_v2/R4-CONTENT.json','../outside.json',None):
            self.caps['active_content_manifest'] = pointer
            self.write_caps()
            with self.assertRaisesRegex(ValueError,'E_CONTENT_SELECTION'):
                self.mod.selected_name(self.root)
        (self.root/'capabilities-v2.json').write_text(
            '{"active_release_profile":{},"active_release_profile":{}}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'E_CONTENT_DUPLICATE'):
            self.mod.selected_name(self.root)

    def test_old_manifest_is_hashed_and_only_active_excludes_itself(self):
        value = self.mod.content_document(self.root)
        self.assertIn('tests_v2/R4-CONTENT.json', value['files'])
        self.assertNotIn('tests_v2/OFFLINE1-CONTENT.json', value['files'])
        self.save('tests_v2/OFFLINE1-CONTENT.json',value)
        self.assertEqual(self.mod.verify_content(self.root),value)
        self.save('tests_v2/R4-CONTENT.json',{'historical':'tampered'})
        with self.assertRaisesRegex(ValueError,'E_CONTENT_DRIFT'):
            self.mod.verify_content(self.root)

    def test_original_content_deletion_and_skill_prefix_change_refuse(self):
        (self.root/'SKILL.md').write_bytes(b'changed skill\n')
        with self.assertRaisesRegex(ValueError,'E_CONTENT_SKILL_PREFIX'):
            self.mod.content_document(self.root)
        self.save('tests_v2/baseline-r1.json',{'files':[{'path':'missing-original','bytes':1,'sha256':'0'*64}]})
        with self.assertRaisesRegex(ValueError,'E_CONTENT_ORIGINAL_MISSING'):
            self.mod.content_document(self.root)

    def test_added_and_changed_lists_are_measured_not_caller_claimed(self):
        (self.root/'new-data').write_bytes(b'new')
        value = self.mod.content_document(self.root)
        self.assertIn('new-data',value['added_files'])
        self.assertEqual(value['changed_r1_files'],[])
        self.save('tests_v2/OFFLINE1-CONTENT.json',dict(value,added_files=[]))
        with self.assertRaisesRegex(ValueError,'E_CONTENT_DRIFT'):
            self.mod.verify_content(self.root)

    def test_packaged_consumers_are_identical_and_legacy_selection_still_works(self):
        mi = ROOT/'memory-integrity/scripts/integrity_v2/release_content.py'
        cm = ROOT/'claude-mon/scripts/complete_read_v2/release_content.py'
        self.assertTrue(cm.is_file())
        self.assertEqual(mi.read_bytes(),cm.read_bytes())
        self.save('capabilities-v2.json',{'engine':'old'})
        self.assertEqual(self.mod.selected_name(self.root),'tests_v2/R4-CONTENT.json')


if __name__ == '__main__':
    unittest.main()
