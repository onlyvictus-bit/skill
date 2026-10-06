"""Verify trusted R3 release ZIPs from any folder, using standard library only.

Executes packaged tests in temporary extraction. No installation, AI calls or
native Beads operations. Do not run this on untrusted replacement archives.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

PACKAGES = ("memory-integrity","claude-mon")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run_suite(root,suite):
    proc = subprocess.run([sys.executable,"-B","-m","unittest","discover","-s",suite,"-v"],cwd=root,
        capture_output=True,text=True,encoding="utf-8",timeout=300,
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8"))
    output = proc.stdout+proc.stderr
    count = re.search(r"Ran (\d+) tests?",output)
    if proc.returncode or count is None:
        print(output)
        raise AssertionError(root.name+"/"+suite+" failed")
    return {"package":root.name,"suite":suite,"tests":int(count.group(1)),"exit_code":0}


def verify(folder):
    release = json.loads((folder/"Memory-Integrity-R3-Release-Manifest.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="mi-r3-check-") as tmp:
        base = Path(tmp)
        for pkg in PACKAGES:
            archive = folder/(pkg+"-r3.zip")
            if sha(archive.read_bytes())!=release["packages"][pkg]["sha256"]:
                raise AssertionError("ZIP digest mismatch: "+pkg)
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                if len(names)!=len(set(names)) or sum(n.endswith("/SKILL.md") for n in names)!=1:
                    raise AssertionError("duplicate member or invalid SKILL count")
                if any(not n.startswith(pkg+"/") or ".." in Path(n).parts or "\\" in n
                       or "__pycache__" in n or n.endswith((".pyc",".pyo")) for n in names):
                    raise AssertionError("unsafe/cache member")
                z.extractall(base)
            root = base/pkg
            manifest = json.loads((root/"tests_v2/R3-CONTENT.json").read_text(encoding="utf-8"))
            actual = {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()
                      and p.relative_to(root).as_posix()!="tests_v2/R3-CONTENT.json"}
            if actual!=manifest["files"]:
                raise AssertionError("content differs from manifest")
            baseline = json.loads((root/"tests_v2/baseline-r2.json").read_text(encoding="utf-8"))
            sk = next(r for r in baseline["files"] if r["path"]=="SKILL.md")
            if sha((root/"SKILL.md").read_bytes()[:sk["bytes"]])!=sk["sha256"]:
                raise AssertionError("R2 instruction prefix changed")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda pair:run_suite(base/pair[0],pair[1]),
                         [(p,s) for p in PACKAGES for s in ("tests","tests_v2")]))
    out = {"ok":True,"tests":sum(r["tests"] for r in results),"suites":results,
           "evidence_class":"TEST_ONLY","native_beads_qualified":False,"installed_promoted":False}
    print(json.dumps(out,indent=2))
    print("R3_PORTABLE_VERIFIED")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip-dir",type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    verify(args.zip_dir.resolve())
