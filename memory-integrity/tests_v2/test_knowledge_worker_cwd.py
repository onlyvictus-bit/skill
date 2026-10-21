"""Real stdlib children reproduce relative writes; NOT numerical/runtime proof.

Removing either production Popen cwd must put the fixture cache in caller source
and fail the corresponding test. No Windows cache writer is simulated as proof.
The campaign's retained runner keeps every created fixture/cache/stream.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from knowledge_bridge import contracts as c
from knowledge_bridge import distributed_retrieval as shard
from knowledge_bridge.worker_client import _process
from knowledge_bridge import workflow

CACHE = Path('%SystemDrive%/ProgramData/Microsoft/Windows/Caches/authored-fixture.db')
SCRIPT = '''import json,os,sys
from pathlib import Path
cache=Path('%SystemDrive%/ProgramData/Microsoft/Windows/Caches/authored-fixture.db')
cache.parent.mkdir(parents=True,exist_ok=True)
cache.write_bytes(b'authored-relative-write-not-a-Windows-runtime-cache')
payload=json.load(sys.stdin)
print(json.dumps({'ok':True,'cwd':os.getcwd(),'payload':payload,'keys':sorted(os.environ),
                  'cache':cache.read_text(encoding='utf-8')}))
'''


class WorkerCwd(unittest.TestCase):
    def fixture(self, root):
        root.mkdir()
        (root/'keep-source.txt').write_bytes(b'unchanged caller source')
        script=root/'distributed_worker.py'
        script.write_text(SCRIPT,encoding='utf-8')
        return script, {p.name:p.read_bytes() for p in root.iterdir()}

    def check_child(self, result, caller):
        self.assertNotEqual(Path(result['cwd']).resolve(),caller.resolve(),
                            'relative child writes must not land in caller source')
        self.assertEqual(result['payload'],{'source':'explicit-source','number':7})
        self.assertEqual(result['cache'],'authored-relative-write-not-a-Windows-runtime-cache')
        keys={k.upper() for k in result['keys']}
        self.assertNotIn('TOKEN_FOR_CWD_TEST',keys)
        self.assertNotIn('SYSTEMDRIVE',keys)
        self.assertIn('HF_HUB_OFFLINE',keys)

    @patch.dict(os.environ,{'TOKEN_FOR_CWD_TEST':'test-only-do-not-forward','SystemDrive':'C:'})
    def test_single_relative_writes_are_isolated_per_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            caller=Path(temp)/'caller'
            script,before=self.fixture(caller)
            parent=Path.cwd()
            os.chdir(caller)
            try:
                digest=c.digest(Path(sys.executable).read_bytes())
                first=_process(sys.executable,script,{'source':'explicit-source','number':7},5,digest)
                self.check_child(first,caller)
                # Relative script selection retains caller-relative meaning even
                # though the child must execute in a different working directory.
                second=_process(sys.executable,Path('distributed_worker.py'),
                                {'source':'explicit-source','number':7},5,digest)
                self.check_child(second,caller)
                self.assertNotEqual(first['cwd'],second['cwd'])
                self.assertFalse((caller/CACHE).exists())
                self.assertEqual({p.name:p.read_bytes() for p in caller.iterdir()},before)
            finally:
                os.chdir(parent)

    @patch.dict(os.environ,{'TOKEN_FOR_CWD_TEST':'test-only-do-not-forward','SystemDrive':'C:'})
    def test_shards_relative_writes_are_isolated_in_each_owned_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            caller=Path(temp)/'caller'
            _,before=self.fixture(caller)
            parent=Path.cwd()
            os.chdir(caller)
            sessions=[]
            try:
                with patch.object(shard,'__file__',str(caller/'distributed_retrieval.py')):
                    for lane in (0,1):
                        session=shard._Session(sys.executable,lane,'test-only-no-native-lease',time.monotonic()+5)
                        sessions.append(session)
                        session.process.stdin.write(c.canonical({'source':'explicit-source','number':7}))
                        session.process.stdin.close()
                    results=[]
                    for session in sessions:
                        self.assertEqual(session.process.wait(timeout=5),0)
                        session.reader.seek(0)
                        result=json.loads(session.reader.read())
                        self.check_child(result,caller)
                        owned=Path(session.directory.name)
                        self.assertEqual(Path(result['cwd']).resolve(),owned.resolve())
                        self.assertEqual((owned/CACHE).read_text(encoding='utf-8'),result['cache'])
                        results.append(result)
                    self.assertNotEqual(results[0]['cwd'],results[1]['cwd'])
                    self.assertNotEqual(sessions[0].process.pid,sessions[1].process.pid)
                self.assertFalse((caller/CACHE).exists())
                self.assertEqual({p.name:p.read_bytes() for p in caller.iterdir()},before)
            finally:
                for session in sessions:
                    session.close()
                os.chdir(parent)

    def test_benchmark_dispatch_keeps_caller_relative_companion_and_report(self):
        """Real dispatch/companion handshake/child, authored argv echo, NO model."""
        with tempfile.TemporaryDirectory() as temp:
            caller=Path(temp)
            (caller/'manifest.json').write_text('{}',encoding='utf-8')
            script=caller/'model_benchmark.py'
            script.write_text('import json,sys,os\nfrom pathlib import Path\n'
                'def arg(k):return Path(sys.argv[sys.argv.index(k)+1])\n'
                'root=arg("--claude-mon-root");out=arg("--output")\n'
                'valid=root.is_absolute() and out.is_absolute() and (root/"scripts/claude_mon_v2.py").is_file()\n'
                'if valid:out.write_text("TEST_ONLY authored argv report",encoding="utf-8")\n'
                'print(json.dumps({"ok":True,"valid_paths":valid,"companion":str(root),'
                '"output":str(out),"cwd":os.getcwd()}))\n',encoding='utf-8')
            parser=argparse.ArgumentParser()
            workflow.register(parser.add_subparsers(dest='command',required=True))
            companion=ROOT.parent/'claude-mon'
            parent=Path.cwd()
            os.chdir(caller)
            try:
                args=parser.parse_args(['knowledge-model-benchmark',
                    '--claude-mon-root',os.path.relpath(companion,caller),
                    '--model-python',sys.executable,'--model-manifest','manifest.json',
                    '--worker-python',sys.executable,'--output','report.json'])
                with patch.object(workflow,'__file__',str(caller/'workflow.py')):
                    result=workflow.dispatch(args)
                self.assertTrue(result['valid_paths'],'cwd isolation must preserve caller-relative CLI paths')
                self.assertEqual(Path(result['companion']).resolve(),companion.resolve())
                self.assertEqual(Path(result['output']),caller/'report.json')
                self.assertNotEqual(Path(result['cwd']).resolve(),caller.resolve())
                self.assertEqual((caller/'report.json').read_text(encoding='utf-8'),
                                 'TEST_ONLY authored argv report')
            finally:
                os.chdir(parent)

    def cleanup_failure(self, script_text, timeout=5):
        """Only cleanup fails artificially; real owned child/streams still run."""
        from knowledge_bridge import worker_client as client
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            script=root/'echo.py'
            script.write_text(script_text,encoding='utf-8')
            directory=root/'owned-cwd'
            directory.mkdir()
            class FailedCleanup:
                name=str(directory)
                def __enter__(self): return self.name
                def __exit__(self,*unused): self.cleanup()
                def cleanup(self): raise OSError('TEST_ONLY_CWD_CLEANUP_FAILED')
            with patch.object(client.tempfile,'TemporaryDirectory',return_value=FailedCleanup()):
                try:
                    _process(sys.executable,script,{},timeout,c.digest(Path(sys.executable).read_bytes()))
                except Exception as error:
                    return error
            self.fail('cleanup failure was silently accepted')

    def test_successful_child_cwd_cleanup_failure_is_named_and_not_success(self):
        error=self.cleanup_failure('import json\nprint(json.dumps({"ok":True}))\n')
        self.assertIsInstance(error,ValueError)
        self.assertEqual(str(error),'E_WORKER_CWD_CLEANUP')
        self.assertIn('TEST_ONLY_CWD_CLEANUP_FAILED',repr(error.__cause__))

    def test_timeout_stays_primary_when_cwd_cleanup_also_fails(self):
        error=self.cleanup_failure('import time\ntime.sleep(20)\n',timeout=.01)
        self.assertIsInstance(error,ValueError)
        self.assertTrue(str(error).startswith('E_WORKER_TIMEOUT'),str(error))
        self.assertIn('E_WORKER_CWD_CLEANUP','\n'.join(getattr(error,'__notes__',[])))
        self.assertIn('TEST_ONLY_CWD_CLEANUP_FAILED','\n'.join(error.__notes__))

    def test_worker_refusal_stays_primary_when_cwd_cleanup_also_fails(self):
        error=self.cleanup_failure('import json\nprint(json.dumps({"ok":False,"error":"TEST_ONLY_REFUSAL"}))\n')
        self.assertIsInstance(error,ValueError)
        self.assertEqual(str(error),'E_WORKER_FAILED: TEST_ONLY_REFUSAL')
        self.assertIn('E_WORKER_CWD_CLEANUP','\n'.join(getattr(error,'__notes__',[])))


if __name__=='__main__':
    unittest.main()
