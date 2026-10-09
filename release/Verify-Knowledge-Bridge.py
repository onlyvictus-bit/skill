"""Verify the new portable pair, current tree, immutable histories and all suites."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
PACKAGES=('memory-integrity','claude-mon')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def suite(root,name):
    # The full extracted v2 suite adds host/history checks to the real worker
    # suite (observed 286s alone on Windows); retain a bounded ten-minute budget.
    p=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',name],cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=600,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'))
    output=p.stdout+p.stderr;count=re.search(r'Ran (\d+) tests?',output);skipped=re.search(r'skipped=(\d+)',output)
    if p.returncode or count is None: raise AssertionError(str(root)+'/'+name+' failed\n'+output)
    return {'package':root.name,'suite':name,'tests':int(count.group(1)),'skipped':int(skipped.group(1)) if skipped else 0}
def verify(folder):
    manifest=json.loads((folder/'Knowledge-Bridge-Manifest.json').read_text(encoding='utf-8'))
    assert manifest['release'] in {'knowledge-bridge-v1','knowledge-bridge-v2'} and manifest['default_graph'] is False and manifest['installed_promoted'] is False
    assert set(manifest['packages'])==set(PACKAGES)
    spec=importlib.util.spec_from_file_location('historical_release_verifier',ROOT/'release/Verify-Memory-Integrity-R4.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    # Historical package digests must still match their original manifests.
    for release in ('R3','R4'):
        previous=json.loads((ROOT/'release'/('Memory-Integrity-'+release+'-Release-Manifest.json')).read_text(encoding='utf-8'))
        for row in previous['packages'].values(): assert sha((ROOT/'release'/row['zip']).read_bytes())==row['sha256']
    with tempfile.TemporaryDirectory(prefix='knowledge-portable-') as temp:
        base=Path(temp)
        for name in PACKAGES:
            row=manifest['packages'][name];archive=folder/row['zip'];raw=archive.read_bytes()
            assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
            names=old.safe_members(archive,name);assert len(names)==row['entries']
            with zipfile.ZipFile(archive) as z:
                assert not any((i.external_attr>>16)&0o170000==0o120000 for i in z.infolist())
                z.extractall(base)
            root=base/name;content_path=root/'tests_v2/R4-CONTENT.json';content=json.loads(content_path.read_text(encoding='utf-8'))
            actual={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file() and p!=content_path}
            assert actual==content['files'],name+' content digest mismatch'
            current={p.relative_to(ROOT/name).as_posix():sha(p.read_bytes()) for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
            packaged={p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
            assert current==packaged,name+' current tree differs from release'
        mi=json.loads((base/'memory-integrity/knowledge-capabilities-v1.json').read_text(encoding='utf-8'))
        assert mi['semantica_revision']==manifest['semantica_revision'] and mi['default_graph'] is False
        for name in PACKAGES:
            caps=json.loads((base/name/'capabilities-v2.json').read_text(encoding='utf-8'))
            assert caps['engine_version']=='2.0.0-m12' and caps['native_beads_qualified'] is False
            if name=='memory-integrity': assert caps['native_merge_qualified'] is False and caps['generic_native_write_qualified'] is False
            else: assert caps['native_shared_claim_guard_support'] is True
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda pair:suite(base/pair[0],pair[1]),[(p,s) for p in PACKAGES for s in ('tests','tests_v2')]))
        results.extend([suite(ROOT,'.github/tests'),suite(ROOT/'evals','.')])
        front=subprocess.run([sys.executable,'-B',str(ROOT/'.github/scripts/validate-frontmatter.py')],cwd=ROOT,capture_output=True,text=True,timeout=30)
        assert front.returncode==0,front.stdout+front.stderr
    out={'ok':True,'release':manifest['release'],'tests':sum(r['tests'] for r in results),'skipped':sum(r['skipped'] for r in results),'suites':results,'real_runtime_selected':bool(os.environ.get('KNOWLEDGE_WORKER_PYTHON')),'evidence_class':'TEST_ONLY','default_graph':False,'coding_benefit':'UNVERIFIED','installed_promoted':False}
    print(json.dumps(out,indent=2));print('KNOWLEDGE_BRIDGE_PORTABLE_VERIFIED');return out
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zip-dir',type=Path,default=ROOT/'release');args=parser.parse_args();verify(args.zip_dir.resolve())
