"""Combined cleanup contracts; real native lifetime controls live in companion tests."""
import io
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from knowledge_bridge import distributed_retrieval as d
from knowledge_bridge.windows_writer import WriterNativeError


@unittest.skipUnless(os.name == 'nt', 'Windows owned session contract')
class WindowsSession(unittest.TestCase):
    def session(self, *, cancel_failure=False, tree_failure=False):
        events, deadlines = [], []
        process = SimpleNamespace(pid=77, stdin=io.BytesIO(), poll=lambda: 0)
        failure = WriterNativeError('CONTROL_CANCEL_FAILURE')
        class Writer:
            has_joined = False
            alive = True
            def is_alive(self): return self.alive
            def request_cancel(self, until):
                events.append('cancel-request'); deadlines.append(until)
                if cancel_failure: raise failure
            def cancel_and_join(self, until):
                events.append('cancel-join'); deadlines.append(until)
                self.alive, self.has_joined = False, True
            def join(self, until):
                events.append('writer-join'); deadlines.append(until)
                self.has_joined = True
            def close_stream(self):
                if not self.has_joined: raise AssertionError('closed before writer join')
                events.append('stdin-close'); process.stdin.close()
        class Tree:
            proof = {'scope':'CONTROL_NOT_NATIVE_PROOF'}
            def stop(self, until):
                events.append('tree-stop'); deadlines.append(until)
                if tree_failure: raise OSError('CONTROL_TREE_EXIT_UNPROVEN')
            def wait(self, until):
                events.append('tree-wait'); deadlines.append(until)
            def release(self): events.append('tree-release')
        item = object.__new__(d._Session)
        item.process, item.writer, item._tree = process, Writer(), Tree()
        item._windows_owned = True
        item.deadline = time.monotonic()-1
        item.reader, item.output, item.errors = io.BytesIO(), io.BytesIO(), io.BytesIO()
        item.directory = SimpleNamespace(cleanup=lambda: events.append('directory-cleanup'))
        item._stop_attempted = item._stopped = item._closed = False
        return item, events, deadlines, failure

    def test_cancel_tree_exit_and_join_share_one_deadline_before_any_disposal(self):
        item, events, deadlines, _ = self.session()
        error = None
        try: item.stop()
        except Exception as caught: error = caught
        self.assertIsNone(error, str(error))
        self.assertEqual(events, ['cancel-request','tree-stop','cancel-join','tree-release'])
        self.assertEqual(len(set(deadlines)), 1, 'shutdown must not reset its five-second deadline')
        self.assertTrue(item._stopped)
        self.assertFalse(item.output.closed)
        item.close()
        self.assertIn('stdin-close', events)
        self.assertEqual(events[-1], 'directory-cleanup')
        self.assertTrue(item.process.stdin.closed)
        self.assertTrue(item._closed)

    def test_cancel_failure_does_not_abandon_owned_tree_or_hide_original(self):
        item, events, deadlines, original = self.session(cancel_failure=True)
        error = None
        try: item.stop()
        except Exception as caught: error = caught
        self.assertIs(error, original)
        self.assertIn('tree-stop', events)
        self.assertIn('cancel-join', events)
        self.assertFalse(item.writer.is_alive())
        self.assertEqual(len(set(deadlines)), 1)
        self.assertFalse(item._stopped)
        self.assertFalse(item.output.closed)
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_STOP_INCOMPLETE'):
            item.close()

    def test_unproven_process_exit_still_joins_writer_but_forbids_resource_disposal(self):
        item, events, deadlines, _ = self.session(tree_failure=True)
        error = None
        try: item.stop()
        except Exception as caught: error = caught
        self.assertIsInstance(error, OSError)
        self.assertIn('CONTROL_TREE_EXIT_UNPROVEN', str(error))
        self.assertIn('cancel-join', events)
        self.assertNotIn('tree-release', events)
        self.assertEqual(len(set(deadlines)), 1)
        self.assertFalse(item._stopped)
        self.assertFalse(item.output.closed)
        self.assertNotIn('directory-cleanup', events)

    def test_failed_close_retains_directory_instead_of_later_finalizer_deletion(self):
        item, events, _, _ = self.session(tree_failure=True)
        class Finalizer:
            detached = False
            def detach(self): self.detached = True
        finalizer = Finalizer()
        item.directory._finalizer = finalizer
        item.directory.name = 'controlled-retained-directory'
        with self.assertRaisesRegex(OSError, 'CONTROL_TREE_EXIT_UNPROVEN') as caught:
            item.close()
        self.assertTrue(finalizer.detached, 'failed shutdown must not schedule later directory deletion')
        self.assertIn('E_DISTRIBUTED_RESOURCES_RETAINED', str(caught.exception.__notes__))
        self.assertFalse(item.output.closed)
        self.assertNotIn('directory-cleanup', events)

    def test_unproven_constructor_cleanup_retains_all_parent_streams_and_original(self):
        streams = []
        finalizer = SimpleNamespace(detach=lambda: events.append('detach'))
        events = []
        directory = SimpleNamespace(name='controlled-owned-directory', _finalizer=finalizer,
                                    cleanup=lambda: events.append('directory-cleanup'))
        original = OSError('CONTROL_UNPROVEN_START_CLEANUP')
        original.owned_cleanup_complete = False
        original.owned_process_owner = SimpleNamespace(process=SimpleNamespace(pid=77))
        def failed_launch(*_args, **_kwargs):
            events.append('owned-launch')
            raise original
        def opened(*_args, **_kwargs):
            stream = io.BytesIO(); streams.append(stream); return stream
        fake_module = SimpleNamespace(launch_current=failed_launch)
        try:
            with patch.dict(sys.modules, {'knowledge_bridge.windows_owned_process': fake_module}), \
                 patch.object(d.tempfile, 'TemporaryDirectory', return_value=directory), \
                 patch.object(d.tempfile, 'TemporaryFile', side_effect=opened), \
                 patch.object(d, 'open', side_effect=opened, create=True), \
                 patch.object(d.subprocess, 'Popen', side_effect=OSError('CONTROL_OLD_PATH')):
                with self.assertRaises(OSError) as caught:
                    d._Session(sys.executable, 0, 'a'*64, time.monotonic()+2)
            self.assertIs(caught.exception, original)
            self.assertIn('owned-launch', events)
            self.assertIn('detach', events)
            self.assertNotIn('directory-cleanup', events)
            self.assertTrue(all(not stream.closed for stream in streams))
        finally:
            for stream in streams: stream.close()  # No native process exists in this fault control.


    def test_missing_start_owner_cannot_mask_original_cleanup_debt(self):
        events = []; streams = []
        directory = SimpleNamespace(name='controlled-no-owner',
            _finalizer=SimpleNamespace(detach=lambda: events.append('detach')),
            cleanup=lambda: events.append('cleanup'))
        original = OSError('CONTROL_NO_OWNER_START_DEBT')
        original.owned_cleanup_complete, original.owned_process_owner = False, None
        def fail(*_args, **_kwargs): raise original
        def opened(*_args, **_kwargs):
            item = io.BytesIO(); streams.append(item); return item
        try:
            with patch.dict(sys.modules, {'knowledge_bridge.windows_owned_process': SimpleNamespace(launch_current=fail)}), \
                 patch.object(d.tempfile, 'TemporaryDirectory', return_value=directory), \
                 patch.object(d.tempfile, 'TemporaryFile', side_effect=opened), \
                 patch.object(d, 'open', side_effect=opened, create=True):
                with self.assertRaises(OSError) as caught:
                    d._Session(sys.executable, 0, 'a'*64, time.monotonic()+2)
            self.assertIs(caught.exception, original)
            self.assertEqual(events, ['detach'])
            self.assertTrue(all(not stream.closed for stream in streams))
        finally:
            for stream in streams: stream.close()

    def test_post_stop_stream_close_failure_detaches_directory_finalizer(self):
        item, events, _, _ = self.session()
        item.stop()
        finalizer = SimpleNamespace(detach=lambda: events.append('detach'))
        item.directory._finalizer = finalizer; item.directory.name = 'controlled-stream-close-debt'
        def failed_close(): raise OSError('CONTROL_OUTPUT_CLOSE_DEBT')
        item.reader = SimpleNamespace(close=failed_close)
        with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_STREAM_CLEANUP') as caught:
            item.close()
        self.assertIn('CONTROL_OUTPUT_CLOSE_DEBT', str(caught.exception.__notes__))
        self.assertIn('detach', events)
        self.assertNotIn('directory-cleanup', events)
        self.assertFalse(item._closed)


if __name__ == '__main__': unittest.main()
