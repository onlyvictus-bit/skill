"""SR3-COPY DATA behavior; fixtures are inert bytes and retained by the runner."""
import hashlib
import os
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
try:
    import shutdown_copy_data as data
except ModuleNotFoundError:
    data = None


class SnapshotSetContractTests(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix='sr3-copy-data-'))
        self.alpha = self.work / 'original-alpha'
        self.beta = self.work / 'original-beta'
        self.alpha.mkdir(); self.beta.mkdir()
        (self.alpha / 'one.bin').write_bytes(b'alpha original bytes')
        (self.beta / 'two.bin').write_bytes(b'beta original bytes')
        self.session = '1' * 32

    def api(self):
        self.assertIsNotNone(data, 'SR3-COPY DATA layer is not implemented')
        return data

    def snapshots(self):
        return self.api().SnapshotSet({'alpha': self.alpha, 'beta': self.beta}, self.session)

    def test_before_scan_is_complete_multi_root_evidence_with_raw_identity_and_acl_digest(self):
        request = self.snapshots().scan('BEFORE')
        self.assertEqual(request['scope'], 'SR3_COPY_DATA_V1')
        self.assertEqual(request['session'], self.session)
        self.assertEqual(request['phase'], 'BEFORE')
        self.assertIsNone(request['binding'])
        self.assertEqual(set(request['roots']), {'alpha', 'beta'})
        for label, root in [('alpha', self.alpha), ('beta', self.beta)]:
            row = request['roots'][label]
            self.assertEqual(row['root'], str(root.absolute()))
            self.assertEqual(row['objects']['.'], {'kind': 'directory'})
            file_row = row['objects']['one.bin' if label == 'alpha' else 'two.bin']
            self.assertEqual(file_row['identity'][3], file_row['size'])
            self.assertTrue(all(type(value) is int for value in file_row['identity']))
            self.assertEqual(len(file_row['permission_sha256']), 64)
            self.assertEqual(row['unresolved'], {})
            self.assertEqual(len(row['policy_sha256']), 64)

    def test_after_derives_outer_and_per_root_bindings_from_complete_before(self):
        snapshots = self.snapshots(); before = snapshots.scan('BEFORE')
        after = snapshots.scan('AFTER', {'before': before, 'workload_sha256': 'a' * 64})
        self.assertEqual(after['binding'], {'before_sha256': self.api().digest(before), 'workload_sha256': 'a' * 64})
        for label in ('alpha', 'beta'):
            self.assertEqual(after['roots'][label]['binding'], {
                'before_sha256': self.api().digest(self.api().SnapshotSet._raw(before['roots'][label])), 'workload_sha256': 'a' * 64})
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            snapshots.scan('AFTER', {'before_sha256': 'b' * 64, 'workload_sha256': 'a' * 64})

    def test_copy_denied_merges_only_verified_inert_bytes_and_rejects_destination_reuse(self):
        hidden = self.alpha / 'restricted'; hidden.mkdir()
        source = hidden / 'history.py'; source.write_bytes(b'print("inert historical bytes")\n')
        snapshots = self.snapshots()
        original_scandir = os.scandir
        def denied(path):
            if Path(path) == hidden:
                raise PermissionError('controlled normal reader denial')
            return original_scandir(path)
        with mock.patch.object(self.api()._primitives()[0].os, 'scandir', side_effect=denied):
            request = snapshots.scan('BEFORE')
        self.assertEqual(request['roots']['alpha']['unresolved'], {'restricted': 'directory'})
        output = self.work / 'new-readable-copy'
        copies = snapshots.copy_denied(request, output)
        copies_sha = self.api().record(output / 'Copies.json')['sha256']
        self.assertEqual((output / 'alpha' / 'data' / 'restricted' / 'history.py').read_bytes(), source.read_bytes())
        self.assertEqual((output / 'alpha' / 'data' / 'restricted' / 'history.py').stat().st_nlink, 1)
        with self.assertRaises(FileExistsError):
            snapshots.copy_denied(request, output)
        with mock.patch.object(self.api()._primitives()[0].os, 'scandir', side_effect=denied):
            bundle = snapshots.merge(request, output, copies_sha)
        self.assertEqual(bundle['roots']['alpha']['objects']['restricted/history.py']['sha256'],
                         hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(snapshots.file_manifests(bundle)[str(self.alpha.absolute())]['restricted/history.py'],
                         hashlib.sha256(source.read_bytes()).hexdigest())

    def test_tampered_copy_and_wrong_receipt_are_rejected_by_fresh_verification(self):
        hidden = self.alpha / 'restricted'; hidden.mkdir(); (hidden / 'history.bin').write_bytes(b'original')
        snapshots = self.snapshots(); original_scandir = os.scandir
        with mock.patch.object(self.api()._primitives()[0].os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == hidden else original_scandir(path)):
            request = snapshots.scan('BEFORE')
        output = self.work / 'tamper-copy'; copies = snapshots.copy_denied(request, output)
        with self.assertRaisesRegex(ValueError, 'EXTERNAL_HASH'):
            snapshots.merge(request, output, '0' * 64)
        (output / 'alpha' / 'data' / 'restricted' / 'history.bin').write_bytes(b'forged')
        with mock.patch.object(self.api()._primitives()[0].os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == hidden else original_scandir(path)):
            with self.assertRaisesRegex(ValueError, 'CONTENT'):
                snapshots.merge(request, output, self.api().record(output / 'Copies.json')['sha256'])

    def test_both_readers_denied_fails_closed_without_a_copy_manifest(self):
        hidden = self.alpha / 'restricted'; hidden.mkdir(); (hidden / 'history.bin').write_bytes(b'original')
        snapshots = self.snapshots(); original_scandir = os.scandir
        def denied(path):
            if Path(path) == hidden:
                raise PermissionError('controlled denial for both readers')
            return original_scandir(path)
        primitive_os = self.api()._primitives()[0].os
        with mock.patch.object(primitive_os, 'scandir', side_effect=denied):
            request = snapshots.scan('BEFORE')
            output = self.work / 'both-denied'
            with self.assertRaises(PermissionError):
                snapshots.copy_denied(request, output)
        self.assertFalse((output / 'Copies.json').exists())

    def test_compare_requires_fresh_after_binding_and_detects_original_change(self):
        snapshots = self.snapshots(); before_request = snapshots.scan('BEFORE')
        before_copies = snapshots.copy_denied(before_request, self.work / 'before-copy')
        before = snapshots.merge(before_request, self.work / 'before-copy', self.api().record(self.work / 'before-copy' / 'Copies.json')['sha256'])
        (self.alpha / 'one.bin').write_bytes(b'changed after before sample')
        after_request = snapshots.scan('AFTER', {'before': before, 'workload_sha256': 'c' * 64})
        after_copies = snapshots.copy_denied(after_request, self.work / 'after-copy')
        after = snapshots.merge(after_request, self.work / 'after-copy', self.api().record(self.work / 'after-copy' / 'Copies.json')['sha256'])
        with self.assertRaisesRegex(ValueError, 'CONTENT_OR_IDENTITY_CHANGED'):
            snapshots.compare(before, after)

    def test_default_policy_refuses_unknown_hardlinks_and_roots_must_be_disjoint(self):
        os.link(self.alpha / 'one.bin', self.alpha / 'other.bin')
        with self.assertRaisesRegex(ValueError, 'LINK_SCOPE'):
            self.snapshots().scan('BEFORE')
        with self.assertRaisesRegex(ValueError, 'ROOT_OVERLAP'):
            self.api().SnapshotSet({'all': self.work, 'part': self.alpha}, self.session)

    def test_exact_per_root_policy_allows_only_its_sealed_hardlink_identity(self):
        retained = self.alpha / 'retained-temp'; retained.mkdir()
        original = retained / 'original.bin'; original.write_bytes(b'exact link policy bytes')
        alias = retained / 'sealed-alias.bin'; os.link(original, alias)
        policy = self.api()._primitives()[1].make_policy(self.alpha, [original, alias], [])
        snapshots = self.api().SnapshotSet({'alpha': self.alpha, 'beta': self.beta}, self.session,
                                           {'alpha': policy, 'beta': {}})
        self.assertIn('retained-temp/sealed-alias.bin', snapshots.scan('BEFORE')['roots']['alpha']['objects'])
        os.link(original, retained / 'unsealed-alias.bin')
        with self.assertRaisesRegex(ValueError, 'LINK_SCOPE|LINK_IDENTITY'):
            snapshots.scan('BEFORE')

    def test_envelope_rejects_recomputed_cross_root_identity_and_phase_mixups(self):
        snapshots = self.snapshots(); before = snapshots.scan('BEFORE')
        for field, value in [('root', str(self.beta.absolute())), ('session', '2' * 32), ('phase', 'AFTER')]:
            mixed = copy.deepcopy(before); mixed['roots']['alpha'][field] = value
            with self.assertRaisesRegex(ValueError, 'REQUEST|BINDING'):
                snapshots.copy_denied(mixed, self.work / ('bad-' + field))
        bound_output = self.work / 'bound-before'; snapshots.copy_denied(before, bound_output)
        bound_before = snapshots.merge(before, bound_output, self.api().record(bound_output / 'Copies.json')['sha256'])
        after = snapshots.scan('AFTER', {'before': bound_before, 'workload_sha256': 'd' * 64})
        # The scan accepts a full request only for BEFORE; the malformed AFTER root must still fail at the envelope boundary.
        mixed = copy.deepcopy(after); mixed['roots']['alpha']['binding']['workload_sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            snapshots.copy_denied(mixed, self.work / 'bad-workload')

    def test_labels_are_casefold_unique_and_reject_all_windows_device_names(self):
        with self.assertRaisesRegex(ValueError, 'LABEL'):
            self.api().SnapshotSet({'alpha': self.alpha, 'ALPHA': self.beta}, self.session)
        for device in ('COM2', 'COM9', 'LPT2', 'LPT9'):
            with self.assertRaisesRegex(ValueError, 'LABEL'):
                self.api().SnapshotSet({device: self.alpha}, self.session)

    def test_inspect_denied_policies_proposes_only_exact_retained_temp_links(self):
        retained = self.alpha / 'retained-temp'; retained.mkdir()
        original = retained / 'old-cache.bin'; original.write_bytes(b'historical inert cache')
        alias = retained / 'old-cache-alias.bin'; os.link(original, alias)
        snapshots = self.snapshots(); primitive_os = self.api()._primitives()[0].os; real_scandir = os.scandir
        with mock.patch.object(primitive_os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == retained else real_scandir(path)):
            request = snapshots.scan('BEFORE')
        before_names = sorted(path.name for path in self.work.iterdir())
        proposal = snapshots.inspect_denied_policies(request, [])
        self.assertEqual(proposal['scope'], 'SR3_COPY_POLICY_PROPOSAL_V1')
        self.assertEqual(proposal['session'], self.session)
        self.assertEqual(proposal['request_sha256'], self.api().digest(request))
        self.assertEqual(proposal['origin'], 'CURRENT_REQUESTED_HISTORICAL_DATA_READ_NOT_AUTHENTICATED')
        self.assertFalse(proposal['policy_approved'])
        allowed = proposal['roots']['alpha']['allowed']
        self.assertEqual(set(allowed), {'retained-temp/old-cache.bin', 'retained-temp/old-cache-alias.bin'})
        self.assertTrue(all(row['role'] == self.api()._primitives()[1].ROLE for row in allowed.values()))
        self.assertEqual(before_names, sorted(path.name for path in self.work.iterdir()))

    def test_inspect_denied_policies_refuses_protected_outside_and_both_reader_denied(self):
        retained = self.alpha / 'retained-temp'; retained.mkdir()
        original = retained / 'old-cache.bin'; original.write_bytes(b'historical inert cache')
        os.link(original, retained / 'old-cache-alias.bin')
        snapshots = self.snapshots(); primitive_os = self.api()._primitives()[0].os; real_scandir = os.scandir
        with mock.patch.object(primitive_os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == retained else real_scandir(path)):
            request = snapshots.scan('BEFORE')
        info = original.stat()
        with self.assertRaisesRegex(ValueError, 'TRUSTED|PROTECTED'):
            snapshots.inspect_denied_policies(request, [[info.st_dev, info.st_ino]])
        outside = self.beta / 'outside'; outside.mkdir(); other = outside / 'linked.bin'; other.write_bytes(b'not history')
        os.link(other, outside / 'linked-alias.bin')
        outside_snapshots = self.api().SnapshotSet({'beta': self.beta}, self.session)
        with mock.patch.object(primitive_os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == outside else real_scandir(path)):
            outside_request = outside_snapshots.scan('BEFORE')
        with self.assertRaisesRegex(ValueError, 'SCOPE'):
            outside_snapshots.inspect_denied_policies(outside_request, [])
        with mock.patch.object(self.api().os, 'scandir', side_effect=lambda path: (_ for _ in ()).throw(PermissionError()) if Path(path) == retained else real_scandir(path)):
            with self.assertRaises(PermissionError):
                snapshots.inspect_denied_policies(request, [])


if __name__ == '__main__':
    unittest.main()
