"""Offline contract tests for the R5 practical ordinary-local fence.

These tests exercise the new contract and generated one-session SQL batches
through a recording Dolt-CLI boundary.  They deliberately do not start Dolt,
run Beads, or qualify native writes.
"""
from pathlib import Path
import sys
import unittest
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from hybrid_bridge import practical_backend, practical_contract, practical_sql
except ImportError as exc:  # RED: the feature is deliberately absent initially.
    raise AssertionError("practical ordinary-local fence modules are absent") from exc


SELECTION = {
    "scratch_root": "C:/scratch/r5-fence",
    "dolt_executable": "C:/scratch/r5-fence/dolt.exe",
    "dolt_sha256": "a" * 64,
    "host": "127.0.0.1",
    "port": 3306,
    "database": "beads_scratch",
    "main_branch": "main",
    "incarnation": "scratch-incarnation-20261013",
    "native_node_id": "practical-scratch-node-1",
    "candidate_route": "APPROVED_SCRATCH_PRACTICAL_CONTRACT",
}


def transition(operation_id="op-claim-1", **changes):
    value = {
        "schema_version": 1,
        "work_item_id": "cm-work-17",
        "operation_id": operation_id,
        "action": "claim",
        "task_id": "mip-42",
        "actor": "alice",
        "expected_status": "open",
        "grant_id": "grant-old-7",
        "target_actor": "alice",
        "new_grant_id": "grant-new-8",
        "expected_row_lock": 731,
        "fixed_deadline_utc": "2030-01-02 03:04:05.123456",
        "new_deadline_utc": "2030-01-02 04:04:05.123456",
    }
    value.update(changes)
    digest_input = {key: item for key, item in value.items() if key != "command_digest"}
    value["command_digest"] = hashlib.sha256(json.dumps(
        digest_input, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return value


def title(operation_id="op-title-1", **changes):
    value = transition(operation_id, action="guarded_title", title="Safe \u20ac title")
    value.update(changes)
    digest_input = {key: item for key, item in value.items() if key != "command_digest"}
    value["command_digest"] = hashlib.sha256(json.dumps(
        digest_input, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return value


def expired_reacquire(operation_id="op-reacquire-1", **changes):
    value = {
        "schema_version": 1,
        "work_item_id": "cm-work-17",
        "operation_id": operation_id,
        "action": "expired_reacquire",
        "task_id": "mip-42",
        "actor": "alice",
        "expected_status": "open",
        "prior_grant_id": "grant-expired-7",
        "prior_deadline_utc": "2030-01-02 03:04:05.123456",
        "expected_row_lock": -731,
        "target_actor": "alice",
        "new_grant_id": "grant-new-8",
        "fresh_authorization_deadline_utc": "2030-01-02 04:04:05.123456",
        "new_deadline_utc": "2030-01-02 05:04:05.123456",
    }
    value.update(changes)
    value["command_digest"] = hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return value


def initial_claim(operation_id="op-claim-initial-1", **changes):
    value = {
        "schema_version": 1,
        "work_item_id": "cm-work-17",
        "operation_id": operation_id,
        "action": "initial_claim",
        "task_id": "mip-42",
        "actor": "alice",
        "expected_status": "open",
        "expected_assignee": None,
        "expected_row_lock": -731,
        "new_grant_id": "grant-alice-1",
        "fresh_authorization_deadline_utc": "2030-01-02 04:04:05.123456",
        "new_deadline_utc": "2030-01-02 05:04:05.123456",
    }
    value.update(changes)
    value["command_digest"] = hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    return value


class RecordingRunner:
    """The unavoidable process boundary fake; contract/SQL stay real."""

    def __init__(self, stdout=b'{"rows":[{"state":"WORKING_SET_APPLIED","resulting_row_lock":812,"authorization_time_utc":"2030-01-02 03:04:05.123456"}]}\n', returncode=0):
        self.calls = []
        self.stdout = stdout
        self.returncode = returncode

    def __call__(self, argv, input_bytes, timeout, cwd):
        self.calls.append((tuple(argv), input_bytes, timeout, cwd))
        return {"returncode": self.returncode, "stdout": self.stdout, "stderr": b""}


class PracticalContractTests(unittest.TestCase):
    def test_selection_is_exact_scratch_contract_and_never_a_generic_activation(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        self.assertEqual(selected.host, "127.0.0.1")
        self.assertEqual(selected.candidate_route, "APPROVED_SCRATCH_PRACTICAL_CONTRACT")
        for key, bad in (("host", "localhost"), ("port", 0),
                         ("candidate_route", "NATIVE_VERIFIED"),
                         ("dolt_sha256", "z" * 64)):
            changed = dict(SELECTION, **{key: bad})
            with self.subTest(key=key):
                with self.assertRaises(practical_contract.PracticalContractError):
                    practical_contract.PracticalSelection.from_value(changed)

        backend = practical_backend.PracticalBackend(selected, runner=RecordingRunner())
        self.assertFalse(backend.native_write_qualified)
        self.assertEqual(backend.evidence_class, "NATIVE_OBSERVED_UNQUALIFIED")
        self.assertFalse(backend.activate(native_write_qualified=True))

    def test_canonical_digest_is_unicode_stable_and_rejects_noncanonical_numbers(self):
        first = practical_contract.canonical_command_digest(title(title="\u03c0 \u20ac"))
        second = practical_contract.canonical_command_digest(dict(title(title="\u03c0 \u20ac")))
        self.assertEqual(first, second)
        with self.assertRaises(practical_contract.PracticalContractError):
            practical_contract.canonical_command_digest(title(expected_row_lock=1.5))


class PracticalSqlTests(unittest.TestCase):
    def test_initial_claim_binds_open_unassigned_task_without_raw_grant_seed(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        request = practical_contract.InitialClaimRequest.from_value(initial_claim())
        sql = practical_sql.initial_claim_sql(selected, request)
        self.assertIn("i.assignee IS NULL", sql)
        self.assertIn("@practical_auth_now < @practical_fresh_authorization_deadline", sql)
        self.assertIn("INSERT INTO memory_integrity_practical_grants", sql)
        self.assertIn("authorization_time_utc", sql)
        self.assertNotIn("DOLT_ADD", sql)
        self.assertNotIn("DOLT_COMMIT", sql)

    def test_expired_reacquire_has_separate_prior_and_fresh_deadline_contract(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        request = practical_contract.ExpiredReacquireRequest.from_value(expired_reacquire())
        sql = practical_sql.expired_reacquire_sql(selected, request)
        self.assertIn("@practical_auth_now >= @practical_prior_deadline", sql)
        self.assertIn("@practical_auth_now < @practical_fresh_authorization_deadline", sql)
        self.assertIn("tombstoned = 1", sql)
        self.assertIn("authorization_time_utc", sql)
        self.assertNotIn("DOLT_COMMIT", sql)

    def test_guarded_title_sql_is_single_transaction_with_fixed_auth_sample_and_no_head_commit_claim(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        request = practical_contract.GuardedTitleRequest.from_value(title())
        sql = practical_sql.guarded_title_sql(selected, request)
        self.assertIn("START TRANSACTION", sql)
        self.assertIn("UTC_TIMESTAMP(6)", sql)
        self.assertIn("@practical_auth_now < @practical_original_deadline", sql)
        self.assertIn("memory_integrity_practical_token_history", sql)
        self.assertIn("AS state", sql)
        self.assertNotIn("DOLT_ADD", sql)
        self.assertNotIn("DOLT_COMMIT", sql)
        self.assertNotIn("HEAD_COMMITTED", sql)

    def test_sql_uses_utf8_hex_literals_not_interpolated_title_or_shell_text(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        hostile = "x'; DROP TABLE issues; -- \u20ac"
        request = practical_contract.GuardedTitleRequest.from_value(title(title=hostile))
        sql = practical_sql.guarded_title_sql(selected, request)
        self.assertNotIn(hostile, sql)
        self.assertIn("CONVERT(0x", sql)
        self.assertIn("USING utf8mb4", sql)
        self.assertNotIn("DELETE ", sql)

    def test_metadata_exposes_only_generated_sql_and_local_only_tables(self):
        selected = practical_contract.PracticalSelection.from_value(SELECTION)
        metadata = practical_sql.metadata(selected)
        self.assertEqual(set(metadata), {"initialize_local_tables", "observe", "read_task", "read_grant", "read_operation"})
        init = metadata["initialize_local_tables"]
        self.assertIn("INSERT INTO dolt_ignore", init)
        self.assertIn("memory_integrity_practical_operations", init)
        self.assertNotIn("DELETE ", init)


class PracticalBackendTests(unittest.TestCase):
    def setUp(self):
        self.selected = practical_contract.PracticalSelection.from_value(SELECTION)
        self.runner = RecordingRunner()
        self.backend = practical_backend.PracticalBackend(self.selected, runner=self.runner)

    def test_unsupported_or_spelled_fallback_rejects_before_any_process_mutation(self):
        for request in (
            transition(action="import"),
            transition(action="restore"),
            transition(action="batch"),
            transition(action="Claim"),
            transition(action="rawadmin"),
            transition(task_id="mip-42; -- foreign"),
        ):
            with self.subTest(request=request["action"]):
                with self.assertRaises(practical_contract.PracticalContractError):
                    self.backend.transition(request)
        self.assertEqual(self.runner.calls, [])

    def test_dependency_reader_returns_only_exact_rows_and_title_sql_rechecks_no_dependencies(self):
        empty = RecordingRunner(stdout=b'{"rows":[]}\n')
        backend = practical_backend.PracticalBackend(self.selected, runner=empty)
        self.assertEqual(backend.read_dependencies("mip-42"), [])
        dependency_sql = empty.calls[0][0][-1]
        self.assertIn("FROM dependencies", dependency_sql)

        title_sql = practical_sql.guarded_title_sql(
            self.selected, practical_contract.GuardedTitleRequest.from_value(title()))
        self.assertIn("NOT EXISTS (SELECT 1 FROM dependencies", title_sql)

        malformed = RecordingRunner(stdout=(
            b'{"rows":[{"id":"dep-1","issue_id":"mip-42",'
            b'"depends_on_issue_id":"other","depends_on_wisp_id":"also",'
            b'"depends_on_external":null,"type":"blocks"}]}\n'))
        with self.assertRaises(practical_backend.PracticalUncertainDelivery):
            practical_backend.PracticalBackend(self.selected, runner=malformed).read_dependencies("mip-42")

    def test_title_dispatches_exactly_one_bounded_dolt_sql_session_and_reports_working_set_only(self):
        result = self.backend.guarded_title(title())
        self.assertEqual(result["status"], "WORKING_SET_APPLIED")
        self.assertFalse(result["head_committed"])
        self.assertEqual(len(self.runner.calls), 1)
        argv, batch, timeout, cwd = self.runner.calls[0]
        self.assertEqual(argv[0], SELECTION["dolt_executable"])
        self.assertEqual(argv[1:9], ("--host", "127.0.0.1", "--port", "3306", "--no-tls", "--use-db", "beads_scratch", "--branch"))
        self.assertEqual(argv[9], "main")
        self.assertEqual(argv[10:14], ("sql", "-r", "json", "-q"))
        self.assertEqual(timeout, practical_backend.SQL_TIMEOUT_SECONDS)
        self.assertEqual(cwd, SELECTION["scratch_root"])
        self.assertIn("START TRANSACTION", argv[-1])

    def test_operation_rebinding_and_uncertain_delivery_never_retry_a_write(self):
        first = self.backend.guarded_title(title())
        self.assertEqual(first["status"], "WORKING_SET_APPLIED")
        with self.assertRaises(practical_contract.PracticalContractError):
            self.backend.guarded_title(title(title="different title"))
        self.assertEqual(len(self.runner.calls), 1)

        uncertain = practical_backend.PracticalBackend(
            self.selected, runner=RecordingRunner(stdout=b"", returncode=1))
        with self.assertRaises(practical_backend.PracticalUncertainDelivery):
            uncertain.guarded_title(title(operation_id="op-uncertain"))
        with self.assertRaises(practical_backend.PracticalUncertainDelivery):
            uncertain.guarded_title(title(operation_id="op-uncertain"))
        self.assertEqual(len(uncertain._runner.calls), 1)

    def test_operation_readback_is_bound_to_operation_id_and_digest_not_reused_title_or_status(self):
        request = title()
        digest = practical_contract.canonical_command_digest(request)
        binding = dict(request)
        binding.update({
            "selection_digest": self.selected.digest,
            "store_incarnation": self.selected.incarnation,
            "database": self.selected.database,
            "branch": self.selected.main_branch,
            "native_task_id": request["task_id"],
            "original_row_lock": request["expected_row_lock"],
            "backend_operation_id": request["operation_id"],
        })
        receipt = {
            "operation_id": "op-title-1", "backend_operation_id": "op-title-1",
            "command_digest": digest, "status": "WORKING_SET_APPLIED",
        }
        runner = RecordingRunner(
            stdout=(json.dumps({"rows": [{
                "store_incarnation": self.selected.incarnation,
                "backend_operation_id": "op-title-1",
                "command_digest": digest,
                "binding_json": json.dumps(binding, sort_keys=True, separators=(",", ":")),
                "receipt_json": json.dumps(receipt, sort_keys=True, separators=(",", ":")),
                "state": "WORKING_SET_APPLIED", "resulting_row_lock": 812,
            }]}) + "\n").encode("utf-8"))
        backend = practical_backend.PracticalBackend(self.selected, runner=runner)
        result = backend.read_operation("op-title-1", digest)
        self.assertEqual(result["operation_id"], "op-title-1")
        self.assertEqual(result["command_digest"], digest)
        batch = runner.calls[0][0][-1]
        self.assertIn("operation_id", batch)
        self.assertIn("command_digest", batch)
        self.assertNotIn("Safe \u20ac title", batch)


if __name__ == "__main__":
    unittest.main(verbosity=2)
