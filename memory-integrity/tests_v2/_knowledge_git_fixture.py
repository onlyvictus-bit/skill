"""Owned sample Git-format data; no Git CLI write or checkout metadata needed."""
import hashlib
from pathlib import Path
import zlib


def create_git_fixture(parent):
    root = Path(parent) / 'git-repository'
    root.mkdir()  # Existing destinations are errors; never seed a real checkout.
    git = root / '.git'
    (git / 'objects').mkdir(parents=True)
    (git / 'refs/heads').mkdir(parents=True)

    def object_file(kind, payload):
        # Git's documented loose-object format: header + NUL + content, zlib.
        raw = kind.encode('ascii') + b' ' + str(len(payload)).encode('ascii') + b'\0' + payload
        ident = hashlib.sha1(raw).hexdigest()
        directory = git / 'objects' / ident[:2]
        directory.mkdir()
        with (directory / ident[2:]).open('xb') as stream:
            stream.write(zlib.compress(raw))
        return ident

    tree = object_file('tree', b'')
    head = object_file('commit', ('tree ' + tree + '\n'
        'author Fixture <fixture@example.invalid> 1 +0000\n'
        'committer Fixture <fixture@example.invalid> 1 +0000\n\n'
        'Read-only fixture\n').encode('ascii'))
    files = {'HEAD': 'ref: refs/heads/fixture\n', 'refs/heads/fixture': head + '\n',
        'config': '[core]\nrepositoryformatversion = 0\nbare = false\nfilemode = false\nlogallrefupdates = false\n'}
    for name, text in files.items():
        with (git / name).open('x', encoding='ascii', newline='\n') as stream:
            stream.write(text)
    return root, head


def fixture_snapshot(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(Path(root).rglob('*')) if path.is_file()}
