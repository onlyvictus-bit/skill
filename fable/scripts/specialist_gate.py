"""Additive specialist coverage gate; original Fable checks run unchanged first."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import fable_guard
from specialist_tools import NAMES, nonempty


def local_path(project, value):
    errors = []
    normalized = fable_guard.normalize_project_path(project, value, 'specialist output', errors)
    if errors or not normalized:
        raise ValueError('; '.join(errors))
    return normalized


def check_specialists(project, gate):
    docs = project / 'docs' / 'fable'
    record = fable_guard.load_json(docs / 'specialists.json')
    if not isinstance(record, dict) or set(record) != {'schema', 'skills'} or record.get('schema') != 1:
        return ['E_SPECIALIST_SCHEMA: expected schema 1 with skills']
    rows = record.get('skills')
    if not isinstance(rows, list) or len(rows) != len(NAMES):
        return ['E_SPECIALIST_COVERAGE: exactly six dispositions required']
    requirements = fable_guard.load_json(docs / 'requirements.json')
    plan = fable_guard.load_json(docs / 'plan.json')
    tests = fable_guard.load_json(docs / 'tests.json')
    reqs = {r['id']: set(r['test_ids']) for r in requirements['requirements']}
    test_ids = {t['id'] for t in tests['tests']}
    artifacts = {a for task in plan['tasks'] for a in task['artifacts']}
    errors, seen = [], set()
    if 'docs/fable/specialists.json' not in artifacts:
        errors.append('E_SPECIALIST_SCOPE: declare specialists.json as a plan artifact')
    fields = {'name', 'disposition', 'reason', 'requirement_ids', 'test_ids', 'outputs', 'status'}
    for row in rows:
        if not isinstance(row, dict) or set(row) != fields:
            errors.append('E_SPECIALIST_SCHEMA: unsupported or missing entry fields')
            continue
        name = row['name']
        if not isinstance(name, str) or name not in NAMES or name in seen:
            errors.append('E_SPECIALIST_NAME: unknown/duplicate skill')
            continue
        seen.add(name)
        if not nonempty(row['reason']):
            errors.append(f'E_SPECIALIST_REASON: {name}')
        if row['disposition'] not in ('selected', 'not_applicable') or row['status'] not in ('pending', 'observed', 'unavailable', 'blocked'):
            errors.append(f'E_SPECIALIST_STATUS: {name}')
        mapping_ok = all(isinstance(row[k], list) and all(nonempty(x) for x in row[k]) for k in ('requirement_ids', 'test_ids'))
        if not mapping_ok or not isinstance(row['outputs'], list):
            errors.append(f'E_SPECIALIST_SCHEMA: invalid lists for {name}')
            continue
        if row['disposition'] == 'not_applicable':
            if row['requirement_ids'] or row['test_ids'] or row['outputs']:
                errors.append(f'E_SPECIALIST_SCOPE: not_applicable must have empty mappings: {name}')
            continue
        if not row['requirement_ids'] or not row['test_ids'] or not row['outputs']:
            errors.append(f'E_SPECIALIST_COVERAGE: selected helper needs mappings and outputs: {name}')
        if not set(row['requirement_ids']) <= set(reqs) or not set(row['test_ids']) <= test_ids:
            errors.append(f'E_SPECIALIST_REF: unresolved mapping: {name}')
        for req_id in row['requirement_ids']:
            if not set(row['test_ids']) & reqs.get(req_id, set()):
                errors.append(f'E_SPECIALIST_TEST: no declared test for {name}/{req_id}')
        for test_id in row['test_ids']:
            if not any(test_id in reqs.get(r, set()) for r in row['requirement_ids']):
                errors.append(f'E_SPECIALIST_TEST: test outside selected requirement mapping: {name}')
        for output in row['outputs']:
            if not isinstance(output, dict) or set(output) != {'path', 'sha256'}:
                errors.append(f'E_SPECIALIST_SCHEMA: invalid output for {name}')
                continue
            try:
                rel = local_path(project, output['path'])
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if rel not in artifacts:
                errors.append(f'E_SPECIALIST_SCOPE: unplanned output {rel}')
            # Each output must be in a task carrying this helper's requirement and test.
            linked = any(rel in t['artifacts'] and set(row['requirement_ids']) & set(t['requirement_ids'])
                         and set(row['test_ids']) & set(t['test_ids']) for t in plan['tasks'])
            if not linked:
                errors.append(f'E_SPECIALIST_TRACE: output not connected to helper requirement/test: {rel}')
            if gate == 'complete':
                path = project / rel
                if not path.is_file() or path.is_symlink():
                    errors.append(f'E_SPECIALIST_OUTPUT: absent/invalid output {rel}')
                elif hashlib.sha256(path.read_bytes()).hexdigest() != output['sha256']:
                    errors.append(f'E_SPECIALIST_STALE: {rel}')
        if gate == 'complete' and row['status'] != 'observed':
            errors.append(f'E_SPECIALIST_UNVERIFIED: {name} is {row["status"]}')
    if seen != set(NAMES):
        errors.append('E_SPECIALIST_COVERAGE: one or more skills omitted')
    return errors


def check(project, gate):
    original_errors = fable_guard.check_project(project, gate)
    if original_errors:
        return original_errors
    return check_specialists(project, gate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--gate', choices=['plan', 'execute', 'resume', 'complete'], required=True)
    args = parser.parse_args()
    try:
        errors = check(args.project.resolve(), args.gate)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        errors = ['E_SPECIALIST_INVALID: ' + str(exc)]
    for error in errors:
        print(error)
    if not errors:
        print('PASS: original Fable and specialist ' + args.gate + ' gates')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
