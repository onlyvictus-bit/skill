"""Native controls for the isolated synchronous Windows stdin writer candidate.

These tests intentionally use only controller Python and a fixture-owned reader.
They neither start the selected runtime nor exercise retrieval.
"""
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

try:
    from knowledge_bridge.windows_writer import (SynchronousWriter, WriterCancelled, WriterError, WriterNativeError,
                                                 WriterDeadline, WriterStillAlive)
except ModuleNotFoundError as exc:
    if exc.name != 'knowledge_bridge.windows_writer':
        raise
    SynchronousWriter = WriterCancelled = WriterError = WriterNativeError = WriterDeadline = WriterStillAlive = None


class _GateStream:
    """Hold the writer in Python so CancelSynchronousIo has no pending I/O to find."""
    def __init__(self):
        self.entered, self.release, self.closed = threading.Event(), threading.Event(), False

    def write(self, data):
        self.entered.set()
        if not self.release.wait(5):
            raise TimeoutError('CONTROL_GATE_RELEASE')
        return len(data)

    def flush(self):
        return None

    def close(self):
        self.closed = True


class _FailingStream:
    def __init__(self):
        self.calls, self.closed = 0, False

    def write(self, _data):
        self.calls += 1
        raise OSError('CONTROL_WRITE_FAILURE')

    def flush(self):
        raise AssertionError('flush after failed write would be a resend-like error')

    def close(self):
        self.closed = True


class _PartialStream:
    def __init__(self):
        self.data, self.closed = bytearray(), False

    def write(self, data):
        part = bytes(data[:3])
        self.data.extend(part)
        return len(part)

    def flush(self):
        return None

    def close(self):
        self.closed = True


class _GateThenPipe:
    """Place a deterministic gap between the final cancellation check and WriteFile."""
    def __init__(self, raw):
        self.raw = raw
        self.entered, self.release = threading.Event(), threading.Event()

    def write(self, data):
        self.entered.set()
        if not self.release.wait(3):
            raise TimeoutError('CONTROL_GATE_THEN_PIPE_RELEASE')
        return self.raw.write(data)

    def flush(self):
        return self.raw.flush()

    def close(self):
        return self.raw.close()


@unittest.skipUnless(os.name == 'nt', 'Windows synchronous I/O cancellation required')
class WindowsWriter(unittest.TestCase):
    def setUp(self):
        if SynchronousWriter is None:
            self.fail('SR2 candidate module is absent')
        self.root = Path(tempfile.mkdtemp(prefix='windows-writer-'))
        self.timings, self.reader, self.writer = [], None, None
        self.addCleanup(self._retain_timing)
        self.addCleanup(self._close_fixture)

    def _elapsed(self, label, started):
        self.timings.append({'label': label, 'seconds': time.monotonic() - started})

    def _retain_timing(self):
        payload = {'case': self.id(), 'timings': self.timings,
                   'writer': None if self.writer is None else self.writer.timing_snapshot()}
        with (self.root / 'Timings.json').open('x', encoding='utf-8') as stream:
            json.dump(payload, stream, sort_keys=True, indent=2)
            stream.write('\n')

    def _close_fixture(self):
        failures = []
        try:
            if self.writer is not None and self.writer.is_alive():
                try:
                    self.writer.request_cancel(time.monotonic() + 3)
                    self.writer.join(time.monotonic() + 3)
                except BaseException as error:
                    failures.append(error)
        finally:
            if self.reader is not None:
                try:
                    if self.reader.poll() is None:
                        self.reader.terminate()
                        try:
                            self.reader.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.reader.kill()
                            self.reader.wait(timeout=3)
                except BaseException as error:
                    failures.append(error)
        if self.writer is not None and self.writer.is_alive():
            try:
                self.writer.join(time.monotonic() + 3)
            except BaseException as error:
                failures.append(error)
        if self.writer is not None:
            if self.writer.is_alive():
                failures.append(AssertionError('fixture writer remained alive; stdin deliberately left open'))
            elif self.writer.has_joined and not self.writer.stream_closed:
                try:
                    self.writer.close_stream()
                except BaseException as error:
                    failures.append(error)
        if self.reader is not None:
            # stdin is the writer-owned stream; never close it while the writer survives.
            streams = (self.reader.stdout, self.reader.stderr)
            if self.writer is None or not self.writer.is_alive():
                streams += (self.reader.stdin,)
            for stream in streams:
                if stream is not None and not stream.closed:
                    try:
                        stream.close()
                    except BaseException as error:
                        failures.append(error)
        if failures:
            error = AssertionError('fixture cleanup failed')
            for failure in failures:
                error.add_note(repr(failure))
            raise error

    def _blocked_reader(self):
        ready = self.root / 'reader-ready'
        code = ('import sys,time\n'
                'from pathlib import Path\n'
                'Path(sys.argv[1]).joinpath("reader-ready").write_text("ready",encoding="utf-8")\n'
                'time.sleep(30)\n')
        self.reader = subprocess.Popen([sys.executable, '-B', '-c', code, str(self.root)], bufsize=0,
                                       stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE)
        until = time.monotonic() + 3
        while not ready.exists():
            exited = self.reader.poll()
            if exited is not None:
                detail = self.reader.stderr.read().decode('utf-8', errors='replace')
                self.fail('controlled non-reading reader exited before ready: ' + detail)
            if time.monotonic() >= until:
                self.fail('controlled non-reading reader readiness timed out')
            threading.Event().wait(.005)
        self.assertIsNone(self.reader.poll())
        return self.reader.stdin

    def _start_blocked_writer(self):
        stream = self._blocked_reader()
        self.writer = SynchronousWriter(stream)
        started = time.monotonic()
        self.writer.start(b'x' * (4 * 1024 * 1024), time.monotonic() + 2)
        self.assertTrue(self.writer.write_started.wait(2), 'writer did not enter real pipe write')
        self.assertFalse(self.writer.done.wait(.1), 'reader unexpectedly drained the writer payload')
        self._elapsed('blocked_write_setup', started)

    def test_real_blocked_write_cancels_while_reader_remains_alive(self):
        self._start_blocked_writer()
        started = time.monotonic()
        cancel = self.writer.request_cancel(time.monotonic() + 3)
        self._elapsed('cancel_request', started)
        self.assertEqual(cancel.status, 'requested')
        self.assertIsNone(self.reader.poll(), 'reader must remain alive during cancellation')
        started = time.monotonic()
        outcome = self.writer.join(time.monotonic() + 3)
        self._elapsed('completion_and_join', started)
        self.assertTrue(outcome.native_thread_exited)
        self.assertFalse(self.writer.is_alive())
        self.assertIsNotNone(outcome.error, 'blocked synchronous write must report its completion result')
        started = time.monotonic()
        self.assertIsNone(self.reader.poll(), 'writer exit must not depend on killing the reader')
        self._elapsed('reader_alive_check', started)
        self.writer.close_stream()

    def test_stream_close_is_refused_until_blocked_writer_has_exited(self):
        self._start_blocked_writer()
        with self.assertRaises(WriterStillAlive):
            self.writer.close_stream()
        self.assertFalse(self.reader.stdin.closed)
        self.writer.request_cancel(time.monotonic() + 3)
        self.writer.join(time.monotonic() + 3)
        self.writer.close_stream()
        self.assertTrue(self.reader.stdin.closed)

    def test_cancel_and_join_retries_after_a_cancel_miss_before_real_pipe_io(self):
        raw = self._blocked_reader()
        gated = _GateThenPipe(raw)
        self.writer = SynchronousWriter(gated)
        deadline = time.monotonic() + 3
        self.writer.start(b'x' * (4 * 1024 * 1024), deadline)
        self.assertTrue(gated.entered.wait(2), 'writer did not reach controlled pre-I/O gap')
        first = self.writer.request_cancel(deadline)
        self.assertEqual(first.status, 'not_found', 'no WriteFile is pending at the controlled gap')
        self.assertFalse(self.writer.done.is_set())
        gated.release.set()
        started = time.monotonic()
        outcome = self.writer.cancel_and_join(deadline)
        self._elapsed('race_cancel_and_join', started)
        self.assertTrue(outcome.native_thread_exited)
        self.assertFalse(self.writer.is_alive())
        self.assertIsNotNone(outcome.error)
        self.assertIn('requested', [row['status'] for row in self.writer.timing_snapshot()['cancel_requests']])
        self.assertIsNone(self.reader.poll(), 'retry must cancel the writer without killing its reader')
        self.writer.close_stream()

    def test_cancel_miss_is_not_completion_and_close_remains_refused(self):
        stream = _GateStream()
        self.writer = SynchronousWriter(stream)
        self.writer.start(b'blocked-before-native-io', time.monotonic() + 2)
        self.assertTrue(stream.entered.wait(2))
        started = time.monotonic()
        cancel = self.writer.request_cancel(time.monotonic() + 2)
        self._elapsed('cancel_miss_request', started)
        self.assertEqual(cancel.status, 'not_found')
        with self.assertRaises(WriterDeadline):
            self.writer.join(time.monotonic() + .05)
        with self.assertRaises(WriterStillAlive):
            self.writer.close_stream()
        stream.release.set()
        started = time.monotonic()
        outcome = self.writer.join(time.monotonic() + 2)
        self._elapsed('cancel_miss_completion_and_join', started)
        self.assertIsInstance(outcome.error, WriterCancelled)
        self.writer.close_stream()
        self.assertTrue(stream.closed)

    def test_failed_write_is_recorded_once_and_never_resent(self):
        stream = _FailingStream()
        self.writer = SynchronousWriter(stream)
        self.writer.start(b'one-request', time.monotonic() + 2)
        outcome = self.writer.join(time.monotonic() + 2)
        self.assertIsInstance(outcome.error, OSError)
        self.assertEqual(stream.calls, 1, 'failed request must not be resent')
        self.writer.close_stream()
        self.assertTrue(stream.closed)

    def test_short_writes_are_completed_before_success(self):
        stream = _PartialStream()
        self.writer = SynchronousWriter(stream)
        self.writer.start(b'abcdefghi', time.monotonic() + 2)
        outcome = self.writer.join(time.monotonic() + 2)
        self.assertIsNone(outcome.error)
        self.assertEqual(bytes(stream.data), b'abcdefghi')
        repeated = self.writer.join(time.monotonic() + 2)
        self.assertEqual(repeated, outcome, 'repeated join must not wait on a retired native handle')
        self.writer.close_stream()

    def test_start_obeys_absolute_deadline_and_prevents_late_write(self):
        stream = _GateStream()
        self.writer = SynchronousWriter(stream)
        entered, release = threading.Event(), threading.Event()
        original = self.writer._kernel.duplicate_current_thread
        def delayed_duplicate():
            entered.set()
            if not release.wait(2):
                raise TimeoutError('CONTROL_DUPLICATE_RELEASE')
            return original()
        self.writer._kernel.duplicate_current_thread = delayed_duplicate
        deadline = time.monotonic() + .05
        with self.assertRaises(WriterDeadline):
            self.writer.start(b'must-not-write-after-start-deadline', deadline)
        self.assertTrue(entered.is_set())
        self.assertFalse(stream.entered.is_set())
        release.set()
        # Test-only observation of the injected stall ending, not a new API deadline.
        self.writer._thread.join(timeout=2)
        self.assertFalse(self.writer.is_alive())
        self.assertTrue(self.writer._handle_closed, 'late duplicate must retire itself before I/O')
        self.assertIsNone(self.writer._thread_handle)
        outcome = self.writer.join(deadline)  # Original expired deadline; zero-time observation only.
        self.assertIsInstance(outcome.error, WriterCancelled)
        self.assertFalse(outcome.native_thread_exited)
        self.assertFalse(stream.entered.is_set())
        self.writer.close_stream()

    def test_buffered_stream_is_rejected_before_any_request(self):
        raw = io.BytesIO()
        stream = io.BufferedWriter(raw)
        try:
            with self.assertRaisesRegex(WriterError, 'E_WRITER_BUFFERED_STREAM'):
                SynchronousWriter(stream)
        finally:
            stream.close()

    def test_failed_thread_handle_creation_preserves_error_and_allows_no_io_cleanup(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        original = WriterNativeError('CONTROL_DUPLICATE_FAILURE: 5')
        try:
            with patch.object(writer._kernel, 'duplicate_current_thread', side_effect=original):
                with self.assertRaisesRegex(WriterNativeError, 'CONTROL_DUPLICATE_FAILURE: 5'):
                    writer.start(b'never-written', time.monotonic() + 2)
            outcome = writer.join(time.monotonic() + 2)
            self.assertIs(outcome.error, original)
            self.assertFalse(outcome.native_thread_exited, 'no duplicate existed to observe natively')
            self.assertTrue(outcome.joined)
            self.assertEqual(writer.join(time.monotonic() - 1), outcome)
            self.assertFalse(writer.write_started.is_set())
            self.assertIsNone(writer._thread_handle)
            self.assertEqual(bytes(stream.data), b'')
            writer.close_stream()
            self.assertTrue(stream.closed)
        finally:
            # Only this fault-injected pre-I/O thread: no native duplicate or I/O exists.
            if writer._thread is not None:
                writer._thread.join(timeout=2)
                self.assertFalse(writer.is_alive())
            stream.close()

    def test_thread_creation_failure_never_transfers_stream_or_starts_io(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        original = OSError('CONTROL_THREAD_START_FAILURE')
        try:
            with patch.object(threading.Thread, 'start', side_effect=original):
                with self.assertRaisesRegex(OSError, 'CONTROL_THREAD_START_FAILURE') as caught:
                    writer.start(b'never-written', time.monotonic() + 2)
            self.assertIs(caught.exception, original)
            self.assertIsNone(writer._thread, 'failed creation cannot leave an unjoinable Thread')
            self.assertIsNone(writer._thread_handle)
            self.assertFalse(writer.write_started.is_set())
            self.assertEqual(bytes(stream.data), b'')
        finally:
            stream.close()  # No thread exists: caller retains the untransferred stream.

    def test_failed_start_handle_retirement_cannot_be_reported_as_success(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        duplicate = writer._kernel.duplicate_current_thread
        def cancel_before_publication():
            handle = duplicate()
            writer.closing.set()
            return handle
        try:
            with patch.object(writer._kernel, 'duplicate_current_thread', side_effect=cancel_before_publication), \
                 patch.object(writer._kernel, 'close', side_effect=WriterNativeError('CONTROL_START_CLOSE_FAILURE')):
                with self.assertRaisesRegex(WriterCancelled, 'E_WRITER_CANCELLED_BEFORE_WRITE') as caught:
                    writer.start(b'never-written', time.monotonic() + 2)
            self.assertIn('CONTROL_START_CLOSE_FAILURE', str(caught.exception.__notes__))
            self.assertFalse(writer.write_started.is_set())
            self.assertEqual(bytes(stream.data), b'')
            self.assertIsNotNone(writer._thread_handle, 'failed native close stays explicit cleanup debt')
            with self.assertRaises(WriterStillAlive):
                writer.close_stream()
            outcome = writer.join(time.monotonic() + 2)
            self.assertIs(outcome.error, caught.exception)
            self.assertTrue(outcome.native_thread_exited)
            self.assertTrue(writer._handle_closed)
            writer.close_stream()
        finally:
            if writer._thread is not None and not writer.has_joined:
                writer.join(time.monotonic() + 2)
            writer.close_stream()

    def test_payload_preparation_past_deadline_cannot_launch_or_write(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        until = time.monotonic() + .02
        class SlowPayload:
            def __bytes__(self):
                # Deliberate test-only conversion delay, not a repair sleep.
                threading.Event().wait(max(0, until - time.monotonic()) + .02)
                return b'never-written'
        try:
            with self.assertRaises(WriterDeadline):
                writer.start(SlowPayload(), until)
            self.assertIsNone(writer._thread)
            self.assertEqual(bytes(stream.data), b'')
        finally:
            if writer._thread is not None:
                writer._thread.join(timeout=2)  # Test-only observation before fault cleanup.
                writer.join(time.monotonic() + 2)
                writer.close_stream()
            else:
                stream.close()

    def test_readiness_after_start_timeout_never_transfers_handle_or_starts_io(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        entered, release = threading.Event(), threading.Event()
        ready_set = writer._ready.set
        def gated_ready():
            entered.set()
            if not release.wait(2):
                raise TimeoutError('CONTROL_READY_RELEASE')
            ready_set()
        deadline = time.monotonic() + .05
        try:
            with patch.object(writer._ready, 'set', side_effect=gated_ready):
                with self.assertRaises(WriterDeadline):
                    writer.start(b'never-written', deadline)
                self.assertTrue(entered.is_set())
                with self.assertRaisesRegex(WriterNativeError, 'E_WRITER_START_NOT_ACCEPTED'):
                    writer.request_cancel(time.monotonic() + 1)
                release.set()
                writer._thread.join(timeout=2)  # Observe only the test-injected stall finishing.
            self.assertFalse(writer.is_alive())
            self.assertFalse(writer.write_started.is_set())
            self.assertEqual(bytes(stream.data), b'')
            self.assertTrue(writer._handle_closed)
            self.assertIsNone(writer._thread_handle)
            outcome = writer.join(deadline)
            self.assertFalse(outcome.native_thread_exited)
            self.assertTrue(outcome.joined)
            writer.close_stream()
        finally:
            release.set()
            if writer._thread is not None and not writer.has_joined:
                writer._thread.join(timeout=2)
                writer.join(time.monotonic() + 2)
            writer.close_stream()

    def test_retiring_worker_handle_cannot_be_accepted_cancelled_or_waited_concurrently(self):
        stream = _PartialStream()
        writer = SynchronousWriter(stream)
        release = threading.Event()
        duplicate = writer._kernel.duplicate_current_thread
        def cancelled_duplicate():
            handle = duplicate()
            writer.closing.set()
            return handle
        def gated_failed_close(_handle):
            writer._ready.set()  # Force simultaneous readiness while retirement owns the handle.
            if not release.wait(2):
                raise TimeoutError('CONTROL_RETIRE_RELEASE')
            raise WriterNativeError('CONTROL_RETIRE_CLOSE_FAILURE')
        try:
            with patch.object(writer._kernel, 'duplicate_current_thread', side_effect=cancelled_duplicate), \
                 patch.object(writer._kernel, 'close', side_effect=gated_failed_close), \
                 patch.object(writer._kernel, 'cancel', side_effect=AssertionError('cancelled worker-owned handle')), \
                 patch.object(writer._kernel, 'wait', side_effect=AssertionError('waited worker-owned handle')):
                with self.assertRaises(WriterCancelled):
                    writer.start(b'never-written', time.monotonic() + 1)
                self.assertEqual(getattr(writer, '_ownership', None), 'RETIRING_WORKER')
                with self.assertRaisesRegex(WriterNativeError, 'E_WRITER_START_NOT_ACCEPTED'):
                    writer.request_cancel(time.monotonic() + 1)
                with self.assertRaises(WriterDeadline):
                    writer.cancel_and_join(time.monotonic() + .02)
                self.assertFalse(writer.write_started.is_set())
                self.assertEqual(bytes(stream.data), b'')
                self.assertFalse(writer.has_joined)
                release.set()
                writer._thread.join(timeout=2)
            self.assertEqual(writer._ownership, 'RETIRE_FAILED_WORKER')
            self.assertIn('CONTROL_RETIRE_CLOSE_FAILURE', str(writer._error.__notes__))
            outcome = writer.join(time.monotonic() + 2)
            self.assertTrue(outcome.native_thread_exited)
            writer.close_stream()
        finally:
            release.set()
            if writer._thread is not None and not writer.has_joined:
                writer._thread.join(timeout=2)
                writer.join(time.monotonic() + 2)
            writer.close_stream()

    def test_boolean_write_count_cannot_be_reported_as_sent_bytes(self):
        class InvalidCount(_PartialStream):
            def write(self, data):
                return True
        self.writer = SynchronousWriter(InvalidCount())
        self.writer.start(b'not-sent', time.monotonic() + 2)
        outcome = self.writer.join(time.monotonic() + 2)
        self.assertIsInstance(outcome.error, WriterError)
        self.assertEqual(bytes(self.writer.stream.data), b'')
        self.writer.close_stream()

    def test_invalid_deadlines_are_rejected_before_starting_a_thread(self):
        self.writer = SynchronousWriter(_PartialStream())
        for until in (True, None, 'later', float('nan'), float('inf')):
            with self.subTest(until=until), self.assertRaisesRegex(WriterError, 'E_WRITER_DEADLINE'):
                self.writer.start(b'no-thread', until)
            self.assertIsNone(self.writer._thread)
        with self.assertRaises(WriterDeadline):
            self.writer.start(b'expired', time.monotonic()-1)
        self.assertIsNone(self.writer._thread)

    def test_native_close_failure_stays_visible_and_does_not_retire_handle(self):
        self.writer = SynchronousWriter(_PartialStream())
        self.writer.start(b'completed', time.monotonic() + 2)
        original = self.writer._kernel.close
        with patch.object(self.writer._kernel, 'close', side_effect=WriterNativeError('CONTROL_CLOSE_FAILURE')):
            with self.assertRaisesRegex(WriterNativeError, 'CONTROL_CLOSE_FAILURE'):
                self.writer.join(time.monotonic() + 2)
        self.assertFalse(self.writer.has_joined)
        self.assertFalse(self.writer._handle_closed)
        with self.assertRaises(WriterStillAlive):
            self.writer.close_stream()
        outcome = self.writer.join(time.monotonic() + 2)
        self.assertTrue(outcome.native_thread_exited)
        self.assertTrue(self.writer.has_joined)
        self.assertTrue(self.writer._handle_closed)
        self.writer.close_stream()

    def test_cancellation_api_failure_is_not_success_and_keeps_original_code(self):
        from knowledge_bridge.windows_writer import CancelObservation
        stream = _GateStream()
        self.addCleanup(stream.release.set)
        self.writer = SynchronousWriter(stream)
        self.writer.start(b'one-attempt', time.monotonic() + 2)
        self.assertTrue(stream.entered.wait(2))
        with patch.object(self.writer._kernel, 'cancel', return_value=CancelObservation('failed', 5, 0.0)):
            with self.assertRaisesRegex(WriterNativeError, 'CancelSynchronousIo: 5'):
                self.writer.request_cancel(time.monotonic() + 2)
        self.assertTrue(self.writer.is_alive())
        with self.assertRaises(WriterStillAlive):
            self.writer.close_stream()
        self.assertEqual(self.writer.timing_snapshot()['cancel_requests'][-1]['error_code'], 5)
        stream.release.set()
        outcome = self.writer.join(time.monotonic() + 2)
        self.assertIsInstance(outcome.error, WriterCancelled)
        self.writer.close_stream()


if __name__ == '__main__':
    unittest.main()
