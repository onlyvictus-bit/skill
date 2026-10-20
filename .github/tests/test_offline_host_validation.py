"""Host-only continuation guards; no selected numerical runtime is started."""
import importlib.util
import copy
import sys
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'.github/scripts'/(name+'.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class HostValidation(unittest.TestCase):
    def setUp(self):
        path = ROOT/'.github/scripts/offline_host_validation.py'
        self.assertTrue(path.is_file(), 'missing bounded host continuation')
        self.host = module('offline_host_validation')

    def test_external_input_hash_checked_before_json_or_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'Prepared.json'
            path.write_bytes(b'not JSON')
            with self.assertRaisesRegex(ValueError, 'E_HOST_EXTERNAL_HASH'):
                self.host.load_prepared(path, '0'*64)

    def test_changed_controller_or_package_refuses_before_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root/'script.py'
            file.write_bytes(b'original')
            package = root/'package'
            package.mkdir()
            (package/'input').write_bytes(b'evidence')
            doc = {'files':{str(file):self.host.sha(file.read_bytes())},
                   'packages':{str(package):self.host.inventory(package)}}
            self.host.verify_inputs(doc)
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'E_HOST_INPUT_CHANGED'):
                self.host.verify_inputs(doc)
            doc['files'][str(file)] = self.host.sha(file.read_bytes())
            (package/'input').write_bytes(b'changed evidence')
            with self.assertRaisesRegex(ValueError, 'E_HOST_PACKAGE_CHANGED'):
                self.host.verify_inputs(doc)

    def test_output_inside_a_package_is_refused_before_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root/'new-output'
            with self.assertRaisesRegex(ValueError, 'E_HOST_OUTPUT_IN_PACKAGE'):
                self.host.check_output(output, {'packages':{str(root):{}}})
            self.assertFalse(output.exists())

    def test_runtime_suite_cannot_hide_errors_exclusions_or_windows_skips(self):
        good = {'tests_run':9, 'discovered':9, 'failures':[], 'errors':[],
                'excluded':[], 'expected_failures':[], 'interrupted':False,
                'skipped':[['test_knowledge_distributed.DistributedRetrieval.test_suspended_worker_expires_shared_deadline_and_is_reaped',
                            'POSIX pinned runtime required']]}
        self.host.validate_suite(good, 'test_knowledge_distributed.py')
        for change in ({'errors':['broken']}, {'excluded':['omitted']},
                       {'tests_run':0}, {'expected_failures':['unresolved']},
                       {'skipped':[['test_real_two_worker_result_equals_single_worker','runtime missing']]},
                       {'tests_run':8}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'E_HOST_SUITE'):
                self.host.validate_suite(dict(good, **change), 'test_knowledge_distributed.py')

    def test_existing_output_stays_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root/'keep'
            marker.write_bytes(b'old')
            with self.assertRaisesRegex(ValueError, 'E_OUTPUT_EXISTS'):
                self.host.create_output(root, {'packages':{}})
            self.assertEqual(marker.read_bytes(), b'old')

    def test_hash_valid_incomplete_prepared_cannot_omit_its_guarded_inputs(self):
        original = self.host.prepared(sys.executable)
        for section,key in [('files',str(ROOT/'.github/scripts/retained_unittest.py')),
                            ('files',sys.executable),
                            ('packages',str(ROOT/'memory-integrity'))]:
            value = copy.deepcopy(original)
            value[section].pop(key)
            with self.subTest(section=section,key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                prepared = root/'Prepared.json'
                self.host.save(prepared,value)
                loaded = self.host.load_prepared(prepared,self.host.sha(prepared.read_bytes()))
                with patch.object(self.host,'capture_owned') as child:
                    with self.assertRaisesRegex(ValueError,'E_HOST_SCHEMA'):
                        self.host.execute(loaded,root/'new-output')
                    child.assert_not_called()
                self.assertFalse((root/'new-output').exists())
        for change in ({'packages':{}},{'native_execution':True},
                       {'worker':'python'},{'whole_skill_ready':True}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError,'E_HOST_SCHEMA'):
                self.host.validate_prepared(dict(original,**change))

    def test_physical_alias_inside_package_is_refused_without_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root/'package'
            package.mkdir()
            alias = root/'alias'
            alias.mkdir()
            real_resolve = Path.resolve
            def resolve(path,*args,**kwargs):
                return real_resolve(package,*args,**kwargs) if path == alias else real_resolve(path,*args,**kwargs)
            with patch.object(Path,'resolve',resolve):
                with self.assertRaisesRegex(ValueError,'E_OUTPUT_PHYSICAL_PACKAGE'):
                    self.host.check_output(alias/'new',{'packages':{str(package):{}}})
            self.assertFalse((alias/'new').exists())

    def test_unproven_tree_timeout_retains_streams_and_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = {'exit_code':1,'stdout':b'partial','stderr':b'waiting',
                       'timed_out':True,'capture_complete':False,'capture_errors':['tree uncertain'],
                       'kill_path_used':True,'tree_contained':False,'output_limit_exceeded':False,
                       'containment_method':'test-double','containment_note':'unproven'}
            with patch.object(self.host,'process_capture',return_value=capture) as own:
                proc, record = self.host.capture_owned([sys.executable,'-B','fake.py'],root,ROOT,{},1)
            own.assert_called_once()
            self.assertIsNone(proc)
            self.assertEqual(record['execution'],'TIMEOUT')
            self.assertFalse(record['containment']['tree_contained'])
            self.assertEqual((root/'stdout.log').read_bytes(),b'partial')
            self.assertEqual((root/'stderr.log').read_bytes(),b'waiting')
            self.assertTrue((root/'Command.json').is_file())

    def test_prepare_inside_package_refuses_without_a_write(self):
        destination = ROOT/'memory-integrity/should-never-be-created.json'
        self.assertFalse(destination.exists())
        with self.assertRaisesRegex(ValueError,'E_HOST_OUTPUT_IN_PACKAGE'):
            self.host.prepare_inputs(destination,sys.executable)
        self.assertFalse(destination.exists())
        with tempfile.TemporaryDirectory() as tmp:
            alias = Path(tmp)
            real_resolve = Path.resolve
            def resolve(path,*args,**kwargs):
                return real_resolve(ROOT/'memory-integrity',*args,**kwargs) if path == alias else real_resolve(path,*args,**kwargs)
            with patch.object(Path,'resolve',resolve):
                with self.assertRaisesRegex(ValueError,'E_OUTPUT_PHYSICAL_PACKAGE'):
                    self.host.prepare_inputs(alias/'new.json',sys.executable)
            self.assertFalse((alias/'new.json').exists())

    def test_optional_external_guard_absence_is_bound_and_present_guard_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'fable_guard.py'
            with patch.object(self.host,'optional_guard_path',return_value=path):
                doc = self.host.prepared(sys.executable)
                self.assertEqual(doc['optional_external_consumer'],{
                    'path':str(path),'state':'ABSENT_NOT_EXERCISED'})
                self.host.validate_prepared(doc)
                self.host.verify_inputs(doc)
                path.write_text('raise RuntimeError("must not import")',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'E_HOST_EXTERNAL_CONSUMER'):
                    self.host.verify_inputs(doc)
                with self.assertRaisesRegex(ValueError,'E_HOST_EXTERNAL_CONSUMER'):
                    self.host.prepared(sys.executable)


if __name__ == '__main__':
    unittest.main()
