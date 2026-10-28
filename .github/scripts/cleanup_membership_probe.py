"""MP1 native membership witness; records a bounded fixture and never fixes MI."""
import argparse
import ctypes
from ctypes import wintypes as w
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import time


ROLES = ('root', 'relay', 'launcher', 'child')
MAX_RECORD_BYTES = 1048576
PROCESS_ACCESS = 0x101001  # TERMINATE | QUERY_LIMITED_INFORMATION | SYNCHRONIZE
THREAD_ACCESS = 0x100801  # TERMINATE | QUERY_LIMITED_INFORMATION | SYNCHRONIZE
WAIT_OBJECT_0, WAIT_TIMEOUT = 0, 258
ERROR_NOT_FOUND = 1168


class _Accounting(ctypes.Structure):
    _fields_ = [('times', ctypes.c_int64 * 4), ('faults', w.DWORD),
                ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]


class _Members(ctypes.Structure):
    _fields_ = [('assigned', w.DWORD), ('listed', w.DWORD),
                ('pids', ctypes.c_size_t * 1024)]


def _require(value, message):
    if not value:
        raise ValueError(message)


def _ordinary(path):
    path = Path(path)
    for part in (path, *path.parents):
        if part.exists():
            _require(not part.is_symlink() and not getattr(part, 'is_junction', lambda: False)(),
                     'E_MP_REDIRECTED_PATH')
    if path.exists():
        _require(path.stat().st_nlink == 1, 'E_MP_LINKED_PATH')


def _inside(path, root):
    try:
        Path(path).resolve(strict=False).relative_to(Path(root).resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_snapshot(row):
    """Validate a complete current membership observation, never cumulative total."""
    _require(isinstance(row, dict) and set(row) == {'members', 'assigned', 'listed', 'total', 'active', 'roles'},
             'E_MP_MEMBERSHIP')
    _require(isinstance(row['members'], list) and all(type(pid) is int and pid > 0 for pid in row['members']) and
             len(row['members']) == len(set(row['members'])) and
             all(type(row[key]) is int and row[key] >= 0 for key in ('assigned', 'listed', 'total', 'active')) and
             row['assigned'] == row['listed'] == row['active'] == len(row['members']) and row['total'] >= row['active'],
             'E_MP_MEMBERSHIP')
    roles = row['roles']
    _require(isinstance(roles, dict) and set(roles) == set(ROLES), 'E_MP_CHAIN')
    pids = []
    for number, role in enumerate(ROLES):
        item = roles[role]
        _require(isinstance(item, dict) and set(item) ==
                 {'pid', 'creation', 'ppid', 'parent_creation', 'in_job', 'signalled'}, 'E_MP_CHAIN')
        _require(type(item['pid']) is int and item['pid'] > 0 and type(item['creation']) is str and
                 item['creation'].isdigit() and type(item['ppid']) is int and item['ppid'] >= 0 and
                 type(item['parent_creation']) is str and item['parent_creation'].isdigit() and
                 type(item['in_job']) is bool and type(item['signalled']) is bool, 'E_MP_CHAIN')
        pids.append(item['pid'])
        if number:
            parent = roles[ROLES[number - 1]]
            _require(item['ppid'] == parent['pid'] and item['parent_creation'] == parent['creation'],
                     'E_MP_CHAIN')
    _require(len(pids) == len(set(pids)), 'E_MP_CHAIN')
    members = set(row['members'])
    _require(all(item['in_job'] == (item['pid'] in members) for item in roles.values()),
             'E_MP_MEMBERSHIP')
    # `total` is intentionally not compared: it is lifetime accounting, not live membership.
    return row


def classify(before, after_role_signalled_dict, writer_alive, stop_error, observation_errors=[]):
    """Classify one observation without promoting a fixture to a repair."""
    _require(not observation_errors, 'E_MP_OBSERVATION')
    validate_snapshot(before)
    _require(isinstance(after_role_signalled_dict, dict) and
             set(after_role_signalled_dict) == set(ROLES) and
             all(type(value) is bool for value in after_role_signalled_dict.values()) and type(writer_alive) is bool,
             'E_MP_MEMBERSHIP')
    outside_live = any(not before['roles'][role]['in_job'] and not after_role_signalled_dict[role]
                       for role in ROLES)
    inside_live = any(before['roles'][role]['in_job'] and not after_role_signalled_dict[role]
                      for role in ROLES)
    if outside_live:
        return 'MEMBERSHIP_GAP_OBSERVED_NOT_FIXED'
    if inside_live:
        return 'MEMBERSHIP_CONTRADICTION_REQUIRES_REDESIGN'
    if writer_alive:
        return 'PIPE_CANCELLATION_GAP_NOT_FIXED'
    if stop_error:
        return 'STOP_FAILURE_WITH_ALL_HANDLES_EXITED_NOT_FIXED'
    return 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE'


def _kernel():
    if os.name != 'nt':
        raise OSError('E_MP_WINDOWS_REQUIRED')
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        'CloseHandle': ([w.HANDLE], w.BOOL),
        'GetProcessTimes': ([w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], w.BOOL),
        'GetThreadTimes': ([w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], w.BOOL),
        'GetThreadId': ([w.HANDLE], w.DWORD),
        'GetProcessIdOfThread': ([w.HANDLE], w.DWORD),
        'IsProcessInJob': ([w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
        'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
        'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
        'TerminateProcess': ([w.HANDLE, w.UINT], w.BOOL),
        'CancelSynchronousIo': ([w.HANDLE], w.BOOL),
    }
    for name, (args, result) in signatures.items():
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    return api


def _check(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def _filetime(value):
    return str((int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime))


def _creation(api, handle, *, thread=False):
    creation = w.FILETIME(); exit_time = w.FILETIME(); kernel = w.FILETIME(); user = w.FILETIME()
    function = api.GetThreadTimes if thread else api.GetProcessTimes
    _check(function(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel), ctypes.byref(user)))
    return _filetime(creation)


def _signalled(api, handle):
    result = api.WaitForSingleObject(handle, 0)
    _require(result in (WAIT_OBJECT_0, WAIT_TIMEOUT), 'E_MP_HANDLE_WAIT')
    return result == WAIT_OBJECT_0


def _pin_writer(api, writer, owned_handles):
    """Bind the cancellation handle to the still-live Python writer thread."""
    _require(writer is not None and writer.is_alive() and isinstance(writer.native_id, int) and writer.native_id > 0,
             'E_MP_WRITER_NOT_BLOCKED')
    native_id = writer.native_id
    handle = api.OpenThread(THREAD_ACCESS, False, native_id); _check(handle)
    try:
        _require(api.GetThreadId(handle) == native_id and api.GetProcessIdOfThread(handle) == os.getpid() and
                 not _signalled(api, handle) and writer.is_alive() and writer.native_id == native_id,
                 'E_MP_WRITER_REUSED')
        creation = _creation(api, handle, thread=True)
    except BaseException as original:
        # The handle was opened locally but did not prove it still belongs to
        # this writer.  Never use it for cancellation; still retain a close
        # failure on the original identity error rather than leaking it.
        try:
            if not api.CloseHandle(handle):
                original.add_note('E_MP_HANDLE_CLOSE: '+str(ctypes.get_last_error()))
        except Exception as close_error:
            original.add_note('E_MP_HANDLE_CLOSE: '+repr(close_error))
        raise
    owned_handles['writer'] = handle
    return handle, {'thread_id':native_id, 'creator_process':api.GetProcessIdOfThread(handle), 'creation':creation}


def _adopt_role_handle(api, role, marker, borrowed_handle, owned_handles):
    """Validate birth before exposing a handle; borrowed Session root is never closed here."""
    local = borrowed_handle is None
    handle = api.OpenProcess(PROCESS_ACCESS, False, marker['pid']) if local else borrowed_handle
    _check(handle)
    try:
        _require(_creation(api, handle) == marker['creation'], 'E_MP_PID_REUSED')
    except BaseException as original:
        if local:
            try:
                if not api.CloseHandle(handle):
                    original.add_note('E_MP_HANDLE_CLOSE: '+str(ctypes.get_last_error()))
            except Exception as close_error:
                original.add_note('E_MP_HANDLE_CLOSE: '+repr(close_error))
        raise
    if local:
        owned_handles[role] = handle
    return handle


def _job_members(api, job_handle):
    members = _Members()
    _check(api.QueryInformationJobObject(job_handle, 3, ctypes.byref(members), ctypes.sizeof(members), None))
    _require(members.listed <= 1024 and members.assigned == members.listed, 'E_MP_MEMBERSHIP')
    return {'assigned': int(members.assigned), 'listed': int(members.listed),
            'members': [int(pid) for pid in members.pids[:members.listed]]}


def _accounting(api, job_handle):
    value = _Accounting()
    _check(api.QueryInformationJobObject(job_handle, 1, ctypes.byref(value), ctypes.sizeof(value), None))
    return {'total': int(value.total), 'active': int(value.active)}


def _in_job(api, process_handle, job_handle):
    inside = w.BOOL()
    _check(api.IsProcessInJob(process_handle, job_handle, ctypes.byref(inside)))
    return bool(inside.value)


def _chain_fixture(root, *, control_topology):
    """A retained stdlib four-process fixture, labelled controller-only in its receipt."""
    helper = '''import ctypes, json, os, sys\nfrom ctypes import wintypes as w\nfrom pathlib import Path\n\ndef _creation(pid):\n    api=ctypes.WinDLL("kernel32",use_last_error=True);api.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];api.OpenProcess.restype=w.HANDLE;api.GetProcessTimes.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p];api.GetProcessTimes.restype=w.BOOL;api.CloseHandle.argtypes=[w.HANDLE];api.CloseHandle.restype=w.BOOL\n    h=api.OpenProcess(0x1000,False,pid)\n    if not h: raise ctypes.WinError(ctypes.get_last_error())\n    try:\n        a=w.FILETIME();b=w.FILETIME();c=w.FILETIME();d=w.FILETIME()\n        if not api.GetProcessTimes(h,ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)): raise ctypes.WinError(ctypes.get_last_error())\n        return str((int(a.dwHighDateTime)<<32)|int(a.dwLowDateTime))\n    finally: api.CloseHandle(h)\n\ndef ready(root,role):\n    with (Path(root)/(role+".ready")).open("x",encoding="utf-8") as f:f.write("ready\\n")\n\ndef mark(root,role):\n    pid=os.getpid();ppid=os.getppid();row={"pid":pid,"creation":_creation(pid),"ppid":ppid,"parent_creation":_creation(ppid)}\n    with (Path(root)/(role+".json")).open("x",encoding="utf-8") as f: json.dump(row,f,sort_keys=True);f.flush();os.fsync(f.fileno())\n    ready(root,role)\n'''
    root_literal = repr(str(root))
    if control_topology:
        scripts = {
        'distributed_worker.py': 'import subprocess,sys\nfrom helper import mark\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"root");raise SystemExit(subprocess.Popen([sys.executable,"-B",str(r/"relay.py")]).wait())\n',
        'relay.py': 'import subprocess,sys\nfrom helper import mark\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"relay");raise SystemExit(subprocess.Popen([sys.executable,"-B",str(r/"launcher.py")]).wait())\n',
        'launcher.py': 'import subprocess,sys\nfrom helper import mark\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"launcher");raise SystemExit(subprocess.Popen([sys.executable,"-B",str(r/"child.py")]).wait())\n',
        'child.py': 'import threading\nfrom helper import mark\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"child");threading.Event().wait(60)\n',
        }
    else:
        # Root is recorded by the coordinator from the Session Popen handle.
        # Relay is this script's actual interpreter; launcher is the relay's
        # Popen identity and child records its own interpreter identity.
        scripts = {
            'distributed_worker.py': 'import os,subprocess,sys\nfrom helper import mark, _creation, ready\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"relay");p=subprocess.Popen([sys.executable,"-B",str(r/"actual.py")]);row={"pid":p.pid,"creation":_creation(p.pid),"ppid":os.getpid(),"parent_creation":_creation(os.getpid())};f=(r/"launcher.json").open("x",encoding="utf-8");__import__("json").dump(row,f,sort_keys=True);f.flush();os.fsync(f.fileno());f.close();ready(r,"launcher");raise SystemExit(p.wait())\n',
            'actual.py': 'import threading\nfrom helper import mark\nfrom pathlib import Path\nr=Path('+root_literal+');mark(r,"child");threading.Event().wait(60)\n',
        }
    (root/'helper.py').write_text(helper, encoding='utf-8', newline='\n')
    for name, text in scripts.items():
        (root/name).write_text(text, encoding='utf-8', newline='\n')
    (root/'distributed_retrieval.py').write_text('# MP1 fixture path only\n', encoding='utf-8', newline='\n')


def _load_bridge(source):
    scripts = source/'memory-integrity'/'scripts'
    _require((scripts/'knowledge_bridge'/'distributed_retrieval.py').is_file(), 'E_MP_SOURCE')
    for name, cached in tuple(sys.modules.items()):
        if name == 'knowledge_bridge' or name.startswith('knowledge_bridge.'):
            _require(getattr(cached, '__file__', None) is not None and
                     _inside(Path(cached.__file__), scripts), 'E_MP_SOURCE_IMPORT')
    sys.path.insert(0, str(scripts))
    try:
        module = importlib.import_module('knowledge_bridge.distributed_retrieval')
    finally:
        sys.path.pop(0)
    _require(_inside(Path(module.__file__), scripts), 'E_MP_SOURCE_IMPORT')
    return module


def _write_json_exclusive(path, value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8') + b'\n'
    _require(len(raw) <= MAX_RECORD_BYTES, 'E_MP_RECORD_LIMIT')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def _error_text(error):
    pieces = []
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error)); pieces.append(type(error).__name__ + ': ' + str(error))
        pieces.extend('NOTE: ' + str(note) for note in getattr(error, '__notes__', ()))
        error = error.__cause__ or error.__context__
    return pieces


def _close_streams_after_writer(session, errors):
    """Do not flush/close buffered stdin while its writer can still be blocked."""
    if session is None:
        return
    stdin = getattr(getattr(session, 'process', None), 'stdin', None)
    if stdin is not None and not stdin.closed:
        raw = getattr(stdin, 'raw', None)
        if raw is not None and not raw.closed:
            try:
                raw.close()
            except Exception as error:
                errors.append('raw stdin close: '+repr(error))
        try:
            stdin.close()
        except Exception as error:
            errors.append('buffered stdin close: '+repr(error))
    for stream in (getattr(session, 'reader', None), getattr(session, 'output', None), getattr(session, 'errors', None)):
        if stream is not None and not stream.closed:
            try:
                stream.close()
            except Exception as error:
                errors.append('stream close: '+repr(error))


def _emergency_cleanup(api, handles, writer, writer_handle, session, event, *, cancel_first=False):
    """Post-measurement only, limited to previously birth-bound fixture roles."""
    value = {'attempted': True, 'completed': False, 'errors': [], 'termination': [],
             'cancel_synchronous_io': None, 'writer_joined': writer is None, 'roles_signalled': {},
             'streams_closed': False, 'root_reaped': False, 'job_closed': False}
    until = time.monotonic() + 5
    def cancel_writer():
        if writer is not None and writer.is_alive() and writer_handle is not None:
            try:
                ok = bool(api.CancelSynchronousIo(writer_handle)); code = ctypes.get_last_error()
                value['cancel_synchronous_io'] = {'ok':ok, 'last_error':(0 if ok else code)}
                if not ok and code != ERROR_NOT_FOUND:
                    value['errors'].append('CancelSynchronousIo: '+str(code))
            except Exception as error:
                value['errors'].append('CancelSynchronousIo: '+repr(error))
    if cancel_first:
        cancel_writer()
    for role in reversed(ROLES):
        handle = handles.get(role)
        if handle is None:
            value['errors'].append('missing pinned role: '+role)
            continue
        try:
            if not _signalled(api, handle):
                ok = bool(api.TerminateProcess(handle, 1)); code = ctypes.get_last_error()
                value['termination'].append({'role':role, 'ok':ok, 'last_error':(0 if ok else code)})
                if not ok:
                    value['errors'].append('TerminateProcess '+role+': '+str(code))
        except Exception as error:
            value['errors'].append('TerminateProcess '+role+': '+repr(error))
    if not cancel_first:
        cancel_writer()
    for role in ROLES:
        handle = handles.get(role)
        if handle is None:
            continue
        state = api.WaitForSingleObject(handle, max(0, int((until-time.monotonic())*1000)))
        value['roles_signalled'][role] = state == WAIT_OBJECT_0
        if state != WAIT_OBJECT_0:
            value['errors'].append('role still alive: '+role)
    if writer is not None:
        writer.join(timeout=max(0, until-time.monotonic()))
        value['writer_joined'] = not writer.is_alive()
        if writer.is_alive():
            value['errors'].append('writer still alive')
    if value['writer_joined'] and (writer is None or writer_handle is not None):
        prior = len(value['errors'])
        _close_streams_after_writer(session, value['errors'])
        value['streams_closed'] = len(value['errors']) == prior
    elif writer is not None:
        value['errors'].append('live writer was not birth-bound')
    process = getattr(session, 'process', None)
    if process is not None:
        try:
            process.wait(timeout=max(0, until-time.monotonic()))
            value['root_reaped'] = process.poll() is not None
        except Exception as error:
            value['errors'].append('root wait: '+repr(error))
    tree = getattr(session, '_tree', None)
    if tree is None or not getattr(tree, 'handle', None):
        value['job_closed'] = True
    else:
        try:
            tree.release()
            value['job_closed'] = not getattr(tree, 'handle', None)
        except Exception as error:
            value['errors'].append('job release: '+repr(error))
    value['completed'] = (not value['errors'] and value['writer_joined'] and value['streams_closed'] and
                          value['root_reaped'] and value['job_closed'] and
                          all(value['roles_signalled'].get(role) for role in ROLES))
    event('emergency-finished', emergency=value)
    return value


def _close_owned_handles(api, owned_handles, event, *, force_error=False):
    """Close each locally opened native handle exactly once before a success receipt."""
    result = {'completed': False, 'errors': []}
    for role, handle in tuple(owned_handles.items()):
        if handle is None:
            continue
        try:
            if not api.CloseHandle(handle):
                result['errors'].append('CloseHandle '+role+': '+str(ctypes.get_last_error()))
        except Exception as error:
            result['errors'].append('CloseHandle '+role+': '+repr(error))
        finally:
            owned_handles[role] = None
    result['completed'] = not result['errors']
    if force_error:
        result['errors'].append('E_MP_CONTROL_HANDLE_CLOSE_FAILURE')
        result['completed'] = False
    event('handle-cleanup', handle_cleanup=result)
    return result


def run_probe(source: Path, output: Path, *, control_topology=False, _fault_after_roles_pinned=False,
              _force_stop_failure=False, _force_nonvalue_after_request=False,
              _force_handle_cleanup_error=False):
    """Run one new fixture using the running interpreter; no caller selects another runtime."""
    source, output = Path(source).resolve(strict=True), Path(output).absolute()
    _require(not output.exists() and not os.path.lexists(output), 'E_MP_OUTPUT_EXISTS')
    # The sealed coordinator's new retained proof directory is the sole permitted
    # in-tree destination.  A source/module path can never become probe output.
    if _inside(output, source):
        _require(_inside(output, source/'.github'/'run-artifacts'), 'E_MP_OUTPUT_IN_SOURCE')
    _ordinary(output.parent)
    output.mkdir()
    _ordinary(output)
    incremental = output/'Incremental.jsonl'
    with incremental.open('xb') as stream:
        stream.write(b'')
    events = []
    def event(stage, **value):
        row = {'stage': stage, 'utc_ns': time.time_ns(), **value}
        raw = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('utf-8') + b'\n'
        _require(len(raw) <= 65536 and incremental.stat().st_size + len(raw) <= MAX_RECORD_BYTES,
                 'E_MP_INCREMENTAL_LIMIT')
        with incremental.open('ab') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        events.append(row)

    api = _kernel(); handles = {}; owned_handles = {}; writer_handle = None; session = None; writer = None
    observation_errors = []; stop_error = None; before = None
    result = None; emergency = None; handle_cleanup = None
    try:
        fixture = output/'fixture'; fixture.mkdir(); _ordinary(fixture)
        _chain_fixture(fixture, control_topology=control_topology)
        topology = ('CONTROLLER_C314_SYNTHETIC_FOUR_PROCESS_NOT_SELECTED_RUNTIME_PROOF' if control_topology
                    else 'SELECTED_VENV_ORIGINAL_RELAY_CHILD')
        event('fixture-created', topology=topology)
        d = _load_bridge(source)
        session_root = output/'session-retained'; session_root.mkdir(); errors_root = output/'errors-retained'; errors_root.mkdir()
        original_dir, original_file, original_file_name = d.tempfile.TemporaryDirectory, d.tempfile.TemporaryFile, None
        class RetainedDirectory:
            def __init__(self, *args, **kwargs): self.name = str(session_root)
            def cleanup(self): return None
        def retained_file(*args, **kwargs):
            nonlocal original_file_name
            original_file_name = errors_root/'worker-errors.bin'
            return original_file_name.open('x+b')
        old_file = d.__file__
        d.tempfile.TemporaryDirectory, d.tempfile.TemporaryFile = RetainedDirectory, retained_file
        try:
            d.__file__ = str(fixture/'distributed_retrieval.py')
            session = d._Session(Path(sys.executable), 0, 'a' * 64, time.monotonic() + 120)
        finally:
            d.__file__ = old_file
            d.tempfile.TemporaryDirectory, d.tempfile.TemporaryFile = original_dir, original_file
        _require(session._tree is not None, 'E_MP_WINDOWS_TREE_REQUIRED')
        event('session-created', root_pid=session.process.pid)
        if not control_topology:
            _write_json_exclusive(fixture/'root.json', {'pid':session.process.pid,
                                  'creation':_creation(api, session.process._handle), 'ppid':0, 'parent_creation':'0'})
            _write_json_exclusive(fixture/'root.ready', {'ready':True})
        # Session already owns the unchanged 120-second deadline.  The sealed
        # outer diagnostic watchdog remains the shorter execution boundary.
        deadline = session.deadline
        marker_rows = {}
        while len(marker_rows) != len(ROLES):
            for role in ROLES:
                marker = fixture/(role+'.json')
                if marker.exists() and (fixture/(role+'.ready')).is_file() and role not in marker_rows:
                    _ordinary(marker)
                    marker_rows[role] = json.loads(marker.read_text(encoding='utf-8'))
            if len(marker_rows) == len(ROLES): break
            if session.process.poll() is not None or time.monotonic() >= deadline:
                raise ValueError('E_MP_MARKERS_NOT_READY')
            threading.Event().wait(.005)
        for role, marker in marker_rows.items():
            _require(set(marker) == {'pid','creation','ppid','parent_creation'} and
                     type(marker['pid']) is int and marker['pid'] > 0 and marker['creation'].isdigit() and
                     type(marker['ppid']) is int and marker['ppid'] >= 0 and marker['parent_creation'].isdigit(),
                     'E_MP_MARKER')
            handle = _adopt_role_handle(api, role, marker,
                                        session.process._handle if role == 'root' and not control_topology else None,
                                        owned_handles)
            handles[role] = handle
        for number, role in enumerate(ROLES[1:], 1):
            parent = marker_rows[ROLES[number - 1]]; current = marker_rows[role]
            _require(current['ppid'] == parent['pid'] and current['parent_creation'] == parent['creation'],
                     'E_MP_CHAIN')
        if not control_topology:
            _require(len({marker_rows[role]['pid'] for role in ROLES}) == len(ROLES),
                     'E_MP_DIRECT_RUNTIME_TOPOLOGY_UNSUPPORTED')
        event('roles-pinned', pids={role: marker_rows[role]['pid'] for role in ROLES})
        if _fault_after_roles_pinned:
            raise RuntimeError('E_MP_CONTROL_FAULT_AFTER_ROLES_PINNED')

        def snapshot(label, *, require_consistent=True):
            membership = _job_members(api, session._tree.handle); accounting = _accounting(api, session._tree.handle)
            roles = {}
            for role in ROLES:
                row = dict(marker_rows[role]); row['in_job'] = _in_job(api, handles[role], session._tree.handle)
                row['signalled'] = _signalled(api, handles[role]); roles[role] = row
            value = {**membership, **accounting, 'roles': roles}
            if require_consistent:
                validate_snapshot(value)
            event(label, membership={'assigned':value['assigned'],'listed':value['listed'],
                                     'members':value['members'],'total':value['total'],'active':value['active']},
                  roles={role:{'in_job':value['roles'][role]['in_job'],'signalled':value['roles'][role]['signalled']}
                         for role in ROLES})
            return value
        before = snapshot('before-write')

        try:
            session.deadline = time.monotonic() + .1
            session.request('fit', {'text': 'x' * 1000000})
            observation_errors.append('E_MP_REQUEST_UNEXPECTED_RETURN')
        except ValueError as error:
            event('request-ended', error=_error_text(error))
        if _force_nonvalue_after_request:
            raise RuntimeError('E_MP_CONTROL_NONVALUE_AFTER_WRITER_START')
        writer = session.writer
        writer_handle, writer_record = _pin_writer(api, writer, owned_handles)
        event('writer-pinned', **writer_record)

        original_terminate = session._tree.api.TerminateJobObject
        def observed_terminate(handle, code):
            incoming = ctypes.get_last_error()
            try:
                try:
                    snapshot('before-terminate')
                except Exception as error:
                    observation_errors.append('before-terminate: '+repr(error))
            finally:
                ctypes.set_last_error(incoming)
            value = original_terminate(handle, code); error_code = ctypes.get_last_error()
            event('terminate-returned', value=bool(value), last_error=(0 if value else error_code))
            try:
                    # Post-termination accounting can transiently show historical
                    # assigned count with an empty live PID list. Retain it; only
                    # the pre-write snapshot is the classification contract.
                    snapshot('after-terminate', require_consistent=False)
            except Exception as error:
                observation_errors.append('after-terminate: '+repr(error))
                event('after-terminate-observation-error', error=repr(error))
            finally:
                ctypes.set_last_error(error_code)
            return value
        session._tree.api.TerminateJobObject = observed_terminate
        try:
            if _force_stop_failure:
                raise RuntimeError('E_MP_CONTROL_STOP_FAILURE')
            session.stop()
        except BaseException as error:
            stop_error = _error_text(error); event('stop-failed', error=stop_error)
        after = {role: _signalled(api, handles[role]) for role in ROLES}
        writer_alive = bool(writer.is_alive())
        event('after-stop', signalled=after, writer_alive=writer_alive, stop_error=stop_error)

        emergency = _emergency_cleanup(api, handles, writer, writer_handle, session, event,
                                       cancel_first=_force_stop_failure)
        handle_cleanup = _close_owned_handles(api, owned_handles, event, force_error=_force_handle_cleanup_error)
        _require(handle_cleanup['completed'], 'E_MP_HANDLE_CLEANUP')
        result = {'scope': 'MP1_MEMBERSHIP_ONLY_NOT_FIX',
                  'fixture_topology': topology,
                  'before': before, 'after': after, 'writer_alive_after_stop': writer_alive,
                  'stop_error': stop_error, 'observation_errors': observation_errors,
                  'emergency_cleanup': emergency, 'stage_complete': False, 'gate1_complete': False,
                  'release_ready': False, 'installed': False, 'fix_validated': False,
                  'root_cause_confirmed': False, 'producer_authentication': False,
                  'handle_cleanup': handle_cleanup}
        result['status'] = classify(before, after, writer_alive, stop_error, observation_errors=observation_errors)
        _write_json_exclusive(output/'Probe.json', result)
        return result
    except BaseException as primary:
        actual_writer = getattr(session, 'writer', None) if session is not None else None
        if writer is None:
            writer = actual_writer
        if writer is not None and writer.is_alive() and writer_handle is None:
            try:
                writer_handle, writer_record = _pin_writer(api, writer, owned_handles)
                event('writer-pinned-during-failure', **writer_record)
            except Exception as pin_error:
                primary.add_note('E_MP_WRITER_PIN: '+repr(pin_error))
        if emergency is None:
            try:
                emergency = _emergency_cleanup(api, handles, writer, writer_handle, session, event)
            except Exception as cleanup:
                primary.add_note('E_MP_EMERGENCY: '+repr(cleanup))
        if emergency is not None and not emergency.get('completed'):
            primary.add_note('E_MP_EMERGENCY_INCOMPLETE: '+repr(emergency))
        if handle_cleanup is None:
            try:
                handle_cleanup = _close_owned_handles(api, owned_handles, event)
            except Exception as cleanup:
                primary.add_note('E_MP_HANDLE_CLEANUP: '+repr(cleanup))
        if handle_cleanup is not None and not handle_cleanup.get('completed'):
            primary.add_note('E_MP_HANDLE_CLEANUP_INCOMPLETE: '+repr(handle_cleanup))
        try:
            _write_json_exclusive(output/'Probe-error.json', {
                'scope':'MP1_MEMBERSHIP_ONLY_NOT_FIX', 'error':_error_text(primary),
                'emergency_cleanup':emergency, 'handle_cleanup':handle_cleanup,
                'stage_complete':False, 'gate1_complete':False,
                'release_ready':False, 'installed':False, 'root_cause_confirmed':False,
                'fix_validated':False, 'producer_authentication':False})
        except Exception as receipt_error:
            primary.add_note('E_MP_ERROR_RECEIPT: '+repr(receipt_error))
        raise
    finally:
        # Success and failure paths close owned handles before writing their final
        # receipt.  Only a catastrophic pre-receipt interruption can reach here.
        if any(handle is not None for handle in owned_handles.values()):
            _close_owned_handles(api, owned_handles, event)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        value = run_probe(args.source, args.output)
    except BaseException as error:
        print(json.dumps({'status':'MP1_PROBE_INCOMPLETE','error':_error_text(error)}))
        return 1
    print(json.dumps({'status':value['status'],'probe':str(args.output/'Probe.json'),
                      'stage_complete':False,'gate1_complete':False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
