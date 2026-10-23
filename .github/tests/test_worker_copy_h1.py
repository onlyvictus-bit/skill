"""H1 closed controller binding; no selected runtime or numerical workload."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import worker_copy_h1 as c
except ModuleNotFoundError:
    c = None
import archive_copy_h1 as h
import archive_copy_snapshot as v
import worker_copy_successor as old


class CopyH1ControllerTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(c,'COPY-H1 sealed successor controller is not built')
        return c

    def fixture(self):
        self.api()
        root = Path(tempfile.mkdtemp(prefix='h1-controller-'))
        archive = root/'archive'; archive.mkdir(); (archive/'public').write_bytes(b'actual')
        run = root/'new-run'; run.mkdir()
        context = h.Context(h.make_policy(archive,[],[]))
        fake_w = types.SimpleNamespace(ARTIFACTS=archive,FLAGS=old.load_w().FLAGS)
        ns = c.bind(context,run,'1'*32)
        ns['load_w'] = lambda:fake_w
        return root,archive,run,context,ns

    def bundle(self,run,archive,context,phase,binding=None):
        folder = run/phase; folder.mkdir()
        request = context.scan(archive,'1'*32,phase,binding)
        v.save(folder/'Request.json',request)
        context.copy_denied(request,folder/'reader-copy')
        digest = v.record(folder/'reader-copy/Copies.json')['sha256']
        result = context.merge(request,folder/'reader-copy',digest)
        v.save(folder/'Bundle.json',result)
        return result,v.record(folder/'Bundle.json')

    def test_missing_before_stops_without_a_workload_claim(self):
        root,archive,run,ctx,ns = self.fixture()
        with self.assertRaises(FileNotFoundError): ns['load_before'](run,'0'*64)
        self.assertFalse((run/'run').exists())

    def test_edited_rehashed_bundle_must_be_derived_from_actual_copy_bytes(self):
        root,archive,run,ctx,ns = self.fixture()
        bundle,row = self.bundle(run,archive,ctx,'BEFORE')
        bundle['objects']['public']['sha256'] = 'f'*64
        (run/'BEFORE/Bundle.json').write_bytes(v.encoded(bundle))
        sha = v.record(run/'BEFORE/Bundle.json')['sha256']
        with self.assertRaisesRegex(ValueError,'BUNDLE_DERIVATION'):
            ns['verify_existing_bundle']('before',sha)

    def test_valid_before_uses_new_session_root_and_uppercase_phase_only(self):
        root,archive,run,ctx,ns = self.fixture()
        bundle,row = self.bundle(run,archive,ctx,'BEFORE')
        actual,_ = ns['verify_existing_bundle']('before',row['sha256'])
        self.assertEqual(actual,bundle)
        self.assertFalse((run/'before').exists() and (run/'before') != (run/'BEFORE'))
        self.assertEqual(ns['ROOT'],run)

    def test_old_controller_globals_and_paths_never_change(self):
        self.api(); before = (old.ROOT,old.SESSION,old.s)
        self.fixture()
        self.assertEqual((old.ROOT,old.SESSION,old.s),before)

    def test_workload_bound_to_different_before_is_rejected(self):
        root,archive,run,ctx,ns = self.fixture()
        bundle,row = self.bundle(run,archive,ctx,'BEFORE')
        (run/'run').mkdir(); v.save(run/'Input-Seal.json',{})
        prepared = {'before':{**row,'sha256':'a'*64},'seal':v.record(run/'Input-Seal.json'),
                    'source_manifest':{'s'+str(n):'b'*64 for n in range(567)},
                    'history':{'label':'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION',
                               'v3_output':{},'v3_source':{},'transitions':[]}}
        v.save(run/'run/Prepared.json',prepared)
        v.save(run/'run/Receipt.json',{'status':'PENDING_AFTER_SNAPSHOT','preservation':False,
            'prepared':v.record(run/'run/Prepared.json'),**{k:False for k in old.load_w().FLAGS}})
        with self.assertRaisesRegex(ValueError,'WORKLOAD_BEFORE'):
            ns['after_binding'](run,row['sha256'])

    def test_pending_workload_remains_not_preserved_and_unqualified(self):
        root,archive,run,ctx,ns = self.fixture()
        receipt = {'status':'DIAGNOSTIC_BLOCKED_OR_FAILED','failure':'real failure',
                   **{k:False for k in old.load_w().FLAGS}}
        ns['save_provisional'](run/'Receipt.json',receipt)
        saved = json.loads((run/'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['workload_status'],'DIAGNOSTIC_BLOCKED_OR_FAILED')
        self.assertFalse(saved['preservation'])
        self.assertEqual(saved['failure'],'real failure')

    def test_original_failure_history_change_is_not_silently_rebaselined(self):
        self.api(); root = Path(tempfile.mkdtemp(prefix='h1-history-'))
        history = root/'old'; history.mkdir(); (history/'Failure.json').write_bytes(b'original')
        expected = v.collect(history)[0]
        (history/'Failure.json').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'FAILED_HISTORY_CHANGED'):
            c.check_failed_history(history,expected)

    def test_mandatory_reader_still_propagates_access_failure(self):
        self.api(); w = old.load_w()
        with mock.patch.object(w,'legacy',side_effect=PermissionError('mandatory inaccessible')):
            with self.assertRaises(PermissionError): old.mandatory_reader(w)()

    def test_real_input_ids_and_failed_history_survive_serialization_exactly(self):
        self.api()
        policy = v.load(c.POLICY,v.record(c.POLICY)['sha256'])
        entry = v.load(c.ENTRY,v.record(c.ENTRY)['sha256'])
        for name,expected in policy['allowed'].items():
            path = Path(policy['root'])/name
            self.assertEqual(expected['identity'],v.identity(path.stat()),name)
            self.assertEqual(h.Context(policy).read_file(path),
                             entry['scope_observation']['allowed_historical_paths'][name])
        self.assertEqual(v.collect(old.ROOT)[0],entry['old_objects'])

    def test_recorded_scope_cannot_disagree_with_policy_or_hide_omissions(self):
        self.api()
        self.assertTrue(callable(getattr(c,'validate_scope_entry',None)),
                        'The sealed policy/entry semantic binding is missing')
        policy = v.load(c.POLICY,v.record(c.POLICY)['sha256'])
        entry = v.load(c.ENTRY,v.record(c.ENTRY)['sha256'])
        forged = copy.deepcopy(entry)
        forged['scope_observation']['allowed_historical_paths'].pop(next(iter(policy['allowed'])))
        with self.assertRaisesRegex(ValueError,'SCOPE_ENTRY'):
            c.validate_scope_entry(policy,forged)

    def test_scope_entry_cannot_reclassify_an_unknown_link_as_known_fixture(self):
        self.api()
        self.assertTrue(callable(getattr(c,'validate_scope_entry',None)),
                        'The historical fixture origin check is missing')
        policy = v.load(c.POLICY,v.record(c.POLICY)['sha256'])
        entry = v.load(c.ENTRY,v.record(c.ENTRY)['sha256'])
        forged = copy.deepcopy(entry)
        next(iter(forged['scope_observation']['allowed_historical_paths'].values()))['sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError,'SCOPE_ENTRY'):
            c.validate_scope_entry(policy,forged)


if __name__ == '__main__': unittest.main()
