"""Bind delivery CI to the qualified base, exact pair, and immutable old releases."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

spec = importlib.util.spec_from_file_location('offline_ci_verify', Path(__file__).with_name('Verify-Offline-First.py'))
v = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(v)
b = v.b
ACCEPTED = 'a2a28bf547a9c3e187c89eb6aee9f0b6bd822956'
QUALIFIED = {
    'memory-integrity-offline-v1.zip': 'c3869791951e4fef87256b96ba1944834e1b8cf9144e21a211a904751359e526',
    'claude-mon-offline-v1.zip': '1de54793ae104f24a50f84401733d16d714744ea68dd4cc89e628339fb26a6f0',
    'Offline-First-Release-Manifest.json': '0fa71257764e4a6089f4d4d635d8309190ab09d81078e6d7395c4b0a32cc5cb2',
}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def historical(source, repo):
    authority = b.read((source/'release/Offline-First-Historical-Hashes.json').read_bytes())
    b.need(set(authority) == {'schema_version', 'source_commit', 'files'} and
           type(authority['schema_version']) is int and authority['schema_version'] == 1 and
           authority['source_commit'] == ACCEPTED, 'HISTORICAL_AUTHORITY')
    expected = {}
    for row in git(repo, 'ls-tree', '-rz', ACCEPTED, '--', 'release').split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, blob = meta.decode().split()
        name = name.decode('utf-8');b.safe_name(name)
        b.need(mode == '100644' and kind == 'blob', 'HISTORICAL_GIT_MODE')
        raw = git(repo, 'cat-file', 'blob', blob)
        expected[name] = {'bytes': len(raw), 'sha256': b.sha(raw)}
        path = b.ordinary(source/name)
        b.need(path.is_file() and path.stat().st_nlink == 1 and path.read_bytes() == raw,
               'HISTORICAL_DRIFT:' + name)
    b.need(len(expected) == 15 and authority['files'] == expected, 'HISTORICAL_SET')
    return expected


def check(source, output, repo):
    source, repo = b.ordinary(source), b.ordinary(repo)
    output = b.new_output(output, [source])
    started = time.monotonic()
    report = {'status': 'FAILED', 'base_source_commit': ACCEPTED,
              'delivery_commit': git(repo, 'rev-parse', 'HEAD').decode().strip(),
              'runtime_verified': False, 'release_ready': False, 'installed': False}
    try:
        subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', ACCEPTED, 'HEAD'], check=True)
        report['historical'] = historical(source, repo)
        b.need(all((source/n/b.ACTIVE).is_file() for n in b.PACKAGES), 'ACTIVE_DELIVERY_REQUIRED')
        maps = b.source_check(source, ACCEPTED, repo)
        for name, expected in QUALIFIED.items():
            path = b.ordinary(source/'release'/name)
            b.need(path.is_file() and path.stat().st_nlink == 1 and b.sha(path.read_bytes()) == expected,
                   'QUALIFIED_DELIVERY_HASH:' + name)
        manifest = b.read((source/'release/Offline-First-Release-Manifest.json').read_bytes())
        b.need(manifest['source_commit'] == ACCEPTED, 'QUALIFIED_BASE_COMMIT')
        b.build(source, ACCEPTED, output/'rebuilt', repo)
        for name, expected in QUALIFIED.items():
            b.need(b.sha((output/'rebuilt'/name).read_bytes()) == expected,
                   'REPRODUCIBLE_HASH:' + name)
        verified = v.verify(source/'release', output/'verified', source, repo)
        report['extracted_root'] = verified['extracted_root']
        report['qualified_hashes'] = QUALIFIED
        b.need(b.source_check(source, ACCEPTED, repo) == maps, 'SOURCE_CHANGED_DURING_CI')
        historical(source, repo)
        report['status'] = 'SOURCE_HISTORY_AND_EXACT_PAIR_VERIFIED_RUNTIME_SEPARATE'
    except BaseException:
        report['failure'] = traceback.format_exc()
        raise
    finally:
        report['seconds'] = time.monotonic() - started
        (output/'Receipt.json').write_bytes(b.canonical(report) + b'\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', type=Path, default=b.ROOT)
    p.add_argument('--repository-root', type=Path, default=b.ROOT)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    check(a.source_root.absolute(), a.output_dir.absolute(), a.repository_root.absolute())
