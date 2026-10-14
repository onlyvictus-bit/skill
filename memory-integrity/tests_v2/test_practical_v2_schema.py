"""v2 grant schema and lease-minting transition checks (offline).

These assert generated SQL text, schema shape and contract binding only.
They are NOT live Dolt grammar, atomicity or native-eligibility proof.

Fence-disabled live control (definition, runs only against a live scratch
database): build the authority predicate, then run the identical batch with
every fence family below stripped (grant equality, row_lock equality, lease
timestamps, strict deadline, tombstone, replay guard). The stripped batch
MUST authorize a stale request that the fenced batch refuses; otherwise the
experiment does not distinguish the fence and proves nothing. Abort conditions:
any stale committed effect, any partial effect without its exact receipt, any
revived old request. This control is defined here; its execution needs a live
database and is not claimed by any test in this file.
"""
import importlib
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hybrid_bridge.practical_contract import LeasePracticalSelection, LeaseGuardedTitleRequest
from tests_v2.test_practical_lease_contract import packet


def selection():
    return LeasePracticalSelection(
        scratch_root='C:/Users/sakth/memory-integrity-practical-fence-20261013/pilot-1',
        dolt_executable='C:/dolt.exe', dolt_sha256='a' * 64, host='127.0.0.1', port=50001,
        database='mipx', main_branch='main', incarnation='store-1',
        native_node_id='practical-approved-scratch-only',
        candidate_route='APPROVED_SCRATCH_PRACTICAL_CONTRACT')


def mod():
    return importlib.import_module('hybrid_bridge.practical_lease_sql')


def hx(text):
    return 'CONVERT(0x' + text.encode('utf-8').hex() + ' USING utf8mb4)'


LEASE_SNAPSHOT = {
    'lease_node': 'practical-approved-scratch-only',
    'lease_granted_at_utc': '2026-10-14 10:00:00.000000',
    'lease_expiry_utc': '2026-10-14 10:05:00.000000',
    'lease_heartbeat_utc': '2026-10-14 10:00:00.000000',
}


def grant_ddl_columns():
    ddl = mod().v2_schema_sql()
    block = ddl[ddl.index('mi_practical_v2_grants'):]
    block = block[:block.index(';')]
    return set(re.findall(r'(\w+)\s+(?:VARCHAR|DATETIME|BIGINT|TINYINT|LONGTEXT|CHAR)', block))


def title_grant_refs():
    sql = mod().guarded_title_sql(selection(), packet())
    return set(re.findall(r'g\.(\w+)\s*=', sql))


class CorrespondenceTests(unittest.TestCase):
    def test_every_title_grant_column_exists_in_schema(self):
        missing = title_grant_refs() - grant_ddl_columns()
        self.assertEqual(missing, set())

    def test_namespace_columns_cover_metadata_predicates(self):
        ddl = mod().v2_schema_sql()
        block = ddl[ddl.index('mi_practical_v2_metadata'):]
        block = block[:block.index(';')]
        cols = set(re.findall(r'(\w+)\s+(?:VARCHAR|DATETIME|BIGINT|TINYINT|LONGTEXT|CHAR)', block))
        sql = mod().guarded_title_sql(selection(), packet())
        refs = set(re.findall(r'm\.(\w+)\s*=', sql))
        self.assertEqual(refs - cols, set())

    def test_mint_populates_lease_snapshot_columns(self):
        sql = mod().initial_claim_grant_sql('store-1', 'task-9', 'alice',
                                            'grant-new-1', '2026-10-20 12:00:00',
                                            **LEASE_SNAPSHOT,
                                            selection_digest='b' * 64,
                                            native_node_id='practical-approved-scratch-only')
        for literal in ('practical-approved-scratch-only', '2026-10-14 10:05:00.000000'):
            self.assertIn(literal.encode('utf-8').hex(), sql)

    def test_initial_claim_mints_namespace_row(self):
        sql = mod().initial_claim_grant_sql('store-1', 'task-9', 'alice',
                                            'grant-new-1', '2026-10-20 12:00:00',
                                            **LEASE_SNAPSHOT,
                                            selection_digest='b' * 64,
                                            native_node_id='practical-approved-scratch-only')
        self.assertIn('INSERT INTO mi_practical_v2_metadata', sql)
        self.assertIn('namespace_key', sql)

    def test_reassign_rejects_bad_lease_facts(self):
        bad = dict(LEASE_SNAPSHOT, lease_expiry_utc='someday')
        with self.assertRaises(ValueError):
            mod().reassign_grant_sql('store-1', 'task-9', 'grant-old-7',
                                     'grant-new-8', 'bob', '2026-10-20 12:00:00',
                                     **bad)

    @unittest.expectedFailure
    def test_dolt_ignore_configuration_proven_on_live_db(self):
        self.assertIn('dolt_ignore', mod().v2_schema_sql().lower())


class V2SchemaTests(unittest.TestCase):
    def test_v2_schema_creates_grant_history_metadata_token_operations(self):
        sql = mod().v2_schema_sql()
        for name in ('mi_practical_v2_grants', 'mi_practical_v2_grant_history',
                     'mi_practical_v2_metadata', 'mi_practical_v2_token_history',
                     'mi_practical_v2_operations', 'mi_practical_assert_v2'):
            self.assertIn(name, sql)
        self.assertIn('PRIMARY KEY', sql)
        self.assertIn('grant_id', sql)
        for forbidden in ('DELETE ', 'DROP ', 'DOLT_ADD', 'DOLT_COMMIT'):
            self.assertNotIn(forbidden, sql)

    def test_grant_uniqueness_is_primary_key_not_convention(self):
        sql = mod().v2_schema_sql()
        grants = sql[sql.index('mi_practical_v2_grants'):]
        self.assertRegex(grants, r'PRIMARY KEY\s*\(\s*store_incarnation\s*,\s*grant_id\s*\)')


class MintingTransitionTests(unittest.TestCase):
    def test_initial_claim_inserts_grant_and_history_atomically(self):
        sql = mod().initial_claim_grant_sql('store-1', 'task-9', 'alice',
                                            'grant-new-1', '2026-10-20 12:00:00',
                                            **LEASE_SNAPSHOT,
                                            selection_digest='b' * 64,
                                            native_node_id='practical-approved-scratch-only')
        self.assertLess(sql.index('START TRANSACTION'), sql.index('COMMIT;'))
        self.assertIn('INSERT INTO mi_practical_v2_grants', sql)
        self.assertIn('INSERT INTO mi_practical_v2_grant_history', sql)
        self.assertIn(hx('grant-new-1'), sql)
        self.assertIn('E_MI2_GRANT_REUSE', sql)
        for forbidden in ('DELETE ', 'UPDATE mi_practical_v2_grants'):
            self.assertNotIn(forbidden, sql)

    def test_reassign_tombstones_prior_and_mints_fresh_never_deleting(self):
        sql = mod().reassign_grant_sql('store-1', 'task-9', 'grant-old-7',
                                       'grant-new-8', 'bob', '2026-10-20 12:00:00',
                                       **LEASE_SNAPSHOT)
        self.assertIn('tombstoned', sql)
        self.assertIn(hx('grant-old-7'), sql)
        self.assertIn(hx('grant-new-8'), sql)
        self.assertIn('INSERT INTO mi_practical_v2_grant_history', sql)
        self.assertNotIn('DELETE ', sql)

    def test_release_and_reclaim_preserve_history(self):
        for builder in ('release_grant_sql', 'reclaim_grant_sql'):
            sql = getattr(mod(), builder)('store-1', 'task-9', 'grant-old-7',
                                          '2026-10-20 12:00:00')
            self.assertIn('tombstoned', sql, builder)
            self.assertIn('INSERT INTO mi_practical_v2_grant_history', sql, builder)
            self.assertNotIn('DELETE ', sql, builder)

    def test_malformed_inputs_refuse_before_sql(self):
        with self.assertRaises(ValueError):
            mod().initial_claim_grant_sql('store-1', 'task-9', 'alice',
                                          'grant-new-1', 'next Friday',
                                          **LEASE_SNAPSHOT,
                                          selection_digest='b' * 64,
                                          native_node_id='practical-approved-scratch-only')
        with self.assertRaises(ValueError):
            mod().reassign_grant_sql('store-1', 'task-9', 'grant-old-7',
                                     'grant-old-7', 'bob', '2026-10-20 12:00:00',
                                     **LEASE_SNAPSHOT)
        with self.assertRaises(ValueError):
            mod().initial_claim_grant_sql('store-1', '', 'alice',
                                          'grant-new-1', '2026-10-20 12:00:00',
                                          **LEASE_SNAPSHOT,
                                          selection_digest='b' * 64,
                                          native_node_id='practical-approved-scratch-only')
        with self.assertRaises(ValueError):
            mod().initial_claim_grant_sql('store-1', 'task-9', 'alice',
                                          'grant-new-1', '2026-10-20 12:00:00',
                                          **LEASE_SNAPSHOT,
                                          selection_digest='not-hex',
                                          native_node_id='practical-approved-scratch-only')


class BindingComparisonTests(unittest.TestCase):
    def test_unknown_grant_is_compared_in_database_not_python(self):
        sql = mod().guarded_title_sql(selection(), packet(grant_id='grant-never-issued'))
        self.assertIn('g.grant_id = ' + hx('grant-never-issued'), sql)

    def test_expiry_equality_refuses_strict_less_than_only(self):
        sql = mod().guarded_title_sql(selection(), packet())
        self.assertIn('@mi2_auth < l.lease_expires_at', sql)
        self.assertNotIn('@mi2_auth <= l.lease_expires_at', sql)

    def test_spelling_mismatch_refuses_before_sql(self):
        from hybrid_bridge.practical_contract import PracticalContractError
        with self.assertRaises(PracticalContractError):
            mod().guarded_title_sql(selection(),
                                    packet(lease_holder='Alice', actor='alice'))

    def test_namespace_identity_is_read_from_database(self):
        sql = mod().guarded_title_sql(selection(), packet())
        for text in ('m.namespace_key = ', 'm.selection_digest', 'm.native_node_id'):
            self.assertIn(text, sql)

    def test_fence_predicates_are_all_present_and_load_bearing(self):
        sql = mod().guarded_title_sql(selection(), packet())
        for family in ('g.grant_id = ', 'row_lock = ', 'l.lease_expires_at',
                       '@mi2_auth < l.lease_expires_at', 'tombstoned = 0',
                       'store_incarnation', 'NOT EXISTS (SELECT 1 FROM dependencies',
                       'E_MI2_OPERATION_REPLAY', 'E_MI2_GRANT_CARDINALITY',
                       'E_MI2_TOKEN_CARDINALITY', 'E_MI2_RECEIPT_CARDINALITY'):
            self.assertIn(family, sql)


if __name__ == '__main__':
    unittest.main(verbosity=2)
