"""Native read-only READY access, parent copy fallback and three-day expiry."""
import ctypes
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).absolute().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
MODULE=ROOT/'scripts/knowledge_bridge/windows_ready_copy.py'
if MODULE.exists():
    from knowledge_bridge import windows_ready_copy as ready
else:ready=None


@unittest.skipUnless(os.name=='nt','Windows native file handles required')
class ReadOnlyCopies(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(ready,'missing strict READY reader and managed copy fallback')
        self.root=Path(tempfile.mkdtemp(prefix='ready-copy-proof-'));self.token='a'*64
        self.source=self.root/('owned-bootstrap-'+self.token+'.ready.json');self.cache=self.root/'ready-copies-v1'
        self.message={'token':self.token,'pid':os.getpid(),'identity':'fixture'}
        self.raw=json.dumps(self.message,sort_keys=True,separators=(',',':')).encode()
        self.now=datetime(2026,11,1,tzinfo=timezone.utc)

    def channel(self):return ready.ReadyCopy(self.source,self.token,root=self.cache)
    def publish(self,channel):ready.publish(channel.contract(),self.raw,lambda:self.source.write_bytes(self.raw))
    def accepted(self):
        channel=self.channel();self.publish(channel);self.assertTrue(channel.ready())
        self.assertEqual(channel.read_ready(),self.raw);channel.accept(self.message,now=self.now)
        channel.finish(native_exit_proved=True,startup_completed=True,now=self.now+timedelta(seconds=1))
        return channel

    def test_native_read_handle_cannot_write(self):
        self.source.write_bytes(self.raw);native=ready.NativeFiles()
        try:
            handle=native.open_read(self.source);count=ctypes.c_ulong()
            self.assertFalse(native.api.WriteFile(handle,b'X',1,ctypes.byref(count),None))
            self.assertEqual(ctypes.get_last_error(),5);self.assertEqual(native.read(handle,4096),self.raw)
        finally:native.close_all()
        self.assertEqual(self.source.read_bytes(),self.raw)

    def test_direct_read_is_preferred_and_backup_matches(self):
        channel=self.channel()
        try:
            self.publish(channel);self.assertEqual(channel.read_ready(),self.raw)
            self.assertEqual(channel.observation['mode'],'DIRECT_READ_ONLY')
            self.assertEqual(channel.observation['copy_sha256'],ready.sha(self.raw))
            self.assertEqual(self.source.read_bytes(),self.raw)
        finally:channel.close()

    def test_real_source_sharing_denial_uses_parent_owned_copy(self):
        channel=self.channel();process=None
        script="""import importlib.util,json,sys
s=importlib.util.spec_from_file_location('ready_fixture',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
info=json.loads(sys.argv[2]);payload=sys.argv[3].encode();native=m.NativeFiles()
h=native.open(info['source'],0xC0000080,0,1)
try:
 m.publish(info,payload,lambda:native.write(h,payload,0))
 print('READY',flush=True);sys.stdin.readline()
finally:native.close_all()
"""
        try:
            process=subprocess.Popen([sys.executable,'-B','-c',script,str(MODULE),json.dumps(channel.contract()),self.raw.decode()],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(process.stdout.readline().strip(),'READY')
            self.assertEqual(channel.read_ready(),self.raw)
            self.assertEqual(channel.observation['mode'],'VERIFIED_PARENT_COPY')
            self.assertEqual(channel.observation['source_winerror'],32)
            output,error=process.communicate('\n',timeout=5);self.assertEqual(process.returncode,0,error)
        finally:
            if process is not None:
                if process.poll() is None:process.kill()
                process.communicate(timeout=5)
            channel.close()

    def test_uncommitted_copy_is_not_ready(self):
        channel=self.channel()
        try:self.assertFalse(channel.ready())
        finally:channel.close()

    def test_failed_original_publication_cannot_commit_copy(self):
        channel=self.channel()
        try:
            def denied():raise PermissionError('CONTROL_PUBLICATION_DENIED')
            with self.assertRaisesRegex(PermissionError,'CONTROL_PUBLICATION_DENIED'):ready.publish(channel.contract(),self.raw,denied)
            self.assertFalse(channel.ready())
        finally:channel.close()

    def test_changed_original_never_falls_back_to_good_copy(self):
        channel=self.channel()
        try:
            self.publish(channel);self.source.write_text('{"token":"forged"}')
            with self.assertRaises(ValueError):channel.read_ready()
        finally:channel.close()

    def test_duplicate_ready_json_is_rejected(self):
        channel=self.channel()
        try:
            raw=('{"token":"'+self.token+'","token":"'+self.token+'"}').encode()
            ready.publish(channel.contract(),raw,lambda:self.source.write_bytes(raw))
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):channel.read_ready()
        finally:channel.close()

    def test_corrupt_copy_hash_is_rejected(self):
        channel=self.channel()
        try:
            self.publish(channel)
            with channel.copy_path.open('r+b') as f:f.seek(-1,2);f.write(b'X')
            with self.assertRaisesRegex(ValueError,'HASH'):channel.read_ready()
        finally:channel.close()

    def test_wrong_token_is_rejected(self):
        channel=self.channel()
        try:
            raw=json.dumps({**self.message,'token':'b'*64}).encode()
            ready.publish(channel.contract(),raw,lambda:self.source.write_bytes(raw))
            with self.assertRaisesRegex(ValueError,'TOKEN'):channel.read_ready()
        finally:channel.close()

    def test_hardlinked_source_is_rejected_without_fallback(self):
        channel=self.channel()
        try:
            self.publish(channel);os.link(self.source,self.root/'alias')
            with self.assertRaisesRegex(ValueError,'FILE_TYPE'):channel.read_ready()
        finally:channel.close()

    def test_expiry_waits_three_days_after_both_read_and_exit(self):
        channel=self.accepted();ready.cleanup(self.cache,now=self.now+timedelta(days=3))
        self.assertTrue(channel.copy_path.exists())
        result=ready.cleanup(self.cache,now=self.now+timedelta(days=3,seconds=2))
        self.assertEqual(result['deleted'],[str(channel.copy_path)]);self.assertFalse(channel.copy_path.exists())
        self.assertEqual(self.source.read_bytes(),self.raw);self.assertTrue(channel.meta_path.exists())

    def test_failed_unaccepted_copy_never_age_deletes(self):
        channel=self.channel();channel.close();ready.cleanup(self.cache,now=self.now+timedelta(days=100))
        self.assertTrue(channel.copy_path.exists())

    def test_missing_native_exit_proof_prevents_expiry(self):
        channel=self.channel();self.publish(channel);channel.read_ready();channel.accept(self.message,now=self.now)
        channel.finish(native_exit_proved=False,startup_completed=True,now=self.now)
        ready.cleanup(self.cache,now=self.now+timedelta(days=100));self.assertTrue(channel.copy_path.exists())

    def test_hardlinked_managed_copy_is_never_deleted(self):
        channel=self.accepted();os.link(channel.copy_path,self.root/'copy-alias')
        result=ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertTrue(channel.copy_path.exists());self.assertTrue(result['errors'])

    def test_repeated_finish_does_not_reset_expiry(self):
        channel=self.accepted();first=json.loads(channel.meta_path.read_bytes())['expires_utc']
        channel.finish(native_exit_proved=True,startup_completed=True,now=self.now+timedelta(days=1))
        self.assertEqual(json.loads(channel.meta_path.read_bytes())['expires_utc'],first)

    def test_unmanaged_existing_directory_is_refused(self):
        self.cache.mkdir();(self.cache/'user-data').write_text('preserve')
        with self.assertRaisesRegex(ValueError,'UNMANAGED_ROOT'):self.channel()
        self.assertEqual((self.cache/'user-data').read_text(),'preserve')

    def test_deleted_receipt_backlog_cannot_starve_later_expired_copy(self):
        channel=self.accepted()
        for number in range(65):
            token=format(number,'064x')
            meta=dict(channel.meta,token=token,copy=ready._norm(self.cache/('ready-'+token+'.copy')),deleted=True)
            ready._save(self.cache/('ready-'+token+'.receipt.json'),meta)
        result=ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['deleted'],[str(channel.copy_path)])

    def test_cleanup_bound_survives_receipt_save_failure_after_delete(self):
        channels=[]
        for number in range(3):
            self.token=format(number+100,'064x')
            self.source=self.root/('owned-bootstrap-'+self.token+'.ready.json')
            self.message=dict(self.message,token=self.token)
            self.raw=json.dumps(self.message,sort_keys=True,separators=(',',':')).encode()
            channels.append(self.accepted())
        original=ready._save
        def failed(path,value):
            if value.get('deleted') is True:raise OSError('CONTROL_RECEIPT_SAVE_AFTER_DELETE')
            return original(path,value)
        with patch.object(ready,'_save',failed):
            result=ready.cleanup(self.cache,now=self.now+timedelta(days=10),maximum=1)
        self.assertEqual(sum(not item.copy_path.exists() for item in channels),1)
        self.assertEqual(len(result['deleted']),1);self.assertTrue(result['errors'])
        audits=list((self.cache/'.expiry-audit').glob('*.audit.json'))
        self.assertTrue(audits,'post-delete persistence failure needs durable diagnostics')
        records=[json.loads(path.read_bytes()) for path in audits]
        self.assertTrue(any(row.get('deleted')==result['deleted'] and 'CONTROL_RECEIPT_SAVE_AFTER_DELETE' in json.dumps(row) for row in records))

    def test_retained_tombstones_are_not_opened_by_cleanup(self):
        channel=self.accepted()
        for number in range(150):
            token=format(number,'064x')
            ready._save(self.cache/('ready-'+token+'.receipt.json'),dict(channel.meta,token=token,deleted=True))
        opened=[];original=ready._read_file
        def observed(path,*args,**kwargs):
            opened.append(Path(path));return original(path,*args,**kwargs)
        with patch.object(ready,'_read_file',observed):
            result=ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertEqual(result['deleted'],[str(channel.copy_path)])
        self.assertLess(len(opened),10,'permanent receipt archive must not be rescanned')

    def test_interrupted_queue_temps_cannot_starve_valid_due_copy(self):
        channel=self.accepted();day=self.cache/'.expiry-queue'/'2026-11-04'
        for number in range(150):(day/('000-stale.tmp-'+str(number))).write_bytes(b'incomplete metadata')
        for _ in range(3):ready.cleanup(self.cache,now=self.now+timedelta(days=10),budget_seconds=1)
        self.assertFalse(channel.copy_path.exists())
        self.assertEqual(self.source.read_bytes(),self.raw)

    def test_invalid_queue_days_cannot_starve_valid_due_copy(self):
        channel=self.accepted();queue=self.cache/'.expiry-queue'
        for number in range(150):(queue/('000-invalid-'+str(number))).mkdir()
        for _ in range(3):ready.cleanup(self.cache,now=self.now+timedelta(days=10),budget_seconds=1)
        self.assertFalse(channel.copy_path.exists())

    def test_expiry_refuses_another_live_reader_and_retains_diagnostic(self):
        channel=self.accepted();native=ready.NativeFiles()
        try:
            handle=native.open_read(channel.copy_path)
            result=ready.cleanup(self.cache,now=self.now+timedelta(days=10),budget_seconds=1)
            self.assertEqual(result['deleted'],[]);self.assertTrue(result['errors'])
            self.assertEqual(native.read(handle,ready.FRAME_LIMIT)[44:],self.raw)
        finally:native.close_all()
        self.assertTrue(channel.copy_path.exists())

    def test_queue_list_permission_error_is_not_silently_deferred(self):
        channel=self.accepted();day=self.cache/'.expiry-queue'/'2026-11-04';original=ready.os.scandir
        def denied(path):
            if Path(path)==day:raise ctypes.WinError(5)
            return original(path)
        with patch.object(ready.os,'scandir',denied):
            with self.assertRaises(OSError) as caught:ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertEqual(caught.exception.winerror,5);self.assertTrue(channel.copy_path.exists())

    def test_queue_empty_directory_permission_error_is_not_hidden(self):
        channel=self.accepted();day=self.cache/'.expiry-queue'/'2026-11-04';original=Path.rmdir
        def denied(path):
            if path==day:raise ctypes.WinError(5)
            return original(path)
        with patch.object(Path,'rmdir',denied):
            with self.assertRaises(OSError) as caught:ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertEqual(caught.exception.winerror,5)
        self.assertFalse(channel.copy_path.exists())
        self.assertTrue(list((self.cache/'.expiry-audit').glob('*.audit.json')))

    def test_replaced_copy_path_is_rejected_even_with_original_handle(self):
        channel=self.channel()
        try:
            self.publish(channel);channel.copy_path.rename(self.root/'moved-copy')
            channel.copy_path.write_bytes(b'other bytes')
            with self.assertRaisesRegex(ValueError,'COPY_PATH_CHANGED'):channel.read_ready()
        finally:channel.close()

    def test_metadata_cannot_redirect_expiry_to_original(self):
        channel=self.accepted();meta=dict(channel.meta,copy=str(self.source))
        ready._save(channel.meta_path,meta)
        result=ready.cleanup(self.cache,now=self.now+timedelta(days=10))
        self.assertTrue(result['errors']);self.assertTrue(channel.copy_path.exists())
        self.assertEqual(self.source.read_bytes(),self.raw)

    def test_incomplete_startup_never_becomes_expiry_eligible(self):
        channel=self.channel();self.publish(channel);channel.read_ready();channel.accept(self.message,now=self.now)
        channel.finish(native_exit_proved=True,startup_completed=False,now=self.now)
        ready.cleanup(self.cache,now=self.now+timedelta(days=100))
        self.assertTrue(channel.copy_path.exists())

    def test_nonfinite_json_is_rejected(self):
        channel=self.channel()
        try:
            raw=('{"token":"'+self.token+'","value":NaN}').encode()
            ready.publish(channel.contract(),raw,lambda:self.source.write_bytes(raw))
            with self.assertRaisesRegex(ValueError,'JSON_CONSTANT'):channel.read_ready()
        finally:channel.close()

    def test_source_close_debt_is_not_hidden_by_access_denied_fallback(self):
        channel=self.channel();debt=None
        try:
            self.publish(channel)
            original=ready.NativeFiles.close
            def failed(native,handle):
                if native is not channel.native:raise ctypes.WinError(5)
                return original(native,handle)
            with patch.object(ready.NativeFiles,'close',failed):
                with self.assertRaises(OSError) as caught:channel.read_ready()
                debt=getattr(caught.exception,'owned_ready_native',None)
                self.assertIsNotNone(debt);self.assertIsNone(channel.raw)
        finally:
            if debt is not None:debt.close_all()
            channel.close()

    def test_missing_source_is_not_an_access_denied_fallback(self):
        channel=self.channel()
        try:
            self.publish(channel)
            original=ready.NativeFiles.open_read
            def failed(native,path):
                if Path(path)==self.source:raise ctypes.WinError(2)
                return original(native,path)
            with patch.object(ready.NativeFiles,'open_read',failed):
                with self.assertRaises(OSError) as caught:channel.read_ready()
            self.assertEqual(caught.exception.winerror,2);self.assertIsNone(channel.raw)
        finally:channel.close()

    def test_known_folder_lookup_preserves_existing_com_apartment(self):
        ole=ctypes.WinDLL('ole32');ole.CoInitializeEx.argtypes=[ctypes.c_void_p,ctypes.c_ulong];ole.CoInitializeEx.restype=ctypes.c_long
        ole.CoUninitialize.argtypes=[];ole.CoUninitialize.restype=None
        initialized=ole.CoInitializeEx(None,0);self.assertIn(initialized,(0,1))
        probe=None
        try:
            self.assertEqual(ready.default_root().name,'ready-copies-v1')
            probe=ole.CoInitializeEx(None,2)
            self.assertEqual(probe,-2147417850,'lookup must not uninitialize an existing MTA')
        finally:
            if probe in (0,1):ole.CoUninitialize()
            ole.CoUninitialize()

    def test_actual_owned_worker_uses_copy_when_parent_original_open_is_denied(self):
        from knowledge_bridge.windows_owned_process import launch_current
        script=self.root/'worker.py';script.write_text('print("worker entered")\n',encoding='utf-8')
        original=ready.NativeFiles.open_read;owner=None
        def denied(native,path):
            if Path(path).name.endswith('.ready.json'):raise ctypes.WinError(5)
            return original(native,path)
        with (self.root/'stdout').open('wb') as output,(self.root/'stderr').open('wb') as errors:
            try:
                with patch.object(ready,'default_root',return_value=self.cache),patch.object(ready.NativeFiles,'open_read',denied):
                    owner=launch_current(subprocess.Popen,sys.executable,script,deadline=time.monotonic()+10,
                        stdin=subprocess.PIPE,stdout=output,stderr=errors,
                        env=dict(os.environ,PYTHONNOUSERSITE='1'),cwd=self.root)
                    owner.wait(time.monotonic()+5);owner.release()
                self.assertIn('ready_read',owner.proof['startup'],'actual owned startup must consume strict copy reader')
                proof=owner.proof['startup']['ready_read']
                self.assertEqual(proof['mode'],'VERIFIED_PARENT_COPY');self.assertEqual(proof['source_winerror'],5)
                self.assertTrue(owner.proof['termination']['native_exit_proved']);self.assertEqual(owner.process.returncode,0)
            finally:
                if owner is not None:
                    if not owner.proof['released']:owner.stop(time.monotonic()+5);owner.release()
                    if owner.process.stdin is not None:owner.process.stdin.close()
        self.assertIn('worker entered',(self.root/'stdout').read_text())


if __name__=='__main__':unittest.main()
