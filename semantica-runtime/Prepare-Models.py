"""Explicit public download of the exact pinned local model files; never install packages."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
from knowledge_bridge import contracts as c
from knowledge_bridge import model_runtime

def prepare(destination):
    destination=Path(destination).absolute()
    c.ordinary(destination,directory=True)
    destination.mkdir(parents=True,exist_ok=True)
    raw=(ROOT/'semantica-runtime/models-lock.json').read_bytes()
    lock=c.loads(raw)
    for role,model in lock['models'].items():
        directory=model_runtime._directory(destination,model['directory'])
        directory.mkdir(parents=True,exist_ok=True)
        expected={row['path'] for row in model['files']}
        for file in directory.rglob('*'):
            c.ordinary(file,directory=file.is_dir())
            if file.is_file() and file.relative_to(directory).as_posix() not in expected:
                raise ValueError('E_MODEL_FILE_SET: foreign or partial file')
        for row in model['files']:
            path=c.within(directory,row['path'])
            if path.exists():
                if model_runtime._file_hash(path)!=row['sha256']:raise ValueError('E_MODEL_FILE_DIGEST: '+row['path'])
                continue
            path.parent.mkdir(parents=True,exist_ok=True)
            partial=path.with_name(path.name+'.partial')
            url='https://huggingface.co/'+model['model_id']+'/resolve/'+model['revision']+'/'+urllib.parse.quote(row['path'],safe='/')
            size=0;digest=hashlib.sha256()
            with partial.open('xb') as output,urllib.request.urlopen(url,timeout=45) as response:
                while True:
                    block=response.read(1024*1024)
                    if not block:break
                    size+=len(block)
                    if size>1100000000:raise ValueError('E_MODEL_DOWNLOAD_LIMIT')
                    output.write(block);digest.update(block)
            if digest.hexdigest()!=row['sha256']:raise ValueError('E_MODEL_FILE_DIGEST: retained partial '+row['path'])
            partial.rename(path)
            print(json.dumps({'downloaded':row['path'],'bytes':size,'sha256':row['sha256']}),flush=True)
    manifest=destination/'models.json'
    if manifest.exists():
        c.ordinary(manifest)
        if manifest.read_bytes()!=raw:raise ValueError('E_MODEL_MANIFEST_DRIFT')
    else:
        with manifest.open('xb') as output:output.write(raw)
    bound=model_runtime.load_manifest(manifest)
    print(json.dumps({'ok':True,'manifest':str(manifest),'manifest_digest':bound['manifest_digest']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True);args=parser.parse_args()
    try:prepare(args.destination)
    except Exception as exc:
        print(json.dumps({'ok':False,'error':str(exc),'partial_files':'preserved; inspect before retry'}));sys.exit(2)
