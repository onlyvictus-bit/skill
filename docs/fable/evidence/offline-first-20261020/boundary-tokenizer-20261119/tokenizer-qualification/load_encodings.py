from pathlib import Path
import os,json,time,hashlib,importlib.metadata
ROOT=Path(__file__).resolve().parent;cache=ROOT/'encodings';cache.mkdir();os.environ['TIKTOKEN_CACHE_DIR']=str(cache)
import tiktoken
rows=[]
for name in ('cl100k_base','o200k_base'):
    t=time.monotonic();enc=tiktoken.get_encoding(name);rows.append({'encoding':name,'vocabulary_size':enc.n_vocab,'seconds':time.monotonic()-t});print(name+': loaded',flush=True)
report={'tiktoken_version':importlib.metadata.version('tiktoken'),'encodings':rows,'cache_files':[{'path':p.name,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in cache.iterdir() if p.is_file()]};(ROOT/'Encoding-Assets.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
