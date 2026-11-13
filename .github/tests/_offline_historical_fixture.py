"""Test-owned old checkouts; historical diagnostic pins remain unchanged."""
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile
import hashlib
import json
import shutil

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
