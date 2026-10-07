"""Build deterministic paired bridge archives; preserve all historic releases."""
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(raw): return hashlib.sha256(raw).hexdigest()
def content(root):
    return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo') and p.relative_to(root).as_posix()!='tests_v2/R4-CONTENT.json'}
def build():
    package=ROOT/'memory-integrity';path=package/'tests_v2/R4-CONTENT.json';doc=json.loads(path.read_text(encoding='utf-8'));actual=content(package)
    doc['files']=actual;doc['extension_release']='knowledge-bridge-v1'
    for baseline,suffix in [('baseline-r1.json','r1'),('baseline-r2.json','r2')]:
        original={r['path']:r['sha256'] for r in json.loads((package/'tests_v2'/baseline).read_text(encoding='utf-8'))['files']}
        if set(original)-set(actual): raise ValueError('original file removed')
        doc['changed_'+suffix+'_files']=sorted(p for p in original if original[p]!=actual[p])
        doc['added_files' if suffix=='r1' else 'added_r2_files']=sorted(set(actual)-set(original))
    path.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    manifest={'schema_version':1,'release':'knowledge-bridge-v1','bridge_version':'1.0.0','base_release':'2.0.0-m12-r4','semantica_version':'0.7.0','semantica_revision':'320761de5d040a54a3220acc563223b4a7ffdc51','default_graph':False,'evidence_class':'TEST_ONLY','installed_promoted':False,'packages':{}}
    for name in ('memory-integrity','claude-mon'):
        archive=ROOT/'release'/(name+'-knowledge-v1.zip');entries=[]
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted((ROOT/name).rglob('*')):
                if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.pyo'): continue
                if p.is_symlink(): raise ValueError('symlink not allowed')
                rel=p.relative_to(ROOT).as_posix();info=zipfile.ZipInfo(rel,date_time=(2026,10,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9);entries.append(rel)
        raw=archive.read_bytes();manifest['packages'][name]={'zip':archive.name,'sha256':sha(raw),'bytes':len(raw),'entries':len(entries)}
    (ROOT/'release/Knowledge-Bridge-Manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__': build()
