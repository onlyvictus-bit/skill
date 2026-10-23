"""Actual selected worker cwd/reaping/cleanup observation, not retained-temp fiction.

Only fresh test-owned temporary directories are cleaned. Bytes of files seen
before cleanup are copied to retained snapshots; original data is never removed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

from gate1_validation import inventory, new_workspace, ordinary, require, save


def execute(source, worker, output):
    new_workspace(output, [source])
    scratch = output/'scratch';scratch.mkdir()
    snapshots = output/'snapshots';snapshots.mkdir()
    tempfile.tempdir = str(scratch)
    os.environ.update(TEMP=str(scratch), TMP=str(scratch), TMPDIR=str(scratch),
                      PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path[:0] = [str(source/'memory-integrity/scripts'), str(source/'memory-integrity/tests_v2')]
    from knowledge_bridge.worker_client import WorkerClient
    from knowledge_bridge.distributed_retrieval import DistributedClient
    from test_knowledge_advanced import fixture
    directories, processes = [], []
    original_directory, original_popen = tempfile.TemporaryDirectory, subprocess.Popen
    class ObservedDirectory(original_directory):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.observation = {'path': self.name, 'removed': False, 'files': {}}
            directories.append(self.observation)
            require(ordinary(Path(self.name)).resolve(strict=True).is_relative_to(scratch), 'E_G1_OWNED_CWD')

        def cleanup(self):
            path = Path(self.name)
            if path.exists():
                observed = inventory(path)
                self.observation['files'] = observed
                target = snapshots/str(directories.index(self.observation));target.mkdir()
                for relative, digest in observed.items():
                    destination = target/relative;destination.parent.mkdir(parents=True, exist_ok=True)
                    with destination.open('xb') as stream:
                        stream.write((path/relative).read_bytes())
                require(inventory(target) == observed, 'E_G1_RETAIN_BEFORE_CLEANUP')
            super().cleanup()  # REAL cleanup, not the retained-suite no-op.
            self.observation['removed'] = not path.exists()

    def observed_popen(*args, **kwargs):
        argv = args[0] if args else kwargs['args']
        # Observe actual selected Python children, not production's taskkill
        # fallback. Never change that fallback's argv or return value.
        if Path(str(argv[0])).absolute() != worker.absolute():
            return original_popen(*args, **kwargs)
        cwd = ordinary(Path(kwargs['cwd'])).resolve(strict=True)
        require(cwd.is_relative_to(scratch) and cwd != scratch, 'E_G1_WORKER_CWD')
        process = original_popen(*args, **kwargs)
        processes.append((process, str(cwd)))
        return process

    def audit(event, values):
        if event in ('os.remove', 'os.rmdir', 'shutil.rmtree'):
            candidate = Path(os.fsdecode(values[0])).absolute()
            require(candidate != scratch and candidate.resolve().is_relative_to(scratch), 'E_G1_CLEANUP_SCOPE')
            ordinary(candidate)
            if candidate.is_file():
                require(candidate.stat().st_nlink == 1, 'E_G1_LINKED_CLEANUP')
            require(len(values) < 2 or values[1] in (None, -1), 'E_G1_DIRFD_CLEANUP')
        if event in ('socket.connect', 'socket.bind', 'socket.getaddrinfo'):
            raise PermissionError('E_G1_NO_NETWORK')
        if event == 'subprocess.Popen' and Path(str(values[0])).name.lower() in ('bd', 'bd.exe', 'dolt', 'dolt.exe', 'pip', 'pip.exe'):
            raise PermissionError('E_G1_NO_NATIVE_OR_INSTALL')
    sys.addaudithook(audit)
    tempfile.TemporaryDirectory, subprocess.Popen = ObservedDirectory, observed_popen
    receipt = {'status': 'PARTIAL_OR_FAILED', 'boundaries': [], 'directories': directories,
               'all_reaped': False, 'failure': None, 'producer_authentication': False,
               'release_ready': False, 'native_execution': False}
    try:
        result = WorkerClient(worker, timeout=60)({'op': 'handshake'})
        require(result['ok'] is True, 'E_G1_SINGLE_POSITIVE')
        receipt['single_reply'] = result
        receipt['boundaries'].append('single')
        nodes, edges = fixture()
        payload = {'nodes': nodes, 'edges': edges, 'query_text': 'alpha validation',
                   'embedding_mode': 'lexical', 'direction': 'outgoing', 'seeds': 1,
                   'max_hops': 2, 'max_visits': 100, 'max_results': 50, 'generation_lease': 'a'*64}
        client = DistributedClient(worker, timeout=60)
        result = client(payload)
        require(result['results'] and len(set(client.execution_proof['worker_pids'])) == 2,
                'E_G1_REAL_TWO_WORKERS')
        receipt['shard_reply'] = result
        receipt['boundaries'].append('shard')
        require(len(directories) >= 3 and all(row['removed'] for row in directories), 'E_G1_CLEANUP_INCOMPLETE')
        receipt['all_reaped'] = bool(processes) and all(process.poll() is not None for process, _ in processes)
        require(receipt['all_reaped'], 'E_G1_UNREAPED_WORKER')
        receipt['processes'] = [{'pid': process.pid, 'cwd': cwd, 'returncode': process.returncode}
                                for process, cwd in processes]
        receipt['status'] = 'PASS_REAL_WORKER_CWD_AND_CLEANUP'
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        tempfile.TemporaryDirectory, subprocess.Popen = original_directory, original_popen
        save(output/'Receipt.json', receipt)
    print(json.dumps({'status': receipt['status'], 'failure': receipt['failure']}))
    return 0 if receipt['status'] == 'PASS_REAL_WORKER_CWD_AND_CLEANUP' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'worker', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    sys.exit(execute(args.source, args.worker, args.output))
