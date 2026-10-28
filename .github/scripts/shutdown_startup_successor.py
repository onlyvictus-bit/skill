"""Sealed SR4 ownership/startup-only normal-account verification successor.

The three D1 sources and all original plus added ownership cases are pinned.
Prepare validates inputs without starting the selected worker. Run consumes
one new ownership observation only after strict identity and source checks;
an external Inputs hash is mandatory. No full stage or preservation claim is
made here: D3 retains its own full controls and fresh ORIGINAL BEFORE/AFTER.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import traceback


REPO = Path(__file__).absolute().parents[2]
SCRIPTS = REPO / '.github' / 'scripts'
ROOT = Path(r'C:\Users\sakth\Documents\Codex\sr4-owned-20261027')
CONTROLLER = Path(r'C:\Python314\python.exe')
EVALUATED_HEAD = 'a38297dd797eeecd25e41ab0af1df4e3db8fa984'
CHECKOUT_HEAD = 'f63f62496f82fb479e352bdd9c90accf9f869e8b'
C1_SHA = '5e1b06812949b72a8723844c4c1b7a8bde1b4fee645c43147e3352acb7696861'
SC_SHA = '234dd24e90a33feeee9fbacd5e75f03b2099c8393b7be86d3d9f994d99946cd3'
SR3_SHA = 'f224d215d0eb8ac898ac6a185cb388d1aa45b627765a006ae266455b800aff69'
OLD_ROOT = Path(r'C:\Users\sakth\Documents\Codex\sr3-copy-20261027-4a52cd8d')
OLD_PINS = {
    'Runtime-Inputs.json': 'f4d945d7b6b98ac736feb4eff7047bd512aa450f4ffa6c00837885ed068cf21a',
    'Policy-Inputs.json': 'c91235f95b135a1e170893513d3105095fb5dd39feef268eb3b2fec3c4cd3180',
    'Run-Claim.json': 'a96e942bba5adcc6204030965a11d467966a8e296ce47d02076634b0b00003f2',
    'Run-Failure.json': 'c908bdc4b9be2fa2964f47ba2e90757ff03add9c2cfabe4b12140ff5aab486f0',
    'run/Receipt.json': 'beab04ef2dde95a01cc25ed21eedf6ff79c3e50c2aceacaf2cd2f74dc4fc76d2',
    'run/tests-ownership/Receipt.json': '4cf5b22c7356554737d077a996a6cb6ad0a92ec5234ec1fb3535bc4c1dfea0d9',
    'run/tests-ownership/unittest.log': '31b890a700844cabbd0636cadf7735610b1c70a2f632a2380a28c94be705eaa8',
}
PATTERN = 'test_knowledge_windows_owned*.py'
MAX_JSON = 16 * 1024 * 1024
MAX_LOG = 1024 * 1024
MAX_STARTUP = 65536

# Candidate pins from parent-observed D1 GREEN. Issuance still requires the
# independent final source/test/launcher review; no agent-account worker run.
SOURCE_NAMES = (
    'memory-integrity/scripts/knowledge_bridge/windows_owned_process.py',
    'memory-integrity/scripts/knowledge_bridge/windows_owned_bootstrap.py',
    'memory-integrity/tests_v2/test_knowledge_windows_owned_startup.py',
)
SR4_SOURCES = {
    SOURCE_NAMES[0]: 'd9f8cf4a2f72db3f320252617982f160e9646b8254860498e2e288eaed2c94e4',
    SOURCE_NAMES[1]: 'a7fa933c35d919e6c730ff58b4634315b5afc05b2917d5c520ab5d5a990e086e',
    SOURCE_NAMES[2]: '1cf10aa195798ed4e10792a8bdbb4cb3b449c216524bbfa9858220abb91d8978',
}
CASE_IDS = (
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_active_count_may_change_after_pid_snapshot_without_identity_gap',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_assignment_failure_reaps_unassigned_suspended_root_and_closes_stdin',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_authored_script_keeps_its_original_sibling_import_directory',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_cpython_consumed_launcher_environment_is_not_false_identity_drift',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_event_drain_cannot_ignore_expired_observation_deadline',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_expired_start_never_opens_work_gate_after_identity_check',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_job_and_member_release_attempt_every_close_and_keep_all_errors',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_job_setup_close_debt_is_not_labelled_complete_without_an_owner',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_member_outside_job_is_not_accepted_from_a_completion_pid',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_missing_accounting_member_still_terminates_all_known_processes',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_nested_job_descendant_has_independent_native_exit_proof',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_popen_failure_keeps_the_pre_owner_job_when_its_close_fails',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_rejects_requested_executable_identity_drift_before_start',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_release_refuses_before_native_exit_proof',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_resume_identity_error_survives_all_handle_close_failures',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_script_system_exit_is_not_relabelled_as_bootstrap_failure',
    'test_knowledge_windows_owned_process.CurrentImageOwnerTests.test_stop_reaps_root_child_grandchild_but_not_unrelated_process',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_actual_startup_retains_identity_frame_then_native_exit_proof',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_assigned_not_resumed_cleanup_records_specific_native_exit_mode',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_assigned_not_resumed_failure_reaps_recorded_root_without_authored_work',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_bootstrap_emitter_caps_detail_and_preserves_identity_in_a_bounded_frame',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_bootstrap_emitter_never_writes_an_oversized_identity_failure',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_bootstrap_role_mismatch_records_bounded_expected_observed_frame_and_reaps_root',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_expected_identity_keeps_parent_base_distinct_from_loaded_image',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_failed_accounting_query_names_its_native_operation',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_failed_completion_query_names_its_native_operation',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_failed_terminate_names_native_operation_and_preserves_resume_error',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_oversized_failure_detail_is_rejected_before_publication',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_preinsert_query_and_close_failure_retain_recoverable_handle_debt',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_ready_file_is_bounded_before_json_parsing',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_real_post_resume_close_failure_keeps_debt_and_never_claims_complete',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_root_exit_without_a_new_event_is_attributable_to_the_pre_resume_ledger',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_same_token_tampered_expected_frame_is_rejected',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_signalled_root_uses_fresh_empty_check_not_termination_of_a_stale_pid_snapshot',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_successful_resume_then_close_failure_still_records_resumed_cleanup_state',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_unknown_nonroot_exit_remains_a_proof_gap',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_wait_failure_is_not_falsely_attributed_to_successful_termination',
    'test_knowledge_windows_owned_startup.OwnedStartupTests.test_wrong_token_failure_cannot_publish_an_identity_frame',
)

ORIGINAL_OWNERSHIP = 'memory-integrity/tests_v2/test_knowledge_windows_owned_process.py'
ORIGINAL_OWNERSHIP_SHA = '00c837f55f8527cefe361c5421155b2b8a4e51b177296506b9f249613eb223c4'
BUDGETS = {'default': 120, 'watchdog': 60, 'cleanup': 5}
FLAGS = ('stage_complete', 'gate1_complete', 'release_ready', 'installed',
         'producer_authentication', 'preservation')


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ordinary(path):
    path = Path(path)
    require(path.is_absolute(), 'E_SR4_ABSOLUTE')
    for item in (path, *path.parents):
        if not item.exists():
            continue
        info = item.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not
                getattr(info, 'st_file_attributes', 0) & 0x400,
                'E_SR4_REDIRECTED_PATH: ' + str(item))
    return path


def record(path):
    path = ordinary(path)
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'E_SR4_INPUT_LINK: '+str(path))
    raw = path.read_bytes()
    after = path.stat()
    require((after.st_dev, after.st_ino, after.st_mode, after.st_nlink, after.st_size,
             after.st_mtime_ns, after.st_ctime_ns) ==
            (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
             info.st_mtime_ns, info.st_ctime_ns), 'E_SR4_INPUT_CHANGED: '+str(path))
    return {'path': str(path), 'size': len(raw), 'sha256': sha(raw), 'links': 1}


def read(path):
    try:
        before = record(path)
        require(before['size'] <= MAX_JSON, 'E_SR4_JSON_LIMIT')
        raw = ordinary(path).read_bytes()
        require(sha(raw) == before['sha256'], 'E_SR4_INPUT_CHANGED')
        def unique(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, 'E_SR4_JSON_DUPLICATE_KEY')
                result[key] = value
            return result
        return json.loads(raw.decode('utf-8'), object_pairs_hook=unique)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError('E_SR4_JSON: '+str(path)) from error


def save(path, value):
    path = ordinary(Path(path))
    ordinary(path.parent)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, ensure_ascii=True,
                                 allow_nan=False) + '\n').encode('utf-8'))


def require_absent(path):
    path = ordinary(Path(path))
    require(not os.path.lexists(path), 'E_SR4_EXISTING: '+str(path))
    return path


def load_checked(path, digest):
    """Seal bytes before executing an imported support module."""
    path = Path(path)
    require(record(path)['sha256'] == digest, 'E_SR4_SUPPORT_CHANGED: '+str(path))
    raw = ordinary(path).read_bytes()
    require(sha(raw) == digest, 'E_SR4_SUPPORT_CHANGED: '+str(path))
    spec = importlib.util.spec_from_file_location('sr4_'+path.stem, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def c1_module():
    return load_checked(SCRIPTS/'gate1_current_preflight.py', C1_SHA)


def sc_module():
    return load_checked(SCRIPTS/'shutdown_copy_verification.py', SC_SHA)


def sr3_module():
    return load_checked(SCRIPTS/'shutdown_repair_verification.py', SR3_SHA)


def old_record(path, digest):
    row = record(path)
    require(row['sha256'] == digest, 'E_SR4_OLD_CONTROL: '+str(path))
    return row


def history(c1):
    """Bind the consumed failure's critical records, never unreadable temp data.

    This narrowly scoped D2 observation does not certify all private histories;
    D3 still requires fresh ORIGINAL BEFORE/AFTER, including copy cooperation.
    """
    pins = {name: old_record(OLD_ROOT/name, digest) for name, digest in OLD_PINS.items()}
    prior = read(OLD_ROOT/'run/Receipt.json')
    runtime = read(OLD_ROOT/'Runtime-Inputs.json')
    commands = []
    for command in prior['commands']:
        target = OLD_ROOT/'run'/command['label']
        require(read(target/'Command.json') == {k: v for k, v in command.items() if k != 'label'},
                'E_SR4_OLD_COMMAND')
        streams = []
        for role in ('stdout', 'stderr'):
            expected = command[role]
            require(Path(expected['path']) == target/(role+'.log'), 'E_SR4_OLD_STREAM_PATH')
            actual = record(Path(expected['path']))
            require({k: v for k, v in actual.items() if k != 'links'} == expected, 'E_SR4_OLD_STREAM')
            streams.append(actual)
        commands.append({'command': record(target/'Command.json'), 'streams': streams})
    require(len(commands) == 4, 'E_SR4_OLD_COMMAND_SET')
    unit = read(OLD_ROOT/'run/tests-ownership/Receipt.json')
    captured = (OLD_ROOT/'run/command-ownership/stdout.log').read_text(encoding='utf-8').splitlines()[0]
    require(json.loads(captured) == unit, 'E_SR4_OLD_UNIT_BINDING')
    expected_source = dict(runtime['source_manifest'])
    expected_source.update({name: row['sha256'] for name, row in runtime['live_delta'].items()})
    c1.verify_source(OLD_ROOT/'run/source', expected_source)
    return {'receipt': pins['run/Receipt.json'], 'pins': pins, 'commands': commands,
            'source_manifest': expected_source}


def verify_live_source(manifest, deltas):
    for name, digest in manifest.items():
        if name.startswith(('memory-integrity/', 'claude-mon/', 'semantica-runtime/', '.github/fixtures/')):
            expected = deltas[name]['sha256'] if name in deltas else digest
            require(record(REPO/name)['sha256'] == expected, 'E_SR4_LIVE_SOURCE: '+name)


def frozen():
    require(set(SR4_SOURCES) == set(SOURCE_NAMES) and
            all(isinstance(value, str) and len(value) == 64 and
                all(ch in '0123456789abcdef' for ch in value)
                for value in SR4_SOURCES.values()), 'E_SR4_UNFROZEN')
    require(isinstance(CASE_IDS, tuple) and CASE_IDS and len(CASE_IDS) == len(set(CASE_IDS)) and
            all(isinstance(value, str) and value.startswith('test_') and '.test_' in value
                for value in CASE_IDS), 'E_SR4_UNFROZEN')


def validate_cases(value, expected):
    require(isinstance(value, (list, tuple)) and isinstance(expected, (list, tuple)) and
            list(value) == list(expected) and bool(expected) and
            len(expected) == len(set(expected)), 'E_SR4_CASES')
    return list(value)


def validate_unit(value, expected_ids):
    expected_ids = validate_cases(expected_ids, expected_ids)
    require(isinstance(value, dict) and type(value.get('discovered')) is int and
            type(value.get('tests_run')) is int and
            value['discovered'] == value['tests_run'] == len(expected_ids) and
            all(value.get(key) == [] for key in
                ('failures', 'errors', 'skipped', 'excluded', 'expected_failures')) and
            value.get('interrupted') is False, 'E_SR4_UNIT')
    return value


def _role_frame(roles):
    required = {'image', 'sys_executable', 'prefix', 'base_prefix', 'base_executable', 'launcher'}
    require(isinstance(roles, dict) and set(roles) == required and
            all(isinstance(roles[key], str) and roles[key] for key in required - {'launcher'}) and
            (roles['launcher'] is None or isinstance(roles['launcher'], str)) and
            roles['base_executable'] != roles['image'], 'E_SR4_STARTUP')
    return roles


def validate_actual_startup(value, roles):
    """Validate the bounded positive worker frame, never a textual success label."""
    roles = _role_frame(roles)
    keys = {'expected', 'observed', 'termination', 'released'}
    require(isinstance(value, dict) and set(value) == keys and value['released'] is True,
            'E_SR4_STARTUP')
    expected = {**roles, 'token': value['expected'].get('token') if isinstance(value['expected'], dict) else None}
    require(isinstance(expected['token'], str) and len(expected['token']) == 64 and
            all(ch in '0123456789abcdef' for ch in expected['token']) and
            value['expected'] == expected, 'E_SR4_STARTUP')
    observed = {**expected, 'pid': value['observed'].get('pid') if isinstance(value['observed'], dict) else None,
                'in_any_job': value['observed'].get('in_any_job') if isinstance(value['observed'], dict) else None}
    termination = value['termination']
    require(isinstance(termination, dict) and set(termination) ==
            {'mode', 'native_exit_proved', 'records', 'accounting_total', 'operations', 'failures'} and
            termination['mode'] in ('graceful', 'forced', 'already-exited') and
            termination['native_exit_proved'] is True and
            type(termination['records']) is int and termination['records'] >= 1 and
            type(termination['accounting_total']) is int and
            termination['accounting_total'] == termination['records'] and
            isinstance(termination['operations'], list) and len(termination['operations']) <= 128 and
            all(isinstance(operation, str) and len(operation) <= 128 for operation in termination['operations']) and
            termination['failures'] == [],
            'E_SR4_STARTUP')
    require(value['observed'] == observed and type(observed['pid']) is int and observed['pid'] > 0 and
            observed['in_any_job'] is True, 'E_SR4_STARTUP')
    return value


def collect_unit(folder, expected_ids, roles, receipt, child_exit):
    """Retain actual diagnostics before rejecting any complete failed child."""
    folder = Path(folder)
    unit = read(folder/'Receipt.json')
    receipt['unit'] = unit
    receipt['unit_receipt'] = record(folder/'Receipt.json')
    require(Path(unit['log']) == folder/'unittest.log', 'E_SR4_UNIT_LOG_PATH')
    log = record(folder/'unittest.log')
    require(log['sha256'] == unit['log_sha256'] and log['size'] <= MAX_LOG, 'E_SR4_UNIT_LOG')
    receipt['unit_log'] = log
    receipt['unit_log_text'] = (folder/'unittest.log').read_text(encoding='utf-8')
    artifacts = []
    for parent, dirs, files in os.walk(folder/'retained-temp', followlinks=False,
                                      onerror=lambda error: (_ for _ in ()).throw(error)):
        ordinary(Path(parent))
        for name in dirs:
            ordinary(Path(parent)/name)
        if 'SR4-Actual-Startup.json' in files:
            path = Path(parent)/'SR4-Actual-Startup.json'
            row = record(path)
            require(row['size'] <= MAX_STARTUP, 'E_SR4_STARTUP_ARTIFACT_LIMIT')
            artifacts.append((row, read(path)))
    receipt['startup_artifacts'] = [row for row, _ in artifacts]
    if len(artifacts) == 1:
        receipt['startup'] = artifacts[0][1]
    # A failed unit may have no positive artifact. Still retain its full log.
    validate_unit(unit, expected_ids)
    require(type(child_exit) is int and child_exit == 0, 'E_SR4_UNIT_EXIT')
    require(len(artifacts) == 1, 'E_SR4_STARTUP_ARTIFACT_SET')
    validate_actual_startup(receipt['startup'], roles)
    return unit


def ownership_result(unit, expected_ids, observation, roles):
    validate_unit(unit, expected_ids)
    validate_actual_startup(observation, roles)
    return {'status': 'SR4_OWNERSHIP_OBSERVED_NOT_STAGE_COMPLETE',
            'ownership_observed': True, 'unit': unit, 'startup': observation,
            **dict.fromkeys(FLAGS, False)}


def source_authority():
    """Re-check only three reviewed D1 deltas plus immutable SR3 source bytes."""
    frozen()
    c1, sc, sr3 = c1_module(), sc_module(), sr3_module()
    manifest, tree = sc.source_basis(c1)
    immutable = {}
    for name, digest in sr3.SEALED_SOURCES.items():
        if name in SR4_SOURCES:
            continue
        immutable[name] = old_record(REPO/name, digest)
    require(old_record(REPO/ORIGINAL_OWNERSHIP, ORIGINAL_OWNERSHIP_SHA)['sha256'] ==
            ORIGINAL_OWNERSHIP_SHA, 'E_SR4_ORIGINAL_OWNERSHIP_CHANGED')
    changed = {name: record(REPO/name) for name in SOURCE_NAMES}
    require(all(changed[name]['sha256'] == SR4_SOURCES[name] for name in SOURCE_NAMES),
            'E_SR4_SOURCE_CHANGED')
    protected = c1.protected()
    old_record(OLD_ROOT/'Policy-Inputs.json', OLD_PINS['Policy-Inputs.json'])
    inputs = read(OLD_ROOT/'Policy-Inputs.json')['authority']
    require(set(protected) == set(inputs['protected']), 'E_SR4_PROTECTED_ROOTS')
    for root, prior in inputs['protected'].items():
        allowed = {name.removeprefix('memory-integrity/') for name in SOURCE_NAMES}
        if root != str(REPO/'memory-integrity'):
            allowed = set()
        sr3.validate_protected_delta(prior, protected[root], allowed)
    live_delta = {**immutable, **changed}
    verify_live_source(manifest, live_delta)
    require(record(REPO/'semantica-runtime/requirements-lock.txt')['sha256'] ==
            manifest['semantica-runtime/requirements-lock.txt'], 'E_SR4_DEPENDENCY_LOCK')
    runtime = c1.fixed_inputs()
    require(record(CONTROLLER)['sha256'] == runtime[str(Path(sys.executable))]['sha256'], 'E_SR4_CONTROLLER')
    return {'checkout_head': CHECKOUT_HEAD, 'evaluated_source_head': EVALUATED_HEAD,
            'source_manifest': manifest, 'tree': tree, 'immutable_sr3': immutable,
            'sr4_sources': changed, 'protected': protected,
            'runtime': runtime, 'dependencies': c1.dependency_versions(),
            'support': sr3.support_records(), 'history': history(c1),
            'controller': record(CONTROLLER), 'helper': record(Path(__file__).absolute())}


def build_contract():
    frozen()
    authority = source_authority()
    return {'schema': 1, 'scope': 'SR4_OWNERSHIP_STARTUP_ONLY_NOT_GATE1',
            'root': str(ROOT), 'controller': authority['controller'], 'helper': authority['helper'],
            'authority': authority, 'case_ids': list(CASE_IDS), 'budgets': BUDGETS,
            'ownership_observed': False, **dict.fromkeys(FLAGS, False)}


def validate_contract(value):
    keys = {'schema', 'scope', 'root', 'controller', 'helper', 'authority', 'case_ids', 'budgets',
            'ownership_observed', *FLAGS}
    require(isinstance(value, dict) and set(value) == keys and type(value['schema']) is int and value['schema'] == 1 and
            value['scope'] == 'SR4_OWNERSHIP_STARTUP_ONLY_NOT_GATE1' and
            value['root'] == str(ROOT) and value['controller'] == record(CONTROLLER) and
            value['helper'] == record(Path(__file__).absolute()) and
            value['budgets'] == BUDGETS and value['ownership_observed'] is False and
            all(value[key] is False for key in FLAGS), 'E_SR4_CONTRACT')
    frozen(); validate_cases(value['case_ids'], CASE_IDS)
    require(value['authority'] == source_authority(), 'E_SR4_DIRECT_AUTHORITY_CHANGED')
    return value


def normal():
    c1_module().normal_account()


def prepare(external_sha):
    """Create Inputs only after normal identity, authority and caller seal agree."""
    normal()
    value = build_contract()
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode('utf-8')
    require(sha(raw) == external_sha, 'E_SR4_EXTERNAL_INPUT')
    require_absent(ROOT)
    ordinary(ROOT.parent)
    ROOT.mkdir()
    save(ROOT/'Inputs.json', value)
    return {'status': 'SR4_INPUTS_ONLY_NO_SELECTED_RUNTIME', 'inputs': record(ROOT/'Inputs.json'),
            'stage_complete': False}


def execute(value, output, receipt):
    """One normal-account ownership/startup observation; no public retrieval."""
    c1, sr3 = c1_module(), sr3_module()
    authority = value['authority']
    def support(name):
        key = '.github/scripts/'+name+'.py'
        return load_checked(REPO/key, authority['support'][key]['sha256'])
    host, c2, g = support('offline_host_validation'), support('gate1_current_runtime'), support('gate1_validation')
    temp = output/'temp'; temp.mkdir()
    env = sr3.environment(c2, temp)
    def capture(label, argv, timeout, exits=(0,)):
        target = output/label; target.mkdir(); ordinary(target)
        print(label+': RUNNING (SR4 ownership/startup only, not stage qualification)', flush=True)
        completed, row = host.capture_owned(list(map(str, argv)), target, target, env, timeout)
        row['label'] = label; receipt['commands'].append(row)
        sr3.validate_capture(completed, row, exits)
        return completed
    identity = capture('preclaim-identity', [g.WORKER, '-B', '-c', g.runtime_probe()], 30)
    actual_identity = json.loads(identity.stdout)
    c1.validate_runtime(actual_identity, env, output/'preclaim-identity')
    receipt['runtime_identity'] = actual_identity
    dependency_script = "import importlib.metadata as m,json,site;d=m.distribution('semantica');u=json.loads(d.read_text('direct_url.json') or '{}');print(json.dumps({'versions':{n:m.version(n) for n in " + repr(sorted(authority['dependencies'])) + "},'revision':u.get('vcs_info',{}).get('commit_id'),'user_site':site.ENABLE_USER_SITE}))"
    deps = capture('preclaim-dependencies', [g.WORKER, '-B', '-c', dependency_script], 30)
    c1.validate_dependencies(json.loads(deps.stdout), authority['dependencies'])
    validate_contract(value)
    copied = output/'source'
    delta = {**authority['immutable_sr3'], **authority['sr4_sources']}
    copied_manifest = sr3.copy_source(c1, {'tree': authority['tree'], 'live_delta': delta}, copied)
    receipt['source_manifest'] = copied_manifest
    discovery = capture('discover-ownership', [g.WORKER, '-B', '-c', sr3.DISCOVERY_SCRIPT,
                                               copied/'memory-integrity', PATTERN], BUDGETS['watchdog'])
    ids = validate_cases(json.loads(discovery.stdout), value['case_ids'])
    receipt['discovered_ids'] = ids
    save(output/'workload-claim.json', {'scope': value['scope'], 'case_ids': ids, 'one_attempt': True})
    folder = output/'tests-ownership'
    completed = capture('command-ownership', sr3.test_argv(g.WORKER,
        copied/'.github/scripts/retained_unittest.py', copied, PATTERN, folder), BUDGETS['watchdog'], (0, 1))
    norm = lambda path: os.path.normcase(os.path.abspath(path))
    roles = {'image': norm(actual_identity['image_path']), 'sys_executable': norm(actual_identity['executable']),
             'prefix': norm(actual_identity['prefix']), 'base_prefix': norm(actual_identity['base_prefix']),
             'base_executable': norm(actual_identity['base_executable']), 'launcher': None}
    collect_unit(folder, ids, roles, receipt, completed.returncode)
    identity = capture('postclaim-identity', [g.WORKER, '-B', '-c', g.runtime_probe()], 30)
    c1.validate_runtime(json.loads(identity.stdout), env, output/'postclaim-identity')
    deps = capture('postclaim-dependencies', [g.WORKER, '-B', '-c', dependency_script], 30)
    c1.validate_dependencies(json.loads(deps.stdout), authority['dependencies'])
    c1.verify_source(copied, copied_manifest)
    receipt.update(ownership_result(receipt['unit'], ids, receipt['startup'], roles))


def run(external_sha):
    """Claim once; retain raw cause, failed units and post-check failures honestly."""
    normal()
    inputs = ROOT/'Inputs.json'
    require(record(inputs)['sha256'] == external_sha, 'E_SR4_EXTERNAL_INPUT')
    value = read(inputs)
    validate_contract(value)
    require_absent(ROOT/'Run-Claim.json')
    require_absent(ROOT/'Run-Failure.json')
    require_absent(ROOT/'run')
    save(ROOT/'Run-Claim.json', {'scope': value.get('scope'), 'input_sha256': external_sha,
                                'started_utc': datetime.now(timezone.utc).isoformat()})
    output = ROOT/'run'; output.mkdir(); ordinary(output)
    receipt = {'status': 'SR4_FAILED_NO_RETRY', 'ownership_observed': False,
               'input': record(inputs), 'started_utc': datetime.now(timezone.utc).isoformat(),
               'commands': [], 'failure': None, **dict.fromkeys(FLAGS, False)}
    try:
        execute(value, output, receipt)
    except BaseException:
        receipt['failure'] = traceback.format_exc()
    finally:
        try:
            validate_contract(value)
        except BaseException:
            receipt['postcheck_failure'] = traceback.format_exc()
        if receipt['failure'] is not None or receipt.get('postcheck_failure'):
            receipt.update(status='SR4_FAILED_NO_RETRY', ownership_observed=False)
        receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(output/'Receipt.json', receipt)
        if not receipt['ownership_observed']:
            save(ROOT/'Run-Failure.json', {'receipt': record(output/'Receipt.json'),
                                           'failure': receipt['failure'], 'postcheck_failure': receipt.get('postcheck_failure')})
    return {key: receipt[key] for key in ('status', 'ownership_observed', *FLAGS)} | {
        'receipt': record(output/'Receipt.json'), 'failure': receipt['failure']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('Prepare', 'Run'), required=True)
    parser.add_argument('--input-sha256', required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.input_sha256) if args.mode == 'Prepare' else run(args.input_sha256)
        print(json.dumps(result, sort_keys=True))
        return 0 if args.mode == 'Prepare' or result['ownership_observed'] else 1
    except BaseException as error:
        print(json.dumps({'status': 'SR4_STOP_NO_RETRY', 'mode': args.mode,
                          'failure': str(error), 'stage_complete': False}, sort_keys=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
