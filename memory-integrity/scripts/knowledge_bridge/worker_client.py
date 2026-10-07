"""Explicit local worker executable, bounded JSON files, timeout, no retries."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
from . import BRIDGE_VERSION,SEMANTICA_VERSION,SEMANTICA_REVISION
from . import contracts as c

class WorkerClient:
    def __init__(self,python,timeout=30,expected_revision=SEMANTICA_REVISION):
        self.python=Path(python)
        # venv launchers commonly are symlinks; resolving the launch path would
        # discard the venv selection. Only an explicitly selected executable
        # may use this exception; sources and generation files still forbid it.
        if not self.python.is_absolute() or not self.python.is_file(): raise ValueError('E_WORKER_PATH')
        self.executable_digest=c.digest(self.python.read_bytes())
        if type(timeout) not in (int,float) or not 0<timeout<=120: raise ValueError('E_WORKER_TIMEOUT_LIMIT')
        self.timeout=timeout;self.expected_revision=expected_revision
    def __call__(self,payload):
        if c.digest(self.python.read_bytes())!=self.executable_digest: raise ValueError('E_WORKER_EXECUTABLE_DRIFT')
        raw=c.canonical(payload)
        if len(raw)>c.MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
        env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','LANG','LC_ALL'}}
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        script=Path(__file__).with_name('worker.py')
        with tempfile.TemporaryFile() as inp,tempfile.TemporaryFile() as out,tempfile.TemporaryFile() as err:
            inp.write(raw);inp.seek(0)
            process=subprocess.Popen([str(self.python),'-B',str(script)],stdin=inp,stdout=out,stderr=err,env=env)
            started=time.monotonic()
            try:
                while process.poll() is None:
                    if time.monotonic()-started>self.timeout: raise ValueError('E_WORKER_TIMEOUT: no resend')
                    if os.fstat(out.fileno()).st_size>c.MAX_MESSAGE or os.fstat(err.fileno()).st_size>65536: raise ValueError('E_WORKER_OUTPUT_LIMIT')
                    time.sleep(.02)
                out.seek(0);response=out.read(c.MAX_MESSAGE+1)
                if len(response)>c.MAX_MESSAGE or os.fstat(err.fileno()).st_size>65536: raise ValueError('E_WORKER_OUTPUT_LIMIT')
                result=c.loads(response)
            finally:
                if process.poll() is None: process.kill()
                process.wait(timeout=5)
        if process.returncode!=0 or result.get('ok') is not True: raise ValueError('E_WORKER_FAILED: '+str(result.get('error','unknown')))
        if result.get('bridge_version')!=BRIDGE_VERSION or result.get('semantica_version')!=SEMANTICA_VERSION or result.get('revision')!=self.expected_revision: raise ValueError('E_WORKER_PIN')
        return result
