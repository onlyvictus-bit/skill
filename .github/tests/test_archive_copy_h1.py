"""COPY-H1 real files, retained fixtures; no historical code is executed."""
import contextlib
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    import archive_copy_h1 as h
except ModuleNotFoundError:
    h = None
import archive_copy_snapshot as strict


class HistoricalHardlinkTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='h1-control-'))
        self.archive = self.root/'archive'; self.archive.mkdir()
        self.scratch = self.archive/'retained-temp/fixture/workspace/old-image'
        self.scratch.mkdir(parents=True)
        self.original = self.scratch/'cache.db'
        self.original.write_bytes(b'old retained cache')
        self.alias = self.scratch/'cache-alias.db'; os.link(self.original,self.alias)
        self.session = '1'*32

    def api(self):
        self.assertIsNotNone(h,'COPY-H1 scoped historical reader is not implemented')
        return h

    def context(self, protected=()):
        mod = self.api()
        policy = mod.make_policy(self.archive,[self.original,self.alias],list(protected))
        return mod.Context(policy)

    @contextlib.contextmanager
    def normal_visibility(self):
        real = os.scandir
        def visible(path):
            if Path(path) == self.archive/'retained-temp':
                raise PermissionError('controlled normal account cannot list old scratch')
            return real(path)
        with mock.patch('os.scandir',side_effect=visible): yield

    def request(self,ctx,phase='BEFORE',binding=None):
        with self.normal_visibility():
            return ctx.scan(self.archive,self.session,phase,binding)

    def copied(self,ctx,req,name='BEFORE'):
        out = self.root/name
        ctx.copy_denied(req,out)
        sha = strict.record(out/'Copies.json')['sha256']
        return out,sha

    def merged(self,ctx,req,out,sha):
        with self.normal_visibility(): return ctx.merge(req,out,sha)

    def pair(self,mutation=None):
        ctx = self.context(); req = self.request(ctx)
        out,sha = self.copied(ctx,req)
        before = self.merged(ctx,req,out,sha)
        if mutation: mutation()
        req2 = self.request(ctx,'AFTER',{'before_sha256':strict.digest(before),'workload_sha256':'e'*64})
        out2,sha2 = self.copied(ctx,req2,'AFTER')
        return ctx,before,self.merged(ctx,req2,out2,sha2)

    def test_two_historical_names_produce_independent_single_link_files(self):
        ctx = self.context(); original_stat = self.original.stat()
        permission = h.permission_digest(self.original)
        out,sha = self.copied(ctx,self.request(ctx))
        paths = [out/'data'/p.relative_to(self.archive) for p in (self.original,self.alias)]
        self.assertEqual([p.read_bytes() for p in paths],[b'old retained cache']*2)
        self.assertEqual([p.stat().st_nlink for p in paths],[1,1])
        self.assertEqual(len({(p.stat().st_dev,p.stat().st_ino) for p in paths}),2)
        self.assertNotIn((original_stat.st_dev,original_stat.st_ino),
                         {(p.stat().st_dev,p.stat().st_ino) for p in paths})
        self.assertEqual(strict.identity(self.original.stat()),strict.identity(original_stat))
        self.assertEqual(h.permission_digest(self.original),permission)
        self.assertEqual(self.original.read_bytes(),b'old retained cache')
        self.assertEqual(self.alias.stat().st_nlink,2)

    def test_unchanged_fresh_original_samples_pass_without_qualification(self):
        ctx,before,after = self.pair()
        result = ctx.compare(before,after)
        self.assertEqual(result['status'],'CONTENT_MATCH_AT_BEFORE_AFTER_SAMPLES')
        self.assertFalse(result['whole_skill_ready'])

    def test_changed_original_is_detected_despite_intact_before(self):
        with self.assertRaisesRegex(ValueError,'CHANGED'):
            ctx,before,after = self.pair(lambda:self.original.write_bytes(b'changed'))
            ctx.compare(before,after)
        old = self.root/'BEFORE/data'/self.original.relative_to(self.archive)
        self.assertEqual(old.read_bytes(),b'old retained cache')

    def test_added_original_is_detected(self):
        ctx,before,after = self.pair(lambda:(self.scratch/'extra').write_bytes(b'new'))
        with self.assertRaisesRegex(ValueError,'CHANGED'): ctx.compare(before,after)

    def test_missing_original_is_detected_without_deleting_it(self):
        def move():
            self.original.rename(self.root/'retained-moved-original')
            self.alias.rename(self.root/'retained-moved-alias')
        ctx,before,after = self.pair(move)
        with self.assertRaisesRegex(ValueError,'CHANGED'): ctx.compare(before,after)

    def test_unlisted_linked_scratch_file_is_refused(self):
        ctx = self.context(); extra = self.scratch/'unlisted'
        os.link(self.original,extra)
        with self.assertRaisesRegex(ValueError,'LINK_SCOPE|LINK_IDENTITY'):
            ctx.copy_denied(self.request(ctx),self.root/'outside-allowlist')

    def test_outside_scratch_link_exception_is_refused(self):
        self.api()
        with self.assertRaisesRegex(ValueError,'SCOPE'):
            h.make_policy(self.archive,[self.archive/'config.json'],[])

    def test_trusted_input_alias_cannot_be_presented_as_scratch_data(self):
        self.api()
        with self.assertRaisesRegex(ValueError,'TRUSTED'):
            self.context(protected=[self.original])

    def test_strict_authoritative_reader_still_refuses_linked_input(self):
        self.context()
        with self.assertRaisesRegex(ValueError,'LINK'): strict.record(self.original)

    def test_altered_copy_cannot_pass_even_with_original_intact(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        (out/'data'/self.original.relative_to(self.archive)).write_bytes(b'forged')
        with self.assertRaisesRegex(ValueError,'CONTENT'): self.merged(ctx,req,out,sha)

    def test_missing_copy_is_refused_and_retained_elsewhere(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        (out/'data'/self.original.relative_to(self.archive)).rename(self.root/'retained-moved-copy')
        with self.assertRaisesRegex(ValueError,'CONTENT'): self.merged(ctx,req,out,sha)

    def test_linked_destination_is_refused(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        os.link(out/'data'/self.original.relative_to(self.archive),self.root/'new-copy-alias')
        with self.assertRaisesRegex(ValueError,'LINK'): self.merged(ctx,req,out,sha)

    def test_existing_destination_is_not_overwritten(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        with self.assertRaises(FileExistsError): ctx.copy_denied(req,out)
        self.assertEqual(strict.record(out/'Copies.json')['sha256'],sha)

    def test_wrong_session_and_phase_copies_are_refused(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        for field,value in [('session','2'*32),('phase','AFTER')]:
            other = copy.deepcopy(req); other[field] = value
            if field == 'phase': other['binding'] = {'before_sha256':'a'*64,'workload_sha256':'b'*64}
            with self.assertRaisesRegex(ValueError,'BINDING'): self.merged(ctx,other,out,sha)

    def test_manifest_has_exact_mapping_verified_batch_and_request_times(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        manifest = strict.load(out/'Copies.json',sha)
        self.assertEqual(manifest['batch']['request_utc'],req['observed_utc'])
        self.assertEqual(manifest['batch']['session'],self.session)
        self.assertEqual(manifest['batch']['phase'],'BEFORE')
        name = self.original.relative_to(self.archive).as_posix()
        row = manifest['files'][name]
        self.assertEqual(row['original'],str(self.original))
        self.assertEqual(row['copy'],str(out/'data'/name))
        self.assertEqual(row['batch_id'],manifest['batch']['id'])
        self.assertEqual(row['verification'],'VERIFIED_CONTENT_COPY_NOT_AUTHENTICATED')
        self.assertEqual(row['size'],18)
        self.assertEqual(row['sha256'],'664060c3688d750c287ee877ab18697a76d020c7c96be866ee1191a318dae64b')

    def test_invalid_timing_mapping_and_completion_are_refused_even_when_rehashed(self):
        ctx = self.context(); req = self.request(ctx); out,sha = self.copied(ctx,req)
        original = strict.load(out/'Copies.json',sha)
        for mutation in (
            lambda doc:doc['batch'].pop('finished_utc'),
            lambda doc:doc['batch'].update(started_utc='not-a-time'),
            lambda doc:doc['batch'].update(phase='AFTER'),
            lambda doc:doc['files'].pop(next(iter(doc['files']))),
            lambda doc:next(iter(doc['files'].values())).update(copy=str(self.root/'wrong')),
            lambda doc:next(iter(doc['files'].values())).update(batch_id='wrong'),
            lambda doc:doc.update(status='PARTIAL')):
            doc = copy.deepcopy(original); mutation(doc)
            (out/'Copies.json').write_bytes(strict.encoded(doc))
            changed = strict.record(out/'Copies.json')['sha256']
            with self.assertRaises(ValueError): self.merged(ctx,req,out,changed)

    def test_midcopy_mutation_retains_partial_output_without_complete_manifest(self):
        ctx = self.context(); req = self.request(ctx); real = ctx.read_file
        def changed(path,destination=None):
            result = real(path,destination)
            if destination is not None: self.original.write_bytes(b'changed during copy')
            return result
        with mock.patch.object(ctx,'read_file',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'CHANGED|IDENTITY'):
                ctx.copy_denied(req,self.root/'interrupted')
        self.assertFalse((self.root/'interrupted/Copies.json').exists())
        self.assertTrue(any((self.root/'interrupted/data').rglob('cache*')))
        with self.assertRaises(FileExistsError): ctx.copy_denied(req,self.root/'interrupted')

    def test_interruption_retains_partial_output_cannot_be_accepted_or_reused(self):
        ctx = self.context(); req = self.request(ctx); real = ctx.read_file
        def interrupted(path,destination=None):
            result = real(path,destination)
            if destination is not None: raise InterruptedError('controlled interruption after first copy')
            return result
        with mock.patch.object(ctx,'read_file',side_effect=interrupted):
            with self.assertRaises(InterruptedError): ctx.copy_denied(req,self.root/'partial')
        self.assertFalse((self.root/'partial/Copies.json').exists())
        with self.assertRaises(FileNotFoundError): ctx.merge(req,self.root/'partial','0'*64)
        with self.assertRaises(FileExistsError): ctx.copy_denied(req,self.root/'partial')

    def test_redirected_destination_is_rejected_before_any_outside_write(self):
        ctx = self.context(); req = self.request(ctx)
        elsewhere = self.root/'elsewhere'; elsewhere.mkdir()
        link = self.root/'redirect'
        if os.name == 'nt':
            subprocess.run([r'C:\Windows\System32\cmd.exe','/c','mklink','/J',str(link),str(elsewhere)],
                           check=True,capture_output=True)
        else: os.symlink(elsewhere,link,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'REDIRECT'): ctx.copy_denied(req,link/'output')
        self.assertEqual(list(elsewhere.iterdir()),[])

    def test_same_inode_change_before_before_capture_is_not_rebaselined(self):
        ctx = self.context(); identity = self.original.stat().st_ino
        self.original.write_bytes(b'different content!')
        self.assertEqual(self.original.stat().st_ino,identity)
        with self.assertRaisesRegex(ValueError,'CHANGED'):
            ctx.copy_denied(self.request(ctx),self.root/'drifted')
        self.assertFalse((self.root/'drifted/Copies.json').exists())

    def test_allowed_path_replaced_by_single_link_file_is_refused(self):
        ctx = self.context()
        self.original.rename(self.root/'retained-old-original')
        self.original.write_bytes(b'old retained cache')
        with self.assertRaisesRegex(ValueError,'CHANGED|IDENTITY'):
            ctx.copy_denied(self.request(ctx),self.root/'replaced')

    def test_invalid_protected_identity_cannot_disable_trusted_alias_check(self):
        self.api()
        policy = h.make_policy(self.archive,[self.original,self.alias],[])
        policy['protected_identities'] = ['not-a-file-identity']
        with self.assertRaisesRegex(ValueError,'POLICY'): h.Context(policy)


if __name__ == '__main__': unittest.main()
