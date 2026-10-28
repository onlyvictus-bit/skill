"""Isolated Windows cancellation primitive for one synchronous stdin writer.

This candidate deliberately owns no worker process and is not wired into the
retrieval coordinator.  Its contract is narrow: a caller starts one write,
requests cancellation against the actual writer thread handle if necessary,
then proves that native thread exit and Python-thread join completed before it
closes the stream.
"""
import ctypes
from ctypes import wintypes as w
from dataclasses import dataclass
import io
import math
import os
import threading
import time


WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
WAIT_FAILED = 0xFFFFFFFF
ERROR_NOT_FOUND = 1168
DUPLICATE_SAME_ACCESS = 0x00000002


class WriterError(RuntimeError):
    """The one owned request could not be completed truthfully."""


class WriterCancelled(WriterError):
    """Cancellation was observed by the writer; the request was not resent."""


class WriterDeadline(WriterError):
    """The supplied absolute deadline expired before proven writer exit."""


class WriterStillAlive(WriterError):
    """The stream cannot be disposed while its writer might still use it."""


class WriterNativeError(WriterError):
    """A required Windows thread-handle operation failed."""


@dataclass(frozen=True)
class CancelObservation:
    """One cancellation request, including ERROR_NOT_FOUND as a non-success."""

    status: str
    error_code: int | None
    seconds: float


@dataclass(frozen=True)
class WriterOutcome:
    """Joined terminal state; native exit is unobserved after a pre-I/O failure."""

    error: BaseException | None
    native_thread_exited: bool
    joined: bool


class _Kernel:
    """The very small Kernel32 surface required for a real current-thread handle."""

    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.GetCurrentProcess.argtypes = []
        self.api.GetCurrentProcess.restype = w.HANDLE
        self.api.GetCurrentThread.argtypes = []
        self.api.GetCurrentThread.restype = w.HANDLE
        self.api.DuplicateHandle.argtypes = [w.HANDLE, w.HANDLE, w.HANDLE,
                                             ctypes.POINTER(w.HANDLE), w.DWORD,
                                             w.BOOL, w.DWORD]
        self.api.DuplicateHandle.restype = w.BOOL
        self.api.CancelSynchronousIo.argtypes = [w.HANDLE]
        self.api.CancelSynchronousIo.restype = w.BOOL
        self.api.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.api.WaitForSingleObject.restype = w.DWORD
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.api.CloseHandle.restype = w.BOOL

    @staticmethod
    def _check(value, operation):
        if not value:
            raise WriterNativeError(operation + ': ' + str(ctypes.get_last_error()))

    def duplicate_current_thread(self):
        process = self.api.GetCurrentProcess()
        duplicate = w.HANDLE()
        self._check(self.api.DuplicateHandle(process, self.api.GetCurrentThread(), process,
                                             ctypes.byref(duplicate), 0, False,
                                             DUPLICATE_SAME_ACCESS), 'DuplicateHandle')
        return duplicate.value

    def cancel(self, handle):
        started = time.monotonic()
        if self.api.CancelSynchronousIo(handle):
            return CancelObservation('requested', None, time.monotonic() - started)
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return CancelObservation('not_found', error, time.monotonic() - started)
        return CancelObservation('failed', error, time.monotonic() - started)

    def wait(self, handle, until):
        remaining = until - time.monotonic()
        # A zero wait is an actual native state observation, not an assumed exit.
        milliseconds = max(0, min(0xFFFFFFFE, math.ceil(remaining * 1000)))
        result = self.api.WaitForSingleObject(handle, milliseconds)
        if result == WAIT_OBJECT_0:
            return
        if result == WAIT_TIMEOUT:
            raise WriterDeadline('E_WRITER_NATIVE_THREAD_STILL_ALIVE')
        if result == WAIT_FAILED:
            raise WriterNativeError('WaitForSingleObject: ' + str(ctypes.get_last_error()))
        raise WriterNativeError('WaitForSingleObject unexpected result: ' + str(result))

    def close(self, handle):
        self._check(self.api.CloseHandle(handle), 'CloseHandle')


class SynchronousWriter:
    """Own exactly one synchronous stream write and its duplicate thread handle.

    ``until`` parameters are absolute ``time.monotonic()`` deadlines.  A true
    CancelSynchronousIo result is only a request: ``join`` is the operation
    that proves termination.  No write is retried after an error or cancellation.
    """

    def __init__(self, stream):
        if os.name != 'nt':
            raise WriterNativeError('E_WRITER_WINDOWS_REQUIRED')
        # A buffered .close() can flush the cancelled request again. Require an
        # unbuffered binary stream (Popen(..., bufsize=0)); never discard buffered
        # bytes silently or depend on a reader dying to release another flush.
        if isinstance(stream, (io.BufferedIOBase, io.TextIOBase)):
            raise WriterError('E_WRITER_BUFFERED_STREAM')
        self.stream = stream
        self.write_started = threading.Event()
        self.done = threading.Event()
        self.closing = threading.Event()
        self._ready = threading.Event()
        self._accepted = threading.Event()
        self._lock = threading.Lock()
        self._ownership = 'NEW'
        self._kernel = _Kernel()
        self._thread = None
        self._thread_handle = None
        self._handle_closed = False
        self._joined = False
        self._native_thread_exited = False
        self._pre_io_failure = False
        self._io_attempted = False
        self._stream_closed = False
        self._error = None
        self._cancel_requests = []
        self._timings = {'started_at': None, 'handle_ready_at': None, 'accepted_at': None,
                         'write_started_at': None, 'write_finished_at': None,
                         'done_at': None, 'native_wait_seconds': [],
                         'thread_join_seconds': [], 'cancel_requests': []}

    @property
    def has_joined(self):
        return self._joined

    @property
    def stream_closed(self):
        return self._stream_closed

    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()

    def timing_snapshot(self):
        """Return immutable-friendly diagnostics; inclusive values are not totals."""
        with self._lock:
            return {key: list(value) if isinstance(value, list) else value
                    for key, value in self._timings.items()}

    @staticmethod
    def _validate_deadline(until):
        if type(until) not in (int, float) or not math.isfinite(until):
            raise WriterError('E_WRITER_DEADLINE_VALUE')

    def start(self, payload, until):
        """Publish the native handle by the caller deadline, or forbid late I/O."""
        self._validate_deadline(until)
        if time.monotonic() >= until:
            raise WriterDeadline('E_WRITER_START_DEADLINE')
        with self._lock:
            if self._thread is not None:
                raise WriterError('E_WRITER_ALREADY_STARTED')
            if self._stream_closed:
                raise WriterError('E_WRITER_STREAM_CLOSED')
            data = bytes(payload)
            if time.monotonic() >= until:
                raise WriterDeadline('E_WRITER_START_DEADLINE')
            self._timings['started_at'] = time.monotonic()
            self._thread = threading.Thread(target=self._run, args=(data, until),
                                            name='owned-synchronous-writer', daemon=False)
            self._ownership = 'PENDING_WORKER'
            try:
                self._thread.start()
            except Exception:
                # Native creation failed: no writer/stream ownership transferred.
                if self._thread.ident is None:
                    self._thread = None
                    self._ownership = 'NEW'
                else:
                    self.closing.set()
                raise
        # Do not let callers issue a cancellation to a pseudo/TID-reused handle.
        if not self._ready.wait(timeout=max(0.0, until - time.monotonic())):
            self.closing.set()
            raise WriterDeadline('E_WRITER_START_DEADLINE')
        # Event notification is not ownership. Acceptance and self-retirement
        # compete for the same PENDING state under this lock.
        with self._lock:
            if self._pre_io_failure and self._error is not None:
                raise self._error
            accepted_at = time.monotonic()
            if self.closing.is_set() or accepted_at >= until:
                self.closing.set()
                raise WriterDeadline('E_WRITER_START_DEADLINE')
            if self._ownership != 'PENDING_WORKER' or self._thread_handle is None:
                raise WriterNativeError('E_WRITER_THREAD_HANDLE_UNAVAILABLE') from self._error
            self._ownership = 'ACCEPTED_CONTROLLER'
            self._timings['accepted_at'] = accepted_at
            self._accepted.set()

    def _run(self, payload, until):
        try:
            # No lock is held across the native call; a delayed allocation must
            # not prevent a controller from observing its own deadline.
            handle = self._kernel.duplicate_current_thread()
            with self._lock:
                self._thread_handle = handle
                self._timings['handle_ready_at'] = time.monotonic()
            if self.closing.is_set():
                raise WriterCancelled('E_WRITER_CANCELLED_BEFORE_WRITE')
            if time.monotonic() >= until:
                raise WriterDeadline('E_WRITER_START_DEADLINE')
            self._ready.set()
            self._accepted.wait(timeout=max(0.0, until - time.monotonic()))
            with self._lock:
                if self._ownership != 'ACCEPTED_CONTROLLER':
                    if self.closing.is_set():
                        raise WriterCancelled('E_WRITER_CANCELLED_BEFORE_WRITE')
                    raise WriterDeadline('E_WRITER_START_DEADLINE')
            remaining = memoryview(payload)
            while remaining:
                if self.closing.is_set():
                    raise WriterCancelled('E_WRITER_CANCELLED')
                if not self._io_attempted and time.monotonic() >= until:
                    raise WriterDeadline('E_WRITER_START_DEADLINE')
                self._io_attempted = True
                if not self.write_started.is_set():
                    self.write_started.set()
                    with self._lock:
                        self._timings['write_started_at'] = time.monotonic()
                written = self.stream.write(remaining)
                if type(written) is not int or written <= 0:
                    raise WriterError('E_WRITER_SHORT_WRITE')
                if written > len(remaining):
                    raise WriterError('E_WRITER_INVALID_WRITE_COUNT')
                remaining = remaining[written:]
                if self.closing.is_set():
                    raise WriterCancelled('E_WRITER_CANCELLED')
            if self.closing.is_set():
                raise WriterCancelled('E_WRITER_CANCELLED')
            self._io_attempted = True
            self.stream.flush()
            if self.closing.is_set():
                raise WriterCancelled('E_WRITER_CANCELLED')
        except BaseException as error:
            self._error = error
            self._pre_io_failure = not self._io_attempted
        finally:
            # If start timed out before publication, no caller owns this late
            # duplicate and no I/O began. Retire it here, without a new deadline.
            retire = None
            with self._lock:
                if self._pre_io_failure and self._ownership == 'PENDING_WORKER':
                    retire = self._thread_handle
                    self._ownership = 'NO_HANDLE' if retire is None else 'RETIRING_WORKER'
            if retire is not None:
                try:
                    self._kernel.close(retire)
                    with self._lock:
                        self._handle_closed = True
                        self._thread_handle = None
                        self._ownership = 'RETIRED_WORKER'
                except BaseException as cleanup:
                    self._error.add_note('E_WRITER_START_HANDLE_CLOSE: ' + repr(cleanup))
                    with self._lock:
                        self._ownership = 'RETIRE_FAILED_WORKER'
            with self._lock:
                self._timings['write_finished_at'] = time.monotonic()
            self.done.set()
            with self._lock:
                self._timings['done_at'] = time.monotonic()
            self._ready.set()

    def request_cancel(self, until):
        """Request cancellation before the caller's absolute monotonic deadline.

        This function only asks Windows to cancel.  ``join(until)`` remains
        mandatory proof of writer termination, including after a successful
        CancelSynchronousIo call or ERROR_NOT_FOUND (1168).
        """
        self._validate_deadline(until)
        if self._thread is None:
            raise WriterError('E_WRITER_NOT_STARTED')
        if time.monotonic() >= until:
            raise WriterDeadline('E_WRITER_CANCEL_DEADLINE')
        self.closing.set()
        with self._lock:
            if self._ownership != 'ACCEPTED_CONTROLLER':
                raise WriterNativeError('E_WRITER_START_NOT_ACCEPTED')
        if self.done.is_set():
            observation = CancelObservation('not_needed', None, 0.0)
        else:
            handle = self._thread_handle
            if handle is None:
                raise WriterNativeError('E_WRITER_THREAD_HANDLE_UNAVAILABLE') from self._error
            observation = self._kernel.cancel(handle)
        with self._lock:
            self._cancel_requests.append(observation)
            self._timings['cancel_requests'].append({'status': observation.status,
                                                       'error_code': observation.error_code,
                                                       'seconds': observation.seconds,
                                                       'at': time.monotonic()})
        if observation.status == 'failed':
            raise WriterNativeError('CancelSynchronousIo: ' + str(observation.error_code))
        return observation

    def join(self, until):
        """Prove native exit, join Python cleanup, then retire the duplicate handle."""
        self._validate_deadline(until)
        if self._joined:
            return WriterOutcome(self._error, native_thread_exited=self._native_thread_exited, joined=True)
        if self._thread is None:
            raise WriterError('E_WRITER_NOT_STARTED')
        with self._lock:
            accepted = self._ownership == 'ACCEPTED_CONTROLLER'
        if not accepted:
            # The worker may still be self-retiring. Never wait/cancel/close its
            # handle until Python join proves that ownership can no longer move.
            self._thread.join(timeout=max(0.0, until - time.monotonic()))
            if self._thread.is_alive():
                raise WriterDeadline('E_WRITER_PYTHON_THREAD_STILL_ALIVE')
        handle = self._thread_handle
        if handle is None:
            if not self._pre_io_failure or self._io_attempted or self._error is None:
                raise WriterNativeError('E_WRITER_THREAD_HANDLE_UNAVAILABLE') from self._error
            # Handle creation failed (or a late unpublished handle was retired)
            # before all I/O. Python join is sufficient to dispose the unused
            # stream, but is NOT reported as a native-handle exit observation.
            self._thread.join(timeout=max(0.0, until - time.monotonic()))
            if self._thread.is_alive():
                raise WriterDeadline('E_WRITER_PYTHON_THREAD_STILL_ALIVE')
            self._joined = True
            return WriterOutcome(self._error, native_thread_exited=False, joined=True)
        native_started = time.monotonic()
        self._kernel.wait(handle, until)
        self._native_thread_exited = True
        with self._lock:
            self._timings['native_wait_seconds'].append(time.monotonic() - native_started)
        join_started = time.monotonic()
        self._thread.join(timeout=max(0.0, until - time.monotonic()))
        with self._lock:
            self._timings['thread_join_seconds'].append(time.monotonic() - join_started)
        if self._thread.is_alive():
            raise WriterDeadline('E_WRITER_PYTHON_THREAD_STILL_ALIVE')
        if not self._handle_closed:
            self._kernel.close(handle)
            self._handle_closed = True
        self._joined = True
        return WriterOutcome(self._error, native_thread_exited=True, joined=True)

    def cancel_and_join(self, until):
        """Cancel I/O-start races under ONE deadline, never resend request bytes.

        ERROR_NOT_FOUND can race the next WriteFile. Short native observation
        windows allow another cancellation request, but every window is capped
        by the same absolute deadline; no shutdown allowance is reset or added.
        The owning controller serializes control calls on this instance.
        """
        self._validate_deadline(until)
        if self._thread is None:
            raise WriterError('E_WRITER_NOT_STARTED')
        self.closing.set()
        with self._lock:
            accepted = self._ownership == 'ACCEPTED_CONTROLLER'
        if not accepted:
            return self.join(until)
        if not self._ready.wait(timeout=max(0.0, until - time.monotonic())):
            raise WriterDeadline('E_WRITER_THREAD_HANDLE_DEADLINE')
        while True:
            if time.monotonic() >= until or self._joined:
                return self.join(until)  # Zero wait may prove an already-ended thread.
            self.request_cancel(until)
            try:
                return self.join(min(until, time.monotonic() + .005))
            except WriterDeadline:
                if time.monotonic() >= until:
                    raise

    def close_stream(self):
        """Dispose only after the native proof and Python join, never before."""
        if self._stream_closed:
            return
        if self.is_alive() or not self._joined:
            raise WriterStillAlive('E_WRITER_STREAM_CLOSE_BEFORE_JOIN')
        self.stream.close()
        self._stream_closed = True
