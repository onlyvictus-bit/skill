"""Test-owned old checkouts; historical diagnostic pins remain unchanged."""
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile
import hashlib
import json
import shutil
import base64
import io
import zipfile
import zlib
from pathlib import PureWindowsPath

REPOSITORY = Path(__file__).resolve().parents[2]
ACCEPTED_OLD = 'a38297dd797eeecd25e41ab0af1df4e3db8fa984'


def git_at(repo, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.autocrlf=false',
                                    '-c', 'core.longpaths=true', '-C', str(repo), *args],
                                   stderr=subprocess.PIPE, timeout=60)


@lru_cache(maxsize=None)
def checkout(commit=ACCEPTED_OLD):
    # No checkout/index in the user's repository is modified. The object store
    # is read through alternates; every checked-out file belongs to this test.
    git_at(REPOSITORY, 'cat-file', '-e', commit + '^{commit}')
    parent = Path(tempfile.mkdtemp(prefix='offline-old-checkout-'))
    root = parent/'repo'
    subprocess.run(['git', '-c', 'core.longpaths=true', 'clone', '--shared', '--no-checkout',
                    str(REPOSITORY), str(root)], capture_output=True, check=True, timeout=60)
    git_at(root, 'checkout', '--detach', commit)
    if git_at(root, 'rev-parse', 'HEAD').decode().strip() != commit:
        raise AssertionError('Historical fixture checkout differs from its exact commit')
    return root


def timing_source(destination):
    old = checkout()
    destination.mkdir()
    for raw in git_at(old, 'ls-files', '-z').split(b'\0'):
        if raw:
            name = raw.decode('utf-8'); target = destination/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(old/name, target)
    fixtures = Path(__file__).parent/'fixtures/timing-source-20261024'
    raw = (fixtures/'Fixture-Manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != '615c99e09827c9e28bc12b56ceded556e354c3d869222bdc4f1a2a7b04fa7ee8':
        raise AssertionError('Frozen timing source authority changed')
    for name, row in json.loads(raw).items():
        data = (fixtures/row['fixture']).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise AssertionError('Frozen timing source changed: ' + name)
        target = destination/name;target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for name in ('extended_timing_log.py', 'worker_diagnostic_events.py'):
        shutil.copyfile(REPOSITORY/'.github/scripts'/name, destination/'.github/scripts'/name)
    return destination


def consumed_startup_history(test, module):
    """Rehydrate exact old inputs; relocate paths only at the test I/O seam."""
    fixtures=Path(__file__).parent/'fixtures/sr3-consumed-history-git-20261027'
    raw=(fixtures/'Fixture-Manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != 'd24f155e937fe5999e992440cf890976abf158acabaca89d532b34a8cd7691af':
        raise AssertionError('Consumed history fixture authority changed')
    manifest=json.loads(raw);parts=[]
    for row in manifest['parts']:
        data=(fixtures/row['name']).read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise AssertionError('Consumed history fixture part changed')
        parts.append(data)
    encoded=b''.join(parts)
    if hashlib.sha256(encoded).hexdigest()!=manifest['encoded_sha256']:
        raise AssertionError('Consumed history fixture payload changed')
    decoder=zlib.decompressobj();raw=decoder.decompress(base64.b64decode(encoded,validate=True),32*1024*1024)
    if len(raw)!=manifest['expanded_json_bytes'] or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
        raise AssertionError('Consumed history fixture expansion changed')
    rows=json.loads(raw)
    if len(rows)!=manifest['files'] or manifest['source_commit']!=ACCEPTED_OLD:
        raise AssertionError('Consumed history fixture membership changed')
    root=Path(tempfile.mkdtemp(prefix='sr3-consumed-history-'))
    with zipfile.ZipFile(io.BytesIO(git_at(REPOSITORY,'archive','--format=zip',ACCEPTED_OLD))) as archive:
        for name,row in rows.items():
            if name.startswith('/') or '\\' in name or '..' in name.split('/'):
                raise AssertionError('Unsafe consumed history fixture path')
            if 'git_path' in row:
                if name!='run/source/'+row['git_path']:
                    raise AssertionError('Consumed history Git role changed')
                data=archive.read(row['git_path'])
            else:
                data=base64.b64decode(row['content'],validate=True)
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
                raise AssertionError('Consumed history input changed: '+name)
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    original=PureWindowsPath(manifest['original_root'])
    native_path=Path
    def relocated(value):
        try: rel=PureWindowsPath(str(value)).relative_to(original)
        except ValueError: return native_path(value)
        return root.joinpath(*rel.parts)
    record=module.record
    def logical_record(path):
        result=record(path)
        try: rel=native_path(path).relative_to(root)
        except ValueError: return result
        return {**result,'path':str(original.joinpath(*rel.parts))}
    from unittest.mock import patch
    test.enterContext(patch.object(module,'OLD_ROOT',root))
    test.enterContext(patch.object(module,'Path',relocated))
    test.enterContext(patch.object(module,'record',logical_record))
    return root
