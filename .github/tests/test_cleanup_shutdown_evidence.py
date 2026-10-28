"""SR1 saved-data regression: never starts a worker or changes old evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).absolute().parents[2]
SCRIPT = REPO/'.github/scripts/cleanup_shutdown_evidence.py'
OLD_PROBE = REPO/'.github/scripts/cleanup_membership_probe.py'
ATTEMPT = REPO/'.github/run-artifacts/cleanup-membership-20261025/normal-membership'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def events():
    return [json.loads(line) for line in (ATTEMPT/'probe/Incremental.jsonl').read_text().splitlines()]


class OldRegressionWitness(unittest.TestCase):
    def test_old_validator_refuses_the_saved_second_termination_transition(self):
        old = load(OLD_PROBE, 'sr_old_mp1_witness')
        rows = events()
        after = [row for row in rows if row['stage'] == 'after-terminate'][-1]
        roles = {}
        for role, observed in after['roles'].items():
            roles[role] = {**json.loads((ATTEMPT/'probe/fixture'/(role+'.json')).read_text()), **observed}
        with self.assertRaisesRegex(ValueError, 'E_MP_MEMBERSHIP'):
            old.validate_snapshot({**after['membership'], 'roles': roles})


class SavedEvidenceRepair(unittest.TestCase):
    def setUp(self):
        if not SCRIPT.exists():
            self.fail('SR1 saved-evidence interpreter is not implemented')
        self.m = load(SCRIPT, 'sr_saved_evidence_tests')

    def test_saved_run_is_a_gap_not_a_fixed_or_accepted_probe(self):
        result = self.m.review_saved_attempt()
        self.assertEqual(result['derived_classification'], 'MEMBERSHIP_GAP_OBSERVED_NOT_FIXED')
        self.assertEqual(result['outside_survivors'], ['launcher', 'child'])
        self.assertEqual(result['outside_survivor_pids'], [35012, 19464])
        self.assertTrue(result['writer_alive_after_stop'])
        self.assertFalse(result['old_probe_accepted'])
        for key in self.m.FALSE_FLAGS:
            self.assertIs(result[key], False)
        self.assertEqual(result['unknown_job_member_pids'], [17336])
        self.assertTrue(result['emergency_combined_cleanup_completed'])
        self.assertFalse(result['cancellation_alone_proven'])
        self.assertEqual(result['commands'][-1]['capture'], 'COMPLETE_NONZERO_EXIT')
        self.assertEqual(len(result['verified_streams']), 6)

    def test_post_termination_empty_job_before_handle_signal_is_observation_not_corruption(self):
        row = next(row for row in events() if row['stage'] == 'after-terminate')
        # Root is still unsignalled here, not just a dead historical association.
        self.assertFalse(row['roles']['root']['signalled'])
        self.m.validate_snapshot(row, phase='after-terminate')
        with self.assertRaisesRegex(ValueError, 'E_SR_STABLE_MEMBERSHIP'):
            self.m.validate_snapshot(row, phase='before-write')

    def test_stable_current_count_mismatch_and_boolean_counter_still_refused(self):
        before = next(row for row in events() if row['stage'] == 'before-write')
        for key, value in (('active', 1), ('total', True), ('members', [44532, 44532])):
            row = copy.deepcopy(before); row['membership'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_SR_'):
                self.m.validate_snapshot(row, phase='before-write')

    def test_unknown_phase_does_not_weaken_validation(self):
        row = next(row for row in events() if row['stage'] == 'before-write')
        with self.assertRaisesRegex(ValueError, 'E_SR_PHASE'):
            self.m.validate_snapshot(row, phase='anything')

    def test_complete_nonzero_exit_is_not_capture_incomplete(self):
        command = json.loads((ATTEMPT/'Receipt.json').read_text())['commands'][-1]
        self.assertEqual(self.m.capture_status(command), 'COMPLETE_NONZERO_EXIT')
        for key, value in (('timed_out', True), ('capture_complete', False), ('capture_errors', ['lost'])):
            row = copy.deepcopy(command); row['containment'][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'E_SR_CAPTURE_INCOMPLETE'):
                self.m.capture_status(row)

    def test_boolean_and_disagreeing_exit_codes_are_refused(self):
        command = json.loads((ATTEMPT/'Receipt.json').read_text())['commands'][-1]
        for code in (True, False, '1'):
            row = copy.deepcopy(command); row['exit_code'] = code
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, 'E_SR_CAPTURE'):
                self.m.capture_status(row)
        row = copy.deepcopy(command); row['containment']['exit_code'] = 0
        with self.assertRaisesRegex(ValueError, 'E_SR_CAPTURE'):
            self.m.capture_status(row)

    def test_missing_or_reordered_events_never_yield_a_gap_classification(self):
        rows = events()
        for changed in ([row for row in rows if row['stage'] != 'after-stop'], list(reversed(rows))):
            with self.subTest(length=len(changed)), self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
                self.m.interpret_events(changed)

    def test_every_termination_and_failure_transition_is_required(self):
        rows = events()
        required = [i for i, row in enumerate(rows) if row['stage'] in
                    ('before-terminate', 'terminate-returned', 'after-terminate', 'stop-failed')]
        for index in required:
            changed = rows[:index] + rows[index+1:]
            with self.subTest(deleted=index), self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
                self.m.interpret_events(changed)
        # Removing all callbacks must not turn missing evidence into a verdict.
        with self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
            self.m.interpret_events([row for i, row in enumerate(rows) if i not in required])

    def test_termination_transition_payload_and_order_are_cross_checked(self):
        rows = events()
        first_return = next(i for i, row in enumerate(rows) if row['stage'] == 'terminate-returned')
        changed = copy.deepcopy(rows)
        changed[first_return], changed[first_return+1] = changed[first_return+1], changed[first_return]
        with self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
            self.m.interpret_events(changed)
        for field, value in (('value', 1), ('last_error', True), ('last_error', 5)):
            changed = copy.deepcopy(rows); changed[first_return][field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
                self.m.interpret_events(changed)
        changed = copy.deepcopy(rows)
        next(row for row in changed if row['stage'] == 'stop-failed')['error'] = ['different error']
        with self.assertRaisesRegex(ValueError, 'E_SR_EVENTS'):
            self.m.interpret_events(changed)

    def test_all_dead_and_writer_alive_remain_distinct_outcomes(self):
        rows = events()
        stopped = next(row for row in rows if row['stage'] == 'after-stop')
        stopped['signalled'] = dict.fromkeys(self.m.ROLES, True)
        self.assertEqual(self.m.interpret_events(rows)['derived_classification'], 'PIPE_CANCELLATION_GAP_NOT_FIXED')
        stopped['writer_alive'] = False
        self.assertEqual(self.m.interpret_events(rows)['derived_classification'], 'STOP_FAILURE_WITH_ALL_HANDLES_EXITED_NOT_FIXED')
        stopped['stop_error'] = None
        rows = [row for row in rows if row['stage'] != 'stop-failed']
        self.assertEqual(self.m.interpret_events(rows)['derived_classification'], 'FAILURE_NOT_REPRODUCED_INCONCLUSIVE')

    def test_derived_report_retains_raw_and_missing_error_limit(self):
        result = self.m.review_saved_attempt()
        self.assertEqual(result['raw_events'], events())
        self.assertIn('OBSERVATION_ERRORS_NOT_RETAINED_BY_OLD_PROBE', result['limitations'])
        self.assertIn('RAW_PROBE_EVENTS_NOT_HASH_BOUND_BY_OLD_RECEIPT', result['limitations'])
        self.assertIn('stop_error', result)
        self.assertIn('E_DISTRIBUTED_WRITER_STILL_ALIVE', str(result['stop_error']))
        self.assertEqual(result['raw_probe_error']['error'], ['ValueError: E_MP_OBSERVATION'])

    def test_retained_exact_export_preserves_every_integer_and_raw_record(self):
        artifact = REPO/'.github/run-artifacts/cleanup-shutdown-repair-20261026/Saved-Evidence-exact.json'
        self.assertTrue(artifact.exists(), 'exact unparsed-stdout export is missing')
        saved = json.loads(artifact.read_bytes())
        actual = self.m.review_saved_attempt()
        self.assertEqual(saved, actual)
        self.assertEqual(saved['raw_events'][2]['utc_ns'], 1793001733541399500)
        self.assertIs(type(saved['raw_events'][2]['utc_ns']), int)

    def test_error_receipt_and_emergency_event_must_agree(self):
        original = self.m.read_bytes
        path = ATTEMPT/'probe/Probe-error.json'
        def corrupt(candidate, **kwargs):
            raw = original(candidate, **kwargs)
            if Path(candidate) == path:
                value = json.loads(raw); value['emergency_cleanup']['writer_joined'] = False
                return json.dumps(value).encode()
            return raw
        with patch.object(self.m, 'read_bytes', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'E_SR_EVENT_RECEIPT'):
                self.m.review_saved_attempt()

    def test_wrong_receipt_seal_fails_before_interpreting(self):
        with self.assertRaisesRegex(ValueError, 'E_SR_RECEIPT_SEAL'):
            self.m.review_saved_attempt(expected_receipt_sha='0'*64)

    def test_changed_stream_and_escaped_path_are_refused(self):
        original = self.m.read_bytes
        stdout = ATTEMPT/'membership/stdout.log'
        def corrupt(path, **kwargs):
            raw = original(path, **kwargs)
            return raw + b'changed' if Path(path) == stdout else raw
        with patch.object(self.m, 'read_bytes', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'E_SR_STREAM'):
                self.m.review_saved_attempt()
        with self.assertRaisesRegex(ValueError, 'E_SR_STREAM_PATH'):
            self.m.verify_stream({'path':str(ATTEMPT/'Receipt.json'), 'size':9846, 'sha256':'0'*64}, stdout)

    def test_duplicate_json_keys_and_bad_readiness_flags_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'E_SR_DUPLICATE_JSON_KEY'):
            self.m.parse_json(b'{"x":1,"x":2}')
        bad = dict.fromkeys(self.m.FALSE_FLAGS, False); bad['stage_complete'] = True
        with self.assertRaisesRegex(ValueError, 'E_SR_FALSE_FLAGS'):
            self.m.require_false_flags(bad)

    def test_read_attempt_never_starts_a_process_or_writes_a_file(self):
        import subprocess
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('no worker allowed')), \
             patch.object(Path, 'write_text', side_effect=AssertionError('read only')), \
             patch.object(Path, 'write_bytes', side_effect=AssertionError('read only')):
            self.m.review_saved_attempt()

    def test_ordinary_read_rejects_oversize_and_linked_evidence(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name)/'evidence.json'; path.write_bytes(b'large')
            with self.assertRaisesRegex(ValueError, 'E_SR_INPUT_SIZE'):
                self.m.read_bytes(path, limit=2)
            import os
            alias = Path(name)/'alias.json'; os.link(path, alias)
            with self.assertRaisesRegex(ValueError, 'E_SR_LINKED_INPUT'):
                self.m.read_bytes(path)


if __name__ == '__main__':
    unittest.main()
