"""Owned-resource regressions; no numerical/native worker or file deletion."""
import builtins
import io
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from knowledge_bridge import contracts as c
from knowledge_bridge import distributed_retrieval as d


class Process:
    def __init__(self): self.alive = True
    def poll(self): return None if self.alive else 0


class Session:
    def __init__(self, lane, events, sessions, broken_close=False):
        self.lane, self.events, self.sessions = lane, events, sessions
        self.process = Process()
        self.process.pid = 100 + lane
        self.broken_close = broken_close
    def request(self, op, payload):
        raise ValueError('ORIGINAL_FIT_FAILURE')
    def stop(self):
        self.events.append(('stop', self.lane))
        self.process.alive = False
    def close(self):
        self.events.append(('close', self.lane))
        # Model the Windows no-delete-sharing constraint without deleting files.
        if any(s.process.alive for s in self.sessions):
            raise PermissionError('sibling retains an output handle')
        if self.broken_close:
            raise OSError('OWNED_STREAM_CLOSE_FAILURE')


class ProcessLifecycle(unittest.TestCase):
    def client(self):
        client = object.__new__(d.DistributedClient)
        client.python, client.timeout = Path(sys.executable), 1
        client.executable_digest = c.digest(client.python.read_bytes())
        client.execution_proof = {}
        return client

    def payload(self):
        return {'nodes': [], 'edges': [], 'query_text': 'source',
                'embedding_mode': 'lexical', 'direction': 'outgoing', 'seeds': 1,
                'max_hops': 0, 'max_visits': 10, 'max_results': 5,
                'generation_lease': 'a'*64}

    def failing_fit(self, broken_close=False):
        sessions, events = [], []
        def make(_python, lane, _lease, _deadline):
            item = Session(lane, events, sessions, broken_close and lane == 0)
            sessions.append(item)
            return item
        client = self.client()
        with patch.object(d, '_Session', side_effect=make):
            with self.assertRaisesRegex(ValueError, 'ORIGINAL_FIT_FAILURE') as caught:
                client(self.payload())
        return client, sessions, events, caught.exception

    def test_every_owned_process_stops_before_any_resource_disposal(self):
        client, sessions, events, _ = self.failing_fit()
        self.assertEqual(events, [('stop',0), ('stop',1), ('close',0), ('close',1)])
        self.assertTrue(all(not s.process.alive for s in sessions))
        self.assertEqual(client.execution_proof['workers_after_close'],
                         [{'pid':100,'alive':False},{'pid':101,'alive':False}])

    def test_one_close_failure_does_not_abandon_sibling_or_hide_original(self):
        _, sessions, events, error = self.failing_fit(broken_close=True)
        self.assertIn(('close',1), events)
        self.assertTrue(all(not s.process.alive for s in sessions))
        self.assertIn('OWNED_STREAM_CLOSE_FAILURE', '\n'.join(getattr(error, '__notes__', [])))

    def test_partial_process_creation_closes_already_opened_parent_streams(self):
        opened = []
        real_open = builtins.open
        def track(*args, **kwargs):
            stream = real_open(*args, **kwargs)
            opened.append(stream)
            return stream
        # The retained runner preserves this directory and its files.
        with patch.object(d, 'open', side_effect=track, create=True), \
                patch.object(d.subprocess, 'Popen', side_effect=OSError('PROCESS_CREATE_FAILED')):
            with self.assertRaisesRegex(OSError, 'PROCESS_CREATE_FAILED'):
                d._Session(sys.executable, 0, 'a'*64, 1)
        try:
            self.assertGreaterEqual(len(opened), 2)
            self.assertTrue(all(stream.closed for stream in opened),
                            'constructor leaked parent streams when Popen failed')
        finally:
            for stream in opened:
                stream.close()

    def test_cleanup_failure_after_success_is_not_returned_as_success(self):
        sessions, events = [], []
        class Successful(Session):
            def request(self, op, payload):
                if op == 'fit':
                    return {'vectors':[], 'query':[1.0], 'metadata':{}}
                if op == 'initialize':
                    return {'shard_digest':c.digest(c.canonical(payload)), 'node_count':0}
                raise AssertionError(op)
        def make(_python, lane, _lease, _deadline):
            session = Successful(lane, events, sessions, broken_close=lane == 0)
            sessions.append(session)
            return session
        client = self.client()
        with patch.object(d, '_Session', side_effect=make), \
                patch.object(client, '_seed_phase', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_CLEANUP'):
                client(self.payload())
        self.assertEqual(events, [('stop',0), ('stop',1), ('close',0), ('close',1)])
        self.assertTrue(all(not p['alive'] for p in client.execution_proof['workers_after_close']))

    def test_partial_second_creation_reaps_the_first_session(self):
        sessions, events = [], []
        def make(_python, lane, _lease, _deadline):
            if lane:
                raise OSError('SECOND_PROCESS_CREATE_FAILED')
            session = Session(lane, events, sessions)
            sessions.append(session)
            return session
        client = self.client()
        with patch.object(d, '_Session', side_effect=make):
            with self.assertRaisesRegex(OSError, 'SECOND_PROCESS_CREATE_FAILED'):
                client(self.payload())
        self.assertEqual(events, [('stop',0), ('close',0)])
        self.assertEqual(client.execution_proof['workers_after_close'], [{'pid':100,'alive':False}])

    def test_pipe_write_timeout_is_joined_before_handle_disposal(self):
        released, writing = threading.Event(), threading.Event()
        events = []
        class Pipe(io.BytesIO):
            def write(self, data):
                writing.set()
                if not released.wait(2):
                    raise OSError('TEST_WRITER_NOT_RELEASED')
                raise BrokenPipeError('owned child stopped')
            def close(self):
                events.append('stdin-close')
                super().close()
        class Child(Process):
            stdin = Pipe()
            def kill(self):
                events.append('kill')
                self.alive = False
                released.set()
            def wait(self, timeout):
                events.append('wait')
                return 0
        session = object.__new__(d._Session)
        session.lane, session.lease, session.sequence = 0, 'a'*64, 0
        session.deadline, session.offset = time.monotonic() - 1, 0
        session.process, session.writer = Child(), None
        session.reader, session.output, session.errors = io.BytesIO(), io.BytesIO(), io.BytesIO()
        session.directory = None
        session._stop_attempted = session._stopped = session._closed = False
        try:
            with self.assertRaisesRegex(ValueError, 'E_DISTRIBUTED_WORKER_TIMEOUT'):
                session.request('fit', {})
            self.assertTrue(writing.wait(1))
            session.close()
            self.assertFalse(session.writer.is_alive())
            self.assertEqual(events, ['kill','wait','stdin-close'])
            session.close()
            self.assertEqual(events, ['kill','wait','stdin-close'])
        finally:
            released.set()
            if session.writer is not None:
                session.writer.join(timeout=2)
