"""Successor gate controls; does not run selected Python or the W workload."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import types
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import worker_copy_successor as successor
except ModuleNotFoundError:
    successor = None


class CopySuccessorTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(successor, 'The sealed staged successor is not built')
        return successor

    def test_old_controller_is_pinned_not_executed_as_command(self):
        w = self.api().load_w()
        self.assertEqual(w.HEAD, '923de16c91a9ef4381e7ac975e3a3780f42a4bf5')
        self.assertEqual(hashlib.sha256(w.HERE.read_bytes()).hexdigest(),
                         '7e67e131c752c1f7c947e899d8a3cd8853cf070730ca2b4e089aeeb66752aa8c')

    def test_mandatory_guard_failure_is_not_swallowed_by_copy_route(self):
        c = self.api(); w = c.load_w()
        def denied(): raise PermissionError('mandatory source remains unreadable')
        with mock.patch.object(w, 'legacy', side_effect=denied):
            check = c.mandatory_reader(w)
            with self.assertRaisesRegex(PermissionError, 'mandatory source'):
                check()

    def test_unknown_controller_bytes_cannot_be_adapted(self):
        c = self.api(); w = c.load_w()
        with mock.patch.object(c.s, 'record', return_value={'sha256':'0'*64}):
            with self.assertRaisesRegex(ValueError, 'CONTROLLER_PIN'):
                c.mandatory_reader(w)

    def test_only_supplementary_inventory_is_removed_from_guard(self):
        c = self.api(); w = c.load_w()
        # Execute the extracted function with explicit stop points to establish
        # that original legacy validation still precedes supplementary snapshots.
        called = []
        class Ordered:
            g = m = i = None
            CONTRACT = 'controlled-contract'
        def legacy(): called.append('legacy'); return Ordered()
        def read(*args): called.append('contract'); raise RuntimeError('contract stop')
        with mock.patch.object(w, 'legacy', legacy), mock.patch.object(w, 'read_sealed', read):
            guard = c.mandatory_reader(w)
            with self.assertRaisesRegex(RuntimeError, 'contract stop'): guard()
        self.assertEqual(called, ['legacy','contract'])

    def test_missing_before_does_not_create_workload_claim(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-gate-'))
        with self.assertRaises(FileNotFoundError):
            c.load_before(root, '0'*64)
        self.assertFalse((root/'run/workload-claim').exists())

    def test_pending_runtime_never_claims_preservation(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-result-'))
        receipt = {'status':'OBSERVATIONS_RECORDED_CAUSES_REQUIRE_REVIEW', 'failure':None,
                   'preservation':True, **{k:False for k in c.load_w().FLAGS}}
        c.save_provisional(root/'Receipt.json', receipt)
        observed = json.loads((root/'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(observed['status'], 'PENDING_AFTER_SNAPSHOT')
        self.assertFalse(observed['preservation'])
        self.assertEqual(observed['workload_status'], 'OBSERVATIONS_RECORDED_CAUSES_REQUIRE_REVIEW')
        self.assertFalse(observed['whole_skill_ready'])

    def test_failed_workload_cannot_be_relabelled_success(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-result-'))
        receipt = {'status':'DIAGNOSTIC_BLOCKED_OR_FAILED', 'failure':'original failure',
                   'preservation':False, **{k:False for k in c.load_w().FLAGS}}
        c.save_provisional(root/'Receipt.json',receipt)
        observed = json.loads((root/'Receipt.json').read_text(encoding='utf-8'))
        self.assertEqual(observed['workload_status'], 'DIAGNOSTIC_BLOCKED_OR_FAILED')
        self.assertEqual(observed['failure'], 'original failure')
        self.assertFalse(observed['preservation'])

    def test_premature_qualification_packet_is_rejected(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-result-'))
        receipt = {'status':'OBSERVATIONS_RECORDED_CAUSES_REQUIRE_REVIEW', 'failure':None,
                   'preservation':True, **{k:False for k in c.load_w().FLAGS}}
        receipt['gate1_complete'] = True
        with self.assertRaisesRegex(ValueError, 'QUALIFICATION'):
            c.save_provisional(root/'Receipt.json',receipt)
        self.assertFalse((root/'Receipt.json').exists())

    def test_after_requires_exact_retained_workload(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-after-'))
        with self.assertRaises(FileNotFoundError):
            c.after_binding(root, '0'*64)
        self.assertFalse((root/'after').exists())

    def test_changed_config_role_is_rejected_without_workload(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-config-'))
        path = root/'helper.py'; path.write_bytes(b'initial')
        row = c.s.record(path)
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'ROLE_CHANGED'):
            c.check_roles({str(path):row})
        self.assertFalse((root/'workload-claim').exists())

    def test_existing_provisional_receipt_is_not_overwritten(self):
        c = self.api()
        root = Path(tempfile.mkdtemp(prefix='copy-result-'))
        receipt = {'status':'DIAGNOSTIC_INCOMPLETE', 'failure':None,
                   'preservation':True, **{k:False for k in c.load_w().FLAGS}}
        path = root/'Receipt.json'
        c.save_provisional(path,receipt)
        old = path.read_bytes()
        with self.assertRaises(FileExistsError): c.save_provisional(path,receipt)
        self.assertEqual(path.read_bytes(),old)

    def real_bundle(self,root,source,phase,binding=None):
        c = self.api(); folder = root/phase; folder.mkdir()
        req = c.s.scan(source,c.SESSION,phase.upper(),binding)
        c.s.save(folder/'Request.json',req)
        c.s.copy_denied(req,folder/'reader-copy')
        row = c.s.record(folder/'reader-copy/Copies.json')
        bundle = c.s.merge(req,folder/'reader-copy',row['sha256'])
        c.s.save(folder/'Bundle.json',bundle)
        return bundle,c.s.record(folder/'Bundle.json')

    def test_rehashed_bundle_tampering_cannot_replace_verified_copy_map(self):
        c = self.api(); root = Path(tempfile.mkdtemp(prefix='copy-binding-'))
        source = root/'archive'; source.mkdir(); (source/'task.txt').write_bytes(b'actual')
        bundle,row = self.real_bundle(root,source,'before')
        bundle['objects']['task.txt']['sha256'] = 'f'*64
        (root/'before/Bundle.json').write_bytes(c.s.encoded(bundle))
        altered = c.s.record(root/'before/Bundle.json')
        with mock.patch.object(c,'ROOT',root), mock.patch.object(c,'load_w',return_value=types.SimpleNamespace(ARTIFACTS=source)):
            with self.assertRaisesRegex(ValueError,'BUNDLE'):
                c.verify_existing_bundle('before',altered['sha256'])

    def test_equal_edited_maps_cannot_hide_different_real_before_after_content(self):
        c = self.api(); root = Path(tempfile.mkdtemp(prefix='copy-binding-'))
        source = root/'archive'; source.mkdir(); (source/'task.txt').write_bytes(b'before')
        before,before_row = self.real_bundle(root,source,'before')
        (source/'task.txt').write_bytes(b'after')
        after,after_row = self.real_bundle(root,source,'after',
            {'before_sha256':before_row['sha256'],'workload_sha256':'e'*64})
        after['objects'] = before['objects']
        (root/'after/Bundle.json').write_bytes(c.s.encoded(after))
        edited = c.s.record(root/'after/Bundle.json')
        with mock.patch.object(c,'ROOT',root), mock.patch.object(c,'load_w',return_value=types.SimpleNamespace(ARTIFACTS=source)):
            with self.assertRaisesRegex(ValueError,'BUNDLE'):
                verified,_ = c.verify_existing_bundle('after',edited['sha256'])
                c.s.compare(before,verified)

    def test_workload_from_before_a_cannot_be_rebound_to_before_b(self):
        c = self.api(); root = Path(tempfile.mkdtemp(prefix='copy-binding-'))
        source = root/'archive'; source.mkdir(); (source/'task.txt').write_bytes(b'before')
        before,row = self.real_bundle(root,source,'before')
        (root/'Input-Seal.json').write_bytes(b'{}\n')
        (root/'run').mkdir()
        prepared = {'before':row,'seal':c.s.record(root/'Input-Seal.json'),
                    'source_manifest':{'file'+str(n):'a'*64 for n in range(567)},
                    'history':{'label':'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION',
                               'v3_output':{},'v3_source':{},'transitions':[]}}
        c.s.save(root/'run/Prepared.json',prepared)
        c.s.save(root/'run/Receipt.json',{'status':'PENDING_AFTER_SNAPSHOT','preservation':False,
            'prepared':c.s.record(root/'run/Prepared.json'), **{k:False for k in c.load_w().FLAGS}})
        before['nonce'] = 'b'*32
        (root/'before/Bundle.json').write_bytes(c.s.encoded(before))
        replacement = c.s.record(root/'before/Bundle.json')
        with self.assertRaisesRegex(ValueError,'WORKLOAD_BEFORE'):
            c.after_binding(root,replacement['sha256'])

    def test_valid_exact_prepared_before_binding_is_accepted(self):
        c = self.api(); root = Path(tempfile.mkdtemp(prefix='copy-binding-'))
        source = root/'archive'; source.mkdir(); (source/'task.txt').write_bytes(b'before')
        before,row = self.real_bundle(root,source,'before')
        (root/'Input-Seal.json').write_bytes(b'{}\n'); (root/'run').mkdir()
        prepared = {'before':row,'seal':c.s.record(root/'Input-Seal.json'),
                    'source_manifest':{'file'+str(n):'a'*64 for n in range(567)},
                    'history':{'label':'FIRST_OBSERVATION_NOT_ORIGINAL_PRESERVATION',
                               'v3_output':{},'v3_source':{},'transitions':[]}}
        c.s.save(root/'run/Prepared.json',prepared)
        c.s.save(root/'run/Receipt.json',{'status':'PENDING_AFTER_SNAPSHOT','preservation':False,
            'prepared':c.s.record(root/'run/Prepared.json'), **{k:False for k in c.load_w().FLAGS}})
        wanted = {'before_sha256':row['sha256'],
                  'workload_sha256':hashlib.sha256((root/'run/Receipt.json').read_bytes()).hexdigest()}
        self.assertEqual(c.after_binding(root,row['sha256']),wanted)


if __name__ == '__main__': unittest.main()
