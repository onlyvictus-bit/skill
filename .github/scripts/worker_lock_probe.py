"""Query-only Windows file-user observation for exact NEW owned files.

Restart Manager creates transient OS session bookkeeping. Never calls shutdown,
restart, elevation, ACL/config changes or unrelated process termination.
"""
import json
import os
from pathlib import Path


def validate_target(path, owned_root):
    from worker_diagnostic_events import ordinary
    path, owned_root = Path(path), Path(owned_root)
    if not path.is_absolute() or not owned_root.is_absolute() or path == owned_root or not path.is_relative_to(owned_root):
        raise ValueError('E_LOCK_TARGET_SCOPE')
    ordinary(owned_root)
    ordinary(path)
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError('E_LOCK_TARGET_FILE')
    return path


def result(holders, api_status=0):
    return {'status': 'OBSERVED' if holders and api_status == 0 else 'UNKNOWN',
            'holders': holders, 'api_status': api_status, 'producer_authentication': False,
            'cause_proven': False, 'fix_validated': False, 'gate1_complete': False}


def query_file_users(path, owned_root):
    path = validate_target(path, owned_root)
    if os.name != 'nt':
        return result([], 'WINDOWS_REQUIRED')
    import ctypes
    from ctypes import wintypes as w
    class Unique(ctypes.Structure):
        _fields_ = [('pid', w.DWORD), ('start', w.FILETIME)]
    class Info(ctypes.Structure):
        _fields_ = [('process', Unique), ('app', w.WCHAR * 256), ('service', w.WCHAR * 64),
                    ('type', ctypes.c_int), ('status', w.ULONG), ('session', w.DWORD), ('restartable', w.BOOL)]
    rm = ctypes.WinDLL('Rstrtmgr')
    rm.RmStartSession.argtypes = [ctypes.POINTER(w.DWORD), w.DWORD, w.LPWSTR]
    rm.RmStartSession.restype = w.DWORD
    rm.RmRegisterResources.argtypes = [w.DWORD, w.UINT, ctypes.POINTER(w.LPCWSTR), w.UINT, ctypes.POINTER(Unique), w.UINT, ctypes.POINTER(w.LPCWSTR)]
    rm.RmRegisterResources.restype = w.DWORD
    rm.RmGetList.argtypes = [w.DWORD, ctypes.POINTER(w.UINT), ctypes.POINTER(w.UINT), ctypes.POINTER(Info), ctypes.POINTER(w.DWORD)]
    rm.RmGetList.restype = w.DWORD
    rm.RmEndSession.argtypes = [w.DWORD]
    rm.RmEndSession.restype = w.DWORD
    session, key = w.DWORD(), ctypes.create_unicode_buffer(33)
    status = rm.RmStartSession(ctypes.byref(session), 0, key)
    if status:
        return result([], int(status))
    observation = result([], 'UNFINISHED')
    try:
        filenames = (w.LPCWSTR * 1)(str(path))
        status = rm.RmRegisterResources(session, 1, filenames, 0, None, 0, None)
        if status:
            observation = result([], int(status))
        else:
            needed, count, reasons = w.UINT(), w.UINT(256), w.DWORD()
            values = (Info * 256)()
            status = rm.RmGetList(session, ctypes.byref(needed), ctypes.byref(count), values, ctypes.byref(reasons))
            # Buffer overflow is UNKNOWN, not a loop that changes the experiment.
            observation = result([{'pid': int(item.process.pid),
                                   'creation': str((item.process.start.dwHighDateTime << 32) | item.process.start.dwLowDateTime)}
                                  for item in values[:count.value]] if status == 0 else [], int(status))
    finally:
        ended = int(rm.RmEndSession(session))
        if ended:
            observation = result([], 'END_SESSION:' + str(ended))
    return observation


def holder(path):
    """Owned fixture only: READY, bounded parent lifetime, RELEASE, CloseHandle."""
    import ctypes
    from ctypes import wintypes as w
    from worker_diagnostic_events import process_identity
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p,
                                  w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.CloseHandle.restype = w.BOOL
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        print(json.dumps({'state': 'READY', 'pid': os.getpid(), 'creation': process_identity(os.getpid())}), flush=True)
        import sys
        if sys.stdin.buffer.read(1) != b'R':
            raise ValueError('E_LOCK_CONTROL_RELEASE')
    finally:
        if not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def controls(root):
    """Two fresh arms; never retries the intentional failed cleanup."""
    import queue
    import shutil
    import subprocess
    import sys
    import threading
    from worker_diagnostic_events import ordinary
    if os.name != 'nt':
        raise ValueError('E_LOCK_CONTROL_WINDOWS_REQUIRED')
    root = Path(root)
    ordinary(root.parent)
    root.mkdir()
    rows = []
    for arm in ('locked', 'released'):
        folder = root / arm; folder.mkdir()
        output = folder / 'output'
        with output.open('xb') as stream:
            stream.write(b'known-owner-control-v1')
        process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).absolute()), '--holder', str(output)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ready_queue = queue.Queue(maxsize=1)
        def read_ready():
            try:
                ready_queue.put(process.stdout.readline(1024))
            except BaseException as error:
                ready_queue.put(error)
        reader = threading.Thread(target=read_ready, daemon=True)
        reader.start()
        release_sent = False
        row = {'arm': arm, 'cleanup_calls': 0, 'expected_native_failure': False}
        try:
            raw = ready_queue.get(timeout=5)
            if not isinstance(raw, bytes):
                raise ValueError('E_LOCK_CONTROL_READY_READ')
            ready = json.loads(raw)
            if ready.get('state') != 'READY' or ready['pid'] != process.pid or ready['creation'].startswith('UNKNOWN'):
                raise ValueError('E_LOCK_CONTROL_READY_IDENTITY')
            row['fixture'] = ready
            if arm == 'locked':
                row['users'] = query_file_users(output, root)
                if {'pid': process.pid, 'creation': ready['creation']} not in row['users']['holders']:
                    raise ValueError('E_LOCK_CONTROL_HOLDER_UNOBSERVED')
                try:
                    row['cleanup_calls'] += 1
                    shutil.rmtree(folder)
                except OSError as error:
                    if getattr(error, 'winerror', None) != 32 or Path(error.filename) != output:
                        raise
                    row.update(expected_native_failure=True, winerror=32, filename=str(output))
                if not row['expected_native_failure'] or not output.is_file():
                    raise ValueError('E_LOCK_CONTROL_FAILED_ARM_NOT_RETAINED')
            process.stdin.write(b'R'); process.stdin.flush(); process.stdin.close()
            release_sent = True
            process.wait(timeout=5)
            if process.returncode != 0:
                raise ValueError('E_LOCK_CONTROL_FIXTURE_EXIT')
            if arm == 'released':
                row['cleanup_calls'] += 1
                shutil.rmtree(folder)
                if folder.exists():
                    raise ValueError('E_LOCK_CONTROL_POSITIVE_CLEANUP')
            rows.append(row)
        finally:
            if process.poll() is None:
                if not release_sent:
                    try:
                        process.stdin.write(b'R'); process.stdin.flush(); process.stdin.close()
                    except (OSError, ValueError):
                        pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
            reader.join(timeout=2)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
            if reader.is_alive():
                raise ValueError('E_LOCK_CONTROL_READER_ALIVE')
    return {'status': 'KNOWN_HOLDER_AND_RELEASED_CONTROL_OBSERVED', 'arms': rows,
            'cause_proven': False, 'fix_validated': False, 'gate1_complete': False}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--path', type=Path)
    p.add_argument('--owned-root', type=Path)
    p.add_argument('--control-root', type=Path)
    p.add_argument('--holder', type=Path)
    a = p.parse_args()
    if a.holder is not None:
        if a.path or a.owned_root or a.control_root:
            p.error('holder only')
        holder(a.holder)
    elif a.control_root is not None:
        if a.path or a.owned_root:
            p.error('control-root only')
        print(json.dumps(controls(a.control_root)))
    else:
        if a.path is None or a.owned_root is None:
            p.error('exact file and owned root required')
        print(json.dumps(query_file_users(a.path, a.owned_root)))
