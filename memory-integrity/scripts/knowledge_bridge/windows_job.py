"""Own a Windows shard tree before its first instruction; await exit before cleanup."""
import ctypes
from ctypes import wintypes as w
import subprocess
import threading
import time


class _Limits(ctypes.Structure):
    _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                ('flags', w.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                ('active_limit', w.DWORD), ('affinity', ctypes.c_size_t),
                ('priority', w.DWORD), ('scheduling', w.DWORD),
                ('io', ctypes.c_uint64 * 6), ('memory', ctypes.c_size_t * 4)]


class _Accounting(ctypes.Structure):
    _fields_ = [('times', ctypes.c_int64 * 4), ('faults', w.DWORD),
                ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]


class _Thread(ctypes.Structure):
    _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('ident', w.DWORD),
                ('owner', w.DWORD), ('base', w.LONG), ('delta', w.LONG), ('flags', w.DWORD)]


class OwnedJob:
    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'IsProcessInJob': ([w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
            'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
            'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
            'Thread32First': ([w.HANDLE, ctypes.POINTER(_Thread)], w.BOOL),
            'Thread32Next': ([w.HANDLE, ctypes.POINTER(_Thread)], w.BOOL),
            'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'GetProcessIdOfThread': ([w.HANDLE], w.DWORD),
            'ResumeThread': ([w.HANDLE], w.DWORD),
            'CloseHandle': ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        self.check(self.handle)
        try:
            limits = _Limits()
            limits.flags = 0x2000  # KILL_ON_JOB_CLOSE, no breakaway permission.
            self.check(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        except BaseException as original:
            try:
                self.release()
            except Exception as cleanup:
                original.add_note('E_SHARD_JOB_RELEASE: ' + repr(cleanup))
            raise

    @staticmethod
    def check(value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())

    def close_handles(self, handles, original=None):
        """Attempt every owned close; keep any active operation error primary."""
        failures = []
        for handle in handles:
            try:
                self.check(self.api.CloseHandle(handle))
            except Exception as cleanup:
                failures.append(cleanup)
        if original is not None:
            for cleanup in failures:
                original.add_note('E_SHARD_HANDLE_CLOSE: ' + repr(cleanup))
        elif failures:
            for cleanup in failures[1:]:
                failures[0].add_note('E_SHARD_HANDLE_CLOSE: ' + repr(cleanup))
            raise failures[0]

    def resume(self, process):
        """Popen closes the primary thread handle: recover it while still suspended."""
        snapshot = self.api.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        handles, failure = [snapshot], None
        try:
            entry = _Thread()
            entry.size = ctypes.sizeof(entry)
            found = []
            self.check(self.api.Thread32First(snapshot, ctypes.byref(entry)))
            while True:
                if entry.owner == process.pid:
                    found.append(entry.ident)
                if not self.api.Thread32Next(snapshot, ctypes.byref(entry)):
                    if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                        raise ctypes.WinError(ctypes.get_last_error())
                    break
            if len(found) != 1:
                raise ValueError('E_SHARD_SUSPENDED_THREAD_IDENTITY')
            thread = self.api.OpenThread(0x802, False, found[0])  # query-limited + suspend/resume
            self.check(thread)
            handles.append(thread)
            if self.api.GetProcessIdOfThread(thread) != process.pid:
                raise ValueError('E_SHARD_THREAD_OWNER')
            if self.api.ResumeThread(thread) != 1:
                raise ValueError('E_SHARD_THREAD_RESUME')
        except BaseException as original:
            failure = original
            raise
        finally:
            self.close_handles(reversed(handles), failure)

    def accounting(self):
        info = _Accounting()
        self.check(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None))
        return info

    def active(self):
        return self.accounting().active

    def wait_empty(self, until):
        while self.active():
            remaining = until - time.monotonic()
            if remaining <= 0:
                raise ValueError('E_SHARD_TREE_STILL_ALIVE')
            # Poll actual job state, not a fixed delay presented as exit proof.
            threading.Event().wait(min(.005, remaining))

    def terminate(self, until):
        # Job active-count zero can precede a process handle becoming signalled.
        # Pin actual members BEFORE termination, then wait their native handles.
        class Members(ctypes.Structure):
            _fields_ = [('assigned', w.DWORD), ('listed', w.DWORD),
                        ('pids', ctypes.c_size_t * 1024)]
        handles, failure = {}, None
        try:
            members = Members()
            self.check(self.api.QueryInformationJobObject(self.handle, 3, ctypes.byref(members), ctypes.sizeof(members), None))
            if members.listed > 1024 or members.assigned != members.listed:
                raise ValueError('E_SHARD_TREE_MEMBERSHIP')
            for pid in members.pids[:members.listed]:
                handle = self.api.OpenProcess(0x101000, False, pid)  # SYNCHRONIZE + query-limited
                self.check(handle)
                handles[pid] = handle
                inside = w.BOOL()
                self.check(self.api.IsProcessInJob(handle, self.handle, ctypes.byref(inside)))
                if not inside.value:
                    raise ValueError('E_SHARD_TREE_MEMBER_CHANGED')
            # The root's Popen handle remains pinned even if it already exited.
            if self.root.pid not in handles:
                handles[self.root.pid] = self.root._handle
            if self.accounting().total != len(handles):
                raise ValueError('E_SHARD_TREE_UNOBSERVED_MEMBER')
            self.check(self.api.TerminateJobObject(self.handle, 1))
            self.wait_empty(until)
            for handle in handles.values():
                millis = max(0, int((until - time.monotonic()) * 1000))
                if self.api.WaitForSingleObject(handle, millis) != 0:
                    raise ValueError('E_SHARD_MEMBER_STILL_ALIVE')
            if self.accounting().total != len(handles):
                raise ValueError('E_SHARD_TREE_CHANGED_DURING_STOP')
        except BaseException as original:
            failure = original
            # A membership failure is NOT successful shutdown; still stop our job.
            if not self.api.TerminateJobObject(self.handle, 1):
                original.add_note('E_SHARD_TERMINATION_FAILED: '+str(ctypes.get_last_error()))
            raise
        finally:
            self.close_handles((handle for handle in handles.values()
                                if handle != self.root._handle), failure)

    def release(self):
        if self.handle:
            self.check(self.api.CloseHandle(self.handle))
            self.handle = None


def start(popen, args, **kwargs):
    """Assignment precedes resume: a launcher cannot create an unowned child."""
    job, process, assigned = OwnedJob(), None, False
    try:
        process = popen(args, creationflags=0x4 | 0x08000000, **kwargs)  # SUSPENDED | NO_WINDOW
        job.root = process
        job.check(job.api.AssignProcessToJobObject(job.handle, process._handle))
        assigned = True
        job.resume(process)
        return process, job
    except BaseException as original:
        try:
            until = time.monotonic() + 5
            if process is not None:
                if assigned:
                    job.terminate(until)
                elif process.poll() is None:
                    process.kill()  # Never resumed, so no descendants can exist.
                process.wait(timeout=max(0, until - time.monotonic()))
                if process.stdin is not None:
                    process.stdin.close()
        except Exception as cleanup:
            original.add_note('E_SHARD_START_CLEANUP: ' + repr(cleanup))
        finally:
            try:
                job.release()
            except Exception as cleanup:
                original.add_note('E_SHARD_JOB_RELEASE: ' + repr(cleanup))
        raise


def stop(process, job, writer, *, graceful):
    """EOF for an idle worker; cancellation kills/waits the entire owned job."""
    until = time.monotonic() + 5
    try:
        if graceful and (writer is None or not writer.is_alive()):
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            process.wait(timeout=max(0, until - time.monotonic()))
            job.wait_empty(until)
        else:
            job.terminate(until)
            process.wait(timeout=max(0, until - time.monotonic()))
        if writer is not None:
            writer.join(timeout=max(0, until - time.monotonic()))
            if writer.is_alive():
                raise ValueError('E_DISTRIBUTED_WRITER_STILL_ALIVE')
        job.release()
    except BaseException as original:
        # Even a failed EOF/observation must not abandon a live owned tree.
        # Keep the same shutdown deadline and the original error as primary.
        try:
            if job.handle:
                job.terminate(until)
                process.wait(timeout=max(0, until - time.monotonic()))
                if writer is not None:
                    writer.join(timeout=max(0, until - time.monotonic()))
                    if writer.is_alive():
                        raise ValueError('E_DISTRIBUTED_WRITER_STILL_ALIVE')
        except Exception as cleanup:
            original.add_note('E_SHARD_STOP_CLEANUP: ' + repr(cleanup))
        finally:
            try:
                job.release()
            except Exception as cleanup:
                original.add_note('E_SHARD_JOB_RELEASE: ' + repr(cleanup))
        raise
