"""Explicit local worker executable, bounded JSON files, timeout, no retries."""
import os
import math
import signal
from pathlib import Path
import subprocess
import tempfile
import time
from . import BRIDGE_VERSION,SEMANTICA_VERSION,SEMANTICA_REVISION
from . import contracts as c

def _process(python, script, payload, timeout, executable_digest, arguments=()):
    if c.digest(Path(python).read_bytes()) != executable_digest:
        raise ValueError('E_WORKER_EXECUTABLE_DRIFT')
    raw = c.canonical(payload)
    if len(raw) > c.MAX_MESSAGE: raise ValueError('E_MESSAGE_LIMIT')
    env = {k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','LANG','LC_ALL'}}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    with tempfile.TemporaryFile() as inp, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        inp.write(raw); inp.seek(0)
        process = subprocess.Popen([str(python),'-B',str(script),*map(str,arguments)], stdin=inp, stdout=out, stderr=err, env=env,
                                   start_new_session=os.name=='posix')
        started = time.monotonic()
        try:
            while process.poll() is None:
                if time.monotonic()-started > timeout: raise ValueError('E_WORKER_TIMEOUT: no resend')
                if os.fstat(out.fileno()).st_size > c.MAX_MESSAGE or os.fstat(err.fileno()).st_size > 65536:
                    raise ValueError('E_WORKER_OUTPUT_LIMIT')
                time.sleep(.02)
            out.seek(0); response = out.read(c.MAX_MESSAGE+1)
            if len(response) > c.MAX_MESSAGE or os.fstat(err.fileno()).st_size > 65536:
                raise ValueError('E_WORKER_OUTPUT_LIMIT')
            result = c.loads(response)
        finally:
            if process.poll() is None:
                if os.name=='posix':
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                elif os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
                if process.poll() is None:process.kill()
            process.wait(timeout=5)
    if process.returncode != 0 or result.get('ok') is not True:
        raise ValueError('E_WORKER_FAILED: '+str(result.get('error','unknown')))
    return result


class ModelClient:
    """Explicit separate local learned-model executable and sealed file set."""
    def __init__(self, python, manifest, timeout=120):
        self.python = Path(python)
        if not self.python.is_absolute() or not self.python.is_file(): raise ValueError('E_MODEL_PATH')
        self.manifest = c.ordinary(manifest)
        if not self.manifest.is_file(): raise ValueError('E_MODEL_MANIFEST_PATH')
        self.manifest_digest = c.digest(self.manifest.read_bytes())
        self.executable_digest = c.digest(self.python.read_bytes())
        if type(timeout) not in (int,float) or not 0 < timeout <= 120: raise ValueError('E_WORKER_TIMEOUT_LIMIT')
        self.timeout = timeout

    def __call__(self, payload):
        if c.digest(self.manifest.read_bytes()) != self.manifest_digest: raise ValueError('E_MODEL_MANIFEST_DRIFT')
        if 'manifest' in payload: raise ValueError('E_MODEL_MANIFEST_SELECTION')
        result = _process(self.python, Path(__file__).with_name('model_runtime.py'),
                          dict(payload,manifest=str(self.manifest)), self.timeout, self.executable_digest)
        if not isinstance(result,dict) or not isinstance(result.get('model'),dict) or result['model'].get('manifest_digest') != self.manifest_digest:
            raise ValueError('E_MODEL_MANIFEST_BINDING')
        self._validate_input_binding(payload,result)
        return result

    @staticmethod
    def _validate_input_binding(payload,result):
        def tokens(ids,count,allow_empty=False):
            return (isinstance(ids,list) and (bool(ids) or allow_empty) and
                    all(type(n) is int and n>=0 for n in ids) and
                    type(count) is int and count==len(ids))
        def digest(text):return c.digest(text.encode('utf-8'))
        try:
            op=payload['op']
            if result.get('operation')!={'embed':'embedding','generate':'generation','rerank':'reranking'}.get(op):
                raise ValueError('operation')
            if op=='embed':
                texts=payload['texts'];vectors=result['vectors'];ids=result['input_token_ids'];counts=result['input_token_counts']
                if result['input_sha256']!=[digest(text) for text in texts] or not all(isinstance(rows,list) and len(rows)==len(texts) for rows in (vectors,ids,counts)):
                    raise ValueError('embedding inputs')
                if not vectors or not isinstance(vectors[0],list) or not vectors[0]:raise ValueError('vectors')
                size=len(vectors[0])
                for vector,unit_ids,count in zip(vectors,ids,counts):
                    if not tokens(unit_ids,count) or not isinstance(vector,list) or len(vector)!=size or not all(type(n) in (int,float) and math.isfinite(n) for n in vector):
                        raise ValueError('embedding token frame')
            elif op=='generate':
                if result['input_sha256']!=digest(payload['prompt']) or not tokens(result['input_token_ids'],result['input_token_count']) or not tokens(result['output_token_ids'],result['output_token_count'],True):
                    raise ValueError('generation token frame')
                if result['finish_reason'] not in ('eos','output_limit') or result['output_token_count']>payload['max_new_tokens'] or not isinstance(result['text'],str):raise ValueError('generation output')
            elif op=='rerank':
                expected={row['id']:digest(row['text']) for row in payload['candidates']};ranking=result['ranking']
                if result['query_sha256']!=digest(payload['query']) or not isinstance(ranking,list) or len(ranking)!=len(expected) or {row['id'] for row in ranking}!=set(expected):raise ValueError('ranking inputs')
                for row in ranking:
                    labels=row['label_token_ids']
                    if row['candidate_sha256']!=expected[row['id']] or not tokens(row['input_token_ids'],row['input_token_count']) or not isinstance(labels,dict) or set(labels)!={'Yes','No'}:raise ValueError('ranking token frame')
                    if not all(tokens(value,len(value)) for value in labels.values()):raise ValueError('ranking labels')
                    count=sum(len(value) for value in labels.values())
                    if type(row['label_token_count']) is not int or row['label_token_count']!=count or type(row['evaluated_token_count']) is not int or row['evaluated_token_count']!=2*row['input_token_count']+count or type(row['score']) not in (int,float) or not math.isfinite(row['score']) or not 0<=row['score']<=1:raise ValueError('ranking counts')
            else:raise ValueError('operation')
        except (KeyError,TypeError,AttributeError,ValueError) as exc:
            raise ValueError('E_MODEL_INPUT_BINDING') from exc

    def syntax(self,text,path):
        return _process(self.python,Path(__file__).with_name('language_extraction.py'),
                        {'text':text,'path':path},self.timeout,self.executable_digest)

class WorkerClient:
    def __init__(self,python,timeout=30,expected_revision=SEMANTICA_REVISION,model_client=None):
        self.python=Path(python)
        # venv launchers commonly are symlinks; resolving the launch path would
        # discard the venv selection. Only an explicitly selected executable
        # may use this exception; sources and generation files still forbid it.
        if not self.python.is_absolute() or not self.python.is_file(): raise ValueError('E_WORKER_PATH')
        self.executable_digest=c.digest(self.python.read_bytes())
        if type(timeout) not in (int,float) or not 0<timeout<=120: raise ValueError('E_WORKER_TIMEOUT_LIMIT')
        self.timeout=timeout;self.expected_revision=expected_revision;self.model_client=model_client
    def __call__(self,payload):
        if payload.get('op')=='retrieve_advanced':
            payload=dict(payload,worker_timeout=self.timeout)
        result=_process(self.python,Path(__file__).with_name('worker.py'),payload,self.timeout,self.executable_digest)
        if result.get('bridge_version')!=BRIDGE_VERSION or result.get('semantica_version')!=SEMANTICA_VERSION or result.get('revision')!=self.expected_revision: raise ValueError('E_WORKER_PIN')
        return result
