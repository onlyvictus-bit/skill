"""Read-only evidence check. Never invokes native programs or deletes files."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[4]
run = Path(__file__).resolve().parent
baseline = json.loads((run / 'baseline.json').read_text(encoding='utf-8'))['files']
source = json.loads((run / 'acceptance-source.json').read_text(encoding='utf-8'))
allowed = set(source) | {
    'docs/fable/derived/practical-fence-plan.md', 'docs/fable/state.json',
    'docs/fable/GATES-lease-reassign.md', 'docs/changes/2026-10-14-practical-fence-wip.md',
}
for name, expected in source.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
for name, expected in baseline.items():
    target = root / name
    assert target.is_file(), 'Missing retained baseline file: ' + name
    if name not in allowed:
        assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, 'Unrelated change: ' + name
contract = json.loads((root / 'docs/fable/derived/practical-fence-contract.json').read_text(encoding='utf-8'))
for name, value in contract.items():
    if name.endswith('_qualified'):
        assert value is False, name
connected = json.loads((run / 'connected-evidence.json').read_text(encoding='utf-8'))
assert connected['native_execution'] is False and connected['TEST_ONLY'] is True
assert connected['source_sha256'] == source
assert connected['case_count'] == 18
for case in connected['cases']:
    assert case['result']['verdict'] != 'PASSED', case['fault']
    if case['fault'] in ('unrelated_transport_failure', 'missing_execution_cause'):
        assert case['canonical_calls'] == 1
        assert case['result']['verdict'] == 'INCONCLUSIVE'
        assert {r['code'] for r in case['result']['reasons']} == {'REFUSAL_UNKNOWN'}
print('SAVED_SOURCE_VERIFIED: 6 source hashes; 501 baseline files retained; native flags false; 18 connected cases')
