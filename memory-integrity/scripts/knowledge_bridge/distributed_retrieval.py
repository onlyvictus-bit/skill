"""Bounded two-process shard coordinator; source authority stays in the bridge."""
from concurrent.futures import ThreadPoolExecutor
import math
import os
from pathlib import Path
import subprocess
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
        self.directory = tempfile.TemporaryDirectory()
        self.output = open(Path(self.directory.name) / 'output', 'w+b')
        self.reader = open(Path(self.directory.name) / 'output', 'rb')
        self.errors = tempfile.TemporaryFile()
        self.offset = 0
        env = {k: v for k, v in os.environ.items() if k.upper() in {'PATH', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'LANG', 'LC_ALL'}}
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        self.process = subprocess.Popen([str(python), '-B', str(Path(__file__).with_name('distributed_worker.py'))],
                                        stdin=subprocess.PIPE, stdout=self.output, stderr=self.errors, env=env)

    def request(self, op, payload):
        request = {'schema_version': 1, 'lane': self.lane, 'sequence': self.sequence,
                   'lease': self.lease, 'op': op, 'payload': payload}
        raw = c.canonical(request) + b'\n'
        if len(raw) > c.MAX_MESSAGE:
            raise ValueError('E_DISTRIBUTED_MESSAGE_LIMIT')
        written, write_errors = threading.Event(), []
        def write():
            try:
                self.process.stdin.write(raw); self.process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                write_errors.append(exc)
            finally:
                written.set()
        # Pipe writes can block before reading starts; the same overall deadline
        # bounds them. Killing the child in finally releases a blocked writer.
        writer = threading.Thread(target=write, daemon=True)
        writer.start()
        while not written.wait(.005):
            if time.monotonic() > self.deadline:
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

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        if self.process.stdin:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        self.reader.close(); self.output.close(); self.errors.close()
        self.directory.cleanup()


class DistributedClient:
    def __init__(self, python, timeout=30):
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
            for session in sessions:
                session.close()
            self.execution_proof['workers_after_close'] = [{'pid': s.process.pid, 'alive': s.process.poll() is None} for s in sessions]

