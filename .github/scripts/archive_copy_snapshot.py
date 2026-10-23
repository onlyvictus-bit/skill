"""Fresh cooperating-account archive snapshots, not authenticated provenance.

No ACL operations, deletion, execution of copied files, or access-denial bypass.
Only a reader that can open an original can copy it. Reports are sampled content.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import uuid
from datetime import datetime, timezone

from gate1_validation import ordinary, require

SCOPE = 'W_COPY_SUPPLEMENTARY_ARCHIVE_CONTENT_V1'


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True)+'\n').encode('utf-8')


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def hexdigest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def relative(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name and
            '\0' not in name and not name.startswith('/'), 'E_COPY_PATH')
    require(name == '.' or all(p not in ('', '.', '..') and p.rstrip(' .') == p
                              for p in name.split('/')), 'E_COPY_PATH')
    require(str(PurePosixPath(name)) == name, 'E_COPY_PATH')
    return name


def within(name, parent):
    return parent == '.' or name == parent or name.startswith(parent+'/')


def identity(info):
    return [info.st_dev, info.st_ino, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns]


def read_file(path, destination=None):
    path = ordinary(Path(path))
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'E_COPY_FILE_LINK')
    hashed, size = hashlib.sha256(), 0
    with path.open('rb') as source:
        opened = os.fstat(source.fileno())
        # Windows path stat may expose creation time as ctime while handle
        # fstat exposes change time. Compare common identity across APIs;
        # require each API's full identity (including ctime) stable separately.
        require(identity(opened)[:5] == identity(before)[:5], 'E_COPY_READ_CHANGED')
        if destination is not None:
            destination = Path(destination)
            ordinary(destination.parent)
            target = destination.open('xb')
        else:
            target = None
        try:
            while block := source.read(1024*1024):
                hashed.update(block); size += len(block)
                if target is not None: target.write(block)
        finally:
            if target is not None: target.close()
        require(identity(os.fstat(source.fileno())) == identity(opened), 'E_COPY_READ_CHANGED')
    require(identity(ordinary(path).stat()) == identity(before) and size == before.st_size,
            'E_COPY_READ_CHANGED')
    return {'kind': 'file', 'size': size, 'sha256': hashed.hexdigest(), 'identity': identity(before)}


def collect(root, allow_denied=False):
    """Unreadable subtrees are unresolved obligations, never empty success."""
    root = ordinary(Path(root))
    objects, unresolved = {}, {}
    def visit(path, name):
        kind = 'unknown'
        try:
            path = ordinary(path)
            info = path.stat()
            if stat.S_ISDIR(info.st_mode):
                kind = 'directory'
                with os.scandir(path) as listing:
                    names = sorted(entry.name for entry in listing)
                require(len({n.casefold() for n in names}) == len(names), 'E_COPY_COVERAGE_ALIAS')
                objects[name] = {'kind': 'directory'}
                for child in names:
                    visit(path/child, relative(child if name == '.' else name+'/'+child))
                with os.scandir(path) as listing:
                    after = sorted(entry.name for entry in listing)
                require(after == names and (info.st_dev, info.st_ino) ==
                        (ordinary(path).stat().st_dev, path.stat().st_ino), 'E_COPY_DIRECTORY_CHANGED')
            elif stat.S_ISREG(info.st_mode):
                kind = 'file'
                objects[name] = read_file(path)
            else:
                raise ValueError('E_COPY_FILE_TYPE')
        except PermissionError:
            # If some descendants were already read, a later denial cannot
            # shrink that observed subtree into a new unresolved obligation.
            if not allow_denied or name in objects:
                raise
            unresolved[name] = kind
    visit(root, '.')
    return dict(sorted(objects.items())), dict(sorted(unresolved.items()))


def validate_objects(objects):
    require(isinstance(objects, dict), 'E_COPY_OBJECTS')
    require(len({relative(k).casefold() for k in objects}) == len(objects), 'E_COPY_COVERAGE_ALIAS')
    for name, row in objects.items():
        require(isinstance(row, dict), 'E_COPY_OBJECT')
        if row.get('kind') == 'directory':
            require(set(row) == {'kind'}, 'E_COPY_OBJECT')
        else:
            require(set(row) == {'kind', 'size', 'sha256', 'identity'} and row['kind'] == 'file' and
                    type(row['size']) is int and row['size'] >= 0 and hexdigest(row['sha256']) and
                    isinstance(row['identity'], list) and len(row['identity']) == 6 and
                    all(type(x) is int for x in row['identity']) and row['identity'][2] == 1,
                    'E_COPY_OBJECT')


def validate_context(value):
    require(value.get('scope') == SCOPE and value.get('producer_authentication') is False and
            isinstance(value.get('root'), str) and Path(value['root']).is_absolute() and
            isinstance(value.get('session'), str) and len(value['session']) == 32 and
            all(c in '0123456789abcdef' for c in value['session']) and
            value.get('phase') in ('BEFORE', 'AFTER') and
            isinstance(value.get('nonce'), str) and len(value['nonce']) == 32 and
            all(c in '0123456789abcdef' for c in value['nonce']), 'E_COPY_CONTEXT')
    binding = value.get('binding')
    require((value['phase'] == 'BEFORE' and binding is None) or
            (value['phase'] == 'AFTER' and isinstance(binding, dict) and
             set(binding) == {'before_sha256', 'workload_sha256'} and
             all(hexdigest(x) for x in binding.values())), 'E_COPY_BINDING')


def validate_request(request):
    require(isinstance(request, dict) and set(request) == {'scope','root','session','phase','nonce',
            'binding','observed_utc','objects','unresolved','producer_authentication'}, 'E_COPY_REQUEST')
    validate_context(request); validate_objects(request['objects'])
    unresolved = request['unresolved']
    require(isinstance(unresolved, dict), 'E_COPY_COVERAGE')
    targets = sorted(unresolved)
    require(len({relative(k).casefold() for k in targets}) == len(targets), 'E_COPY_COVERAGE_ALIAS')
    for number, name in enumerate(targets):
        require(unresolved[name] in ('directory', 'file', 'unknown'), 'E_COPY_COVERAGE')
        require(not any(within(other.casefold(), name.casefold()) or within(name.casefold(), other.casefold())
                        for other in targets[:number]), 'E_COPY_COVERAGE_OVERLAP')
        require(not any(within(k.casefold(), name.casefold()) for k in request['objects']), 'E_COPY_COVERAGE')
    require('.' in request['objects'] or '.' in unresolved, 'E_COPY_COVERAGE_ROOT')
    for name in [*request['objects'], *targets]:
        if name != '.':
            parent = str(PurePosixPath(name).parent)
            require(request['objects'].get(parent) == {'kind': 'directory'}, 'E_COPY_COVERAGE_PARENT')


def scan(root, session, phase, binding=None):
    root = ordinary(Path(root).absolute())
    value = {'scope': SCOPE, 'root': str(root), 'session': session, 'phase': phase,
             'nonce': uuid.uuid4().hex, 'binding': binding,
             'observed_utc': datetime.now(timezone.utc).isoformat(),
             'objects': {}, 'unresolved': {}, 'producer_authentication': False}
    validate_context(value)
    value['objects'], value['unresolved'] = collect(root, True)
    validate_request(value)
    return value


def save(path, value):
    path = Path(path); ordinary(path.parent)
    with path.open('xb') as stream: stream.write(encoded(value))


def record(path):
    value = read_file(path)
    return {'path': str(Path(path).absolute()), 'size': value['size'], 'sha256': value['sha256']}


def load(path, sha):
    row = record(path)
    require(hexdigest(sha) and row['sha256'] == sha, 'E_COPY_EXTERNAL_HASH')
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == sha, 'E_COPY_EXTERNAL_HASH')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'E_COPY_DUPLICATE_KEY'); result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique)


def content(objects):
    return {k: {f: v for f, v in row.items() if f != 'identity'} for k, row in objects.items()}


def expected_copy_objects(objects):
    result = content(objects)
    result['.'] = {'kind': 'directory'}
    for name in objects:
        parent = PurePosixPath(name).parent
        while str(parent) != '.':
            result.setdefault(str(parent), {'kind': 'directory'}); parent = parent.parent
    return result


def copy_directory(data, target):
    """Check every existing ancestor before creating any child directory."""
    current = ordinary(Path(data))
    for part in Path(target).relative_to(data).parts:
        ordinary(current)
        child = current/part
        try:
            child.lstat()
        except FileNotFoundError:
            child.mkdir()
        ordinary(child)
        require(child.is_dir(), 'E_COPY_DIRECTORY_TYPE')
        current = child
    return current


def copy_denied(request, output):
    validate_request(request)
    root = ordinary(Path(request['root']))
    output = Path(output).absolute(); ordinary(output.parent)
    require(not output.is_relative_to(root) and not root.is_relative_to(output), 'E_COPY_OUTPUT_SCOPE')
    output.mkdir()  # No reuse or replacement, including after partial failure.
    data = output/'data'; data.mkdir()
    copied = {}
    for target in request['unresolved']:
        original = root if target == '.' else root/target
        rows, missing = collect(original)
        require(not missing, 'E_COPY_UNREADABLE')
        expected_kind = request['unresolved'][target]
        require(expected_kind == 'unknown' or rows['.']['kind'] == expected_kind, 'E_COPY_TYPE_CHANGED')
        for name, row in rows.items():
            name = target if name == '.' else (name if target == '.' else target+'/'+name)
            copied[name] = row
            dest = data if name == '.' else data/name
            if row['kind'] == 'directory':
                copy_directory(data,dest)
            else:
                copy_directory(data,dest.parent)
                require(read_file(root/name, dest) == row, 'E_COPY_SOURCE_CHANGED')
        again, missing = collect(original)
        require(again == rows and not missing, 'E_COPY_SOURCE_CHANGED')
    value = {'scope': SCOPE, 'request_sha256': digest(request), 'objects': dict(sorted(copied.items())),
             'producer_authentication': False}
    save(output/'Copies.json', value)
    return value


def verify_copies(request, output, sha):
    validate_request(request)
    output = ordinary(Path(output))
    copies = load(output/'Copies.json', sha)
    require(isinstance(copies, dict) and set(copies) == {'scope','request_sha256','objects','producer_authentication'}
            and copies['scope'] == SCOPE and copies['request_sha256'] == digest(request) and
            copies['producer_authentication'] is False, 'E_COPY_BINDING')
    validate_objects(copies['objects'])
    objects = copies['objects']
    targets = request['unresolved']
    require(all(sum(within(name, target) for target in targets) == 1 for name in objects) and
            all(target in objects for target in targets), 'E_COPY_COVERAGE')
    for name in objects:
        parent = str(PurePosixPath(name).parent)
        require(name in targets or objects.get(parent) == {'kind': 'directory'}, 'E_COPY_COVERAGE_PARENT')
    actual, denied = collect(output/'data')
    require(not denied and content(actual) == expected_copy_objects(objects), 'E_COPY_CONTENT')
    return copies


def bundle_from_copies(request, output, sha):
    """Derive every bundle field from the sealed request and verified copies."""
    validate_request(request)
    copies = verify_copies(request, output, sha)
    objects = dict(request['objects'])
    for key, row in copies['objects'].items():
        require(key not in objects, 'E_COPY_COVERAGE_OVERLAP'); objects[key] = row
    copy_record = record(Path(output)/'Copies.json')
    require(copy_record['sha256'] == sha, 'E_COPY_EXTERNAL_HASH')
    result = {k: request[k] for k in ('scope','root','session','phase','nonce','binding','producer_authentication')}
    result.update(objects=dict(sorted(objects.items())), request_sha256=digest(request),
                  copy_record=copy_record,
                  status='COMPLETE_'+request['phase']+'_SAMPLE_NOT_WORKLOAD_QUALIFICATION')
    return result


def merge(request, output, sha):
    result = bundle_from_copies(request,output,sha)
    actual, denied = collect(Path(request['root']), True)
    require(denied == request['unresolved'], 'E_COPY_VISIBILITY_CHANGED')
    require(actual == request['objects'], 'E_COPY_READABLE_CHANGED')
    return result


def compare(before, after):
    validate_context(before); validate_context(after)
    require(before['phase'] == 'BEFORE' and after['phase'] == 'AFTER', 'E_COPY_PHASE')
    validate_objects(before['objects']); validate_objects(after['objects'])
    require(before['root'] == after['root'] and before['session'] == after['session'] and
            before['nonce'] != after['nonce'] and after['binding']['before_sha256'] == digest(before), 'E_COPY_BINDING')
    require(content(before['objects']) == content(after['objects']), 'E_COPY_CONTENT_CHANGED')
    return {'status': 'CONTENT_MATCH_AT_BEFORE_AFTER_SAMPLES', 'producer_authentication': False,
            'whole_skill_ready': False, 'continuous_immutability_proven': False}
