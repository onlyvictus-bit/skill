"""Build a new deterministic pair from exact Git package bytes; retain all history."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

PACKAGES = ('memory-integrity', 'claude-mon')
ACTIVE = 'tests_v2/OFFLINE1-CONTENT.json'
RELEASE = 'offline-first-v1'
ROOT = Path(__file__).resolve().parents[1]


def need(value, code):
    if not value:
        raise ValueError('E_OFFLINE_RELEASE_' + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def read(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'DUPLICATE_JSON')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: need(False, 'NONFINITE_JSON'))


def ordinary(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        need(not item.is_symlink(), 'REDIRECT:' + str(item))
        if item.exists():
            need(not getattr(item.stat(), 'st_file_attributes', 0) & 0x400,
                 'REDIRECT:' + str(item))
    return path


def safe_name(name):
    need(isinstance(name, str) and name and '\\' not in name and ':' not in name,
         'MEMBER_PATH')
    parts = name.split('/')
    need(not PurePosixPath(name).is_absolute() and
         all(p not in ('', '.', '..') and p.rstrip(' .') == p and
             not any(ord(c) < 32 for c in p) and
             not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',
                              p.split('.')[0], re.I) for p in parts), 'MEMBER_PATH:' + name)
    return name


def inventory(root):
    root = ordinary(root)
    need(root.is_dir(), 'SOURCE_DIRECTORY')
    result, seen = {}, set()
    def failed(error):
        raise error
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        for name in sorted(dirs + files):
            path = Path(parent) / name
            rel = safe_name(path.relative_to(root).as_posix())
            ordinary(path)
            key = rel.casefold()
            need(key not in seen, 'CASE_COLLISION:' + rel)
            seen.add(key)
            if name in dirs:
                continue
            if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo'):
                continue
            info = path.stat()
            need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'NONORDINARY_FILE:' + rel)
            result[rel] = sha(path.read_bytes())
    return result


def git_packages(repo, commit):
    need(re.fullmatch('[0-9a-f]{40}', commit), 'SOURCE_COMMIT')
    result = subprocess.run(['git', '-C', str(repo), 'ls-tree', '-rz', commit, '--', *PACKAGES],
                            capture_output=True, check=True)
    maps = {name: {} for name in PACKAGES}
    for row in result.stdout.split(b'\0'):
        if not row:
            continue
        meta, raw_name = row.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        name = raw_name.decode('utf-8')
        safe_name(name)
        need(mode == '100644' and kind == 'blob', 'GIT_MODE:' + name)
        package, rel = name.split('/', 1)
        maps[package][rel] = blob
    need(all(maps.values()), 'EMPTY_SOURCE')
    return maps


def source_check(source, commit, repo=ROOT):
    maps = git_packages(repo, commit)
    actual = {n: inventory(source/n) for n in PACKAGES}
    for package in PACKAGES:
        need(set(actual[package]) == set(maps[package]), 'SOURCE_MEMBERS:' + package)
        for rel, blob in maps[package].items():
            raw = (source/package/rel).read_bytes()
            got = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            need(got == blob, 'SOURCE_BYTES:' + package + '/' + rel)
    return actual


def consumer(package):
    owner = 'integrity_v2' if package.name == PACKAGES[0] else 'complete_read_v2'
    path = package/'scripts'/owner/'release_content.py'
    spec = importlib.util.spec_from_file_location('offline_content_' + owner, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def pair_contract(source):
    cm = source/'claude-mon'
    code = ('import sys;sys.path.insert(0,sys.argv[1]);'
            'from complete_read_v2.contracts import schema_digest;print(schema_digest())')
    proc = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(cm/'scripts')],
                          capture_output=True, check=True, timeout=30)
    digest = proc.stdout.decode().strip()
    need(re.fullmatch('[0-9a-f]{64}', digest), 'COMPANION_DIGEST')
    for name, constant in (('memory_integrity_v2.py', 'PINNED_ENGINE_DIGEST'),
                           ('memory_integrity_workflow.py', 'SCHEMA_DIGEST')):
        tree = ast.parse((source/'memory-integrity/scripts'/name).read_bytes())
        values = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == constant for t in node.targets)
                  and isinstance(node.value, ast.Constant)]
        need(values == [digest], 'COMPANION_PIN:' + name)
    caps = {n: read((source/n/'capabilities-v2.json').read_bytes()) for n in PACKAGES}
    need(len({c['engine_version'] for c in caps.values()}) == 1 and
         all(c['schema_version'] == 2 for c in caps.values()), 'PAIR_METADATA')
    for n in PACKAGES:
        need(caps[n]['engine'] == n and consumer(source/n).selected_name(source/n) == ACTIVE,
             'PAIR_PROFILE')
    return {'schema_digest': digest, 'engine_version': caps[PACKAGES[0]]['engine_version'],
            'schema_version': 2, 'active_profile': RELEASE}


def new_output(path, sources):
    path = ordinary(path)
    physical = path.parent.resolve(strict=True)/path.name
    need(not path.exists(), 'OUTPUT_EXISTS')
    need(all(not physical.is_relative_to(Path(s).resolve()) for s in sources), 'OUTPUT_IN_SOURCE')
    path.mkdir(exist_ok=False)
    return path


def build(source, commit, output, repo=ROOT):
    source = ordinary(source)
    maps = source_check(source, commit, repo)
    contract = pair_contract(source)
    documents = {n: consumer(source/n).content_document(source/n) for n in PACKAGES}
    output = new_output(output, [source])
    manifest = {'schema_version': 1, 'release': RELEASE, 'source_commit': commit,
                'source_packages': maps, 'pair_contract': contract, 'packages': {},
                'runtime_verified': False, 'installed': False, 'release_ready': False}
    for name in PACKAGES:
        need(ACTIVE not in maps[name], 'PREEXISTING_ACTIVE_MANIFEST')
        payload = {rel: (source/name/rel).read_bytes() for rel in maps[name]}
        payload[ACTIVE] = canonical(documents[name]) + b'\n'
        archive = output/(name + '-offline-v1.zip')
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for rel, raw in sorted(payload.items()):
                need(rel == ACTIVE or sha(raw) == maps[name][rel], 'SOURCE_CHANGED_DURING_BUILD')
                info = zipfile.ZipInfo(name + '/' + rel, (2026, 11, 13, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        raw = archive.read_bytes()
        manifest['packages'][name] = {'zip': archive.name, 'sha256': sha(raw), 'bytes': len(raw),
                                     'entries': len(payload), 'files': {k: sha(v) for k, v in payload.items()}}
    need(source_check(source, commit, repo) == maps, 'SOURCE_CHANGED_AFTER_BUILD')
    with (output/'Offline-First-Release-Manifest.json').open('xb') as stream:
        stream.write(canonical(manifest) + b'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--repository-root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source_root, args.source_commit, args.output_dir, args.repository_root)
    print(json.dumps({'status': 'PAIR_BUILT_NOT_RUNTIME_QUALIFIED', 'manifest': result}, indent=2))
