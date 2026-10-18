"""TEST_ONLY stateful model of the unavoidable native process boundary.

This consumes the actual builder SQL and its complete serialized binding and
receipt templates. It owns one evolving set of physical tables. It does not
override driver identity/authority/snapshot methods, consumer completion,
journal operations, or the verdict. It is NOT a SQL engine, a Dolt grammar
check, a native conflict test, or a source of trusted execution-cause proof.
"""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import patch

from hybrid_bridge import practical_race_controller as controller
from hybrid_bridge import practical_lease_backend as backend
from hybrid_bridge import practical_lease_sql as sql_builder
from hybrid_bridge import practical_race_alice as worker
from hybrid_bridge.practical_contract import LeasePracticalSelection


def hex_values(sql):
    return [bytes.fromhex(value).decode('utf-8')
            for value in re.findall(r'CONVERT\(0x([0-9a-f]+) USING utf8mb4\)', sql)]


class ModelProcess:
    next_pid = 4200

    def __init__(self, model, argv, **kwargs):
        ModelProcess.next_pid += 1
        self.pid = ModelProcess.next_pid
        self.model = model
        self.returncode = None
        self.thread = None
        self.error = None
        self.corrupted = False
        self.server = 'sql-server' in argv
        model.handles.append(self)
        if self.server:
            return
        assert argv[1:3] == ['-m', 'hybrid_bridge.practical_race_alice'], argv
        self.spec_path = Path(argv[-1])

        def execute():
            try:
                self.returncode = worker.run(self.spec_path)
                if model.fault == 'wrong_worker_operation':
                    spec = json.loads(self.spec_path.read_text())
                    path = Path(spec['outcome_path'])
                    original = path.read_text()
                    path.with_suffix('.original.json').write_text(original)
                    value = json.loads(original)
                    value['operation_id'] = 'foreign-worker-operation'
                    path.write_text(json.dumps(value))
            except BaseException as exc:
                self.error = repr(exc)
                self.returncode = 4

        self.thread = threading.Thread(target=execute, name='TEST_ONLY_alice_boundary')
        self.thread.start()

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        if self.thread is not None:
            self.model.resume.set()
            self.thread.join(timeout=min(timeout or 3, 3))
            if self.thread.is_alive():
                raise TimeoutError('TEST_ONLY worker did not finish')
            if self.model.fault == 'duplicate_dispatch' and not self.corrupted:
                # Fault injection into this retained TEST_ONLY companion DB:
                # append a syntactically chained but semantically duplicate
                # dispatch event. Production journal APIs remain unchanged.
                from complete_read_v2 import ledger
                spec = json.loads(self.spec_path.read_text())
                db = ledger.connect(spec['journal_path'])
                try:
                    row = db.execute("SELECT * FROM events WHERE kind='PRACTICAL_NATIVE_DISPATCHED' "
                                     'ORDER BY seq LIMIT 1').fetchone()
                    db.execute('BEGIN IMMEDIATE')
                    ledger._append(db, row['kind'], row['work_item_id'], row['detail'])
                    db.execute('COMMIT')
                finally:
                    db.close()
                self.corrupted = True
        return self.returncode

    def terminate(self):
        if self.server and self.model.fault == 'failed_cleanup':
            raise RuntimeError('TEST_ONLY owned handle refused termination')
        self.wait()
        self.returncode = 0

    def kill(self):
        self.terminate()


class StatefulNativeTransport:
    def __init__(self, root, schedule, fault=None):
        self.root = root
        self.schedule = schedule
        self.fault = fault
        self.tables = {}
        self.phase = 'fresh'
        self.trace = []
        self.handles = []
        self.dispatches = []
        self.held = threading.Event()
        self.resume = threading.Event()
        self.lock = threading.RLock()
        self.minted = 'c0dec0de-2026-4017-8017-000000000017'
        self.token = 100
        self.pending = None
        self.patches = []

    @property
    def selected(self):
        return LeasePracticalSelection.from_value(self.schedule['requests']['selection'])

    def __enter__(self):
        # Only physical runtime eligibility is substituted. All packet, type,
        # digest, prerequisite, dispatch, receipt and journal guards stay real.
        def native_boundary(selection):
            assert selection.dolt_sha256 == backend.DOLT_PIN
            assert Path(selection.scratch_root) == self.root

        def physical_preflight(engine, scratch_root, executable, expected):
            assert scratch_root == str(self.root)
            assert expected == backend.DOLT_PIN
            return {'engine': engine, 'scratch_root': scratch_root,
                    'dolt_executable': executable, 'dolt_sha256': expected,
                    'structural_only': True, 'TEST_ONLY': True}

        transport = SimpleNamespace(run=self.run, Popen=self.spawn,
                                    DEVNULL=subprocess.DEVNULL, PIPE=subprocess.PIPE,
                                    STDOUT=subprocess.STDOUT,
                                    CREATE_NO_WINDOW=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.patches = [patch.object(controller, 'subprocess', transport),
                        patch.object(backend, 'subprocess', transport),
                        patch.object(backend, '_native_boundary', native_boundary),
                        patch.object(controller, 'verify_engine', physical_preflight)]
        for item in self.patches:
            item.start()
        return self

    def __exit__(self, *unused):
        self.resume.set()
        for handle in self.handles:
            if handle.thread is not None:
                handle.thread.join(timeout=3)
                assert not handle.thread.is_alive(), 'TEST_ONLY worker leaked'
        for item in reversed(self.patches):
            item.stop()

    def spawn(self, argv, **kwargs):
        return ModelProcess(self, argv, **kwargs)

    def now(self):
        second = {'fresh': 0, 'bootstrapped': 0, 'registered': 0, 'seeded': 0,
                  'claimed': 1, 'alice_held': 1, 'transferred': 2,
                  'alice_finished': 3, 'positive': 4, 'disabled': 5}[self.phase]
        return '2026-10-14 10:00:%02d.600000' % second

    def _projection(self, sql, rows):
        fields = sql.split(' FROM ', 1)[0][len('SELECT '):].split(',')
        return [{field.strip().split('.')[-1]: row.get(field.strip().split('.')[-1])
                 for field in fields} for row in rows]

    def _record(self, event, **fields):
        self.trace.append(dict(event=event, phase=self.phase, **copy.deepcopy(fields)))

    def run(self, argv, **kwargs):
        assert kwargs.get('shell') is False
        assert argv[0] == self.selected.dolt_executable
        assert '--branch' in argv and argv[argv.index('--branch') + 1] == 'main'
        sql = argv[-1]
        if 'FROM information_schema.processlist' in sql:
            # Do not hold the modeled database mutex while waiting for the
            # worker to reach its separate session's paused dispatch.
            self.held.wait(timeout=2)
        if controller.BARRIER_COMMENT in sql and 'BEGIN NOT ATOMIC' in sql:
            binding, receipt = self._packets(sql)
            with self.lock:
                self.pending = (binding, receipt)
                self.phase = 'alice_held'
                self.dispatches.append(binding['operation_id'])
                self._record('paused_dispatch', binding=binding, receipt_template=receipt)
            self.held.set()
            if not self.resume.wait(timeout=3):
                raise TimeoutError('TEST_ONLY resume not reached')
            with self.lock:
                self.phase = 'alice_finished'
                if self.fault in ('stale_effect', 'stale_success_record'):
                    if self.fault == 'stale_effect':
                        self.tables['issues'][0]['title'] = binding['title']
                    self._save_operation(binding, receipt, self.now())
                    rows = [self._operation_row(binding['operation_id'])]
                elif self.fault == 'missing_execution_cause':
                    rows = []
                else:
                    # A transport failure contains no operation-bound proof
                    # that any authorization predicate executed or rejected.
                    return SimpleNamespace(returncode=1, stdout=b'{"rows":[]}',
                                           stderr=b'E_UNRELATED_TRANSPORT_FAILURE')
        else:
            with self.lock:
                rows = self._execute(sql)
        return SimpleNamespace(returncode=0, stderr=b'',
                               stdout=json.dumps({'rows': rows}).encode('utf-8'))

    def _packets(self, sql):
        packets = [json.loads(value) for value in hex_values(sql) if value.startswith('{')]
        assert len(packets) == 2, 'complete producer binding and receipt required'
        binding, receipt = packets
        assert binding['store_incarnation'] == self.selected.incarnation == self.minted
        assert binding['selection_digest'] == self.selected.digest
        assert binding['database'] == self.selected.database
        assert binding['branch'] == 'main'
        return binding, receipt

    def _operation_row(self, operation_id):
        return next(row for row in self.tables['mi_practical_v2_operations']
                    if row['operation_id'] == operation_id)

    def _save_operation(self, binding, template, authorization):
        self.token += 17
        receipt = dict(template, authorization_time_utc=authorization,
                       resulting_row_lock=self.token)
        if binding['action'] == 'initial_claim_lease':
            lease = self.tables['leases'][0]
            receipt.update(lease_granted_at_utc=lease['granted_at'] + '.000000',
                           lease_expires_at_utc=lease['lease_expires_at'] + '.000000',
                           lease_heartbeat_at_utc=lease['heartbeat_at'] + '.000000')
        if binding['action'] == 'reassign_title_lease':
            receipt['resulting_lease_heartbeat_at_utc'] = authorization.split('.')[0] + '.000000'
        if self.fault == 'backend_companion_status_confusion' and binding['action'] == 'reassign_title_lease':
            receipt['status'] = 'PRACTICAL_NATIVE_APPLIED'
        row = dict(store_incarnation=binding['store_incarnation'],
                   operation_id=binding['operation_id'], command_digest=binding['command_digest'],
                   binding_json=json.dumps(binding, sort_keys=True, separators=(',', ':')),
                   receipt_json=json.dumps(receipt, sort_keys=True, separators=(',', ':')),
                   authorization_time=authorization, resulting_row_lock=self.token)
        self.tables['mi_practical_v2_operations'].append(row)
        self.tables['mi_practical_v2_token_history'].append(dict(
            store_incarnation=binding['store_incarnation'], row_token=self.token,
            operation_id=binding['operation_id']))
        return self.token

    def _mutate(self, sql):
        binding, receipt = self._packets(sql)
        op = binding['operation_id']
        assert op not in self.dispatches, 'TEST_ONLY duplicate native mutation'
        self.dispatches.append(op)
        action = binding['action']
        if action == 'initial_claim_lease':
            issue = self.tables['issues'][0]
            assert issue['status'] == 'open' and issue['assignee'] is None
            assert not self.tables['leases']
            authorization = '2026-10-14 10:00:00.500000'
            self.tables['leases'].append(dict(issue_id=binding['task_id'], holder=binding['actor'],
                granted_node=binding['native_node_id'], granted_at='2026-10-14 10:00:00',
                lease_expires_at='2026-10-14 10:05:00', heartbeat_at='2026-10-14 10:00:00'))
            grant_id = binding['new_grant_id']
            token = self._save_operation(binding, receipt, authorization)
            issue.update(status='in_progress', assignee=binding['actor'], row_lock=token)
            grant = self._grant(binding, grant_id, 'CURRENT', token)
            self.tables['mi_practical_v2_grants'].append(grant)
            self.tables['mi_practical_v2_current_grants'].append(dict(
                store_incarnation=self.minted, task_id=binding['task_id'],
                grant_id=grant_id, current_revision=token))
            self._history(grant_id, 'INITIAL_CLAIM', authorization)
            self.phase = 'claimed'
        elif action == 'reassign_title_lease':
            assert self.phase == 'alice_held' and self.pending is not None
            assert self.pending[0]['expected_row_lock'] == binding['expected_row_lock']
            self.phase = 'transferred'
            authorization = '2026-10-14 10:00:02.500000'
            token = self._save_operation(binding, receipt, authorization)
            self.tables['issues'][0].update(assignee=binding['target_actor'],
                                           title=binding['title'], row_lock=token)
            self.tables['leases'][0].update(holder=binding['target_actor'],
                                            heartbeat_at=authorization.split('.')[0])
            prior = next(row for row in self.tables['mi_practical_v2_grants']
                         if row['grant_id'] == binding['grant_id'])
            prior['tombstoned'] = 1
            self.tables['mi_practical_v2_grants'].append(
                self._grant(binding, binding['new_grant_id'], 'GRANTED', token))
            self.tables['mi_practical_v2_current_grants'][0].update(
                grant_id=binding['new_grant_id'], current_revision=token)
            self._history(binding['grant_id'], 'TOMBSTONED', authorization)
            self._history(binding['new_grant_id'], 'MINTED', authorization)
        else:
            assert action == 'guarded_title_lease' and self.phase == 'alice_finished'
            if self.fault == 'ineffective_positive_control':
                raise OSError('TEST_ONLY positive-control transport failure')
            self.phase = 'positive'
            token = self._save_operation(binding, receipt, '2026-10-14 10:00:04.500000')
            self.tables['issues'][0].update(title=binding['title'], row_lock=token)
            self.tables['mi_practical_v2_current_grants'][0]['current_revision'] = token
            self.tables['mi_practical_v2_grants'][-1]['issue_revision'] = token
        self._record('mutation', binding=binding, receipt=copy.deepcopy(
            json.loads(self._operation_row(op)['receipt_json'])))
        return [self._operation_row(op)]

    def _grant(self, binding, grant_id, status, token):
        lease = self.tables['leases'][0]
        return dict(store_incarnation=self.minted, grant_id=grant_id,
                    task_id=binding['task_id'], actor=lease['holder'], status=status,
                    fixed_deadline_utc=lease['lease_expires_at'] + '.000000',
                    issue_revision=token, tombstoned=0, lease_node=lease['granted_node'],
                    lease_granted_at=lease['granted_at'], lease_expiry=lease['lease_expires_at'],
                    lease_heartbeat=lease['heartbeat_at'])

    def _history(self, grant, kind, authorization):
        self.tables['mi_practical_v2_grant_history'].append(dict(
            store_incarnation=self.minted, grant_id=grant, event_kind=kind,
            event_utc=authorization, details='TEST_ONLY producer-shaped history'))

    def _authority(self):
        i, lease, pointer = self.tables['issues'][0], self.tables['leases'][0], \
            self.tables['mi_practical_v2_current_grants'][0]
        g = next(row for row in self.tables['mi_practical_v2_grants']
                 if row['grant_id'] == pointer['grant_id'])
        metadata = self.tables['mi_practical_v2_metadata'][0]
        return dict(issue_id=i['id'], issue_title=i['title'], issue_status=i['status'],
            assignee=i['assignee'], issue_row_lock=i['row_lock'], ephemeral=i['ephemeral'],
            holder=lease['holder'], granted_node=lease['granted_node'], granted_at=lease['granted_at'],
            lease_expires_at=lease['lease_expires_at'], heartbeat_at=lease['heartbeat_at'],
            grant_id=g['grant_id'], grant_actor=g['actor'], grant_status=g['status'],
            fixed_deadline_utc=g['fixed_deadline_utc'], issue_revision=g['issue_revision'],
            tombstoned=g['tombstoned'], lease_node=g['lease_node'],
            lease_granted_at=g['lease_granted_at'], lease_expiry=g['lease_expiry'],
            lease_heartbeat=g['lease_heartbeat'], current_revision=pointer['current_revision'],
            selection_digest=metadata['selection_digest'], native_node_id=metadata['native_node_id'],
            selected_database=metadata['selected_database'], selected_main_branch=metadata['selected_main_branch'],
            observed_utc=self.now())

    def _execute(self, sql):
        if sql.startswith('CREATE TABLE'):
            for table in re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', sql):
                assert table not in self.tables
                self.tables[table] = []
            self._record('ddl', tables=sorted(self.tables))
            return []
        if sql == sql_builder.v2_namespace_bootstrap_sql():
            assert not self.tables['mi_practical_v2_metadata']
            self.tables['mi_practical_v2_metadata'].append(dict(
                store_incarnation=self.minted, namespace_key='identity', selection_digest=None,
                native_node_id=None, selected_database=None, selected_main_branch=None))
            self.phase = 'bootstrapped'
            self._record('bootstrap', namespace=self.minted)
            return [{'store_incarnation': self.minted, 'namespace_key': 'identity'}]
        if 'UPDATE mi_practical_v2_metadata SET selection_digest' in sql:
            values = hex_values(sql)
            assert self.minted in values and self.selected.digest in values
            metadata = self.tables['mi_practical_v2_metadata'][0]
            assert metadata['selection_digest'] is None
            metadata.update(selection_digest=values[0], native_node_id=values[1],
                            selected_database=values[2], selected_main_branch=values[3])
            self.phase = 'registered'
            self._record('register', metadata=metadata)
            return [dict(metadata)]
        if sql.startswith('INSERT INTO issues'):
            match = re.search(r"VALUES \('([^']+)', 'open', NULL, '([^']+)', 0, 0\);", sql)
            assert match and not self.tables['issues']
            self.tables['issues'].append(dict(id=match[1], status='open', assignee=None,
                                             title=match[2], row_lock=0, ephemeral=0))
            self.phase = 'seeded'
            self._record('seed', issue=self.tables['issues'][0])
            return []
        if sql.startswith('BEGIN NOT ATOMIC'):
            return self._mutate(sql)
        if sql.startswith('-- HARNESS-ONLY'):
            if self.fault == 'ineffective_disabled_control':
                raise OSError('TEST_ONLY disabled-control transport failure')
            title, actor, task = hex_values(sql)
            assert task == self.tables['issues'][0]['id']
            self.tables['issues'][0].update(title=title, assignee=actor)
            self.phase = 'disabled'
            self._record('disabled_comparison', issue=self.tables['issues'][0])
            return []
        assert sql.startswith('SELECT'), sql
        if 'FROM information_schema.processlist' in sql:
            return [{'session_id': 'TEST_ONLY-session-4242', 'observed_statement':
                     controller.BARRIER_COMMENT}] if self.held.is_set() else []
        if 'FROM information_schema.tables' in sql:
            names = list(self.tables)
            if self.fault == 'missing_physical_table':
                names.remove('mi_practical_v2_operations')
            self._record('schema_observation', physical_tables=names)
            return [{'observed_table': name} for name in names]
        if 'DATABASE() AS observed_database' in sql:
            return [{'observed_database': self.selected.database, 'observed_branch': 'main',
                     'observed_utc': self.now()}]
        if 'FROM issues AS i JOIN leases AS l' in sql:
            return [self._authority()]
        if sql == 'SELECT UTC_TIMESTAMP(6) AS observed_utc;':
            return [{'observed_utc': self.now()}]
        table = re.search(r' FROM (\w+)', sql)[1]
        rows = copy.deepcopy(self.tables[table])
        if table == 'mi_practical_v2_operations' and self.phase == 'transferred' \
                and self.fault == 'missing_s1_operation' and 'o.operation_id' not in sql:
            rows = [row for row in rows if row['operation_id'] != self.schedule['operation_ids']['bob']]
        if table == 'mi_practical_v2_metadata' and self.fault == 'foreign_namespace' \
                and self.phase == 'registered':
            rows[0]['store_incarnation'] = 'foreign-namespace'
        if table == 'mi_practical_v2_operations' and 'o.operation_id' in sql:
            operation_id = re.search(r'o.operation_id=BINARY CONVERT\(0x([0-9a-f]+)', sql)
            operation_id = bytes.fromhex(operation_id[1]).decode('utf-8')
            rows = [row for row in rows if row['operation_id'] == operation_id]
        elif table == 'mi_practical_v2_operations' and 'receipt_json' in sql:
            for row in rows:
                if row['operation_id'] == self.schedule['operation_ids']['bob']:
                    if self.fault == 'missing_receipt':
                        row['receipt_json'] = None
                    if self.fault == 'contradictory_receipt':
                        receipt = json.loads(row['receipt_json'])
                        receipt['backend_operation_id'] = 'foreign-operation'
                        row['receipt_json'] = json.dumps(receipt)
        if table == 'mi_practical_v2_grant_history' and self.fault == 'missing_history':
            rows = [row for row in rows if row['event_kind'] == 'INITIAL_CLAIM']
        if self.phase == 'transferred' and self.fault == 'invalid_s1' and table == 'issues':
            rows[0]['status'] = 'open'
        if self.phase == 'transferred' and self.fault == 'invalid_s1_lease' and table == 'mi_practical_v2_grants':
            rows[-1].pop('lease_node')
        result = self._projection(sql, rows)
        self._record('read', table=table, rows=result)
        return result
