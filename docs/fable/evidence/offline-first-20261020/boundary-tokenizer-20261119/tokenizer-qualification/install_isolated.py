from pathlib import Path
import subprocess,json,os,time,sys,hashlib
ROOT=Path(__file__).resolve().parent
scratch=ROOT/'temp';scratch.mkdir();cache=ROOT/'pip-cache';cache.mkdir()
env={**os.environ,'TEMP':str(scratch),'TMP':str(scratch),'TMPDIR':str(scratch),'PIP_CONFIG_FILE':os.devnull,'PIP_DISABLE_PIP_VERSION_CHECK':'1','PYTHONDONTWRITEBYTECODE':'1'}
meta=json.loads((ROOT/'PyPI-tiktoken.json').read_bytes());version=meta['info']['version']
(ROOT/'Plan.md').write_bytes(('Approved isolated tokenizer qualification. Pin tiktoken=='+version+' from PyPI metadata; require Windows binary wheels, isolated venv and local pip/encoding caches. Test actual installed Claude-Mon modules, UTF-8/Unicode roundtrips, exact counts, unknown-model/encoding refusal, full-request reserves and oversize rejection. No installed-skill, source, global-runtime, service or Git changes.\n').encode())
rows=[]
def run(label,argv):
    print(label+': RUNNING',flush=True);t=time.monotonic();p=subprocess.run(argv,env=env,capture_output=True)
    (ROOT/(label+'.stdout.log')).write_bytes(p.stdout);(ROOT/(label+'.stderr.log')).write_bytes(p.stderr)
    row={'label':label,'argv':argv,'exit':p.returncode,'seconds':time.monotonic()-t};rows.append(row);(ROOT/(label+'.Command.json')).write_bytes((json.dumps(row,indent=2)+'\n').encode());print(label+f": {row['seconds']:.3f} seconds exit={p.returncode}",flush=True)
    if p.returncode:raise RuntimeError(label+': '+p.stderr.decode(errors='replace')[-3000:])
run('venv-create',[sys.executable,'-B','-m','venv',str(ROOT/'venv')])
python=str(ROOT/'venv/Scripts/python.exe')
run('install-pinned-tokenizer',[python,'-I','-B','-m','pip','--isolated','--disable-pip-version-check','install','--no-input','--require-virtualenv','--only-binary=:all:','--index-url','https://pypi.org/simple','--cache-dir',str(cache),'--report',str(ROOT/'Install-Report.json'),'tiktoken=='+version])
run('dependency-check',[python,'-I','-B','-m','pip','--isolated','check'])
run('freeze',[python,'-I','-B','-m','pip','--isolated','freeze','--all'])
(ROOT/'Install-Commands.json').write_bytes((json.dumps(rows,indent=2)+'\n').encode());print('ISOLATED_INSTALL_COMPLETE',flush=True)
