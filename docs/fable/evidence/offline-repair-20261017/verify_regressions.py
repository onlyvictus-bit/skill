"""Read-only comparison of observed, safety-adapted offline test results."""
import json
from pathlib import Path

run = Path(__file__).resolve().parent
comparison = json.loads((run / 'regression-comparison.json').read_text(encoding='utf-8'))
for group in comparison['groups']:
    before = json.loads((run / group['baseline']).read_text(encoding='utf-8'))
    after = json.loads((run / group['after']).read_text(encoding='utf-8'))
    for kind in ('failures', 'errors', 'skips', 'expected_failures', 'unexpected_successes'):
        ids = lambda result: {item['test'] if isinstance(item, dict) else item for item in result[kind]}
        assert ids(before) == ids(after), (group['group'], kind)
    assert after['tests_run'] - before['tests_run'] == group['declared_added_tests']
    print(group['group'], group['before_counts'], '->', group['after_counts'])
assert all(not result['removed'] for result in comparison['baseline_definitions_preserved'].values())
print('BASELINE_DIFFERENCES_ACCOUNTED: no existing problem-set changes; no baseline definitions removed')
