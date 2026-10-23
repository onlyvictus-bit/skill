"""Bounded, self-reported observation for NEW diagnostic copies, never authority.

No protocol output, persistent file handle, worker thread, network or retry.
AST helpers below are controller-only and import ast/hashlib lazily.
"""
import contextlib
import functools
import json
import os
from pathlib import Path
import threading
import time

ENV = 'MEMORY_INTEGRITY_WORKER_DIAGNOSTICS'
SOURCE_PINS = {
    'worker.py': '6ae67511cefef46bf1c80541bb1ceb0252f4649c03cbcd9f1422c5c51bbe108c',
    'worker_client.py': '75b017e23f9334ac748d4293f1975cf3e2b1eefc039347885cd1f324d8f0b099',
    'distributed_retrieval.py': 'f84371cf78bcd596a594e76c9f649d3e1d2790829f280049b28b5e690f85ff62',
    'distributed_worker.py': '5d05e78e3917ef031fcb076e49bccd6b148e6f16dbba9c24e635b7d401faee00',
    'advanced_retrieval.py': '4fad12c689b545922eaaaf38edcb28d9442466ea312665911949ebd0c092f0a6',
    'offline_engine.py': 'be64a19e65289f36327eeaf832cdcca757970bbce36fa94860c0f7f082ea4ea7',
}
_lock = threading.RLock()
_key, _seq, _bytes, _span = None, 0, 0, 0
_errors = []
_creation = None
_parent = None
_roles = set()
_context = threading.local()
CHILD_EVENTS, CHILD_BYTES = 128, 16384
COORDINATOR_EVENTS, COORDINATOR_BYTES = 512, 65536
_FIELDS = {'kind', 'phase', 'span', 'outcome', 'error_type', 'errno', 'winerror',
           'filename', 'duration_ns', 'snapshot', 'child_pid', 'child_creation',
           'deadline_ns', 'budget_seconds', 'request_bytes', 'nodes', 'edges',
           'text_chars', 'stream', 'before', 'after', 'role', 'child_role'}


def role_for(phase):
    for prefix, role in [('distributed-worker', 'shard'), ('distributed-retrieval', 'coordinator'),
                         ('worker-client', 'client'), ('worker-', 'worker'),
                         ('offline-engine', 'numerical'), ('advanced-retrieval', 'advanced')]:
        if phase.startswith(prefix): return role
    if phase.startswith('lifetime-'): return 'coordinator'
    if phase in ('advanced-imports', 'community-hierarchy', 'community-reports', 'strategy-selection'): return 'advanced'
    if phase == 'numerical-imports': return 'numerical'
    return getattr(_context, 'role', 'worker')


def module_entry(name):
    role = role_for(name + '-entry')
    _roles.add(role)
    emit({'kind': 'POINT', 'phase': name + '-entry', 'role': role})


def ordinary(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('E_DIAG_TARGET_ABSOLUTE')
    for part in reversed((path, *path.parents)):
        value = part.lstat()
        if part.is_symlink() or getattr(value, 'st_file_attributes', 0) & 0x400:
            raise ValueError('E_DIAG_TARGET_REDIRECT')
    return path


def process_identity(pid):
    """PID + actual Windows creation FILETIME; no duplicate/inherited handles."""
    if os.name != 'nt':
        return 'NONWINDOWS_UNVERIFIED:' + str(pid)
    import ctypes
    from ctypes import wintypes as w
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.GetProcessTimes.argtypes = [w.HANDLE, ctypes.POINTER(w.FILETIME),
                                      ctypes.POINTER(w.FILETIME), ctypes.POINTER(w.FILETIME),
                                      ctypes.POINTER(w.FILETIME)]
    kernel.GetProcessTimes.restype = w.BOOL
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return 'UNKNOWN:' + str(ctypes.get_last_error())
    try:
        born, ended, system, user = (w.FILETIME() for unused in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(born), ctypes.byref(ended),
                                      ctypes.byref(system), ctypes.byref(user)):
            return 'UNKNOWN:' + str(ctypes.get_last_error())
        return str((born.dwHighDateTime << 32) | born.dwLowDateTime)
    finally:
        kernel.CloseHandle(handle)


def _state():
    global _key, _seq, _bytes, _span, _creation, _parent
    value = os.environ.get(ENV)
    if not value:
        return None
    root = ordinary(Path(value))
    if not root.is_dir():
        raise ValueError('E_DIAG_TARGET_DIRECTORY')
    key = (os.getpid(), str(root))
    if _key != key:
        _key, _seq, _bytes, _span = key, 0, 0, 0
        _errors.clear()
        _roles.clear()
        _creation = process_identity(os.getpid())
        _parent = (os.getppid(), process_identity(os.getppid()))
    return root


def next_path():
    with _lock:
        root = _state()
        return root / (str(os.getpid()) + '-' + str(_seq).zfill(3) + '.json')


def failures():
    return list(_errors)


def _failed(root, reason):
    if len(_errors) < 16:
        _errors.append(reason)
    # Snapshot failures occur before phase emission. Reuse only an already
    # established exact current root; never recurse into failing _state().
    if root is None and _key and _key[0] == os.getpid() and _key[1] == os.environ.get(ENV):
        root = Path(_key[1])
    if root is not None:
        try:
            marker = root / (str(os.getpid()) + '.error')
            ordinary(root)
            with marker.open('xb') as stream:
                stream.write(json.dumps({'status': 'DIAGNOSTIC_INCOMPLETE',
                                         'pid': os.getpid(), 'reason': reason}).encode('ascii'))
        except Exception:
            pass  # A missing/incomplete event set is also invalid to the controller.


def emit(event):
    global _seq, _bytes
    root = None
    with _lock:
        try:
            root = _state()
            if root is None:
                return
            if not isinstance(event, dict) or not set(event) <= _FIELDS:
                raise ValueError('E_DIAG_FIELDS')
            phase_name = event.get('phase')
            if not isinstance(phase_name, str) or not 1 <= len(phase_name) <= 100 or \
                    any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for ch in phase_name):
                raise ValueError('E_DIAG_PHASE')
            if event.get('kind') not in ('START', 'END', 'POINT'):
                raise ValueError('E_DIAG_KIND')
            event = dict(event)
            event.setdefault('role', role_for(phase_name))
            _roles.add(event['role'])
            row = dict(schema=1, arm=root.name, pid=os.getpid(), creation=_creation,
                       parent_pid=_parent[0], parent_creation=_parent[1],
                       thread=threading.get_ident(), sequence=_seq,
                       wall_ns=time.monotonic_ns(), cpu_ns=time.process_time_ns(), **event)
            raw = json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False).encode('ascii')
            count, cap = ((COORDINATOR_EVENTS, COORDINATOR_BYTES) if 'coordinator' in _roles else
                          (CHILD_EVENTS, CHILD_BYTES))
            if _seq >= count or len(raw) > 4096 or _bytes + len(raw) > cap:
                raise ValueError('E_DIAG_LIMIT')
            target = next_path()
            with target.open('xb') as stream:
                stream.write(raw)
            _seq += 1
            _bytes += len(raw)
        except Exception as error:
            _failed(root, type(error).__name__ + ':' + str(error).split(':', 1)[0][:100])


@contextlib.contextmanager
def phase(name, **fields):
    global _span
    with _lock:
        try:
            _state()
        except Exception as error:
            _failed(None, type(error).__name__ + ':E_DIAG_CONTEXT')
        span = _span
        _span += 1
    started = time.monotonic_ns()
    previous_role = getattr(_context, 'role', None)
    _context.role = role_for(name)
    emit(dict(kind='START', phase=name, span=span, **fields))
    outcome, detail = 'RETURNED', {}
    try:
        yield
    except BaseException as error:
        outcome = 'EXCEPTION'
        detail = {'error_type': type(error).__name__}
        for key in ('errno', 'winerror', 'filename'):
            value = getattr(error, key, None)
            if value is not None:
                detail[key] = value if isinstance(value, (int, str)) else 'UNKNOWN'
        raise
    finally:
        emit(dict(kind='END', phase=name, span=span, outcome=outcome,
                  duration_ns=time.monotonic_ns() - started, **detail))
        if previous_role is None:
            try: del _context.role
            except AttributeError: pass
        else: _context.role = previous_role


def stream_snapshot(stream):
    if stream is not None and not hasattr(stream, 'closed'):
        return {'not_a_stream': True}
    result = {'closed': stream is None or stream.closed}
    if not result['closed']:
        try:
            fd = stream.fileno()
            result.update(fd=fd, inheritable=os.get_inheritable(fd))
            if os.name == 'nt':
                import msvcrt
                result['native_handle'] = msvcrt.get_osfhandle(fd)
        except (OSError, ValueError, AttributeError) as error:
            result['observation_error'] = type(error).__name__
    return result


def snapshot(value):
    if value is None or not hasattr(value, 'process'):
        return {}
    process = value.process
    row = {'session': id(value), 'lane': getattr(value, 'lane', None),
           'child_pid': process.pid if process else None,
           'returncode_already_observed': process.returncode if process else None,
           'writer_alive': value.writer.is_alive() if value.writer else False}
    row['streams'] = {name: stream_snapshot(getattr(value, name, None))
                      for name in ('reader', 'output', 'errors')}
    row['streams']['stdin'] = stream_snapshot(process.stdin if process else None)
    if getattr(value, 'directory', None) is not None:
        row['directory'] = value.directory.name
    return row


def safe_snapshot(value):
    try:
        return snapshot(value) if hasattr(value, 'process') else stream_snapshot(value)
    except Exception as error:
        _failed(None, 'E_DIAG_SNAPSHOT:' + type(error).__name__)
        return {'observation_error': type(error).__name__}


def traced(name):
    def decorate(function):
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            # No polling/reaping/opening observed streams in these snapshots.
            owner = args[0] if args else None
            detail = {'snapshot': safe_snapshot(owner)} if name in (
                'distributed-retrieval-init', 'distributed-retrieval-stop', 'distributed-retrieval-close') else {}
            with phase(name, **detail):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def call(name, owner, method, *args, **kwargs):
    detail = {}
    try:
        if method == 'close': detail['before'] = safe_snapshot(owner)
        if method == 'cleanup': detail['filename'] = str(Path(owner.name) / 'output')
    except Exception as error:
        _failed(None, 'E_DIAG_CALL_CONTEXT:' + type(error).__name__)
    with phase(name, **detail):
        try:
            return getattr(owner, method)(*args, **kwargs)
        finally:
            if method == 'close':
                emit({'kind': 'POINT', 'phase': name + '-after', 'after': safe_snapshot(owner)})


def returned_spawn(process, child_role):
    emit({'kind': 'POINT', 'phase': 'popen-return', 'child_pid': process.pid,
          'child_creation': process_identity(process.pid), 'child_role': child_role})
    return process


def deadline(started, seconds, child_pid):
    emit({'kind': 'POINT', 'phase': 'worker-deadline', 'child_pid': child_pid,
          'deadline_ns': int((started + seconds) * 1000000000), 'budget_seconds': seconds})


def sizes(payload, raw=None):
    row = {'kind': 'POINT', 'phase': 'input-size'}
    if raw is not None:
        row['request_bytes'] = len(raw)
    if isinstance(payload, dict):
        for field in ('nodes', 'edges'):
            if isinstance(payload.get(field), list):
                row[field] = len(payload[field])
        if isinstance(payload.get('nodes'), list):
            row['text_chars'] = sum(len(n.get('text', '')) for n in payload['nodes'] if isinstance(n, dict))
    emit(row)


def parse_events(records, expected):
    """Invalid or unfinished telemetry cannot establish a cause or a repair."""
    result = {'status': 'INCOMPLETE', 'active': [], 'errors': [], 'events': [],
              'cause_proven': False, 'fix_validated': False, 'gate1_complete': False}
    stacks, counters, sizes_by_pid = {}, {}, {}
    try:
        if not isinstance(records, list) or not records or sum(map(len, records)) > 1048576:
            raise ValueError('E_DIAG_EMPTY_OR_LIMIT')
        rows = [json.loads(raw.decode('ascii')) for raw in records]
        rows.sort(key=lambda row: (row['pid'], row['sequence']))
        for row, raw in zip(rows, sorted(records, key=lambda raw: (json.loads(raw)['pid'], json.loads(raw)['sequence']))):
            pid = row['pid']
            if row.get('schema') != 1 or row.get('arm') != expected['arm'] or \
                    type(pid) is not int or not row.get('creation') or \
                    type(row.get('sequence')) is not int or row['sequence'] != counters.get(pid, 0) or \
                    any(type(row.get(key)) is not int or row[key] < 0 for key in ('wall_ns', 'cpu_ns', 'thread')):
                raise ValueError('E_DIAG_EVENT_IDENTITY_ORDER')
            if 'pids' in expected and expected['pids'].get(str(pid)) != row['creation']:
                raise ValueError('E_DIAG_PID_GENERATION')
            counters[pid] = row['sequence'] + 1
            sizes_by_pid[pid] = sizes_by_pid.get(pid, 0) + len(raw)
            if counters[pid] > COORDINATOR_EVENTS or sizes_by_pid[pid] > COORDINATOR_BYTES or len(counters) > 64:
                raise ValueError('E_DIAG_LIMIT')
            key = (pid, row['creation'], row['thread'])
            stack = stacks.setdefault(key, [])
            if row['kind'] == 'START':
                stack.append(row)
            elif row['kind'] == 'END':
                if not stack or (stack[-1]['span'], stack[-1]['phase']) != (row['span'], row['phase']) or \
                        row['wall_ns'] < stack[-1]['wall_ns'] or row.get('outcome') not in ('RETURNED', 'EXCEPTION'):
                    raise ValueError('E_DIAG_PHASE_PAIR')
                stack.pop()
            elif row['kind'] != 'POINT':
                raise ValueError('E_DIAG_KIND')
            result['events'].append(row)
        result['active'] = [item for stack in stacks.values() for item in stack]
        # Balance alone is only a fragment. Only validate_trace can close roles.
        result['status'] = 'INCOMPLETE' if result['active'] else 'FRAGMENT_OBSERVED_NOT_COMPLETE'
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        result['errors'].append(type(error).__name__ + ':' + str(error))
    return result


def validate_trace(records, expected):
    """Checked filenames + root capture + process/spawn/role/phase closure.

    Still self-reported observations, not authenticated production evidence.
    Killed work with an open phase is incomplete; idle shards may be reaped only
    after their bounded request phases finish, as observed by parent wait/close.
    """
    result = parse_events([r['raw'] for r in records], expected)
    try:
        def observation_failed(value):
            if isinstance(value, dict):
                return 'observation_error' in value or any(observation_failed(v) for v in value.values())
            if isinstance(value, list): return any(observation_failed(v) for v in value)
            return False
        if set(expected) != {'arm', 'root_pid', 'public_count'} or type(expected['root_pid']) is not int:
            raise ValueError('E_DIAG_EXPECTATION')
        rows = result['events']
        if result['errors'] or result['active'] or len(rows) != len(records):
            raise ValueError('E_DIAG_PARTIAL_TRACE')
        names, identities, by_pid = set(), {}, {}
        for item in records:
            row = json.loads(item['raw'])
            name = str(row['pid']) + '-' + str(row['sequence']).zfill(3) + '.json'
            if item['name'] != name or name in names: raise ValueError('E_DIAG_FILENAME')
            names.add(name)
        allowed = {
            'client': {'worker-client-entry', 'worker-client-process', 'popen-entry', 'popen-return', 'worker-deadline'},
            'worker': {'worker-entry', 'worker-main', 'worker-runtime_identity', 'worker-retrieve', 'worker-shacl',
                       'base-imports-complete', 'input-size', 'semantica-imports', 'vectors', 'graph-construction',
                       'provenance', 'shacl-validation', 'serialization'},
            'shard': {'distributed-worker-entry', 'base-imports-complete', 'shard-request'},
            'advanced': {'advanced-retrieval-entry', 'advanced-retrieval-retrieve', 'advanced-retrieval-traverse',
                         'advanced-imports', 'community-hierarchy', 'community-reports', 'strategy-selection'},
            'numerical': {'offline-engine-entry', 'offline-engine-search_vectors', 'numerical-imports'},
            'coordinator': {'distributed-retrieval-entry', 'distributed-retrieval-init', 'distributed-retrieval-request',
                            'distributed-retrieval-stop', 'distributed-retrieval-close', 'distributed-retrieval-call',
                            'popen-entry', 'popen-return', 'lifetime-close', 'lifetime-close-after',
                            'lifetime-cleanup', 'lifetime-wait', 'lifetime-kill'},
        }
        for row in rows:
            if observation_failed(row): raise ValueError('E_DIAG_OBSERVATION_FAILED')
            pid = row['pid']; identity = (row['creation'], row['parent_pid'], row['parent_creation'])
            if (not str(row['creation']).isdigit() or not str(row['parent_creation']).isdigit() or
                    identities.setdefault(pid, identity) != identity): raise ValueError('E_DIAG_PID_GENERATION')
            if row.get('role') not in allowed or row['phase'] not in allowed[row['role']]: raise ValueError('E_DIAG_ROLE')
            if not set(row) <= {'schema','arm','pid','creation','parent_pid','parent_creation','thread','sequence','wall_ns','cpu_ns'} | _FIELDS:
                raise ValueError('E_DIAG_FIELDS')
            group = by_pid.setdefault(pid, [])
            if group and (row['wall_ns'] < group[-1]['wall_ns'] or row['cpu_ns'] < group[-1]['cpu_ns']):
                raise ValueError('E_DIAG_CLOCK')
            group.append(row)
        root = expected['root_pid']
        if root not in by_pid: raise ValueError('E_DIAG_MISSING_ROOT')
        def phases(pid): return {r['phase'] for r in by_pid[pid]}
        if 'worker-client-entry' not in phases(root): raise ValueError('E_DIAG_ROOT_ROLE')
        spawned = {}
        for row in rows:
            if row['phase'] == 'popen-return':
                child = row['child_pid']
                if child in spawned or row.get('child_role') not in ('worker', 'shard'):
                    raise ValueError('E_DIAG_DUPLICATE_OR_UNKNOWN_SPAWN')
                spawned[child] = (row['pid'], row['child_creation'], row['child_role'])
        for pid, identity in identities.items():
            if pid != root:
                visited = {pid}; cursor = pid
                while cursor != root:
                    parent = identities[cursor][1]
                    if parent in visited or parent not in identities or identities[parent][0] != identities[cursor][2]:
                        raise ValueError('E_DIAG_UNBOUND_PROCESS')
                    visited.add(parent); cursor = parent
            present = phases(pid)
            if pid != root and ('worker-entry' in present or 'distributed-worker-entry' in present):
                required_role = 'shard' if 'distributed-worker-entry' in present else 'worker'
                if spawned.get(pid) != (identity[1], identity[0], required_role):
                    raise ValueError('E_DIAG_UNCLAIMED_EMITTER')
            if 'distributed-worker-entry' in present:
                required = {'distributed-worker-entry', 'base-imports-complete', 'worker-runtime_identity', 'shard-request'}
            elif 'worker-entry' in present:
                required = {'worker-entry', 'base-imports-complete', 'worker-main', 'worker-runtime_identity',
                            'worker-retrieve', 'input-size', 'serialization'}
            else: required = {'worker-client-entry', 'worker-client-process'}
            if not required <= present: raise ValueError('E_DIAG_MISSING_ROLE_PHASE')
            for row in by_pid[pid]:
                if row['phase'] == 'popen-return':
                    child = row['child_pid']
                    entry = 'distributed-worker-entry' if row['child_role'] == 'shard' else 'worker-entry'
                    if (child not in identities or identities[child] != (row['child_creation'], pid, identity[0]) or
                            entry not in phases(child)): raise ValueError('E_DIAG_SPAWN_CLOSURE')
            # Each completed actual _process call must have its one original
            # spawn and unchanged budget marker. Removing a whole balanced
            # method is not a complete observation of the public workload.
            for begin in (r for r in by_pid[pid] if r['phase'] == 'worker-client-process' and r['kind'] == 'START'):
                end = next((r for r in by_pid[pid] if r['kind'] == 'END' and r['phase'] == begin['phase'] and
                            r['span'] == begin['span'] and r['thread'] == begin['thread']), None)
                segment = [r for r in by_pid[pid] if end and begin['sequence'] < r['sequence'] < end['sequence']]
                if (sum(r['phase'] == 'popen-return' for r in segment) != 1 or
                        sum(r['phase'] == 'worker-deadline' and r.get('budget_seconds') == 30 for r in segment) != 1):
                    raise ValueError('E_DIAG_PROCESS_PHASE_CLOSURE')
        for pid, group in by_pid.items():
            spawned_shards = [r['child_pid'] for r in group if r['phase'] == 'popen-return' and r['child_role'] == 'shard']
            if spawned_shards:
                requests = sum(r['phase'] == 'distributed-retrieval-request' and r['kind'] == 'START' for r in group)
                received = sum(r['phase'] == 'shard-request' and r['kind'] == 'START'
                               for child in spawned_shards for r in by_pid[child])
                if requests != received: raise ValueError('E_DIAG_REQUEST_CLOSURE')
        public = [pid for pid in by_pid if pid != root and identities[pid][1] == root and
                  'worker-client-entry' in phases(pid) and 'worker-entry' not in phases(pid)]
        if len(public) != expected['public_count']: raise ValueError('E_DIAG_MISSING_PUBLIC_PROCESS')
        for pid, group in by_pid.items():
            coordinator = 'distributed-retrieval-entry' in phases(pid)
            count, cap = ((COORDINATOR_EVENTS, COORDINATOR_BYTES) if coordinator else (CHILD_EVENTS, CHILD_BYTES))
            if len(group) > count or sum(len(r['raw']) for r in records if json.loads(r['raw'])['pid'] == pid) > cap:
                raise ValueError('E_DIAG_LIMIT')
        result['status'] = 'OBSERVED'
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        result['status'] = 'INCOMPLETE'
        result['errors'].append(type(error).__name__ + ':' + str(error))
    return result


def diagnostic_source(raw, expected_sha, role):
    """Hash-bound AST overlay. Remove observer nodes to obtain the original AST."""
    import ast
    import hashlib
    if role not in SOURCE_PINS or expected_sha != SOURCE_PINS[role] or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('E_DIAG_SOURCE_PIN')
    tree = ast.parse(raw.decode('utf-8'))
    def statement(text):
        return ast.parse(text).body[0]
    def with_phase(nodes, label):
        return ast.With(items=[ast.withitem(context_expr=ast.Call(
            func=ast.Attribute(value=ast.Name(id='_wd', ctx=ast.Load()), attr='phase', ctx=ast.Load()),
            args=[ast.Constant(label)], keywords=[]))], body=nodes)
    def assigns(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == name
                                                   for target in node.targets for x in ast.walk(target))
    def bracket(body, first, last, label):
        starts = [n for n, node in enumerate(body) if first(node)]
        if len(starts) != 1:
            raise ValueError('E_DIAG_SOURCE_ANCHOR:' + label)
        ends = [n for n, node in enumerate(body) if n >= starts[0] and last(node)]
        if not ends:
            raise ValueError('E_DIAG_SOURCE_ANCHOR:' + label)
        a, b = starts[0], ends[0]
        return body[:a] + [with_phase(body[a:b+1], label)] + body[b+1:]
    class Overlay(ast.NodeTransformer):
        function = None
        def visit_FunctionDef(self, node):
            before = self.function
            self.function = node.name
            self.generic_visit(node)
            self.function = before
            wanted = {'worker.py': {'main', 'runtime_identity', 'retrieve', 'shacl'},
                      'worker_client.py': {'_process'},
                      'distributed_retrieval.py': {'__init__', 'request', 'stop', 'close', '__call__'},
                      'distributed_worker.py': set(), 'advanced_retrieval.py': {'retrieve', 'traverse'},
                      'offline_engine.py': {'search_vectors'}}[role]
            if node.name in wanted:
                node.decorator_list.append(ast.parse('_wd.traced(' + repr(role[:-3].replace('_', '-') + '-' + node.name.strip('_')) + ')', mode='eval').body)
            if role == 'worker.py' and node.name == 'retrieve':
                node.body = bracket(node.body, lambda n: isinstance(n, ast.ImportFrom) and n.module == 'semantica.context.context_graph',
                                    lambda n: isinstance(n, ast.ImportFrom) and n.module == 'semantica.provenance', 'semantica-imports')
                node.body = bracket(node.body, lambda n: isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'text_mode' and any(isinstance(child, ast.ImportFrom) and child.module == 'knowledge_bridge.offline_engine' for child in ast.walk(n)),
                                    lambda n: True, 'vectors')
                node.body = bracket(node.body, lambda n: assigns(n, 'graph'),
                                    lambda n: isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'e', 'graph-construction')
                node.body = bracket(node.body, lambda n: assigns(n, 'prov'),
                                    lambda n: isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'item', 'provenance')
                node.body = bracket(node.body, lambda n: assigns(n, 'conform'),
                                    lambda n: isinstance(n, ast.If), 'shacl-validation')
            if role == 'advanced_retrieval.py' and node.name == 'retrieve':
                node.body = bracket(node.body, lambda n: isinstance(n, ast.ImportFrom) and n.module == 'semantica.kg.community_hierarchy',
                                    lambda n: isinstance(n, ast.ImportFrom) and n.module == 'semantica.context.drift_search', 'advanced-imports')
                for target, label in [('hierarchy', 'community-hierarchy'), ('reports', 'community-reports')]:
                    node.body = bracket(node.body, lambda n, target=target: assigns(n, target), lambda n: True, label)
                node.body = bracket(node.body, lambda n: isinstance(n, ast.If) and isinstance(n.test, ast.Compare) and isinstance(n.test.left, ast.Name) and n.test.left.id == 'strategy' and isinstance(n.test.ops[0], ast.Eq) and isinstance(n.test.comparators[0], ast.Constant) and n.test.comparators[0].value == 'community',
                                    lambda n: True, 'strategy-selection')
            return node
        def visit_While(self, node):
            self.generic_visit(node)
            if role == 'distributed_worker.py':
                # Do not time the idle blocking read as an unfinished request.
                # Original request/error/serialization order is unchanged.
                node.body = bracket(node.body, lambda n: isinstance(n, ast.Try),
                                    lambda n: isinstance(n, ast.Expr) and 'flush' in ast.unparse(n), 'shard-request')
            return node
        def visit_ImportFrom(self, node):
            if role in ('worker.py', 'distributed_worker.py') and node.module == 'knowledge_bridge' and any(a.name == 'contracts' for a in node.names):
                return [node, statement("_wd.emit({'kind':'POINT','phase':'base-imports-complete'})")]
            return node
        def visit_Try(self, node):
            self.generic_visit(node)
            if role == 'offline_engine.py' and any(isinstance(n, ast.Import) and any(a.name == 'numpy' for a in n.names) for n in node.body):
                node.body = [with_phase(node.body, 'numerical-imports')]
            if role == 'worker.py' and self.function == 'main' and any(assigns(n, 'response') for n in node.body):
                node.body = bracket(node.body, lambda n: isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'update',
                                    lambda n: isinstance(n, ast.Return), 'serialization')
            return node
        def visit_Assign(self, node):
            self.generic_visit(node)
            extra = []
            if role == 'worker_client.py' and assigns(node, 'started'):
                extra.append(statement('_wd.deadline(started, timeout, process.pid)'))
            if role == 'worker.py' and self.function == 'main' and assigns(node, 'payload'):
                extra.append(statement('_wd.sizes(payload, raw)'))
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and \
                    isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == 'subprocess' and node.value.func.attr == 'Popen':
                child_role = 'shard' if role == 'distributed_retrieval.py' else 'worker'
                node.value = ast.Call(func=ast.Attribute(value=ast.Name(id='_wd', ctx=ast.Load()), attr='returned_spawn', ctx=ast.Load()), args=[node.value, ast.Constant(child_role)], keywords=[])
                return [statement("_wd.emit({'kind':'POINT','phase':'popen-entry'})"), node] + extra
            return [node] + extra if extra else node
        def visit_Call(self, node):
            self.generic_visit(node)
            if role == 'distributed_retrieval.py' and isinstance(node.func, ast.Attribute) and \
                    (node.func.attr in ('cleanup', 'kill') or
                     (node.func.attr == 'close' and isinstance(node.func.value, ast.Name) and node.func.value.id == 'stream') or
                     (node.func.attr == 'wait' and ast.unparse(node.func.value) == 'self.process')):
                method = node.func.attr
                node = ast.Call(func=ast.Attribute(value=ast.Name(id='_wd', ctx=ast.Load()), attr='call', ctx=ast.Load()),
                                args=[ast.Constant('lifetime-' + method), node.func.value, ast.Constant(method), *node.args], keywords=node.keywords)
            return node
        def visit_Set(self, node):
            self.generic_visit(node)
            # This exact environment whitelist exists once in each copied client.
            if role in ('worker_client.py', 'distributed_retrieval.py') and \
                    {x.value for x in node.elts if isinstance(x, ast.Constant)} == {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL'}:
                node.elts.append(ast.Constant(ENV))
            return node
    tree = Overlay().visit(tree)
    prelude = "from knowledge_bridge import _worker_diag_v1 as _wd\n_wd.module_entry(" + repr(role[:-3].replace('_', '-')) + ")\n"
    if role in ('worker.py', 'distributed_worker.py'):
        prelude = "import os as _wdo\nimport sys as _wds\n_wds.path.insert(0,_wdo.path.dirname(_wdo.path.dirname(__file__)))\n" + prelude
    start = 1 if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str) else 0
    tree.body[start:start] = ast.parse(prelude).body
    ast.fix_missing_locations(tree)
    observed = (ast.unparse(tree) + '\n').encode('utf-8')
    if original_ast(observed) != original_ast(raw):
        raise ValueError('E_DIAG_SOURCE_SEMANTICS')
    return observed


def original_ast(raw):
    import ast
    def helper(node, method=None):
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
            isinstance(node.func.value, ast.Name) and node.func.value.id == '_wd' and \
            (method is None or node.func.attr == method)
    class Strip(ast.NodeTransformer):
        def visit_Import(self, node):
            return None if any(a.asname in ('_wdo', '_wds') for a in node.names) else node
        def visit_ImportFrom(self, node):
            return None if any(a.asname == '_wd' for a in node.names) else node
        def visit_Expr(self, node):
            if any(helper(node.value, name) for name in ('emit', 'module_entry', 'deadline', 'sizes')) or (isinstance(node.value, ast.Call) and ast.unparse(node.value.func).startswith('_wds.')):
                return None
            return self.generic_visit(node)
        def visit_With(self, node):
            if len(node.items) == 1 and helper(node.items[0].context_expr, 'phase'):
                return [self.visit(child) for child in node.body]
            return self.generic_visit(node)
        def visit_FunctionDef(self, node):
            node.decorator_list = [d for d in node.decorator_list if not helper(d, 'traced')]
            return self.generic_visit(node)
        def visit_Call(self, node):
            if helper(node, 'returned_spawn'):
                return self.visit(node.args[0])
            if helper(node, 'call'):
                return self.visit(ast.Call(func=ast.Attribute(value=node.args[1], attr=node.args[2].value, ctx=ast.Load()), args=node.args[3:], keywords=node.keywords))
            return self.generic_visit(node)
        def visit_Set(self, node):
            node.elts = [e for e in node.elts if not (isinstance(e, ast.Constant) and e.value == ENV)]
            return self.generic_visit(node)
    return ast.dump(Strip().visit(ast.parse(raw.decode('utf-8'))), include_attributes=False)
