#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

SCHEMA_VERSION = 2
PRIORITIES = {'blocking', 'required', 'recommended', 'future', 'rejected'}
EVIDENCE_KINDS = {'automated', 'runtime', 'visual', 'manual', 'performance', 'data', 'operational'}
AUTH_SOURCES = {'conversation', 'user_input'}
FABLE_METADATA_EXACT = {
    'docs/fable/requirements.json',
    'docs/fable/plan.json',
    'docs/fable/tests.json',
    'docs/fable/approvals.json',
    'docs/fable/state.json',
    'docs/fable/evidence/index.json',
}
FABLE_METADATA_PREFIXES = (
    'docs/fable/evidence/runs/',
    'docs/fable/derived/strictdoc/',
)


def canonical_digest(obj):
    data = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def file_identity(path: Path):
    if path.is_symlink():
        return 'symlink:' + os.readlink(path)
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return '<DELETED>'


def artifact_digest(project: Path, paths):
    h = hashlib.sha256()
    for rel in sorted(paths):
        file_path = project / rel
        if not file_path.is_file() or file_path.is_symlink():
            return None
        h.update(rel.encode('utf-8'))
        h.update(b'\0')
        h.update(file_path.read_bytes())
        h.update(b'\0')
    return h.hexdigest()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError(f'E_FILE_MISSING: {path}')
    except json.JSONDecodeError as exc:
        raise ValueError(f'E_JSON_INVALID: {path}: {exc}')


def write_json_atomic(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temp.replace(path)


def add_error(errors, code, message):
    errors.append(f'{code}: {message}')


def validate_keys(obj, *, required, allowed, where, errors):
    if not isinstance(obj, dict):
        add_error(errors, 'E_SCHEMA_TYPE', f'{where} must be an object')
        return False
    unknown = sorted(set(obj) - set(allowed))
    if unknown:
        add_error(errors, 'E_SCHEMA_FIELD', f'{where} has unsupported field(s): {", ".join(unknown)}')
    missing = sorted(set(required) - set(obj))
    if missing:
        add_error(errors, 'E_SCHEMA_REQUIRED', f'{where} missing required field(s): {", ".join(missing)}')
    return not missing


def validate_schema(doc, name, errors):
    if not isinstance(doc, dict):
        add_error(errors, 'E_SCHEMA_TYPE', f'{name} must be an object')
        return
    if doc.get('schema') != SCHEMA_VERSION:
        add_error(errors, 'E_SCHEMA_VERSION', f'{name}.schema must be {SCHEMA_VERSION}, got {doc.get("schema")!r}')


def ensure_nonempty_string(value, where, errors):
    if not isinstance(value, str) or not value.strip():
        add_error(errors, 'E_SCHEMA_VALUE', f'{where} must be a non-empty string')
        return False
    return True


def ensure_string_list(value, where, errors, *, allow_empty=True):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        add_error(errors, 'E_SCHEMA_TYPE', f'{where} must be a list of non-empty strings')
        return False
    if not allow_empty and not value:
        add_error(errors, 'E_SCHEMA_VALUE', f'{where} must not be empty')
        return False
    return True


def validate_id_uniqueness(rows, where, errors):
    seen = set()
    for idx, row in enumerate(rows if isinstance(rows, list) else []):
        if not isinstance(row, dict):
            continue
        ident = row.get('id')
        if not isinstance(ident, str) or not ident.strip():
            add_error(errors, 'E_SCHEMA_VALUE', f'{where}[{idx}].id must be a non-empty string')
            continue
        if ident in seen:
            add_error(errors, 'E_ID_DUPLICATE', f'duplicate id {ident!r} in {where}')
        seen.add(ident)
    return seen


def normalize_project_path(project: Path, rel, where, errors):
    if not isinstance(rel, str) or not rel.strip():
        add_error(errors, 'E_PATH_INVALID', f'{where} must be a non-empty relative path')
        return None
    if Path(rel).is_absolute() or re.match(r'^[A-Za-z]:[\\/]', rel) or rel.startswith('\\\\'):
        add_error(errors, 'E_PATH_ESCAPE', f'{where} must stay inside project root: {rel}')
        return None
    portable_parts = rel.replace('\\', '/').split('/')
    if '..' in portable_parts:
        add_error(errors, 'E_PATH_ESCAPE', f'{where} contains parent traversal: {rel}')
        return None
    root = project.resolve()
    candidate = (project / rel).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        add_error(errors, 'E_PATH_ESCAPE', f'{where} resolves outside project root: {rel}')
        return None
    return Path(rel).as_posix()


def validate_source_links(project, links, where, errors):
    if links is None:
        return
    if not isinstance(links, list):
        add_error(errors, 'E_SCHEMA_TYPE', f'{where} must be a list')
        return
    for idx, link in enumerate(links):
        loc = f'{where}[{idx}]'
        if not validate_keys(
            link,
            required={'path'},
            allowed={'path', 'function', 'class', 'line_range'},
            where=loc,
            errors=errors,
        ):
            continue
        normalize_project_path(project, link.get('path'), f'{loc}.path', errors)
        if 'function' in link:
            ensure_nonempty_string(link.get('function'), f'{loc}.function', errors)
        if 'class' in link:
            ensure_nonempty_string(link.get('class'), f'{loc}.class', errors)
        if 'function' in link and 'class' in link:
            add_error(errors, 'E_SCHEMA_VALUE', f'{loc} cannot specify both function and class')
        if 'line_range' in link:
            lr = link.get('line_range')
            if not (
                isinstance(lr, list) and len(lr) == 2
                and all(isinstance(x, int) and x > 0 for x in lr)
                and lr[0] <= lr[1]
            ):
                add_error(errors, 'E_SCHEMA_VALUE', f'{loc}.line_range must be [positive_start, positive_end]')


def validate_core_docs(project: Path, requirements, plan, tests):
    errors = []
    validate_schema(requirements, 'requirements.json', errors)
    validate_schema(plan, 'plan.json', errors)
    validate_schema(tests, 'tests.json', errors)

    validate_keys(
        requirements,
        required={'schema', 'requirements'},
        allowed={'schema', 'requirements'},
        where='requirements.json',
        errors=errors,
    )
    validate_keys(
        plan,
        required={'schema', 'plan_id', 'milestone', 'tasks'},
        allowed={'schema', 'plan_id', 'milestone', 'tasks'},
        where='plan.json',
        errors=errors,
    )
    validate_keys(
        tests,
        required={'schema', 'tests'},
        allowed={'schema', 'tests'},
        where='tests.json',
        errors=errors,
    )

    requirement_rows = requirements.get('requirements')
    task_rows = plan.get('tasks')
    test_rows = tests.get('tests')
    if not isinstance(requirement_rows, list):
        add_error(errors, 'E_SCHEMA_TYPE', 'requirements.json.requirements must be a list')
        requirement_rows = []
    if not isinstance(task_rows, list):
        add_error(errors, 'E_SCHEMA_TYPE', 'plan.json.tasks must be a list')
        task_rows = []
    if not isinstance(test_rows, list):
        add_error(errors, 'E_SCHEMA_TYPE', 'tests.json.tests must be a list')
        test_rows = []

    ensure_nonempty_string(plan.get('plan_id'), 'plan.json.plan_id', errors)
    ensure_nonempty_string(plan.get('milestone'), 'plan.json.milestone', errors)

    requirement_ids = validate_id_uniqueness(requirement_rows, 'requirements', errors)
    task_ids = validate_id_uniqueness(task_rows, 'tasks', errors)
    test_ids = validate_id_uniqueness(test_rows, 'tests', errors)
    del task_ids

    criterion_ids = set()
    criterion_owner = {}
    criterion_tests = {}
    requirement_tests = {}
    required_requirement_ids = set()

    for idx, row in enumerate(requirement_rows):
        loc = f'requirements[{idx}]'
        if not validate_keys(
            row,
            required={'id', 'text', 'priority', 'criteria', 'test_ids'},
            allowed={'id', 'text', 'priority', 'criteria', 'test_ids', 'source_links'},
            where=loc,
            errors=errors,
        ):
            continue
        req_id = row.get('id')
        ensure_nonempty_string(row.get('text'), f'{loc}.text', errors)
        priority = row.get('priority')
        if priority not in PRIORITIES:
            add_error(errors, 'E_SCHEMA_ENUM', f'{loc}.priority must be one of {sorted(PRIORITIES)}, got {priority!r}')
        if priority in {'blocking', 'required'} and isinstance(req_id, str):
            required_requirement_ids.add(req_id)
        if priority in {'blocking', 'required'} and isinstance(row.get('test_ids'), list) and not row.get('test_ids'):
            add_error(errors, 'E_TEST_MISSING', f'{req_id} has no required verification ids')
        if ensure_string_list(row.get('test_ids'), f'{loc}.test_ids', errors, allow_empty=False):
            requirement_tests[req_id] = set(row.get('test_ids') or [])
        else:
            requirement_tests[req_id] = set()
        criteria = row.get('criteria')
        if not isinstance(criteria, list):
            add_error(errors, 'E_SCHEMA_TYPE', f'{loc}.criteria must be a list')
            criteria = []
        for cidx, criterion in enumerate(criteria):
            cloc = f'{loc}.criteria[{cidx}]'
            if not validate_keys(
                criterion,
                required={'id', 'text', 'test_ids'},
                allowed={'id', 'text', 'test_ids', 'source_links'},
                where=cloc,
                errors=errors,
            ):
                continue
            cid = criterion.get('id')
            if not isinstance(cid, str) or not cid.strip():
                add_error(errors, 'E_SCHEMA_VALUE', f'{cloc}.id must be a non-empty string')
            elif cid in criterion_ids:
                add_error(errors, 'E_ID_DUPLICATE', f'duplicate criterion id {cid!r}')
            else:
                criterion_ids.add(cid)
                criterion_owner[cid] = req_id
            ensure_nonempty_string(criterion.get('text'), f'{cloc}.text', errors)
            if priority in {'blocking', 'required'} and isinstance(criterion.get('test_ids'), list) and not criterion.get('test_ids'):
                add_error(errors, 'E_CRITERIA_TEST_MISSING', f'{cid} has no direct verification ids')
            if ensure_string_list(criterion.get('test_ids'), f'{cloc}.test_ids', errors, allow_empty=False):
                criterion_tests[cid] = set(criterion.get('test_ids') or [])
            else:
                criterion_tests[cid] = set()
            validate_source_links(project, criterion.get('source_links'), f'{cloc}.source_links', errors)
        validate_source_links(project, row.get('source_links'), f'{loc}.source_links', errors)

    test_catalog = {}
    for idx, row in enumerate(test_rows):
        loc = f'tests[{idx}]'
        if not validate_keys(
            row,
            required={'id', 'kind'},
            allowed={
                'id', 'kind', 'argv', 'expect', 'shell_command', 'shell_authorized',
                'authorization_ref', 'instructions', 'source_links'
            },
            where=loc,
            errors=errors,
        ):
            continue
        test_id = row.get('id')
        kind = row.get('kind')
        if kind not in EVIDENCE_KINDS:
            add_error(errors, 'E_SCHEMA_ENUM', f'{loc}.kind must be one of {sorted(EVIDENCE_KINDS)}, got {kind!r}')
        if isinstance(test_id, str) and test_id:
            test_catalog[test_id] = row
        if kind == 'automated':
            has_argv = 'argv' in row
            has_shell = 'shell_command' in row
            if has_argv == has_shell:
                add_error(errors, 'E_TEST_EXECUTION', f'{loc} must define exactly one of argv or shell_command')
            if row.get('expect') != 'exit=0':
                add_error(errors, 'E_TEST_EXPECT_UNSUPPORTED', f'{test_id}: automated runner supports only expect=exit=0')
            if has_argv:
                argv = row.get('argv')
                if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
                    add_error(errors, 'E_TEST_EXECUTION', f'{loc}.argv must be a non-empty string array')
            if has_shell:
                ensure_nonempty_string(row.get('shell_command'), f'{loc}.shell_command', errors)
                if row.get('shell_authorized') is not True or not isinstance(row.get('authorization_ref'), str) or not row.get('authorization_ref').strip():
                    add_error(errors, 'E_SHELL_AUTH', f'{test_id}: shell_command requires shell_authorized=true and authorization_ref')
        else:
            if 'argv' in row or 'shell_command' in row:
                add_error(errors, 'E_TEST_KIND', f'{test_id}: {kind} evidence must be recorded, not executed by the built-in runner')
            ensure_nonempty_string(row.get('instructions'), f'{loc}.instructions', errors)
        validate_source_links(project, row.get('source_links'), f'{loc}.source_links', errors)

    for req_id, refs in requirement_tests.items():
        for test_id in refs:
            if test_id not in test_ids:
                add_error(errors, 'E_REF_TEST', f'{req_id} references unknown test {test_id}')
    for cid, refs in criterion_tests.items():
        owner = criterion_owner.get(cid)
        for test_id in refs:
            if test_id not in test_ids:
                add_error(errors, 'E_REF_TEST', f'{cid} references unknown test {test_id}')
            if owner in requirement_tests and test_id not in requirement_tests[owner]:
                add_error(errors, 'E_CRITERIA_TEST_REF', f'{cid}->{test_id} is not declared by parent requirement {owner}')

    task_catalog = []
    for idx, task in enumerate(task_rows):
        loc = f'tasks[{idx}]'
        if not validate_keys(
            task,
            required={'id', 'requirement_ids', 'criterion_ids', 'test_ids', 'artifacts', 'action'},
            allowed={'id', 'requirement_ids', 'criterion_ids', 'test_ids', 'artifacts', 'action'},
            where=loc,
            errors=errors,
        ):
            continue
        ensure_nonempty_string(task.get('action'), f'{loc}.action', errors)
        for key in ('requirement_ids', 'criterion_ids', 'test_ids', 'artifacts'):
            ensure_string_list(task.get(key), f'{loc}.{key}', errors, allow_empty=(key != 'requirement_ids'))
        mapped_req_ids = set(task.get('requirement_ids') or [])
        mapped_criterion_ids = set(task.get('criterion_ids') or [])
        mapped_test_ids = set(task.get('test_ids') or [])
        for req_id in mapped_req_ids:
            if req_id not in requirement_ids:
                add_error(errors, 'E_REF_REQUIREMENT', f'{task.get("id")} references unknown requirement {req_id}')
        for cid in mapped_criterion_ids:
            if cid not in criterion_ids:
                add_error(errors, 'E_REF_CRITERION', f'{task.get("id")} references unknown criterion {cid}')
            elif criterion_owner.get(cid) not in mapped_req_ids:
                add_error(errors, 'E_REF_CRITERION_SCOPE', f'{task.get("id")} maps {cid} without its parent requirement {criterion_owner.get(cid)}')
        permitted_tests = set()
        for req_id in mapped_req_ids:
            permitted_tests |= requirement_tests.get(req_id, set())
        for test_id in mapped_test_ids:
            if test_id not in test_ids:
                add_error(errors, 'E_REF_TEST', f'{task.get("id")} references unknown test {test_id}')
            elif test_id not in permitted_tests:
                add_error(errors, 'E_REF_TEST_SCOPE', f'{task.get("id")} uses test {test_id} not declared by mapped requirements')
        normalized_artifacts = []
        for aidx, artifact in enumerate(task.get('artifacts') or []):
            norm = normalize_project_path(project, artifact, f'{loc}.artifacts[{aidx}]', errors)
            if norm:
                normalized_artifacts.append(norm)
        task_catalog.append((task, mapped_req_ids, mapped_criterion_ids, mapped_test_ids, normalized_artifacts))

    covered_requirements = set()
    for _, reqs, _, _, _ in task_catalog:
        covered_requirements |= reqs
    missing = sorted(required_requirement_ids - covered_requirements)
    if missing:
        add_error(errors, 'E_REQ_COVERAGE', f'requirements missing from plan: {", ".join(missing)}')

    for req in requirement_rows:
        if not isinstance(req, dict):
            continue
        req_id = req.get('id')
        if req_id not in required_requirement_ids:
            continue
        planned_tests = set()
        planned_criteria = set()
        for _, reqs, criteria, task_tests, _ in task_catalog:
            if req_id in reqs:
                planned_tests |= task_tests
                planned_criteria |= criteria
        missing_tests = sorted(requirement_tests.get(req_id, set()) - planned_tests)
        if missing_tests:
            add_error(errors, 'E_PLAN_TEST_COVERAGE', f'{req_id} missing mapped plan tests: {", ".join(missing_tests)}')
        req_criteria = [c for c in (req.get('criteria') or []) if isinstance(c, dict) and c.get('id')]
        required_criteria = {c['id'] for c in req_criteria}
        missing_criteria = sorted(required_criteria - planned_criteria)
        if missing_criteria:
            add_error(errors, 'E_CRITERIA_COVERAGE', f'{req_id} acceptance criteria missing from plan: {", ".join(missing_criteria)}')
        for criterion in req_criteria:
            cid = criterion.get('id')
            tasks_for_criterion = [t for t in task_catalog if cid in t[2]]
            criterion_plan_tests = set()
            for task_info in tasks_for_criterion:
                criterion_plan_tests |= task_info[3]
            missing_criterion_tests = sorted(criterion_tests.get(cid, set()) - criterion_plan_tests)
            if missing_criterion_tests:
                add_error(errors, 'E_CRITERIA_TEST_COVERAGE', f'{cid} missing direct mapped tests: {", ".join(missing_criterion_tests)}')

    return {
        'errors': errors,
        'requirement_rows': requirement_rows,
        'task_rows': task_rows,
        'test_rows': test_rows,
        'required_requirement_ids': required_requirement_ids,
        'requirement_tests': requirement_tests,
        'criterion_owner': criterion_owner,
        'criterion_tests': criterion_tests,
        'test_catalog': test_catalog,
        'task_catalog': task_catalog,
    }


def git_write_set(project: Path):
    try:
        top = subprocess.run(
            ['git', '-C', str(project), 'rev-parse', '--show-toplevel'],
            text=True, capture_output=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ValueError(f'E_WRITESET_UNAVAILABLE: git repository required for execute/complete scope enforcement: {exc}')
    if Path(top).resolve() != project.resolve():
        raise ValueError(f'E_WRITESET_UNAVAILABLE: project root must equal git root ({top})')
    try:
        tracked = subprocess.run(
            ['git', '-C', str(project), 'diff', '--name-only', 'HEAD'],
            text=True, capture_output=True, check=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ['git', '-C', str(project), 'ls-files', '--others', '--exclude-standard'],
            text=True, capture_output=True, check=True,
        ).stdout.splitlines()
    except subprocess.CalledProcessError as exc:
        raise ValueError(f'E_WRITESET_UNAVAILABLE: unable to inspect git write set: {exc.stderr.strip()}')
    result = {}
    for rel in sorted(set(filter(None, tracked)) | set(filter(None, untracked))):
        normalized = Path(rel).as_posix()
        result[normalized] = file_identity(project / normalized)
    return result


def is_fable_metadata(path):
    return path in FABLE_METADATA_EXACT or any(path.startswith(prefix) for prefix in FABLE_METADATA_PREFIXES)


def validate_approvals(project, approvals, milestone, current_req, current_plan, current_tests, errors):
    validate_schema(approvals, 'approvals.json', errors)
    validate_keys(
        approvals,
        required={'schema', 'approvals'},
        allowed={'schema', 'approvals'},
        where='approvals.json',
        errors=errors,
    )
    rows = approvals.get('approvals')
    if not isinstance(rows, list):
        add_error(errors, 'E_SCHEMA_TYPE', 'approvals.json.approvals must be a list')
        return None
    validate_id_uniqueness(rows, 'approvals', errors)
    relevant = []
    for idx, row in enumerate(rows):
        loc = f'approvals[{idx}]'
        if not validate_keys(
            row,
            required={
                'id', 'scope', 'approved', 'requirements_digest', 'plan_digest', 'tests_digest',
                'write_set_baseline', 'approved_at', 'actor', 'authorization'
            },
            allowed={
                'id', 'scope', 'approved', 'requirements_digest', 'plan_digest', 'tests_digest',
                'write_set_baseline', 'approved_at', 'actor', 'authorization'
            },
            where=loc,
            errors=errors,
        ):
            continue
        if not isinstance(row.get('approved'), bool):
            add_error(errors, 'E_SCHEMA_TYPE', f'{loc}.approved must be boolean')
        for key in ('scope', 'requirements_digest', 'plan_digest', 'tests_digest', 'approved_at', 'actor'):
            ensure_nonempty_string(row.get(key), f'{loc}.{key}', errors)
        baseline = row.get('write_set_baseline')
        if not isinstance(baseline, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in (baseline or {}).items()):
            add_error(errors, 'E_SCHEMA_TYPE', f'{loc}.write_set_baseline must be an object mapping path to content identity')
        else:
            for rel in baseline:
                normalize_project_path(project, rel, f'{loc}.write_set_baseline[{rel}]', errors)
        auth = row.get('authorization')
        if not isinstance(auth, dict):
            add_error(errors, 'E_APPROVAL_AUTH', f'{loc}.authorization must record source and quote')
        else:
            validate_keys(
                auth,
                required={'source', 'quote'},
                allowed={'source', 'quote', 'message_id'},
                where=f'{loc}.authorization',
                errors=errors,
            )
            if auth.get('source') not in AUTH_SOURCES:
                add_error(errors, 'E_APPROVAL_AUTH', f'{loc}.authorization.source must be one of {sorted(AUTH_SOURCES)}')
            if not isinstance(auth.get('quote'), str) or not auth.get('quote').strip():
                add_error(errors, 'E_APPROVAL_AUTH', f'{loc}.authorization.quote must be non-empty')
        if row.get('actor') != 'user':
            add_error(errors, 'E_APPROVAL_AUTH', f'{loc}.actor must be user')
        if row.get('approved') is True and row.get('scope') == milestone:
            relevant.append(row)

    if not relevant:
        add_error(errors, 'E_APPROVAL_MISSING', f'no active approval for milestone {milestone}')
        return None
    matching = [
        row for row in relevant
        if row.get('requirements_digest') == current_req
        and row.get('plan_digest') == current_plan
        and row.get('tests_digest') == current_tests
    ]
    if not matching:
        ids = ', '.join(str(row.get('id', '<unknown>')) for row in relevant)
        add_error(errors, 'E_APPROVAL_STALE', f'approval digest no longer matches current requirements/plan/tests: {ids}')
        return None
    return matching[-1]


def approved_artifacts(task_catalog):
    return {artifact for _, _, _, _, artifacts in task_catalog for artifact in artifacts}


def enforce_write_set(project, approval, task_catalog, errors):
    if approval is None:
        return
    try:
        current = git_write_set(project)
    except ValueError as exc:
        errors.append(str(exc))
        return
    baseline = approval.get('write_set_baseline') or {}
    changed_since_approval = {
        path for path in (set(current) | set(baseline))
        if current.get(path) != baseline.get(path)
    }
    allowed = approved_artifacts(task_catalog)
    unplanned = sorted(path for path in changed_since_approval if path not in allowed and not is_fable_metadata(path))
    if unplanned:
        add_error(errors, 'E_WRITESET_SCOPE', f'changed paths outside approved artifacts/Fable metadata: {", ".join(unplanned)}')


def validate_state(state, errors):
    validate_schema(state, 'state.json', errors)
    validate_keys(
        state,
        required={
            'schema', 'campaign_id', 'milestone', 'phase', 'current_task', 'next_action',
            'completed_requirement_ids', 'basis'
        },
        allowed={
            'schema', 'campaign_id', 'milestone', 'phase', 'current_task', 'next_action',
            'completed_requirement_ids', 'basis'
        },
        where='state.json',
        errors=errors,
    )
    ensure_nonempty_string(state.get('campaign_id'), 'state.json.campaign_id', errors)
    ensure_nonempty_string(state.get('milestone'), 'state.json.milestone', errors)
    ensure_nonempty_string(state.get('phase'), 'state.json.phase', errors)
    if state.get('current_task') is not None and not isinstance(state.get('current_task'), str):
        add_error(errors, 'E_SCHEMA_TYPE', 'state.json.current_task must be string or null')
    ensure_nonempty_string(state.get('next_action'), 'state.json.next_action', errors)
    ensure_string_list(state.get('completed_requirement_ids'), 'state.json.completed_requirement_ids', errors)
    basis = state.get('basis')
    if isinstance(basis, dict):
        validate_keys(
            basis,
            required={'requirements_digest', 'plan_digest', 'tests_digest'},
            allowed={'requirements_digest', 'plan_digest', 'tests_digest'},
            where='state.json.basis',
            errors=errors,
        )
    else:
        add_error(errors, 'E_SCHEMA_TYPE', 'state.json.basis must be an object')


def evidence_paths(project):
    base = project / 'docs' / 'fable' / 'evidence'
    return base, base / 'index.json', base / 'runs'


def load_evidence(project, errors):
    base, index_path, runs_dir = evidence_paths(project)
    del base
    index = load_json(index_path)
    validate_schema(index, 'evidence/index.json', errors)
    validate_keys(
        index,
        required={'schema', 'run_ids', 'current_run_id'},
        allowed={'schema', 'run_ids', 'current_run_id'},
        where='evidence/index.json',
        errors=errors,
    )
    run_ids = index.get('run_ids')
    if not isinstance(run_ids, list) or any(not isinstance(x, str) or not x for x in run_ids):
        add_error(errors, 'E_SCHEMA_TYPE', 'evidence/index.json.run_ids must be a list of non-empty strings')
        run_ids = []
    if len(run_ids) != len(set(run_ids)):
        add_error(errors, 'E_ID_DUPLICATE', 'evidence/index.json.run_ids contains duplicates')
    current = index.get('current_run_id')
    if current is not None and current not in run_ids:
        add_error(errors, 'E_REF_EVIDENCE', 'current_run_id must be null or reference run_ids')
    batches = []
    observations = []
    for run_id in run_ids:
        run_path = runs_dir / f'{run_id}.json'
        try:
            batch = load_json(run_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        validate_schema(batch, f'evidence/runs/{run_id}.json', errors)
        validate_keys(
            batch,
            required={'schema', 'run_id', 'created_at', 'basis', 'observations'},
            allowed={'schema', 'run_id', 'created_at', 'basis', 'observations'},
            where=f'evidence/runs/{run_id}.json',
            errors=errors,
        )
        if batch.get('run_id') != run_id:
            add_error(errors, 'E_REF_EVIDENCE', f'evidence file {run_id}.json contains run_id={batch.get("run_id")!r}')
        if not isinstance(batch.get('observations'), list):
            add_error(errors, 'E_SCHEMA_TYPE', f'evidence run {run_id}.observations must be a list')
            continue
        batches.append(batch)
        observations.extend(batch.get('observations') or [])
    return index, batches, observations


def append_evidence_batch(project, observations, basis):
    _, index_path, runs_dir = evidence_paths(project)
    if index_path.exists():
        index = load_json(index_path)
        if index.get('schema') != SCHEMA_VERSION:
            raise ValueError(f'E_SCHEMA_VERSION: evidence/index.json.schema must be {SCHEMA_VERSION}')
    else:
        index = {'schema': SCHEMA_VERSION, 'run_ids': [], 'current_run_id': None}
    now = dt.datetime.now(dt.timezone.utc)
    run_id = now.strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    run_path = runs_dir / f'{run_id}.json'
    if run_path.exists():
        raise ValueError(f'E_EVIDENCE_IMMUTABLE: evidence run already exists: {run_id}')
    batch = {
        'schema': SCHEMA_VERSION,
        'run_id': run_id,
        'created_at': now.isoformat(),
        'basis': basis,
        'observations': observations,
    }
    runs_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(run_path, batch)
    new_index = {
        'schema': SCHEMA_VERSION,
        'run_ids': [*(index.get('run_ids') or []), run_id],
        'current_run_id': run_id,
    }
    write_json_atomic(index_path, new_index)
    return run_id


def check_project(project: Path, gate: str):
    docs = project / 'docs' / 'fable'
    requirements = load_json(docs / 'requirements.json')
    plan = load_json(docs / 'plan.json')
    tests = load_json(docs / 'tests.json')
    core = validate_core_docs(project, requirements, plan, tests)
    errors = core['errors']

    current_req = canonical_digest(requirements)
    current_plan = canonical_digest(plan)
    current_tests = canonical_digest(tests)
    matching_approval = None

    if gate in {'execute', 'complete'}:
        approvals = load_json(docs / 'approvals.json')
        matching_approval = validate_approvals(
            project, approvals, plan.get('milestone'), current_req, current_plan, current_tests, errors
        )
        enforce_write_set(project, matching_approval, core['task_catalog'], errors)

    if gate == 'resume':
        state = load_json(docs / 'state.json')
        validate_state(state, errors)
        basis = state.get('basis') or {}
        drift = []
        if basis.get('requirements_digest') != current_req:
            drift.append('requirements')
        if basis.get('plan_digest') != current_plan:
            drift.append('plan')
        if basis.get('tests_digest') != current_tests:
            drift.append('tests')
        if drift:
            add_error(errors, 'E_RECOVERY_DRIFT', f'saved state basis does not match current {"/".join(drift)}')
        if state.get('milestone') != plan.get('milestone'):
            add_error(errors, 'E_RECOVERY_MILESTONE', 'saved milestone does not match current plan')
        task_ids = {task.get('id') for task in core['task_rows'] if isinstance(task, dict) and task.get('id')}
        current_task = state.get('current_task')
        if current_task and current_task not in task_ids:
            add_error(errors, 'E_RECOVERY_TASK', f'saved current task is not in current plan: {current_task}')

    if gate == 'complete':
        state = load_json(docs / 'state.json')
        validate_state(state, errors)
        basis = state.get('basis') or {}
        state_drift = []
        if basis.get('requirements_digest') != current_req:
            state_drift.append('requirements')
        if basis.get('plan_digest') != current_plan:
            state_drift.append('plan')
        if basis.get('tests_digest') != current_tests:
            state_drift.append('tests')
        if state_drift:
            add_error(errors, 'E_RECOVERY_DRIFT', f'completion state basis does not match current {"/".join(state_drift)}')

        _, batches, observations = load_evidence(project, errors)
        del batches
        completed = state.get('completed_requirement_ids') or []
        missing_completed = sorted(core['required_requirement_ids'] - set(completed))
        if missing_completed:
            add_error(errors, 'E_COMPLETION_COVERAGE', f'required requirements not marked complete: {", ".join(missing_completed)}')

        requirement_map = {
            row.get('id'): row for row in core['requirement_rows'] if isinstance(row, dict) and row.get('id')
        }
        for req_id in completed:
            req = requirement_map.get(req_id)
            if not req:
                add_error(errors, 'E_COMPLETION_UNKNOWN', f'completed requirement does not exist: {req_id}')
                continue
            expected_artifacts = sorted({
                artifact
                for _, reqs, _, _, artifacts in core['task_catalog']
                if req_id in reqs
                for artifact in artifacts
            })
            criteria_for_req = {
                c.get('id'): set(c.get('test_ids') or [])
                for c in (req.get('criteria') or []) if isinstance(c, dict) and c.get('id')
            }
            for test_id in req.get('test_ids') or []:
                test = core['test_catalog'].get(test_id) or {}
                expected_criteria = sorted(cid for cid, tids in criteria_for_req.items() if test_id in tids)
                candidates = []
                for obs in observations:
                    if not isinstance(obs, dict):
                        continue
                    obs_basis = obs.get('basis') or {}
                    if (
                        obs.get('test_id') == test_id
                        and req_id in (obs.get('requirement_ids') or [])
                        and obs.get('result') == 'pass'
                        and obs.get('evidence_type') == test.get('kind')
                        and obs_basis.get('requirements_digest') == current_req
                        and obs_basis.get('plan_digest') == current_plan
                        and obs_basis.get('tests_digest') == current_tests
                    ):
                        candidates.append(obs)
                if not candidates:
                    add_error(errors, 'E_COMPLETION_EVIDENCE', f'{req_id} lacks fresh passing evidence for {test_id}')
                    continue
                criterion_scoped = [
                    obs for obs in candidates
                    if all(cid in (obs.get('criterion_ids') or []) for cid in expected_criteria)
                ]
                if expected_criteria and not criterion_scoped:
                    add_error(errors, 'E_EVIDENCE_CRITERIA', f'{req_id} evidence for {test_id} lacks criterion links: {", ".join(expected_criteria)}')
                    continue
                scoped = [
                    obs for obs in (criterion_scoped if expected_criteria else candidates)
                    if sorted(obs.get('artifacts') or []) == expected_artifacts and expected_artifacts
                ]
                if not scoped:
                    add_error(errors, 'E_EVIDENCE_SCOPE', f'{req_id} evidence for {test_id} does not cover exact planned artifacts')
                    continue
                fresh = [
                    obs for obs in scoped
                    if obs.get('artifacts_digest') == artifact_digest(project, obs.get('artifacts') or [])
                ]
                if not fresh:
                    add_error(errors, 'E_EVIDENCE_STALE', f'{req_id} evidence for {test_id} does not match current artifacts')

    return errors


def automated_observation(project, req_id, criterion_ids, test_id, test, artifacts, basis, timeout):
    started = dt.datetime.now(dt.timezone.utc)
    try:
        if 'argv' in test:
            proc = subprocess.run(
                test['argv'],
                shell=False,
                cwd=project,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            command_repr = {'argv': test['argv']}
        else:
            proc = subprocess.run(
                test['shell_command'],
                shell=True,
                cwd=project,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            command_repr = {
                'shell_command': test['shell_command'],
                'authorization_ref': test.get('authorization_ref'),
            }
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout or ''
        stderr = exc.stderr or ''
        command_repr = {'argv': test.get('argv')} if 'argv' in test else {
            'shell_command': test.get('shell_command'), 'authorization_ref': test.get('authorization_ref')
        }
    passed = exit_code == 0
    return {
        'id': 'EV-' + uuid.uuid4().hex,
        'test_id': test_id,
        'requirement_ids': [req_id],
        'criterion_ids': sorted(criterion_ids),
        'evidence_type': 'automated',
        'result': 'pass' if passed else 'fail',
        'exit_code': exit_code,
        'observed_at': started.isoformat(),
        'observer': 'fable_guard',
        'source': 'subprocess',
        'command': command_repr,
        'stdout_tail': str(stdout)[-2000:],
        'stderr_tail': str(stderr)[-2000:],
        'artifacts': artifacts,
        'artifacts_digest': artifact_digest(project, artifacts) if artifacts else None,
        'basis': basis,
    }


def run_project_tests(project: Path, timeout: int):
    gate_errors = check_project(project, 'execute')
    if gate_errors:
        for error in gate_errors:
            print(error)
        return 0, len(gate_errors), False

    docs = project / 'docs' / 'fable'
    requirements = load_json(docs / 'requirements.json')
    plan = load_json(docs / 'plan.json')
    tests = load_json(docs / 'tests.json')
    core = validate_core_docs(project, requirements, plan, tests)
    test_catalog = core['test_catalog']
    basis = {
        'requirements_digest': canonical_digest(requirements),
        'plan_digest': canonical_digest(plan),
        'tests_digest': canonical_digest(tests),
    }
    observations = []
    failed = 0
    total = 0
    for req in requirements.get('requirements', []):
        if req.get('priority') not in {'blocking', 'required'}:
            continue
        req_id = req.get('id')
        artifacts = sorted({
            artifact for _, reqs, _, _, artifacts in core['task_catalog']
            if req_id in reqs for artifact in artifacts
        })
        criterion_map = {
            c.get('id'): set(c.get('test_ids') or [])
            for c in (req.get('criteria') or []) if isinstance(c, dict) and c.get('id')
        }
        for test_id in req.get('test_ids') or []:
            test = test_catalog.get(test_id)
            if not test or test.get('kind') != 'automated':
                continue
            total += 1
            criterion_ids = [cid for cid, tids in criterion_map.items() if test_id in tids]
            obs = automated_observation(project, req_id, criterion_ids, test_id, test, artifacts, basis, timeout)
            observations.append(obs)
            if obs['result'] != 'pass':
                failed += 1
    append_evidence_batch(project, observations, basis)
    return total, failed, True


def record_typed_evidence(project, test_id, requirement_id, criterion_ids, result, observer, source, note):
    gate_errors = check_project(project, 'execute')
    if gate_errors:
        return gate_errors, None
    docs = project / 'docs' / 'fable'
    requirements = load_json(docs / 'requirements.json')
    plan = load_json(docs / 'plan.json')
    tests = load_json(docs / 'tests.json')
    core = validate_core_docs(project, requirements, plan, tests)
    test = core['test_catalog'].get(test_id)
    if not test:
        return [f'E_REF_TEST: unknown test {test_id}'], None
    if test.get('kind') == 'automated':
        return [f'E_EVIDENCE_TYPE: automated evidence must come from run-tests: {test_id}'], None
    req = next((r for r in requirements.get('requirements', []) if r.get('id') == requirement_id), None)
    if not req:
        return [f'E_REF_REQUIREMENT: unknown requirement {requirement_id}'], None
    if test_id not in (req.get('test_ids') or []):
        return [f'E_REF_TEST_SCOPE: {test_id} is not declared by {requirement_id}'], None
    expected_criteria = {
        c.get('id') for c in (req.get('criteria') or [])
        if test_id in (c.get('test_ids') or [])
    }
    if expected_criteria - set(criterion_ids):
        return [f'E_EVIDENCE_CRITERIA: missing criterion ids: {", ".join(sorted(expected_criteria - set(criterion_ids)))}'], None
    artifacts = sorted({
        artifact for _, reqs, _, _, artifacts in core['task_catalog']
        if requirement_id in reqs for artifact in artifacts
    })
    basis = {
        'requirements_digest': canonical_digest(requirements),
        'plan_digest': canonical_digest(plan),
        'tests_digest': canonical_digest(tests),
    }
    obs = {
        'id': 'EV-' + uuid.uuid4().hex,
        'test_id': test_id,
        'requirement_ids': [requirement_id],
        'criterion_ids': sorted(set(criterion_ids)),
        'evidence_type': test.get('kind'),
        'result': result,
        'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'observer': observer,
        'source': source,
        'note': note or '',
        'artifacts': artifacts,
        'artifacts_digest': artifact_digest(project, artifacts) if artifacts else None,
        'basis': basis,
    }
    run_id = append_evidence_batch(project, [obs], basis)
    return [], run_id


def snapshot_project(project: Path):
    docs = project / 'docs' / 'fable'
    requirements = load_json(docs / 'requirements.json')
    plan = load_json(docs / 'plan.json')
    tests = load_json(docs / 'tests.json')
    core = validate_core_docs(project, requirements, plan, tests)
    if core['errors']:
        raise ValueError('\n'.join(core['errors']))
    return {
        'requirements_digest': canonical_digest(requirements),
        'plan_digest': canonical_digest(plan),
        'tests_digest': canonical_digest(tests),
        'write_set_baseline': git_write_set(project),
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)

    check = sub.add_parser('check')
    check.add_argument('--project', required=True)
    check.add_argument('--gate', choices=['plan', 'execute', 'complete', 'resume'], default='plan')

    run_tests = sub.add_parser('run-tests')
    run_tests.add_argument('--project', required=True)
    run_tests.add_argument('--timeout', type=int, default=120)

    record = sub.add_parser('record-evidence')
    record.add_argument('--project', required=True)
    record.add_argument('--test-id', required=True)
    record.add_argument('--requirement-id', required=True)
    record.add_argument('--criterion-id', action='append', default=[])
    record.add_argument('--result', choices=['pass', 'fail'], required=True)
    record.add_argument('--observer', required=True)
    record.add_argument('--source', required=True)
    record.add_argument('--note', default='')

    snapshot = sub.add_parser('snapshot')
    snapshot.add_argument('--project', required=True)

    args = parser.parse_args()
    project = Path(args.project).resolve()
    try:
        if args.command == 'run-tests':
            total, failed, executed = run_project_tests(project, args.timeout)
            if not executed:
                return 1
            if failed:
                print(f'FAIL: run-tests {total - failed}/{total}')
                return 1
            print(f'PASS: run-tests {total}/{total}')
            return 0
        if args.command == 'record-evidence':
            errors, run_id = record_typed_evidence(
                project, args.test_id, args.requirement_id, args.criterion_id,
                args.result, args.observer, args.source, args.note,
            )
            if errors:
                for error in errors:
                    print(error)
                return 1
            print(f'PASS: evidence recorded {run_id}')
            return 0
        if args.command == 'snapshot':
            print(json.dumps(snapshot_project(project), indent=2, sort_keys=True))
            return 0
        errors = check_project(project, args.gate)
    except ValueError as exc:
        print(str(exc))
        return 2

    if errors:
        for err in errors:
            print(err)
        return 1
    print(f'PASS: {args.gate}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
