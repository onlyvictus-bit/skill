"""Bounded worker process for the stale owner's client session.

Alice's protected batch holds an open transaction with a bounded pause inside
it. That can only be observed from another session if her dispatch runs in a
separate process, so this module is that process. It is deliberately tiny and
side-effect free beyond one dispatch:

* it reads exactly one JSON spec file the harness wrote;
* it rebuilds the selection and request through the production contracts, so
  a hand-edited spec is refused rather than trusted;
* it dispatches once through the sealed backend and the existing CM journal,
  using the same paused-title capability the fence exposes for observation;
* it writes exactly one JSON outcome file and exits with a fixed code.

No SQL crosses the process boundary. The worker receives a pause length, not a
statement, and the protected batch is derived from the validated request
inside the sealed backend. That is what keeps the paused experiment connected
to the real dispatch path without opening a caller-SQL seam.

It has no success reader and no way to claim an effect it did not observe. It
has never been executed: no host was available.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

EXIT_DISPATCHED = 0
EXIT_REFUSED = 3
EXIT_UNREADABLE = 4

_SPEC_KEYS = frozenset({'selection', 'request', 'work_item_id', 'journal_path',
                        'outcome_path', 'pause_seconds'})


def _refusal_source(exc):
    """Retained for callers that want a coarse component name.

    The worker no longer uses this to decide a refusal: the companion may
    return an uncertain terminal without raising, so an exception is not the
    only path and never the authority on its own.
    """
    from .practical_race_controller import _protected_refusal_source
    return _protected_refusal_source(exc)


def run(spec_path):
    from .release_profile import require_native_execution_enabled
    require_native_execution_enabled()
    from complete_read_v2 import ledger
    from .practical_lease_backend import LeaseScratchBackend
    from .practical_lease_consumer import LeaseNativeConsumer
    from .practical_contract import LeaseGuardedTitleRequest, LeasePracticalSelection
    from .practical_race_controller import completion_outcome

    spec = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    if not isinstance(spec, dict) or set(spec) != _SPEC_KEYS:
        raise ValueError('E_RACE_WORKER_SPEC: exact spec fields required')
    pause_seconds = spec['pause_seconds']
    if type(pause_seconds) is not int or not 1 <= pause_seconds <= 30:
        raise ValueError('E_RACE_WORKER_SPEC: pause must be 1..30 seconds')
    selection = LeasePracticalSelection.from_value(spec['selection'])
    request = LeaseGuardedTitleRequest.from_value(spec['request'])
    # The companion terminal is the only outcome evidence. An uncertain
    # terminal is reported as uncertain and is never dressed up as a refusal:
    # current authority and execution cause remain separate observations.
    outcome_record = {'operation_id': request.operation_id, 'outcome': None, 'code': None}
    db = ledger.connect(spec['journal_path'])
    try:
        # The parent registered this work before the initial claim. Reopen
        # that exact item; creating it again fails before Alice can dispatch.
        item = db.execute('SELECT task_digest,source_id FROM work_items WHERE id=?',
                          (spec['work_item_id'],)).fetchone()
        if request.work_item_id != spec['work_item_id'] or item is None \
                or item['task_digest'] != 'task-' + spec['work_item_id'] \
                or item['source_id'] != 'PRACTICAL-RACE-HARNESS' \
                or ledger.coordination_get(db, spec['work_item_id']) != {'registered': True}:
            raise ValueError('E_RACE_WORKER_JOURNAL: exact parent registration required')
        consumer = LeaseNativeConsumer(db, LeaseScratchBackend(selection))
        code = EXIT_DISPATCHED
        try:
            result = consumer.dispatch_paused_lease_title(request, pause_seconds=pause_seconds)
            outcome_record['outcome'] = completion_outcome(result)
            if outcome_record['outcome'] is None:
                outcome_record['code'] = 'E_HARNESS_NO_TERMINAL_OBSERVED'
        except Exception as exc:
            outcome_record['code'] = type(exc).__name__
            code = EXIT_REFUSED
        Path(spec['outcome_path']).write_text(json.dumps(outcome_record, sort_keys=True),
                                               encoding='utf-8')
        return code
    finally:
        db.close()


def main(argv):
    if len(argv) != 2:
        sys.stderr.write('usage: practical_race_alice SPEC_JSON\n')
        return EXIT_UNREADABLE
    try:
        return run(argv[1])
    except Exception as exc:
        sys.stderr.write('%s\n' % (type(exc).__name__,))
        return EXIT_UNREADABLE


if __name__ == '__main__':
    sys.exit(main(sys.argv))
