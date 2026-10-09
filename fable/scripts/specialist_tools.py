"""Local helpers for the six-specialist adapters; never install or deploy."""
import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import sys
from pathlib import Path

NAMES = ('unlazy', 'graphify', 'triangulate', 'cortex', 'blueprint', 'release-helper')


def status():
    root = Path(__file__).resolve().parents[1]
    return {'python': sys.executable, 'node': shutil.which('node'),
            'graphify_importable': importlib.util.find_spec('graphify') is not None,
            'bundled_sources': {n: (root / 'references' / 'specialists' / n / 'SKILL.md').is_file() for n in NAMES},
            'note': 'Discovery only; not a runtime behavior test.'}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def triangulate(data):
    if not isinstance(data, dict) or not nonempty(data.get('target')) or not nonempty(data.get('unit')):
        raise ValueError('target and unit are required')
    width = data.get('max_tight_width')
    if not number(width) or width < 0:
        raise ValueError('max_tight_width must be a finite nonnegative predeclared bound')
    lenses = data.get('lenses')
    if not isinstance(lenses, list) or not lenses:
        raise ValueError('nonempty lenses required')
    groups, ids = [], set()
    for row in lenses:
        if not isinstance(row, dict) or not nonempty(row.get('id')) or row['id'] in ids:
            raise ValueError('unique nonempty lens IDs required')
        ids.add(row['id'])
        origins, interval = row.get('origins'), row.get('range')
        if not isinstance(origins, list) or not origins or not all(nonempty(x) for x in origins):
            raise ValueError('every lens needs raw-data origins')
        if not isinstance(interval, list) or len(interval) != 2 or not all(number(x) for x in interval) or interval[0] > interval[1]:
            raise ValueError('range must be [finite low, finite high]')
        group = {'members': [row['id']], 'origins': set(origins), 'range': interval[:], 'raw_ranges': [interval[:] ]}
        # Connected components of provenance, including transitive correlation.
        remaining = []
        for previous in groups:
            if group['origins'] & previous['origins']:
                group['members'] += previous['members']
                group['origins'] |= previous['origins']
                group['raw_ranges'] += previous['raw_ranges']
                group['range'] = [min(group['range'][0], previous['range'][0]), max(group['range'][1], previous['range'][1])]
            else:
                remaining.append(previous)
        groups = remaining + [group]
    families = [{**g, 'origins': sorted(g['origins']), 'members': sorted(g['members'])} for g in groups]
    count = len(families)
    common = [max(g['range'][0] for g in groups), min(g['range'][1] for g in groups)]
    common = common if common[0] <= common[1] else None
    spread = max(g['range'][1] for g in groups) - min(g['range'][0] for g in groups)
    overlap = max(sum(g['range'][0] <= point <= g['range'][1] for g in groups)
                  for point in (g['range'][0] for g in groups))
    if count < 2:
        verdict, grade = 'INSUFFICIENT', None
    elif common is not None and spread <= width:
        verdict, grade = 'TIGHT', 'A'
    elif common is not None or overlap > count / 2:
        verdict, grade = 'PARTIAL', 'B'
    elif overlap >= 2:
        verdict, grade = 'SCATTERED', 'C'
    else:
        verdict, grade = 'NONE', 'NO-GO'
    return {'target': data['target'], 'unit': data['unit'], 'families': families,
            'independent_family_count': count, 'common_region': common,
            'max_agreeing_families': overlap, 'total_span': spread,
            'overlap': verdict, 'grade': grade,
            'limitation': 'Provenance labels and reliability require source review. No probability or action authorization.'}


def release_check(data):
    if not isinstance(data, dict):
        raise ValueError('release observation must be an object')
    errors = []
    for key in ('expected_environment', 'observed_environment', 'observation_source'):
        if not nonempty(data.get(key)):
            errors.append('missing ' + key)
    for key in ('expected_digest', 'observed_digest'):
        if not isinstance(data.get(key), str) or not re.fullmatch(r'[a-fA-F0-9]{64}', data[key]):
            errors.append('invalid SHA256 ' + key)
    if data.get('authorized') is not True:
        errors.append('authorization not established')
    if type(data.get('exit_code')) is not int or data['exit_code'] != 0:
        errors.append('release process did not exit zero')
    if data.get('healthy') is not True:
        errors.append('runtime not observed healthy')
    if data.get('expected_environment') != data.get('observed_environment'):
        errors.append('wrong environment')
    if str(data.get('expected_digest', '')).lower() != str(data.get('observed_digest', '')).lower():
        errors.append('stale or wrong deployed identity')
    return {'consistent': not errors, 'errors': errors,
            'limitation': 'Checks supplied observations only; does not authenticate consent, deploy, or observe a live service.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    for name in ('triangulate', 'release-check'):
        child = sub.add_parser(name)
        child.add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'status':
            result = status()
        else:
            data = json.loads(args.input.read_text(encoding='utf-8'))
            result = triangulate(data) if args.command == 'triangulate' else release_check(data)
        print(json.dumps(result, indent=2))
        return 1 if result.get('consistent') is False else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
