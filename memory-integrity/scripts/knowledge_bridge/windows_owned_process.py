"""Fail-closed ownership of a direct, current-image Windows process Job.

Independent from the immutable ``windows_job`` control: its cumulative/live
comparison is not used here.  Cumulative accounting is checked only against an
identity-pinned lifetime ledger; a missing notification or unpinnable member is
an explicit proof gap.
"""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import time

_CREATE_SUSPENDED, _CREATE_NO_WINDOW = 4, 0x08000000
_SYNC_QUERY, _THREAD_QUERY_RESUME, _TH32CS_SNAPTHREAD = 0x101000, 0x0802, 4
_INVALID_HANDLE, _WAIT_OBJECT_0, _WAIT_TIMEOUT = ctypes.c_void_p(-1).value, 0, 258
_ERROR_MORE_DATA, _ERROR_NO_MORE_FILES = 234, 18
_KILL_ON_CLOSE, _ACCOUNTING, _PID_LIST, _ASSOCIATE_PORT, _EXTENDED = 0x2000, 1, 3, 7, 9
_NEW_PROCESS, _EXIT_PROCESS = 6, 7
_DUPLICATE_SAME_ACCESS = 2
_BOOTSTRAP_FAILURE_BYTES, _BOOTSTRAP_DETAIL_CHARS, _BOOTSTRAP_FIELD_CHARS = 4096, 512, 2048
_IDENTITY_FIELDS = ("image", "sys_executable", "prefix", "base_prefix", "base_executable", "launcher")


def _bootstrap_json(path, role):
    with path.open('rb') as stream:
        raw = stream.read(_BOOTSTRAP_FAILURE_BYTES + 1)
    if len(raw) > _BOOTSTRAP_FAILURE_BYTES:
        raise ValueError('E_OWNED_BOOTSTRAP_' + role + '_SIZE')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('E_OWNED_BOOTSTRAP_DUPLICATE_KEY')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique)


class _BasicLimit(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("flags", w.DWORD),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", w.DWORD),
                ("f", ctypes.c_size_t), ("g", w.DWORD), ("h", w.DWORD)]


class _Extended(ctypes.Structure):
    _fields_ = [("basic", _BasicLimit), ("io", ctypes.c_uint64 * 6),
                ("a", ctypes.c_size_t), ("b", ctypes.c_size_t),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t)]


class _Accounting(ctypes.Structure):
    _fields_ = [("times", ctypes.c_int64 * 4), ("faults", w.DWORD),
                ("total", w.DWORD), ("active", w.DWORD), ("terminated", w.DWORD)]


class _Port(ctypes.Structure):
    _fields_ = [("key", ctypes.c_void_p), ("port", w.HANDLE)]


class _Thread(ctypes.Structure):
    _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("ident", w.DWORD),
                ("owner", w.DWORD), ("base", w.LONG), ("delta", w.LONG), ("flags", w.DWORD)]


class _FileTime(ctypes.Structure):
    _fields_ = [("low", w.DWORD), ("high", w.DWORD)]


def _norm(value): return os.path.normcase(os.path.abspath(os.fspath(value)))
def _left(until): return max(0, until - time.monotonic())


def _native_error(operation):
    error = ctypes.WinError(ctypes.get_last_error())
    error.add_note('E_OWNED_NATIVE_OPERATION: ' + operation)
    return error


class _Job:
    def __init__(self):
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        spec = {"CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
         "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
         "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
         "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
          "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL), "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
          "GetCurrentProcess": ([], w.HANDLE), "DuplicateHandle": ([w.HANDLE, w.HANDLE, w.HANDLE, ctypes.POINTER(w.HANDLE), w.DWORD, w.BOOL, w.DWORD], w.BOOL),
         "IsProcessInJob": ([w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
         "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD), "CloseHandle": ([w.HANDLE], w.BOOL),
         "CreateIoCompletionPort": ([w.HANDLE, w.HANDLE, ctypes.c_size_t, w.DWORD], w.HANDLE),
         "GetQueuedCompletionStatus": ([w.HANDLE, ctypes.POINTER(w.DWORD), ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_void_p), w.DWORD], w.BOOL),
         "CreateToolhelp32Snapshot": ([w.DWORD, w.DWORD], w.HANDLE), "Thread32First": ([w.HANDLE, ctypes.POINTER(_Thread)], w.BOOL),
         "Thread32Next": ([w.HANDLE, ctypes.POINTER(_Thread)], w.BOOL), "OpenThread": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
         "GetProcessIdOfThread": ([w.HANDLE], w.DWORD), "ResumeThread": ([w.HANDLE], w.DWORD),
         "QueryFullProcessImageNameW": ([w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL),
         "GetProcessTimes": ([w.HANDLE, ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime)], w.BOOL)}
        for name, (args, result) in spec.items():
            fun = getattr(self.api, name); fun.argtypes, fun.restype = args, result
        self.handle = self.port = None
        self._handle_debt = []
        self.handle = self.check(self.api.CreateJobObjectW(None, None))
        try:
            limits = _Extended(); limits.basic.flags = _KILL_ON_CLOSE
            self.check(self.api.SetInformationJobObject(self.handle, _EXTENDED, ctypes.byref(limits), ctypes.sizeof(limits)))
            self.port = self.check(self.api.CreateIoCompletionPort(w.HANDLE(_INVALID_HANDLE), None, 1, 1))
            info = _Port(ctypes.c_void_p(1), self.port)
            self.check(self.api.SetInformationJobObject(self.handle, _ASSOCIATE_PORT, ctypes.byref(info), ctypes.sizeof(info)))
        except BaseException as original:
            try: self.close()
            except Exception as cleanup:
                original.add_note('E_OWNED_JOB_SETUP_CLEANUP: ' + repr(cleanup) + '; notes=' + repr(getattr(cleanup, '__notes__', [])))
                original.owned_job_debt = self
            raise

    @staticmethod
    def check(value):
        if not value: raise ctypes.WinError(ctypes.get_last_error())
        return value

    def accounting(self):
        info = _Accounting()
        if not self.api.QueryInformationJobObject(self.handle, _ACCOUNTING, ctypes.byref(info), ctypes.sizeof(info), None):
            raise _native_error('QueryInformationJobObject(accounting)')
        return info

    def pids(self):
        count = 8
        for _ in range(5):
            size = 8 + ctypes.sizeof(ctypes.c_size_t) * count; raw = ctypes.create_string_buffer(size)
            ok = self.api.QueryInformationJobObject(self.handle, _PID_LIST, raw, size, None)
            assigned, listed = w.DWORD.from_buffer(raw, 0).value, w.DWORD.from_buffer(raw, 4).value
            if not ok and ctypes.get_last_error() != _ERROR_MORE_DATA: raise _native_error('QueryInformationJobObject(pids)')
            if ok and assigned == listed:
                return [int(item) for item in (ctypes.c_size_t * listed).from_buffer(raw, 8)], assigned
            count = max(count * 2, assigned + 1)
        raise ValueError("E_OWNED_PID_LIST_CHURN")

    def resume(self, process):
        snap = self.api.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        if snap == _INVALID_HANDLE: raise ctypes.WinError(ctypes.get_last_error())
        thread = None
        resumed = False
        try:
            entry = _Thread(); entry.size = ctypes.sizeof(entry); self.check(self.api.Thread32First(snap, ctypes.byref(entry)))
            found = []
            while True:
                if entry.owner == process.pid: found.append(entry.ident)
                if not self.api.Thread32Next(snap, ctypes.byref(entry)):
                    if ctypes.get_last_error() != _ERROR_NO_MORE_FILES: raise ctypes.WinError(ctypes.get_last_error())
                    break
            if len(found) != 1: raise ValueError("E_OWNED_SUSPENDED_THREAD")
            thread = self.check(self.api.OpenThread(_THREAD_QUERY_RESUME, False, found[0]))
            if self.api.GetProcessIdOfThread(thread) != process.pid: raise ValueError("E_OWNED_THREAD_OWNER")
            previous = self.api.ResumeThread(thread)
            resumed = previous in (0, 1)
            if previous != 1: raise ValueError("E_OWNED_THREAD_RESUME")
        finally:
            original = sys.exception()
            if resumed and original is not None:
                original.owned_resume_started = True
            try:
                self.close_handles((thread, snap), original)
            except BaseException as error:
                if resumed: error.owned_resume_started = True
                raise

    def duplicate_popen_handle(self, source):
        """Take one owned same-process duplicate of Popen's direct root handle."""
        current, result = self.api.GetCurrentProcess(), w.HANDLE()
        self.check(self.api.DuplicateHandle(current, w.HANDLE(source), current,
                                            ctypes.byref(result), 0, False,
                                            _DUPLICATE_SAME_ACCESS))
        return result

    def close_handles(self, handles, original=None):
        failures = []
        for handle in handles:
            if handle:
                try: self.check(self.api.CloseHandle(handle))
                except Exception as error:
                    if not hasattr(self, "_handle_debt"): self._handle_debt = []
                    if handle not in self._handle_debt: self._handle_debt.append(handle)
                    failures.append((handle, error))
        if failures:
            primary = original if original is not None else failures[0][1]
            for _handle, error in failures:
                primary.add_note('E_OWNED_HANDLE_CLOSE: ' + repr(error))
                primary.add_note('E_OWNED_NATIVE_OPERATION: CloseHandle: ' + repr(error))
            if original is None: raise primary

    def close(self):
        first = None
        debts, self._handle_debt = tuple(getattr(self, "_handle_debt", [])), []
        for handle in debts:
            try: self.check(self.api.CloseHandle(handle))
            except Exception as error:
                self._handle_debt.append(handle)
                if first is None: first = error
                else: first.add_note('E_OWNED_HANDLE_CLOSE: ' + repr(error))
        for field in ("port", "handle"):
            handle = getattr(self, field, None)
            if handle:
                try: self.check(self.api.CloseHandle(handle))
                except Exception as error:
                    if first is None: first = error
                    else: first.add_note('E_OWNED_JOB_CLOSE: ' + repr(error))
                else: setattr(self, field, None)
        if first: raise first


class CurrentImageOwner:
    def __init__(self, job, process, paths, expected):
        self._job, self.process, self._paths, self._expected = job, process, paths, expected
        self._records, self._by_pid, self._gap = {}, {}, None
        self.proof = {"startup": {"expected": expected, "paths": {k: str(v) for k, v in paths.items()},
                                  "state": "suspended-unassigned"},
                      "membership": {"events": [], "records": []}, "termination": {}, "released": False}

    def _fail(self, code): self._gap = self._gap or code; raise ValueError(self._gap)
    def _image(self, handle):
        size = w.DWORD(512)
        while True:
            text = ctypes.create_unicode_buffer(size.value); actual = w.DWORD(size.value)
            if self._job.api.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(actual)): return _norm(text.value)
            if ctypes.get_last_error() != 122: raise _native_error('QueryFullProcessImageNameW')
            size = w.DWORD(size.value * 2)
    def _created(self, handle):
        a = _FileTime(); b = _FileTime(); c = _FileTime(); d = _FileTime()
        if not self._job.api.GetProcessTimes(handle, ctypes.byref(a), ctypes.byref(b), ctypes.byref(c), ctypes.byref(d)):
            raise _native_error('GetProcessTimes')
        return (a.high << 32) | a.low
    def _record(self, pid, source, *, handle=None, owned_handle=True, handle_origin="OpenProcess"):
        if pid in self._by_pid: return self._by_pid[pid]
        opened = handle is None
        if opened:
            handle = self._job.api.OpenProcess(_SYNC_QUERY, False, pid)
            if not handle: self._fail("E_OWNED_LEDGER_UNPINNED")
            owned_handle, handle_origin = True, "OpenProcess"
        try:
            inside = w.BOOL()
            if not self._job.api.IsProcessInJob(handle, self._job.handle, ctypes.byref(inside)):
                raise _native_error('IsProcessInJob(record)')
            if not inside.value: self._fail('E_OWNED_MEMBER_OUTSIDE_JOB')
            created, image = self._created(handle), self._image(handle); key = (pid, created)
            if key in self._records: self._fail("E_OWNED_LEDGER_PID_REUSE")
            record = {"pid": pid, "created": created, "image": image, "handle": handle,
                      "source": source, "handle_owned": owned_handle, "handle_origin": handle_origin}
            self._records[key] = record; self._by_pid[pid] = record
            self.proof["membership"]["records"].append({k: record[k] for k in ("pid", "created", "image", "source", "handle_origin")})
            return record
        except BaseException as original:
            if owned_handle: self._job.close_handles((handle,), original)
            raise
    def assigned_root(self):
        """Pin the assigned suspended root before it can execute user code."""
        self.proof["startup"]["state"] = "assigned-not-resumed"
        duplicate = self._job.duplicate_popen_handle(self.process._handle)
        record = self._record(self.process.pid, "assigned-root", handle=duplicate,
                              owned_handle=True, handle_origin="popen-duplicate")
        if record["image"] != self._expected["image"]:
            self._fail("E_OWNED_ROOT_IMAGE")
        return record
    def resumed(self):
        self.proof["startup"]["state"] = "resumed"
    def _events(self, until):
        while True:
            message = w.DWORD(); key = ctypes.c_size_t(); value = ctypes.c_void_p()
            ok = self._job.api.GetQueuedCompletionStatus(self._job.port, ctypes.byref(message), ctypes.byref(key), ctypes.byref(value), 0)
            if not ok:
                if ctypes.get_last_error() == _WAIT_TIMEOUT: return
                raise _native_error('GetQueuedCompletionStatus')
            if _left(until) <= 0: raise TimeoutError('E_OWNED_OBSERVATION_DEADLINE')
            if key.value != 1: self._fail("E_OWNED_COMPLETION_PORT_KEY")
            pid = int(value.value or 0); self.proof["membership"]["events"].append({"message": int(message.value), "pid": pid})
            if message.value == _NEW_PROCESS:
                if not pid: self._fail("E_OWNED_NEW_PROCESS_NO_PID")
                self._record(pid, "completion-port")
            elif message.value == _EXIT_PROCESS and (not pid or pid not in self._by_pid): self._fail("E_OWNED_EXIT_UNKNOWN")
    def _observe(self, until):
        self._events(until); pids, assigned = self._job.pids()
        if assigned != len(pids): self._fail("E_OWNED_PID_LIST_INCOMPLETE")
        for pid in pids:
            if _left(until) <= 0: raise TimeoutError('E_OWNED_OBSERVATION_DEADLINE')
            record = self._record(pid, "pid-list"); inside = w.BOOL()
            if not self._job.api.IsProcessInJob(record["handle"], self._job.handle, ctypes.byref(inside)):
                raise _native_error('IsProcessInJob(observe)')
            if not inside.value: self._fail("E_OWNED_MEMBER_OUTSIDE_JOB")
        self._events(until); accounting = self.accounting()
        if accounting.total != len(self._records): self._fail("E_SHARD_TREE_UNOBSERVED_MEMBER")
        # These are separate native queries, not an atomic snapshot: an exit
        # may change active count after the PID-list read. _exits requires both
        # empty observations and every pinned native handle before proof.
        return pids, accounting
    def accounting(self):
        return self._job.accounting()
    def verify_bootstrap(self, until):
        while not self._paths["ready"].exists():
            if self._paths["failure"].exists():
                failure = _bootstrap_json(self._paths['failure'], 'FAILURE')
                if not isinstance(failure, dict) or set(failure) not in ({"token", "code", "detail"}, {"token", "code", "detail", "identity"}):
                    raise ValueError("E_OWNED_BOOTSTRAP_FAILURE_SHAPE")
                if failure.get("token") != self._expected["token"]:
                    raise ValueError("E_OWNED_BOOTSTRAP_FAILURE_TOKEN")
                if not isinstance(failure["code"], str) or not isinstance(failure["detail"], str) or len(failure["code"]) > 128 or len(failure["detail"]) > _BOOTSTRAP_DETAIL_CHARS:
                    raise ValueError("E_OWNED_BOOTSTRAP_FAILURE_VALUE")
                frame = failure.get("identity")
                if frame is not None:
                    if not isinstance(frame, dict) or set(frame) != {"expected", "observed"} or any(
                            not isinstance(frame[name], dict) or set(frame[name]) != set(_IDENTITY_FIELDS)
                            for name in ("expected", "observed")):
                        raise ValueError("E_OWNED_BOOTSTRAP_FRAME")
                    if frame["expected"] != {name: self._expected[name] for name in _IDENTITY_FIELDS}:
                        raise ValueError("E_OWNED_BOOTSTRAP_EXPECTED")
                    if any((value is not None if name == 'launcher' else True) and
                           (not isinstance(value, str) or len(value) > _BOOTSTRAP_FIELD_CHARS)
                           for name, value in frame["observed"].items()):
                        raise ValueError("E_OWNED_BOOTSTRAP_FRAME")
                self.proof["startup"]["failure"] = {"code": failure.get("code"), "detail": failure.get("detail"),
                                                     "expected": None if frame is None else frame["expected"],
                                                     "observed": None if frame is None else frame["observed"]}
                raise ValueError("E_OWNED_BOOTSTRAP_FAILURE:" + json.dumps(failure, sort_keys=True, separators=(",", ":")))
            if self.process.poll() is not None: raise ValueError("E_OWNED_BOOTSTRAP_EXITED")
            if _left(until) <= 0: raise TimeoutError("E_OWNED_BOOTSTRAP_DEADLINE")
            time.sleep(min(.005, _left(until)))
        observed = _bootstrap_json(self._paths['ready'], 'READY')
        if not isinstance(observed, dict) or set(observed) != set(_IDENTITY_FIELDS) | {'token', 'pid', 'in_any_job'}:
            raise ValueError('E_OWNED_BOOTSTRAP_READY_SHAPE')
        if observed.get("token") != self._expected["token"] or observed.get("pid") != self.process.pid: raise ValueError("E_OWNED_BOOTSTRAP_ROOT_IDENTITY")
        for field in ("image", "sys_executable", "prefix", "base_prefix", "base_executable", "launcher"):
            if observed.get(field) != self._expected[field]: raise ValueError("E_OWNED_BOOTSTRAP_" + field.upper())
        if observed.get("in_any_job") is not True: raise ValueError("E_OWNED_BOOTSTRAP_OUTSIDE_JOB")
        pids, _ = self._observe(until)
        if self.process.pid not in pids or self._by_pid[self.process.pid]["image"] != self._expected["image"]: raise ValueError("E_OWNED_ROOT_IMAGE")
        self.proof["startup"]["observed"] = observed
    def open_gate(self, until):
        temporary = self._paths['go'].with_suffix('.go.tmp')
        with open(temporary, 'x', encoding='utf-8') as stream:
            stream.write(self._expected['token']); stream.flush(); os.fsync(stream.fileno())
        if _left(until) <= 0: raise TimeoutError('E_OWNED_START_DEADLINE')
        # Windows rename refuses an existing destination and exposes complete
        # bytes, never a partially written token, to the child.
        os.rename(temporary, self._paths['go'])
        self.proof["startup"]["go_opened"] = True
    def _exits(self, until, mode):
        while True:
            pids, accounting = self._observe(until)
            if not pids and not accounting.active: break
            if _left(until) <= 0: raise TimeoutError("E_OWNED_TREE_STILL_ALIVE")
            time.sleep(min(.005, _left(until)))
        for record in self._records.values():
            self._wait_native(record['handle'], until)
        operations = list(self.proof["termination"].get("operations", []))
        failures = list(self.proof["termination"].get("failures", []))
        self.proof["termination"] = {"mode": mode, "native_exit_proved": True, "records": len(self._records),
                                       "accounting_total": accounting.total, "operations": operations, "failures": failures}
    def wait(self, until):
        self._exits(until, "graceful")
        return self.process.wait(timeout=_left(until))
    def stop(self, until):
        if self.proof.get('startup', {}).get('state') == 'assigned-not-resumed':
            return self._stop_assigned_suspended(until)
        if not self.proof["termination"].get("native_exit_proved"):
            failure = None
            empty = False
            try:
                pids, accounting = self._observe(until)
                # Suspended members can be absent from the active-count view.
                # Job emptiness alone is not exit proof; every pinned handle
                # must already be signalled before termination is skipped.
                # Native signalled handles cannot spawn new descendants. The
                # Job PID snapshot can lag that exit; _exits still independently
                # requires fresh empty Job/accounting observations before proof.
                empty = self.process.pid in self._by_pid and bool(self._records) and all(
                    self._job.api.WaitForSingleObject(record["handle"], 0) == _WAIT_OBJECT_0
                    for record in self._records.values())
            except Exception as error:
                failure = error
            # A proof gap must remain an error, but must not prevent stopping
            # the job that is unambiguously ours.
            if empty:
                try:
                    self._exits(until, "already-exited")
                except Exception as error:
                    failure = error if failure is None else failure
                    if failure is not error: failure.add_note('E_OWNED_STOP_CLEANUP: ' + repr(error))
            else:
                try:
                    self._job.check(self._job.api.TerminateJobObject(self._job.handle, 1))
                    self.proof["termination"].setdefault("operations", []).append("TerminateJobObject")
                except Exception as error:
                    self._native_failure("TerminateJobObject", error)
                    if failure is None: failure = error
                    else: failure.add_note('E_OWNED_STOP_CLEANUP: ' + repr(error))
                else:
                    try:
                        self._exits(until, "forced")
                    except Exception as error:
                        if failure is None: failure = error
                        else: failure.add_note('E_OWNED_STOP_CLEANUP: ' + repr(error))
            try:
                self.process.wait(timeout=_left(until))
                self.proof["termination"].setdefault("operations", []).append("Popen.wait")
            except Exception as error:
                self._native_failure("Popen.wait", error)
                if failure is None: failure = error
                else: failure.add_note('E_OWNED_STOP_WAIT: ' + repr(error))
            for record in self._records.values():
                try:
                    self._wait_native(record['handle'], until)
                except Exception as error:
                    if failure is None: failure = error
                    else: failure.add_note('E_OWNED_STOP_WAIT: ' + repr(error))
            if failure is not None:
                self.proof['termination']['native_exit_proved'] = False
                raise failure
        return self.process.returncode

    def _stop_assigned_suspended(self, until):
        """No authored instruction ran: pin the exact root, terminate, then prove.

        Unlike a resumed tree, a suspended assigned root cannot have spawned a
        descendant. Do not depend on a startup notification to find that root.
        A failed duplicate can still use Popen's already-owned handle for exit
        observation; release must never close this borrowed source handle.
        """
        if self.proof['termination'].get('native_exit_proved'):
            return self.process.returncode
        failure = None
        if self.process.pid not in self._by_pid:
            try:
                self._record(self.process.pid, 'assigned-root', handle=self.process._handle,
                             owned_handle=False, handle_origin='popen-borrowed')
            except Exception as error:
                failure = error
        try:
            self._job.check(self._job.api.TerminateJobObject(self._job.handle, 1))
            self.proof['termination'].setdefault('operations', []).append('TerminateJobObject')
        except Exception as error:
            self._native_failure('TerminateJobObject', error)
            if failure is None: failure = error
            else: failure.add_note('E_OWNED_STOP_CLEANUP: ' + repr(error))
        try:
            self.process.wait(timeout=_left(until))
            self.proof['termination'].setdefault('operations', []).append('Popen.wait')
        except Exception as error:
            self._native_failure('Popen.wait', error)
            if failure is None: failure = error
            else: failure.add_note('E_OWNED_STOP_WAIT: ' + repr(error))
        try:
            self._exits(until, 'assigned-not-resumed')
        except Exception as error:
            if failure is None: failure = error
            else: failure.add_note('E_OWNED_STOP_CLEANUP: ' + repr(error))
        if failure is not None:
            self.proof['termination']['native_exit_proved'] = False
            raise failure
        return self.process.returncode

    def _wait_native(self, handle, until):
        result = self._job.api.WaitForSingleObject(handle, max(0, int(_left(until)*1000)))
        if result != _WAIT_OBJECT_0:
            error = ctypes.WinError(ctypes.get_last_error()) if result == 0xFFFFFFFF else ValueError('E_OWNED_MEMBER_STILL_ALIVE')
            self._native_failure('WaitForSingleObject', error)
            raise error
    def release(self):
        if not self.proof["termination"].get("native_exit_proved"): raise ValueError("E_OWNED_RELEASE_UNPROVEN")
        first = None
        for record in self._records.values():
            if record["handle"] and record.get("handle_owned", True):
                try: self._job.check(self._job.api.CloseHandle(record["handle"]))
                except Exception as error:
                    if first is None: first = error
                    else: first.add_note('E_OWNED_MEMBER_CLOSE: ' + repr(error))
                else: record["handle"] = None
        try: self._job.close()
        except Exception as error:
            if first is None: first = error
            else: first.add_note('E_OWNED_JOB_RELEASE: ' + repr(error) + '; notes=' + repr(getattr(error, '__notes__', [])))
        if first: raise first
        self.proof["released"] = True
    def abort_unassigned(self, until):
        if self.process.poll() is None: self.process.kill()
        if self._job.api.WaitForSingleObject(self.process._handle, max(0, int(_left(until)*1000))) != _WAIT_OBJECT_0: raise TimeoutError("E_OWNED_UNASSIGNED_STILL_ALIVE")
        self.proof["termination"] = {"mode": "unassigned", "native_exit_proved": True, "records": 0,
                                      "operations": ["Popen.kill", "WaitForSingleObject"]}

    def _native_failure(self, operation, error):
        self.proof["termination"].setdefault("failures", []).append({"operation": operation, "error": repr(error)})
        error.add_note("E_OWNED_NATIVE_OPERATION: " + operation + ": " + repr(error))


def _current_image():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True); kernel.GetModuleFileNameW.argtypes = [w.HMODULE, w.LPWSTR, w.DWORD]; kernel.GetModuleFileNameW.restype = w.DWORD
    size = 260
    while True:
        value = ctypes.create_unicode_buffer(size); actual = kernel.GetModuleFileNameW(None, value, size)
        if not actual: raise ctypes.WinError(ctypes.get_last_error())
        if actual < size-1: return _norm(value.value)
        size *= 2


def _failure(error, owner, complete, until):
    if owner is not None:
        for operation in owner.proof.get("termination", {}).get("operations", []):
            error.add_note("E_OWNED_START_CLEANUP_OPERATION: " + operation)
        for failure in owner.proof.get("termination", {}).get("failures", []):
            error.add_note("E_OWNED_NATIVE_OPERATION: " + failure["operation"] + ": " + failure["error"])
    error.owned_process_owner, error.owned_cleanup_complete, error.owned_cleanup_until = owner, complete, until
    return error


def _startup_expected(token, image=None):
    """Keep the parent-attested base role distinct from the loaded image role."""
    image = _current_image() if image is None else _norm(image)
    return {"token": token, "image": image, "sys_executable": _norm(sys.executable),
            "prefix": _norm(sys.prefix), "base_prefix": _norm(sys.base_prefix),
            "base_executable": _norm(getattr(sys, "_base_executable", sys.executable)), "launcher": None}


def _source_record(path):
    """Seal the same ordinary source bytes that the child must check before exec."""
    path = Path(path).absolute()
    for item in (path, *path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('E_OWNED_RECURSIVE_SOURCE_PATH')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ValueError('E_OWNED_RECURSIVE_SOURCE_TYPE')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino, opened.st_nlink) != (before.st_dev, before.st_ino, 1):
            raise ValueError('E_OWNED_RECURSIVE_SOURCE_IDENTITY')
        raw = stream.read(262145)
    if len(raw) > 262144:
        raise ValueError('E_OWNED_RECURSIVE_SOURCE_SIZE')
    return {'path': str(path), 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'links': 1}


def launch_current(popen, python, script, *, deadline, stdin, stdout, stderr, env, cwd,
                   recursive_deadline=None):
    """Launch current native image, assign suspended root, attest, then open gate."""
    if os.name != "nt": raise OSError("E_OWNED_WINDOWS_ONLY")
    requested, selected, script_path, cwd_path = _norm(python), _norm(sys.executable), _norm(script), Path(cwd).resolve()
    if requested != selected or not os.path.isfile(requested) or not os.path.isfile(script_path): raise ValueError("E_OWNED_REQUESTED_PYTHON")
    if not cwd_path.is_dir(): raise ValueError("E_OWNED_CWD")
    if _left(deadline) <= 0: raise TimeoutError("E_OWNED_START_DEADLINE")
    recursive_deadline = time.monotonic() + 120 if recursive_deadline is None else recursive_deadline
    if type(recursive_deadline) not in (int, float) or not math.isfinite(recursive_deadline) or _left(recursive_deadline) <= 0:
        raise ValueError('E_OWNED_RECURSIVE_DEADLINE')
    token = secrets.token_hex(32); paths = {key: cwd_path / ("owned-bootstrap-"+token+suffix) for key, suffix in {"contract":".json", "ready":".ready.json", "go":".go", "failure":".failure.json", "requests":".recursive-requests"}.items()}
    if any(path.exists() for path in paths.values()): raise ValueError("E_OWNED_BOOTSTRAP_PATH_COLLISION")
    recursive = {'version': 1, 'deadline': recursive_deadline, 'requests': str(paths['requests']),
        'bootstrap': _source_record(Path(__file__).with_name('recursive_bootstrap.py')),
        'policy': _source_record(Path(__file__).with_name('recursive_policy.py'))}
    paths['requests'].mkdir()
    image = _current_image(); child_env = dict(env); launcher = child_env.get("__PYVENV_LAUNCHER__")
    if _norm(sys.prefix) != _norm(sys.base_prefix): child_env["__PYVENV_LAUNCHER__"] = selected; launcher = selected
    # CPython consumes and removes __PYVENV_LAUNCHER__ before script entry.
    # Its effect is attested through sys.executable/prefix, not by expecting
    # an environment variable that no longer exists in the Python child.
    expected = _startup_expected(token, image)
    expected["sys_executable"] = selected
    with open(paths["contract"], "x", encoding="utf-8") as stream: json.dump({"token":token,"deadline":deadline,"expected":expected,"script":script_path,"recursive":recursive}, stream, sort_keys=True, separators=(",",":")); stream.flush(); os.fsync(stream.fileno())
    job = process = owner = None
    assigned = False
    try:
        job = _Job(); args = [image,"-B",str(Path(__file__).with_name("windows_owned_bootstrap.py")),"--contract",str(paths["contract"]),"--ready",str(paths["ready"]),"--go",str(paths["go"]),"--failure",str(paths["failure"]),"--script",script_path]
        if _left(deadline) <= 0: raise TimeoutError('E_OWNED_START_DEADLINE')
        process = popen(args, stdin=stdin, stdout=stdout, stderr=stderr, env=child_env, cwd=str(cwd_path), bufsize=0, close_fds=True, creationflags=_CREATE_SUSPENDED|_CREATE_NO_WINDOW)
        owner = CurrentImageOwner(job, process, paths, expected)
        job.check(job.api.AssignProcessToJobObject(job.handle, process._handle))
        assigned = True
        owner.assigned_root()
        if _left(deadline) <= 0: raise TimeoutError('E_OWNED_START_DEADLINE')
        try:
            job.resume(process)
        except BaseException as resume_error:
            if getattr(resume_error, "owned_resume_started", False): owner.resumed()
            raise
        owner.resumed(); owner.verify_bootstrap(deadline); owner.open_gate(deadline); return owner
    except BaseException as original:
        cleanup_until, complete = time.monotonic()+5, False
        try:
            if owner is not None:
                if assigned: owner.stop(cleanup_until)
                else: owner.abort_unassigned(cleanup_until)
                owner.release()
            elif process is not None:
                owner = CurrentImageOwner(job, process, paths, expected); owner.abort_unassigned(cleanup_until); owner.release()
            elif job is not None: job.close()
            if process is not None and process.stdin is not None:
                process.stdin.close()
            if job is not None and job._handle_debt:
                original.owned_job_debt = job
            complete = getattr(original, 'owned_job_debt', None) is None
        except Exception as cleanup:
            original.add_note("E_OWNED_START_CLEANUP: " + repr(cleanup) + '; notes=' + repr(getattr(cleanup, '__notes__', [])))
            if job is not None: original.owned_job_debt = job
        raise _failure(original, owner, complete, cleanup_until)
