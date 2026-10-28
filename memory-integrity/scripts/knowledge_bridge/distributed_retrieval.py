"""Bounded two-process shard coordinator; source authority stays in the bridge."""
from concurrent.futures import ThreadPoolExecutor
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

from . import contracts as c
from . import BRIDGE_VERSION, SEMANTICA_VERSION, SEMANTICA_REVISION
from .advanced_retrieval import _bounds, traverse
from .worker_client import WorkerClient


def owner(ident):
    return int(c.digest(ident.encode('utf-8')), 16) % 2


def validate_reply(reply, lane, sequence, lease, request_digest):
    if not isinstance(reply, dict) or reply.get('ok') is not True:
        raise ValueError('E_DISTRIBUTED_WORKER: ' + str(reply.get('error', 'invalid response') if isinstance(reply, dict) else 'invalid response'))
    if any(reply.get(k) != v for k, v in {'schema_version': 1, 'lane': lane,
           'sequence': sequence, 'lease': lease, 'request_digest': request_digest}.items()):
        raise ValueError('E_DISTRIBUTED_REPLY_BINDING')
    c.keys(reply, {'schema_version', 'lane', 'sequence', 'lease', 'request_digest',
                   'ok', 'result', 'identity'}, 'shard reply')
    identity = reply['identity']
    if identity.get('bridge_version') != BRIDGE_VERSION or identity.get('semantica_version') != SEMANTICA_VERSION or identity.get('revision') != SEMANTICA_REVISION or identity.get('answer_generation') is not False:
        raise ValueError('E_DISTRIBUTED_RUNTIME_PIN')
    return reply['result']


class _Session:
    def __init__(self, python, lane, lease, deadline):
        self.lane, self.lease, self.deadline, self.sequence = lane, lease, deadline, 0
        self.directory = self.output = self.reader = self.errors = None
        self.process = self.writer = None
        self._tree = None
        self._windows_owned = False
        self._stop_attempted = self._stopped = self._closed = False
        self.offset = 0
        env = {k: v for k, v in os.environ.items() if k.upper() in {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL'}}
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        try:
            self.directory = tempfile.TemporaryDirectory()
            self.output = open(Path(self.directory.name) / 'output', 'w+b')
            self.reader = open(Path(self.directory.name) / 'output', 'rb')
            self.errors = tempfile.TemporaryFile()
            # The already-owned directory also contains relative startup caches.
            args = [str(python), '-B', str(Path(__file__).absolute().with_name('distributed_worker.py'))]
            options = dict(stdin=subprocess.PIPE, stdout=self.output, stderr=self.errors,
                           env=env, cwd=self.directory.name)
            if os.name == 'nt':
                from .windows_owned_process import launch_current
                self._tree = launch_current(subprocess.Popen, python, Path(args[2]),
                                            deadline=deadline, **options)
                self.process = self._tree.process
                self._windows_owned = True
            else:
                self.process = subprocess.Popen(args, **options)
        except BaseException as original:
            if getattr(original, 'owned_cleanup_complete', None) is False:
                self._tree = original.owned_process_owner
                self.process = getattr(self._tree, 'process', None)
                self._windows_owned = True
                self._retain_resources(original)
                raise
            try:
                self.close()
            except Exception as cleanup:
                original.add_note('E_DISTRIBUTED_CONSTRUCTION_CLEANUP: ' + repr(cleanup))
            raise

    def request(self, op, payload):
        request = {'schema_version': 1, 'lane': self.lane, 'sequence': self.sequence,
                   'lease': self.lease, 'op': op, 'payload': payload}
        raw = c.canonical(request) + b'\n'
        if len(raw) > c.MAX_MESSAGE:
            raise ValueError('E_DISTRIBUTED_MESSAGE_LIMIT')
        if getattr(self, '_windows_owned', False):
            from .windows_writer import SynchronousWriter, WriterDeadline
            self.writer = SynchronousWriter(self.process.stdin)
            try:
                self.writer.start(raw, self.deadline)
                while not self.writer.done.wait(.005):
                    if time.monotonic() > self.deadline:
                        raise WriterDeadline('E_WRITER_REQUEST_DEADLINE')
                outcome = self.writer.join(self.deadline)
            except WriterDeadline as error:
                raise ValueError('E_DISTRIBUTED_WORKER_TIMEOUT') from error
            if outcome.error is not None:
                raise ValueError('E_DISTRIBUTED_WORKER: terminated') from outcome.error
        else:
            written, write_errors = threading.Event(), []
            def write():
                try:
                    self.process.stdin.write(raw); self.process.stdin.flush()
                except (OSError, ValueError) as exc:
                    write_errors.append(exc)
                finally:
                    written.set()
            # Preserve the POSIX path. Native Windows cancellation is separate.
            self.writer = threading.Thread(target=write, daemon=True)
            self.writer.start()
            while not written.wait(.005):
                if time.monotonic() > self.deadline:
                    raise ValueError('E_DISTRIBUTED_WORKER_TIMEOUT')
            self.writer.join(timeout=max(0, self.deadline - time.monotonic()))
            if self.writer.is_alive():
                raise ValueError('E_DISTRIBUTED_WORKER_TIMEOUT')
            if write_errors:
                raise ValueError('E_DISTRIBUTED_WORKER: terminated') from write_errors[0]
        while True:
            if time.monotonic() > self.deadline:
                raise ValueError('E_DISTRIBUTED_WORKER_TIMEOUT')
            size = os.fstat(self.output.fileno()).st_size
            if size > 4 * c.MAX_MESSAGE or size - self.offset > c.MAX_MESSAGE or os.fstat(self.errors.fileno()).st_size > 65536:
                raise ValueError('E_DISTRIBUTED_OUTPUT_LIMIT')
            self.reader.seek(self.offset)
            raw_reply = self.reader.read(c.MAX_MESSAGE + 1)
            if b'\n' in raw_reply:
                line, trailing = raw_reply.split(b'\n', 1)
                if trailing:
                    raise ValueError('E_DISTRIBUTED_UNSOLICITED_REPLY')
                self.offset += len(line) + 1
                result = validate_reply(c.loads(line), self.lane, self.sequence,
                                        self.lease, c.digest(c.canonical(request)))
                self.sequence += 1
                return result
            if self.process.poll() is not None:
                raise ValueError('E_DISTRIBUTED_WORKER: terminated before response')
            time.sleep(.005)

    def stop(self):
        """Reap our owned tree and writer before disposing any output handles."""
        if self._stop_attempted:
            if not self._stopped:
                raise ValueError('E_DISTRIBUTED_STOP_INCOMPLETE')
            return
        self._stop_attempted = True
        if getattr(self, '_windows_owned', False):
            self._stop_owned(time.monotonic() + 5)
            self._stopped = True
            return
        if getattr(self, '_tree', None) is not None:
            from .windows_job import stop
            stop(self.process, self._tree, self.writer,
                 graceful=time.monotonic() < self.deadline)
            self._stopped = True
            return
        if self.process is not None:
            if self.process.poll() is None:
                self.process.kill()
            self.process.wait(timeout=5)
        if self.writer is not None:
            self.writer.join(timeout=5)
            if self.writer.is_alive():
                raise ValueError('E_DISTRIBUTED_WRITER_STILL_ALIVE')
        self._stopped = True

    def _stop_owned(self, until):
        """Independent cancel, process exit and writer join share ONE allowance."""
        failures = []
        active_writer = self.writer is not None and self.writer.is_alive()
        if active_writer:
            try:
                self.writer.request_cancel(until)
            except Exception as error:
                failures.append(error)
        tree_stopped = False
        graceful = not active_writer and not failures and time.monotonic() < self.deadline
        if graceful:
            try:
                if self.writer is not None:
                    self.writer.join(until)
                    self.writer.close_stream()
                elif self.process.stdin is not None:
                    self.process.stdin.close()
                self._tree.wait(until)
                tree_stopped = True
            except Exception as error:
                failures.append(error)
        if not tree_stopped:
            try:
                self._tree.stop(until)
                tree_stopped = True
            except Exception as error:
                failures.append(error)
        # A cancellation or process-stop error cannot abandon the other owner.
        if self.writer is not None:
            try:
                if active_writer:
                    self.writer.cancel_and_join(until)
                elif not self.writer.has_joined:
                    self.writer.join(until)
            except Exception as error:
                failures.append(error)
        if tree_stopped:
            try:
                self._tree.release()
            except Exception as error:
                failures.append(error)
        if failures:
            for secondary in failures[1:]:
                failures[0].add_note('E_DISTRIBUTED_STOP_CLEANUP: ' + repr(secondary))
            raise failures[0]

    def close(self):
        if self._closed:
            return
        try:
            self.stop()
        except BaseException as error:
            if getattr(self, '_windows_owned', False):
                self._retain_resources(error)
            raise
        failures = []
        streams = [self.reader, self.output, self.errors]
        closers = [stream.close for stream in streams if stream is not None]
        if getattr(self, '_windows_owned', False) and self.writer is not None:
            closers.append(self.writer.close_stream)
        elif self.process is not None and self.process.stdin is not None:
            closers.append(self.process.stdin.close)
        for close in closers:
            if close is not None:
                try:
                    close()
                except Exception as exc:
                    failures.append(exc)
        # Do not remove a directory while one of its handles failed to close.
        if failures:
            error = ValueError('E_DISTRIBUTED_STREAM_CLEANUP')
            for failure in failures:
                error.add_note(repr(failure))
            if getattr(self, '_windows_owned', False):
                self._retain_resources(error)
            raise error from failures[0]
        if self.directory is not None:
            self.directory.cleanup()
        self._closed = True

    def _retain_resources(self, error):
        """Fail closed: a later TemporaryDirectory finalizer must not erase debt."""
        finalizer = getattr(self.directory, '_finalizer', None)
        if finalizer is not None:
            finalizer.detach()
        error.add_note('E_DISTRIBUTED_RESOURCES_RETAINED: ' +
                       str(getattr(self.directory, 'name', None)))


class DistributedClient:
    def __init__(self, python, timeout=120):
        checked = WorkerClient(python, timeout=timeout)
        self.python, self.timeout = checked.python, checked.timeout
        self.executable_digest = checked.executable_digest
        self.execution_proof = {}

    def _seed_phase(self, sessions, payload, vectors, query):
        with ThreadPoolExecutor(max_workers=2) as executor:
            replies = list(executor.map(lambda s: s.request('seed', {'seeds': payload['seeds']}), sessions))
        found = []
        table = {n['id']: vector for n, vector in zip(payload['nodes'], vectors)}
        seen = set()
        for lane, reply in enumerate(replies):
            c.keys(reply, {'seeds'}, 'distributed seeds')
            if not isinstance(reply['seeds'], list) or len(reply['seeds']) > payload['seeds']:
                raise ValueError('E_DISTRIBUTED_SEED_LIMIT')
            for item in reply['seeds']:
                c.keys(item, {'id', 'score'}, 'distributed seed')
                if item['id'] in seen:
                    raise ValueError('E_DISTRIBUTED_SEED_DUPLICATE')
                seen.add(item['id'])
                if item['id'] not in table or owner(item['id']) != lane:
                    raise ValueError('E_DISTRIBUTED_FOREIGN_OWNER')
                score = float(item['score'])
                if not math.isfinite(score) or not -1.00001 <= score <= 1.00001:
                    raise ValueError('E_SCORE')
                vector = table[item['id']]
                expected = math.fsum(a * b for a, b in zip(vector, query)) / (math.hypot(*vector) * math.hypot(*query))
                if abs(expected - score) > 1e-8:
                    raise ValueError('E_DISTRIBUTED_SEED_SCORE')
                found.append((item['id'], score))
        return sorted(found, key=lambda p: (-p[1], p[0]))[:payload['seeds']]

    def __call__(self, payload):
        required = {'nodes', 'edges', 'query_text', 'embedding_mode', 'direction', 'seeds',
                    'max_hops', 'max_visits', 'max_results', 'generation_lease'}
        if isinstance(payload, dict) and 'vector_override' in payload:
            required.add('vector_override')
        c.keys(payload, required, 'distributed query')
        _bounds(payload['direction'], payload['seeds'], payload['max_hops'], payload['max_visits'], payload['max_results'])
        c.sha(payload['generation_lease'])
        if c.digest(self.python.read_bytes()) != self.executable_digest:
            raise ValueError('E_WORKER_EXECUTABLE_DRIFT')
        deadline = time.monotonic() + self.timeout
        sessions = []
        self.execution_proof = {}
        try:
            for lane in range(2):
                sessions.append(_Session(self.python, lane, payload['generation_lease'], deadline))
            self.execution_proof['worker_pids'] = [s.process.pid for s in sessions]
            fit_payload = {k: payload[k] for k in ('nodes', 'edges', 'query_text', 'embedding_mode')}
            if 'vector_override' in payload:
                fit_payload['vector_override'] = payload['vector_override']
            fit = sessions[0].request('fit', fit_payload)
            c.keys(fit, {'vectors', 'query', 'metadata'}, 'shared fit')
            vectors, query, metadata = fit['vectors'], fit['query'], fit['metadata']
            fit_digest = c.digest(c.canonical(fit))
            shards = []
            for lane, session in enumerate(sessions):
                pairs = [(n, v) for n, v in zip(payload['nodes'], vectors) if owner(n['id']) == lane]
                local = {n['id'] for n, _ in pairs}
                shard = {'nodes': [n for n, _ in pairs], 'vectors': [v for _, v in pairs],
                         'edges': [e for e in payload['edges'] if e['subject'] in local or e['object'] in local],
                         'query': query, 'direction': payload['direction'], 'fit_digest': fit_digest}
                reply = session.request('initialize', shard)
                expected = c.digest(c.canonical(shard))
                if reply != {'shard_digest': expected, 'node_count': len(local)}:
                    raise ValueError('E_DISTRIBUTED_SHARD_BINDING')
                shards.append(expected)
            seeds = self._seed_phase(sessions, payload, vectors, query)
            table = {n['id']: n for n in payload['nodes']}
            edges = {e['id']: e for e in payload['edges']}
            def neighbors(ident):
                reply = sessions[owner(ident)].request('neighbors', {'id': ident})
                c.keys(reply, {'neighbors'}, 'distributed neighbors')
                checked = []
                for target, edge_id in reply['neighbors']:
                    edge = edges.get(edge_id)
                    if target not in table or edge is None:
                        raise ValueError('E_DISTRIBUTED_FOREIGN_EDGE')
                    outbound = edge['subject'] == ident and edge['object'] == target
                    inbound = edge['object'] == ident and edge['subject'] == target
                    if not ((outbound and payload['direction'] in {'outgoing', 'both'}) or (inbound and payload['direction'] in {'incoming', 'both'})):
                        raise ValueError('E_PATH_EDGE')
                    checked.append((target, edge_id))
                expected = set()
                for edge in edges.values():
                    if edge['subject'] == ident and payload['direction'] in {'outgoing', 'both'}:
                        expected.add((edge['object'], edge['id']))
                    if edge['object'] == ident and payload['direction'] in {'incoming', 'both'}:
                        expected.add((edge['subject'], edge['id']))
                if checked != sorted(expected):
                    raise ValueError('E_DISTRIBUTED_NEIGHBOR_COVERAGE')
                return checked
            results, limits = traverse(seeds, neighbors, payload['max_hops'], payload['max_visits'], payload['max_results'])
            return {'results': results, 'limits_reached': limits, 'embedding_metadata': metadata,
                    'diagnostics': {'strategy': 'local', 'execution': 'distributed-local',
                                    'qualification_scope': 'LOCAL_TWO_PROCESS_SHARDED',
                                    'shards': 2, 'partition_algorithm': 'sha256-node-id-mod2',
                                    'generation_lease': payload['generation_lease'],
                                    'fit_digest': fit_digest, 'shard_digests': shards,
                                    'semantic_truth': 'UNVERIFIED', 'provider_calls': 0}}
        finally:
            original, cleanup_errors = sys.exception(), []
            # A sibling may have inherited an owned handle. Stop the entire
            # owned process set before closing handles/removing directories.
            for session in sessions:
                try:
                    session.stop()
                except Exception as exc:
                    cleanup_errors.append(exc)
            for session in sessions:
                try:
                    session.close()
                except Exception as exc:
                    cleanup_errors.append(exc)
            self.execution_proof['workers_after_close'] = [{'pid': s.process.pid, 'alive': s.process.poll() is None} for s in sessions]
            if cleanup_errors:
                if original is not None:
                    for error in cleanup_errors:
                        original.add_note('E_DISTRIBUTED_CLEANUP: ' + repr(error))
                else:
                    error = ValueError('E_DISTRIBUTED_CLEANUP')
                    for failure in cleanup_errors:
                        error.add_note(repr(failure))
                    raise error from cleanup_errors[0]

