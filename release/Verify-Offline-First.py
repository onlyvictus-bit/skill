"""Verify exact source closure and fresh safe extraction; runtime remains separate."""
import argparse
import importlib.util
import json
from pathlib import Path
import stat
import sys
import zipfile

BUILD = Path(__file__).with_name('Build-Offline-First.py')
spec = importlib.util.spec_from_file_location('offline_release_build', BUILD)
b = importlib.util.module_from_spec(spec)
previous = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(b)
finally:
    sys.dont_write_bytecode = previous


def verify(folder, output, source, repo=b.ROOT):
    folder, source = b.ordinary(folder), b.ordinary(source)
    manifest = b.read((folder/'Offline-First-Release-Manifest.json').read_bytes())
    b.need(manifest['schema_version'] == 1 and manifest['release'] == b.RELEASE and
           set(manifest['packages']) == set(b.PACKAGES), 'MANIFEST_SCHEMA')
    maps = b.source_check(source, manifest['source_commit'], repo)
    b.need(maps == manifest['source_packages'], 'MANIFEST_SOURCE')
    contract = b.pair_contract(source)
    b.need(contract == manifest['pair_contract'], 'MANIFEST_PAIR')
    payloads = {}
    for name in b.PACKAGES:
        row = manifest['packages'][name]
        b.need(row['zip'] == name + '-offline-v1.zip', 'ARCHIVE_NAME')
        path = b.ordinary(folder/row['zip'])
        b.need(path.is_file() and path.stat().st_nlink == 1, 'ARCHIVE_TYPE')
        raw = path.read_bytes()
        b.need(len(raw) == row['bytes'] and b.sha(raw) == row['sha256'], 'ARCHIVE_HASH')
        payload, seen = {}, set()
        with zipfile.ZipFile(path) as z:
            b.need(len(z.infolist()) == row['entries'], 'ARCHIVE_COUNT')
            for item in z.infolist():
                rel = b.safe_name(item.filename)
                b.need(rel.startswith(name + '/') and rel.casefold() not in seen and
                       stat.S_IFMT(item.external_attr >> 16) == stat.S_IFREG and
                       not item.is_dir() and not item.flag_bits & 1, 'UNSAFE_MEMBER:' + rel)
                seen.add(rel.casefold())
                payload[rel[len(name)+1:]] = z.read(item)
        expected = dict(maps[name])
        expected[b.ACTIVE] = b.sha(b.canonical(b.consumer(source/name).content_document(source/name)) + b'\n')
        b.need({rel: b.sha(data) for rel, data in payload.items()} == expected == row['files'],
               'PACKAGE_SOURCE_CLOSURE:' + name)
        payloads[name] = payload
    output = b.new_output(output, [source, folder])
    extracted = output/'extracted'
    extracted.mkdir()
    for name, payload in payloads.items():
        root = extracted/name
        root.mkdir()
        for rel, data in payload.items():
            target = root.joinpath(*rel.split('/'))
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
        b.consumer(root).verify_content(root)
        b.need(b.inventory(root) == manifest['packages'][name]['files'], 'EXTRACTED_CONTENT')
    b.need(b.pair_contract(extracted) == contract, 'EXTRACTED_PAIR')
    report = {'status': 'PAIR_ARCHIVE_AND_EXTRACTION_VERIFIED',
              'source_commit': manifest['source_commit'], 'pair_contract': contract,
              'packages': manifest['packages'], 'extracted_root': str(extracted),
              'source_unchanged': b.source_check(source, manifest['source_commit'], repo) == maps,
              'runtime_verified': False, 'installed': False, 'release_ready': False}
    with (output/'Verification.json').open('xb') as stream:
        stream.write(b.canonical(report) + b'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-dir', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--repository-root', type=Path, default=b.ROOT)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.release_dir, args.output_dir, args.source_root, args.repository_root)
    print(json.dumps({k: v for k, v in report.items() if k != 'packages'}, indent=2))
